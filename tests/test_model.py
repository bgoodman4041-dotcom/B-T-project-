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

def test_max_land_price_round_trips_to_binding_yield_gross():
    """
    The solved land price must return the yield it was solved at. That is the
    BINDING yield -- the tighter of the equity hurdle and the DSCR-implied
    yield -- not the hurdle in isolation.
    """
    r = two_stack.underwrite(CFG, "RT-GROSS")
    y = two_stack.yield_on_cost(
        r.stabilized_noi, r.max_land_gross, r.cost, r.for_sale, "gross", CFG
    )
    assert approx(y, r.required_yield), f"gross round-trip gave {y:.8f}"


def test_max_land_price_round_trips_to_binding_yield_net():
    r = two_stack.underwrite(CFG, "RT-NET")
    y = two_stack.yield_on_cost(
        r.stabilized_noi, r.max_land_net, r.cost, r.for_sale, "net", CFG
    )
    assert approx(y, r.required_yield), f"net round-trip gave {y:.8f}"


def test_yield_only_land_price_still_round_trips_to_the_hurdle():
    """The isolated equity-hurdle solve must remain exact at 6.50%."""
    r = two_stack.underwrite(CFG, "RT-YIELD")
    y = two_stack.yield_on_cost(
        r.stabilized_noi, r.max_land_gross_yield_only, r.cost, r.for_sale, "gross", CFG
    )
    assert approx(y, HURDLE), f"yield-only round-trip gave {y:.8f}, expected {HURDLE}"


def test_net_basis_supports_more_land_than_gross():
    """For-sale proceeds offset the basis, so net must support a higher price."""
    r = two_stack.underwrite(CFG, "CMP")
    assert r.max_land_net > r.max_land_gross
    # With an ad-valorem tax the gap is the proceeds scaled by h/(h+tau) and
    # then discounted by the carry factor -- the tax is levied on the gross
    # basis, so it does not shrink when proceeds offset the net basis.
    tau = two_stack.tax_load(CFG)
    h = r.required_yield
    expected_gap = (h * (r.for_sale.net_proceeds + r.cost.incentives)
                    / ((h + tau) * (1 + r.cost.carry_factor)))
    assert approx(r.max_land_net - r.max_land_gross, expected_gap, tol=1e-9)


def test_carry_accrues_on_land_not_just_improvements():
    r = two_stack.underwrite(CFG, "CARRY")
    b0 = r.cost.gross_basis(0)
    b1 = r.cost.gross_basis(10_000_000)
    assert approx(b1 - b0, 10_000_000 * (1 + r.cost.carry_factor))


# =============================================================================
# DSCR — the covenant test that runs alongside the yield hurdle
# =============================================================================

def test_mortgage_constant_matches_closed_form():
    """MC = m*i / (1 - (1+i)^-n). Verified against a hand calculation."""
    mc = two_stack.mortgage_constant(0.0725, 25, 12)
    i = 0.0725 / 12
    n = 25 * 12
    expected = 12 * i / (1 - (1 + i) ** -n)
    assert approx(mc, expected)
    # $1M at 7.25% over 25 years amortizes at roughly $86.7k/yr.
    assert 0.086 < mc < 0.087


def test_mortgage_constant_edge_cases():
    # Zero coupon returns principal only.
    assert approx(two_stack.mortgage_constant(0.0, 25, 12), 1 / 25)
    # Longer amortization always lowers the constant.
    assert two_stack.mortgage_constant(0.0725, 30) < two_stack.mortgage_constant(0.0725, 25)
    # Higher coupon always raises it.
    assert two_stack.mortgage_constant(0.09, 25) > two_stack.mortgage_constant(0.0725, 25)
    try:
        two_stack.mortgage_constant(0.07, 0)
    except ValueError:
        pass
    else:
        raise AssertionError("zero amortization must raise")


