"""
Tests for the analytical layer: property tax, cash flow, scenarios, and risk.

The load-bearing ones here are the *identities*:

  * an ad-valorem tax must be exactly equivalent to adding tau to the required
    yield, which is the claim that lets the closed-form land solve survive;
  * sources must equal uses, or the funding waterfall is double-counting;
  * an amortizing note must retire to zero at term;
  * a degenerate Monte Carlo must reproduce the base case to the cent.

Run:  python3 tests/test_analytics.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model import cashflow as cfm  # noqa: E402
from model import risk as rk  # noqa: E402
from model import roadmap as rmap  # noqa: E402
from model import scenarios as sc  # noqa: E402
from model import two_stack as ts  # noqa: E402

CFG = ts.load_config()
ASK = 9_800_000.0


def approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


# =============================================================================
# Property tax — the tau identity
# =============================================================================

def test_tax_load_is_product_of_four_terms():
    pt = CFG["income"]["property_tax"]
    assert approx(
        ts.tax_load(CFG),
        pt["taxable_share_of_gross_basis"] * pt["assessment_ratio"]
        * pt["effective_rate"] * (1 - pt["abatement_pct"]),
    )


def test_ad_valorem_tax_equals_adding_tau_to_the_yield():
    """
    The identity the closed form rests on: solving with tax at hurdle h must
    equal solving WITHOUT tax at hurdle h + tau.
    """
    r = ts.underwrite(CFG, "TAU")
    tau = ts.tax_load(CFG)
    h = r.required_yield
    for basis in ("gross",):
        with_tax = ts.max_supportable_land_price(
            r.stabilized_noi, r.cost, r.for_sale, h, basis, CFG)
        no_tax_higher_hurdle = ts.max_supportable_land_price(
            r.stabilized_noi, r.cost, r.for_sale, h + tau, basis, None)
        assert approx(with_tax, no_tax_higher_hurdle), basis


def test_round_trip_holds_after_tax():
    """At the solved land price, the AFTER-TAX yield equals the required yield."""
    r = ts.underwrite(CFG, "RT")
    for basis, land in (("gross", r.max_land_gross), ("net", r.max_land_net)):
        y = ts.yield_on_cost(r.stabilized_noi, land, r.cost, r.for_sale, basis, CFG)
        assert approx(y, r.required_yield), f"{basis}: {y}"


def test_zero_abatement_versus_full_abatement():
    full = copy.deepcopy(CFG)
    full["income"]["property_tax"]["abatement_pct"] = 1.0
    assert approx(ts.tax_load(full), 0.0)
    assert ts.underwrite(full, "A").max_land_gross > ts.underwrite(CFG, "B").max_land_gross


def test_tax_never_negative_on_negative_basis():
    assert ts.property_tax_annual(CFG, -50_000_000) == 0.0


def test_higher_tax_rate_lowers_land_price():
    hi = copy.deepcopy(CFG)
    hi["income"]["property_tax"]["effective_rate"] *= 1.5
    assert ts.underwrite(hi, "H").max_land_net < ts.underwrite(CFG, "B").max_land_net


# =============================================================================
# Amortization and IRR
# =============================================================================

def test_amortizing_note_retires_at_term():
    sched = cfm.amortization_schedule(100_000_000, 0.0725, 25, 12, 25)
    assert sched[-1][1] < 1.0, f"balance at term {sched[-1][1]}"


def test_amortization_balance_declines_monotonically():
    sched = cfm.amortization_schedule(50_000_000, 0.07, 25, 12, 20)
    bals = [b for _, b in sched]
    assert bals == sorted(bals, reverse=True)


def test_amortization_zero_principal_is_all_zeros():
    assert cfm.amortization_schedule(0, 0.07, 25, 12, 5) == [(0.0, 0.0)] * 5


def test_annual_debt_service_matches_mortgage_constant():
    p = 80_000_000
    sched = cfm.amortization_schedule(p, 0.0725, 25, 12, 3)
    expected = p * ts.mortgage_constant(0.0725, 25, 12)
    assert approx(sched[0][0], expected, tol=1e-6)


def test_irr_recovers_a_known_rate():
    # -100 then 110 one year later is exactly 10%.
    assert approx(cfm.irr([-100, 110]), 0.10, tol=1e-4)


def test_irr_returns_none_without_a_sign_change():
    assert cfm.irr([100, 200, 300]) is None
    assert cfm.irr([-100, -200]) is None


def test_irr_of_flat_return_is_zero():
    assert abs(cfm.irr([-100, 50, 50])) < 1e-3


# =============================================================================
# Cash flow
# =============================================================================

def test_sources_equal_uses():
    """If these diverge the waterfall is double-counting or losing money."""
    cf = cfm.project_cash_flow(CFG, ASK)
    su = cf.sources_uses
    assert approx(su.total_sources, su.total_uses, tol=1e-9)


def test_debt_never_exceeds_its_ltc_capacity():
    cf = cfm.project_cash_flow(CFG, ASK)
    assert cf.sources_uses.debt <= cf.sources_uses.debt_capacity + 1e-6


def test_initiation_cash_totals_cap_times_fee():
    cf = cfm.project_cash_flow(CFG, ASK)
    m = CFG["income"]["membership"]
    expected = ts.membership_schedule(CFG, 12)[-1] * m["initiation_fee_usd"]
    assert approx(cf.sources_uses.initiation_cash, expected)


def test_peak_funding_is_non_negative_and_dated():
    cf = cfm.project_cash_flow(CFG, ASK)
    assert cf.peak_funding_requirement >= 0
    assert any(p.year == cf.peak_funding_year for p in cf.periods)


def test_peak_funding_exceeds_residual_equity():
    """
    The trough is what must be written in checks; the residual is what stays in
    at the end. Conflating them understated the check by two orders of magnitude.
    """
    cf = cfm.project_cash_flow(CFG, ASK)
    assert cf.peak_equity_requirement >= cf.residual_equity


def test_cumulative_cash_is_running_sum_of_net_flows():
    cf = cfm.project_cash_flow(CFG, ASK)
    run = 0.0
    for p in cf.periods:
        run += p.net_cash_flow
        assert approx(p.cumulative_cash, run, tol=1e-9)


def test_construction_phase_has_no_noi():
    cf = cfm.project_cash_flow(CFG, ASK)
    for p in cf.periods:
        if p.phase == "construction":
            assert p.noi_pretax == 0 and p.dscr is None


def test_dscr_by_year_matches_noi_over_debt_service():
    cf = cfm.project_cash_flow(CFG, ASK)
    for p in cf.periods:
        if p.dscr is not None:
            assert approx(p.dscr, p.noi_after_tax / -p.debt_service, tol=1e-9)


def test_min_dscr_is_the_minimum_of_the_series():
    cf = cfm.project_cash_flow(CFG, ASK)
    assert approx(cf.min_dscr, min(cf.dscr_by_year.values()))


def test_covenant_report_flags_every_breach():
    cf = cfm.project_cash_flow(CFG, ASK)
    rep = cfm.covenant_report(cf, CFG["debt"]["min_dscr"])
    manual = [y for y, v in cf.dscr_by_year.items() if v < CFG["debt"]["min_dscr"]]
    assert rep["breach_years"] == sorted(manual)
    assert rep["passes_every_year"] == (not manual)


def test_stabilized_dscr_alone_understates_the_risk():
    """
    The covenant is tested from conversion, not at stabilization. Coverage is
    tightest early, when opex is full and the ramp is not -- so the minimum
    across the hold must be no better than the stabilized figure.
    """
    cf = cfm.project_cash_flow(CFG, ASK)
    uw = ts.underwrite(CFG, "X", ask_price=ASK)
    assert cf.min_dscr <= uw.dscr_net_at_ask + 1e-9


def test_permanent_sizing_basis_changes_the_loan():
    gross = copy.deepcopy(CFG)
    gross["debt"]["permanent_sizing_basis"] = "gross"
    a = cfm.project_cash_flow(CFG, ASK).sources_uses.debt_capacity
    b = cfm.project_cash_flow(gross, ASK).sources_uses.debt_capacity
    assert b > a, "gross sizing must lend against more collateral"


def test_breakeven_exit_cap_makes_value_equal_cost():
    cf = cfm.project_cash_flow(CFG, ASK)
    c = copy.deepcopy(CFG)
    c["income"]["exit_cap"] = cf.breakeven_exit_cap
    c["income"]["exit_cost_pct"] = 0.0
    assert approx(cfm.project_cash_flow(c, ASK).value_to_cost, 1.0, tol=1e-4)


# =============================================================================
# Scenarios
# =============================================================================

def test_apply_scenario_rejects_unknown_factors():
    """A silently-dropped factor is a scenario lying about how stressed it is."""
    try:
        sc.apply_scenario(CFG, {"nonsense_factor": 0.5})
    except ValueError:
        return
    raise AssertionError("unknown scenario factor must raise")


def test_apply_scenario_does_not_mutate_the_base():
    before = CFG["income"]["membership"]["annual_dues_usd"]
    sc.apply_scenario(CFG, {"dues_factor": 0.5})
    assert CFG["income"]["membership"]["annual_dues_usd"] == before


def test_cap_factor_scales_cap_and_ramp_together():
    c = sc.apply_scenario(CFG, {"cap_factor": 0.5})
    assert c["income"]["membership"]["cap"] < CFG["income"]["membership"]["cap"]
    assert sum(c["income"]["membership"]["ramp"]) < sum(CFG["income"]["membership"]["ramp"])


def test_ramp_stretch_preserves_total_members():
    c = sc.apply_scenario(CFG, {"ramp_stretch": 2.0})
    assert len(c["income"]["membership"]["ramp"]) > len(CFG["income"]["membership"]["ramp"])
    assert abs(sum(c["income"]["membership"]["ramp"])
               - sum(CFG["income"]["membership"]["ramp"])) <= 2


def test_absorption_slowdown_extends_sellout():
    c = sc.apply_scenario(CFG, {"absorption_slowdown": 2.0})
    assert ts.project_for_sale(c).sellout_years > ts.project_for_sale(CFG).sellout_years


def test_perm_rate_moves_both_coupon_and_carry():
    c = sc.apply_scenario(CFG, {"perm_rate_bps": 100})
    assert approx(c["debt"]["permanent_rate"], CFG["debt"]["permanent_rate"] + 0.01)
    assert approx(c["cost"]["carry"]["interest_rate"],
                  CFG["cost"]["carry"]["interest_rate"] + 0.01)


def test_scenarios_are_monotonically_ordered():
    """Upside must beat base must beat downside must beat severe."""
    res = {r.name: r for r in sc.run_all(CFG, ask_price=ASK)}
    order = ["upside", "base", "downside", "severe"]
    lands = [res[n].max_land_net for n in order if n in res]
    assert lands == sorted(lands, reverse=True), lands


def test_severe_is_no_easier_than_base():
    """
    Severe widens the coupon, which raises the DSCR-implied yield. At low
    leverage the equity hurdle may still bind in both cases, so the required
    yield can be equal -- it must never be LOWER.
    """
    res = {r.name: r for r in sc.run_all(CFG, ask_price=ASK)}
    assert (res["severe"].effective_required_yield
            >= res["base"].effective_required_yield - 1e-12)
    assert res["severe"].max_land_net < res["base"].max_land_net


def test_upside_abatement_lowers_the_tax_load():
    res = {r.name: r for r in sc.run_all(CFG, ask_price=ASK)}
    assert res["upside"].tax_load < res["base"].tax_load


def test_base_scenario_reproduces_the_base_case():
    res = {r.name: r for r in sc.run_all(CFG, ask_price=ASK)}
    uw = ts.underwrite(CFG, "B", ask_price=ASK)
    assert approx(res["base"].max_land_net, uw.max_land_net)
    assert approx(res["base"].stabilized_noi_pretax, uw.stabilized_noi)


def test_scenario_spread_counts_are_consistent():
    res = sc.run_all(CFG, ask_price=ASK)
    sp = sc.scenario_spread(res)
    assert sp["total_scenarios"] == len(res)
    assert sp["swing"] >= 0
    assert 0 <= sp["scenarios_clearing_gross"] <= len(res)


# =============================================================================
# Break-evens
# =============================================================================

def test_break_even_solver_finds_a_root():
    be = rk.solve_break_even(CFG, "dues_factor", rk.metric_max_land_net, 0.0, "test")
    assert be.reachable
    c = sc.apply_scenario(CFG, {"dues_factor": be.break_even_value})
    assert abs(rk.metric_max_land_net(c)) < 50_000


def test_break_even_reports_unreachable_rather_than_guessing():
    be = rk.solve_break_even(
        CFG, "dues_factor", rk.metric_max_land_net, 10 ** 12, "absurd target")
    assert not be.reachable and be.break_even_value is None and be.note


def test_direct_break_even_members_is_self_consistent():
    d = rk.direct_break_evens(CFG, ASK)
    assert d["members_to_meet_covenant"] > d["members_to_cover_opex_and_tax"]
    assert d["per_member_contribution"] > 0


def test_covenant_is_reachable_within_the_membership_cap():
    """
    Under v1.0 the covenant needed 291 members against a cap of 250 -- it was
    unreachable at any land price. v2.0 lowers leverage and raises the cap, so
    the required count now sits INSIDE the cap. Locking that in: if a future
    change pushes it back outside, the deal has quietly become unfinanceable.
    """
    d = rk.direct_break_evens(CFG, ASK)
    assert d["members_to_meet_covenant"] <= d["membership_cap"], (
        f"covenant needs {d['members_to_meet_covenant']:.0f} members against a "
        f"cap of {d['membership_cap']}")


def test_break_even_suite_returns_every_test():
    suite = rk.break_even_suite(CFG, ASK)
    assert len(suite) == 12
    assert all(b.metric for b in suite)


# =============================================================================
# Tornado
# =============================================================================

def test_tornado_is_sorted_by_swing():
    bars, _base, _n = rk.tornado(CFG)
    swings = [b.swing_abs for b in bars]
    assert swings == sorted(swings, reverse=True)


def test_tornado_base_matches_the_metric():
    bars, base, _n = rk.tornado(CFG)
    assert approx(base, rk.metric_max_land_net(CFG))
    assert bars


def test_tornado_cost_driver_is_inverted():
    """Higher hard cost must lower the land price, not raise it."""
    bars = {b.driver: b for b in rk.tornado(CFG)[0]}
    hc = bars["hard_cost_factor"]
    assert hc.high_value < hc.low_value


def test_tornado_revenue_driver_is_direct():
    bars = {b.driver: b for b in rk.tornado(CFG)[0]}
    du = bars["dues_factor"]
    assert du.high_value > du.low_value


# =============================================================================
# Monte Carlo
# =============================================================================

def _degenerate_cfg():
    c = copy.deepcopy(CFG)
    for k in c["monte_carlo"]["drivers"]:
        neutral = 0.0 if k in rk.RATE_DRIVERS else 1.0
        c["monte_carlo"]["drivers"][k] = [neutral, neutral, neutral]
    return c


def test_degenerate_monte_carlo_reproduces_the_base_case():
    """Pin every driver at neutral and the distribution must collapse to base."""
    mc = rk.monte_carlo(_degenerate_cfg(), ASK, iterations=20)
    base = ts.underwrite(CFG, "B").max_land_net
    assert approx(mc.percentiles["p50"], base, tol=1e-6)
    assert approx(mc.stdev, 0.0, tol=1e-6)


def test_monte_carlo_percentiles_are_ordered():
    mc = rk.monte_carlo(CFG, ASK, iterations=300)
    keys = ["p5", "p10", "p25", "p50", "p75", "p90", "p95"]
    vals = [mc.percentiles[k] for k in keys]
    assert vals == sorted(vals)


def test_monte_carlo_is_reproducible_under_a_seed():
    a = rk.monte_carlo(CFG, ASK, iterations=120, seed=42)
    b = rk.monte_carlo(CFG, ASK, iterations=120, seed=42)
    assert a.percentiles == b.percentiles


def test_monte_carlo_probabilities_are_fractions():
    mc = rk.monte_carlo(CFG, ASK, iterations=200)
    for p in (mc.p_feasible_gross, mc.p_feasible_net, mc.p_covenant_holds):
        assert 0.0 <= p <= 1.0
    assert mc.p_feasible_net >= mc.p_feasible_gross


def test_monte_carlo_records_evaluation_failures():
    mc = rk.monte_carlo(CFG, ASK, iterations=100)
    assert mc.failures >= 0
    assert len(mc.samples) + mc.failures == mc.iterations


# =============================================================================
# Plausibility
# =============================================================================

def test_plausibility_still_catches_an_inflated_for_sale_margin():
    """
    The motivating defect was a 53% merchant-build margin subsidising the club.
    v2.0 sits inside the band, so re-inflate the price and confirm the guard
    still fires.
    """
    c = copy.deepcopy(CFG)
    c["for_sale"]["garage_condos"]["sale_price_psf"] *= 1.6
    rep = rk.plausibility_report(c, ASK)
    margins = [x for x in rep["checks"] if "gross margin" in x.name.lower()]
    assert margins and margins[0].severity in {"WARN", "FAIL"}


def test_value_exceeds_retained_cost():
    """v2.0 must create value: exit proceeds above the retained cost basis."""
    rep = rk.plausibility_report(CFG, ASK)
    vc = [c for c in rep["checks"] if c.name == "Value / cost"]
    assert vc and vc[0].passed, vc[0].message if vc else "check missing"
    assert vc[0].value > 1.0


def test_base_case_is_internally_coherent():
    """
    The v2.0 base case must carry ZERO plausibility failures. This is the gate
    that stopped the calibration from optimising its way into an implausibly
    efficient operating ratio.
    """
    rep = rk.plausibility_report(CFG, ASK)
    assert rep["fail_count"] == 0, [c.message for c in rep["checks"]
                                    if c.severity == "FAIL"]
    assert rep["coherent"]


def test_plausibility_passes_a_coherent_pro_forma():
    """Move the two failing inputs into band and the audit must stop failing."""
    c = copy.deepcopy(CFG)
    c["for_sale"]["garage_condos"]["sale_price_psf"] = 500
    c["for_sale"]["homesites"]["price_per_unit_usd"] = 640_000
    rep = rk.plausibility_report(c, ASK)
    margin = [x for x in rep["checks"] if "gross margin" in x.name.lower()][0]
    assert margin.passed, margin.message


def test_plausibility_severity_values_are_known():
    rep = rk.plausibility_report(CFG, ASK)
    assert all(c.severity in {"OK", "WARN", "FAIL"} for c in rep["checks"])


# =============================================================================
# Roadmap, platform scale, and the listing test
# =============================================================================

def test_timing_is_derived_from_the_model():
    """Change the construction period and the roadmap must move with it."""
    T = rmap.timing(CFG)
    assert T.construction_months == round(CFG["cost"]["carry"]["development_years"] * 12)
    assert T.opening_month == CFG["roadmap"]["entitlement_months"] + T.construction_months
    assert T.stabilisation_month == T.opening_month + ts.stabilization_year(CFG) * 12

    slow = copy.deepcopy(CFG)
    slow["cost"]["carry"]["development_years"] += 2
    assert rmap.timing(slow).opening_month > T.opening_month


def test_all_ten_horizons_are_present_and_ordered():
    ms = rmap.milestones(CFG)
    assert len(ms) == 10
    assert [x.month for x in ms] == sorted(x.month for x in ms)
    assert [x.horizon for x in ms][0] == "1 month"
    assert [x.horizon for x in ms][-1] == "10 years"


def test_every_milestone_carries_a_gate_and_a_kpi():
    for x in rmap.milestones(CFG):
        assert x.objective and x.gate and x.kpi and x.deliverables, x.horizon


def test_milestone_phases_are_computed_not_asserted():
    """Phase labels must follow the derived timing, not a hardcoded list."""
    T = rmap.timing(CFG)
    for x in rmap.milestones(CFG):
        if x.month <= T.feasibility_months:
            assert "Feasibility" in x.phase
        elif x.month <= T.entitlement_months:
            assert "Entitlement" in x.phase
        elif x.month <= T.opening_month:
            assert "Construction" in x.phase


def test_platform_scale_is_linear_in_club_count():
    pts = rmap.platform_scale(CFG, ASK, 0.0, 5)
    one = pts[0]
    for p in pts:
        assert approx(p.stabilised_noi, one.stabilised_noi * p.clubs, tol=1e-9)
        assert approx(p.asset_value, one.asset_value * p.clubs, tol=1e-9)


def test_listing_requires_more_than_one_club():
    """A single-asset issuer of this size has no public-market path."""
    lt = rmap.listing_readiness(CFG, ASK)
    assert lt.clubs_required > 1
    assert lt.clubs_required == max(lt.clubs_required_by_noi,
                                    lt.clubs_required_by_value,
                                    lt.clubs_required_by_diversification)


def test_acquisition_route_is_faster_than_ground_up():
    lt = rmap.listing_readiness(CFG, ASK)
    assert lt.acquisition_year < lt.ground_up_year


def test_listing_verdict_is_honest_about_year_ten():
    """
    Documents the finding: club 1 stabilises at ~year 10, so year 10 is not a
    listing date. If this flips, the timing assumptions moved materially.
    """
    lt = rmap.listing_readiness(CFG, ASK)
    T = rmap.timing(CFG)
    assert T.stabilisation_year > 9.0
    assert not lt.listable_by_year_10
    assert "NOT LISTABLE BY YEAR 10" in lt.verdict


def test_higher_thresholds_require_more_clubs():
    hard = copy.deepcopy(CFG)
    hard["listing_thresholds"]["min_recurring_noi_usd"] *= 2
    assert (rmap.listing_readiness(hard, ASK).clubs_required
            > rmap.listing_readiness(CFG, ASK).clubs_required)


def test_exit_ladder_is_ranked_and_complete():
    paths = rmap.exit_paths(CFG, ASK)
    assert len(paths) == 7
    assert [p.rank for p in paths] == list(range(1, 8))
    assert "public offering" in paths[-1].route.lower(), "IPO must rank last"
    assert "for-sale" in paths[0].route.lower(), "self-liquidating routes rank first"


def test_exit_ladder_ipo_entry_carries_the_verdict():
    paths = rmap.exit_paths(CFG, ASK)
    assert "STRETCH OUTCOME" in paths[-1].assessment


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items())
           if n.startswith("test_") and callable(f)]
    failed = 0
    for name, fn in fns:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {name}: {exc}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
