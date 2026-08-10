"""
Data integrity — every file against every other file.

The model has been tested hard. The DATA had not been, and the data is where the
quiet errors live: a per-acre price computed on a different denominator than
every other row, a citation marker that resolves to nothing, a site filed under
a metro it is two hours from, an unquoted comma that shifts a whole row one
column to the right and silently relabels a confidence grade.

None of those break a build. All of them mislead a reader, and several of them
feed the composite that ranks the pipeline.

Rules enforced here
-------------------
* Every CSV is rectangular. A ragged row means a field contained an unquoted
  delimiter and every value after it is in the wrong column.
* Arithmetic that appears in two places agrees: price per acre against price and
  acres, condo $/SF against price and area, best drive time against its anchors.
* Physical impossibilities are impossible: developable acres cannot exceed gross,
  flat acres cannot exceed developable.
* Cross-file identity holds: the site file, the jurisdiction register and the
  risk register describe the same fifteen targets with the same state, posture,
  timeline, abatement and noise position.
* Every bracketed citation marker resolves to a row in the source register.
* Nothing claims a confidence grade the retrieval could not support.
* A drive anchor is a WEALTH NODE. An airport, a resort corridor or an
  industrial belt is access or context, and using one as the best origin makes
  a site look closer to its buyers than it is.

Run:  python3 tests/test_data_integrity.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model import markets as mk  # noqa: E402
from model import two_stack as ts  # noqa: E402
from model.schema import coerce  # noqa: E402

DATA = ROOT / "data"
CFG = ts.load_config()


def _rows(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _raw(name: str) -> list[list[str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))


SITES = _rows("sites_targets.csv")
JURIS = _rows("jurisdictions.csv")
RISKS = _rows("risk_register.csv")
COMPS = _rows("comps_clubs.csv")
SOURCES = _rows("sources.csv")


# =============================================================================
# File shape
# =============================================================================

def test_every_csv_is_rectangular():
    """
    A ragged row means an unquoted delimiter inside a field, and every value
    after it sits one column to the right. It did: an unquoted comma in
    "Trade press / Fortune (2018, pre-opening)" pushed a source row's real
    confidence grade into the note column and left the grade reading
    " pre-opening)". Nothing failed; the register just quietly lied.
    """
    for name in ("sites_targets.csv", "jurisdictions.csv", "risk_register.csv",
                 "comps_clubs.csv", "sources.csv", "parcels.example.csv"):
        rows = _raw(name)
        if not rows:
            continue
        width = len(rows[0])
        ragged = [(i, len(r)) for i, r in enumerate(rows) if r and len(r) != width]
        assert not ragged, f"{name}: rows {ragged} do not match the {width}-column header"


def test_no_duplicate_identifiers():
    for label, rows, key in (("sites", SITES, "parcel_id"), ("jurisdictions", JURIS, "target"),
                             ("risks", RISKS, "risk_id"), ("sources", SOURCES, "no")):
        ids = [r[key] for r in rows]
        assert len(ids) == len(set(ids)), f"{label}: duplicate {key}"


# =============================================================================
# Arithmetic that appears twice must agree
# =============================================================================

def test_ask_price_per_acre_is_ask_over_gross_acres():
    """
    Land trades on gross. One row had been computed on DEVELOPABLE acres, which
    made it look 11% dearer per acre than a like-for-like comparison.
    """
    for r in SITES:
        ask, gross = float(r["ask_price"] or 0), float(r["gross_acres"] or 0)
        stated = float(r["ask_price_per_acre"] or 0)
        if not (ask and gross and stated):
            continue
        expect = ask / gross
        assert abs(stated - expect) / expect < 0.02, (
            f"{r['parcel_id']}: ask_price_per_acre {stated:,.0f} but ask/gross is "
            f"{expect:,.0f} — different denominators across rows are not comparable")


def test_acreage_is_physically_possible():
    for r in SITES:
        gross = float(r["gross_acres"] or 0)
        dev = float(r["contiguous_developable_acres"] or 0)
        flat = float(r["contiguous_acres_under_8pct_grade"] or 0)
        assert dev <= gross, f"{r['parcel_id']}: developable {dev} exceeds gross {gross}"
        assert flat <= dev, f"{r['parcel_id']}: flat {flat} exceeds developable {dev}"


def test_percentage_fields_are_fractions_not_percents():
    """A 6 in a `pct` column is 600%, and nothing downstream would notice."""
    pct_cols = ["pct_wetlands", "pct_floodway", "pct_watercourse_buffer",
                "property_tax_effective_rate", "property_tax_abatement_pct"]
    for r in SITES:
        for c in pct_cols:
            v = r.get(c)
            if v:
                assert 0.0 <= float(v) <= 1.0, f"{r['parcel_id']} {c}={v} is not a fraction"


def test_best_drive_time_is_the_minimum_of_the_named_anchors():
    for p in (coerce(r) for r in SITES):
        times = p["drive_times_min"]
        assert times, f"{p['parcel_id']}: no drive anchors"
        assert p["best_drive_min"] == min(times.values()), f"{p['parcel_id']}: best != min"


def test_no_site_exceeds_the_mandated_drive_ceiling():
    ceiling = CFG["mandate"]["drive_time"]["max_minutes"]
    for p in (coerce(r) for r in SITES):
        assert p["best_drive_min"] <= ceiling, (
            f"{p['parcel_id']}: best drive {p['best_drive_min']} exceeds the "
            f"{ceiling}-minute ceiling and should not be in the pipeline")


def test_drive_anchors_are_wealth_nodes():
    """
    The mandate measures drive time to where members live. Three sites had been
    anchored on an airport, a resort corridor and a race-shop industrial belt,
    which set a best-origin time that is not comparable to measuring a Northeast
    site against Manhattan — and catchment is 15 points of the composite.
    """
    forbidden = re.compile(
        r"airport|sky harbor|\bfbo\b|resort corridor|the strip|race shop|"
        r"industrial|logistics|port\b(?! royal)", re.I)
    for r in SITES:
        for i in (1, 2, 3):
            name = r.get(f"drive_anchor_{i}_name") or ""
            assert not forbidden.search(name), (
                f"{r['parcel_id']} anchor {i} '{name}' is access or context, not a "
                f"wealth node — it must not be able to set best_drive_min")


def test_anchor_name_and_time_are_present_together():
    for r in SITES:
        for i in (1, 2, 3):
            name, mins = r.get(f"drive_anchor_{i}_name"), r.get(f"drive_anchor_{i}_min")
            assert bool(name) == bool(mins), (
                f"{r['parcel_id']} anchor {i}: name '{name}' / time '{mins}' — one without "
                f"the other is a half-recorded fact")


# =============================================================================
# Cross-file identity
# =============================================================================

def test_every_target_appears_in_every_register():
    ids = {r["parcel_id"] for r in SITES}
    assert {r["target"] for r in JURIS} == ids, "jurisdiction register does not cover the set"


def test_site_and_jurisdiction_registers_agree_field_by_field():
    """
    Two files describing the same fifteen places will drift the moment one is
    edited alone. Every shared field is compared, not a sample.
    """
    jm = {r["target"]: r for r in JURIS}
    for r in SITES:
        j = jm[r["parcel_id"]]
        assert r["state"] == j["state"], f"{r['parcel_id']}: state"
        assert r["zoning_posture"] == j["use_posture"], f"{r['parcel_id']}: posture"
        assert (r["noise_ordinance_dba_day"] or "") == (j["noise_dba_day"] or ""), (
            f"{r['parcel_id']}: dBA '{r['noise_ordinance_dba_day']}' vs "
            f"'{j['noise_dba_day']}'")
        assert int(r["permitting_timeline_months"]) == int(float(j["timeline_researched_months"])), (
            f"{r['parcel_id']}: the site file must carry the RESEARCHED timeline")
        assert abs(float(r["property_tax_abatement_pct"] or 0)
                   - float(j["abatement_realistic_pct"] or 0)) < 1e-9, (
            f"{r['parcel_id']}: abatement")


def test_risk_register_targets_exist():
    ids = {r["parcel_id"] for r in SITES}
    for r in RISKS:
        for t in (r["applies_to_targets"] or "").split(";"):
            t = t.strip()
            assert not t or t == "ALL" or t in ids, f"{r['risk_id']}: unknown target '{t}'"


def test_every_site_metro_exists_and_its_state_belongs_to_it():
    metros = {m.metro: m for m in mk.MARKETS}
    for r in SITES:
        metro = r["market_metro"]
        assert metro in metros, f"{r['parcel_id']}: metro '{metro}' is not in markets.py"
        assert r["state"] in metros[metro].states, (
            f"{r['parcel_id']}: state {r['state']} is not in '{metros[metro].states}' for "
            f"{metro} — the site is filed under a metro it does not sit in")


def test_site_season_is_close_to_its_metro():
    """
    A site may differ from the metro average for micro-climate or elevation, but
    not by a season. A large gap means the site is filed under the wrong metro.
    """
    metros = {m.metro: m for m in mk.MARKETS}
    for r in SITES:
        gap = abs(int(r["season_days"]) - metros[r["market_metro"]].season_days)
        assert gap <= 15, (
            f"{r['parcel_id']}: {r['season_days']} days against {r['market_metro']} at "
            f"{metros[r['market_metro']].season_days} — a {gap}-day gap is a filing error")


# =============================================================================
# Citations and confidence
# =============================================================================

def test_every_citation_marker_resolves_to_the_source_register():
    """
    A marker that resolves to nothing is worse than no marker: it asserts a
    traceable source exists. The jurisdiction research used its own internal
    footnote numbering that was never written out, and those numbers were
    propagated into the data where they read as source-register IDs.
    """
    known = {s["no"] for s in SOURCES}
    for name, rows in (("sites", SITES), ("jurisdictions", JURIS),
                       ("risks", RISKS), ("comps", COMPS)):
        for r in rows:
            rid = r.get("parcel_id") or r.get("target") or r.get("risk_id") or r.get("club")
            for field, value in r.items():
                if not isinstance(value, str):
                    continue
                for num in re.findall(r"\[S?(\d+)\]", value):
                    assert num in known, (
                        f"{name} {rid} {field}: citation [{num}] has no row in "
                        f"sources.csv")


def test_a_recorded_dba_always_has_a_citation():
    """§10 both ways: never invent one, never record one without its source."""
    for r in SITES:
        if r["noise_ordinance_dba_day"]:
            assert r["noise_ordinance_citation"].strip(), (
                f"{r['parcel_id']} carries a dBA limit with no citation")
            assert re.search(r"\[S\d+\]", r["noise_ordinance_citation"]), (
                f"{r['parcel_id']} cites an ordinance with no source-register marker")


def test_nothing_in_the_comp_set_claims_verified():
    for r in COMPS:
        assert r["confidence"].strip() != "Verified", (
            f"{r['club']}: retrieval was blocked for this study — no row can be Verified")


def test_every_source_row_is_complete():
    for s in SOURCES:
        for field in ("name", "cited_for", "confidence", "accessed"):
            assert (s.get(field) or "").strip(), f"source {s['no']}: {field} is empty"


def test_target_profiles_carry_no_fabricated_identifiers():
    for r in SITES:
        if r["confidence"] == "Target Profile":
            for k in ("apn", "listing_url", "latitude", "longitude"):
                assert not r[k], f"{r['parcel_id']} carries a fabricated {k}"


# =============================================================================
# The comp register's own arithmetic
# =============================================================================

def test_comp_price_per_sf_agrees_with_price_and_area():
    for r in COMPS:
        price, sf, psf = (r["garage_condo_price_usd"], r["garage_condo_sf"],
                          r["garage_condo_psf"])
        if not (price and sf and psf):
            continue
        expect = float(price) / float(sf)
        assert abs(float(psf) - expect) / expect < 0.03, (
            f"{r['club']} [{r['membership_tier']}]: {psf}/SF against "
            f"{price}/{sf} = {expect:.0f}")


def test_comp_figures_are_in_a_survivable_range():
    """
    Catches a decimal-place slip, which is the error a reader cannot see.

    Note the zero handling. A blank dues cell means NOT PUBLISHED; a literal 0
    means published as zero, and one club really does sell a zero-dues lifetime
    tier at a $350,000 initiation. That is not a data error, it is the cleanest
    example in the set of trading recurring revenue for upfront capital, and a
    range check that rejects it would delete the finding.
    """
    for r in COMPS:
        dues = r["annual_dues_usd"]
        if dues == "0":
            assert r["note"].strip(), (
                f"{r['club']}: a zero-dues tier must carry a note saying it is "
                f"deliberate, or it is indistinguishable from a missing value")
        elif dues:
            assert 500 <= float(dues) <= 200_000, f"{r['club']}: dues {dues}"
        if r["initiation_fee_usd"]:
            assert 0 <= float(r["initiation_fee_usd"]) <= 2_000_000, (
                f"{r['club']}: initiation {r['initiation_fee_usd']}")
        if r["track_miles"]:
            assert 0 <= float(r["track_miles"]) <= 10, f"{r['club']}: {r['track_miles']} mi"
        if r["acreage"]:
            assert 10 <= float(r["acreage"]) <= 5_000, f"{r['club']}: {r['acreage']} ac"


def test_the_optional_real_estate_dues_claim_matches_the_data():
    """
    The load-bearing structural claim in the plan, the deck and CLAUDE.md is
    about what clubs charge where buying real estate is OPTIONAL. It was first
    written as "$18,500 or below, no exceptions" and the register held two:
    Concours at $35,000, which the sentence carves out as invitation-only, and
    NJMP at $20,000, which no carve-out covered.

    A claim that leans on a data file has to be checkable against it, so this
    recomputes the sentence's own numbers and fails if the prose drifts from the
    register in either direction.
    """
    optional = [r for r in COMPS
                if r["annual_dues_usd"]
                and r["real_estate_required"].strip().upper().startswith("NO")]
    assert optional, "fixture drift: no optional-real-estate club with published dues"
    by_dues = sorted(optional, key=lambda r: -float(r["annual_dues_usd"]))

    top = by_dues[0]
    assert "concours" in top["club"].lower(), (
        f"the sentence carves out one Miami club as the exception; the top "
        f"optional-real-estate club is now {top['club']}")

    runner_up = by_dues[1]
    assert float(runner_up["annual_dues_usd"]) == 20_000, (
        f"the prose says the highest optional-purchase dues outside Miami is "
        f"$20,000; the register says ${float(runner_up['annual_dues_usd']):,.0f} "
        f"({runner_up['club']})")
    assert float(runner_up["initiation_fee_usd"] or 0) == 0, (
        "the prose says that club charges no initiation fee; the register disagrees")

    six_figure = [r for r in by_dues
                  if float(r["initiation_fee_usd"] or 0) >= 100_000
                  and "concours" not in r["club"].lower()]
    assert six_figure and float(six_figure[0]["annual_dues_usd"]) == 18_500, (
        "the prose says the highest optional-purchase club charging a six-figure "
        "initiation prices dues at $18,500")

    # And the direction the whole argument rests on.
    modelled = CFG["income"]["membership"]["annual_dues_usd"]
    assert float(runner_up["annual_dues_usd"]) < modelled, (
        "the comparable set no longer undercuts the modelled dues — the warning "
        "in every artifact is stale")


def test_claude_md_test_counts_are_current():
    """
    CLAUDE.md states a test count per file, in two places, and they had drifted
    apart from each other and from the code. A document whose whole claim is
    that it contains no transcribed figures cannot carry a stale one.
    """
    md = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        actual = len(re.findall(r"^def test_", path.read_text(encoding="utf-8"), re.M))
        if actual == 0:
            continue                      # script-style checkers, not counted
        for stated in re.findall(rf"{re.escape(path.name)}\s+(\d+) tests", md):
            assert int(stated) == actual, (
                f"CLAUDE.md says {path.name} has {stated} tests; it has {actual}")
        for stated in re.findall(rf"{re.escape(path.name)}\s+#\s*(\d+) tests", md):
            assert int(stated) == actual, (
                f"CLAUDE.md command block says {path.name} has {stated}; it has {actual}")


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
