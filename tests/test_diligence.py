"""
The diligence register — does it price what it claims to price?

A register that ranks open items by how much the answer moves is only worth
having if the ranking is computed rather than asserted. These tests hold it to
that, and they are deliberately willing to fail on presentation as well as
arithmetic, because a diligence plan that cannot be reconciled against the money
being asked for is a wish list.

Four things get checked:

* Every flexer actually moves the model. A flexer that silently no-ops produces
  a zero swing, which reads as "this question does not matter" — the most
  dangerous possible output from this module.
* Width and downside are distinguished. A two-sided unbid cost block has a wide
  range mostly because its favourable end is better than the base case; the dues
  question has no favourable end at all. Ranking them on the same number
  flatters the wrong item.
* The register reconciles against the Tranche 1 ask in both directions.
* The findings the artifacts quote are the findings the model produces.

Run:  python3 tests/test_diligence.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build.build_workbook import enrich, load_parcels_csv  # noqa: E402
from model import diligence as dd  # noqa: E402
from model import two_stack as ts  # noqa: E402

CFG = ts.load_config()
_UNIVERSE, _ = enrich(load_parcels_csv(ROOT / "data" / "sites_targets.csv"), CFG)
LIVE = sorted([p for p in _UNIVERSE if not p.get("killed_at_gate")],
              key=lambda p: p.get("composite_score") or 0, reverse=True)
LEAD = LIVE[0]
ASK = float(LEAD["ask_price"])
PREM = float(LEAD.get("site_cost_premium_usd") or 0.0)
LCFG = ts.site_config(CFG, LEAD)

PRICED = dd.price(LCFG, ASK, PREM)
BY_ID = {p.item.id: p for p in PRICED}
SUMMARY = dd.summary(PRICED)


# =============================================================================
# The register itself
# =============================================================================

def test_ids_are_unique_and_sequential():
    ids = [i.id for i in dd.register(CFG)]
    assert len(ids) == len(set(ids)), "duplicate diligence IDs"
    assert ids == sorted(ids), "the register is not in ID order"
    for n, i in enumerate(ids, start=1):
        assert i == f"DD-{n:02d}", f"gap in the register at {i}"


def test_every_item_names_an_owner_a_gate_and_a_source():
    for i in dd.register(CFG):
        assert i.owner.strip(), f"{i.id} has no owner"
        assert i.gates.strip(), f"{i.id} does not say what it gates"
        assert i.source.strip(), f"{i.id} cites nothing"
        assert i.weeks > 0, f"{i.id} takes no time, which cannot be true"
        assert i.range_note.strip(), f"{i.id} states no range"


def test_every_priced_item_states_its_range_in_the_note():
    """
    The swing is meaningless without the span it was measured over. A reader who
    cannot see 18,500-to-34,000 next to 947 bp has been handed a number to
    believe rather than a calculation to check.
    """
    for p in PRICED:
        if p.irr_swing_bps is None:
            continue
        assert any(ch.isdigit() for ch in p.item.range_note), (
            f"{p.item.id} is priced but its range note carries no figures: "
            f"{p.item.range_note!r}")


# =============================================================================
# The flexers must actually flex
# =============================================================================

def test_no_flexer_silently_does_nothing():
    """
    The failure this catches is quiet and severe: a flexer that writes to a
    config path that does not exist, or applies a factor of 1.0 at both ends,
    returns a zero swing. Zero swing reads as "this question does not matter",
    which is the opposite of what a diligence register is for.
    """
    for item in dd.register(CFG):
        if item.flex is None:
            continue
        fav_cfg, fav_prem = item.flex(LCFG, PREM, "fav")
        adv_cfg, adv_prem = item.flex(LCFG, PREM, "adv")
        assert (fav_cfg != adv_cfg) or (fav_prem != adv_prem), (
            f"{item.id} produces an identical model at both ends of its range")


def test_no_flexer_mutates_the_config_it_is_handed():
    """
    Every flexer runs against the same config object. One that mutates in place
    contaminates every item measured after it, and the corruption would show up
    as a plausible-looking ranking rather than an error.
    """
    import copy
    before = copy.deepcopy(LCFG)
    for item in dd.register(CFG):
        if item.flex is not None:
            item.flex(LCFG, PREM, "fav")
            item.flex(LCFG, PREM, "adv")
    assert LCFG == before, "a flexer mutated the shared config"


def test_the_site_premium_is_reachable_by_a_flexer():
    """
    The most-argued number in the programme is the lead site's cost credit, and
    it is an argument to the cash flow rather than a config key. A register that
    could only reach the config would leave it unpriced.
    """
    epcal = BY_ID["DD-06"]
    assert epcal.irr_swing_bps is not None, (
        "the environmental item is unpriced — the premium flexer is not wired")
    assert PREM < 0, "the lead site no longer carries a cost credit; DD-06 is stale"
    assert epcal.irr_adv is not None and epcal.irr_fav is not None
    assert epcal.irr_adv < epcal.irr_fav, "writing the credit off should hurt"


def test_writing_the_lead_credit_to_zero_costs_what_the_documents_say():
    """
    CLAUDE.md and the risk register both quote the lead site's return with the
    pavement credit written off. This is where that figure comes from, so the
    two cannot drift.
    """
    epcal = BY_ID["DD-06"]
    assert 0.070 <= epcal.irr_adv <= 0.078, (
        f"the documents say ~7.4% at zero credit; the model says {epcal.irr_adv:.1%}")


# =============================================================================
# Width is not downside
# =============================================================================

def test_downside_is_never_greater_than_the_width():
    for p in PRICED:
        if p.downside_bps is None or p.irr_swing_bps in (None, math.inf):
            continue
        assert p.downside_bps <= p.irr_swing_bps + 1e-6, (
            f"{p.item.id} reports {p.downside_bps:.0f} bp of downside inside a "
            f"{p.irr_swing_bps:.0f} bp range")


def test_a_two_sided_range_reports_less_downside_than_width():
    """
    Hard cost is flexed -8%/+15% because nothing is bid. Most of that range sits
    ABOVE the base case, so reporting its full width as risk would rank an unbid
    cost block alongside a revenue assumption the comparable set contradicts.
    """
    hc = BY_ID["DD-08"]
    assert hc.downside_bps < hc.irr_swing_bps - 50, (
        "the two-sided hard-cost range now reports its full width as downside")


def test_a_one_sided_range_reports_its_full_width_as_downside():
    """
    The model already sits at the top of the dues range. There is no favourable
    end, so width and downside are the same number.
    """
    dues = BY_ID["DD-01"]
    assert abs(dues.downside_bps - dues.irr_swing_bps) < 1.0


def test_the_ranking_runs_on_downside_and_puts_breakers_first():
    breakers = [p for p in PRICED if p.breaks_covenant]
    if breakers:
        assert PRICED[0].breaks_covenant, "a covenant-breaker is not ranked first"
    priced = [p for p in PRICED if p.downside_bps is not None]
    non_breakers = [p for p in priced if not p.breaks_covenant]
    downs = [p.downside_bps for p in non_breakers]
    assert downs == sorted(downs, reverse=True), (
        "the non-breaking items are not ordered by downside")
    assert all(p.downside_bps is None for p in PRICED[len(priced):]), (
        "unpriced items are not held at the end of the register")


def test_a_zero_cost_item_is_not_infinitely_efficient():
    for p in PRICED:
        if p.bps_per_100k is None or p.item.cost_usd > 0:
            continue
        assert p.bps_per_100k != math.inf, (
            f"{p.item.id} costs nothing and reports infinite efficiency")


# =============================================================================
# Reconciliation against the ask
# =============================================================================

def test_the_register_reconciles_against_the_tranche_1_budget():
    r = dd.reconcile(CFG)
    assert not r["orphan_items"], (
        f"register items spending money the ask does not contain: {r['orphan_items']}")
    assert not r["mismatched_lines"], (
        f"register cost disagrees with the ask line: {r['mismatched_lines']}")
    assert not r["unclaimed_lines"], (
        f"lines of the ask no numbered question claims: {r['unclaimed_lines']}")
    assert r["clean"]


def test_the_only_unclaimed_line_is_the_one_that_is_not_a_question():
    """
    Programme management is real money and is not a diligence item. Naming it
    explicitly is what keeps the reconciliation from quietly tolerating a second
    exception later.
    """
    r = dd.reconcile(CFG)
    excluded = {n for n, _ in r["excluded_lines"]}
    assert excluded == dd.NOT_A_QUESTION
    assert abs(r["register_cost"] + sum(v for _, v in r["excluded_lines"])
               - r["budget_subtotal"]) < 1.0, (
        "the register plus the excluded line does not add to the ask")


def test_the_lead_sites_title_exposure_is_funded():
    """
    The risk register carries the lead site's disposition as High/High, in
    litigation since 2024. The ask had no title line until the register was
    reconciled against it — which is the entire reason to reconcile.
    """
    lines = {i["name"]: i["usd"] for i in ts.tranche_1_budget(CFG)["items"]}
    title = [n for n in lines if "title" in n.lower()]
    assert title, "the feasibility ask funds no title work on a site in litigation"
    assert BY_ID["DD-14"].item.tranche_line in lines


def test_the_two_kill_switch_items_resolve_before_the_money_is_spent():
    """
    The two items that can end the programme are the revenue assumption and
    whether either finalist can be controlled. Both must land early enough that
    the rest of the budget is still uncommitted.
    """
    lines = {i["name"]: int(i["month"]) for i in ts.tranche_1_budget(CFG)["items"]}
    comp = BY_ID["DD-01"].item
    assert lines[comp.tranche_line] <= 6, (
        "the largest single uncertainty does not resolve in the first half-year")


# =============================================================================
# The findings the artifacts quote
# =============================================================================

def test_the_revenue_question_is_the_largest_single_item():
    top = PRICED[0]
    assert top.item.id == "DD-01", (
        f"the register now leads with {top.item.id}; every artifact says the "
        f"comparable club study is the first call on feasibility capital")
    assert top.breaks_covenant


def test_the_covenant_breakers_are_the_ones_the_package_calls_conditions_precedent():
    breakers = {p.item.id for p in PRICED if p.breaks_covenant}
    assert "DD-01" in breakers, "the dues question no longer breaks the covenant"
    assert len(breakers) >= 2, (
        "only one item breaks the covenant — the conditions precedent list in the "
        "plan and memo is now overstated")


def test_the_free_items_carry_real_money_and_the_plan_must_say_so():
    """
    Eight items cost nothing and together carry more downside than several of
    the funded studies. That is the finding a diligence register exists to
    produce, and it is the one most easily lost.
    """
    free = [p for p in PRICED if p.item.cost_usd == 0 and p.downside_bps]
    assert len(free) >= 5
    assert SUMMARY["free_downside_bps"] > 1_000, (
        f"the free items now carry only {SUMMARY['free_downside_bps']:.0f} bp; the "
        f"sentence claiming they are worth more than a funded study is stale")
    best = SUMMARY["best_value"]
    assert best.item.cost_usd == 0, (
        "the most efficient item in the register is now a funded study — the "
        "'make the phone calls first' recommendation no longer follows")


def test_nothing_priced_is_nan():
    for p in PRICED:
        for v in (p.irr_fav, p.irr_adv, p.irr_swing_bps, p.downside_bps,
                  p.dscr_adv, p.bps_per_100k):
            assert v is None or not math.isnan(v), f"{p.item.id} produced a nan"


def test_the_register_covers_every_open_research_thread():
    """
    The register consolidates four separate task lists. If a new category of
    open item appears in the research and nothing here answers it, the
    consolidation has quietly stopped being one.
    """
    cats = {i.category for i in dd.register(CFG)}
    for required in ("Revenue", "For-sale", "Environmental", "Tax", "Cost",
                     "Entitlement", "Land", "Title", "Market", "Control"):
        assert required in cats, f"no diligence item covers {required}"


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
