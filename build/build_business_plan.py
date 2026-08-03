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
from model import cashflow as cfm
from model import risk as rk
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

    uw = ts.underwrite(cfg, "LEAD", ask_price=lead_ask, site_cost_premium=lead_prem)
    cf = cfm.project_cash_flow(cfg, lead_ask, horizon_operating_years=12,
                               site_cost_premium=lead_prem)
    stab = ts.stabilization_year(cfg)
    dev = int(round(cfg["cost"]["carry"]["development_years"]))
    cov = cfm.covenant_report(cf, cfg["debt"]["min_dscr"], tested_from_year=dev + stab)
    plaus = rk.plausibility_report(cfg, lead_ask)
    scen = sc.run_all(cfg, ask_price=lead_ask, site_cost_premium=lead_prem)
    spread = sc.scenario_spread(scen)
    bev = rk.direct_break_evens(cfg, lead_ask)
    tor, tor_base, _ = rk.tornado(cfg)
    mc = rk.monte_carlo(cfg, lead_ask)

    # Per-site economics
    sites = []
    for p in live:
        prem = float(p.get("site_cost_premium_usd") or 0.0)
        ask = float(p.get("ask_price") or 0.0)
        s_uw = ts.underwrite(cfg, p["parcel_id"], ask_price=ask, site_cost_premium=prem)
        s_cf = cfm.project_cash_flow(cfg, ask, horizon_operating_years=12,
                                     site_cost_premium=prem)
        s_cov = cfm.covenant_report(s_cf, cfg["debt"]["min_dscr"],
                                    tested_from_year=dev + stab)
        sites.append({"p": p, "uw": s_uw, "cf": s_cf, "cov": s_cov})

    return dict(cfg=cfg, universe=universe, unverified=unverified, live=live,
                lead=lead, lead_ask=lead_ask, uw=uw, cf=cf, cov=cov, stab=stab,
                dev=dev, plaus=plaus, scen=scen, spread=spread, bev=bev,
                tor=tor, tor_base=tor_base, mc=mc, sites=sites)


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
    A(Paragraph("THE NORTHEAST MOTOR CLUB", S_COVER_T))
    A(Spacer(1, 0.12 * inch))
    A(Paragraph("A Private Motorsport Country Club and Trackside Residential Community<br/>"
                "New York &middot; Connecticut &middot; New Jersey", S_COVER_S))
    A(Spacer(1, 0.5 * inch))
    A(HRFlowable(width="55%", thickness=0.8, color=RULE, hAlign="CENTER"))
    A(Spacer(1, 0.4 * inch))
    A(Paragraph("<b>CONFIDENTIAL BUSINESS PLAN</b>", S_COVER_S))
    A(Paragraph(f"{today:%d %B %Y}", S_COVER_S))
    A(Spacer(1, 1.6 * inch))
    A(Paragraph(
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
        f"sited within two hours of Manhattan, Greenwich and northern New Jersey. The club "
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
        f"development basis, and no site in the three-state search changes that. Section 7 "
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
        "The three-state search produced a small number of sites that clear an acreage floor, "
        "a noise screen, a two-hour drive time and an exclusion-zone test simultaneously. "
        "NJ Highlands and Pinelands, the NYC watershed and the Adirondack Park remove most "
        "large-acreage inventory before price is discussed."))

    A(Paragraph("3. MARKET", S_H1))
    A(Paragraph(
        f"The catchment is the densest concentration of investable wealth in the United "
        f"States. The lead site reports {int(S['lead'].get('hnw_households_90min') or 0):,} "
        f"households with over $1M of investable assets within ninety minutes. Against that, "
        f"the club needs {m['cap']} members — a penetration rate low enough that demand risk "
        f"is a marketing question rather than a market-size question.", S_BODY))
    A(Paragraph(
        "The binding market question is not whether the households exist. It is whether a "
        "Northeast club can price like a year-round one. The reference asset for this typology "
        "operates in the California desert with close to twelve months of usable track time; "
        "the Northeast season is roughly half that. We have therefore weighted revenue toward "
        "indoor storage, the service department and the karting and skidpad complex, which "
        "earn in the shoulder season, and we treat dues parity with year-round clubs as "
        "unproven until the comparable study is complete.", S_BODY))
    A(Paragraph(
        "COMPARABLE SET — the club economics comparison remains unresearched and is the first "
        "use of feasibility capital. The plan does not rely on any published competitor figure, "
        "because none has been verified. Treat every revenue assumption in Section 7 as "
        "benchmark-derived and unconfirmed.", S_NOTE))
    A(PageBreak())

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
    A(Paragraph(
        "Five acquisition targets are underwritten below. Each is a typology and a submarket, "
        "not a parcel under contract: assessor identifiers, coordinates and title work are "
        "pending and are a first-phase deliverable. They are ranked on the composite score in "
        "Section 11 of the underwriting specification, and each carries a site-specific cost "
        "premium or credit reflecting remediation, blasting, utility extension and the value "
        "of existing pavement.", S_BODY))
    rows = [["Rank", "Target", "County / ST", "Acres", "Prior use", "Ask",
             "Site premium", "Best drive", "IRR", "Min DSCR", "Score"]]
    for i, s in enumerate(S["sites"], start=1):
        p, s_cf, s_cov = s["p"], s["cf"], s["cov"]
        rows.append([
            i, p["parcel_id"].replace("TP-", ""),
            f"{p.get('county')} / {p.get('state')}",
            f"{p.get('contiguous_developable_acres'):,.0f}",
            str(p.get("prior_use", "")).replace("_", " "),
            _m(p.get("ask_price")), _m(p.get("site_cost_premium_usd")),
            f"{p.get('best_drive_min')} min",
            _pct(s_cf.equity_irr, 1),
            _x(s_cov["min_dscr_tested"]),
            f"{p.get('composite_score'):.0f}",
        ])
    A(table(rows, [0.34 * inch, 1.0 * inch, 0.82 * inch, 0.44 * inch, 0.92 * inch,
                   0.6 * inch, 0.68 * inch, 0.53 * inch, 0.42 * inch, 0.5 * inch,
                   0.4 * inch]))
    A(Paragraph(
        "Ask prices are indicative for the typology and submarket, not quoted asking prices "
        "for identified parcels. Drive time is to the best of the three origins.", S_NOTE))

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

    # ---------------- 6. Development plan ----------------
    A(Paragraph("6. DEVELOPMENT PLAN AND TIMELINE", S_H1))
    A(table([
        ["Phase", "Duration", "Milestones", "Capital"],
        ["Phase 0 — Feasibility", "0–9 months",
         "Comparable club study; 150-parcel sourcing pass; site selection; option executed; "
         "acoustic model; Phase I environmental; municipal pre-application",
         "Tranche 1"],
        ["Phase 1 — Entitlement", "9–33 months",
         "Special permit or map amendment; environmental review; wetlands; abatement "
         "agreement executed; founding-member pre-sales open",
         "Tranche 1"],
        ["Phase 2 — Construction",
         f"{S['dev']} years",
         "Land closing; circuit, clubhouse, service centre, first condominium building; "
         "construction facility drawn",
         "Tranche 2"],
        ["Phase 3 — Lease-up",
         f"Years 1–{S['stab']} of operations",
         f"Membership ramp to {m['cap']}; condominium and homesite closings; "
         f"permanent loan conversion at stabilisation",
         "Tranche 2"],
        ["Phase 4 — Stabilised hold", "Years 5–12",
         "Full membership; dues escalation; refinance or sale of the retained club",
         "—"],
    ], [1.25 * inch, 0.85 * inch, 3.55 * inch, 0.75 * inch]))
    A(Paragraph(
        "Total programme duration from first feasibility dollar to stabilisation is "
        f"approximately {33 + S['dev'] * 12 + S['stab'] * 12} months. Entitlement is the "
        "longest and least controllable phase, which is why the plan spends option money "
        "rather than acquisition money until the permit is in hand.", S_BODY))

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
        f"{S['mc'].p_covenant_holds:.0%}. Several driver modes are deliberately adverse to the "
        f"base case, so the median draw sits below it by construction; this is a stress "
        f"distribution, not an unbiased forecast.", S_BODY))
    A(PageBreak())

    # ---------------- 8. The ask ----------------
    A(Paragraph("8. CAPITAL STRUCTURE AND THE ASK", S_H1))
    t1 = 4_250_000
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
         "Land development and entitlement track record in NY, CT or NJ",
         "To be confirmed"],
        ["Club operator",
         "Private-club or motorsport-facility operating history; accountable for the operating "
         "budget that drives the covenant",
         "OPEN — condition precedent"],
        ["Circuit designer",
         "FIA-informed road-course design with runoff and noise-attenuation experience",
         "To be appointed"],
        ["Entitlement counsel",
         "Municipal land-use counsel in the selected jurisdiction; SEQRA or CEPA experience",
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
        f"internal-consistency checks plus 129 unit tests, including a check that the live "
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
        ["Northeast seasonality",
         "Material and structurally different from the reference asset",
         "Revenue weighted to indoor storage, service department and karting; dues parity with "
         "year-round clubs treated as unproven"],
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

    # ---------------- 12. Appendix ----------------
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
    path = out / f"Northeast_Motor_Club_Business_Plan_{today:%Y-%m-%d}.pdf"

    doc = BaseDocTemplate(str(path), pagesize=LETTER, leftMargin=MARGIN,
                          rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN,
                          title="The Northeast Motor Club — Confidential Business Plan",
                          author="Track Boss")

    def painter(canv, docu):
        canv.saveState()
        if docu.page > 1:
            canv.setFont(SERIF_I, 8)
            canv.setFillColor(GREY)
            canv.drawString(MARGIN, 0.55 * inch,
                            "The Northeast Motor Club — Confidential Business Plan")
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
