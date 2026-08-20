"""
IC readiness — is this package fit to put in front of an investment committee?

Not "does it build" and not "is the arithmetic right"; both are covered
elsewhere. This asks the questions a committee chair asks, and it is deliberately
willing to FAIL on things that are true but badly presented.

The distinction that runs through it: this package supports a TRANCHE 1 decision
— feasibility capital against options and studies — and it does not support a
Tranche 2 construction commitment, because the revenue assumptions the whole
model rests on are not verified. Every artifact has to say that in the same
voice, or the committee will read three different recommendations from one
package.

What gets checked
-----------------
* The recommendation runs on the GOVERNING tests, never on the retired
  gross-basis hurdle, and every artifact reaches the same verdict.
* The comparable-set warning is present wherever the base case is quoted.
* No artifact promises a year-10 listing.
* The ask is sized from line items and the two kill-switch items resolve early.
* Conditions precedent exist and name the abatement and the comp study.
* Nothing claims Verified where retrieval was blocked, and no site carries a
  fabricated identifier.

Run:  python3 tests/test_ic_ready.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build.build_workbook import enrich, load_parcels_csv  # noqa: E402
from model import cashflow as cfm  # noqa: E402
from model import risk as rk  # noqa: E402
from model import roadmap as rmap  # noqa: E402
from model import scenarios as sc  # noqa: E402
from model import two_stack as ts  # noqa: E402

CFG = ts.load_config()
TARGETS = ROOT / "data" / "sites_targets.csv"

_UNIVERSE, _ = enrich(load_parcels_csv(TARGETS), CFG)
LIVE = sorted([p for p in _UNIVERSE if not p.get("killed_at_gate")],
              key=lambda p: p.get("composite_score") or 0, reverse=True)
LEAD = LIVE[0]
ASK = float(LEAD["ask_price"])
PREM = float(LEAD.get("site_cost_premium_usd") or 0.0)
LCFG = ts.site_config(CFG, LEAD)
CF = cfm.project_cash_flow(LCFG, ASK, horizon_operating_years=12, site_cost_premium=PREM)
COV = cfm.covenant_report(
    CF, CFG["debt"]["min_dscr"],
    tested_from_year=int(round(CFG["cost"]["carry"]["development_years"]))
    + ts.stabilization_year(LCFG))


def _plan_source() -> str:
    return (ROOT / "build" / "build_business_plan.py").read_text(encoding="utf-8")


def _deck_source() -> str:
    return (ROOT / "build" / "deck" / "make_deck.js").read_text(encoding="utf-8")


def _memo_source() -> str:
    return (ROOT / "build" / "build_memo.py").read_text(encoding="utf-8")


# =============================================================================
# One verdict, reached the same way everywhere
# =============================================================================

def test_the_memo_recommendation_runs_on_the_governing_tests():
    """
    It ran on the retired gross-basis hurdle, which charges the retained club
    with the full cost of units the programme SELLS and is therefore negative
    for any merchant build at any land price. The single most important sentence
    in the IC document said DO NOT PROCEED on a test the rest of the package
    reports as secondary and explained.
    """
    src = _memo_source()
    rec = src[src.index("# --- Recommendation"):src.index('story.append(Paragraph("RECOMMENDATION"')]
    assert "equity_irr" in rec and "covenant_report" in rec and "value_to_cost" in rec, (
        "the memo recommendation does not read the governing tests")
    assert "program_feasible" not in rec, (
        "the memo recommendation is still keyed off the retired gross-basis test")


def test_the_retired_test_is_labelled_wherever_it_appears():
    """It may be reported. It may not be the headline anywhere."""
    memo = _memo_source()
    assert "Secondary — the mandated gross-basis yield test" in memo, (
        "the memo prints the gross-basis verdict without labelling it secondary")
    plan = _plan_source()
    assert "SECONDARY — the mandated gross-basis yield test" in plan, (
        "the plan never REPORTS the gross-basis verdict labelled as secondary where "
        "the committee reads the numbers — recommending its retirement in a later "
        "section is not the same thing")
    assert "13. RECOMMENDED CHANGE TO THE INVESTMENT TEST" in plan, (
        "the plan does not ask the committee to rule on the test itself")


def test_every_artifact_reaches_the_same_governing_verdict():
    clears = (COV["passes_every_year"] and CF.equity_irr is not None
              and CF.equity_irr > 0 and CF.value_to_cost >= 1.0)
    # The workbook's own verdict helper must agree with the memo's arithmetic.
    from build.build_workbook import _governing_verdict
    wb = _governing_verdict(LCFG, LIVE)
    assert wb["clears"] == clears, (
        f"workbook says clears={wb['clears']}, the governing arithmetic says {clears}")


# =============================================================================
# The open item cannot be buried
# =============================================================================

def test_the_comparable_warning_appears_in_every_artifact():
    """
    A committee that reads the base case without the comp case has been given
    half the package. It appears in the workbook Executive Summary, plan §1,
    the deck and the memo — by construction, not by memory.
    """
    assert "comp_repriced" in CFG["scenarios"], "the comparable case is not modelled"
    for label, src in (("plan", _plan_source()), ("deck", _deck_source()),
                       ("memo", _memo_source()), ("workbook", (
                           ROOT / "build" / "build_workbook.py").read_text(encoding="utf-8"))):
        assert "comp_repriced" in src or "COMPARABLE" in src.upper(), (
            f"{label} never surfaces the comparable-set case")


def test_the_comparable_case_is_materially_worse_or_the_warning_is_stale():
    comp = next(x for x in sc.run_all(LCFG, ask_price=ASK, site_cost_premium=PREM)
                if x.name == "comp_repriced")
    assert (comp.equity_irr or 0) < (CF.equity_irr or 0)
    assert comp.min_dscr_tested < CFG["debt"]["min_dscr"], (
        "the comp case now clears the covenant — every warning in the package is "
        "overstated and must be re-written, not left standing")


def test_no_artifact_promises_a_listing_by_year_ten():
    lt = rmap.listing_readiness(LCFG, ASK, PREM)
    assert not lt.listable_by_year_10
    for label, src in (("plan", _plan_source()), ("deck", _deck_source())):
        assert "year-10 listing" not in src.lower(), f"{label} promises a year-10 listing"


# =============================================================================
# The ask
# =============================================================================

def test_the_ask_is_built_from_line_items_and_sequenced():
    t1 = ts.tranche_1_budget(CFG)
    assert t1["items"], "there is no Tranche 1 budget"
    assert abs(t1["total"] - t1["subtotal"] * (1 + t1["contingency_pct"])) < 1.0
    by_name = {i["name"].lower(): i for i in t1["items"]}
    comp = next(v for k, v in by_name.items() if "comparable club" in k)
    assert comp["month"] <= 6, "the largest uncertainty is not resolved in the first half-year"


def test_the_two_asks_are_not_confused():
    """
    Peak construction equity is two orders of magnitude above the feasibility
    raise. A package that lets a reader think it is asking for the larger number
    today will be declined for the wrong reason.
    """
    t1 = ts.tranche_1_budget(CFG)["total"]
    assert CF.peak_equity_requirement > t1 * 10
    plan = _plan_source()
    assert "Tranche 1" in plan and "Tranche 2" in plan
    assert "not requested today" in plan, (
        "the plan does not say plainly that construction equity is not being asked for")


def test_the_ask_reconciles_against_the_diligence_register():
    """
    A budget nobody can tie to a question list is a number to argue about. The
    register claims each line of the ask, and the one line that is not a
    diligence item is named rather than absorbed into a rounding note.
    """
    from model import diligence as dil
    r = dil.reconcile(CFG)
    assert r["clean"], (
        f"the ask and the diligence register do not reconcile: orphans "
        f"{r['orphan_items']}, unclaimed {r['unclaimed_lines']}, mismatched "
        f"{r['mismatched_lines']}")


def test_the_diligence_register_reaches_every_artifact():
    """
    The committee will ask what is unverified and what it costs to find out. The
    answer exists; it has to be in the documents they read, not only in a module.
    """
    for label, src in (("plan", _plan_source()), ("memo", _memo_source()),
                       ("workbook", (ROOT / "build" / "build_workbook.py")
                        .read_text(encoding="utf-8")),
                       ("deck", (ROOT / "build" / "deck" / "export_data.py")
                        .read_text(encoding="utf-8"))):
        assert "diligence" in src.lower(), (
            f"{label} never surfaces the diligence register")


def test_the_free_diligence_finding_is_stated_where_it_will_be_read():
    """
    Eight of the twenty items cost nothing and carry more downside than most of
    the funded studies. That is the most actionable sentence the analysis
    produced, and it is worthless inside a module.
    """
    from model import diligence as dil
    s = dil.summary(dil.price(LCFG, ASK, PREM))
    assert s["free_items"] >= 5 and s["free_downside_bps"] > 1_000
    for label, src in (("plan", _plan_source()), ("memo", _memo_source())):
        assert "cost nothing" in src, (
            f"{label} does not say that the cheapest diligence items carry real money")


def test_the_sequencing_claim_is_derived_and_true():
    """
    The plan, the deck and the workbook all claim the two kill-switch answers
    land before option money is at risk. That was transcribed as 'months 3 and
    7' against options in month 6, which was false. It is now derived.
    """
    months = {i["name"]: int(i["month"]) for i in ts.tranche_1_budget(CFG)["items"]}
    comp = next(v for k, v in months.items() if "Comparable club" in k)
    acoustic = next(v for k, v in months.items() if "Acoustic" in k)
    options = next(v for k, v in months.items() if "option payments" in k)
    assert comp <= options and acoustic <= options, (
        f"the package claims the comparable study (month {comp}) and the acoustic "
        f"model (month {acoustic}) land before the option payments (month {options})")
    for label, src in (("plan", _plan_source()),
                       ("deck", _deck_source()),
                       ("workbook", (ROOT / "build" / "build_workbook.py")
                        .read_text(encoding="utf-8"))):
        assert "months 3 and 7" not in src, f"{label} transcribes the sequencing months"


def test_the_package_names_the_test_that_actually_binds():
    """
    THE ONE A CHAIR WILL CATCH. The DSCR covenant is the principal's confirmed
    number, so it is quoted in every section of every artifact and the risk reads
    as a coverage story. On this capital structure it is not the tight test:
    walking any driver from the base case toward its adverse end, value against
    retained cost fails first on every item that fails at all, and on most of
    them the covenant never breaks anywhere in the range. A package that lets the
    committee discover that for itself has buried its own most important
    structural fact.
    """
    from model import diligence as dil
    b = dil.binding_summary(dil.tolerance(LCFG, ASK, PREM))
    assert b["binds"] > 0, "no item binds at all — the finding below is vacuous"
    assert b["first_to_fail"] == "value to retained cost"
    for label, src in (("plan", _plan_source()), ("memo", _memo_source()),
                       ("workbook", (ROOT / "build" / "build_workbook.py")
                        .read_text(encoding="utf-8")),
                       ("deck", (ROOT / "build" / "deck" / "make_deck.js")
                        .read_text(encoding="utf-8"))):
        assert "binding_test" in src or "binds before the covenant" in src \
            or "first_fail" in src or "binding_summary" in src, (
            f"{label} never states which governing test actually binds")


def test_no_artifact_sums_the_per_item_downsides():
    """
    Each item's downside is measured from the same base case, so adding them
    double-counts every interaction. It is also the single most obvious thing for
    a reader to do with the column, which is why every artifact carrying the
    column must carry the warning too.
    """
    from model import diligence as dil
    sv = dil.survival(LCFG, ASK, PREM)
    assert not sv["additive"]
    for label, src in (("plan", _plan_source()),
                       ("workbook", (ROOT / "build" / "build_workbook.py")
                        .read_text(encoding="utf-8"))):
        low = src.lower()
        assert "must not be added" in low or "do not add the downside" in low, (
            f"{label} prints the downside column without warning against summing it")


def test_the_survival_walk_reports_a_breaking_point_and_the_ask_matches_it():
    """
    The deal survives zero adverse answers from its own register. That is the
    arithmetic behind a Tranche-1-only recommendation, and the two have to agree:
    a package that survives nothing and asks for construction equity is
    incoherent.
    """
    from model import diligence as dil
    sv = dil.survival(LCFG, ASK, PREM)
    assert isinstance(sv["breaking_point"], int)
    if sv["breaking_point"] == 0:
        plan = _plan_source()
        assert "not requested today" in plan, (
            "the register says the deal survives no adverse answers while the plan "
            "does not say construction equity is unrequested")


def test_conditions_precedent_exist_and_name_the_real_ones():
    plan = _plan_source()
    assert "CONDITIONS PRECEDENT" in plan.upper()
    low = plan.lower()
    for item in ("abatement", "comparable"):
        assert item in low, f"conditions precedent do not mention {item}"


# =============================================================================
# Provenance discipline
# =============================================================================

def test_no_site_going_to_ic_carries_a_fabricated_identifier():
    with TARGETS.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for k in ("apn", "listing_url", "latitude", "longitude"):
                assert not r[k], f"{r['parcel_id']} carries a fabricated {k}"


def test_the_package_states_that_no_site_is_under_contract():
    for label, src in (("plan", _plan_source()), ("deck", _deck_source())):
        assert "under contract" in src.lower(), (
            f"{label} does not state that no site is under contract")


def test_the_plausibility_audit_is_clean_on_the_lead():
    rep = rk.plausibility_report(LCFG, ASK)
    assert rep["fail_count"] == 0, (
        f"{rep['fail_count']} plausibility FAIL(s) on the lead site: "
        + "; ".join(c.name for c in rep["checks"] if c.severity == "FAIL"))


def test_assumption_register_marks_what_is_unverified():
    plan = _plan_source()
    assert "ASSUMPTION REGISTER" in plan.upper()
    assert "ASSUMED" in plan, "the plan does not mark its assumed inputs"


def test_the_lead_site_is_the_one_every_artifact_describes():
    """
    site_config exists so the workbook, plan, memo and deck all describe the same
    site. A package where the cash flow runs at 210 days and the site table leads
    with a 310-day parcel is not one analysis, it is two.
    """
    for src_name in ("build_business_plan.py", "build_memo.py", "build_workbook.py"):
        src = (ROOT / "build" / src_name).read_text(encoding="utf-8")
        assert "site_config" in src, f"{src_name} does not use the lead site's own config"
    deck = (ROOT / "build" / "deck" / "export_data.py").read_text(encoding="utf-8")
    assert "site_config" in deck


def test_no_number_in_the_package_is_infinite_or_undefined():
    import math
    for p in LIVE:
        for k, v in p.items():
            if isinstance(v, float):
                assert not math.isnan(v) and not math.isinf(v), f"{p['parcel_id']}.{k}={v}"


def test_the_deck_and_plan_carry_a_securities_disclaimer():
    for label, src in (("plan", _plan_source()), ("deck", _deck_source())):
        assert re.search(r"not an offer to sell", src, re.I), (
            f"{label} carries no securities disclaimer")


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
    print(f"\n{len(fns) - failed}/{len(fns)} IC-readiness checks passed")
    sys.exit(1 if failed else 0)
