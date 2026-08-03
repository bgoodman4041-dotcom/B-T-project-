"""
TRACK BOSS — Scenario Engine
============================

A two-axis sensitivity grid assumes its axes are independent. They are not.

In a soft cycle dues soften, the membership ramp stretches, condo pricing
compresses, absorption slows, construction cost rises, and the exit cap widens
*simultaneously*, because they share a driver. Flexing one variable at a time
systematically understates downside: it prices five 1-in-4 events as if they
could not co-occur, when in practice they arrive together or not at all.

This module applies coherent bundles. Every scenario is a set of multipliers on
the base configuration, so there is exactly one source of truth for the base
case and the scenarios are transparent deltas from it.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from . import cashflow as cf_mod
from . import two_stack as ts


@dataclass
class ScenarioResult:
    name: str
    label: str

    stabilized_noi_pretax: float
    property_tax: float
    stabilized_noi_after_tax: float

    required_yield: float
    binding_constraint: str
    tax_load: float
    effective_required_yield: float     # required + tau

    max_land_gross: float
    max_land_net: float

    yoc_gross_at_ask: float | None
    dscr_stabilized_gross: float | None
    dscr_stabilized_net: float | None

    min_dscr_any_year: float | None
    min_dscr_year: int | None
    covenant_breach_years: int

    peak_equity: float
    equity_multiple: float
    equity_irr: float | None
    value_to_cost: float
    breakeven_exit_cap: float | None
    sellout_years: float
    carry_factor: float

    feasible_gross: bool
    feasible_net: bool
    covenant_holds: bool

    @property
    def verdict(self) -> str:
        if self.feasible_gross and self.covenant_holds:
            return "CLEARS"
        if self.feasible_net and self.covenant_holds:
            return "CLEARS NET ONLY"
        if self.feasible_net:
            return "NET ONLY, COVENANT FAILS"
        return "FAILS"


# =============================================================================
# Applying a bundle
# =============================================================================

def apply_scenario(cfg: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """
    Return a deep copy of cfg with the scenario multipliers applied.

    Unknown keys raise rather than being ignored -- a silently-dropped scenario
    factor is a scenario that lies about how stressed it is.
    """
    c = copy.deepcopy(cfg)
    m = c["income"]["membership"]
    fs = c["for_sale"]
    known = {
        "label", "dues_factor", "cap_factor", "ancillary_factor", "condo_psf_factor",
        "homesite_price_factor", "absorption_slowdown", "hard_cost_factor",
        "opex_factor", "exit_cap_bps", "perm_rate_bps", "ramp_stretch",
        "abatement_pct", "ltc_delta", "min_dscr_delta",
    }
    unknown = set(overrides) - known
    if unknown:
        raise ValueError(f"unknown scenario factor(s): {sorted(unknown)}")

    if (f := overrides.get("dues_factor")) is not None:
        m["annual_dues_usd"] *= f

    if (f := overrides.get("cap_factor")) is not None:
        # Cap and ramp scale together -- a lower achieved cap is not a cap cut
        # with the same ramp, it is fewer members joining each year.
        m["cap"] = max(1, int(round(m["cap"] * f)))
        m["ramp"] = [max(0, int(round(r * f))) for r in m["ramp"]]

    if (f := overrides.get("ramp_stretch")) is not None and f != 1:
        # Stretch the ramp over more years by scaling annual additions down and
        # extending the tail, preserving the total.
        ramp = m["ramp"]
        new_len = max(1, int(round(len(ramp) * f)))
        total = sum(ramp)
        per = total / new_len
        m["ramp"] = [int(round(per))] * new_len
        drift = total - sum(m["ramp"])
        if m["ramp"]:
            m["ramp"][-1] += drift

    if (f := overrides.get("ancillary_factor")) is not None:
        for k in c["income"]["ancillary_annual_usd"]:
            c["income"]["ancillary_annual_usd"][k] *= f

    if (f := overrides.get("opex_factor")) is not None:
        for k in c["income"]["opex_annual_usd"]:
            c["income"]["opex_annual_usd"][k] *= f

    if (f := overrides.get("condo_psf_factor")) is not None:
        fs["garage_condos"]["sale_price_psf"] *= f

    if (f := overrides.get("homesite_price_factor")) is not None:
        fs["homesites"]["price_per_unit_usd"] *= f

    if (f := overrides.get("absorption_slowdown")) is not None and f != 1:
        for key in ("garage_condos", "homesites"):
            cur = fs[key]["absorption_units_per_year"]
            fs[key]["absorption_units_per_year"] = max(1, cur / f)

    if (f := overrides.get("hard_cost_factor")) is not None:
        cost = c["cost"]
        cost["track"]["hard_cost_per_mile_usd"] *= f
        cost["track"]["paddock_and_pit_usd"] *= f
        for k in cost["vertical_hard_usd"]:
            cost["vertical_hard_usd"][k] *= f
        for k in cost["site_infrastructure_usd"]:
            cost["site_infrastructure_usd"][k] *= f
        fs["garage_condos"]["hard_cost_psf"] *= f
        fs["homesites"]["improvement_cost_per_unit_usd"] *= f

    if (b := overrides.get("exit_cap_bps")) is not None:
        c["income"]["exit_cap"] += b / 10_000

    if (b := overrides.get("perm_rate_bps")) is not None:
        c["debt"]["permanent_rate"] += b / 10_000
        # Construction carry prices off the same curve.
        c["cost"]["carry"]["interest_rate"] += b / 10_000

    if (a := overrides.get("abatement_pct")) is not None:
        c["income"]["property_tax"]["abatement_pct"] = a

    if (d := overrides.get("ltc_delta")) is not None:
        c["debt"]["target_ltc"] = max(0.0, min(0.95, c["debt"]["target_ltc"] + d))

    if (d := overrides.get("min_dscr_delta")) is not None:
        c["debt"]["min_dscr"] = max(1.0, c["debt"]["min_dscr"] + d)

    return c


# =============================================================================
# Running
# =============================================================================

def run_scenario(
    cfg: dict[str, Any],
    name: str,
    overrides: dict[str, Any],
    ask_price: float | None = None,
    horizon: int = 12,
) -> ScenarioResult:
    c = apply_scenario(cfg, overrides)
    label = overrides.get("label", name)

    uw = ts.underwrite(c, parcel_id=f"SCEN-{name}", ask_price=ask_price)
    land_for_cf = ask_price if ask_price is not None else max(0.0, uw.max_land_net)
    cf = cf_mod.project_cash_flow(c, land_for_cf, horizon_operating_years=horizon)
    cov = cf_mod.covenant_report(cf, c["debt"]["min_dscr"])

    tau = ts.tax_load(c)
    return ScenarioResult(
        name=name,
        label=label,
        stabilized_noi_pretax=uw.stabilized_noi,
        property_tax=uw.property_tax_at_max_land,
        stabilized_noi_after_tax=uw.stabilized_noi_after_tax,
        required_yield=uw.required_yield,
        binding_constraint=uw.binding_constraint,
        tax_load=tau,
        effective_required_yield=uw.required_yield + tau,
        max_land_gross=uw.max_land_gross,
        max_land_net=uw.max_land_net,
        yoc_gross_at_ask=uw.yoc_gross_at_ask,
        dscr_stabilized_gross=uw.dscr_gross_at_ask,
        dscr_stabilized_net=uw.dscr_net_at_ask,
        min_dscr_any_year=cf.min_dscr,
        min_dscr_year=cf.min_dscr_year,
        covenant_breach_years=cov["breach_count"],
        peak_equity=cf.peak_equity_requirement,
        equity_multiple=cf.equity_multiple,
        equity_irr=cf.equity_irr,
        value_to_cost=cf.value_to_cost,
        breakeven_exit_cap=cf.breakeven_exit_cap,
        sellout_years=cf.periods and uw.for_sale.sellout_years or 0.0,
        carry_factor=uw.cost.carry_factor,
        feasible_gross=uw.max_land_gross > 0,
        feasible_net=uw.max_land_net > 0,
        covenant_holds=cov["passes_every_year"],
    )


SCENARIO_ORDER = ["upside", "base", "downside", "severe"]


def run_all(
    cfg: dict[str, Any], ask_price: float | None = None, horizon: int = 12
) -> list[ScenarioResult]:
    """Run every scenario defined in config, best case first."""
    defs = {k: v for k, v in cfg["scenarios"].items() if isinstance(v, dict)}
    ordered = [n for n in SCENARIO_ORDER if n in defs]
    ordered += [n for n in defs if n not in ordered]
    return [run_scenario(cfg, n, defs[n], ask_price, horizon) for n in ordered]


def scenario_spread(results: list[ScenarioResult]) -> dict[str, Any]:
    """
    How far the answer travels across the scenario set. A land price that swings
    by more than the deal size is a signal that the assumptions, not the site,
    are driving the recommendation.
    """
    lands = [r.max_land_net for r in results]
    return {
        "max_land_net_high": max(lands),
        "max_land_net_low": min(lands),
        "swing": max(lands) - min(lands),
        "scenarios_clearing_gross": sum(1 for r in results if r.feasible_gross),
        "scenarios_clearing_net": sum(1 for r in results if r.feasible_net),
        "scenarios_covenant_ok": sum(1 for r in results if r.covenant_holds),
        "total_scenarios": len(results),
    }
