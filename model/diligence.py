"""
TRACK BOSS — Diligence Register, ranked by how much the answer moves
====================================================================

The package names roughly fifty open items across the comparable study, the
jurisdiction register, the risk register and the source register. Scattered like
that they are a to-do list, and a to-do list is not a diligence plan: it does not
say what to do first, and it does not say what any of it is worth.

This consolidates them and prices each one the only way that is defensible —
by flexing the model over the range the item is uncertain across and measuring
what happens to the governing tests. Two numbers come out per item:

    irr_swing_bps     equity IRR at the favourable end minus the adverse end
    breaks_covenant   whether the adverse end drops coverage below the floor

Then the ranking that matters:

    bps_per_100k      IRR swing bought per $100,000 of diligence spend

That last column is the whole point. The comparable club study costs $285,000
and moves the answer more than everything else combined. A noise ordinance in a
county we may never buy in costs a phone call and moves nothing until we are
under option there. Both are worth doing; only one is worth doing first, and
until now nothing in the package said so.

WHAT THIS IS NOT
----------------
It is not a claim that the adverse end is likely. The range is the honest span
of what the item could turn out to be, and the swing is what is at stake in
finding out. An item with a large swing is not a problem — it is a question
worth the money to answer, which is exactly what a feasibility budget buys.

Items with no model driver — a title search, a records request, an acoustic
model — carry a swing of None rather than a guessed one. They are ranked by the
gate they clear instead, and the register says which.

THE SITE COST PREMIUM IS A FLEXED INPUT, NOT A FIXED ONE
--------------------------------------------------------
The single most-argued number in the programme is the lead site's −$9.5M
pavement credit, and it lives in `site_cost_premium`, not in the config. A
flexer that could only reach the config would have left the biggest question in
the package unpriced, so every flexer takes and returns the premium as well.

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

# A flexer maps (cfg, premium, end) -> (cfg, premium) for end in {"fav", "adv"}.
Flex = Callable[[dict[str, Any], float, str], tuple[dict[str, Any], float]]

# One Tranche 1 line is not a question and never will be. Naming it here keeps
# the reconciliation honest rather than letting it drift into a rounding note.
NOT_A_QUESTION = {"Sponsor overhead and programme management"}


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
    flex: Flex | None = None
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


# =============================================================================
# The flexers
# =============================================================================
# A scenario factor where one exists, a direct config edit where it does not,
# and the site cost premium where the question is about the dirt. Every range is
# the honest span between the evidence's answer and the configured assumption --
# not a stress, just the width of what is unknown.

def _factor(name: str, fav: float, adv: float) -> Flex:
    def _f(cfg: dict[str, Any], prem: float, end: str):
        return sc.apply_scenario(cfg, {name: fav if end == "fav" else adv}), prem
    return _f


def _set(path: tuple[str, ...], fav: Any, adv: Any) -> Flex:
    def _f(cfg: dict[str, Any], prem: float, end: str):
        c = copy.deepcopy(cfg)
        node = c
        for k in path[:-1]:
            node = node[k]
        node[path[-1]] = fav if end == "fav" else adv
        return c, prem
    return _f


def _scale(path: tuple[str, ...], fav: float, adv: float) -> Flex:
    """Scale every numeric leaf of a config subtree. For unbid cost blocks."""
    def _f(cfg: dict[str, Any], prem: float, end: str):
        c = copy.deepcopy(cfg)
        node = c
        for k in path[:-1]:
            node = node[k]
        f = fav if end == "fav" else adv
        node[path[-1]] = {k: (v * f if isinstance(v, (int, float)) else v)
                          for k, v in node[path[-1]].items()}
        return c, prem
    return _f


def _premium(fav: Callable[[float], float], adv: Callable[[float], float]) -> Flex:
    """
    Flex the site cost premium, which is a per-site argument rather than config.

    Both ends are functions of the site's own premium so one register serves
    every site: EPCAL carries a credit and Pinal carries a charge, and "write
    the credit off" has to mean something different on each.
    """
    def _f(cfg: dict[str, Any], prem: float, end: str):
        return cfg, (fav(prem) if end == "fav" else adv(prem))
    return _f


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
    ne_dues, ne_init = 18_500.0, 125_000.0
    comp_psf = 348.0
    ent_assumed, ent_researched = 33, 45          # months, EPCAL, jurisdiction register
    # A credit can evaporate and a premium can only be bid against, so only the
    # credit direction is priceable here. On a site that already carries a
    # charge the Phase II can confirm it or make it worse, and by how much is
    # exactly what the study is for -- guessing a multiplier would be inventing
    # the answer the item exists to buy.
    prem_note = (f"a ${abs(premium) / 1e6:,.1f}M cost credit, or zero" if premium < 0
                 else f"a ${premium / 1e6:,.1f}M charge — confirmed, or worse by an "
                      f"amount only the study can state")
    prem_flex = _premium(lambda p: p, lambda p: 0.0) if premium < 0 else None

    return [
        Item("DD-01", "Revenue",
             f"Will members pay ${m['annual_dues_usd']:,.0f} a year where buying real "
             f"estate is optional? The comparable set's ceiling outside a "
             f"mandatory-purchase club or invitation-only Miami is ${ne_dues:,.0f}.",
             "Everything. It is the largest single input to NOI.",
             "Hospitality/club consultancy + direct calls to MMC, NJMP, Apex, AMP",
             285_000, 10, "comps_findings.md §1, §3",
             _factor("dues_factor", 1.0, ne_dues / m["annual_dues_usd"]),
             f"${ne_dues:,.0f} to ${m['annual_dues_usd']:,.0f} a year",
             "Comparable club economics study"),

        Item("DD-02", "Revenue",
             f"Is the ${m['initiation_fee_usd']:,.0f} initiation collectable, and is any "
             f"of it REFUNDABLE? The reference asset is reported to refund 70% on exit, "
             f"which would make most of it a liability rather than income.",
             "NOI and the funding waterfall — initiation is the deepest source of "
             "cash during the equity trough.",
             "Direct call: Monticello, Concours and Thermal membership offices",
             0, 2, "comps_findings.md §1 (refundable deposit)",
             _set(("income", "initiation_treatment", "refundable_share"), 0.0, 0.70),
             "0% to 70% refundable", None),

        Item("DD-03", "Revenue",
             f"Does the Northeast initiation ceiling of ${ne_init:,.0f} hold? It rests "
             f"on ONE AI-generated wiki entry about ONE club, with a five-fold gap to "
             f"the next observation in the set.",
             "The initiation line, and the credibility of the whole comp register.",
             "Monticello Motor Club membership office",
             0, 1, "comps_findings.md §2",
             _factor("initiation_factor", 1.0, ne_init / m["initiation_fee_usd"]),
             f"${ne_init:,.0f} to ${m['initiation_fee_usd']:,.0f}", None),

        Item("DD-04", "For-sale",
             f"Will garage condominiums sell at ${condo['sale_price_psf']:,.0f}/SF? The "
             f"two operating new-build track comps price at $344-352 — which is this "
             f"model's assumed HARD COST, before the 1.298x soft and contingency load.",
             "The for-sale stack, which funds the build and sets the carry.",
             "Residential/flex market study + a Suffolk industrial broker on trades",
             175_000, 8, "comps_findings.md §4",
             _factor("condo_psf_factor", 1.0, comp_psf / condo["sale_price_psf"]),
             f"${comp_psf:,.0f} to ${condo['sale_price_psf']:,.0f}/SF",
             "Market and absorption study for the for-sale stack"),

        Item("DD-05", "For-sale",
             f"Can {condo['absorption_units_per_year']} units a year be absorbed? M1 "
             f"realised 17.5 and NJMP delivered 10-15 across nine phases in fifteen "
             f"years — and NJMP is the closest structural Northeast analogue there is.",
             "Carry. Sell-out sets the carry period in a merchant build.",
             "NJMP phase records + county recorder (inside the DD-04 study scope)",
             0, 4, "comps_findings.md §7",
             _factor("absorption_slowdown", 1.0, condo["absorption_units_per_year"] / 15),
             f"{condo['absorption_units_per_year']} units/yr to 15", None),

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
             _factor("abatement_pct", pt["abatement_pct"], 0.0),
             f"{pt['abatement_pct']:.0%} to 0% abatement",
             "Property tax abatement negotiation"),

        Item("DD-08", "Cost",
             "Is the circuit and vertical hard cost right? Nothing in the package is a "
             "bid; the whole cost stack is benchmark-derived.",
             "The basis, and therefore every yield and coverage figure.",
             "General contractor — budget pricing to a GMP-track estimate",
             0, 10, "config cost block, all ASSUMED",
             _factor("hard_cost_factor", 0.92, 1.15),
             "-8% to +15% on hard cost", None),

        Item("DD-09", "Operations",
             "Will a club operator run this at the modelled operating ratio? No operator "
             "is appointed and the ratio drives the covenant.",
             "The covenant, and a condition precedent to construction capital.",
             "Operator search and management agreement (sponsor time, not a vendor)",
             0, 20, "plan §10 — role OPEN",
             _factor("opex_factor", 0.94, 1.16),
             "-6% to +16% on club opex", None),

        Item("DD-10", "Market",
             f"Can {m['cap']} members actually be recruited at this price? Every rate in "
             f"the demand funnel — collector share, track-active share, incumbent "
             f"capture — is judgment, not measured conversion.",
             "Whether the ramp is achievable at all, and the club's size.",
             "Founding-member campaign with a paid waitlist — measured conversion",
             240_000, 24, "model/demand.py — all rates ASSUMED",
             _factor("cap_factor", 1.0, 0.80),
             f"{m['cap']} members achieved, or {int(m['cap'] * 0.8)}",
             "Founding-member demand testing"),

        Item("DD-11", "Season",
             "Is 210 usable days right for the lead site? The only published Northeast "
             "facility figure in the comp set is 150 days, at a materially colder site.",
             "Ancillary revenue, and the ranking of every Sun Belt site against it.",
             "Operator calendars + a climate-hours analysis",
             0, 3, "comps_findings.md §6",
             _set(("income", "season_days"), 210, 180),
             "210 usable days to 180", None),

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
             "Will a 7.25% exit cap clear for a special-purpose recreational asset with "
             "a thin buyer universe?",
             "Terminal value, which is where most of the equity return sits.",
             "Broker opinion of value from two national capital-markets teams",
             0, 6, "config income.exit_cap — ASSUMED",
             _factor("exit_cap_bps", -50, 150),
             "-50 bp to +150 bp on the exit cap", None),

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
             _scale(("cost", "site_infrastructure_usd"), 0.85, 1.25),
             "-15% to +25% on site infrastructure",
             "Survey, geotechnical and cut/fill validation"),

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
             _set(("cost", "entitlement_budget_usd"),
                  cfg["cost"]["entitlement_budget_usd"],
                  cfg["cost"]["entitlement_budget_usd"] * ent_researched / ent_assumed),
             f"{ent_assumed} months to {ent_researched}",
             "Entitlement counsel and municipal strategy"),

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


# =============================================================================
# Pricing
# =============================================================================

def price(cfg: dict[str, Any], land_price: float, premium: float = 0.0,
          horizon: int = 12) -> list[Priced]:
    """
    Flex each item across its uncertainty range and measure the governing tests.

    The favourable end is normally the configured assumption -- the model already
    believes it -- and the adverse end is what the evidence suggests it might be
    instead. The swing between them is what the diligence buys knowledge of.
    """
    floor = cfg["debt"]["min_dscr"]
    dev = int(round(cfg["cost"]["carry"]["development_years"]))

    def run(c: dict[str, Any], prem: float) -> tuple[float | None, float | None]:
        cf = cf_mod.project_cash_flow(c, land_price, horizon_operating_years=horizon,
                                      site_cost_premium=prem)
        rep = cf_mod.covenant_report(cf, floor,
                                     tested_from_year=dev + ts.stabilization_year(c))
        return cf.equity_irr, rep["min_dscr_tested"]

    irr_base, _ = run(cfg, premium)

    out: list[Priced] = []
    for item in register(cfg, premium):
        if item.flex is None:
            out.append(Priced(item, None, None, None, None, None, None, None,
                              f"No model driver — {item.gates}"))
            continue
        irr_f, _ = run(*item.flex(cfg, premium, "fav"))
        irr_a, dscr_a = run(*item.flex(cfg, premium, "adv"))

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
