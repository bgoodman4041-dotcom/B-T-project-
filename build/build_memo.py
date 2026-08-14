"""
TRACK BOSS — One-Page IC Memo (§9.B)
====================================

Times New Roman, diamond bullets, bold-label/value structure, numbered
citations, no padding. Fixed section order per §9.B:

    Recommendation -> Site -> Program -> Underwriting -> Path to Control
    -> Risks -> Ask

One page is a constraint, not a target. The builder measures the flowable
height and warns loudly if the content overruns -- it will not silently ship a
two-page "one-pager".

Usage:
    python3 build/build_memo.py --parcels data/parcels.example.csv --rank 1
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
)

from build.build_workbook import enrich, load_parcels_csv
from model import cashflow as cf_mod
from model import diligence as dil
from model import risk as rk, scenarios as sc, two_stack

SERIF = "Times-Roman"
SERIF_B = "Times-Bold"
SERIF_I = "Times-Italic"

MARGIN = 0.6 * inch
FRAME_W = LETTER[0] - 2 * MARGIN
FRAME_H = LETTER[1] - 2 * MARGIN

S_TITLE = ParagraphStyle("t", fontName=SERIF_B, fontSize=13.5, leading=16, spaceAfter=1)
S_SUB = ParagraphStyle("s", fontName=SERIF_I, fontSize=8.5, leading=10,
                       textColor=colors.HexColor("#444444"), spaceAfter=5)
S_H = ParagraphStyle("h", fontName=SERIF_B, fontSize=9.2, leading=11,
                     spaceBefore=3.0, spaceAfter=1.2)
S_BODY = ParagraphStyle("b", fontName=SERIF, fontSize=8.5, leading=9.9,
                        alignment=TA_JUSTIFY, spaceAfter=1.0)
S_BULLET = ParagraphStyle("u", fontName=SERIF, fontSize=8.5, leading=9.9,
                          leftIndent=11, firstLineIndent=-11, spaceAfter=1.0)
S_NOTE = ParagraphStyle("n", fontName=SERIF_I, fontSize=7.6, leading=9.2,
                        textColor=colors.HexColor("#555555"), spaceBefore=3)
MEMO_CITATION_LIMIT = 2

S_CITE = ParagraphStyle("c", fontName=SERIF, fontSize=7.4, leading=9,
                        leftIndent=11, firstLineIndent=-11)

# Times-Roman has no U+25C6, and reportlab silently substitutes a literal "u"
# when asked for one. ZapfDingbats is a base-14 font present in every PDF
# reader, and its "u" IS the filled diamond -- so the glyph comes from there
# while the body stays in Times per §9.B.
DIAMOND = '<font name="ZapfDingbats">u</font>'


def _usd(v: Any) -> str:
    if v is None:
        return "n/a"
    v = float(v)
    sign = "(" if v < 0 else ""
    close = ")" if v < 0 else ""
    return f"{sign}${abs(v):,.0f}{close}"


def _pct(v: Any) -> str:
    if v is None or v == float("-inf"):
        return "n/a"
    return f"{float(v):.2%}"


def _x(v: Any) -> str:
    """Coverage multiple. Infinite coverage means there is no basis to lever."""
    if v is None:
        return "n/a"
    v = float(v)
    if v in (float("inf"), float("-inf")):
        return "n/m"
    return f"{v:.2f}&times;"


def bullet(label: str, value: str) -> Paragraph:
    """Diamond bullet, bold label, plain value."""
    return Paragraph(f"{DIAMOND}&nbsp;<b>{label}:</b> {value}", S_BULLET)


def build_memo(
    parcel: dict[str, Any],
    cfg: dict[str, Any],
    diag: dict[str, Any],
    sources: list[dict[str, Any]] | None = None,
    out_dir: Path | str = "dist",
) -> Path:
    sources = sources or _default_sources()

    ask = parcel.get("ask_price") or 0.0
    # The memo describes ONE site, so it runs on that site's season, ad valorem
    # regime and cost premium -- not the national base case. Reporting a
    # nationwide pipeline's lead site at the default 210-day Northeast economics
    # would put a number on the page that no other artifact agrees with.
    scfg = two_stack.site_config(cfg, parcel)
    prem = float(parcel.get("site_cost_premium_usd") or 0.0)
    cf = cf_mod.project_cash_flow(scfg, ask, horizon_operating_years=12,
                                  site_cost_premium=prem)
    # Coverage is tested from conversion, not from the first operating day: a
    # funded debt-service reserve covers lease-up and the covenant does not bite
    # until the permanent note converts. Testing every year reported breaches
    # that are not defaults.
    tested_from = (int(round(cfg["cost"]["carry"]["development_years"]))
                   + two_stack.stabilization_year(scfg))
    cov = cf_mod.covenant_report(cf, cfg["debt"]["min_dscr"], tested_from_year=tested_from)
    spread = sc.scenario_spread(sc.run_all(scfg, ask_price=ask or None,
                                           site_cost_premium=prem))
    plaus = rk.plausibility_report(scfg, ask)

    pid = parcel.get("parcel_id", "UNKNOWN")
    muni = parcel.get("municipality", "—")
    county = parcel.get("county", "—")
    state = parcel.get("state", "—")

    story: list[Any] = []
    story.append(Paragraph("INVESTMENT COMMITTEE MEMORANDUM", S_TITLE))
    story.append(Paragraph(
        f"Track Boss &middot; Car Community Deal Lane &middot; {muni}, {county} County, {state} "
        f"&middot; {dt.date.today():%d %B %Y}", S_SUB))
    story.append(HRFlowable(width="100%", thickness=0.7, color=colors.black, spaceAfter=4))

    # --- Recommendation ------------------------------------------------------
    # THE RECOMMENDATION RUNS ON THE GOVERNING TESTS, NOT THE RETIRED ONE.
    #
    # It used to lead with the gross-basis yield hurdle, which charges the
    # retained club with the entire cost of garage condos and homesites that are
    # SOLD. That test is negative for any merchant build regardless of the dirt
    # -- the workbook already reports it as a secondary, explained line beneath
    # the governing verdict, and business plan §13 recommends retiring it. The
    # memo had not been updated, so the single most important sentence in the IC
    # document said DO NOT PROCEED on a test the rest of the package says is the
    # wrong one to ask, while equity IRR, covenant coverage and value against
    # retained cost all pointed the other way.
    stab_yr = two_stack.stabilization_year(scfg)
    dev_yrs = int(round(cfg["cost"]["carry"]["development_years"]))
    gov_cov = cf_mod.covenant_report(cf, cfg["debt"]["min_dscr"],
                                     tested_from_year=dev_yrs + stab_yr)
    irr = cf.equity_irr
    clears = (gov_cov["passes_every_year"] and irr is not None and irr > 0
              and cf.value_to_cost >= 1.0)

    if clears:
        rec = (
            f"<b>PROCEED TO OPTION — TRANCHE 1 ONLY.</b> On the governing tests {pid} "
            f"returns {_pct(irr)} equity IRR over 12 operating years, covers at "
            f"{_x(gov_cov['min_dscr_tested'])} from loan conversion against a "
            f"{cfg['debt']['min_dscr']:.2f}&times; covenant with "
            f"{gov_cov['breach_count']} breach year(s), and exits at "
            f"{_x(cf.value_to_cost)} of retained cost. Peak equity is "
            f"{_usd(cf.peak_equity_requirement)}. This recommendation authorises an "
            f"OPTION and the feasibility programme, not an acquisition — see the "
            f"conditions precedent below."
        )
    else:
        fails = []
        if not gov_cov["passes_every_year"]:
            fails.append(f"covenant coverage bottoms at {_x(gov_cov['min_dscr_tested'])} "
                         f"against a {cfg['debt']['min_dscr']:.2f}&times; floor")
        if irr is None or irr <= 0:
            fails.append("equity IRR is not positive")
        if cf.value_to_cost < 1.0:
            fails.append(f"exit value is {_x(cf.value_to_cost)} of retained cost")
        rec = (
            f"<b>DO NOT PROCEED.</b> {pid} fails the governing tests: "
            + "; ".join(fails) + ". Re-base the programme before any site is optioned."
        )

    # The retired test, reported because the mandate still names it -- never as
    # the recommendation.
    secondary = (
        f"<b>Secondary — the mandated gross-basis yield test.</b> "
        f"{diag['verdict']} This test holds stabilised club NOI against a basis that "
        f"includes garage condos and homesites the programme SELLS, so it is negative "
        f"for any merchant build at any land price. Business plan §13 recommends "
        f"replacing it with the project-return and coverage tests used above."
    )

    story.append(Paragraph("RECOMMENDATION", S_H))
    story.append(Paragraph(rec, S_BODY))
    story.append(Paragraph(secondary, S_NOTE))

    # The comparable study is the largest open item in the project and it now has
    # a partial answer that cuts against the recommendation above. An IC memo
    # that omits it is not a memo, it is a pitch.
    comp = next((x for x in sc.run_all(scfg, ask_price=ask or None,
                                       site_cost_premium=prem)
                 if x.name == "comp_repriced"), None)
    if comp is not None:
        story.append(Paragraph(
            f"<b>SUBJECT TO THE COMPARABLE SET.</b> The recommendation above rests on "
            f"member pricing the comparable study does not support. Every club priced in "
            f"the set that sustains dues above "
            f"{_usd(cfg['income']['membership']['annual_dues_usd'])} either requires a "
            f"real-estate purchase or is invitation-only; this programme cannot require one. "
            f"Repriced to the comparable set the same site returns "
            f"{_pct(comp.equity_irr)} equity IRR and covers at "
            f"{_x(comp.min_dscr_tested)} against a {cfg['debt']['min_dscr']:.2f}&times; "
            f"covenant. No comparable figure reached Verified status — retrieval was "
            f"blocked and each carries its own confidence grade. Six named calls close the "
            f"gap; they are Tranche 1 item one and a condition precedent to any option "
            f"payment.", S_BODY))

    # --- Site ----------------------------------------------------------------
    story.append(Paragraph("SITE", S_H))
    acres = parcel.get("contiguous_developable_acres")
    site_bits = [
        bullet("Parcel", f"{pid} &middot; APN {parcel.get('apn', '—')} &middot; "
                         f"{parcel.get('latitude', '—')}, {parcel.get('longitude', '—')}"),
        bullet("Acreage / prior use",
               (f"{acres:,.0f} contiguous developable acres" if acres else "unresolved")
               + " &middot; " + str(parcel.get("prior_use", "—")).replace("_", " ")),
        bullet("Nearest residence",
               f"{parcel.get('nearest_residence_ft'):,.0f} ft &middot; "
               f"{parcel.get('residences_within_1mi', '—')} residences within one mile"
               if parcel.get("nearest_residence_ft") else "UNVERIFIED"),
        bullet("Drive time", f"{parcel.get('best_drive_min', '—')} min best origin "
                             f"(ceiling {cfg['mandate']['drive_time']['max_minutes']} min)"),
        bullet("Zoning", f"{parcel.get('zoning_district', '—')} &middot; "
                         f"{str(parcel.get('zoning_posture', '—')).replace('_', ' ')}"),
    ]
    story.extend(site_bits)

    # --- Program -------------------------------------------------------------
    tr = cfg["cost"]["track"]
    fs = cfg["for_sale"]
    m = cfg["income"]["membership"]
    story.append(Paragraph("PROGRAM", S_H))
    story.extend([
        bullet("Program",
               f"{tr['miles']:.1f} mi circuit &middot; "
               f"{fs['garage_condos']['units']} garage condos @ "
               f"{fs['garage_condos']['avg_sf']:,} SF / "
               f"{_usd(fs['garage_condos']['sale_price_psf'])}/SF &middot; "
               f"{fs['homesites']['units']} homesites @ "
               f"{_usd(fs['homesites']['price_per_unit_usd'])}"),
        bullet("Membership", f"{m['cap']} cap &middot; "
                             f"{_usd(m['initiation_fee_usd'])} initiation &middot; "
                             f"{_usd(m['annual_dues_usd'])} dues &middot; merchant build, "
                             f"both for-sale components sold"),
    ])

    # --- Underwriting --------------------------------------------------------
    story.append(Paragraph("UNDERWRITING", S_H))
    story.extend([
        bullet("Stabilized NOI",
               f"{_usd(diag['stabilized_noi'])} in operating year "
               f"{two_stack.stabilization_year(scfg)} "
               f"(membership at {m['stabilization_threshold']:.0%} of cap)"),
        bullet("Net cost basis (non-land)", _usd(diag["non_land_cost"])),
        bullet("For-sale net proceeds", _usd(diag["for_sale_net_proceeds"])),
        bullet("Binding test",
               f"{_pct(diag['required_yield'])} — {diag['binding_constraint']} "
               f"({_pct(diag['hurdle'])} equity hurdle vs "
               f"{_pct(diag['dscr_implied_yield'])} implied by "
               f"{diag['min_dscr']:.2f}&times; DSCR at {cfg['debt']['target_ltc']:.0%} LTC)"),
        bullet("Max supportable land — gross basis", _usd(parcel.get("max_land_gross"))),
        bullet("Max supportable land — net basis", _usd(parcel.get("max_land_net"))),
        bullet("Ask", _usd(parcel.get("ask_price"))),
        bullet("YoC at ask",
               f"gross {_pct(parcel.get('yoc_gross_at_ask'))} &middot; "
               f"net {_pct(parcel.get('yoc_net_at_ask'))} &middot; "
               f"Year 5 gross {_pct(parcel.get('yoc_gross_year5'))}"),
        bullet("DSCR at ask",
               f"gross {_x(parcel.get('dscr_gross_at_ask'))} &middot; "
               f"net {_x(parcel.get('dscr_net_at_ask'))} &middot; "
               f"covenant floor {diag['min_dscr']:.2f}&times;"),
        bullet("Property tax", f"{_usd(diag['property_tax_annual'])}/yr &mdash; "
                               f"{diag['tax_load']:.2%} of gross basis, which adds directly "
                               f"to the required yield"),
    ])

    # --- Downside ------------------------------------------------------------
    story.append(Paragraph("DOWNSIDE AND COVERAGE", S_H))
    story.extend([
        bullet("Peak equity requirement",
               f"{_usd(cf.peak_equity_requirement)} in year {cf.peak_funding_year} &mdash; "
               f"before condo closings and initiation fees arrive"),
        bullet("Minimum DSCR across the hold",
               f"{_x(cf.min_dscr)} in year {cf.min_dscr_year} against a "
               f"{diag['min_dscr']:.2f}&times; floor &middot; "
               f"{cov['breach_count']} breach year(s) of {len(cf.dscr_by_year)}"),
        bullet("Value vs cost",
               f"{cf.value_to_cost:.2f}&times; at a {cfg['income']['exit_cap']:.2%} exit cap "
               f"&middot; break-even exit cap "
               f"{(f'{cf.breakeven_exit_cap:.2%}' if cf.breakeven_exit_cap else 'n/a')}"),
        bullet("Scenario range (max land, net)",
               f"{_usd(spread['max_land_net_high'])} best case to "
               f"{_usd(spread['max_land_net_low'])} severe &middot; "
               f"{spread['scenarios_clearing_gross']} of {spread['total_scenarios']} "
               f"scenarios clear the gross test"),
    ])
    if plaus["fail_count"]:
        story.append(Paragraph(
            f"{DIAMOND}&nbsp;<b>Internal consistency:</b> {plaus['fail_count']} implausible "
            f"and {plaus['warn_count']} questionable input relationship(s). "
            f"{[c.name for c in plaus['checks'] if c.severity == 'FAIL'][0]} is the worst.",
            S_BULLET))
    story.append(Paragraph(
        "Initiation fees are amortized over expected member tenure, not capitalized into NOI; "
        "the workbook Sensitivity tab carries the fully-excluded and fully-capitalized "
        "bookends. Model math, not a sourced figure. Permanent coupon and amortization "
        "behind the DSCR test are ASSUMED, not quoted, and leverage is unconfirmed — the "
        "coverage figures move with all three. [1][2]", S_NOTE))

    # --- Path to Control -----------------------------------------------------
    story.append(Paragraph("PATH TO CONTROL", S_H))
    story.extend([
        bullet("Owner", f"{parcel.get('owner_name') or '—'} &middot; "
                        f"{str(parcel.get('owner_type', '—')).replace('_', ' ')} &middot; "
                        f"{parcel.get('days_on_market', '—')} DOM &middot; abatement path "
                        f"{parcel.get('tax_abatement_path') or 'unresolved'}"),
        bullet("Structure", "24-month option with entitlement contingency; extension fees "
                            "credited to purchase price at closing"),
    ])

    # --- Risks ---------------------------------------------------------------
    story.append(Paragraph("RISKS", S_H))
    flags = [f.strip() for f in str(parcel.get("flags") or "").split("|") if f.strip()]
    if not clears:
        flags.insert(0, "FAILS THE GOVERNING TESTS on current assumptions")
    if comp is not None and comp.min_dscr_tested < cfg["debt"]["min_dscr"]:
        flags.insert(0, f"COMPARABLE-SET REPRICING breaks the covenant — "
                        f"{_x(comp.min_dscr_tested)} against a "
                        f"{cfg['debt']['min_dscr']:.2f}x floor at comp-supported pricing")
    for f in flags[:3]:
        story.append(Paragraph(f"{DIAMOND}&nbsp;{f}", S_BULLET))
    if not flags:
        story.append(Paragraph(f"{DIAMOND}&nbsp;No screen flags raised.", S_BULLET))

    # --- Ask -----------------------------------------------------------------
    story.append(Paragraph("ASK", S_H))
    if not clears:
        ask_txt = (
            "Approval to commission the verified comp study (§7) and re-base dues, membership "
            "cap, ancillary revenue and the for-sale margin against it. Diligence priority is "
            "set by the Diligence tab, not by intuition. No capital at risk and no site under "
            "control until the program clears the binding test on paper, the covenant holds in "
            "every year of the hold rather than at stabilization only, and the internal "
            "consistency audit is clean.")
    else:
        ask_txt = (f"Approval to execute a 24-month option on {pid} at or below "
                   f"{_usd(parcel.get('max_land_gross'))}, and to fund Phase I, a boundary "
                   f"and topographic survey, and an acoustic model.")
    story.append(Paragraph(ask_txt, S_BODY))

    # The register that sequences the above. It belongs in the ASK because it is
    # the answer to "why this order" -- and because its cheapest finding is one
    # no committee should have to open a workbook to see.
    dsum = dil.summary(dil.price(scfg, ask, prem))
    story.append(Paragraph(
        f"<b>Diligence.</b> {dsum['items']} open items priced by flexing the model over each "
        f"one's range; {dsum['covenant_breakers']} break the covenant adversely and are "
        f"conditions precedent. {dsum['free_items']} cost nothing and carry "
        f"{dsum['free_downside_bps']:,.0f} bp of downside between them — calls and records "
        f"requests. Those go first. Workbook, Diligence tab.", S_BODY))

    # --- Citations -----------------------------------------------------------
    # A one-pager cites what it leans on, not the whole register. When the
    # comparable study appended twenty-one rows the memo printed all of them and
    # spilled to 186% of a page -- the register belongs in the workbook, and the
    # memo carries the parcel's own citations plus a pointer.
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=colors.HexColor("#999999"), spaceBefore=5, spaceAfter=3))
    wanted = {t.strip() for t in str(parcel.get("source_ids") or "").split(",") if t.strip()}
    cited = [s for s in sources if str(s.get("no")) in wanted]
    if not cited:
        cited = sources[:MEMO_CITATION_LIMIT]
    for s in cited[:MEMO_CITATION_LIMIT]:
        story.append(Paragraph(
            f"[{s['no']}] <b>{s['name']}</b> — <i>Cited for: {s['cited_for']}</i> {s['url']}",
            S_CITE))
    if len(sources) > len(cited[:MEMO_CITATION_LIMIT]):
        story.append(Paragraph(
            f"Full register — {len(sources)} entries including the comparable club study — "
            f"is the workbook Sources tab. No comparable figure reached Verified; each "
            f"carries its own grade.", S_CITE))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"IC_Memo_{pid}_{dt.date.today():%Y-%m-%d}.pdf"

    doc = BaseDocTemplate(str(path), pagesize=LETTER,
                          leftMargin=MARGIN, rightMargin=MARGIN,
                          topMargin=MARGIN, bottomMargin=MARGIN,
                          title=f"IC Memo — {pid}", author="Track Boss")
    doc.addPageTemplates([PageTemplate(
        id="one", frames=[Frame(MARGIN, MARGIN, FRAME_W, FRAME_H, id="f",
                                leftPadding=0, rightPadding=0,
                                topPadding=0, bottomPadding=0)])])

    # Measure before committing: a "one-pager" that spills is a defect.
    #
    # wrap() returns the flowable's own height and NOTHING ELSE. Summing it
    # ignores spaceBefore and spaceAfter on every paragraph, which on a memo of
    # this density is over an inch of real estate -- the check passed while the
    # PDF ran to two pages. Count the spacing.
    used = 0.0
    for f in story:
        used += f.wrap(FRAME_W, FRAME_H)[1]
        style = getattr(f, "style", None)
        used += getattr(style, "spaceBefore", 0) or 0
        used += getattr(style, "spaceAfter", 0) or 0
        used += getattr(f, "spaceBefore", 0) or 0 if style is None else 0
        used += getattr(f, "spaceAfter", 0) or 0 if style is None else 0
    doc.build(story)

    if used > FRAME_H:
        print(f"  WARNING: content is {used:.0f}pt against a {FRAME_H:.0f}pt frame "
              f"({used / FRAME_H:.0%}) — memo will spill past one page.")
    return path


def _default_sources() -> list[dict[str, Any]]:
    """Shared citation register — same rows the workbook's Sources tab uses."""
    from build.build_workbook import _default_sources as reg
    return reg()


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the one-page IC memo.")
    ap.add_argument("--parcels", type=Path, required=True)
    ap.add_argument("--rank", type=int, default=1, help="1-based rank to memo")
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=Path("dist"))
    args = ap.parse_args()

    cfg = two_stack.load_config(args.config)
    universe, _ = enrich(load_parcels_csv(args.parcels), cfg)
    survivors = [p for p in universe if not p.get("killed_at_gate")]
    if not survivors:
        print("No parcels survived the funnel — nothing to memo.")
        return
    if args.rank > len(survivors):
        print(f"Only {len(survivors)} survivor(s); cannot memo rank {args.rank}.")
        return

    diag = two_stack.feasibility_diagnostic(cfg)
    path = build_memo(survivors[args.rank - 1], cfg, diag, out_dir=args.out)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
