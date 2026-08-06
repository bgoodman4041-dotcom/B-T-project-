"""
Tests for the nationwide layer: market scoring, season economics, and the
per-site config overlay.

The load-bearing ones here are the *asymmetries*. A season model that lifts
revenue without lifting cost, or a tax overlay that carries a New York PILOT
into Florida, does not produce a slightly optimistic answer -- it produces a
national ranking that is upside down. Each of those failure modes has a test.

Run:  python3 tests/test_markets.py
"""

from __future__ import annotations

import copy
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model import demand  # noqa: E402
from model import gates  # noqa: E402
from model import markets as mk  # noqa: E402
from model import scoring  # noqa: E402
from model import two_stack as ts  # noqa: E402
from model.schema import COLUMN_KEYS, coerce  # noqa: E402

CFG = ts.load_config()
TARGETS = ROOT / "data" / "sites_targets.csv"


def _rows() -> list[dict]:
    with TARGETS.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def approx(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


# =============================================================================
# Market framework
# =============================================================================

def test_every_market_scores_inside_the_scale():
    for r in mk.ranked_markets():
        assert 0.0 <= r.total <= 100.0, f"{r.market.metro} scored {r.total}"


def test_ranking_is_descending():
    totals = [r.total for r in mk.ranked_markets()]
    assert totals == sorted(totals, reverse=True)


def test_weights_total_100():
    assert sum(mk.WEIGHTS.values()) == 100


def test_proven_matches_on_the_prefix_not_the_whole_string():
    """
    Several entries qualify the negative -- "None confirmed (COTA is a public
    circuit)" is still an unserved market. An exact compare counted those as
    proven and zeroed their whitespace score, which is the one thing that
    ranking is supposed to reward.
    """
    unserved = [m for m in mk.MARKETS if m.existing_clubs.startswith("None confirmed")]
    assert unserved, "fixture drift: no unserved markets left to test"
    for m in unserved:
        assert not m.proven, f"{m.metro} counted as proven"


def test_the_northeast_is_not_the_best_market_on_the_composite():
    """
    The whole reason the pipeline went national. New York has the deepest wealth
    in the country and still loses on land, friction and season. If it ever
    ranks first again, the supply-side drivers have stopped biting.
    """
    ranked = mk.ranked_markets()
    assert ranked[0].market.region != "Northeast"
    ny = next(r for r in ranked if r.market.metro == "New York metro")
    assert ny.total < ranked[0].total


def test_season_days_span_a_real_range():
    days = [m.season_days for m in mk.MARKETS]
    assert max(days) - min(days) >= 100, "season is the headline driver; it must vary"


# =============================================================================
# Season economics -- the asymmetry that inverted the national ranking
# =============================================================================

def test_season_factor_is_one_at_the_baseline():
    cfg = copy.deepcopy(CFG)
    cfg["income"]["season_days"] = cfg["income"]["season"]["baseline_days"]
    assert approx(ts.season_factor(cfg), 1.0)
    assert approx(ts.opex_season_factor(cfg, 1.0), 1.0)


def test_opex_season_factor_is_one_when_no_season_block():
    cfg = copy.deepcopy(CFG)
    cfg["income"].pop("season", None)
    assert approx(ts.opex_season_factor(cfg, 0.5), 1.0)
    assert approx(ts.season_factor(cfg), 1.0)


def test_a_longer_season_raises_both_revenue_and_cost():
    """
    Lifting ancillary with the season while holding opex flat hands a 310-day
    site a margin it has not earned. Both sides must move.
    """
    short, long = _cfg_days(150), _cfg_days(310)
    ys, yl = ts.project_income(short, years=12), ts.project_income(long, years=12)
    i = ts.stabilization_year(CFG) - 1
    assert yl[i].ancillary_revenue > ys[i].ancillary_revenue
    assert yl[i].opex > ys[i].opex


def test_a_longer_season_still_earns_a_positive_incremental_margin():
    """
    The other side of the same coin. Charging the full opex uplift against an
    ancillary line already discounted by member penetration erased the entire
    long-season advantage and put a 210-day Northeast site above a 310-day one.
    """
    i = ts.stabilization_year(CFG) - 1
    base = ts.project_income(_cfg_days(210), years=12)[i]
    sun = ts.project_income(_cfg_days(310), years=12)[i]
    assert sun.noi > base.noi
    lift = (sun.noi - base.noi) / base.noi
    assert 0.02 < lift < 0.25, f"a 100-day season difference moved NOI {lift:.1%}"


def test_opex_still_does_not_ramp_with_membership_at_the_baseline_season():
    """The flat-opex rule survives the season overlay untouched at 210 days."""
    years = ts.project_income(_cfg_days(210), years=12)
    assert approx(years[0].opex, years[-1].opex / (1 + CFG["income"]["membership"]
                                                   ["dues_escalator"]) ** (len(years) - 1),
                  tol=1e-9)


def _cfg_days(days: int) -> dict:
    cfg = copy.deepcopy(CFG)
    cfg["income"]["season_days"] = days
    return cfg


# =============================================================================
# Per-site config overlay
# =============================================================================

def test_site_config_is_a_noop_without_overrides():
    assert ts.site_config(CFG, {"parcel_id": "X"}) is CFG


def test_site_config_does_not_mutate_the_national_case():
    before = CFG["income"]["property_tax"]["abatement_pct"]
    ts.site_config(CFG, {"property_tax_abatement_pct": 0.0, "season_days": 320})
    assert CFG["income"]["property_tax"]["abatement_pct"] == before
    assert CFG["income"].get("season_days") is None


def test_the_new_york_pilot_does_not_travel():
    """
    A 50% abatement is NY-IDA-specific. Carrying it into Florida or Nevada, on
    top of a season advantage those states already have, flatters the Sun Belt
    twice for one reason.
    """
    abated = ts.site_config(CFG, {"property_tax_effective_rate": 0.0225,
                                  "property_tax_abatement_pct": 0.50})
    unabated = ts.site_config(CFG, {"property_tax_effective_rate": 0.0070,
                                    "property_tax_abatement_pct": 0.0})
    assert ts.tax_load(unabated) < ts.tax_load(abated), (
        "Arizona at 0.70% unabated should still carry less tau than New York at "
        "2.25% abated by half"
    )


def test_a_higher_local_rate_lowers_supportable_land():
    cheap = ts.underwrite(ts.site_config(CFG, {"property_tax_effective_rate": 0.0065}), "NV")
    dear = ts.underwrite(ts.site_config(CFG, {"property_tax_effective_rate": 0.0260}), "CT")
    assert cheap.max_land_net > dear.max_land_net


# =============================================================================
# The target file itself
# =============================================================================

def test_target_file_columns_are_schema_keys_in_schema_order():
    rows = _rows()
    header = list(rows[0].keys())
    assert header == [k for k in COLUMN_KEYS if k in set(header)], (
        "column order drifted from the schema -- a value can land in the wrong field"
    )


def test_no_target_profile_carries_a_fabricated_identifier():
    """
    §5 doctrine. A target profile is a submarket and a typology; APN, listing URL
    and coordinates are Tranche 1 deliverables, and inventing them is the one
    thing the sourcing protocol forbids outright.
    """
    for r in _rows():
        if r["confidence"] == gates.TARGET_PROFILE_CONFIDENCE:
            for k in ("apn", "listing_url", "latitude", "longitude"):
                assert not r[k], f"{r['parcel_id']} carries a fabricated {k}"


def test_no_target_profile_invents_a_dba_limit():
    """§10: an unpublished ordinance is a phone call, not a number."""
    for r in _rows():
        assert not r["noise_ordinance_dba_day"], f"{r['parcel_id']} invented a dBA limit"


def test_the_pipeline_is_actually_nationwide():
    rows = _rows()
    regions = {r["market_region"] for r in rows}
    assert len(regions) >= 4, f"only {regions} represented"
    assert len({r["state"] for r in rows}) >= 8


def test_every_target_carries_its_season_and_tax_regime():
    for r in _rows():
        assert r["season_days"], f"{r['parcel_id']} has no season"
        assert r["property_tax_effective_rate"], f"{r['parcel_id']} has no local tax rate"
        assert r["property_tax_abatement_pct"] != "", f"{r['parcel_id']} has no abatement view"


def test_drive_anchors_are_named_per_site():
    """
    A nationwide pipeline cannot measure a Phoenix parcel against Manhattan.
    Gate 3 and the composite both read the dict, so the anchor must travel
    with the row.
    """
    for r in _rows():
        p = coerce(r)
        times = p["drive_times_min"]
        assert times, f"{r['parcel_id']} has no drive anchors"
        assert not any(k.startswith("Anchor ") for k in times), (
            f"{r['parcel_id']} has an unnamed anchor")
        assert p["best_drive_min"] == min(times.values())


def test_the_funnel_kills_some_targets_and_survives_others():
    """A screen that passes everything is not a screen."""
    killed, survived = 0, 0
    for r in _rows():
        sr = gates.screen(coerce(r), CFG)
        killed += bool(sr.killed_at)
        survived += sr.survived
    assert killed >= 1 and survived >= 5, f"{killed} killed, {survived} survived"


# =============================================================================
# The composite, on the real national set
# =============================================================================

def test_the_yield_component_actually_discriminates():
    """
    It did not. The mandate ranks on the gross basis, which is negative for every
    merchant build regardless of the dirt, so a fifth of the composite scored a
    flat zero on all fifteen sites and the ranking was decided by the other 80
    points. The nationwide set is what made the dead weight visible.
    """
    scores = _score_all()
    yields = {pid: s.components["yield_on_cost"] for pid, s in scores.items()}
    assert max(yields.values()) > 0.0, "yield component is inert"
    assert len(set(round(v, 2) for v in yields.values())) > 3, (
        "yield component does not separate sites")


def test_yield_score_is_monotone_in_the_yield_spread():
    ranked = sorted(_underwrite_all().items(),
                    key=lambda kv: kv[1][1].yoc_net_at_ask or 0.0)
    scores = _score_all()
    seq = [scores[pid].components["yield_on_cost"] for pid, _ in ranked]
    assert seq == sorted(seq), "a site with a better yield scored worse on yield"


def test_a_positive_supportable_land_price_is_not_punished():
    """
    Dollar headroom over the ask is unstable where the supportable land price
    crosses zero: the only site in the set with a positive one scored 0.00 on
    yield while sites with negative supportable prices scored above it.
    """
    uw = _underwrite_all()
    positive = {pid for pid, (_, u) in uw.items() if u.max_land_net > 0}
    if not positive:
        return  # nothing to prove on this pricing
    scores = _score_all()
    worst_positive = min(scores[pid].components["yield_on_cost"] for pid in positive)
    for pid, (_, u) in uw.items():
        if u.max_land_net <= 0:
            assert scores[pid].components["yield_on_cost"] <= worst_positive + 1e-9, (
                f"{pid} has no supportable land price and outscored one that does")


def _underwrite_all() -> dict:
    out = {}
    for raw in _rows():
        p = coerce(raw)
        if not p.get("ask_price"):
            continue
        cfg = ts.site_config(CFG, p)
        out[p["parcel_id"]] = (p, ts.underwrite(
            cfg, p["parcel_id"], ask_price=p["ask_price"],
            site_cost_premium=float(p.get("site_cost_premium_usd") or 0.0)))
    return out


def _score_all() -> dict:
    out = {}
    for pid, (p, uw) in _underwrite_all().items():
        out[pid] = scoring.composite_score(p, CFG, uw, gates.screen(p, CFG))
    return out


# =============================================================================
# Membership demand
# =============================================================================

def _parcel(**kw):
    p = {"parcel_id": "D", "hnw_households_90min": 200_000,
         "nearest_motorsport_club_mi": 100.0, "marque_clubs_in_catchment": 10,
         "exotic_dealers_in_catchment": 10}
    p.update(kw)
    return p


def test_a_bigger_pool_gives_more_coverage():
    small = demand.assess(CFG, _parcel(hnw_households_90min=100_000))
    big = demand.assess(CFG, _parcel(hnw_households_90min=500_000))
    assert big.coverage > small.coverage
    assert approx(big.coverage / small.coverage, 5.0, tol=1e-9)


def test_a_closer_competitor_takes_more_of_the_pool():
    far = demand.assess(CFG, _parcel(nearest_motorsport_club_mi=100.0))
    near = demand.assess(CFG, _parcel(nearest_motorsport_club_mi=9.0))
    assert near.incumbent_capture > far.incumbent_capture
    assert far.incumbent_capture == 0.0, (
        "100 mi is the sentinel for an unserved market and must decay to zero")
    assert near.capturable < far.capturable


def test_marque_clubs_are_a_channel_not_extra_demand():
    """
    Their members are already inside the HNW pool. Adding them to `addressable`
    would count the same household twice; they belong in reachability.
    """
    bare = demand.assess(CFG, _parcel(marque_clubs_in_catchment=0,
                                      exotic_dealers_in_catchment=0))
    rich = demand.assess(CFG, _parcel(marque_clubs_in_catchment=18,
                                      exotic_dealers_in_catchment=22))
    assert approx(bare.addressable, rich.addressable), "channels inflated the pool"
    assert rich.reachable_share > bare.reachable_share
    assert rich.capturable > bare.capturable


def test_channel_lift_is_capped():
    absurd = demand.assess(CFG, _parcel(marque_clubs_in_catchment=500,
                                        exotic_dealers_in_catchment=500))
    assert absurd.reachable_share <= CFG["demand"]["reachable_share_base"] * (
        1 + demand.MAX_CHANNEL_LIFT) + 1e-12
    assert absurd.reachable_share <= 1.0


def test_break_even_lands_exactly_on_one_times_coverage():
    """
    The break-even is the only number here that survives the funnel rates being
    assumed, so it has to be exactly right, not approximately right.
    """
    import copy as _c
    p = _parcel()
    be = demand.demand_break_even(CFG, p)
    flexed = _c.deepcopy(CFG)
    flexed["demand"]["collector_share"] = be["collector_share"]
    assert approx(demand.assess(flexed, p).coverage, 1.0, tol=1e-9)


def test_thin_coverage_is_called_out_not_smoothed_over():
    thin = demand.assess(CFG, _parcel(hnw_households_90min=20_000))
    assert thin.verdict.startswith("DEMAND-CONSTRAINED")
    fat = demand.assess(CFG, _parcel(hnw_households_90min=900_000))
    assert fat.verdict.startswith("DEMAND-COMFORTABLE")


def test_the_national_set_actually_separates_on_demand():
    rows = [coerce(r) for r in _rows()]
    res = demand.portfolio(CFG, rows)
    covs = [r.coverage for r in res]
    assert covs == sorted(covs, reverse=True)
    assert max(covs) / min(covs) > 3.0, (
        "demand coverage does not discriminate across the national set")
    assert any(r.verdict.startswith("DEMAND-CONSTRAINED") for r in res), (
        "no site is demand-constrained — the funnel is not biting anywhere")


def test_demand_is_reported_on_a_high_composite_site_with_a_thin_pool():
    """
    Catchment scores heavily on drive time, so a site can rank near the top of
    the composite while sitting in the thinnest HNW pool in the set. Las Vegas
    does exactly that. The flag has to reach the row, or the workbook recommends
    a club nobody can fill.
    """
    rows = [coerce(r) for r in _rows()]
    thin = [r for r in demand.portfolio(CFG, rows)
            if r.verdict.startswith(("DEMAND-CONSTRAINED", "RAMP-CONSTRAINED"))]
    assert thin, "fixture drift: nothing is constrained"
    from build.build_workbook import enrich
    universe, _ = enrich([dict(r) for r in _rows()], CFG)
    flagged = {p["parcel_id"] for p in universe
               if "CONSTRAINED" in str(p.get("flags") or "")}
    for r in thin:
        if r.parcel_id in {p["parcel_id"] for p in universe}:
            assert r.parcel_id in flagged, f"{r.parcel_id} constrained but not flagged"


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
