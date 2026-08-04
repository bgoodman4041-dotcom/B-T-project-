"""
TRACK BOSS — Roadmap, Platform Scale, and Exit Path
===================================================

Three questions this answers, in the order an investor asks them:

  1. **What happens, and when?** A milestone schedule from month 1 to year 10,
     with the gate that must clear at each and the KPI that proves it did.
     Timing is DERIVED from the underwriting -- construction period,
     stabilisation year, sell-out -- so the roadmap cannot drift from the model.

  2. **Does this reach public-market scale?** Tested, not asserted. A single
     club stabilises with under $10M of NOI and roughly $170M of asset value.
     No issuer of that size and concentration lists. The question is whether a
     PLATFORM reaches scale, and by which growth route.

  3. **If not an IPO, then what?** A ranked ladder of realistic exits with the
     conditions each requires.

The uncomfortable arithmetic, stated up front: on a ground-up path the first
club does not stabilise until roughly month 123. Year 10 is the month the first
asset finishes ramping -- it is not a plausible listing date for a company that
still owns one thing. Reaching listing scale by year 10 requires the platform to
grow by ACQUIRING existing facilities, which is a different strategy with
different skills, not an acceleration of this one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import cashflow as cf_mod
from . import two_stack as ts


# =============================================================================
# Derived programme timing
# =============================================================================

@dataclass
class Timing:
    feasibility_months: int
    entitlement_months: int
    construction_months: int
    opening_month: int
    stabilisation_month: int
    sellout_months: int
    stabilisation_op_year: int

    @property
    def opening_year(self) -> float:
        return self.opening_month / 12.0

    @property
    def stabilisation_year(self) -> float:
        return self.stabilisation_month / 12.0


def timing(cfg: dict[str, Any]) -> Timing:
    rd = cfg["roadmap"]
    dev_months = int(round(cfg["cost"]["carry"]["development_years"] * 12))
    stab_op_year = ts.stabilization_year(cfg)
    ent = rd["entitlement_months"]
    opening = ent + dev_months
    fs = ts.project_for_sale(cfg)
    return Timing(
        feasibility_months=rd["feasibility_months"],
        entitlement_months=ent,
        construction_months=dev_months,
        opening_month=opening,
        stabilisation_month=opening + stab_op_year * 12,
        sellout_months=int(round(fs.sellout_years * 12)),
        stabilisation_op_year=stab_op_year,
    )


# =============================================================================
# Milestones
# =============================================================================

@dataclass
class Milestone:
    horizon: str
    month: int
    phase: str
    objective: str
    deliverables: list[str]
    gate: str
    kpi: str
    capital: str

    @property
    def deliverable_text(self) -> str:
        return " · ".join(self.deliverables)


HORIZONS = [
    ("1 month", 1), ("3 months", 3), ("6 months", 6), ("1 year", 12),
    ("18 months", 18), ("2 years", 24), ("3 years", 36), ("5 years", 60),
    ("7 years", 84), ("10 years", 120),
]


def milestones(cfg: dict[str, Any]) -> list[Milestone]:
    """
    The ten horizons the principal asked for, each anchored to where the derived
    programme timing actually puts it. Phase labels are computed, not asserted,
    so a change to the construction period re-labels the schedule.
    """
    T = timing(cfg)
    m = cfg["income"]["membership"]
    cap = m["cap"]

    def phase_at(month: int) -> str:
        if month <= T.feasibility_months:
            return "Phase 0 — Feasibility"
        if month <= T.entitlement_months:
            return "Phase 1 — Entitlement"
        if month <= T.opening_month:
            return "Phase 2 — Construction"
        if month <= T.stabilisation_month:
            return "Phase 3 — Lease-up"
        return "Phase 4 — Stabilised hold / platform"

    # Membership at a given month, from the actual ramp.
    sched = ts.membership_schedule(cfg, 20)

    def members_at(month: int) -> int:
        if month <= T.opening_month:
            return 0
        op_year = min(len(sched), max(1, int((month - T.opening_month) / 12) + 1))
        return sched[op_year - 1]

    spec: list[tuple[str, str, list[str], str, str, str]] = [
        # 1 month
        ("Mandate and mobilisation",
         ["Comparable club study commissioned",
          "Sourcing brief issued to Parcel Scout across NY/CT/NJ",
          "Entitlement counsel and acoustic consultant shortlisted",
          "Tranche 1 closed and escrowed"],
         "Tranche 1 funded",
         "Study engaged; sourcing brief live",
         "Tranche 1"),
        # 3 months
        ("Revenue truth-test",
         ["Comparable club economics delivered: initiation ceiling, dues, "
          "condo $/SF against local flex, realised absorption",
          "Model re-based against verified comps",
          "150+ parcel universe assembled; Gates 1-2 run"],
         "HARD GATE — if verified comps materially undercut the assumption base, "
          "the programme stops here and the balance of Tranche 1 is released",
         "Assumption register moves from ASSUMED to VERIFIED on revenue",
         "Tranche 1"),
        # 6 months
        ("Site shortlist and control path",
         ["Gates 3-5 complete; universe cut to a ranked shortlist of two",
          "Acoustic pre-model against the actual municipal standard",
          "Phase I environmental ordered on both finalists",
          "LOI negotiated; option terms agreed in principle"],
         "Two sites with identifiers, coordinates and clean title review",
         "Shortlist of 2 with signed LOIs",
         "Tranche 1"),
        # 1 year
        ("Control secured",
         ["Option executed on the lead site — entitlement-contingent, extension "
          "fees credited to purchase price",
          "Municipal pre-application meeting held",
          "IDA/EDA abatement conversation opened",
          "Boundary, topographic and geotechnical survey complete"],
         "Site under option WITHOUT acquisition risk",
         "Executed option; pre-application on record",
         "Tranche 1"),
        # 18 months
        ("Application filed",
         ["Special permit or map amendment application filed",
          "Environmental review underway (SEQRA or CEPA)",
          "Wetlands delineation and permitting commenced",
          "Founding-member programme soft-launched to a curated list",
          "Circuit design to 60% and GMP pricing conversation opened"],
         "Application accepted as complete",
         "Founding-member expressions of interest against the ramp",
          "Tranche 1"),
        # 2 years
        ("Hearings and pricing",
         ["Public hearings underway; opposition mapped and answered",
          "Abatement term sheet agreed",
          "Guaranteed maximum price negotiated with the general contractor",
          "Construction and permanent lender term sheets received",
          "Founding-member deposits held in escrow"],
         "Abatement term sheet and lender commitments in hand",
         "Pre-sale and founding-member deposits versus the waterfall assumption",
         "Tranche 1"),
        # 3 years
        ("Permit, close, break ground",
         ["Permit issued and appeal period run",
          "Abatement agreement executed",
          "SEVEN CONDITIONS PRECEDENT satisfied; Tranche 2 called",
          "Land closing and construction start",
          "Site 2 entitlement commenced in parallel"],
         "HARD GATE — Tranche 2 draws only on all seven conditions",
         "Permit issued; land closed; construction facility drawn",
         "Tranche 2"),
        # 5 years
        ("Vertical delivery and pre-sales",
         ["Circuit and paddock complete; clubhouse and service centre topped out",
          "First garage-condominium building delivered; closings commence",
          "Membership sales at full pace against the ramp",
          "Site 2 permitted; site 3 under option"],
         "Construction on programme and on budget",
         "Condominium closings and membership count versus plan",
         "Tranche 2"),
        # 7 years
        ("Open and ramp",
         ["Club open and operating",
          "Membership ramping toward cap; dues escalation live",
          "Homesite closings underway",
          "Site 2 under construction — platform of two in delivery"],
         "Opening on schedule; operating ratio inside the plausible band",
         "Members on-boarded; operating ratio; DSCR from conversion",
         "Tranche 2 / recycled"),
        # 10 years
        ("Stabilisation and the platform decision",
         [f"Club 1 stabilised at {cap} members; permanent loan converted",
          "Sell-out substantially complete; construction facility retired",
          "Club 2 open and ramping; club 3 in construction",
          "Platform decision: continue ground-up, pivot to acquisition, "
          "recapitalise, or sell"],
         "Stabilised operating history on asset 1; covenant holding",
         "Stabilised NOI, DSCR, value against retained cost, platform NOI",
         "Recycled / platform capital"),
    ]

    out: list[Milestone] = []
    for (label, month), (obj, deliv, gate, kpi, capital) in zip(HORIZONS, spec):
        out.append(Milestone(
            horizon=label, month=month, phase=phase_at(month), objective=obj,
            deliverables=deliv, gate=gate, kpi=kpi, capital=capital,
        ))
    return out


# =============================================================================
# Platform scale
# =============================================================================

@dataclass
class PlatformPoint:
    clubs: int
    stabilised_noi: float
    asset_value: float
    cumulative_dev_cost: float


def platform_scale(cfg: dict[str, Any], land_price: float, premium: float = 0.0,
                   max_clubs: int = 8) -> list[PlatformPoint]:
    """
    Scale economics by club count, holding the unit economics of the base case.
    Deliberately linear: it does not assume platform G&A leverage or a portfolio
    cap-rate premium, both of which would flatter the answer without evidence.
    """
    uw = ts.underwrite(cfg, "PLAT", ask_price=land_price, site_cost_premium=premium)
    cf = cf_mod.project_cash_flow(cfg, land_price, horizon_operating_years=12,
                                  site_cost_premium=premium)
    noi = uw.stabilized_noi_after_tax
    value = cf.exit_net_proceeds
    cost = uw.cost.gross_basis(land_price)
    return [PlatformPoint(n, noi * n, value * n, cost * n)
            for n in range(1, max_clubs + 1)]


@dataclass
class ListingTest:
    clubs_required_by_noi: int
    clubs_required_by_value: int
    clubs_required_by_diversification: int
    clubs_required: int
    ground_up_month: int
    ground_up_year: float
    acquisition_month: int
    acquisition_year: float
    listable_by_year_10: bool
    verdict: str
    thresholds: dict[str, Any] = field(default_factory=dict)


def listing_readiness(cfg: dict[str, Any], land_price: float,
                      premium: float = 0.0) -> ListingTest:
    """
    Answer the IPO question with arithmetic instead of optimism.

    Two growth routes are timed:

    * **Ground-up** — each additional club is entitled and built from scratch,
      started `ground_up_stagger_months` after the previous one. The binding
      constraint is that the LAST club still needs the full entitlement,
      construction and lease-up cycle.
    * **Acquisition** — clubs 2..N are existing facilities bought and
      repositioned, reaching stabilised contribution in
      `acquisition_ramp_months`. Far faster, and a different business.
    """
    th = cfg["listing_thresholds"]
    T = timing(cfg)
    rd = cfg["roadmap"]
    scale = platform_scale(cfg, land_price, premium, max_clubs=20)

    def first_n(pred) -> int:
        for p in scale:
            if pred(p):
                return p.clubs
        return 999

    by_noi = first_n(lambda p: p.stabilised_noi >= th["min_recurring_noi_usd"])
    by_val = first_n(lambda p: p.asset_value >= th["min_equity_value_usd"])
    by_div = th["min_stabilised_assets"]
    need = max(by_noi, by_val, by_div)

    # Ground-up: club n starts (n-1)*stagger after club 1 and stabilises a full
    # cycle later. Listing also needs operating history on the first asset.
    gu = T.stabilisation_month + (need - 1) * rd["ground_up_stagger_months"]
    gu = max(gu, T.stabilisation_month + th["min_operating_history_years"] * 12)

    # Acquisition: club 1 is ground-up; the rest are bought once club 1 opens
    # and proves the model, each stabilising after the acquisition ramp.
    acq = max(
        T.opening_month + rd["acquisition_ramp_months"] + (need - 2) * 12,
        T.stabilisation_month + th["min_operating_history_years"] * 12,
    )

    listable = acq <= 120
    if need > 12:
        verdict = (
            f"NO CREDIBLE LISTING PATH. Reaching the "
            f"${th['min_recurring_noi_usd'] / 1e6:.0f}M recurring-NOI threshold would "
            f"require {need} clubs, which is beyond any plausible build or buy "
            f"programme. Plan for a strategic sale or recapitalisation.")
    elif listable:
        verdict = (
            f"LISTING IS REACHABLE BY YEAR 10, BUT ONLY BY ACQUISITION. "
            f"{need} stabilised assets are needed to clear the thresholds. Built "
            f"ground-up at a {rd['ground_up_stagger_months']}-month cadence that "
            f"lands in year {gu / 12:.0f}; grown by acquiring existing facilities "
            f"after club 1 opens it lands in year {acq / 12:.0f}. Ground-up alone "
            f"does not get there.")
    else:
        verdict = (
            f"NOT LISTABLE BY YEAR 10 ON EITHER ROUTE. {need} stabilised assets "
            f"are needed. Ground-up reaches that in year {gu / 12:.0f}; even an "
            f"acquisition-led platform reaches it in year {acq / 12:.0f}. Year 10 "
            f"is when club 1 finishes ramping, not when a platform lists. The "
            f"earliest credible route is acquisition-led at year {acq / 12:.0f}; "
            f"treat a listing as a year-{acq / 12:.0f} stretch outcome, plan the "
            f"platform for it, and underwrite to a strategic sale or "
            f"recapitalisation in the meantime.")

    return ListingTest(
        clubs_required_by_noi=by_noi, clubs_required_by_value=by_val,
        clubs_required_by_diversification=by_div, clubs_required=need,
        ground_up_month=gu, ground_up_year=gu / 12.0,
        acquisition_month=acq, acquisition_year=acq / 12.0,
        listable_by_year_10=listable, verdict=verdict, thresholds=dict(th),
    )


# =============================================================================
# Exit ladder
# =============================================================================

@dataclass
class ExitPath:
    rank: int
    route: str
    timing: str
    proceeds_basis: str
    requires: str
    assessment: str


def exit_paths(cfg: dict[str, Any], land_price: float,
               premium: float = 0.0) -> list[ExitPath]:
    """Ranked by probability of actually happening, not by headline proceeds."""
    T = timing(cfg)
    cf = cf_mod.project_cash_flow(cfg, land_price, horizon_operating_years=12,
                                  site_cost_premium=premium)
    lt = listing_readiness(cfg, land_price, premium)
    exit_cap = cfg["income"]["exit_cap"]

    return [
        ExitPath(1, "For-sale closings (self-liquidating)",
                 f"Years {T.opening_year:.0f}–{(T.opening_month + T.sellout_months) / 12:.0f}",
                 f"${cf.sources_uses.for_sale_net_proceeds / 1e6:,.0f}M of net proceeds",
                 "Delivery and absorption only — no capital-markets event",
                 "HIGHEST CERTAINTY. Returns the majority of invested capital "
                 "independent of any exit market. This is why the programme is "
                 "structured as a merchant build."),
        ExitPath(2, "Member capital (non-dilutive)",
                 f"Years 2–{T.stabilisation_year:.0f}",
                 f"${cf.sources_uses.initiation_cash / 1e6:,.0f}M of initiation fees",
                 "Membership sales against the ramp",
                 "HIGH CERTAINTY once the club is credible. Collected as the "
                 "club fills and never repaid."),
        ExitPath(3, "Refinance of the stabilised club",
                 f"Year {T.stabilisation_year:.0f}+",
                 "Permanent debt sized on stabilised NOI",
                 "Stabilised operating history and covenant compliance",
                 "PROBABLE. Note the negative-leverage finding: refinancing is a "
                 "liquidity tool here, not a return enhancer, and should not be "
                 "sized to the maximum available."),
        ExitPath(4, "Strategic sale of the retained club",
                 f"Year {T.stabilisation_year:.0f}–12",
                 f"${cf.exit_net_proceeds / 1e6:,.0f}M at a {exit_cap:.2%} cap",
                 "A buyer for single-asset special-purpose recreational property",
                 "REALISTIC BUT THIN. Buyer universe is family offices, club "
                 "operators and member-buyout vehicles, not institutional core "
                 f"capital. Break-even cap is {cf.breakeven_exit_cap:.2%}; beyond "
                 f"that the club is worth less than it cost to keep."),
        ExitPath(5, "Member buyout / equity club conversion",
                 f"Year {T.stabilisation_year:.0f}+",
                 "Negotiated, typically at or near the refinance value",
                 "A cohesive, capitalised membership",
                 "UNDERRATED. The standard end-state for private golf and country "
                 "clubs and a genuine alternative when no third-party bid clears."),
        ExitPath(6, "Platform recapitalisation",
                 f"Year {min(10, T.stabilisation_year + 2):.0f}+",
                 "Institutional capital into a multi-asset holding company",
                 f"{lt.clubs_required_by_diversification}+ assets and a proven "
                 f"operating platform",
                 "PLAUSIBLE IF THE PLATFORM IS BUILT. Requires the second and "
                 "third clubs, which requires club 1 to prove the model first."),
        ExitPath(7, "Initial public offering",
                 f"Year {lt.acquisition_year:.0f}+ (acquisition-led) / "
                 f"year {lt.ground_up_year:.0f}+ (ground-up)",
                 f"Requires ${lt.thresholds['min_equity_value_usd'] / 1e6:,.0f}M+ "
                 f"equity value and ${lt.thresholds['min_recurring_noi_usd'] / 1e6:,.0f}M+ "
                 f"recurring NOI",
                 f"{lt.clubs_required} stabilised assets, {lt.thresholds['min_operating_history_years']}+ "
                 f"years of audited operating history, and a platform management team",
                 "STRETCH OUTCOME, NOT A PLAN. " + lt.verdict),
    ]