def test_dscr_implied_yield_is_product_of_three_terms():
    d = CFG["debt"]
    mc = two_stack.mortgage_constant(
        d["permanent_rate"], d["amortization_years"], d["periods_per_year"])
    assert approx(two_stack.dscr_implied_yield(CFG), d["min_dscr"] * d["target_ltc"] * mc)


def test_dscr_round_trips_at_max_supportable_land():
    """
    At the DSCR-solved land price, coverage must equal the covenant exactly.
    This is the DSCR analogue of the yield round-trip identity.
    """
    r = two_stack.underwrite(CFG, "DSCR-RT")
    implied = two_stack.dscr_implied_yield(CFG)
    for basis in ("gross", "net"):
        land = two_stack.max_supportable_land_price(
            r.stabilized_noi, r.cost, r.for_sale, implied, basis, CFG)
        got = two_stack.dscr_at(r.stabilized_noi, land, r.cost, r.for_sale, CFG, basis)
        assert approx(got, CFG["debt"]["min_dscr"]), f"{basis}: got {got}"


def test_binding_constraint_is_the_tighter_of_the_two():
    req, which = two_stack.binding_yield(CFG)
    hurdle = CFG["meta"]["hurdle_yoc"]
    implied = two_stack.dscr_implied_yield(CFG)
    assert req == max(hurdle, implied)
    assert which == ("DSCR" if implied > hurdle else "YIELD")


def test_yield_binds_at_low_leverage():
    """
    Documents the live state under v2.0. At 30% permanent LTC the DSCR-implied
    yield is only ~3.4%, so the 6.50% EQUITY HURDLE binds and DSCR has real
    cushion. Under the old 60% LTC the DSCR test bound at 6.77%. Leverage decides
    which constraint governs -- that is the point of `binding_yield`.
    """
    req, which = two_stack.binding_yield(CFG)
    assert which == "YIELD"
    assert approx(req, CFG["meta"]["hurdle_yoc"])
    assert two_stack.dscr_implied_yield(CFG) < CFG["meta"]["hurdle_yoc"]


def test_dscr_binds_once_leverage_is_high_enough():
    """The crossover must still work in the other direction."""
    hi = copy.deepcopy(CFG)
    hi["debt"]["target_ltc"] = 0.70
    req, which = two_stack.binding_yield(hi)
    assert which == "DSCR"
    assert req > hi["meta"]["hurdle_yoc"]


def test_binding_land_price_is_the_more_conservative():
    r = two_stack.underwrite(CFG, "BIND")
    assert r.max_land_gross == min(r.max_land_gross_yield_only, r.max_land_gross_dscr_only)


def test_dscr_falls_as_land_price_rises():
    r = two_stack.underwrite(CFG, "PROBE")
    lo = two_stack.dscr_at(r.stabilized_noi, 5_000_000, r.cost, r.for_sale, CFG, "net")
    hi = two_stack.dscr_at(r.stabilized_noi, 50_000_000, r.cost, r.for_sale, CFG, "net")
    assert lo > hi


def test_lower_leverage_relaxes_the_dscr_constraint():
    """Leverage scales the DSCR-implied yield linearly."""
    low = copy.deepcopy(CFG)
    low["debt"]["target_ltc"] = CFG["debt"]["target_ltc"] / 2
    assert two_stack.dscr_implied_yield(low) < two_stack.dscr_implied_yield(CFG)
    # Land price only improves when DSCR was the binding constraint to begin with.
    hi = copy.deepcopy(CFG)
    hi["debt"]["target_ltc"] = 0.70
    hi_low = copy.deepcopy(hi)
    hi_low["debt"]["target_ltc"] = 0.50
    assert (two_stack.underwrite(hi_low, "L").max_land_gross
            > two_stack.underwrite(hi, "H").max_land_gross)


