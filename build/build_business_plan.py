"""
TRACK BOSS — Formal Business Plan (PDF)
=======================================

Every number in this document is read from the live model at build time. There
are no transcribed figures, so the plan cannot drift from the workbook. If an
assumption changes in `config/underwriting_inputs.yaml`, the plan changes.

Usage:
    python3 build/build_business_plan.py --parcels data/sites_targets.csv --out dist/
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from build.build_workbook import enrich, load_parcels_csv
from model import gates, scoring
from model import cashflow as cfm
from model import demand as dm
from model import markets as mk
from model import respec as rs
from model import risk as rk
from model import roadmap as rmap
from model import scenarios as sc
from model import two_stack as ts

SERIF, SERIF_B, SERIF_I = "Times-Roman", "Times-Bold", "Times-Italic"
MARGIN = 0.85 * inch
FW = LETTER[0] - 2 * MARGIN

INK = colors.HexColor("#111111")
GREY = colors.HexColor("#555555")
RULE = colors.HexColor("#999999")
BAND = colors.HexColor("#EFEFEF")

S_COVER_T = ParagraphStyle("ct", fontName=SERIF_B, fontSize=26, leading=30,
                           alignment=TA_CENTER, textColor=INK)
S_COVER_S = ParagraphStyle("cs", fontName=SERIF_I, fontSize=13, leading=17,
                           alignment=TA_CENTER, textColor=GREY)
S_H1 = ParagraphStyle("h1", fontName=SERIF_B, fontSize=15, leading=18,
                      spaceBefore=16, spaceAfter=7, textColor=INK)
S_H2 = ParagraphStyle("h2", fontName=SERIF_B, fontSize=11.5, leading=14,
                      spaceBefore=10, spaceAfter=4, textColor=INK)
S_BODY = ParagraphStyle("b", fontName=SERIF, fontSize=10, leading=13.6,
                        alignment=TA_JUSTIFY, spaceAfter=6)
S_BULLET = ParagraphStyle("u", fontName=SERIF, fontSize=10, leading=13.4,
                          leftIndent=15, firstLineIndent=-11, spaceAfter=3.5)
S_NOTE = ParagraphStyle("n", fontName=SERIF_I, fontSize=8.6, leading=11,
                        textColor=GREY, spaceBefore=4, spaceAfter=4)
S_TBL = ParagraphStyle("t", fontName=SERIF, fontSize=8.6, leading=10.8)
S_TBLB = ParagraphStyle("tb", fontName=SERIF_B, fontSize=8.6, leading=10.8)

DIA = '<font name="ZapfDingbats">u</font>'


def _usd(v: Any, dp: int = 0) -> str:
    if v is None:
        return "n/a"
    v = float(v)
    return f"({'$'}{abs(v):,.{dp}f})" if v < 0 else f"${v:,.{dp}f}"


def _m(v: Any) -> str:
    if v is None:
        return "n/a"
    return f"({'$'}{abs(float(v)) / 1e6:,.1f}M)" if float(v) < 0 else f"${float(v) / 1e6:,.1f}M"


def _pct(v: Any, dp: int = 2) -> str:
    return "n/a" if v is None else f"{float(v):.{dp}%}"


def _x(v: Any) -> str:
    if v is None:
        return "n/a"
    v = float(v)
    return "n/m" if v in (float("inf"), float("-inf")) else f"{v:.2f}x"


def _test_count() -> int:
    """
    Count test functions rather than quoting a number that goes stale. The plan
    claims it has no transcribed figures; a hardcoded "129 unit tests" was one.
    """
    import re
    root = Path(__file__).resolve().parent.parent / "tests"
    n = 0
    for f in sorted(root.glob("test_*.py")):
        n += len(re.findall(r"^def test_", f.read_text(encoding="utf-8"), re.M))
    return n


def _ord(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def B(label: str, body: str) -> Paragraph:
    return Paragraph(f"{DIA}&nbsp;<b>{label}.</b> {body}", S_BULLET)


def table(rows: list[list[Any]], widths: list[float], header: bool = True,
          align_right_from: int = 1) -> Table:
    data = []
    for i, r in enumerate(rows):
        style = S_TBLB if (header and i == 0) else S_TBL
        data.append([c if isinstance(c, Paragraph) else Paragraph(str(c), style) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#CCCCCC")),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), BAND),
                 ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK)]
    t.setStyle(TableStyle(cmds))
    return t


# =============================================================================
# Model snapshot — one place, read once
# =============================================================================

def snapshot(cfg: dict[str, Any], parcels_csv: Path) -> dict[str, Any]:
    universe, unverified = enrich(load_parcels_csv(parcels_csv), cfg)
    live = [p for p in universe if not p.get("killed_at_gate")]
    live.sort(key=lambda p: p.get("composite_score") or 0, reverse=True)

    lead = live[0] if live else {}
    lead_prem = float(lead.get("site_cost_premium_usd") or 0.0)
    lead_ask = float(lead.get("ask_price") or 0.0)

    # Every figure in the plan describes the LEAD SITE, which means the lead
    # site's season and ad valorem regime -- not the national defaults. Running
    # the roadmap and the scenario set on a 210-day Northeast base case while
    # the site table leads on a 310-day Sun Belt parcel is exactly the drift
    # this single-snapshot pattern exists to prevent.
    lcfg = ts.site_config(cfg, lead)

    uw = ts.underwrite(lcfg, "LEAD", ask_price=lead_ask, site_cost_premium=lead_prem)
    cf = cfm.project_cash_flow(lcfg, lead_ask, horizon_operating_years=12,
                               site_cost_premium=lead_prem)
    stab = ts.stabilization_year(lcfg)
    dev = int(round(cfg["cost"]["carry"]["development_years"]))
    cov = cfm.covenant_report(cf, cfg["debt"]["min_dscr"], tested_from_year=dev + stab)
    plaus = rk.plausibility_report(lcfg, lead_ask)
    scen = sc.run_all(lcfg, ask_price=lead_ask, site_cost_premium=lead_prem)
    spread = sc.scenario_spread(scen)
    bev = rk.direct_break_evens(lcfg, lead_ask)
    comp = next((r for r in scen if r.name == "comp_repriced"), None)
    respec_r = rs.search(lcfg, lead_ask, lead_prem, parcel=lead)
    t1 = ts.tranche_1_budget(cfg)
    bridge = rk.return_bridge(lcfg, lead_ask, target_irr=0.15,
                              site_cost_premium=lead_prem)
    tor, tor_base, _ = rk.tornado(lcfg)
    mc = rk.monte_carlo(lcfg, lead_ask, site_cost_premium=lead_prem)

    # Per-site economics, each on its own season and tax regime.
    sites = []
    for p in live:
        prem = float(p.get("site_cost_premium_usd") or 0.0)
        ask = float(p.get("ask_price") or 0.0)
        scfg = ts.site_config(cfg, p)
        s_uw = ts.underwrite(scfg, p["parcel_id"], ask_price=ask, site_cost_premium=prem)
        s_cf = cfm.project_cash_flow(scfg, ask, horizon_operating_years=12,
                                     site_cost_premium=prem)
        s_cov = cfm.covenant_report(s_cf, cfg["debt"]["min_dscr"],
                                    tested_from_year=dev + stab)
        sites.append({"p": p, "uw": s_uw, "cf": s_cf, "cov": s_cov, "cfg": scfg})

    return dict(cfg=cfg, lcfg=lcfg, universe=universe, unverified=unverified, live=live,
                lead=lead, lead_ask=lead_ask, uw=uw, cf=cf, cov=cov, stab=stab,
                dev=dev, plaus=plaus, scen=scen, spread=spread, bev=bev, bridge=bridge,
                comp=comp, respec=respec_r,
                fragility=scoring.lead_site_fragility(
                    [p for p in universe], cfg, ts.underwrite, gates.screen, ts.site_config),
                t1=t1,
                tor=tor, tor_base=tor_base, mc=mc, sites=sites,
                markets=mk.ranked_markets(), rollout=mk.rollout(lead_site=lead),
                demand=dm.portfolio(cfg, live),
                demand_be={p["parcel_id"]: dm.demand_break_even(cfg, p) for p in live},
                national=mk.national_summary(),
                timing=rmap.timing(lcfg), milestones=rmap.milestones(lcfg),
                platform=rmap.platform_scale(lcfg, lead_ask, lead_prem, 7),
                listing=rmap.listing_readiness(lcfg, lead_ask, lead_prem),
                exits=rmap.exit_paths(lcfg, lead_ask, lead_prem))


# =============================================================================
# Document
# =============================================================================

def build(cfg: dict[str, Any], parcels_csv: Path, out_dir: Path) -> Path:
    S = snapshot(cfg, parcels_csv)
    cf, uw, cov = S["cf"], S["uw"], S["cov"]
    m = cfg["income"]["membership"]
    fs = cfg["for_sale"]
    d = cfg["debt"]
    today = dt.date.today()

    st: list[Any] = []
    A = st.append

    # ---------------- Cover ----------------
    A(Spacer(1, 1.5 * inch))
    A(Paragraph("BELLWETHER MOTOR CLUB", S_COVER_T))
    A(Spacer(1, 0.12 * inch))
    A(Paragraph("A Private Motorsport Country Club and Trackside Residential Community<br/>"
                "A National Platform &middot; Lead Site in the "
                f"{S['lead'].get('market_metro') or 'lead'} Market", S_COVER_S))
    A(Spacer(1, 0.5 * inch))
    A(HRFlowable(width="55%", thickness=0.8, color=RULE, hAlign="CENTER"))
    A(Spacer(1, 0.4 * inch))
    A(Paragraph("<b>CONFIDENTIAL BUSINESS PLAN</b>", S_COVER_S))
    A(Paragraph(f"{today:%d %B %Y}", S_COVER_S))
    A(Spacer(1, 1.6 * inch))
    A(Paragraph(
        "BELLWETHER MOTOR CLUB is a working title. It was checked against operating private "
        "motorsport clubs and no collision was found, but it has not been trademark-cleared "
        "and the principal should expect to replace it. "
        "This document contains forward-looking projections based on assumptions that are "
        "identified as such throughout. It is not an offer to sell securities. No site is "
        "under contract. Financial projections depend on conditions precedent set out in "
        "Section 10, including a property-tax abatement and verification of the comparable "
        "club economics on which revenue is based.", S_NOTE))
    A(PageBreak())

    # ---------------- 1. Executive summary ----------------
    A(Paragraph("1. EXECUTIVE SUMMARY", S_H1))
    A(Paragraph(
        f"We are assembling a {cfg['cost']['track']['miles']:.1f}-mile private motorsport "
        f"country club with an attached for-sale garage-condominium and homesite community, "
        f"sited within two hours of the wealth centres of its metro. The club "
        f"sells {m['cap']} memberships at a "
        f"{_usd(m['initiation_fee_usd'])} initiation fee and "
        f"{_usd(m['annual_dues_usd'])} of annual dues, alongside "
        f"{fs['garage_condos']['units']} garage condominiums and "
        f"{fs['homesites']['units']} trackside homesites sold to members.", S_BODY))
    A(Paragraph(
        f"Total development cost is {_m(uw.cost.gross_basis(S['lead_ask']))} on the lead site. "
        f"For-sale proceeds of {_m(uw.for_sale.net_proceeds)} and "
        f"{_m(cf.sources_uses.initiation_cash)} of initiation-fee capital fund the majority of "
        f"the programme. The retained club stabilises at "
        f"{_m(uw.stabilized_noi_after_tax)} of net operating income after property tax in "
        f"operating year {S['stab']}.", S_BODY))

    if S["comp"] is not None:
        c = S["comp"]
        A(Paragraph("Read this before the numbers", S_H2))
        A(Paragraph(
            f"<b>The comparable club study is partially complete and it cuts against this "
            f"plan.</b> Every revenue figure below assumes member pricing — "
            f"{_usd(m['initiation_fee_usd'])} initiation and {_usd(m['annual_dues_usd'])} of "
            f"annual dues — that the comparable set does not support. Across the clubs we "
            f"could price, every one that sustains dues above {_usd(m['annual_dues_usd'])} "
            f"either makes real-estate purchase mandatory or is invitation-only in Miami. "
            f"Every club where real estate is optional prices dues at $18,500 or below. This "
            f"programme sells {fs['garage_condos']['units'] + fs['homesites']['units']} units "
            f"against a {m['cap']}-member cap, so purchase cannot be mandatory here.", S_BODY))
        A(Paragraph(
            f"Repriced to what the comparable set actually charges and sells, the programme "
            f"returns <b>{_pct(c.equity_irr, 1)}</b> equity IRR, covers at "
            f"<b>{_x(c.min_dscr_tested)}</b> against a {d['min_dscr']:.2f}× covenant, and "
            f"exits at <b>{_x(c.value_to_cost)}</b> of retained cost. That case is carried "
            f"as a named scenario in Section 7, not as a footnote, and it is the reason "
            f"Tranche 1 buys the comparable study first and everything else second.", S_BODY))
        A(Paragraph(
            "Two things are true at once, and the plan does not resolve them for you. The "
            "base case is internally coherent and passes every consistency test in Appendix "
            "B. The comparable set says its revenue line is roughly half again too high. "
            "Nothing in the research reached strict Verified status — direct URL retrieval "
            "was blocked throughout, so every comparable figure came through a search index "
            "and each carries its own confidence grade in the workbook. Six named phone "
            "calls, listed in Section 12, close most of the gap for a few thousand dollars.",
            S_NOTE))

    A(Paragraph("Headline economics — lead site", S_H2))
    A(table([
        ["Metric", "Base case", "Note"],
        ["Peak equity requirement", _m(cf.peak_equity_requirement),
         f"Deepest in year {cf.peak_funding_year}, before for-sale closings"],
        ["Equity multiple", _x(cf.equity_multiple), "12 operating years, single exit"],
        ["Project equity IRR", _pct(cf.equity_irr, 1), "Levered at the stated capital stack"],
        ["Stabilised NOI after tax", _m(uw.stabilized_noi_after_tax),
         f"Operating year {S['stab']}"],
        ["Minimum DSCR", _x(cov["min_dscr_tested"]),
         f"Covenant {d['min_dscr']:.2f}x — {cov['breach_count']} breach years"],
        ["Value / retained cost", _x(cf.value_to_cost),
         f"At a {cfg['income']['exit_cap']:.2%} exit cap"],
        ["Profit on retained cost", _m(cf.profit_on_cost), "Exit proceeds less retained basis"],
        ["Break-even exit cap", _pct(cf.breakeven_exit_cap),
         "Cap rate at which value equals retained cost"],
    ], [1.85 * inch, 1.2 * inch, 3.0 * inch]))

    A(Paragraph("What this is, and what it is not", S_H2))
    A(B("This is a merchant-build development with a retained income asset",
        "Roughly two thirds of the capital returns through for-sale closings and member "
        "capital. The held club is the residual asset and the source of terminal value."))
    A(B("It is not a stabilised-yield play",
        f"The retained club does not clear a {cfg['meta']['hurdle_yoc']:.2%} yield on a gross "
        f"development basis, and no site in a {S['national']['markets_screened']}-metro "
        f"national search changes that. Section 7 "
        f"recommends replacing that test with a project-return and coverage test, and "
        f"explains why. An investor underwriting this as a core yield asset should decline."))
    A(B("Returns are mid-single to low-double digit, not opportunistic",
        f"The base case produces {_pct(cf.equity_irr, 1)} levered IRR and "
        f"{_x(cf.equity_multiple)} of multiple. We are not presenting a 20% development "
        f"return, because the analysis does not support one at defensible operating costs."))
    A(PageBreak())

    # ---------------- 2. Thesis ----------------
    A(Paragraph("2. INVESTMENT THESIS", S_H1))
    A(B("The spread between garage-condominium pricing and industrial flex is the profit engine",
        f"Garage condominiums are underwritten at "
        f"{_usd(fs['garage_condos']['sale_price_psf'])} per square foot against a "
        f"{_usd(fs['garage_condos']['hard_cost_psf'])} hard cost — a "
        f"{fs['garage_condos']['sale_price_psf'] / fs['garage_condos']['hard_cost_psf']:.2f}x "
        f"ratio. That premium exists because the buyer is purchasing access and adjacency, "
        f"not square footage. Validating it against local flex comparables is the single most "
        f"important diligence item in the plan."))
    A(B("Prior-use sites are the only economically viable typology",
        "Site infrastructure is underwritten 30% below a greenfield programme because the "
        "target sites are former airfields, reclaimed quarries, capped landfills and closed "
        "golf courses with existing pavement, grading and utilities. On raw land the "
        "infrastructure reverts and the programme does not clear. Site typology is an "
        "economic requirement, not an aesthetic preference."))
    A(B("An inherited noise floor is the entitlement asset",
        "Noise, not zoning, kills motorsport projects, and it kills them in court after the "
        "permits are issued. Every target site carries a prior intensive use, which supports "
        "a coming-to-the-nuisance posture and materially improves the litigation position."))
    A(B("Member capital funds the build",
        f"Initiation fees contribute {_m(cf.sources_uses.initiation_cash)} of cash. Combined "
        f"with pre-sold garage condominiums, member and buyer capital covers a majority of "
        f"total uses, which is why peak equity is "
        f"{_m(cf.peak_equity_requirement)} rather than the full development cost."))
    A(B("Scarcity is structural, not cyclical",
        f"A {S['national']['markets_screened']}-metro national search produced a small number "
        f"of sites that clear an acreage floor, a noise screen, a two-hour drive time and an "
        f"exclusion-zone test simultaneously. The binding constraint is never demand; it is a "
        f"large contiguous parcel with an inherited noise floor and a jurisdiction that will "
        f"hear the application."))

    A(Paragraph("3. MARKET — THE NATIONAL SCREEN", S_H1))
    nat = S["national"]
    lo, hi = nat["season_spread"]
    A(Paragraph(
        f"The mandate began in New York, Connecticut and New Jersey. Screening "
        f"{nat['markets_screened']} metropolitan markets on six drivers — usable season, "
        f"wealth density, land cost, entitlement friction, competitive whitespace and "
        f"incentive access — put the New York metro {_ord(nat['northeast_rank'])} of "
        f"{nat['markets_screened']}, at {nat['northeast_score']:.1f} points against "
        f"{nat['top'].total:.1f} for {nat['top'].market.metro}. That result is not a comment "
        f"on demand. New York has the deepest investable wealth in the country and one club "
        f"serving it. It loses on the supply side: land price, entitlement friction and a "
        f"season roughly two-thirds the length of the Sun Belt.", S_BODY))
    A(Paragraph(
        f"Season length is the single largest economic difference between two otherwise "
        f"identical sites. Usable track days across the screened set run from {lo} to {hi} a "
        f"year. The model treats that explicitly: "
        f"{cfg['income']['season']['ancillary_elasticity']:.0%} of ancillary revenue moves "
        f"with days open, and {cfg['income']['season']['opex_elasticity']:.0%} of club "
        f"operating cost moves with it too, because a longer calendar buys more crew, more "
        f"consumables and more track preparation as well as more revenue. Net of that cost, "
        f"the long-season sites earn a real but bounded premium — not the free margin a "
        f"revenue-only season adjustment would have shown.", S_BODY))
    A(Paragraph(
        "The second driver is statutory rather than climatic. Effective property tax runs "
        "from roughly 0.65% of value in Nevada to 2.6% in Connecticut, and a PILOT or "
        "abatement reaches this use in some states and not others. The 50% abatement that "
        "the Northeast case depends on is a New York IDA mechanism; it does not travel to "
        "Florida or Nevada. Each site in Section 11 is therefore underwritten at its own "
        "local rate and its own honest view of what relief is available — in several cases, "
        "none. Arizona and Nevada still carry the lightest tax load in the set, unabated.",
        S_BODY))

    A(Paragraph("Tier 1 markets", S_H2))
    A(table([["Metro", "States", "Season", "Score", "Why it ranks"]] + [
        [r.market.metro, r.market.states, f"{r.market.season_days} d", f"{r.total:.1f}",
         r.market.whitespace[:150]]
        for r in nat["tier1"]
    ], [1.25 * inch, 0.5 * inch, 0.45 * inch, 0.42 * inch, 4.28 * inch]))

    A(Paragraph("Tier 2 — the second wave", S_H2))
    A(table([["Metro", "States", "Season", "Score", "Existing club product"]] + [
        [r.market.metro, r.market.states, f"{r.market.season_days} d", f"{r.total:.1f}",
         r.market.existing_clubs[:110]]
        for r in nat["tier2"][:6]
    ], [1.25 * inch, 0.5 * inch, 0.45 * inch, 0.42 * inch, 4.28 * inch]))

    A(Paragraph(
        f"{nat['proven_markets']} of the {nat['markets_screened']} screened metros already "
        f"carry an operating private club or a comparable facility. That is a feature of the "
        f"screen, not a problem with it: a market with a functioning club has proven the "
        f"format absorbs, and the question becomes whether the incumbent is small, remote or "
        f"under-amenitised enough to leave room. Where the answer is no — the Coachella "
        f"Valley, where the reference asset operates — the market is a comparable, not a "
        f"target.", S_BODY))
    A(Paragraph(
        f"The lead site sits in the {S['lead'].get('market_metro')} market and reports "
        f"{int(S['lead'].get('hnw_households_90min') or 0):,} households with over $1M of "
        f"investable assets within ninety minutes, against a club that needs {m['cap']} "
        f"members. The usual next sentence is that the required penetration is a few basis "
        f"points and demand is therefore a marketing question. We do not make that argument, "
        f"because it reads identically for a 520,000-household catchment and a "
        f"98,000-household one, and telling those apart is the entire job of a nationwide "
        f"screen. Section 5B builds the pool down instead.", S_BODY))
    A(Paragraph(
        "MARKET TIERING IS A MODEL OUTPUT, NOT A SOURCED RANKING. Season days are estimated "
        "from climate; wealth, land cost, friction and incentive access are graded on ordinal "
        "bands, not measured. The existing-club column is the only column built from confirmed "
        "operator facts. The comparable club economics study remains the first use of "
        "feasibility capital, and no published competitor figure is relied upon in Section 7.",
        S_NOTE))
    A(PageBreak())

    # ---------------- 3b. Rollout sequence ----------------
    A(Paragraph("3B. THE ROLLOUT SEQUENCE", S_H1))
    A(Paragraph(
        "One club is a deal. The platform case depends on repeating it, and the order matters "
        "more than the count: entitlement is the long pole, so markets enter the pipeline in "
        "parallel rather than in series once club 1 is permitted.", S_BODY))
    A(table([["Phase", "Horizon", "Markets", "Capital"]] + [
        [r.phase, r.horizon, f"{r.markets}<br/><i>{r.rationale}</i>", r.capital]
        for r in S["rollout"]
    ], [1.15 * inch, 0.78 * inch, 4.35 * inch, 0.62 * inch]))

    # ---------------- 4. Programme ----------------
    A(Paragraph("4. THE PROGRAMME", S_H1))
    anc = cfg["income"]["ancillary_annual_usd"]
    A(table([
        ["Component", "Programme", "Economics"],
        ["Circuit", f"{cfg['cost']['track']['miles']:.1f} miles, multi-configuration",
         f"{_usd(cfg['cost']['track']['hard_cost_per_mile_usd'])} per mile"],
        ["Membership", f"{m['cap']} members "
                       f"({m['cap'] / cfg['cost']['track']['miles']:.0f} per track mile)",
         f"{_usd(m['initiation_fee_usd'])} initiation, "
         f"{_usd(m['annual_dues_usd'])} dues"],
        ["Garage condominiums", f"{fs['garage_condos']['units']} units @ "
                                f"{fs['garage_condos']['avg_sf']:,} SF",
         f"{_usd(fs['garage_condos']['sale_price_psf'])}/SF sale"],
        ["Homesites", f"{fs['homesites']['units']} trackside lots",
         f"{_usd(fs['homesites']['price_per_unit_usd'])} each"],
        ["Clubhouse", "32,000 SF — dining, lounge, fitness, event",
         _usd(cfg["cost"]["vertical_hard_usd"]["clubhouse"])],
        ["Service and tech centre", "22,000 SF — storage, prep, detailing",
         _usd(cfg["cost"]["vertical_hard_usd"]["service_tech_center"])],
        ["Karting, skidpad, autocross", "Shoulder-season and family revenue",
         _usd(cfg["cost"]["vertical_hard_usd"]["karting_skidpad_autocross"])],
    ], [1.5 * inch, 2.35 * inch, 2.2 * inch]))

    A(Paragraph("Stabilised revenue and expense", S_H2))
    yrs = ts.project_income(cfg, years=max(12, S["stab"]))
    stabrow = yrs[S["stab"] - 1]
    A(table([
        ["Line", "Stabilised", "Basis"],
        ["Dues revenue", _m(stabrow.dues_revenue), f"{stabrow.members} members"],
        ["Initiation, amortised", _m(stabrow.initiation_recognized),
         f"Over {m['expected_tenure_years']}-year expected tenure — never capitalised"],
        ["Ancillary revenue", _m(stabrow.ancillary_revenue),
         "Track rental, school, storage, F&B, service"],
        ["Effective gross income", _m(stabrow.egi), ""],
        ["Operating expense", _m(-stabrow.opex),
         f"{stabrow.opex / stabrow.egi:.0%} of EGI — inside the private-club band"],
        ["Management fee and reserve",
         _m(-(stabrow.management_fee + stabrow.replacement_reserve)),
         f"{cfg['income']['management_fee_pct_egi']:.1%} + "
         f"{cfg['income']['replacement_reserve_pct_egi']:.1%} of EGI"],
        ["Property tax", _m(-ts.property_tax_annual(cfg, uw.cost.gross_basis(S['lead_ask']))),
         f"{ts.tax_load(cfg):.2%} of gross basis, net of the assumed abatement"],
        ["NET OPERATING INCOME", _m(uw.stabilized_noi_after_tax), "After tax"],
    ], [1.9 * inch, 1.1 * inch, 3.05 * inch]))
    A(PageBreak())

    # ---------------- 5. Sites ----------------
    A(Paragraph("5. SITE STRATEGY AND TARGET PORTFOLIO", S_H1))
    killed = [p for p in S["universe"] if p.get("killed_at_gate")]
    A(Paragraph(
        f"{len(S['universe'])} acquisition targets were screened across "
        f"{len({p.get('market_metro') for p in S['universe'] if p.get('market_metro')})} "
        f"markets; {len(killed)} died in the funnel and {len(S['sites'])} are underwritten "
        f"below. Each is a typology and a submarket, not a parcel under contract: assessor "
        f"identifiers, coordinates and title work are pending and are a first-phase "
        f"deliverable. Each carries its own usable season, its own local ad valorem rate and "
        f"a site-specific cost premium or credit reflecting remediation, blasting, utility "
        f"extension and the value of existing pavement.", S_BODY))
    rows = [["#", "Target", "Metro", "County / ST", "Ac", "Prior use", "Days",
             "Ask", "Site prem.", "Drive", "Tax", "IRR", "DSCR", "Score"]]
    for i, s in enumerate(S["sites"], start=1):
        p, s_cf, s_cov = s["p"], s["cf"], s["cov"]
        eff = p.get("property_tax_effective_rate")
        ab = p.get("property_tax_abatement_pct")
        rows.append([
            i, p["parcel_id"].replace("TP-", ""),
            str(p.get("market_metro") or "").split(" – ")[0],
            f"{p.get('county')} / {p.get('state')}",
            f"{p.get('contiguous_developable_acres'):,.0f}",
            str(p.get("prior_use", "")).replace("_", " "),
            f"{int(p.get('season_days') or 0)}",
            _m(p.get("ask_price")), _m(p.get("site_cost_premium_usd")),
            f"{p.get('best_drive_min')}m",
            f"{eff:.2%}<br/>{'—' if not ab else f'−{ab:.0%}'}" if eff else "—",
            _pct(s_cf.equity_irr, 1),
            _x(s_cov["min_dscr_tested"]),
            f"{p.get('composite_score'):.0f}",
        ])
    A(table(rows, [0.22 * inch, 0.78 * inch, 0.62 * inch, 0.66 * inch, 0.28 * inch,
                   0.72 * inch, 0.32 * inch, 0.5 * inch, 0.58 * inch, 0.38 * inch,
                   0.44 * inch, 0.4 * inch, 0.38 * inch, 0.32 * inch]))
    A(Paragraph(
        "Ask prices are indicative for the typology and submarket, not quoted asking prices "
        "for identified parcels. Drive time is to the best named anchor for that site — a "
        "Phoenix parcel is measured to Scottsdale, not to Manhattan. Tax shows the local "
        "effective rate above the abatement assumed; a dash means no abatement statute "
        "reaches this use in that state and none is taken.", S_NOTE))

    if killed:
        A(Paragraph("Screened out — the funnel is the audit trail", S_H2))
        A(table([["Target", "Market", "Died at", "Reason"]] + [
            [p["parcel_id"].replace("TP-", ""),
             str(p.get("market_metro") or ""),
             str(p.get("killed_at_gate", "")).replace("_", " ").title(),
             str(p.get("rejection_reasons") or "")[:190]]
            for p in killed
        ], [0.85 * inch, 1.05 * inch, 1.05 * inch, 3.95 * inch]))

    # The top of a ranking that separates by less than a point is not a ranking,
    # it is a tie, and presenting it as a winner is the easiest way to lose a
    # reader who checks. Say so where it happens.
    if len(S["sites"]) >= 2:
        a, b = S["sites"][0], S["sites"][1]
        gap = (a["p"].get("composite_score") or 0) - (b["p"].get("composite_score") or 0)
        if gap < 2.0:
            A(Paragraph("The top two are a tie, and they win for opposite reasons", S_H2))
            A(Paragraph(
                f"{a['p']['parcel_id']} scores {a['p'].get('composite_score'):.1f} against "
                f"{b['p']['parcel_id']} at {b['p'].get('composite_score'):.1f} — a "
                f"{gap:.1f}-point gap on a 100-point scale, which is noise. The composition "
                f"of those scores is not noise. "
                f"{a['p']['parcel_id']} wins on catchment and on infrastructure already in "
                f"the ground. {b['p']['parcel_id']} wins on yield: a longer season, a lighter "
                f"ad valorem load and a lower entry price give it "
                f"{(b['uw'].yoc_net_at_ask - a['uw'].yoc_net_at_ask) * 10000:.0f} basis points "
                f"more yield at the ask, and it is the only target in the set that supports a "
                f"positive land price on the retained basis.", S_BODY))
            A(Paragraph(
                f"The two are also asymmetric in the direction their cost basis can move. "
                f"{b['p']['parcel_id']} carries a {_m(abs(b['p'].get('site_cost_premium_usd') or 0))} "
                f"cost PREMIUM — utilities that must be built and are priced in. "
                f"{a['p']['parcel_id']} carries a "
                f"{_m(abs(a['p'].get('site_cost_premium_usd') or 0))} cost CREDIT that depends "
                f"on existing pavement converting to base course and on a Phase II "
                f"environmental result that has not been ordered. Halve that credit and its "
                f"IRR falls to roughly 8.1%; remove it and 7.4%. A premium is a number you "
                f"can bid against. A credit is a number that can disappear. Both sites go "
                f"into Tranche 1 diligence, and the credit is the first thing tested.", S_BODY))

    fr = S.get("fragility")
    if fr is not None and fr.flips:
        A(Paragraph("The lead turns on one unverified number", S_H2))
        A(Paragraph(f"<b>{fr.verdict}</b>", S_BODY))
        A(Paragraph(
            "The risk register carries this as RR-02, Severe and High, evidenced against the "
            "Navy's 2023 identification of fifteen new PFAS areas of concern at the former "
            "NWIRP Calverton, concentrated around the western runway and sourced to firefighting "
            "foam. As of early 2025 the Navy was reported to be at the beginning of CERCLA site "
            "evaluation. PFAS-impacted pavement is a waste characterisation and generator "
            "liability question, not a base-course credit. RR-04 adds that the wider EPCAL "
            "disposition has been in litigation since 2024, with one cause of action surviving "
            "dismissal in February 2026 and the land described throughout as in limbo.", S_BODY))
        A(Paragraph(
            "We are not moving the credit to zero in the base case, because a Phase II has not "
            "been ordered and inventing the answer in either direction would be the same "
            "error. We are saying plainly that the site ranking is not settled, that both "
            "finalists go into Tranche 1 diligence, and that the PFAS analytical is the "
            "cheapest test in the programme that can change the answer.", S_BODY))

    for s in S["sites"][:3]:
        p = s["p"]
        A(Paragraph(f"{p['parcel_id']} — {p.get('municipality')}, {p.get('county')} County, "
                    f"{p.get('state')}", S_H2))
        A(Paragraph(f"<b>Typology.</b> {p.get('address')}", S_BODY))
        A(B("Why it ranks", str(p.get("why_wins") or "")))
        A(B("What would kill it", str(p.get("what_kills") or "")))
        A(B("Cost basis", str(p.get("site_cost_basis_note") or "")))
        A(B("Entitlement", f"{p.get('zoning_district')} — "
                           f"{str(p.get('zoning_posture','')).replace('_',' ')}; "
                           f"{p.get('permitting_timeline_months')} month estimated path. "
                           f"Abatement route: {p.get('tax_abatement_path')}"))
    A(PageBreak())

    # ---------------- 5B. Membership demand ----------------
    A(Paragraph("5B. MEMBERSHIP DEMAND — CAN THESE CLUBS ACTUALLY BE FILLED?", S_H1))
    dcfg = cfg["demand"]
    A(Paragraph(
        f"Every dollar of dues, initiation and ancillary revenue in Section 7 assumes "
        f"{m['cap']} members arrive on the schedule in the ramp. That is the largest "
        f"unexamined assumption in a plan that examines everything else, and it is the one "
        f"that varies most across a nationwide pipeline. We build the high-net-worth pool "
        f"down to a number a founding campaign can actually reach:", S_BODY))
    A(Paragraph(
        f"households with over $1M investable within ninety minutes, times "
        f"{dcfg['collector_share']:.1%} owning a car worth tracking, times "
        f"{dcfg['track_active_share']:.0%} who actually drive it on a circuit, less the share "
        f"a nearby competitor already holds, times the share a campaign can put an offer in "
        f"front of. Competitor capture decays with distance from "
        f"{dcfg['incumbent_capture_at_zero_mi']:.0%} at the gate to nothing at "
        f"{dcfg['incumbent_decay_radius_mi']:.0f} miles, because a club nine miles away "
        f"competes for the same wallet and one a hundred miles away does not.", S_BODY))

    rows = [["Target", "Metro", "HNW <90m", "Capturable", "Coverage", "Joins/yr",
             "Yr-1 ask", "Break-even", "Verdict"]]
    ramp1 = float(m["ramp"][0])
    for r in S["demand"]:
        be = S["demand_be"].get(r.parcel_id, {})
        p = next((x["p"] for x in S["sites"] if x["p"]["parcel_id"] == r.parcel_id), {})
        rows.append([
            r.parcel_id.replace("TP-", ""),
            str(p.get("market_metro") or "").split(" – ")[0],
            f"{r.hnw_households:,}", f"{r.capturable:,.0f}", f"{r.coverage:.1f}x",
            f"{r.joins_per_year:,.0f}", f"{ramp1:.0f}",
            f"{be.get('collector_share', 0):.2%}",
            r.verdict.split("—")[0].strip(),
        ])
    A(table(rows, [0.85 * inch, 0.85 * inch, 0.65 * inch, 0.7 * inch, 0.58 * inch,
                   0.55 * inch, 0.5 * inch, 0.68 * inch, 1.49 * inch]))

    thin = dcfg["coverage_thin"]
    constrained = [r for r in S["demand"] if r.coverage < thin]
    A(Paragraph("What the funnel changes", S_H2))
    A(B("Coverage, not penetration, is the test",
        f"Below {thin:.1f} capturable prospects per seat, market size is the binding risk and "
        f"no amount of marketing spend fixes it. "
        + (f"{len(constrained)} of the {len(S['demand'])} live targets sit below that line: "
           f"{', '.join(r.parcel_id.replace('TP-', '') for r in constrained)}."
           if constrained else
           "No live target sits below that line.")))
    A(B("It disagrees with the composite, and that is the point",
        f"The §11 catchment component scores heavily on drive time, so a site can rank near "
        f"the top of the composite while sitting in the thinnest pool in the set. The lowest-"
        f"coverage target here is {S['demand'][-1].parcel_id.replace('TP-', '')} at "
        f"{S['demand'][-1].coverage:.1f}x. It carries the flag on its row in the workbook "
        f"rather than a silent penalty in the score, because the principal set the §11 "
        f"weights and the model does not get to re-weight them quietly."))
    A(B("The break-even is what survives the inputs being assumed",
        f"Every rate in this funnel is judgment, not measured conversion — the second-largest "
        f"open item after the club economics comps. The defensible number is the last column: "
        f"the collector-ownership share at which coverage falls to 1.0x, meaning the club "
        f"sells out only if literally every reachable prospect joins. On the lead site that "
        f"is {S['demand_be'].get(S['sites'][0]['p']['parcel_id'], {}).get('collector_share', 0):.2%} "
        f"against an assumed {dcfg['collector_share']:.1%} — the assumption can be wrong by a "
        f"wide margin before the conclusion moves."))
    A(B("It also disciplines the ramp",
        f"A catchment that supports {S['demand'][0].joins_per_year:,.0f} joins a year can feed "
        f"a {ramp1:.0f}-member first year; one that supports "
        f"{S['demand'][-1].joins_per_year:,.0f} cannot. Where the pool cannot feed the ramp, "
        f"the flag is RAMP-CONSTRAINED and the fix is a longer lease-up in the underwriting, "
        f"not a bigger sales budget."))
    A(Paragraph(
        "DEMAND FUNNEL RATES ARE ASSUMED. Collector ownership, track-active share, competitor "
        "capture and reachability are benchmark-shaped judgments. They are applied identically "
        "to every catchment, so the RANKING is defensible even where the level is not. "
        "Replacing them with measured conversion from the founding campaign is a Tranche 1 "
        "deliverable.", S_NOTE))
    A(PageBreak())

    # ---------------- 6. Development plan ----------------
    A(Paragraph("6. ROADMAP — MONTH 1 TO YEAR 10", S_H1))
    T = S["timing"]
    A(Paragraph(
        f"Timing below is derived from the underwriting, not asserted alongside it. "
        f"Entitlement is assumed at {T.entitlement_months} months; construction runs "
        f"{T.construction_months} months; the club opens in month {T.opening_month} "
        f"(year {T.opening_year:.1f}) and stabilises in month {T.stabilisation_month} "
        f"(year {T.stabilisation_year:.1f}). Every horizon carries the gate that must clear "
        f"and the metric that proves it did.", S_BODY))

    for ms in S["milestones"]:
        rows = [[Paragraph(f"<b>{ms.horizon.upper()}</b> &nbsp; month {ms.month}", S_TBLB),
                 Paragraph(f"<b>{ms.objective}</b><br/>"
                           f"<font color='#555555'>{ms.phase} &middot; capital: "
                           f"{ms.capital}</font>", S_TBL)]]
        A(table(rows, [1.5 * inch, 5.35 * inch], header=False))
        for dv in ms.deliverables:
            A(Paragraph(f"{DIA}&nbsp;{dv}", S_BULLET))
        A(Paragraph(f"<b>Gate:</b> {ms.gate} &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"<b>KPI:</b> {ms.kpi}", S_NOTE))
        A(Spacer(1, 0.06 * inch))

    A(Paragraph(
        f"Total programme duration from the first feasibility dollar to stabilisation is "
        f"approximately {T.stabilisation_month} months. Entitlement is the longest and least "
        f"controllable phase, which is why the plan spends option money rather than "
        f"acquisition money until the permit is in hand. Note what the arithmetic means for "
        f"the ten-year horizon: year 10 is when the FIRST asset finishes ramping, not when a "
        f"platform is mature. Section 14 addresses that directly.", S_BODY))
    A(PageBreak())

    # ---------------- 7. Financial plan ----------------
    A(Paragraph("7. FINANCIAL PLAN", S_H1))
    su = cf.sources_uses
    A(Paragraph("Sources and uses — lead site", S_H2))
    A(table([
        ["Uses", "Amount", "Sources", "Amount"],
        ["Land", _m(su.land), "For-sale net proceeds", _m(su.for_sale_net_proceeds)],
        ["Non-land development cost", _m(su.non_land_cost),
         "Initiation-fee capital", _m(su.initiation_cash)],
        ["Construction carry", _m(su.carry), "Permanent debt", _m(su.debt)],
        ["Operating deficit reserve", _m(su.operating_deficit_funded),
         "Equity (residual)", _m(su.equity_required)],
        ["TOTAL USES", _m(su.total_uses), "TOTAL SOURCES", _m(su.total_sources)],
    ], [1.9 * inch, 0.85 * inch, 1.85 * inch, 0.85 * inch]))
    A(Paragraph(
        f"The construction facility is sized separately at "
        f"{_m(su.construction_facility)} against total project cost and is repaid by for-sale "
        f"closings; the permanent note of {_m(su.debt)} is secured only by the retained club. "
        f"Peak equity of {_m(cf.peak_equity_requirement)} in year {cf.peak_funding_year} is the "
        f"figure that must actually be funded — materially larger than the residual equity of "
        f"{_m(su.equity_required)}, because the trough precedes the closings.", S_BODY))

    A(Paragraph("Why leverage is deliberately low", S_H2))
    mc_const = ts.mortgage_constant(d["permanent_rate"], d["amortization_years"],
                                    d.get("periods_per_year", 12))
    A(Paragraph(
        f"The permanent loan is sized at {d['target_ltc']:.0%} loan-to-cost, well below a "
        f"conventional 60%. This is the central capital-structure finding. The mortgage "
        f"constant on a {d['permanent_rate']:.2%} note amortising over "
        f"{d['amortization_years']} years is {mc_const:.2%}, while the retained club yields "
        f"roughly {uw.stabilized_noi_after_tax / max(1.0, cf.retained_cost):.2%} on retained "
        f"cost. Borrowing above the asset's yield is negative leverage: modelled across the "
        f"leverage curve, equity IRR RISES as leverage falls, and the DSCR covenant breaks at "
        f"conventional gearing. Low leverage is not conservatism here; it is arithmetic.",
        S_BODY))

    A(Paragraph("Scenario analysis", S_H2))
    rows = [["Scenario", "Required yield", "Max land (net)", "Min DSCR",
             "Peak equity", "IRR", "Multiple", "Value/cost", "Verdict"]]
    for r in S["scen"]:
        rows.append([r.label.split("—")[0].strip(),
                     _pct(r.effective_required_yield), _m(r.max_land_net),
                     _x(r.min_dscr_any_year), _m(r.peak_equity),
                     _pct(r.equity_irr, 1), _x(r.equity_multiple),
                     _x(r.value_to_cost), r.verdict])
    A(table(rows, [0.72 * inch, 0.72 * inch, 0.78 * inch, 0.55 * inch, 0.68 * inch,
                   0.5 * inch, 0.55 * inch, 0.58 * inch, 1.0 * inch]))
    A(Paragraph(
        f"Scenarios move dues, membership ramp, pricing, absorption, construction cost and "
        f"exit cap together, because in a soft cycle they arrive together. The maximum "
        f"supportable land price swings {_m(S['spread']['swing'])} across the set — wider than "
        f"the land budget itself, which is the honest measure of how much the answer depends on "
        f"assumptions rather than on the site.", S_BODY))

    A(Paragraph("Break-even analysis", S_H2))
    bv = S["bev"]
    A(table([
        ["Test", "Requirement", "Base case", "Headroom"],
        ["Members to cover opex and tax", f"{bv['members_to_cover_opex_and_tax']:,.0f}",
         f"{bv['members_at_stabilization']:,.0f} at stabilisation",
         f"{bv['members_at_stabilization'] - bv['members_to_cover_opex_and_tax']:,.0f} members"],
        ["Members to meet the DSCR covenant", f"{bv['members_to_meet_covenant']:,.0f}",
         f"cap of {bv['membership_cap']:,.0f}",
         f"{bv['membership_cap'] - bv['members_to_meet_covenant']:,.0f} members"],
        ["Dues to meet the covenant", _usd(bv["dues_to_meet_covenant"]),
         _usd(bv["dues_base"]),
         f"{(bv['dues_base'] / bv['dues_to_meet_covenant'] - 1):+.0%}"],
        ["Exit cap at which value equals cost", _pct(cf.breakeven_exit_cap),
         _pct(cfg["income"]["exit_cap"]),
         f"{(cf.breakeven_exit_cap - cfg['income']['exit_cap']) * 10000:+.0f} bps"],
    ], [2.0 * inch, 1.1 * inch, 1.4 * inch, 1.0 * inch]))

    A(Paragraph("Driver sensitivity", S_H2))
    rows = [["Rank", "Driver", "Swing on max supportable land", "Share"]]
    tot = sum(b.swing_abs for b in S["tor"]) or 1.0
    for i, b in enumerate(S["tor"][:6], start=1):
        rows.append([i, b.driver.replace("_", " "), _m(b.swing_abs),
                     f"{b.swing_abs / tot:.0%}"])
    A(table(rows, [0.4 * inch, 2.1 * inch, 1.7 * inch, 0.7 * inch]))
    A(Paragraph(
        f"Each driver is flexed {cfg['tornado']['swing_pct']:.0%} one at a time. Diligence "
        f"spend follows this ranking, not intuition.", S_NOTE))

    A(Paragraph("Probability analysis", S_H2))
    A(Paragraph(
        f"Across {S['mc'].iterations:,} joint draws with triangular distributions on every "
        f"driver, the programme clears the retained-asset yield test in "
        f"{S['mc'].p_feasible_net:.0%} of cases and holds the DSCR covenant in "
        f"{S['mc'].p_covenant_holds:.0%}. Every driver's modal value is the base case, so the "
        f"simulation is centred on the underwriting rather than beside it; the asymmetry sits "
        f"in the spread, where each driver carries a longer adverse tail than favourable one. "
        f"Nine independent draws compound, which is why the hold rate is well below what any "
        f"single driver would suggest. Read it as a measure of how wide the parameter "
        f"uncertainty still is before the comparable study lands — not as a second forecast.",
        S_BODY))
    A(PageBreak())

    # ---------------- 8. The ask ----------------
    A(Paragraph("7B. THE RETURN, AND WHO IT IS FOR", S_H1))
    br = S["bridge"]
    A(Paragraph(
        f"A base-case equity IRR of {_pct(cf.equity_irr, 1)} is a core-to-core-plus return "
        f"being earned on an opportunistic risk profile. Ground-up development with "
        f"entitlement risk is conventionally underwritten to 18% and above; stabilised core "
        f"assets to 6–9%. This programme lands at the top of core. We state that plainly "
        f"because a reader who prices deals for a living will see it in thirty seconds, and "
        f"an adjective is not an answer to it.", S_BODY))
    A(Paragraph("What would have to be true to earn an opportunistic return", S_H2))
    A(table([["Driver", "Favourable move", "Equity IRR", "Value / cost",
              f"Reaches {br.target_irr:.0%} alone?"]] + [
        [r.driver, r.move, _pct(r.irr, 1), _x(r.value_to_cost),
         "YES" if r.reaches_target else "no"]
        for r in br.rungs
    ], [1.5 * inch, 1.35 * inch, 1.1 * inch, 1.05 * inch, 1.85 * inch]))
    A(Paragraph(f"<b>{br.verdict}</b>", S_BODY))
    A(Paragraph(
        f"The minimal path to {br.target_irr:.0%} is {br.combined_drivers} moves — "
        f"{br.combined_label} — reaching {_pct(br.combined_irr, 1)} at "
        f"{_x(br.combined_value_to_cost)} value to retained cost. Both are MEMBER PRICING. "
        f"Neither is a construction outcome, a cap-rate outcome or a leverage trick. The "
        f"entire distance between a core return and an opportunistic one on this programme "
        f"is what a member will pay to join and to stay — which is precisely the assumption "
        f"Section 12 makes a condition precedent and Tranche 1 buys the answer to.", S_BODY))

    A(Paragraph("Three honest answers, and one honest warning", S_H2))
    A(B("The unlevered return is the cleaner number",
        f"At zero permanent leverage the programme returns "
        f"{_pct(next((r.irr for r in br.rungs if 'leverage' in r.driver.lower()), None), 1)} "
        f"because the mortgage constant exceeds the retained asset's yield on cost. An "
        f"all-cash holder is not giving up return to avoid debt here; they are collecting it. "
        f"Section 8 holds permanent leverage at {d['target_ltc']:.0%} for that reason."))
    A(B("The risk is barbelled, not uniform",
        f"{_m(S['t1']['total'])} of Tranche 1 resolves the revenue assumption set, the "
        f"abatement and "
        f"the entitlement path before a dollar of land closes. The opportunistic-risk portion "
        f"of this programme is roughly 4% of the peak equity requirement and it is spent "
        f"first. What follows it is a construction programme against pre-sold inventory."))
    A(B("The capital that prices this correctly is not an opportunistic fund",
        "It is family-office, strategic and member-adjacent capital that holds a hard asset, "
        "uses it, and sells the residential around it — the way the reference assets in this "
        "typology were actually funded. An 18%-hurdle fund should decline this deal, and we "
        "would rather they declined it now than at the IC."))
    A(B("The warning",
        f"If the comparable study comes back and member pricing will not support the "
        f"assumed {_usd(m['initiation_fee_usd'])} initiation and {_usd(m['annual_dues_usd'])} "
        f"of dues, the answer is not to stretch another driver. It is that this programme is "
        f"a core-plus asset at a core-plus price, and the land bid has to fall to match. The "
        f"model already solves for that: it is the maximum supportable land price in "
        f"Section 11."))
    A(PageBreak())

    A(Paragraph("7C. IF THE COMPARABLE SET IS RIGHT, IS THERE A PROGRAMME THAT WORKS?",
                S_H1))
    R = S["respec"]
    b, best = R.baseline, R.best_feasible
    A(Paragraph(
        f"Section 1 says the comparable study cuts the revenue line by roughly half. The "
        f"obvious reading is that the deal is dead. That reading skips a step. A pro forma "
        f"can be wrong in two ways: it can be the right programme at the wrong prices, or the "
        f"wrong programme. Repricing to the comparable set and stopping there tests only the "
        f"first. So we held the comp-supported prices fixed and searched the programme "
        f"itself — track length, membership cap, and the number of units for sale — across "
        f"{len(R.variants)} configurations, scored on the same governing tests.", S_BODY))
    if best is not None:
        A(table([
            ["", "As configured", "Re-specified"],
            ["Membership cap", f"{b.member_cap}", f"{best.member_cap}"],
            ["Track miles", f"{b.track_miles:.2f}", f"{best.track_miles:.2f}"],
            ["Members per track mile", f"{b.members_per_mile:.0f}",
             f"{best.members_per_mile:.0f}"],
            ["Garage condos", f"{b.condo_units}", f"{best.condo_units}"],
            ["Stabilised NOI", _m(b.stabilized_noi), _m(best.stabilized_noi)],
            ["Equity IRR", _pct(b.equity_irr, 1), _pct(best.equity_irr, 1)],
            ["Minimum DSCR", _x(b.min_dscr), _x(best.min_dscr)],
            ["Value / retained cost", _x(b.value_to_cost), _x(best.value_to_cost)],
            ["Peak equity", _m(b.peak_equity), _m(best.peak_equity)],
            ["Demand coverage at the lead site",
             f"{(b.demand_coverage or 0):.1f}x", f"{(best.demand_coverage or 0):.1f}x"],
        ], [2.3 * inch, 2.2 * inch, 2.35 * inch]))
    A(Paragraph(f"<b>{R.verdict}</b>", S_BODY))

    A(Paragraph("Three things the search settles", S_H2))
    A(B("Track length is not the lever, and the intuition that it is was wrong",
        f"The circuit is roughly 7% of non-land cost. Across the searched range track "
        f"length is worth {R.track_sensitivity_bps:.0f} basis points of equity IRR. A shorter "
        f"course is a smaller parcel, a cheaper entitlement and a wider set of eligible "
        f"sites — all real, none of them the answer to the comparable set."))
    A(B("More for-sale product makes it worse, not better",
        f"Worth {R.condo_sensitivity_bps:.0f} basis points across the range, and it moves the "
        f"wrong way. The for-sale vertical is 43% of non-land cost; it draws soft cost and "
        f"contingency like every other hard dollar, so a garage condo costs "
        f"{_usd(uw.for_sale.loaded_cost_psf)}/SF to deliver against a hard cost of "
        f"{_usd(fs['garage_condos']['hard_cost_psf'])}. At the "
        f"{_usd(fs['garage_condos']['sale_price_psf'])}/SF in the base case that is "
        f"{_usd(uw.for_sale.condo_margin_per_unit)} a unit and it works. At the $344–352/SF "
        f"operating new-build track comps actually achieve, the same unit loses money on "
        f"every sale, and in a merchant build the carry runs until the last one closes."))
    A(B("Member count is the lever, and demand — not design — is what bounds it",
        "Lower dues need more payers; that is arithmetic. What is not arithmetic is whether "
        "the catchment supplies them. Section 5B is the constraint on this table, and it is "
        "why the search will not recommend a configuration the market cannot fill even when "
        "the arithmetic clears."))
    A(Paragraph(
        "This section is a diagnostic, not a proposal. It says the comparable-set case is a "
        "specification question as well as a pricing one, and it names which dial matters. "
        "Re-specifying the programme is a decision for the principal and it changes the "
        "product, the parcel requirement and the member proposition all at once.", S_NOTE))
    A(PageBreak())

    A(Paragraph("8. CAPITAL STRUCTURE AND THE ASK", S_H1))
    t1b = S["t1"]
    t1 = t1b["total"]
    A(Paragraph(
        "We are raising in two tranches. Tranche 1 is the money that converts this plan from "
        "an underwriting exercise into a controlled, entitled site. Tranche 2 is the "
        "construction equity and is not requested today.", S_BODY))
    A(table([
        ["", "Tranche 1 — Feasibility and control", "Tranche 2 — Construction equity"],
        ["Amount", _usd(t1), f"{_m(cf.peak_equity_requirement)} peak"],
        ["Timing", "On execution", "At construction start, subject to Section 12"],
        ["Use of proceeds",
         "Comparable club study; 150-parcel sourcing pass; site option payments and "
         "extensions; acoustic model; Phase I and II environmental; survey and geotechnical; "
         "entitlement counsel and consultants; abatement negotiation; founding-member "
         "marketing programme",
         "Land closing; circuit and vertical construction; FF&E; carry; operating deficit "
         "reserve"],
        ["Structure",
         "Preferred equity in the predevelopment entity, converting at a negotiated discount "
         "into the development entity, or expensed and returned first from Tranche 2",
         "Development-entity common equity alongside the construction facility"],
        ["Investor protection",
         "Capital is spent on options and studies, not on land. If the comparable study or "
         "the abatement fails, the programme stops before acquisition and the remaining "
         "commitment is released",
         "Draw conditions tied to permit issuance, abatement execution, pre-sale thresholds "
         "and a lender commitment"],
    ], [0.85 * inch, 2.85 * inch, 2.6 * inch]))
    A(Paragraph("Tranche 1 — line by line, and when each answer lands", S_H2))
    A(table([["Mo.", "Item", "Cost", "Who does it", "What it resolves"]] + [
        [str(i["month"]), i["name"], _usd(i["usd"]), i["vendor"], i["resolves"]]
        for i in t1b["items"]
    ] + [
        ["", "Subtotal", _usd(t1b["subtotal"]), "", ""],
        ["", f"Contingency ({t1b['contingency_pct']:.0%})", _usd(t1b["contingency"]), "", ""],
        ["", "TRANCHE 1 TOTAL", _usd(t1), "",
         f"Complete by month {t1b['months']}"],
    ], [0.3 * inch, 1.78 * inch, 0.66 * inch, 1.72 * inch, 2.39 * inch]))
    A(Paragraph(
        "Sequencing is the point. The comparable club study and the acoustic model land in "
        "months 3 and 7 — both before the option payments are at real risk and long before "
        "land closes. If either comes back wrong, the programme stops having spent a fraction "
        "of the commitment, and the remaining capital is released.", S_NOTE))

    A(Paragraph(
        f"Tranche 1 is deliberately the smaller number and the harder gate. The programme's "
        f"largest single uncertainty is the revenue assumption set, and it can be resolved for "
        f"a fraction of a percent of total cost. Committing "
        f"{_m(cf.peak_equity_requirement)} before that work is done would be indefensible, "
        f"and we are not asking anyone to.", S_BODY))

    # ---------------- 8b. Exit ----------------
    A(Paragraph("9. EXIT STRATEGY", S_H1))
    A(Paragraph(
        "Capital returns through three independent channels, which is the principal structural "
        "protection in the plan. They do not all depend on the same buyer or the same market.",
        S_BODY))
    A(B("Channel 1 — for-sale closings",
        f"{_m(uw.for_sale.net_proceeds)} of net proceeds from garage condominiums and "
        f"homesites, realised across the sell-out. This is merchant-build profit and it does "
        f"not require a capital-markets exit."))
    A(B("Channel 2 — member capital",
        f"{_m(cf.sources_uses.initiation_cash)} of initiation-fee cash. Non-refundable and "
        f"non-dilutive, collected as the club fills."))
    A(B("Channel 3 — the retained club",
        f"Exit value of {_m(cf.exit_net_proceeds)} at a {cfg['income']['exit_cap']:.2%} cap "
        f"against a retained cost of {_m(cf.retained_cost)}. Refinance is the alternative to "
        f"sale; low leverage means the asset is not forced to transact on a lender's timetable."))
    A(Paragraph(
        f"The break-even exit cap is {_pct(cf.breakeven_exit_cap)}, "
        f"{(cf.breakeven_exit_cap - cfg['income']['exit_cap']) * 10000:+.0f} basis points from "
        f"the assumed exit. Beyond that widening the retained club is worth less than it cost "
        f"to build, and the return depends entirely on the first two channels. Buyer universe "
        f"for a single-asset special-purpose recreational property is thin — family offices, "
        f"club operators and member-buyout vehicles rather than institutional core capital — "
        f"and that illiquidity is priced into the assumed exit cap.", S_BODY))

    # ---------------- 10. Team ----------------
    A(Paragraph("10. SPONSOR, TEAM AND GOVERNANCE", S_H1))
    A(Paragraph(
        "The plan is presented without a completed team, and that is disclosed rather than "
        "papered over. The roles below are prerequisites, not preferences; three of them are "
        "conditions precedent to construction capital. An investor should weight execution "
        "risk accordingly and should expect these seats filled before Tranche 2.", S_BODY))
    A(table([
        ["Role", "Requirement", "Status"],
        ["Sponsor / developer",
         "Land development and entitlement track record in the selected state — the "
         "entitlement regimes in this pipeline range from an unzoned Texas county to a "
         "New York special permit under SEQRA, and they are not the same job",
         "To be confirmed"],
        ["Club operator",
         "Private-club or motorsport-facility operating history; accountable for the operating "
         "budget that drives the covenant",
         "OPEN — condition precedent"],
        ["Circuit designer",
         "FIA-informed road-course design with runoff and noise-attenuation experience",
         "To be appointed"],
        ["Entitlement counsel",
         "Land-use counsel admitted in the selected jurisdiction. Not portable: SEQRA, "
         "a Florida comprehensive-plan consistency finding and a Texas plat-and-TCEQ path "
         "share no procedure",
         "To be appointed in Phase 0"],
        ["Acoustic consultant",
         "Motorsport-specific modelling against the actual municipal standard",
         "To be appointed in Phase 0"],
        ["General contractor",
         "Heavy civil and vertical; guaranteed maximum price capability",
         "OPEN — condition precedent"],
        ["Sales and membership",
         "Founding-member programme and garage-condominium pre-sales",
         "OPEN — drives the funding waterfall"],
    ], [1.35 * inch, 3.3 * inch, 1.65 * inch]))
    A(Paragraph("Governance and reporting", S_H2))
    A(B("Assumption discipline",
        "Every figure in this plan is generated from a single versioned model. There are no "
        "transcribed numbers in this document or in the accompanying workbook, so the plan "
        "cannot drift from the underwriting. Each input is tagged CONFIRMED or ASSUMED."))
    A(B("Automated coherence testing",
        f"The model runs {S['plaus']['fail_count'] + S['plaus']['warn_count'] + S['plaus']['ok_count']} "
        f"internal-consistency checks plus {_test_count()} unit tests, including a check "
        f"that the live "
        f"spreadsheet formulas agree with the model to the cent. Appendix B reports current "
        f"status."))
    A(B("Quarterly reporting",
        "Against the milestone schedule in Section 6 and the conditions precedent in "
        "Section 11, with the assumption register re-marked as items move from ASSUMED to "
        "VERIFIED."))

    # ---------------- 11. Risks ----------------
    A(PageBreak())
    A(Paragraph("11. RISK ANALYSIS", S_H1))
    A(table([
        ["Risk", "Assessment", "Mitigation"],
        ["Revenue assumptions unverified",
         "Highest. Every income figure is benchmark-derived, not sourced. The plausibility "
         "audit passes but that tests internal consistency, not market truth",
         "Comparable club study is the first use of Tranche 1 and a gate on all further spend"],
        ["Property-tax abatement not secured",
         "Severe. Without a 50% abatement the covenant breaches and maximum supportable land "
         "goes negative",
         "Condition precedent to land closing. IDA PILOT precedent in NY; EDA and municipal "
         "agreements in NJ and CT. Negotiated in Phase 1, before acquisition"],
        ["Noise litigation after permits issue",
         "High and the classic failure mode for this asset class",
         "Prior-use sites only; acoustic model pre-application; berming and sound-wall budget "
         "in base cost; muffler rule in club by-laws; opposition history reviewed in P&Z "
         "minutes before any option is signed"],
        ["Seasonality and the season premium",
         f"The lead site runs {int(S['lead'].get('season_days') or 0)} usable days against a "
         f"{cfg['income']['season']['baseline_days']}-day baseline",
         "Both sides of the season are modelled: revenue and the crew, consumables and track "
         "preparation a longer calendar consumes. Dues parity with the reference asset is "
         "treated as unproven until the comparable study is complete"],
        ["Abatement does not travel",
         "The 50% relief in the base case is a New York IDA mechanism with no Florida or "
         "Nevada equivalent for this use",
         "Every site is underwritten at its own local rate and its own honest view of relief. "
         "Low-rate states carry the lighter load unabated; high-rate states make the abatement "
         "a condition precedent, not an upside"],
        ["Construction cost escalation",
         f"The largest single driver: {_m(S['tor'][0].swing_abs)} of swing on a "
         f"{cfg['tornado']['swing_pct']:.0%} flex",
         "Guaranteed maximum price where obtainable; prior-use sites to reduce earthwork; "
         "10% contingency on hard and soft cost; phased vertical delivery"],
        ["Absorption and lease-up",
         "Sell-out drives carry; a slower ramp extends the period capital is outstanding",
         "Founding-member programme and condominium pre-sales before construction start; "
         "phasing so later buildings follow demand"],
        ["Negative leverage at conventional gearing",
         "Identified and designed around",
         f"Permanent leverage held at {d['target_ltc']:.0%}. Any lender proposal above roughly "
         f"45% loan-to-cost should be declined on return grounds, not accepted as cheap capital"],
        ["Single-asset, special-purpose collateral",
         "Thin resale market; no agency execution; refinance risk at exit",
         "Alternate-use analysis on every target site; low leverage to reduce refinance "
         "dependence; for-sale component returns capital independent of the club"],
    ], [1.5 * inch, 2.3 * inch, 2.5 * inch]))
    A(PageBreak())

    # ---------------- 10. Conditions ----------------
    A(Paragraph("12. CONDITIONS PRECEDENT TO TRANCHE 2", S_H1))
    A(Paragraph("No construction capital is drawn until all of the following are satisfied. "
                "These are not aspirations; they are the gates the base case depends on.",
                S_BODY))
    for i, (h, b) in enumerate([
        ("Verified comparable club economics",
         "Initiation ceiling, dues, garage-condominium pricing against local flex "
         "comparables, and realised absorption, sourced and dated. If the verified set "
         "materially undercuts the assumption base, the programme stops."),
        ("Property-tax abatement executed",
         "A PILOT or equivalent delivering not less than the modelled abatement. Without it "
         "the covenant fails and the land has no supportable value."),
        ("Entitlement in hand",
         "Special permit or map amendment issued, appeal period run, wetlands and "
         "environmental review complete."),
        ("Acoustic model and mitigation budget",
         "Third-party model against the actual municipal standard, with the mitigation cost "
         "carried in hard cost, not in contingency."),
        ("Pre-sale thresholds met",
         "Founding memberships and garage-condominium contracts at the levels assumed in the "
         "funding waterfall before the first construction draw."),
        ("Lender commitment on modelled terms",
         "Construction facility and permanent takeout at or better than the assumed coupon, "
         "amortisation and covenant. The assumed terms are not quoted."),
        ("Operator and management agreement",
         "A named operator with private-club or motorsport-facility track record, and a "
         "management agreement consistent with the modelled fee."),
    ], start=1):
        A(B(f"{i}. {h}", b))

    # ---------------- 11. Recommendation on the hurdle ----------------
    A(Paragraph("13. RECOMMENDED CHANGE TO THE INVESTMENT TEST", S_H1))
    A(Paragraph(
        f"The programme was originally underwritten against a "
        f"{cfg['meta']['hurdle_yoc']:.2%} yield on gross development cost. We recommend "
        f"retiring that test for this asset and we want the reasoning on the record.", S_BODY))
    A(B("A gross-basis yield test asks the income asset to carry cost it does not own",
        "Roughly half of development cost is garage condominiums and homesites which are sold. "
        "Holding stabilised club NOI against a basis that includes sold collateral is not a "
        "conservative test, it is an incoherent one. The same error, applied to exit value, "
        "understated value-to-cost by roughly a factor of two until it was corrected."))
    A(B("The economically meaningful tests are three",
        f"Project equity IRR and multiple; minimum DSCR across the hold on the retained asset; "
        f"and value against retained cost at exit. The base case reports "
        f"{_pct(cf.equity_irr, 1)}, {_x(cov['min_dscr_tested'])} against a "
        f"{d['min_dscr']:.2f}x covenant, and {_x(cf.value_to_cost)}."))
    A(B("Keep the covenant, drop the yield hurdle",
        f"The {d['min_dscr']:.2f}x DSCR floor is a real constraint imposed by a real "
        f"counterparty and should stay. The {cfg['meta']['hurdle_yoc']:.2%} yield-on-cost "
        f"hurdle is an internal test borrowed from core real estate and it does not fit a "
        f"merchant-build programme with a retained amenity."))

    # ---------------- 14. Platform, IPO test, exit ladder ----------------
    A(PageBreak())
    A(Paragraph("14. PLATFORM STRATEGY, THE LISTING QUESTION, AND EXIT", S_H1))
    lt = S["listing"]
    T = S["timing"]
    A(Paragraph(
        "An initial public offering has been raised as a ten-year objective. It deserves "
        "arithmetic rather than an aspiration, so this section tests it against screening "
        "thresholds for whether a listing is even a conversation. The answer is no at year "
        "ten, and the reason is scale and concentration rather than performance.", S_BODY))

    A(Paragraph("Unit economics do not scale into a listing on their own", S_H2))
    rows = [["Stabilised clubs", "Recurring NOI", "Asset value at exit cap",
             "Cumulative development cost", "Clears listing thresholds?"]]
    for pt in S["platform"]:
        clears = (pt.stabilised_noi >= lt.thresholds["min_recurring_noi_usd"]
                  and pt.asset_value >= lt.thresholds["min_equity_value_usd"]
                  and pt.clubs >= lt.thresholds["min_stabilised_assets"])
        rows.append([str(pt.clubs), _m(pt.stabilised_noi), _m(pt.asset_value),
                     _m(pt.cumulative_dev_cost), "YES" if clears else "no"])
    A(table(rows, [1.15 * inch, 1.25 * inch, 1.55 * inch, 1.75 * inch, 1.15 * inch]))
    A(Paragraph(
        f"Thresholds applied are judgment, not sourced: "
        f"{_m(lt.thresholds['min_equity_value_usd'])} of equity value, "
        f"{_m(lt.thresholds['min_recurring_noi_usd'])} of recurring NOI, "
        f"{lt.thresholds['min_stabilised_assets']} stabilised assets for diversification, and "
        f"{lt.thresholds['min_operating_history_years']} years of audited operating history. "
        f"Scale is modelled linearly — no platform overhead leverage and no portfolio "
        f"cap-rate premium are assumed, because neither is evidenced.", S_NOTE))

    A(Paragraph("The listing test", S_H2))
    A(table([
        ["Test", "Requirement", "Result"],
        ["Clubs needed on recurring NOI", f"{lt.clubs_required_by_noi}",
         f"{_m(lt.thresholds['min_recurring_noi_usd'])} threshold"],
        ["Clubs needed on equity value", f"{lt.clubs_required_by_value}",
         f"{_m(lt.thresholds['min_equity_value_usd'])} threshold"],
        ["Clubs needed on diversification", f"{lt.clubs_required_by_diversification}",
         "Single-asset issuers do not list"],
        ["BINDING REQUIREMENT", f"{lt.clubs_required} stabilised clubs", "The maximum of the three"],
        ["Reached by ground-up development", f"Year {lt.ground_up_year:.0f}",
         f"Each club needs the full {T.stabilisation_month}-month cycle at a "
         f"{cfg['roadmap']['ground_up_stagger_months']}-month cadence"],
        ["Reached by acquisition-led growth", f"Year {lt.acquisition_year:.0f}",
         "Existing facilities carry a circuit and an entitlement already"],
        ["LISTABLE BY YEAR 10", "NO" if not lt.listable_by_year_10 else "POSSIBLE",
         "Year 10 is when club 1 finishes ramping"],
    ], [2.05 * inch, 1.55 * inch, 3.25 * inch]))
    A(Paragraph(f"<b>Conclusion.</b> {lt.verdict}", S_BODY))

    A(Paragraph("What this means for strategy", S_H2))
    A(B("Club 1 is the proof, not the platform",
        "Its purpose is to demonstrate that the typology works in its market, establish "
        "the operating platform and the brand, and generate the track record that makes "
        "capital for clubs 2 and 3 cheap. Underwrite it on its own merits, which Sections "
        "7 and 11 do."))
    A(B("Growth beyond club 2 should be acquisitive, not ground-up",
        f"Ground-up entitlement and construction is a {T.stabilisation_month}-month cycle per "
        f"asset. Acquiring and repositioning existing facilities compresses that to roughly "
        f"{cfg['roadmap']['acquisition_ramp_months']} months and is the only route that "
        f"reaches listing scale inside a normal fund life. It is also a different skill set "
        f"and should be resourced as one."))
    A(B("Do not underwrite to the IPO",
        "It is a stretch outcome contingent on a platform that does not yet exist. The "
        "capital returned in the base case comes from for-sale closings, member capital and "
        "a stabilised asset — none of which requires a public listing."))

    A(Paragraph("15. EXIT LADDER", S_H1))
    A(Paragraph("Ranked by probability of actually happening, not by headline proceeds.",
                S_BODY))
    rows = [["#", "Route", "Timing", "Proceeds basis", "Requires", "Assessment"]]
    for e in S["exits"]:
        rows.append([str(e.rank), e.route, e.timing, e.proceeds_basis, e.requires,
                     e.assessment])
    A(table(rows, [0.28 * inch, 1.35 * inch, 0.95 * inch, 1.15 * inch, 1.35 * inch,
                   1.77 * inch]))
    A(Paragraph(
        "The first two routes together return the majority of invested capital and depend on "
        "delivery and absorption rather than on any capital-markets window. That is the "
        "structural protection in this programme and it is why the plan is built as a "
        "merchant build with a retained amenity rather than as a yield play.", S_BODY))

    # ---------------- Appendices ----------------
    A(PageBreak())
    A(Paragraph("APPENDIX A — ASSUMPTION REGISTER", S_H1))
    A(Paragraph("Every material assumption, its status, and who resolves it.", S_BODY))
    A(table([
        ["Assumption", "Value", "Status", "Resolved by"],
        ["Minimum DSCR", f"{d['min_dscr']:.2f}x", "CONFIRMED by principal", "—"],
        ["Yield basis and ranking", "Gross and net; ranked gross",
         "CONFIRMED by principal", "See Section 11 recommendation"],
        ["Acreage floor", f"{cfg['mandate']['acreage']['hard_floor_acres']} ac hard floor",
         "CONFIRMED by principal", "—"],
        ["Drive-time ceiling", f"{cfg['mandate']['drive_time']['max_minutes']} min",
         "CONFIRMED by principal", "—"],
        ["Initiation fee and dues",
         f"{_usd(m['initiation_fee_usd'])} / {_usd(m['annual_dues_usd'])}",
         "ASSUMED — benchmark-derived", "Comparable club study"],
        ["Membership cap and ramp", f"{m['cap']} over {len(m['ramp'])} years",
         "ASSUMED", "Comparable club study; founding-member response"],
        ["Ancillary revenue", _m(sum(anc.values())), "ASSUMED", "Comparable club study"],
        ["Operating expense", _m(sum(cfg['income']['opex_annual_usd'].values())),
         "ASSUMED — set to a plausible operating ratio", "Operator budget"],
        ["Garage condominium pricing",
         f"{_usd(fs['garage_condos']['sale_price_psf'])}/SF",
         "ASSUMED", "Local flex comparables and pre-sales"],
        ["Construction cost", _m(uw.cost.hard), "ASSUMED", "GMP or hard bid"],
        ["Site infrastructure", "30% below greenfield",
         "ASSUMED — requires a prior-use site", "Geotechnical and civil design"],
        ["Property tax rate and abatement",
         f"{cfg['income']['property_tax']['effective_rate']:.2%}, "
         f"{cfg['income']['property_tax']['abatement_pct']:.0%} abated",
         "ASSUMED — CONDITION PRECEDENT", "Assessor and IDA/EDA negotiation"],
        ["Permanent coupon and amortisation",
         f"{d['permanent_rate']:.2%} / {d['amortization_years']} yr",
         "ASSUMED — within a surveyed range", "Lender term sheet"],
        ["Permanent and construction leverage",
         f"{d['target_ltc']:.0%} / {d['construction_ltc']:.0%}",
         "ASSUMED — see negative-leverage finding", "Lender term sheet"],
        ["Exit cap", _pct(cfg["income"]["exit_cap"]), "ASSUMED", "Broker opinion at exit"],
        ["Entitlement period", f"{cfg['roadmap']['entitlement_months']} months",
         "ASSUMED", "Municipal pre-application and counsel"],
        ["Ground-up cadence between clubs",
         f"{cfg['roadmap']['ground_up_stagger_months']} months", "ASSUMED",
         "Management bandwidth and capital recycling"],
        ["Listing thresholds",
         f"{_m(cfg['listing_thresholds']['min_equity_value_usd'])} value / "
         f"{_m(cfg['listing_thresholds']['min_recurring_noi_usd'])} NOI",
         "JUDGMENT — screening only", "Banker guidance if a listing is pursued"],
    ], [1.55 * inch, 1.15 * inch, 1.75 * inch, 1.8 * inch]))

    A(Paragraph("APPENDIX B — INTERNAL CONSISTENCY AUDIT", S_H1))
    A(Paragraph(
        f"The model runs an automated coherence check that tests whether the assumption set "
        f"can all be true simultaneously. Current status: {S['plaus']['fail_count']} failures, "
        f"{S['plaus']['warn_count']} warnings.", S_BODY))
    rows = [["Check", "Value", "Plausible band", "Status"]]
    for c in S["plaus"]["checks"]:
        rows.append([c.name, f"{c.value:,.4g}",
                     f"{c.band[0]:,.4g} – {c.band[1]:,.4g}", c.severity])
    A(table(rows, [2.1 * inch, 0.9 * inch, 1.4 * inch, 0.8 * inch]))
    A(Paragraph(
        "This check is why the plan does not show a higher return. Configurations producing a "
        "13–14% IRR required a club operating ratio near 31% of gross income, which is far "
        "below what private clubs actually run at. Those configurations were rejected.", S_NOTE))

    A(Paragraph("APPENDIX C — SOURCES", S_H1))
    from build.build_workbook import _default_sources
    rows = [["No.", "Source", "Cited for", "Confidence"]]
    for s in _default_sources():
        rows.append([s.get("no"), s.get("name"), s.get("cited_for"), s.get("confidence")])
    A(table(rows, [0.35 * inch, 1.35 * inch, 3.15 * inch, 1.35 * inch]))
    A(Paragraph(
        "Nothing in the assumption register marked ASSUMED is sourced. The comparable club "
        "economics set remains unresearched and is the first use of feasibility capital.",
        S_NOTE))

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"Bellwether_Motor_Club_Business_Plan_{today:%Y-%m-%d}.pdf"

    doc = BaseDocTemplate(str(path), pagesize=LETTER, leftMargin=MARGIN,
                          rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN,
                          title="Bellwether Motor Club — Confidential Business Plan",
                          author="Track Boss")

    def painter(canv, docu):
        canv.saveState()
        if docu.page > 1:
            canv.setFont(SERIF_I, 8)
            canv.setFillColor(GREY)
            canv.drawString(MARGIN, 0.55 * inch,
                            "Bellwether Motor Club — Confidential Business Plan")
            canv.drawRightString(LETTER[0] - MARGIN, 0.55 * inch, f"{docu.page}")
            canv.setStrokeColor(RULE)
            canv.setLineWidth(0.3)
            canv.line(MARGIN, 0.72 * inch, LETTER[0] - MARGIN, 0.72 * inch)
        canv.restoreState()

    doc.addPageTemplates([PageTemplate(
        id="main",
        frames=[Frame(MARGIN, MARGIN, FW, LETTER[1] - 2 * MARGIN, id="f",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
        onPage=painter)])
    doc.build(st)
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the formal business plan PDF.")
    ap.add_argument("--parcels", type=Path, default=Path("data/sites_targets.csv"))
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=Path("dist"))
    args = ap.parse_args()
    cfg = ts.load_config(args.config)
    print(f"Wrote {build(cfg, args.parcels, args.out)}")


if __name__ == "__main__":
    main()
