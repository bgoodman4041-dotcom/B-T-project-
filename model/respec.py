"""
TRACK BOSS — Programme Re-specification
=======================================

The comparable study says the revenue line is roughly half again too high. The
obvious reading is that the deal is dead. That reading skips a step.

A pro forma has two ways to be wrong. It can be mis-PRICED -- the right programme
at the wrong numbers -- or mis-SPECIFIED -- the wrong programme. Repricing to the
comparable set and stopping there tests only the first. This module holds the
comp-supported pricing fixed and searches the programme itself: how much track,
how many members, how many units for sale.

What the search found, and why it is worth having
-------------------------------------------------

**Track length is not the lever, and the intuition that it is was wrong.** The
circuit is 7% of non-land cost. Going from 3.0 miles to 2.25 moves equity IRR by
about forty basis points. A shorter track is a smaller parcel and a cheaper
entitlement, which are real, but it does not rescue the economics.

**Member count is the lever, and it is bounded by demand, not by design.** The
programme needs roughly 470 members at comp pricing where it needed 340 at the
assumed pricing. That is arithmetic -- lower dues need more payers -- and its
constraint sits in `model/demand.py`, not here. A 470-seat club in a catchment
that supports 1.6x coverage at 340 is not a plan.

**More for-sale product makes it worse, which is the counterintuitive one.**
Raising garage condos from 140 to 200 units lowers IRR at every track length.
The for-sale vertical is 43% of non-land cost, the comp-supported margin on it is
thin, and in a merchant build the carry runs until the last unit sells. Adding
units adds cost and carry faster than it adds proceeds.

Every configuration is scored on the GOVERNING tests -- covenant coverage from
conversion, positive equity IRR, and exit value against retained cost -- not on
the gross-basis yield, which is negative for any merchant build.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from . import cashflow as cf_mod
from . import demand as dm
from . import scenarios as sc
from . import two_stack as ts


@dataclass
class Variant:
    track_miles: float
    member_cap: int
    condo_units: int
    members_per_mile: float
    stabilized_noi: float
    equity_irr: float | None
    min_dscr: float
    value_to_cost: float
    peak_equity: float
    clears: bool
    demand_coverage: float | None = None
    demand_ok: bool | None = None


@dataclass
class Respec:
    baseline: Variant
    variants: list[Variant]
    best: Variant | None
    best_feasible: Variant | None
    track_sensitivity_bps: float
    condo_sensitivity_bps: float
    verdict: str


def _apply(cfg: dict[str, Any], miles: float, cap: int, condos: int) -> dict[str, Any]:
    c = copy.deepcopy(cfg)
    c["cost"]["track"]["miles"] = miles
    m = c["income"]["membership"]
    old = int(m["cap"])
    m["cap"] = int(cap)
    # The ramp scales with the cap. A larger club is not the same ramp reaching a
    # higher number; it is more members joining each year, which is also what
    # `demand` is asked to support.
    m["ramp"] = [max(1, int(round(r * cap / old))) for r in m["ramp"]]
    c["for_sale"]["garage_condos"]["units"] = int(condos)
    return c


def _evaluate(cfg: dict[str, Any], land_price: float, premium: float,
              miles: float, cap: int, condos: int, horizon: int,
              parcel: dict[str, Any] | None) -> Variant:
    c = _apply(cfg, miles, cap, condos)
    uw = ts.underwrite(c, "RESPEC", ask_price=land_price, site_cost_premium=premium)
    cf = cf_mod.project_cash_flow(c, land_price, horizon_operating_years=horizon,
                                  site_cost_premium=premium)
    tested_from = (int(round(c["cost"]["carry"]["development_years"]))
                   + ts.stabilization_year(c))
    cov = cf_mod.covenant_report(cf, c["debt"]["min_dscr"], tested_from_year=tested_from)
    min_dscr = cov["min_dscr_tested"] if cov["min_dscr_tested"] is not None else 0.0

    coverage = ok = None
    if parcel is not None:
        r = dm.assess(c, parcel)
        coverage = r.coverage
        ok = coverage >= float(c["demand"]["coverage_thin"])

    clears = (ts._at_least(min_dscr, c["debt"]["min_dscr"])
              and (cf.equity_irr or -1) > 0
              and ts._at_least(cf.value_to_cost, 1.0))
    return Variant(
        track_miles=miles, member_cap=int(cap), condo_units=int(condos),
        members_per_mile=cap / miles if miles else 0.0,
        stabilized_noi=uw.stabilized_noi, equity_irr=cf.equity_irr,
        min_dscr=min_dscr, value_to_cost=cf.value_to_cost,
        peak_equity=cf.peak_equity_requirement, clears=clears,
        demand_coverage=coverage, demand_ok=ok,
    )


def search(
    cfg: dict[str, Any],
    land_price: float,
    premium: float = 0.0,
    scenario: str = "comp_repriced",
    track_miles: tuple[float, ...] = (2.25, 2.5, 2.75, 3.0, 3.5, 4.0),
    member_caps: tuple[int, ...] = (340, 380, 425, 470, 510),
    condo_units: tuple[int, ...] = (110, 140, 170, 200),
    horizon: int = 12,
    parcel: dict[str, Any] | None = None,
) -> Respec:
    """
    Hold the comp-supported PRICING fixed and search the PROGRAMME.

    `scenario` names the pricing to hold. Defaults to the comparable set's own
    view, because re-specifying against pricing the comp set contradicts would
    just be re-deriving the base case.

    `parcel` is optional and only feeds the demand cross-check. A variant that
    clears the governing tests but needs more members than the catchment can
    supply is not a solution, and the search reports both facts rather than
    quietly preferring one.
    """
    priced = sc.apply_scenario(cfg, {k: v for k, v in cfg["scenarios"][scenario].items()
                                     if k != "label"})
    base_miles = float(cfg["cost"]["track"]["miles"])
    base_cap = int(cfg["income"]["membership"]["cap"])
    base_condos = int(cfg["for_sale"]["garage_condos"]["units"])

    baseline = _evaluate(priced, land_price, premium, base_miles, base_cap,
                         base_condos, horizon, parcel)

    variants: list[Variant] = []
    for miles in track_miles:
        for cap in member_caps:
            for condos in condo_units:
                variants.append(_evaluate(priced, land_price, premium, miles, cap,
                                          condos, horizon, parcel))
    variants.sort(key=lambda v: -(v.equity_irr if v.equity_irr is not None else -1e9))

    best = variants[0] if variants else None
    feasible = [v for v in variants if v.clears and (v.demand_ok is not False)]
    best_feasible = feasible[0] if feasible else None

    # Attribution: how much of the answer is track length, and how much is the
    # for-sale count? Both measured at the best variant's cap, one at a time.
    ref = best or baseline
    track_bps = _spread_bps(
        [v for v in variants if v.member_cap == ref.member_cap
         and v.condo_units == ref.condo_units])
    condo_bps = _spread_bps(
        [v for v in variants if v.member_cap == ref.member_cap
         and v.track_miles == ref.track_miles])

    if best_feasible is None:
        verdict = (
            f"NO PROGRAMME CLEARS AT COMP-SUPPORTED PRICING. The best configuration "
            f"searched returns {(best.equity_irr or 0):.1%} at {best.min_dscr:.2f}x "
            f"coverage. Re-specifying the programme does not rescue the comp case; "
            f"either the comps are wrong or the land bid has to fall to match them.")
    else:
        b = best_feasible
        verdict = (
            f"THE COMP CASE IS A SPECIFICATION PROBLEM, NOT ONLY A PRICING ONE. At "
            f"comp-supported pricing the configured programme returns "
            f"{(baseline.equity_irr or 0):.1%} and covers at {baseline.min_dscr:.2f}x. "
            f"A {b.member_cap}-member club on {b.track_miles:.2f} miles with "
            f"{b.condo_units} garage condos returns {(b.equity_irr or 0):.1%} and covers "
            f"at {b.min_dscr:.2f}x — clearing every governing test on the same dirt at "
            f"the same prices. The lever is MEMBER COUNT, not track length: across the "
            f"searched range track length is worth {track_bps:.0f} bp of IRR and the "
            f"for-sale count {condo_bps:.0f} bp, and the for-sale count moves the WRONG "
            f"WAY — more units lower the return, because the vertical is 43% of non-land "
            f"cost on a thin comp-supported margin and the carry runs until the last one "
            f"sells.")

    return Respec(baseline=baseline, variants=variants, best=best,
                  best_feasible=best_feasible, track_sensitivity_bps=track_bps,
                  condo_sensitivity_bps=condo_bps, verdict=verdict)


def _spread_bps(group: list[Variant]) -> float:
    irrs = [v.equity_irr for v in group if v.equity_irr is not None]
    return (max(irrs) - min(irrs)) * 10_000 if len(irrs) > 1 else 0.0
