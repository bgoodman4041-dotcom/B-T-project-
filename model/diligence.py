"""
TRACK BOSS — Diligence Register, ranked by how much the answer moves
====================================================================

The package names roughly fifty open items across the comparable study, the
jurisdiction register, the risk register and the source register. Scattered like
that they are a to-do list, and a to-do list is not a diligence plan: it does not
say what to do first, and it does not say what any of it is worth.

This consolidates them and prices each one the only way that is defensible —
by flexing the model over the range the item is uncertain across and measuring
what happens to the governing tests. Three questions come out, and they are
different questions:

    price()      What is at stake in the answer?   (downside in bp, per item)
    tolerance()  How much of the bad answer can we absorb before it breaks?
    survival()   How many of them can go wrong at once?

WHAT THIS IS NOT
----------------
It is not a claim that the adverse end is likely. The range is the honest span
of what the item could turn out to be, and the swing is what is at stake in
finding out. An item with a large swing is not a problem — it is a question
worth the money to answer, which is exactly what a feasibility budget buys.

Items with no model driver — a title search, a records request, an acoustic
model — carry no swing rather than a guessed one. They are ranked by the gate
they clear instead, and the register says which.

RANGES ARE CONTINUOUS, NOT BINARY
---------------------------------
Every range is a `Span` in the item's own natural units — dollars of dues, days
of season, members of cap — with `t=0` the favourable end and `t=1` the adverse
one. That is what makes `tolerance()` possible: bisecting on t answers "the deal
breaks when dues fall below $X", which is a far more useful sentence than "the
adverse end breaks it". A binary flexer can only ever say whether the worst case
survives; it cannot say how much of the range the deal actually absorbs.

THE SITE COST PREMIUM IS A FLEXED INPUT, NOT A FIXED ONE
--------------------------------------------------------
The single most-argued number in the programme is the lead site's −$9.5M
pavement credit, and it lives in `site_cost_premium`, not in the config. A
flexer that could only reach the config would have left the biggest question in
the package unpriced, so every span takes and returns the premium as well.

RECONCILIATION
--------------
`reconcile()` checks the register against the Tranche 1 budget in both
directions: no item may spend money the ask does not contain, and no line of
the ask may go unclaimed by a numbered question. It found one gap on first run —
the ask had no title line while the risk register carried the lead site's
disposition in litigation as a High/High entry.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable

from . import cashflow as cf_mod
from . import scenarios as sc
from . import two_stack as ts

# One Tranche 1 line is not a question and never will be. Naming it here keeps
# the reconciliation honest rather than letting it drift into a rounding note.
NOT_A_QUESTION = {"Sponsor overhead and programme management"}


@dataclass
class Span:
    """
    One item's uncertainty range, in the units the question is asked in.

    `fav` and `adv` are natural units -- $34,000 of dues, 210 days of season --
    not model factors, so the register can state where a break falls in language
    a committee uses. `apply` converts a natural value into the model.
    """
    fav: float
    adv: float
    fmt: Callable[[float], str]
    apply: Callable[[dict[str, Any], float, float], tuple[dict[str, Any], float]]

    def value(self, t: float) -> float:
        """Linear interpolation. t=0 favourable, t=1 adverse."""
        return self.fav + (self.adv - self.fav) * t

    def __call__(self, cfg: dict[str, Any], prem: float,
                 t: float | str) -> tuple[dict[str, Any], float]:
        if t == "fav":
            t = 0.0
        elif t == "adv":
            t = 1.0
        return self.apply(cfg, prem, self.value(float(t)))

    def describe(self, t: float) -> str:
        return self.fmt(self.value(t))

    @property
    def note(self) -> str:
        return f"{self.fmt(self.fav)} to {self.fmt(self.adv)}"


@dataclass
class Item:
    id: str
    category: str
    question: str
    gates: str
    owner: str
    cost_usd: float
    weeks: int
    source: str
    flex: Span | None = None
    range_note: str = ""
    tranche_line: str | None = None


@dataclass
class Priced:
    item: Item
    irr_fav: float | None
    irr_adv: float | None
    irr_swing_bps: float | None
    downside_bps: float | None
    dscr_adv: float | None
    breaks_covenant: bool | None
    bps_per_100k: float | None
    verdict: str


@dataclass
class Tolerance:
    """
    How far into an item's adverse range the deal still clears every test.

    Two boundaries, deliberately, because they are not the same one. The
    governing boundary is the first of the three tests to fail; the covenant
    boundary is where the DSCR floor alone gives way. The package quotes the
    covenant everywhere, so showing only that number would hide the fact that
    something else binds earlier.
    """
    item: Item
    absorbed_pct: float | None      # share of the range absorbed, 0..1
    breaks_at: float | None         # natural-unit value where it stops clearing
    breaks_at_text: str
    binding_test: str
    verdict: str
    covenant_pct: float | None = None      # share absorbed before DSCR alone fails
    covenant_at: float | None = None
    covenant_at_text: str = "does not break"


@dataclass
class Step:
    """One rung of the compounding walk in `survival`."""
    added: str
    irr: float | None
    min_dscr: float
    equity_multiple: float
    value_to_cost: float
    clears: bool


# =============================================================================
# The spans
# =============================================================================
# A scenario factor where one exists, a direct config edit where it does not,
# and the site cost premium where the question is about the dirt. Every range is
# the honest span between the evidence's answer and the configured assumption --
# not a stress, just the width of what is unknown.

def _factor(name: str, base: float, fav: float, adv: float,
            fmt: Callable[[float], str]) -> Span:
    """A scenario multiplier expressed in natural units against `base`."""
    return Span(fav, adv, fmt,
                lambda c, p, v: (sc.apply_scenario(c, {name: v / base}), p))


def _inverse_factor(name: str, base: float, fav: float, adv: float,
                    fmt: Callable[[float], str]) -> Span:
    """For factors that DIVIDE, like absorption_slowdown."""
    return Span(fav, adv, fmt,
                lambda c, p, v: (sc.apply_scenario(c, {name: base / v}), p))


def _absolute(name: str, fav: float, adv: float, fmt: Callable[[float], str]) -> Span:
    """A scenario override that is already an absolute value, like abatement_pct."""
    return Span(fav, adv, fmt,
                lambda c, p, v: (sc.apply_scenario(c, {name: v}), p))


def _set(path: tuple[str, ...], fav: float, adv: float,
         fmt: Callable[[float], str], cast: Callable[[float], Any] = float) -> Span:
    def _apply(cfg: dict[str, Any], prem: float, v: float):
        c = copy.deepcopy(cfg)
        node = c
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = cast(v)
        return c, prem
    return Span(fav, adv, fmt, _apply)


def _scale(path: tuple[str, ...], fav: float, adv: float,
           fmt: Callable[[float], str]) -> Span:
    """Scale every numeric leaf of a config subtree. For unbid cost blocks."""
    def _apply(cfg: dict[str, Any], prem: float, v: float):
        c = copy.deepcopy(cfg)
        node = c
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = {k: (x * v if isinstance(x, (int, float)) else x)
                          for k, x in node[path[-1]].items()}
        return c, prem
    return Span(fav, adv, fmt, _apply)


def _premium(fav: float, adv: float) -> Span:
    """
    The site cost premium, which is a per-site argument rather than config.

    EPCAL carries a credit and Pinal carries a charge, so the span is built from
    the site's own number rather than a national one.
    """
    return Span(fav, adv, lambda v: f"${v / 1e6:,.1f}M premium" if v > 0
                else (f"${abs(v) / 1e6:,.1f}M credit" if v < 0 else "no credit"),
                lambda c, p, v: (c, v))


def _usd(v: float) -> str:
    return f"${v:,.0f}"


def _pct_move(v: float) -> str:
    return f"{v - 1:+.0%}"


# =============================================================================
# The register
# =============================================================================

def register(cfg: dict[str, Any], premium: float = 0.0) -> list[Item]:
    """
    The register. `premium` is the site's own cost premium or credit, which is
    an argument to the cash flow rather than a config key, so an item that flexes
    it cannot state its range in dollars without being told the site.
    """
    m = cfg["income"]["membership"]
    condo = cfg["for_sale"]["garage_condos"]
    pt = cfg["income"]["property_tax"]
    inc = cfg["income"]
    dues, init, cap = m["annual_dues_usd"], m["initiation_fee_usd"], m["cap"]
    psf, absorp = condo["sale_price_psf"], condo["absorption_units_per_year"]
    season = float(inc.get("season_days") or inc["season"]["baseline_days"])
    ent_budget = cfg["cost"]["entitlement_budget_usd"]
    ne_dues, ne_init = 18_500.0, 125_000.0
    comp_psf = 348.0
    ent_assumed, ent_researched = 33, 45          # months, EPCAL, jurisdiction register

    # A credit can evaporate and a premium can only be bid against, so only the
    # credit direction is priceable here. On a site that already carries a
    # charge the Phase II can confirm it or make it worse, and by how much is
    # exactly what the study is for -- guessing a multiplier would be inventing
    # the answer the item exists to buy.
    prem_flex = _premium(premium, 0.0) if premium < 0 else None
    # When there IS a span it writes its own range, like every other item. The
    # hand-written note only exists for the case where no span is defensible.
    prem_note = ("" if prem_flex is not None
                 else f"${premium / 1e6:,.1f}M charge — confirmed, or worse by an "
                      f"amount only the study can state")

    items = [
        Item("DD-01", "Revenue",
             f"Will members pay ${dues:,.0f} a year where buying real estate is "
             f"optional? The comparable set's ceiling outside a mandatory-purchase "
             f"club or invitation-only Miami is ${ne_dues:,.0f}.",
             "Everything. It is the largest single input to NOI.",
             "Hospitality/club consultancy + direct calls to MMC, NJMP, Apex, AMP",
             285_000, 10, "comps_findings.md §1, §3",
             _factor("dues_factor", dues, dues, ne_dues, lambda v: f"${v:,.0f}/yr"),
             "", "Comparable club economics study"),

        Item("DD-02", "Revenue",
             f"Is the ${init:,.0f} initiation collectable, and is any of it "
             f"REFUNDABLE? The reference asset is reported to refund 70% on exit, "
             f"which would make most of it a liability rather than income.",
             "NOI and the funding waterfall — initiation is the deepest source of "
             "cash during the equity trough.",
             "Direct call: Monticello, Concours and Thermal membership offices",
             0, 2, "comps_findings.md §1 (refundable deposit)",
             _set(("income", "initiation_treatment", "refundable_share"), 0.0, 0.70,
                  lambda v: f"{v:.0%} refundable"),
             "", None),

        Item("DD-03", "Revenue",
             f"Does the Northeast initiation ceiling of ${ne_init:,.0f} hold? It rests "
             f"on ONE AI-generated wiki entry about ONE club, with a five-fold gap to "
             f"the next observation in the set.",
             "The initiation line, and the credibility of the whole comp register.",
             "Monticello Motor Club membership office",
             0, 1, "comps_findings.md §2",
             _factor("initiation_factor", init, init, ne_init, _usd),
             "", None),

        Item("DD-04", "For-sale",
             f"Will garage condominiums sell at ${psf:,.0f}/SF? The two operating "
             f"new-build track comps price at $344-352 — which is this model's assumed "
             f"HARD COST, before the 1.298x soft and contingency load.",
             "The for-sale stack, which funds the build and sets the carry.",
             "Residential/flex market study + a Suffolk industrial broker on trades",
             175_000, 8, "comps_findings.md §4",
             _factor("condo_psf_factor", psf, psf, comp_psf, lambda v: f"${v:,.0f}/SF"),
             "", "Market and absorption study for the for-sale stack"),

        Item("DD-05", "For-sale",
             f"Can {absorp} units a year be absorbed? M1 realised 17.5 and NJMP "
             f"delivered 10-15 across nine phases in fifteen years — and NJMP is the "
             f"closest structural Northeast analogue there is.",
             "Carry. Sell-out sets the carry period in a merchant build.",
             "NJMP phase records + county recorder (inside the DD-04 study scope)",
             0, 4, "comps_findings.md §7",
             _inverse_factor("absorption_slowdown", absorp, absorp, 15.0,
                             lambda v: f"{v:.0f} units/yr"),
             "", None),

        Item("DD-06", "Environmental",
             "Is the EPCAL runway pavement reusable as base course, or is it a PFAS "
             "waste-characterisation problem? The Navy identified fifteen new areas of "
             "concern around that runway in 2023, sourced to firefighting foam.",
             "The lead site's cost credit, and which of the two finalists gets funded.",
             "Environmental engineering — Phase II with PFAS and 1,4-dioxane analytical",
             420_000, 12, "risk_register RR-02",
             prem_flex, prem_note,
             "Phase I and Phase II environmental (2 sites)"),

        Item("DD-07", "Tax",
             f"Will the IDA grant a {pt['abatement_pct']:.0%} PILOT? Without it the "
             f"covenant breaks and maximum supportable land goes negative. Section 862 "
             f"eligibility for a private recreation use is the open question.",
             "A condition precedent to land closing in every high-rate state.",
             "Economic development counsel — obtain a § 862 opinion",
             145_000, 16, "jurisdiction_register Part III",
             _absolute("abatement_pct", pt["abatement_pct"], 0.0,
                       lambda v: f"{v:.0%} abated"),
             "", "Property tax abatement negotiation"),

        Item("DD-08", "Cost",
             "Is the circuit and vertical hard cost right? Nothing in the package is a "
             "bid; the whole cost stack is benchmark-derived.",
             "The basis, and therefore every yield and coverage figure.",
             "General contractor — budget pricing to a GMP-track estimate",
             0, 10, "config cost block, all ASSUMED",
             _factor("hard_cost_factor", 1.0, 0.92, 1.15, _pct_move),
             "", None),

        Item("DD-09", "Operations",
             "Will a club operator run this at the modelled operating ratio? No operator "
             "is appointed and the ratio drives the covenant.",
             "The covenant, and a condition precedent to construction capital.",
             "Operator search and management agreement (sponsor time, not a vendor)",
             0, 20, "plan §10 — role OPEN",
             _factor("opex_factor", 1.0, 0.94, 1.16, _pct_move),
             "", None),

        Item("DD-10", "Market",
             f"Can {cap} members actually be recruited at this price? Every rate in the "
             f"demand funnel — collector share, track-active share, incumbent capture — "
             f"is judgment, not measured conversion.",
             "Whether the ramp is achievable at all, and the club's size.",
             "Founding-member campaign with a paid waitlist — measured conversion",
             240_000, 24, "model/demand.py — all rates ASSUMED",
             _factor("cap_factor", cap, cap, cap * 0.80, lambda v: f"{v:,.0f} members"),
             "", "Founding-member demand testing"),

        Item("DD-11", "Season",
             f"Is {season:.0f} usable days right for the lead site? The only published "
             f"Northeast facility figure in the comp set is 150 days, at a materially "
             f"colder site.",
             "Ancillary revenue, and the ranking of every Sun Belt site against it.",
             "Operator calendars + a climate-hours analysis",
             0, 3, "comps_findings.md §6",
             _set(("income", "season_days"), season, 180.0,
                  lambda v: f"{v:.0f} days", cast=lambda v: int(round(v))),
             "", None),

        Item("DD-12", "Entitlement",
             "What is the daytime dBA limit at the nine sites where none is published? "
             "Two have ordinances whose tables would not open; seven publish nothing.",
             "Gate 2 and the entitlement score. Cheap, and it removes an "
             "unverified-ordinance discount from every affected row.",
             "Nine named municipal offices — see the Jurisdictions tab",
             0, 3, "jurisdiction_register — nine blanks",
             None, "unverified to cited", None),

        Item("DD-13", "Land",
             "What does large-acreage land actually trade at in the target counties, and "
             "who owns these parcels? No land comparables were obtained and no target "
             "carries an APN, coordinates or an owner to call.",
             "Gate 0. Fifteen target PROFILES become parcels, or they do not.",
             "Land brokers and GIS/title research in the target counties",
             310_000, 8, "comps_findings.md §10 — NOT DELIVERED",
             None, "profile to parcel",
             "Nationwide sourcing pass — 150+ parcels to identifiers"),

        Item("DD-14", "Title",
             "Is the EPCAL disposition free to transact? In litigation since 2024, one "
             "cause of action surviving dismissal in February 2026, land described as in "
             "limbo throughout.",
             "Whether the lead site can be optioned at all.",
             "Title counsel — affirmative coverage naming the pending action",
             100_000, 12, "risk_register RR-04",
             None, "clean to unmarketable",
             "Title and disposition counsel (lead site)"),

        Item("DD-15", "Exit",
             f"Will a {inc['exit_cap']:.2%} exit cap clear for a special-purpose "
             f"recreational asset with a thin buyer universe?",
             "Terminal value, which is where most of the equity return sits.",
             "Broker opinion of value from two national capital-markets teams",
             0, 6, "config income.exit_cap — ASSUMED",
             _set(("income", "exit_cap"), inc["exit_cap"] - 0.0050,
                  inc["exit_cap"] + 0.0150, lambda v: f"{v:.2%} cap"),
             "", None),

        Item("DD-16", "Entitlement",
             "Does the circuit meet the municipal standard at the property line, as "
             "designed? A fail here is not a cost line — it is a redesign, a berm "
             "programme, or a different site.",
             "Gate 2. It is the one item that can end a site outright.",
             "Motorsport-specific acoustic consultant",
             165_000, 9, "risk_register RR-01, RR-03",
             None, "pass, redesign, or fatal",
             "Acoustic modelling against the actual municipal standard"),

        Item("DD-17", "Cost",
             "Is the site infrastructure budget real? Earthwork, utilities and stormwater "
             "are carried at benchmark on a parcel nobody has surveyed.",
             "The basis. Site work is the least bid-able line in the stack.",
             "Civil engineering and geotech — survey and cut/fill validation",
             380_000, 10, "config cost.site_infrastructure_usd — ASSUMED",
             _scale(("cost", "site_infrastructure_usd"), 0.85, 1.25, _pct_move),
             "", "Survey, geotechnical and cut/fill validation"),

        Item("DD-18", "Design",
             "Do 4.0 miles of circuit, 140 garage condominiums and the homesites fit the "
             "parcel at a workable grade? The re-specification search wants a shorter "
             "course; nobody has drawn either version on real topography.",
             "Gate 1 and Gate 4, and the acreage the programme actually needs.",
             "Road-course designer — concept design and fit study",
             295_000, 14, "respec.py — 2.25 vs 4.0 miles, worth ~107 bp",
             None, "fits as drawn, or the programme changes",
             "Circuit concept design and fit study"),

        Item("DD-19", "Entitlement",
             f"How long is the entitlement path really, and what does running it cost? "
             f"The researched path at the lead site is {ent_researched} months against "
             f"the programme's {ent_assumed}, and fourteen of fifteen sites revised up.",
             "The roadmap, the option term, and the entitlement budget.",
             "Land-use counsel admitted in the jurisdiction",
             340_000, 16, "jurisdiction_register — mean 23.4 to 31.3 months",
             _set(("cost", "entitlement_budget_usd"), ent_budget,
                  ent_budget * ent_researched / ent_assumed,
                  lambda v: f"${v / 1e6:,.2f}M"),
             "", "Entitlement counsel and municipal strategy"),

        Item("DD-20", "Control",
             "Can both finalists be optioned, at what price, and for long enough to run "
             "the entitlement? Nothing is under contract and one of the two is in "
             "litigation over its disposition.",
             "Everything downstream. Without control the rest of the budget is spent on "
             "somebody else's land.",
             "Sellers — option payments and extensions, two sites",
             900_000, 26, "plan §12 — no site under contract",
             None, "optioned, or not",
             "Site option payments and extensions (2 sites)"),
    ]

    # A span already knows its own range in its own units. Transcribing it into
    # `range_note` by hand is how the two drift apart, so the span writes it.
    for it in items:
        if it.flex is not None and not it.range_note:
            it.range_note = it.flex.note
    return items


# =============================================================================
# Running the model at a point in the register's space
# =============================================================================

@dataclass
class _Runner:
    cfg: dict[str, Any]
    land_price: float
    horizon: int
    floor: float
    dev: int

    def __call__(self, cfg: dict[str, Any], prem: float):
        cf = cf_mod.project_cash_flow(cfg, self.land_price,
                                      horizon_operating_years=self.horizon,
                                      site_cost_premium=prem)
        rep = cf_mod.covenant_report(
            cf, self.floor, tested_from_year=self.dev + ts.stabilization_year(cfg))
        return cf, rep

    def clears(self, cfg: dict[str, Any], prem: float) -> bool:
        """The governing tests, identically to every other artifact."""
        cf, rep = self(cfg, prem)
        return bool(rep["passes_every_year"] and cf.equity_irr is not None
                    and cf.equity_irr > 0 and cf.value_to_cost >= 1.0)

    def binding(self, cfg: dict[str, Any], prem: float) -> str:
        cf, rep = self(cfg, prem)
        if not rep["passes_every_year"]:
            return f"DSCR covenant ({rep['min_dscr_tested']:.2f}x)"
        if cf.equity_irr is None or cf.equity_irr <= 0:
            return "equity IRR"
        if cf.value_to_cost < 1.0:
            return f"value to retained cost ({cf.value_to_cost:.2f}x)"
        return "none"


def _runner(cfg: dict[str, Any], land_price: float, horizon: int) -> _Runner:
    return _Runner(cfg, land_price, horizon, cfg["debt"]["min_dscr"],
                   int(round(cfg["cost"]["carry"]["development_years"])))


# =============================================================================
# price -- what is at stake in the answer
# =============================================================================

def price(cfg: dict[str, Any], land_price: float, premium: float = 0.0,
          horizon: int = 12) -> list[Priced]:
    """
    Flex each item across its uncertainty range and measure the governing tests.

    The favourable end is normally the configured assumption -- the model already
    believes it -- and the adverse end is what the evidence suggests it might be
    instead. The swing between them is what the diligence buys knowledge of.
    """
    run = _runner(cfg, land_price, horizon)
    floor = cfg["debt"]["min_dscr"]
    base_cf, _ = run(cfg, premium)
    irr_base = base_cf.equity_irr

    out: list[Priced] = []
    for item in register(cfg, premium):
        if item.flex is None:
            out.append(Priced(item, None, None, None, None, None, None, None,
                              f"No model driver — {item.gates}"))
            continue
        cf_f, _ = run(*item.flex(cfg, premium, "fav"))
        cf_a, rep_a = run(*item.flex(cfg, premium, "adv"))
        irr_f, irr_a, dscr_a = cf_f.equity_irr, cf_a.equity_irr, rep_a["min_dscr_tested"]

        swing: float | None = None
        if irr_f is not None and irr_a is not None:
            swing = (irr_f - irr_a) * 10_000
        elif irr_f is not None and irr_a is None:
            # The adverse end has no computable rate at all. That is not a large
            # swing, it is a different kind of answer, and reporting it as a
            # number would invite it to be compared against one.
            swing = float("inf")

        # The width of the range and the distance below the base case are not
        # the same number, and conflating them flatters the two-sided items.
        # An unbid cost block flexed -8%/+15% has a wide range mostly because
        # the favourable end is BETTER than what the model assumes; the dues
        # question has no favourable end at all, because the model already sits
        # at the top of it. What an IC is buying is protection against the
        # downside, so that is what the ranking runs on.
        down: float | None = None
        if irr_base is not None and irr_a is not None:
            down = max(0.0, (irr_base - irr_a) * 10_000)
        elif irr_a is None:
            down = float("inf")

        breaks = dscr_a is not None and not ts._at_least(dscr_a, floor)

        per_100k: float | None = None
        if down is not None and down != float("inf"):
            # A zero-cost item is a phone call. Ranking it as infinitely
            # efficient is true and useless, so cost it at a nominal $2,000 of
            # somebody's week rather than dividing by zero.
            per_100k = down / (max(item.cost_usd, 2_000) / 100_000)
        elif down == float("inf"):
            per_100k = float("inf")

        if down == float("inf"):
            verdict = ("No computable return at the adverse end — the deal does not "
                       "survive this one going against us.")
        elif breaks:
            verdict = (f"Breaks the covenant at the adverse end ({dscr_a:.2f}x against a "
                       f"{floor:.2f}x floor). Condition precedent, not a refinement.")
        elif down is not None and down >= 300:
            verdict = f"Material — {down:,.0f} bp below the base case if it goes against us."
        elif down is not None and down > 0:
            verdict = f"Contained — {down:,.0f} bp below the base case at the adverse end."
        else:
            verdict = ("No downside — the model already carries the adverse end. "
                       f"Confirming it is worth up to {swing:,.0f} bp of upside.")

        out.append(Priced(item, irr_f, irr_a, swing, down, dscr_a, breaks,
                          per_100k, verdict))

    # Covenant-breakers first, then by how far below the base case the adverse
    # end lands. Items with no driver keep their register order at the end
    # rather than being sorted against nothing.
    def key(p: Priced) -> tuple:
        if p.downside_bps is None:
            return (2, 0.0)
        return (0 if p.breaks_covenant else 1,
                -(1e18 if p.downside_bps == float("inf") else p.downside_bps))

    return sorted(out, key=key)


# =============================================================================
# tolerance -- how much of the bad answer the deal absorbs
# =============================================================================

def tolerance(cfg: dict[str, Any], land_price: float, premium: float = 0.0,
              horizon: int = 12, grid: int = 12, depth: int = 7) -> list[Tolerance]:
    """
    For each item, how far into its adverse range can the answer go before the
    deal stops clearing the governing tests?

    "The adverse end breaks the covenant" is a yes/no. "The covenant breaks once
    dues fall below $29,400, which is 30% of the way into a range the comparable
    set says ends at $18,500" is a margin of safety, and it is the sentence an
    investment committee actually needs.

    A coarse grid runs first and bisection refines inside the bracket it finds.
    That is deliberate: these flexes are very nearly monotone in t but not
    guaranteed to be, and bisecting a non-monotone function from the endpoints
    alone can walk straight past a failure and report tolerance the deal does
    not have.
    """
    run = _runner(cfg, land_price, horizon)
    out: list[Tolerance] = []

    def covenant_ok(c: dict[str, Any], prem: float) -> bool:
        _cf, rep = run(c, prem)
        return bool(rep["passes_every_year"])

    def bisect(span: Span, ok, lo: float, hi: float) -> float:
        for _ in range(depth):
            mid = (lo + hi) / 2
            if ok(*span(cfg, premium, mid)):
                lo = mid
            else:
                hi = mid
        return lo

    for item in register(cfg, premium):
        span = item.flex
        if span is None:
            out.append(Tolerance(item, None, None, "n/a", "no model driver",
                                 f"No model driver — {item.gates}"))
            continue

        if not run.clears(*span(cfg, premium, 0.0)):
            out.append(Tolerance(
                item, 0.0, span.fav, span.describe(0.0),
                run.binding(*span(cfg, premium, 0.0)),
                "Fails at the FAVOURABLE end — this item is not the reason, but the "
                "deal does not clear even with it resolved well."))
            continue

        # One grid pass, both predicates. The first t at which each fails brackets
        # its own bisection; `None` means that test survives the whole range.
        g_lo, g_hi = 0.0, None
        c_lo, c_hi = 0.0, None
        for k in range(1, grid + 1):
            t = k / grid
            c, pm = span(cfg, premium, t)
            if g_hi is None:
                if run.clears(c, pm):
                    g_lo = t
                else:
                    g_hi = t
            if c_hi is None:
                if covenant_ok(c, pm):
                    c_lo = t
                else:
                    c_hi = t
            if g_hi is not None and c_hi is not None:
                break

        cov_pct = 1.0 if c_hi is None else bisect(span, covenant_ok, c_lo, c_hi)
        cov_at = None if c_hi is None else span.value(cov_pct)
        cov_txt = "does not break" if c_hi is None else span.describe(cov_pct)

        if g_hi is None:
            out.append(Tolerance(
                item, 1.0, None, "does not break", "none",
                f"Absorbs the whole range. Even at {span.describe(1.0)} the deal "
                f"still clears every governing test.",
                cov_pct, cov_at, cov_txt))
            continue

        pct = bisect(span, run.clears, g_lo, g_hi)
        binding = run.binding(*span(cfg, premium, min(1.0, pct + 1e-3)))
        if pct <= 1e-9:
            verdict = (f"NO TOLERANCE. The deal stops clearing at the configured value "
                       f"of {span.describe(0.0)} — the first step into this range breaks "
                       f"it on {binding}.")
        elif pct < 0.34:
            verdict = (f"Thin — {pct:.0%} of the range. Breaks on {binding} once this "
                       f"passes {span.describe(pct)}.")
        else:
            verdict = (f"Absorbs {pct:.0%} of the range, to {span.describe(pct)}, before "
                       f"{binding} binds.")

        out.append(Tolerance(item, pct, span.value(pct), span.describe(pct),
                             binding, verdict, cov_pct, cov_at, cov_txt))

    # Thinnest tolerance first; unpriced items keep register order at the end.
    return sorted(out, key=lambda x: (1, 0.0) if x.absorbed_pct is None
                  else (0, x.absorbed_pct))


def binding_summary(tols: list[Tolerance]) -> dict[str, Any]:
    """
    Which governing test actually binds first, across every item that binds.

    This exists because the package tells the covenant story everywhere -- the
    covenant is the confirmed mandate number, so it is the one everybody quotes
    -- and on this configuration it is not the tight one. Walking any driver
    from the base case toward its adverse end, exit value against retained cost
    fails first on every single item that fails at all. Reporting only "breaks
    the covenant" is true at the far end of the range and wrong about which
    constraint the deal is actually operating against.
    """
    binding = [t for t in tols if t.absorbed_pct is not None and t.absorbed_pct < 1.0]
    counts: dict[str, int] = {}
    for t in binding:
        key = t.binding_test.split(" (")[0]
        counts[key] = counts.get(key, 0) + 1
    first = max(counts.items(), key=lambda kv: kv[1])[0] if counts else "none"
    # The sharpest form of the finding: items where the covenant survives the
    # ENTIRE range while another test has already failed. On those the covenant
    # is not a loose constraint, it is not a constraint at all.
    never = [t for t in binding if t.covenant_pct is not None and t.covenant_pct >= 1.0]
    thin = binding[0] if binding else None
    gap = None
    if thin is not None and thin.covenant_pct is not None:
        gap = thin.covenant_pct - thin.absorbed_pct
    return {
        "binds": len(binding),
        "absorb_everything": sum(1 for t in tols
                                 if t.absorbed_pct is not None and t.absorbed_pct >= 1.0),
        "counts": counts,
        "first_to_fail": first,
        "unanimous": len(counts) == 1 and bool(counts),
        "thinnest": thin,
        "covenant_never_breaks": len(never),
        "thinnest_gap_pct": gap,
    }


# =============================================================================
# survival -- how many can go wrong at once
# =============================================================================

def survival(cfg: dict[str, Any], land_price: float, premium: float = 0.0,
             horizon: int = 12, order: list[str] | None = None,
             depth: int = 5) -> dict[str, Any]:
    """
    Compound adverse answers, largest first, and report where the deal stops.

    This is the question the per-item table cannot answer, and the one a
    committee asks immediately: fine, but what if two of these go against us?

    It is NOT a probability statement and the register must not be read as one.
    Every rung is an adverse end by construction, so the walk describes a joint
    tail, not an expectation -- the same distinction the project already enforces
    between a correlated scenario and a one-at-a-time tornado flex.

    The walk runs a FIXED number of rungs rather than stopping at the first
    failure, because the point of the last rung is the additivity check, and a
    walk that halts as soon as it breaks can only ever compare one item's
    downside against itself. Past the break the coverage ratio and the multiple
    stop meaning anything individually; what they still say, correctly, is that
    the equity is gone.
    """
    run = _runner(cfg, land_price, horizon)
    priced = price(cfg, land_price, premium, horizon)
    ranked = [p.item.id for p in priced if p.downside_bps]
    ids = (order or ranked)[:depth]
    items = {i.id: i for i in register(cfg, premium)}
    by_id = {p.item.id: p for p in priced}

    cf, rep = run(cfg, premium)
    steps = [Step("base case", cf.equity_irr, rep["min_dscr_tested"],
                  cf.equity_multiple, cf.value_to_cost, run.clears(cfg, premium))]

    c, pm = cfg, premium
    breaking_point: int | None = None
    for n, iid in enumerate(ids, start=1):
        span = items[iid].flex
        if span is None:
            continue
        c, pm = span(c, pm, "adv")
        cf, rep = run(c, pm)
        clears = bool(rep["passes_every_year"] and cf.equity_irr is not None
                      and cf.equity_irr > 0 and cf.value_to_cost >= 1.0)
        steps.append(Step(iid, cf.equity_irr, rep["min_dscr_tested"],
                          cf.equity_multiple, cf.value_to_cost, clears))
        if not clears and breaking_point is None:
            breaking_point = n - 1        # adverse answers survived before this one

    # Additivity is the trap. The per-item downsides are each measured from the
    # same base case, so adding them double-counts every interaction between
    # them -- and quoting the sum as a joint downside would put a number in front
    # of a committee that nobody can reproduce from the model.
    walked = [s.added for s in steps[1:]]
    parts = sum(by_id[i].downside_bps for i in walked
                if by_id[i].downside_bps not in (None, float("inf")))
    joint = steps[-1]
    joint_bps = (float("inf") if joint.irr is None
                 else (steps[0].irr - joint.irr) * 10_000)

    return {
        "steps": steps,
        "walked": walked,
        "breaking_point": len(ids) if breaking_point is None else breaking_point,
        "sum_of_parts_bps": parts,
        "joint_bps": joint_bps,
        "additive": joint_bps != float("inf") and abs(joint_bps - parts) < 50,
        "total_loss": joint.equity_multiple <= 0.01,
        "order": ids,
    }


# =============================================================================
# Reconciliation against the ask
# =============================================================================

def reconcile(cfg: dict[str, Any]) -> dict[str, Any]:
    """
    Check the register against the Tranche 1 budget in both directions.

    A register that spends money the ask does not contain is asking the committee
    for the wrong number. An ask carrying a line no numbered question claims is a
    line nobody has to justify. Both are reported.
    """
    budget = ts.tranche_1_budget(cfg)
    lines = {i["name"]: float(i["usd"]) for i in budget["items"]}
    claimed: dict[str, float] = {}
    orphans: list[tuple[str, str, float]] = []

    for item in register(cfg):
        if item.tranche_line is None:
            if item.cost_usd > 0:
                orphans.append((item.id, "(no line)", item.cost_usd))
            continue
        if item.tranche_line not in lines:
            orphans.append((item.id, item.tranche_line, item.cost_usd))
            continue
        claimed[item.tranche_line] = claimed.get(item.tranche_line, 0.0) + item.cost_usd

    mismatched = [(name, claimed[name], lines[name])
                  for name in claimed if abs(claimed[name] - lines[name]) > 1.0]
    unclaimed = [(n, v) for n, v in lines.items()
                 if n not in claimed and n not in NOT_A_QUESTION]

    return {
        "budget_subtotal": budget["subtotal"],
        "budget_total": budget["total"],
        "register_cost": sum(claimed.values()),
        "orphan_items": orphans,
        "mismatched_lines": mismatched,
        "unclaimed_lines": unclaimed,
        "excluded_lines": [(n, lines[n]) for n in lines if n in NOT_A_QUESTION],
        "clean": not orphans and not mismatched and not unclaimed,
    }


def summary(priced: list[Priced]) -> dict[str, Any]:
    breakers = [p for p in priced if p.breaks_covenant]
    finite = [p for p in priced
              if p.downside_bps is not None and p.downside_bps != float("inf")]
    fatal = [p for p in priced if p.downside_bps == float("inf")]
    return {
        "items": len(priced),
        "priced": sum(1 for p in priced if p.downside_bps is not None),
        "unpriced": sum(1 for p in priced if p.downside_bps is None),
        "covenant_breakers": len(breakers),
        "fatal_items": len(fatal),
        "total_cost": sum(p.item.cost_usd for p in priced),
        "free_items": sum(1 for p in priced if p.item.cost_usd == 0),
        "costed": sum(1 for p in priced if p.item.cost_usd > 0),
        "longest_weeks": max((p.item.weeks for p in priced), default=0),
        "largest_downside_bps": max((p.downside_bps for p in finite), default=0.0),
        "free_downside_bps": sum(p.downside_bps for p in finite if p.item.cost_usd == 0),
        "cheapest_breaker": min(breakers, key=lambda p: p.item.cost_usd) if breakers else None,
        "best_value": max(finite, key=lambda p: p.bps_per_100k or 0.0) if finite else None,
    }