def test_higher_dscr_floor_tightens_land_price():
    """
    Only once the covenant is the binding constraint. At the base 30% LTC the
    equity hurdle binds, so a modestly higher floor changes nothing -- which is
    itself correct and worth asserting.
    """
    base = two_stack.underwrite(CFG, "B").max_land_gross
    mild = copy.deepcopy(CFG)
    mild["debt"]["min_dscr"] = 1.50
    assert approx(two_stack.underwrite(mild, "M").max_land_gross, base)

    binding = copy.deepcopy(CFG)
    binding["debt"]["min_dscr"] = 3.00      # high enough to overtake the hurdle
    assert two_stack.underwrite(binding, "T").max_land_gross < base


def test_hurdle_cleared_requires_both_yield_and_coverage():
    """A deal that yields well but does not cover is not financeable."""
    r = two_stack.underwrite(CFG, "BOTH", ask_price=1.0)
    if r.hurdle_cleared:
        assert r.dscr_cleared, "hurdle_cleared must not be True while DSCR fails"


def test_boundary_comparison_tolerates_float_error():
    """
    A deal solved to sit exactly ON its covenant must pass. Coverage computes to
    1.2999999999999998 against a 1.30 floor, and an exact `>=` reported that
    compliant deal as a breach.
    """
    assert two_stack._at_least(1.2999999999999998, 1.30)
    assert two_stack._at_least(1.30, 1.30)
    assert not two_stack._at_least(1.29, 1.30)
    assert not two_stack._at_least(float("nan"), 1.30)
    assert two_stack._at_least(0.06499999999999999, 0.065)


def test_deal_exactly_on_both_floors_is_reported_as_clearing():
    cfg = _net_ranked_cfg()
    r0 = two_stack.underwrite(cfg, "P")
    r = two_stack.underwrite(cfg, "AT", ask_price=r0.max_land_net)
    assert r.dscr_cleared and r.hurdle_cleared


