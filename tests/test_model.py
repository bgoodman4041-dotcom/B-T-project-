"""
Track Boss model tests.

The important ones are the round-trip identities: if the max supportable land
price is correct, feeding it back as the ask must return exactly the hurdle.
Everything else is guardrails.

Run:  python3 -m pytest tests/ -q      (or)      python3 tests/test_model.py
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model import gates, scoring, two_stack  # noqa: E402

CFG = two_stack.load_config()
HURDLE = CFG["meta"]["hurdle_yoc"]


def approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


# =============================================================================
# The round-trip identity — the test that matters
# =============================================================================

def test_max_land_price_round_trips_to_hurdle_gross():
    r = two_stack.underwrite(CFG, "RT-GROSS")
    y = two_stack.yield_on_cost(
        r.stabilized_noi, r.max_land_gross, r.cost, r.for_sale, "gross"
    )
    assert approx(y, HURDLE), f"gross round-trip gave {y:.8f}, expected {HURDLE}"


def test_max_land_price_round_trips_to_hurdle_net():
    r = two_stack.underwrite(CFG, "RT-NET")
    y = two_stack.yield_on_cost(
        r.stabilized_noi, r.max_land_net, r.cost, r.for_sale, "net"
    )
    assert approx(y, HURDLE), f"net round-trip gave {y:.8f}, expected {HURDLE}"


def test_net_basis_supports_more_land_than_gross():
    """For-sale proceeds offset the basis, so net must support a higher price."""
    r = two_stack.underwrite(CFG, "CMP")
    assert r.max_land_net > r.max_land_gross
    # The gap should be roughly the proceeds discounted by the carry factor.
    expected_gap = r.for_sale.net_proceeds / (1 + r.cost.carry_factor)
    assert approx(r.max_land_net - r.max_land_gross, expected_gap, tol=1e-9)


def test_carry_accrues_on_land_not_just_improvements():
    r = two_stack.underwrite(CFG, "CARRY")
    b0 = r.cost.gross_basis(0)
    b1 = r.cost.gross_basis(10_000_000)
    assert approx(b1 - b0, 10_000_000 * (1 + r.cost.carry_factor))


# =============================================================================
# Stack B
# =============================================================================

def test_membership_ramp_clamps_at_cap():
    sched = two_stack.membership_schedule(CFG, 15)
    cap = CFG["income"]["membership"]["cap"]
    assert max(sched) <= cap
    assert sched == sorted(sched), "membership must be monotonically non-decreasing"


def test_stabilization_is_first_year_at_85pct():
    cap = CFG["income"]["membership"]["cap"]
    thresh = CFG["income"]["membership"]["stabilization_threshold"]
    year = two_stack.stabilization_year(CFG)
    sched = two_stack.membership_schedule(CFG, 20)
    assert sched[year - 1] >= cap * thresh
    if year > 1:
        assert sched[year - 2] < cap * thresh, "not the FIRST qualifying year"


def test_initiation_never_capitalized_in_base_case():
    """§3: initiation must not be capitalized into NOI in the base case."""
    assert CFG["income"]["initiation_treatment"]["mode"] == "amortized"


def test_initiation_amortization_is_bounded_by_cash():
    """Amortized recognition must sit strictly between excluded and capitalized."""
    bk = two_stack.initiation_bookends(CFG)
    assert bk["excluded"]["stabilized_noi"] < bk["amortized"]["stabilized_noi"]
    assert bk["amortized"]["stabilized_noi"] < bk["capitalized"]["stabilized_noi"]


def test_amortized_initiation_totals_reconcile():
    """Total recognized over the tenure window equals total cash collected."""
    m = CFG["income"]["membership"]
    horizon = len(m["ramp"]) + m["expected_tenure_years"] + 2
    sched = two_stack.membership_schedule(CFG, horizon)
    recognized = sum(
        two_stack._initiation_recognized(CFG, y, sched, "amortized")
        for y in range(1, horizon + 1)
    )
    collected = sched[-1] * m["initiation_fee_usd"]
    assert approx(recognized, collected, tol=1e-9)


def test_opex_does_not_ramp_with_membership():
    """You insure and maintain the full circuit from day one."""
    years = two_stack.project_income(CFG, years=6)
    esc = CFG["income"]["membership"]["dues_escalator"]
    y1, y3 = years[0], years[2]
    assert approx(y3.opex, y1.opex * (1 + esc) ** 2)


def test_noi_is_positive_at_stabilization():
    r = two_stack.underwrite(CFG, "NOI")
    assert r.stabilized_noi > 0, "placeholder assumptions produce a negative NOI"


# =============================================================================
# Stack A
# =============================================================================

def test_for_sale_proceeds_exclude_vertical_cost():
    """Vertical cost lives in hard cost; proceeds are net of selling cost only."""
    fs = two_stack.project_for_sale(CFG)
    expected = fs.total_gross_revenue - fs.cost_of_sale
    assert approx(fs.net_proceeds, expected)


def test_for_sale_vertical_cost_lands_in_hard_cost():
    fs = two_stack.project_for_sale(CFG)
    cost = two_stack.build_cost_stack(CFG, fs)
    assert cost.hard > fs.total_vertical_cost
    # Rebuild with a zero-unit program and confirm hard cost drops by exactly the delta.
    c2 = copy.deepcopy(CFG)
    c2["for_sale"]["garage_condos"]["units"] = 0
    c2["for_sale"]["homesites"]["units"] = 0
    fs2 = two_stack.project_for_sale(c2)
    cost2 = two_stack.build_cost_stack(c2, fs2)
    assert approx(cost.hard - cost2.hard, fs.total_vertical_cost)


# =============================================================================
# Price feasibility
# =============================================================================

def _net_ranked_cfg():
    """
    Config copy that ranks on the NET basis.

    The placeholder assumptions produce a NEGATIVE max supportable land price on
    the gross basis, so the >20% feasibility boundary cannot be exercised there
    -- every ask is infeasible by definition. Net basis is positive, which lets
    us test the boundary arithmetic against real config rather than a fixture.
    """
    c = copy.deepcopy(CFG)
    c["mandate"]["yoc_basis"]["rank_on"] = "net"
    return c


def test_price_infeasible_triggers_above_20pct_over_max():
    cfg = _net_ranked_cfg()
    r0 = two_stack.underwrite(cfg, "PROBE")
    assert r0.max_land_net > 0, "test precondition: net basis must be feasible"

    ok = two_stack.underwrite(cfg, "OK", ask_price=r0.max_land_net * 1.15)
    bad = two_stack.underwrite(cfg, "BAD", ask_price=r0.max_land_net * 1.25)
    assert not ok.price_infeasible
    assert bad.price_infeasible


def test_negative_max_land_is_infeasible_at_any_ask():
    """
    When the income stack cannot carry the vertical even on free land, every
    ask is PRICE-INFEASIBLE -- including a nominal $1. This is the current state
    of the gross basis under placeholder assumptions.
    """
    r0 = two_stack.underwrite(CFG, "PROBE")
    if r0.max_land_gross > 0:
        return  # assumptions were revised to gross-feasible; nothing to assert
    for ask in (1.0, 1_000_000.0, 50_000_000.0):
        r = two_stack.underwrite(CFG, "NEG-MAX", ask_price=ask)
        assert r.price_infeasible
        assert not r.hurdle_cleared


def test_hurdle_cleared_exactly_at_max_supportable():
    """Round-trip through the full underwrite path, on a feasible basis."""
    cfg = _net_ranked_cfg()
    r0 = two_stack.underwrite(cfg, "PROBE")
    r = two_stack.underwrite(cfg, "AT-MAX", ask_price=r0.max_land_net)
    assert r.hurdle_cleared
    assert approx(r.yoc_net_at_ask, HURDLE)


def test_yoc_falls_as_land_price_rises():
    """Monotonicity on absolute prices -- independent of the sign of max land."""
    lo = two_stack.underwrite(CFG, "LO", ask_price=5_000_000)
    hi = two_stack.underwrite(CFG, "HI", ask_price=50_000_000)
    assert lo.yoc_gross_at_ask > hi.yoc_gross_at_ask
    assert lo.yoc_net_at_ask > hi.yoc_net_at_ask


def test_negative_basis_returns_neg_inf_not_crash():
    r = two_stack.underwrite(CFG, "NEG")
    y = two_stack.yield_on_cost(r.stabilized_noi, -10**12, r.cost, r.for_sale, "gross")
    assert y == float("-inf")


# =============================================================================
# Gates
# =============================================================================

def _base_parcel(**over):
    p = {
        "parcel_id": "TEST-001",
        "state": "NY",
        "county": "Dutchess",
        "municipality": "Test Town",
        "apn": "1234-56-789",
        "latitude": 41.7,
        "longitude": -73.9,
        "listing_url": "https://example.invalid/listing",
        "contiguous_developable_acres": 420,
        "contiguous_acres_under_8pct_grade": 260,
        "nearest_residence_ft": 4200,
        "residences_within_1mi": 12,
        "pct_floodway": 0.02,
        "pct_wetlands": 0.06,
        "pct_watercourse_buffer": 0.03,
        "has_legal_road_frontage": True,
        "prior_use": "reclaimed_quarry",
        "zoning_posture": "special_permit",
        "noise_ordinance_dba_day": 70,
        "noise_measurement_point": "property line",
        "noise_standard_type": "absolute",
        "drive_times_min": {"Manhattan": 105, "Greenwich": 88, "Short Hills": 132},
        "owner_type": "llc",
    }
    p.update(over)
    return p


def test_gate1_rejects_under_hard_floor():
    r = gates.gate1_hard_knockouts(_base_parcel(contiguous_developable_acres=180), CFG)
    assert not r.passed
    assert any("acreage floor" in x.lower() for x in r.reasons)


def test_gate1_flags_sub_scale_band():
    """250-350 survives but must carry the SUB-SCALE flag."""
    r = gates.gate1_hard_knockouts(_base_parcel(contiguous_developable_acres=300), CFG)
    assert r.passed
    assert any("SUB-SCALE" in f for f in r.flags)


def test_gate1_accepts_at_preferred_floor_without_flag():
    r = gates.gate1_hard_knockouts(_base_parcel(contiguous_developable_acres=350), CFG)
    assert r.passed
    assert not any("SUB-SCALE" in f for f in r.flags)


def test_gate1_assemblage_can_reach_the_floor():
    r = gates.gate1_hard_knockouts(
        _base_parcel(
            contiguous_developable_acres=190,
            assemblage_possible=True,
            assemblage_adjacent_acres=120,
        ),
        CFG,
    )
    assert r.passed
    assert any("ASSEMBLAGE" in f for f in r.flags)


def test_gate1_rejects_excluded_jurisdictions():
    for zone in gates.EXCLUSION_ZONES:
        r = gates.gate1_hard_knockouts(_base_parcel(jurisdiction_flags=[zone]), CFG)
        assert not r.passed, f"{zone} must be an auto-reject"


def test_gate1_rejects_close_residence_without_buffer():
    r = gates.gate1_hard_knockouts(_base_parcel(nearest_residence_ft=900), CFG)
    assert not r.passed


def test_gate1_allows_close_residence_with_buffer():
    r = gates.gate1_hard_knockouts(
        _base_parcel(nearest_residence_ft=900, has_intervening_buffer=True), CFG
    )
    assert r.passed
    assert any("CLOSE-NEIGHBOR" in f for f in r.flags)


def test_gate1_rejects_over_constrained_land():
    r = gates.gate1_hard_knockouts(
        _base_parcel(pct_floodway=0.20, pct_wetlands=0.20, pct_watercourse_buffer=0.05), CFG
    )
    assert not r.passed


def test_gate1_woh_watershed_rejects_when_confirmed():
    r = gates.gate1_hard_knockouts(
        _base_parcel(county="Sullivan", in_woh_watershed=True), CFG
    )
    assert not r.passed
    r2 = gates.gate1_hard_knockouts(_base_parcel(county="Sullivan"), CFG)
    assert r2.passed and any("WATERSHED-CHECK" in f for f in r2.flags)


def test_gate2_kills_exposed_greenfield():
    r = gates.gate2_noise_entitlement(
        _base_parcel(prior_use="greenfield_agricultural", residences_within_1mi=90), CFG
    )
    assert not r.passed


def test_gate2_never_invents_a_dba_limit():
    """§10: an unpublished ordinance is a research task, not a number."""
    r = gates.gate2_noise_entitlement(_base_parcel(noise_ordinance_dba_day=None), CFG)
    assert r.passed
    assert any("ORDINANCE-UNVERIFIED" in f for f in r.flags)


def test_gate2_kills_unachievable_absolute_ordinance():
    r = gates.gate2_noise_entitlement(
        _base_parcel(noise_ordinance_dba_day=50, noise_standard_type="absolute"), CFG
    )
    assert not r.passed


def test_gate2_flags_ct_home_rule():
    r = gates.gate2_noise_entitlement(_base_parcel(state="CT"), CFG)
    assert any("CT-HOME-RULE" in f for f in r.flags)


def test_gate2_flags_golf_conversion_priority():
    r = gates.gate2_noise_entitlement(_base_parcel(prior_use="golf_course"), CFG)
    assert any("GOLF-CONVERSION" in f for f in r.flags)


def test_gate3_rejects_beyond_120_minutes():
    r = gates.gate3_market_catchment(
        _base_parcel(drive_times_min={"Manhattan": 145, "Greenwich": 138, "Short Hills": 160}),
        CFG,
    )
    assert not r.passed


def test_gate3_accepts_at_the_120_boundary():
    r = gates.gate3_market_catchment(_base_parcel(drive_times_min={"Manhattan": 120}), CFG)
    assert r.passed


def test_gate5_rejects_conservation_easement():
    r = gates.gate5_deal_control(_base_parcel(conservation_easement=True), CFG)
    assert not r.passed


def test_funnel_stops_at_first_failure():
    p = _base_parcel(contiguous_developable_acres=100)
    res = gates.screen(p, CFG)
    assert res.killed_at == gates.Gate.HARD_KNOCKOUT
    assert not res.survived


def test_funnel_survivor_clears_all_five():
    res = gates.screen(_base_parcel(), CFG)
    assert res.survived
    assert res.passed_through == gates.Gate.DEAL_CONTROL


def test_gates_1_and_2_only_mode():
    res = gates.screen(_base_parcel(), CFG, stop_after=gates.Gate.NOISE_ENTITLEMENT)
    assert res.passed_through == gates.Gate.NOISE_ENTITLEMENT


def test_required_identifiers_enforced():
    ok, missing = gates.has_required_identifiers(_base_parcel())
    assert ok and not missing
    bad = _base_parcel()
    del bad["latitude"]
    bad["listing_url"] = ""
    ok2, missing2 = gates.has_required_identifiers(bad)
    assert not ok2
    assert set(missing2) == {"latitude", "listing_url"}


# =============================================================================
# Scoring
# =============================================================================

def test_weights_total_100():
    assert sum(CFG["scoring"]["weights"].values()) == 100


def test_composite_cannot_exceed_100():
    p = _base_parcel(
        prior_use="airport_airfield",
        zoning_posture="as_of_right",
        nearest_residence_ft=9000,
        residences_within_1mi=2,
        contiguous_developable_acres=500,
        contiguous_acres_under_8pct_grade=450,
        natural_amphitheater=True,
        hnw_households_90min=500_000,
        water_source="municipal",
        sewer="municipal",
        existing_paved_runway=True,
        owner_type="bankruptcy",
        days_on_market=700,
        option_feasible=True,
        phaseable=True,
        expansion_land_adjacent_acres=400,
        alternate_use="industrial_park",
        noise_ordinance_dba_day=75,
    )
    uw = two_stack.underwrite(CFG, "MAX", ask_price=1_000_000)
    s = scoring.composite_score(p, CFG, uw)
    assert 0 <= s.total <= 100


def test_composite_floor_is_non_negative():
    p = _base_parcel(
        prior_use="greenfield_forest",
        zoning_posture="prohibited_no_amendment_path",
        nearest_residence_ft=1500,
        residences_within_1mi=200,
        contiguous_developable_acres=250,
        conservation_easement=True,
    )
    uw = two_stack.underwrite(CFG, "MIN", ask_price=500_000_000)
    s = scoring.composite_score(p, CFG, uw)
    assert s.total >= 0


def test_prior_use_beats_greenfield_all_else_equal():
    quarry = scoring.composite_score(_base_parcel(prior_use="reclaimed_quarry"), CFG)
    green = scoring.composite_score(_base_parcel(prior_use="greenfield_forest"), CFG)
    assert quarry.total > green.total


def test_sub_scale_acreage_is_penalized():
    big = scoring.composite_score(_base_parcel(contiguous_developable_acres=400), CFG)
    small = scoring.composite_score(_base_parcel(contiguous_developable_acres=270), CFG)
    assert big.total > small.total


def test_price_infeasible_scores_zero_on_yield():
    uw = two_stack.underwrite(CFG, "INF", ask_price=10**12)
    raw, _ = scoring.score_yield(uw, CFG)
    assert raw == 0.0


def test_ranking_is_descending():
    scores = [
        scoring.composite_score(_base_parcel(parcel_id=f"P{i}", contiguous_developable_acres=a), CFG)
        for i, a in enumerate([260, 400, 320, 500, 380])
    ]
    ranked = scoring.rank(scores, top_n=5)
    assert [s.total for s in ranked] == sorted([s.total for s in scores], reverse=True)


# =============================================================================
# Sensitivity
# =============================================================================

def test_sensitivity_grid_shape():
    g = two_stack.sensitivity_grid(CFG, "membership_cap", "annual_dues_usd")
    assert len(g["cells"]) == len(g["y_values"])
    assert all(len(row) == len(g["x_values"]) for row in g["cells"])


def test_higher_dues_supports_higher_land_price():
    g = two_stack.sensitivity_grid(CFG, "membership_cap", "annual_dues_usd")
    col = [row[len(g["x_values"]) // 2] for row in g["cells"]]
    assert col == sorted(col), "max supportable land must rise with dues"


def test_higher_track_cost_lowers_supportable_land():
    g = two_stack.sensitivity_grid(
        CFG, "track_hard_cost_per_mile_usd", "annual_dues_usd"
    )
    row = g["cells"][0]
    assert row == sorted(row, reverse=True), "costlier pavement must reduce land headroom"


def test_config_validation_rejects_bad_weights():
    bad = copy.deepcopy(CFG)
    bad["scoring"]["weights"]["optionality"] = 99
    try:
        two_stack._validate_config(bad)
    except ValueError:
        return
    raise AssertionError("bad weight table must raise")


if __name__ == "__main__":
    fns = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
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