def test_dscr_reported_on_both_bases():
    r = two_stack.underwrite(CFG, "TWO", ask_price=9_800_000)
    assert r.dscr_gross_at_ask is not None and r.dscr_net_at_ask is not None
    # Net basis is smaller, so coverage on it is always the higher number.
    assert r.dscr_net_at_ask > r.dscr_gross_at_ask


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
    Config copy that ranks on the NET basis AND actually clears it.

    The placeholder assumptions are infeasible on both bases once property tax
    is charged, so the >20% boundary and the at-the-money identity cannot be
    exercised on them -- every ask is infeasible by definition. Scaling revenue
    up until the net basis clears lets the boundary arithmetic be tested against
    real config rather than a hand-built fixture. The multiplier is a test
    device; it is not an assumption about the program.
    """
    c = copy.deepcopy(CFG)
    c["mandate"]["yoc_basis"]["rank_on"] = "net"
    m = c["income"]["membership"]
    m["annual_dues_usd"] *= 2.5
    for k in c["income"]["ancillary_annual_usd"]:
        c["income"]["ancillary_annual_usd"][k] *= 2.5
    assert two_stack.underwrite(c, "PRECHK").max_land_net > 0, (
        "test helper must produce a net-feasible config")
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
    """
    At the binding land price both tests sit exactly on their floor: the yield
    clears the hurdle with room (because DSCR binds tighter) and coverage lands
    on the covenant to the cent.
    """
    cfg = _net_ranked_cfg()
    r0 = two_stack.underwrite(cfg, "PROBE")
    r = two_stack.underwrite(cfg, "AT-MAX", ask_price=r0.max_land_net)
    assert r.hurdle_cleared, "both yield and coverage must pass at the binding price"
    assert approx(r.yoc_net_at_ask, r.required_yield)
    assert r.yoc_net_at_ask >= HURDLE
    # Coverage sits exactly ON the covenant only when DSCR is the binding
    # constraint. At low leverage the yield binds and DSCR carries cushion, so
    # the invariant is "meets the floor", not "equals it".
    assert two_stack._at_least(r.dscr_net_at_ask, cfg["debt"]["min_dscr"])
    if r.binding_constraint == "DSCR":
        assert approx(r.dscr_net_at_ask, cfg["debt"]["min_dscr"])


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


def test_sensitivity_applies_both_axes():
    """
    Regression: chaining the two axis mutations with `or` short-circuited as
    soon as the x axis returned a per-mile override, silently dropping the y
    axis and producing a grid whose rows were all identical.
    """
    for x_key, y_key in [
        ("track_hard_cost_per_mile_usd", "annual_dues_usd"),
        ("membership_cap", "track_hard_cost_per_mile_usd"),
        ("membership_cap", "annual_dues_usd"),
    ]:
        g = two_stack.sensitivity_grid(CFG, x_key, y_key)
        rows = g["cells"]
        assert any(r != rows[0] for r in rows[1:]), f"y axis {y_key} had no effect"
        assert any(len(set(r)) > 1 for r in rows), f"x axis {x_key} had no effect"


def test_absorption_reaches_yield_through_carry():
    """
    A sensitivity axis that cannot move the number is decorative. Absorption
    reaches YoC only through carry duration, so a slower sell-out must lower
    the supportable land price.
    """
    if not CFG["cost"]["carry"].get("follows_absorption", False):
        return
    g = two_stack.sensitivity_grid(CFG, "absorption_years", "annual_dues_usd")
    for row in g["cells"]:
        assert row == sorted(row, reverse=True), "slower sell-out must cost land headroom"
        assert len(set(row)) > 1, "absorption axis is flat"


def test_carry_period_follows_sellout_when_longer():
    fs = two_stack.project_for_sale(CFG)
    cost = two_stack.build_cost_stack(CFG, fs)
    dev = CFG["cost"]["carry"]["development_years"]
    if CFG["cost"]["carry"].get("follows_absorption", False):
        assert cost.carry_years == max(dev, fs.sellout_years)
    else:
        assert cost.carry_years == dev


def test_slower_sellout_raises_carry_and_lowers_land():
    if not CFG["cost"]["carry"].get("follows_absorption", False):
        return
    slow = copy.deepcopy(CFG)
    slow["for_sale"]["garage_condos"]["absorption_units_per_year"] = 4
    slow["for_sale"]["homesites"]["absorption_units_per_year"] = 2
    base = two_stack.underwrite(CFG, "BASE")
    slower = two_stack.underwrite(slow, "SLOW")
    assert slower.cost.carry_factor > base.cost.carry_factor
    assert slower.max_land_gross < base.max_land_gross


# =============================================================================
# §11 narrative
# =============================================================================

def test_narrative_returns_both_lines():
    p = _base_parcel()
    uw = two_stack.underwrite(CFG, "NARR", ask_price=9_800_000)
    cs = scoring.composite_score(p, CFG, uw)
    why, kills = scoring.narrative(cs, p, uw)
    assert why and kills
    assert not why.endswith(" ") and not kills.endswith(" ")


def test_narrative_surfaces_the_killer_flag():
    p = _base_parcel(flags="SUB-SCALE — thin buffer | PRIOR-DENIAL — denied 2019")
    cs = scoring.composite_score(p, CFG)
    _, kills = scoring.narrative(cs, p)
    assert "denied" in kills.lower(), f"most fatal flag should win, got: {kills}"


def test_narrative_reports_infeasible_income_stack():
    p = _base_parcel()
    uw = two_stack.underwrite(CFG, "INF", ask_price=5_000_000)
    if uw.max_land_gross > 0:
        return
    cs = scoring.composite_score(p, CFG, uw)
    _, kills = scoring.narrative(cs, p, uw)
    assert "any land price" in kills or "above the" in kills


def test_config_validation_rejects_bad_weights():
    bad = copy.deepcopy(CFG)
    bad["scoring"]["weights"]["optionality"] = 99
    try:
        two_stack._validate_config(bad)
    except ValueError:
        return
    raise AssertionError("bad weight table must raise")


def test_every_sensitivity_axis_spans_its_own_base_case():
    """
    The dues axis ran $16k-$28k against a $34k base case: the grid did not
    contain the deal being underwritten, so every cell described a different
    club and the "base" cell was an extrapolation off the end of the axis.
    An axis that does not bracket its own base case is not a sensitivity.
    """
    sens = CFG["sensitivity"]
    m = CFG["income"]["membership"]
    fs = CFG["for_sale"]["garage_condos"]
    bases = {
        "membership_cap": m["cap"],
        "annual_dues_usd": m["annual_dues_usd"],
        "track_hard_cost_per_mile_usd": CFG["cost"]["track"]["hard_cost_per_mile_usd"],
        "absorption_years": fs["units"] / fs["absorption_units_per_year"],
    }
    for axis, base in bases.items():
        vals = sens[axis]
        assert min(vals) <= base <= max(vals), (
            f"sensitivity axis {axis} spans {min(vals)}-{max(vals)} but the base "
            f"case is {base} — the grid does not contain the deal")


def test_plausibility_band_does_not_reject_an_operating_club():
    """
    Apex Motor Club runs 425 members over 2.27 miles = 187 per mile, and Club
    Motorsports ~120. A ceiling of 90 flagged real operating clubs as
    implausible, which is a broken guardrail, not a finding. [S25]
    """
    lo, hi = CFG["plausibility"]["members_per_track_mile"]
    for club, per_mile in (("Apex", 187), ("Club Motorsports", 120),
                           ("Concours", 100), ("Thermal", 41)):
        assert lo <= per_mile <= hi, f"band rejects {club} at {per_mile}/mile"


def test_for_sale_margin_is_reported_fully_loaded():
    """
    `build_cost_stack` puts for-sale vertical cost into HARD cost, where it draws
    soft cost and contingency like every other hard dollar. The reported margin
    ignored that load entirely -- 35.5% against a fully-loaded 17.9% -- so the
    plausibility band warned the margin was too HIGH on a figure that is fine
    once loaded, while the real exposure went unreported.
    """
    fs = two_stack.project_for_sale(CFG)
    cost = CFG["cost"]
    load = (1 + cost["soft_cost_pct_of_hard"]) * (1 + cost["contingency_pct"])
    assert load > 1.2, "fixture drift: there is no soft/contingency load to test"
    assert fs.loaded_margin_pct < fs.gross_margin_pct
    assert abs(fs.loaded_cost_psf
               - CFG["for_sale"]["garage_condos"]["hard_cost_psf"] * load) < 1e-6


def test_the_condo_margin_goes_negative_at_observed_comp_pricing():
    """
    Operating new-build track comps sell at $344-352/SF against a $454/SF
    fully-loaded cost. At that price every garage condo is delivered at a loss,
    and more units make it worse -- which is invisible in a raw-cost margin and
    is why the programme search wants fewer of them.
    """
    import copy as _c
    c = _c.deepcopy(CFG)
    c["for_sale"]["garage_condos"]["sale_price_psf"] = 348
    assert two_stack.project_for_sale(c).condo_margin_per_unit < 0
    assert two_stack.project_for_sale(CFG).condo_margin_per_unit > 0, (
        "the base case condo should still be profitable; only comp pricing breaks it")


def test_the_audit_catches_a_loss_making_condo_line():
    import copy as _c
    from model import risk as _rk
    c = _c.deepcopy(CFG)
    c["for_sale"]["garage_condos"]["sale_price_psf"] = 348
    flagged = [x for x in _rk.plausibility_report(c, 9_800_000)["checks"]
               if x.severity != "OK"]
    assert any("margin" in x.name.lower() for x in flagged), (
        "a for-sale stack delivered below cost passed the audit")


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
