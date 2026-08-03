"""
TRACK BOSS — Excel Workbook Builder (§9.A)
==========================================

Emits Car_Community_Site_Radar_[YYYY-MM-DD].xlsx with the eleven tabs §9
requires. The `Underwriting` tab is built with LIVE EXCEL FORMULAS -- the
principal can change a dues number in a cell and watch every yield and land
price recompute. Nothing on that tab is a pasted Python result.

Usage:
    python3 build/build_workbook.py --parcels data/parcels.csv --out dist/
    python3 build/build_workbook.py --demo          # schema-only skeleton
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from model import cashflow as cf_mod
from model import gates, risk as rk, scenarios as sc, scoring, two_stack
from model.schema import PARCEL_SCHEMA, coerce

# -----------------------------------------------------------------------------
# House style
# -----------------------------------------------------------------------------
HDR_FILL = PatternFill("solid", fgColor="1F2937")
HDR_FONT = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
SEC_FILL = PatternFill("solid", fgColor="E5E7EB")
SEC_FONT = Font(name="Calibri", size=10, bold=True, color="111827")
BODY_FONT = Font(name="Calibri", size=10)
MONO_FONT = Font(name="Consolas", size=9)
NOTE_FONT = Font(name="Calibri", size=9, italic=True, color="6B7280")

GREEN = PatternFill("solid", fgColor="D1FAE5")
AMBER = PatternFill("solid", fgColor="FEF3C7")
RED = PatternFill("solid", fgColor="FEE2E2")

THIN = Side(style="thin", color="D1D5DB")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

FMT_USD = '"$"#,##0;[Red]("$"#,##0)'
FMT_USD0 = '"$"#,##0'
FMT_PCT = "0.00%"
FMT_NUM = "#,##0"
FMT_DEC = "#,##0.0"


def _safe(v: Any) -> Any:
    """
    Excel has no representation for inf or nan; writing one yields a file that
    will not open. Coverage is infinite whenever there is no basis to lever, and
    a sensitivity cell is nan where the ramp breaks -- both are reachable, so
    every numeric written to a sheet goes through here.
    """
    if isinstance(v, float):
        if v != v:                      # nan
            return "n/a"
        if v in (float("inf"), float("-inf")):
            return "n/m"
    return v


def _header_row(ws: Worksheet, labels: list[str], row: int = 1) -> None:
    for c, label in enumerate(labels, start=1):
        cell = ws.cell(row=row, column=c, value=label)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[row].height = 34


def _section(ws: Worksheet, row: int, label: str, width: int = 2) -> None:
    for c in range(1, width + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = SEC_FILL
        cell.font = SEC_FONT
        cell.border = BORDER
    ws.cell(row=row, column=1, value=label)


def _finish(ws: Worksheet, freeze: str = "A2", widths: dict[str, int] | None = None,
            autofilter: bool = True, ncols: int | None = None, nrows: int | None = None,
            header_row: int = 1) -> None:
    """
    `header_row` must be the actual header row. Anchoring the autofilter at A1
    when the header sits lower makes the range overlap anything above it -- a
    merged banner, for instance -- which produces a file Excel and LibreOffice
    both refuse to open.
    """
    ws.freeze_panes = freeze
    if autofilter and ncols and nrows and nrows > header_row:
        ws.auto_filter.ref = f"A{header_row}:{get_column_letter(ncols)}{nrows}"
    for col, w in (widths or {}).items():
        ws.column_dimensions[col].width = w


def _governing_verdict(cfg: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Grade the lead site on the tests that actually govern a merchant build with
    a retained amenity: equity IRR, covenant coverage from conversion, and exit
    value against RETAINED cost.
    """
    lead = next((p for p in rows if p.get("ask_price")), None)
    if not lead:
        return {"clears": False, "verdict": "No underwritten site with an ask price."}
    ask = float(lead["ask_price"])
    prem = float(lead.get("site_cost_premium_usd") or 0.0)
    cf = cf_mod.project_cash_flow(cfg, ask, horizon_operating_years=12,
                                  site_cost_premium=prem)
    stab = two_stack.stabilization_year(cfg)
    dev = int(round(cfg["cost"]["carry"]["development_years"]))
    cov = cf_mod.covenant_report(cfg and cf, cfg["debt"]["min_dscr"],
                                 tested_from_year=dev + stab)
    irr = cf.equity_irr
    clears = (cov["passes_every_year"] and irr is not None and irr > 0
              and cf.value_to_cost >= 1.0)
    return {
        "clears": clears,
        "verdict": (
            f"{'CLEARS' if clears else 'DOES NOT CLEAR'} on {lead['parcel_id']}: "
            f"equity IRR {irr:.1%} and {cf.equity_multiple:.2f}x multiple over 12 "
            f"operating years; minimum DSCR {cov['min_dscr_tested']:.2f}x against a "
            f"{cfg['debt']['min_dscr']:.2f}x covenant with {cov['breach_count']} breach "
            f"year(s); exit value {cf.value_to_cost:.2f}x retained cost; peak equity "
            f"${cf.peak_equity_requirement:,.0f} in year {cf.peak_funding_year}."
            if irr is not None else
            f"DOES NOT CLEAR on {lead['parcel_id']}: no positive equity return."
        ),
    }


# =============================================================================
# Tab: Executive Summary
# =============================================================================

def _tab_exec_summary(wb: Workbook, rows: list[dict[str, Any]], cfg: dict[str, Any],
                      diag: dict[str, Any]) -> None:
    ws = wb.create_sheet("Executive Summary")
    hurdle = cfg["meta"]["hurdle_yoc"]
    rank_basis = cfg["mandate"]["yoc_basis"]["rank_on"]

    ws["A1"] = "TRACK BOSS — CAR COMMUNITY SITE RADAR"
    ws["A1"].font = Font(name="Calibri", size=16, bold=True)
    ws["A2"] = (
        f"NY / CT / NJ  ·  {hurdle:.2%} YoC hurdle  ·  {diag['min_dscr']:.2f}x min DSCR  ·  "
        f"binding test {diag['required_yield']:.2%} ({diag['binding_constraint']})  ·  "
        f"ranked on {rank_basis.upper()} basis  ·  generated {dt.date.today():%Y-%m-%d}"
    )
    ws["A2"].font = NOTE_FONT

    # Two verdicts, and the distinction matters. The GOVERNING tests are project
    # return, covenant coverage and value against retained cost. The gross-basis
    # yield test is reported below them because holding stabilised club NOI
    # against a basis that includes SOLD garage condos and homesites is not a
    # conservative test, it is an incoherent one. Showing only the gross verdict
    # made a financeable programme read as dead.
    gov = _governing_verdict(cfg, rows)
    ws["A4"] = "GOVERNING TESTS — project return, covenant, value vs retained cost"
    ws["A4"].font = SEC_FONT
    ws["A5"] = gov["verdict"]
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A5"].fill = GREEN if gov["clears"] else RED
    ws.merge_cells("A5:J6")

    ws["A7"] = "SECONDARY — gross-basis yield on cost (see business plan §13)"
    ws["A7"].font = SEC_FONT
    ws["A8"] = diag["verdict"] + (
        "  NOTE: this test charges the retained club with the full cost of "
        "garage condos and homesites that are SOLD. It is reported for continuity "
        "with the original mandate and is not the governing test.")
    ws["A8"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A8"].font = NOTE_FONT
    ws.merge_cells("A8:J9")
    ws.row_dimensions[5].height = 16

    for i, (label, val, fmt) in enumerate([
        ("Stabilized NOI", diag["stabilized_noi"], FMT_USD),
        ("NOI required at zero land cost", diag["noi_required_at_zero_land"], FMT_USD),
        ("NOI gap", diag["noi_gap"], FMT_USD),
        ("Non-land cost basis", diag["non_land_cost"], FMT_USD),
        ("For-sale net proceeds", diag["for_sale_net_proceeds"], FMT_USD),
        ("Max supportable land (ranking basis)", diag["max_supportable_land"], FMT_USD),
        ("Equity hurdle", diag["hurdle"], FMT_PCT),
        ("DSCR-implied yield", diag["dscr_implied_yield"], FMT_PCT),
        ("Required yield (binding)", diag["required_yield"], FMT_PCT),
    ], start=11):
        ws.cell(row=i, column=1, value=label).font = BODY_FONT
        c = ws.cell(row=i, column=3, value=_safe(val))
        c.number_format = fmt
        c.font = Font(name="Calibri", size=10, bold=True)

    start = 21
    ws.cell(row=start - 1, column=1, value="TOP 10 RANKED").font = SEC_FONT
    headers = [
        "Rank", "Parcel ID", "Municipality", "County", "ST", "Acres", "Prior Use",
        "Best Drive (min)", "Ask", "Max Land — Gross", "Max Land — Net",
        "YoC @ Ask — Gross", "YoC @ Ask — Net", "DSCR @ Ask — Gross", "DSCR @ Ask — Net",
        "Headroom", "Composite", "Grade",
        "Why this one wins", "What would kill it", "Link",
    ]
    _header_row(ws, headers, row=start)

    for i, r in enumerate(rows[:10], start=1):
        rr = start + i
        vals = [
            i, r.get("parcel_id"), r.get("municipality"), r.get("county"), r.get("state"),
            r.get("contiguous_developable_acres"), r.get("prior_use"), r.get("best_drive_min"),
            r.get("ask_price"), r.get("max_land_gross"), r.get("max_land_net"),
            r.get("yoc_gross_at_ask"), r.get("yoc_net_at_ask"),
            r.get("dscr_gross_at_ask"), r.get("dscr_net_at_ask"), r.get("headroom_to_ask"),
            r.get("composite_score"), r.get("grade"),
            r.get("why_wins", ""), r.get("what_kills", ""), r.get("listing_url"),
        ]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=rr, column=c, value=_safe(v))
            cell.font = BODY_FONT
            cell.border = BORDER
        for col in (9, 10, 11, 16):
            ws.cell(row=rr, column=col).number_format = FMT_USD
        for col in (12, 13):
            ws.cell(row=rr, column=col).number_format = FMT_PCT
        for col in (14, 15):
            ws.cell(row=rr, column=col).number_format = "0.00x"
        ws.cell(row=rr, column=17).number_format = FMT_DEC
        if r.get("listing_url"):
            link = ws.cell(row=rr, column=21)
            link.hyperlink = r["listing_url"]
            link.font = Font(name="Calibri", size=10, color="2563EB", underline="single")

    last = start + max(len(rows[:10]), 1)
    rng_yoc = f"L{start + 1}:M{last}"
    ws.conditional_formatting.add(rng_yoc, CellIsRule(operator="greaterThanOrEqual",
                                                      formula=[str(hurdle)], fill=GREEN))
    ws.conditional_formatting.add(rng_yoc, CellIsRule(operator="between",
                                                      formula=[str(hurdle * 0.85), str(hurdle)],
                                                      fill=AMBER))
    ws.conditional_formatting.add(rng_yoc, CellIsRule(operator="lessThan",
                                                      formula=[str(hurdle * 0.85)], fill=RED))
    rng_dscr = f"N{start + 1}:O{last}"
    ws.conditional_formatting.add(rng_dscr, CellIsRule(
        operator="greaterThanOrEqual", formula=[str(cfg["debt"]["min_dscr"])], fill=GREEN))
    ws.conditional_formatting.add(rng_dscr, CellIsRule(
        operator="lessThan", formula=[str(cfg["debt"]["min_dscr"])], fill=RED))
    ws.conditional_formatting.add(
        f"Q{start + 1}:Q{last}",
        ColorScaleRule(start_type="num", start_value=35, start_color="FEE2E2",
                       mid_type="num", mid_value=60, mid_color="FEF3C7",
                       end_type="num", end_value=85, end_color="D1FAE5"),
    )

    _finish(ws, freeze=f"A{start + 1}", ncols=len(headers), nrows=last, header_row=start,
            widths={"A": 6, "B": 14, "C": 20, "D": 14, "E": 5, "F": 9, "G": 20,
                    "H": 12, "I": 14, "J": 18, "K": 18, "L": 15, "M": 15, "N": 13,
                    "O": 13, "P": 14, "Q": 11, "R": 22, "S": 50, "T": 50, "U": 32})


# =============================================================================
# Tab: Full Parcel Universe
# =============================================================================

def _tab_universe(wb: Workbook, rows: list[dict[str, Any]]) -> None:
    ws = wb.create_sheet("Full Parcel Universe")
    _header_row(ws, [f.label for f in PARCEL_SCHEMA])

    for i, r in enumerate(rows, start=2):
        for c, f in enumerate(PARCEL_SCHEMA, start=1):
            v = r.get(f.key)
            if isinstance(v, (list, tuple)):
                v = ", ".join(str(x) for x in v)
            elif isinstance(v, dict):
                v = ", ".join(f"{k}:{x}" for k, x in v.items())
            cell = ws.cell(row=i, column=c, value=_safe(v))
            cell.font = BODY_FONT
            if f.kind == "usd":
                cell.number_format = FMT_USD
            elif f.kind == "pct":
                cell.number_format = FMT_PCT
            elif f.kind in ("float", "int"):
                cell.number_format = FMT_NUM
            if f.key == "listing_url" and v:
                cell.hyperlink = str(v)
                cell.font = Font(name="Calibri", size=10, color="2563EB", underline="single")

    n = len(PARCEL_SCHEMA)
    _finish(ws, freeze="G2", ncols=n, nrows=max(len(rows) + 1, 2))
    for c in range(1, n + 1):
        ws.column_dimensions[get_column_letter(c)].width = 18


# =============================================================================
# Tab: Underwriting  (LIVE FORMULAS)
# =============================================================================

def _tab_underwriting(wb: Workbook, rows: list[dict[str, Any]], cfg: dict[str, Any]) -> None:
    """
    Live two-stack model. Column B holds the shared program assumptions and the
    derived NOI / cost stack. Columns D onward are one parcel each, and every
    yield and land-price cell is an Excel formula pointing back at column B.

    Change a dues figure in B and the whole sheet moves. That is the point.
    """
    ws = wb.create_sheet("Underwriting")
    inc, m, fs, cost = cfg["income"], cfg["income"]["membership"], cfg["for_sale"], cfg["cost"]
    hurdle = cfg["meta"]["hurdle_yoc"]
    top = rows[:15]

    ws["A1"] = "TWO-STACK UNDERWRITING MODEL — LIVE"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws["A2"] = ("Column B drives everything. Yellow cells are inputs; white cells are formulas. "
                "Stack A proceeds offset the NET basis only.")
    ws["A2"].font = NOTE_FONT

    r = 4
    INPUT_FILL = PatternFill("solid", fgColor="FEF9C3")

    def put_input(label: str, value: Any, fmt: str = FMT_NUM, note: str = "") -> str:
        nonlocal r
        ws.cell(row=r, column=1, value=label).font = BODY_FONT
        c = ws.cell(row=r, column=2, value=value)
        c.number_format, c.fill, c.border = fmt, INPUT_FILL, BORDER
        if note:
            ws.cell(row=r, column=3, value=note).font = NOTE_FONT
        ref = f"$B${r}"
        r += 1
        return ref

    def put_formula(label: str, formula: str, fmt: str = FMT_USD, note: str = "") -> str:
        nonlocal r
        ws.cell(row=r, column=1, value=label).font = BODY_FONT
        c = ws.cell(row=r, column=2, value=formula)
        c.number_format, c.border = fmt, BORDER
        c.font = Font(name="Calibri", size=10, bold=True)
        if note:
            ws.cell(row=r, column=3, value=note).font = NOTE_FONT
        ref = f"$B${r}"
        r += 1
        return ref

    # --- Stack B inputs ------------------------------------------------------
    _section(ws, r, "STACK B — INCOME ASSUMPTIONS", 3); r += 1
    cap = put_input("Membership cap", m["cap"])
    stab_pct = put_input("Stabilization threshold", m["stabilization_threshold"], FMT_PCT)
    dues = put_input("Annual dues", m["annual_dues_usd"], FMT_USD0)
    init_fee = put_input("Initiation fee", m["initiation_fee_usd"], FMT_USD0)
    tenure = put_input("Expected tenure (yrs)", m["expected_tenure_years"])
    esc = put_input("Dues escalator", m["dues_escalator"], FMT_PCT)

    # Membership ramp, live. Stabilization is DERIVED from the ramp -- it is the
    # first year cumulative membership crosses the threshold -- and NOI is taken
    # at the actual member count in that year, not at the threshold itself.
    # cap x 85% would understate members whenever the ramp overshoots.
    r += 1
    _section(ws, r, "MEMBERSHIP RAMP (cumulative, capped)", 4); r += 1
    for c, h in enumerate(["Operating year", "Members added", "Cumulative", "Qualifies?"], start=1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font, cell.fill = HDR_FONT, HDR_FILL
    r += 1
    ramp_first = r
    for i, add in enumerate(m["ramp"], start=1):
        ws.cell(row=r, column=1, value=i).font = BODY_FONT
        a = ws.cell(row=r, column=2, value=add)
        a.fill, a.border, a.number_format = INPUT_FILL, BORDER, FMT_NUM
        prev = f"C{r - 1}" if i > 1 else "0"
        cum = ws.cell(row=r, column=3, value=f"=MIN({cap},{prev}+B{r})")
        cum.number_format, cum.border = FMT_NUM, BORDER
        # 9999 sentinel so MIN() picks the first qualifying year.
        q = ws.cell(row=r, column=4, value=f"=IF(C{r}>={cap}*{stab_pct},A{r},9999)")
        q.number_format, q.border = FMT_NUM, BORDER
        r += 1
    ramp_last = r - 1

    stab_yr = put_formula("Stabilization year (derived)",
                          f"=MIN(D{ramp_first}:D{ramp_last})", FMT_NUM,
                          "§3: first year membership reaches the threshold")
    members = put_formula(
        "Members at stabilization",
        f"=INDEX(C{ramp_first}:C{ramp_last},{stab_yr})", FMT_NUM,
        "actual ramp count in that year, not cap x threshold",
    )
    infl = put_formula("Inflation factor at stabilization", f"=(1+{esc})^({stab_yr}-1)", "0.0000")

    r += 1
    _section(ws, r, "STACK B — REVENUE AT STABILIZATION", 3); r += 1
    dues_rev = put_formula("Dues revenue", f"={members}*{dues}*{infl}")
    init_rev = put_formula(
        "Initiation — amortized", f"={members}*{init_fee}/{tenure}", FMT_USD,
        "§3: NOT capitalized. Valid while stabilization year <= tenure.",
    )
    anc_refs = []
    for k, v in inc["ancillary_annual_usd"].items():
        anc_refs.append(put_input(f"  {k.replace('_', ' ').title()}", v, FMT_USD0))
    frac = put_formula("Member penetration at stabilization", f"={members}/{cap}", FMT_PCT)
    anc = put_formula("Ancillary revenue (scaled)",
                      f"=SUM({','.join(anc_refs)})*{frac}*{infl}")
    egi = put_formula("EFFECTIVE GROSS INCOME", f"={dues_rev}+{init_rev}+{anc}")

    r += 1
    _section(ws, r, "STACK B — OPERATING EXPENSE", 3); r += 1
    opex_refs = [put_input(f"  {k.replace('_', ' ').title()}", v, FMT_USD0)
                 for k, v in inc["opex_annual_usd"].items()]
    opex = put_formula("Total opex (escalated, does not ramp)",
                       f"=SUM({','.join(opex_refs)})*{infl}")
    mgmt_pct = put_input("Management fee (% EGI)", inc["management_fee_pct_egi"], FMT_PCT)
    res_pct = put_input("Replacement reserve (% EGI)", inc["replacement_reserve_pct_egi"], FMT_PCT)
    mgmt = put_formula("Management fee", f"={egi}*{mgmt_pct}")
    reserve = put_formula("Replacement reserve", f"={egi}*{res_pct}")
    noi = put_formula("STABILIZED NOI", f"={egi}-{opex}-{mgmt}-{reserve}")

    r += 1
    _section(ws, r, "STACK A — FOR-SALE (merchant build: both components sold)", 3); r += 1
    c_units = put_input("Garage condo units", fs["garage_condos"]["units"])
    c_sf = put_input("Avg condo SF", fs["garage_condos"]["avg_sf"])
    c_psf = put_input("Condo sale $/SF", fs["garage_condos"]["sale_price_psf"], FMT_USD0)
    c_cost_psf = put_input("Condo hard cost $/SF", fs["garage_condos"]["hard_cost_psf"], FMT_USD0)
    h_units = put_input("Homesite units", fs["homesites"]["units"])
    h_price = put_input("Homesite price", fs["homesites"]["price_per_unit_usd"], FMT_USD0)
    h_cost = put_input("Homesite improvement cost", fs["homesites"]["improvement_cost_per_unit_usd"], FMT_USD0)
    cos_pct = put_input("Cost of sale", fs["garage_condos"]["cost_of_sale_pct"], FMT_PCT)
    c_absorb = put_input("Condo absorption (units/yr)",
                         fs["garage_condos"]["absorption_units_per_year"])
    h_absorb = put_input("Homesite absorption (units/yr)",
                         fs["homesites"]["absorption_units_per_year"])
    sellout = put_formula("Sell-out period (yrs)",
                          f"=MAX({c_units}/{c_absorb},{h_units}/{h_absorb})", FMT_DEC)

    fs_rev = put_formula("For-sale gross revenue", f"={c_units}*{c_sf}*{c_psf}+{h_units}*{h_price}")
    fs_vert = put_formula("For-sale vertical cost", f"={c_units}*{c_sf}*{c_cost_psf}+{h_units}*{h_cost}",
                          FMT_USD, "sits inside HARD COST below")
    fs_net = put_formula("NET FOR-SALE PROCEEDS", f"={fs_rev}*(1-{cos_pct})", FMT_USD,
                         "after cost of sale; offsets NET basis only")

    r += 1
    _section(ws, r, "COST STACK — NON-LAND", 3); r += 1
    miles = put_input("Track miles", cost["track"]["miles"], FMT_DEC)
    per_mile = put_input("Track hard cost / mile", cost["track"]["hard_cost_per_mile_usd"], FMT_USD0)
    paddock = put_input("Paddock and pit", cost["track"]["paddock_and_pit_usd"], FMT_USD0)
    vert_refs = [put_input(f"  {k.replace('_', ' ').title()}", v, FMT_USD0)
                 for k, v in cost["vertical_hard_usd"].items()]
    infra_refs = [put_input(f"  {k.replace('_', ' ').title()}", v, FMT_USD0)
                  for k, v in cost["site_infrastructure_usd"].items()]
    hard = put_formula(
        "TOTAL HARD COST",
        f"={miles}*{per_mile}+{paddock}+SUM({','.join(vert_refs)})"
        f"+SUM({','.join(infra_refs)})+{fs_vert}",
    )
    soft_pct = put_input("Soft cost (% of hard)", cost["soft_cost_pct_of_hard"], FMT_PCT)
    soft = put_formula("Soft cost", f"={hard}*{soft_pct}")
    entitle = put_input("Entitlement budget", cost["entitlement_budget_usd"], FMT_USD0)
    ffe = put_input("FF&E", cost["ffe_usd"], FMT_USD0)
    cont_pct = put_input("Contingency (% of hard+soft)", cost["contingency_pct"], FMT_PCT)
    cont = put_formula("Contingency", f"=({hard}+{soft})*{cont_pct}")
    S = put_formula("NON-LAND SUBTOTAL  (S)", f"={hard}+{soft}+{entitle}+{ffe}+{cont}")

    rate = put_input("Carry interest rate", cost["carry"]["interest_rate"], FMT_PCT)
    avg_out = put_input("Avg outstanding balance", cost["carry"]["avg_outstanding_pct"], FMT_PCT)
    dev_yrs = put_input("Development years", cost["carry"]["development_years"], FMT_DEC)
    if cost["carry"].get("follows_absorption", False):
        carry_yrs = put_formula("Carry period (yrs)", f"=MAX({dev_yrs},{sellout})", FMT_DEC,
                                "merchant build: capital is out until the last unit sells")
    else:
        carry_yrs = dev_yrs
    k = put_formula("CARRY FACTOR  (k)", f"={rate}*{avg_out}*{carry_yrs}", "0.0000")
    incent = put_input("Capital incentives (IDA/PILOT/EDA)", cost["incentives_usd"], FMT_USD0,
                       "base case zero — upside only")

    # --- Property tax --------------------------------------------------------
    r += 1
    _section(ws, r, "PROPERTY TAX (ad valorem)", 3); r += 1
    pt = cfg["income"]["property_tax"]
    tax_share = put_input("Taxable share of gross basis", pt["taxable_share_of_gross_basis"],
                          FMT_PCT, "sold units are separately assessed to their owners")
    assess = put_input("Assessment ratio", pt["assessment_ratio"], FMT_PCT)
    eff_rate = put_input("Effective tax rate", pt["effective_rate"], FMT_PCT)
    abate = put_input("Abatement (PILOT/EDA)", pt["abatement_pct"], FMT_PCT)
    tau = put_formula("TAX LOAD (tau)", f"={tax_share}*{assess}*{eff_rate}*(1-{abate})",
                      FMT_PCT, "adds directly to the required yield")

    # --- Debt and coverage ---------------------------------------------------
    r += 1
    _section(ws, r, "DEBT AND COVERAGE", 3); r += 1
    dbt = cfg["debt"]
    hurdle_ref = put_input("Equity hurdle YoC", hurdle, FMT_PCT)
    min_dscr = put_input("Minimum DSCR", dbt["min_dscr"], "0.00",
                         "confirmed by the principal")
    ltc = put_input("Target LTC", dbt["target_ltc"], FMT_PCT)
    perm_rate = put_input("Permanent coupon", dbt["permanent_rate"], FMT_PCT)
    amort = put_input("Amortization (yrs)", dbt["amortization_years"], FMT_NUM)
    ppy = put_input("Periods per year", dbt.get("periods_per_year", 12), FMT_NUM)
    mc = put_formula(
        "Mortgage constant", f"={ppy}*({perm_rate}/{ppy})/(1-(1+{perm_rate}/{ppy})^(-{amort}*{ppy}))",
        "0.000000", "annual debt service per $1 of loan")
    dscr_yield = put_formula("DSCR-implied yield", f"={min_dscr}*{ltc}*{mc}", FMT_PCT,
                             "the yield the covenant alone demands")
    required_ref = put_formula("REQUIRED YIELD (binding)", f"=MAX({hurdle_ref},{dscr_yield})",
                               FMT_PCT, "the tighter of hurdle and covenant")
    effective_ref = put_formula("EFFECTIVE TEST (required + tau)", f"={required_ref}+{tau}",
                                FMT_PCT, "what the deal must actually earn")
    ws.cell(row=r, column=1, value="Binding constraint").font = BODY_FONT
    bc = ws.cell(row=r, column=2, value=f'=IF({dscr_yield}>{hurdle_ref},"DSCR","YIELD")')
    bc.border, bc.font = BORDER, Font(name="Calibri", size=10, bold=True)
    bc.alignment = Alignment(horizontal="center")
    r += 1

    # --- Per-parcel block ----------------------------------------------------
    r += 2
    _section(ws, r, "PER-PARCEL — LIVE FORMULAS", 3 + len(top))
    hdr = r
    ws.cell(row=hdr, column=1, value="PER-PARCEL — LIVE FORMULAS")
    labels = [
        "Parcel ID", "Municipality", "Ask price",
        "Max supportable land — GROSS", "Max supportable land — NET",
        "Gross cost basis @ ask", "Net cost basis @ ask",
        "Property tax @ ask", "NOI after tax @ ask",
        "YoC @ ask — GROSS", "YoC @ ask — NET",
        "DSCR @ ask — GROSS", "DSCR @ ask — NET",
        "Headroom vs ask (ranking basis)", "Ask ÷ max supportable",
        "PRICE-INFEASIBLE (>20% over)", "Clears hurdle AND covenant",
    ]
    for i, lab in enumerate(labels, start=1):
        cell = ws.cell(row=hdr + i, column=1, value=lab)
        cell.font = BODY_FONT if i > 2 else Font(name="Calibri", size=10, bold=True)
        cell.border = BORDER

    rank_basis = cfg["mandate"]["yoc_basis"]["rank_on"]
    for j, p in enumerate(top):
        col = 4 + j                      # start at column D
        L = get_column_letter(col)
        ask_row = hdr + 3

        ws.cell(row=hdr + 1, column=col, value=p.get("parcel_id")).font = Font(
            name="Calibri", size=10, bold=True)
        ws.cell(row=hdr + 2, column=col, value=p.get("municipality")).font = BODY_FONT
        ask = ws.cell(row=ask_row, column=col, value=p.get("ask_price"))
        ask.number_format, ask.fill, ask.border = FMT_USD, INPUT_FILL, BORDER

        A = f"{L}{ask_row}"
        # Closed-form inversions, written as Excel. Solved at the REQUIRED
        # yield -- the tighter of the equity hurdle and the DSCR-implied yield:
        #   gross: NOI / (y*(1+k)) - S
        #   net:   (NOI/y + P + G) / (1+k) - S
        # DSCR is NOI over debt service, with the loan sized as LTC x basis.
        # Ad-valorem tax is equivalent to adding tau to the required yield, so
        # the inversions divide by (required + tau) rather than netting tax out
        # of NOI first. YoC and DSCR at the ask net it explicitly.
        f = {
            hdr + 4: f"={noi}/({effective_ref}*(1+{k}))-{S}",
            hdr + 5: f"=(({noi}+{required_ref}*({fs_net}+{incent}))/{effective_ref})"
                     f"/(1+{k})-{S}",
            hdr + 6: f"=({A}+{S})*(1+{k})",
            hdr + 7: f"=({A}+{S})*(1+{k})-{fs_net}-{incent}",
            hdr + 8: f"={tau}*MAX(0,{L}{hdr + 6})",
            hdr + 9: f"={noi}-{L}{hdr + 8}",
            hdr + 10: f"=IF({L}{hdr + 6}<=0,\"n/a\",{L}{hdr + 9}/{L}{hdr + 6})",
            hdr + 11: f"=IF({L}{hdr + 7}<=0,\"n/a\",{L}{hdr + 9}/{L}{hdr + 7})",
            hdr + 12: f"=IF({L}{hdr + 6}<=0,\"n/a\",{L}{hdr + 9}/({ltc}*{L}{hdr + 6}*{mc}))",
            hdr + 13: f"=IF({L}{hdr + 7}<=0,\"n/a\",{L}{hdr + 9}/({ltc}*{L}{hdr + 7}*{mc}))",
        }
        max_ref = f"{L}{hdr + 4}" if rank_basis == "gross" else f"{L}{hdr + 5}"
        yoc_ref = f"{L}{hdr + 10}" if rank_basis == "gross" else f"{L}{hdr + 11}"
        dscr_ref = f"{L}{hdr + 12}" if rank_basis == "gross" else f"{L}{hdr + 13}"
        f[hdr + 14] = f"={max_ref}-{A}"
        f[hdr + 15] = f"=IF({max_ref}<=0,\"n/a\",{A}/{max_ref})"
        f[hdr + 16] = f"=IF({max_ref}<=0,\"YES\",IF({A}>{max_ref}*1.2,\"YES\",\"no\"))"
        f[hdr + 17] = (
            f"=IF(AND(ISNUMBER({yoc_ref}),ISNUMBER({dscr_ref}),"
            f"{yoc_ref}>={hurdle_ref},{dscr_ref}>={min_dscr}),\"YES\",\"no\")"
        )

        pct_rows = {hdr + 10, hdr + 11, hdr + 15}
        dscr_rows = {hdr + 12, hdr + 13}
        text_rows = {hdr + 16, hdr + 17}
        for row_i, formula in f.items():
            cell = ws.cell(row=row_i, column=col, value=formula)
            cell.border = BORDER
            cell.font = BODY_FONT
            if row_i in pct_rows:
                cell.number_format = FMT_PCT
            elif row_i in dscr_rows:
                cell.number_format = "0.00x"
            elif row_i in text_rows:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.number_format = FMT_USD

    if top:
        end = get_column_letter(3 + len(top))
        yoc_rng = f"D{hdr + 10}:{end}{hdr + 11}"
        ws.conditional_formatting.add(yoc_rng, CellIsRule(
            operator="greaterThanOrEqual", formula=[str(hurdle)], fill=GREEN))
        ws.conditional_formatting.add(yoc_rng, CellIsRule(
            operator="lessThan", formula=[str(hurdle * 0.85)], fill=RED))
        dscr_rng = f"D{hdr + 12}:{end}{hdr + 13}"
        ws.conditional_formatting.add(dscr_rng, CellIsRule(
            operator="greaterThanOrEqual", formula=[str(cfg["debt"]["min_dscr"])], fill=GREEN))
        ws.conditional_formatting.add(dscr_rng, CellIsRule(
            operator="lessThan", formula=[str(cfg["debt"]["min_dscr"])], fill=RED))
        ws.conditional_formatting.add(f"D{hdr + 16}:{end}{hdr + 16}", CellIsRule(
            operator="equal", formula=['"YES"'], fill=RED))
        ws.conditional_formatting.add(f"D{hdr + 17}:{end}{hdr + 17}", CellIsRule(
            operator="equal", formula=['"YES"'], fill=GREEN))

    ws.freeze_panes = "D1"
    ws.column_dimensions["A"].width = 38
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 34
    for j in range(len(top)):
        ws.column_dimensions[get_column_letter(4 + j)].width = 20


# =============================================================================
# Tab: Sensitivity
# =============================================================================

def _tab_sensitivity(wb: Workbook, cfg: dict[str, Any]) -> None:
    ws = wb.create_sheet("Sensitivity")
    ws["A1"] = "BREAK-EVEN LAND PRICE SURFACE"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws["A2"] = ("Each cell is the maximum supportable land price at that combination. "
                "Negative means the income stack cannot carry the vertical at any land price.")
    ws["A2"].font = NOTE_FONT

    row = 4
    pairs = [
        ("membership_cap", "annual_dues_usd"),
        ("track_hard_cost_per_mile_usd", "annual_dues_usd"),
        ("membership_cap", "track_hard_cost_per_mile_usd"),
        ("absorption_years", "annual_dues_usd"),
    ]
    for x_key, y_key in pairs:
        grid = two_stack.sensitivity_grid(cfg, x_key, y_key)
        ws.cell(row=row, column=1,
                value=f"{y_key}  ×  {x_key}   →   max supportable land, {grid['basis']} basis")
        ws.cell(row=row, column=1).font = SEC_FONT
        row += 1

        ws.cell(row=row, column=1, value=f"{y_key} ↓ / {x_key} →").font = HDR_FONT
        ws.cell(row=row, column=1).fill = HDR_FILL
        for c, xv in enumerate(grid["x_values"], start=2):
            cell = ws.cell(row=row, column=c, value=xv)
            cell.fill, cell.font = HDR_FILL, HDR_FONT
            cell.number_format = FMT_NUM
            cell.alignment = Alignment(horizontal="center")
        row += 1

        first = row
        for yi, yv in enumerate(grid["y_values"]):
            hc = ws.cell(row=row, column=1, value=yv)
            hc.fill, hc.font = SEC_FILL, SEC_FONT
            hc.number_format = FMT_NUM
            for xi in range(len(grid["x_values"])):
                cell = ws.cell(row=row, column=2 + xi, value=_safe(grid["cells"][yi][xi]))
                cell.number_format = FMT_USD
                cell.border = BORDER
                cell.font = BODY_FONT
            row += 1

        last_col = get_column_letter(1 + len(grid["x_values"]))
        ws.conditional_formatting.add(
            f"B{first}:{last_col}{row - 1}",
            ColorScaleRule(start_type="min", start_color="FEE2E2",
                           mid_type="num", mid_value=0, mid_color="FEF3C7",
                           end_type="max", end_color="D1FAE5"),
        )
        row += 2

    # Initiation-fee bookends -- §3 requires the sensitivity both ways.
    ws.cell(row=row, column=1, value="INITIATION FEE TREATMENT — §3 BOOKENDS").font = SEC_FONT
    row += 1
    for c, h in enumerate(["Treatment", "Stabilized NOI", "Max Land — Gross", "Max Land — Net"], start=1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.fill, cell.font = HDR_FILL, HDR_FONT
    row += 1
    for mode, vals in two_stack.initiation_bookends(cfg).items():
        ws.cell(row=row, column=1, value=mode).font = BODY_FONT
        for c, key in enumerate(["stabilized_noi", "max_land_gross", "max_land_net"], start=2):
            cell = ws.cell(row=row, column=c, value=vals[key])
            cell.number_format = FMT_USD
            cell.border = BORDER
        row += 1

    ws.freeze_panes = "B1"
    ws.column_dimensions["A"].width = 34
    for c in range(2, 10):
        ws.column_dimensions[get_column_letter(c)].width = 18


# =============================================================================
# Simple tabular tabs
# =============================================================================

def _simple_tab(wb: Workbook, name: str, headers: list[str], rows: list[list[Any]],
                widths: dict[str, int] | None = None, note: str = "") -> Worksheet:
    ws = wb.create_sheet(name)
    start = 1
    if note:
        ws["A1"] = note
        ws["A1"].font = NOTE_FONT
        start = 2
    _header_row(ws, headers, row=start)
    for i, row in enumerate(rows, start=start + 1):
        for c, v in enumerate(row, start=1):
            cell = ws.cell(row=i, column=c, value=_safe(v))
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    _finish(ws, freeze=f"A{start + 1}", ncols=len(headers),
            nrows=len(rows) + start, widths=widths, header_row=start,
            autofilter=bool(rows))
    return ws


def _tab_noise(wb: Workbook, rows: list[dict[str, Any]]) -> None:
    headers = ["Parcel ID", "Municipality", "ST", "Zoning District", "Outdoor Rec Posture",
               "Noise Ordinance Citation", "Daytime dBA", "Measurement Point",
               "Absolute / Ambient", "Nearest Residence (ft)", "Residences <1 mi",
               "Prior Use", "Permitting Path", "Timeline (mo)", "Prior Denial",
               "Opposition Risk", "Flags"]
    data = [[
        r.get("parcel_id"), r.get("municipality"), r.get("state"), r.get("zoning_district"),
        r.get("zoning_posture"), r.get("noise_ordinance_citation"),
        r.get("noise_ordinance_dba_day") if r.get("noise_ordinance_dba_day") is not None
        else "UNVERIFIED — call the clerk",
        r.get("noise_measurement_point"), r.get("noise_standard_type"),
        r.get("nearest_residence_ft"), r.get("residences_within_1mi"), r.get("prior_use"),
        r.get("permitting_path"), r.get("permitting_timeline_months"),
        "YES" if r.get("prior_denial_same_use") else "no", r.get("opposition_risk"),
        r.get("flags"),
    ] for r in rows]
    _simple_tab(wb, "Noise & Entitlement", headers, data,
                widths={"A": 14, "B": 20, "C": 5, "F": 30, "Q": 60},
                note="§10: a blank dBA is a research task, never an invented number.")


def _tab_physical(wb: Workbook, rows: list[dict[str, Any]]) -> None:
    headers = ["Parcel ID", "Gross Acres", "Contiguous Developable", "Acres <8% Grade",
               "Elevation Change (ft)", "Natural Bowl", "% Wetlands", "% Floodway",
               "% Watercourse Buffer", "Soil Class", "Bedrock (ft)", "Cut/Fill (CY)",
               "3-Phase Power (mi)", "Water", "Sewer", "Perc (min/in)", "Fiber",
               "Existing Pavement"]
    data = [[
        r.get("parcel_id"), r.get("gross_acres"), r.get("contiguous_developable_acres"),
        r.get("contiguous_acres_under_8pct_grade"), r.get("elevation_change_ft"),
        "YES" if r.get("natural_amphitheater") else "no",
        r.get("pct_wetlands"), r.get("pct_floodway"), r.get("pct_watercourse_buffer"),
        r.get("soil_class"), r.get("bedrock_depth_ft"), r.get("cutfill_balance_cy"),
        r.get("three_phase_power_distance_mi"), r.get("water_source"), r.get("sewer"),
        r.get("perc_rate_min_per_inch"), "YES" if r.get("fiber_available") else "no",
        "YES" if r.get("existing_paved_runway") else "no",
    ] for r in rows]
    ws = _simple_tab(wb, "Physical", headers, data, widths={"A": 14})
    for row in range(2, len(data) + 2):
        for col in (7, 8, 9):
            ws.cell(row=row, column=col).number_format = FMT_PCT


def _tab_comps(wb: Workbook) -> None:
    """
    §7 forbids stating any comp figure from memory. This tab ships as a
    structured blank for Comp Analyst to populate with cited, dated research.
    """
    headers = ["Club", "State", "Acres", "Track Miles", "Membership Cap", "Initiation Fee",
               "Annual Dues", "Garage Condo $/SF", "Local Industrial Flex $/SF",
               "Spread", "Absorption (months)", "Members per Track Mile",
               "Dues ÷ Initiation", "Source ID", "Data As-Of", "Confidence"]
    clubs = [
        ("Monticello Motor Club", "NY"), ("New Jersey Motorsports Park", "NJ"),
        ("Thompson Speedway Motorsports Park", "CT"), ("Lime Rock Park", "CT"),
        ("Palmer Motorsports Park", "MA"), ("Club Motorsports", "NH"),
        ("M1 Concourse", "MI"), ("Iron Gate Motor Condos", "VT"),
        ("Autobahn Country Club", "IL"), ("Atlanta Motorsports Park", "GA"),
        ("Apex Motor Club", "AZ"), ("The Concours Club", "FL"),
        ("The Thermal Club", "CA"),
    ]
    data = [[name, st] + [None] * 11 + [None, "UNRESEARCHED"] for name, st in clubs]
    _simple_tab(wb, "Comps", headers, data, widths={"A": 34, "B": 5},
                note="§7: every cell below must be pulled and cited. Do not fill from memory.")


def _tab_land_comps(wb: Workbook) -> None:
    headers = ["County", "State", "Property", "Acres", "Sale Price", "$/Acre", "Sale Date",
               "Prior Use", "Deed Reference", "Source ID", "Confidence"]
    _simple_tab(wb, "Land Comps", headers, [],
                widths={"A": 16, "C": 34, "I": 24},
                note="Recent large-acreage trades. County clerk deed records preferred over MLS.")


def _tab_risk(wb: Workbook, rows: list[dict[str, Any]]) -> None:
    headers = ["Rank", "Parcel ID", "Risk", "Category", "Severity", "Likelihood",
               "Mitigant", "Cost to Cure", "Owner", "Source ID"]
    data: list[list[Any]] = []
    n = 0
    for r in rows:
        for flag in str(r.get("flags") or "").split(" | "):
            if not flag.strip():
                continue
            n += 1
            data.append([n, r.get("parcel_id"), flag.strip(), "Screen flag",
                         None, None, None, None, None, None])
    _simple_tab(wb, "Risk Register", headers, data,
                widths={"C": 55, "G": 45}, note="Auto-seeded from screen flags; Risk Marshal ranks and prices each.")


def _tab_sources(wb: Workbook, sources: list[dict[str, Any]]) -> None:
    headers = ["No.", "Source Name", "Cited For", "URL", "Accessed", "Tier",
               "Confidence", "Provenance Note"]
    data = [[s.get("no"), s.get("name"), s.get("cited_for"), s.get("url"),
             s.get("accessed"), s.get("tier"), s.get("confidence"), s.get("note")]
            for s in sources]
    ws = _simple_tab(
        wb, "Sources", headers, data,
        widths={"A": 6, "B": 30, "C": 55, "D": 45, "E": 12, "F": 20, "G": 22, "H": 60},
        note=("§10: every claim in this workbook traces to a numbered row here. "
              "Nothing in `config/underwriting_inputs.yaml` marked `basis: assumed` "
              "is sourced — those are structural placeholders, not estimates."))
    for i in range(len(data)):
        cell = ws.cell(row=i + 3, column=4)
        if cell.value:
            cell.hyperlink = str(cell.value)
            cell.font = Font(name="Calibri", size=10, color="2563EB", underline="single")


def _tab_unverified(wb: Workbook, rows: list[dict[str, Any]]) -> None:
    headers = ["Parcel ID", "Municipality", "County", "ST", "Missing Identifiers",
               "What We Have", "Next Action", "Source Tier"]
    data = [[
        r.get("parcel_id"), r.get("municipality"), r.get("county"), r.get("state"),
        ", ".join(r.get("_missing", [])),
        "; ".join(f"{k}={r[k]}" for k in ("apn", "listing_url", "latitude", "longitude")
                  if r.get(k)),
        r.get("next_action", "Resolve missing identifier before underwriting"),
        r.get("source_tier"),
    ] for r in rows]
    _simple_tab(wb, "Unverified", headers, data, widths={"E": 30, "F": 50, "G": 40},
                note="§5: a parcel missing any of URL / APN / lat-long / municipality lands here, not in the universe.")




# =============================================================================
# Tab: Scenarios  (correlated downside, not one-at-a-time)
# =============================================================================

def _tab_scenarios(wb: Workbook, cfg: dict[str, Any], ask: float | None,
                   premium: float = 0.0) -> None:
    ws = wb.create_sheet("Scenarios")
    ws["A1"] = "SCENARIO MATRIX — CORRELATED STRESS"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws["A2"] = ("A two-axis grid assumes its axes are independent. They are not. These bundles "
                "move dues, ramp, pricing, absorption, cost and cap rate together, because in a "
                "soft cycle they arrive together.")
    ws["A2"].font = NOTE_FONT

    results = sc.run_all(cfg, ask_price=ask, site_cost_premium=premium)
    headers = ["Scenario", "Description", "Required yield + tax", "Binding",
               "Max land — GROSS", "Max land — NET", "Min DSCR (any yr)", "DSCR breach yrs",
               "Peak equity", "Equity multiple", "Equity IRR", "Value / cost",
               "Sell-out (yrs)", "Verdict"]
    _header_row(ws, headers, row=4)

    for i, r in enumerate(results, start=5):
        vals = [r.name.upper(), r.label, r.effective_required_yield, r.binding_constraint,
                r.max_land_gross, r.max_land_net, r.min_dscr_any_year,
                r.covenant_breach_years, r.peak_equity, r.equity_multiple,
                r.equity_irr, r.value_to_cost, r.sellout_years, r.verdict]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=c, value=_safe(v))
            cell.font = BODY_FONT
            cell.border = BORDER
        ws.cell(row=i, column=3).number_format = FMT_PCT
        for col in (5, 6, 9):
            ws.cell(row=i, column=col).number_format = FMT_USD
        for col in (7, 10, 12):
            ws.cell(row=i, column=col).number_format = "0.00x"
        ws.cell(row=i, column=11).number_format = FMT_PCT
        ws.cell(row=i, column=13).number_format = FMT_DEC
        ws.cell(row=i, column=14).fill = GREEN if r.verdict == "CLEARS" else RED

    last = 4 + len(results)
    sp = sc.scenario_spread(results)
    row = last + 2
    ws.cell(row=row, column=1, value="SPREAD ACROSS SCENARIOS").font = SEC_FONT
    for lbl, v, fmt in [
        ("Max land (net) — best case", sp["max_land_net_high"], FMT_USD),
        ("Max land (net) — worst case", sp["max_land_net_low"], FMT_USD),
        ("Swing", sp["swing"], FMT_USD),
        ("Scenarios clearing GROSS", f"{sp['scenarios_clearing_gross']} of {sp['total_scenarios']}", None),
        ("Scenarios clearing NET", f"{sp['scenarios_clearing_net']} of {sp['total_scenarios']}", None),
        ("Scenarios where covenant holds", f"{sp['scenarios_covenant_ok']} of {sp['total_scenarios']}", None),
    ]:
        row += 1
        ws.cell(row=row, column=1, value=lbl).font = BODY_FONT
        c = ws.cell(row=row, column=3, value=_safe(v))
        c.font = Font(name="Calibri", size=10, bold=True)
        if fmt:
            c.number_format = fmt
    row += 2
    ws.cell(row=row, column=1, value=(
        "A land-price swing wider than the deal itself means the assumptions, not the site, "
        "are driving the recommendation.")).font = NOTE_FONT

    _finish(ws, freeze="C5", ncols=len(headers), nrows=last, header_row=4,
            widths={"A": 12, "B": 38, "C": 18, "D": 10, "E": 19, "F": 19, "G": 16,
                    "H": 14, "I": 17, "J": 15, "K": 12, "L": 12, "M": 13, "N": 26})


# =============================================================================
# Tab: Cash Flow & Funding
# =============================================================================

def _tab_cashflow(wb: Workbook, cfg: dict[str, Any], land_price: float) -> None:
    ws = wb.create_sheet("Cash Flow & Funding")
    cf = cf_mod.project_cash_flow(cfg, land_price, horizon_operating_years=12)
    su = cf.sources_uses

    ws["A1"] = "DEVELOPMENT CASH FLOW, PEAK FUNDING AND COVERAGE BY YEAR"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws["A2"] = (f"At a ${land_price:,.0f} land price. Stabilized yield is silent on peak funding "
                f"and on coverage in every year but one — both are shown here.")
    ws["A2"].font = NOTE_FONT

    row = 4
    ws.cell(row=row, column=1, value="SOURCES AND USES").font = SEC_FONT
    row += 1
    for lbl, v in [
        ("Land", su.land), ("Non-land cost (S)", su.non_land_cost), ("Carry", su.carry),
        ("Operating deficit funded", su.operating_deficit_funded),
        ("TOTAL USES", su.total_uses), ("", None),
        ("For-sale net proceeds", su.for_sale_net_proceeds),
        ("Initiation fee cash", su.initiation_cash),
        ("Debt drawn", su.debt), ("  Debt capacity at LTC", su.debt_capacity),
        ("Incentives", su.incentives),
        ("Residual equity", su.equity_required),
        ("TOTAL SOURCES", su.total_sources),
    ]:
        if lbl:
            ws.cell(row=row, column=1, value=lbl).font = (
                Font(name="Calibri", size=10, bold=True) if lbl.isupper() else BODY_FONT)
            c = ws.cell(row=row, column=3, value=_safe(v))
            c.number_format = FMT_USD
            c.border = BORDER
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="FUNDING AND RETURN").font = SEC_FONT
    row += 1
    for lbl, v, fmt in [
        ("PEAK EQUITY REQUIREMENT", cf.peak_equity_requirement, FMT_USD),
        ("  deepest in year", cf.peak_funding_year, FMT_NUM),
        ("Total contributions", cf.total_contributions, FMT_USD),
        ("Total distributions", cf.total_distributions, FMT_USD),
        ("Equity multiple", cf.equity_multiple, "0.00x"),
        ("Equity IRR", cf.equity_irr, FMT_PCT),
        ("Cumulative operating deficit", cf.cumulative_operating_deficit, FMT_USD),
        ("Years with negative NOI", cf.deficit_years, FMT_NUM),
        ("Min DSCR across the hold", cf.min_dscr, "0.00x"),
        ("  in year", cf.min_dscr_year, FMT_NUM),
        ("Exit value", cf.exit_value, FMT_USD),
        ("Exit net proceeds", cf.exit_net_proceeds, FMT_USD),
        ("Value / cost", cf.value_to_cost, "0.00x"),
        ("Profit on cost", cf.profit_on_cost, FMT_USD),
        ("Break-even exit cap (value = cost)", cf.breakeven_exit_cap, FMT_PCT),
    ]:
        ws.cell(row=row, column=1, value=lbl).font = (
            Font(name="Calibri", size=10, bold=True) if lbl.isupper() else BODY_FONT)
        c = ws.cell(row=row, column=3, value=_safe(v))
        c.number_format = fmt
        c.border = BORDER
        row += 1

    row += 2
    hdr = row
    headers = ["Year", "Phase", "Members", "NOI pre-tax", "Property tax", "NOI after tax",
               "Initiation cash", "For-sale cash", "Construction draw", "Land",
               "Debt draw", "Debt service", "Net cash flow", "Cumulative", "DSCR"]
    _header_row(ws, headers, row=hdr)
    for i, pd in enumerate(cf.periods, start=hdr + 1):
        vals = [pd.year, pd.phase, pd.members, pd.noi_pretax, -pd.property_tax if pd.phase == "operating" else 0,
                pd.noi_after_tax, pd.initiation_cash, pd.for_sale_net_cash,
                pd.construction_draw, pd.land_payment, pd.debt_draw, pd.debt_service,
                pd.net_cash_flow, pd.cumulative_cash, pd.dscr]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=c, value=_safe(v))
            cell.font = BODY_FONT
            cell.border = BORDER
        for col in range(4, 15):
            ws.cell(row=i, column=col).number_format = FMT_USD
        ws.cell(row=i, column=15).number_format = "0.00x"

    end = hdr + len(cf.periods)
    ws.conditional_formatting.add(f"O{hdr+1}:O{end}", CellIsRule(
        operator="lessThan", formula=[str(cfg["debt"]["min_dscr"])], fill=RED))
    ws.conditional_formatting.add(f"O{hdr+1}:O{end}", CellIsRule(
        operator="greaterThanOrEqual", formula=[str(cfg["debt"]["min_dscr"])], fill=GREEN))
    ws.conditional_formatting.add(f"N{hdr+1}:N{end}", CellIsRule(
        operator="lessThan", formula=["0"], fill=AMBER))

    _finish(ws, freeze=f"C{hdr+1}", ncols=len(headers), nrows=end, header_row=hdr,
            widths={"A": 7, "B": 14, "C": 9, **{get_column_letter(i): 16 for i in range(4, 16)}})


# =============================================================================
# Tab: Break-Even
# =============================================================================

def _tab_breakeven(wb: Workbook, cfg: dict[str, Any], land_price: float) -> None:
    ws = wb.create_sheet("Break-Even")
    ws["A1"] = "BREAK-EVEN — HOW WRONG CAN THE ASSUMPTIONS BE"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws["A2"] = ("The distance to break-even is the real margin of safety. UNREACHABLE means no "
                "achievable value of that driver alone flips the test.")
    ws["A2"].font = NOTE_FONT

    d = rk.direct_break_evens(cfg, land_price)
    row = 4
    ws.cell(row=row, column=1, value="STATED IN THE UNITS THE PRINCIPAL THINKS IN").font = SEC_FONT
    row += 1
    for lbl, v, fmt in [
        ("Members at stabilization (modeled)", d["members_at_stabilization"], FMT_NUM),
        ("Membership cap", d["membership_cap"], FMT_NUM),
        ("Members needed to cover opex + tax", d["members_to_cover_opex_and_tax"], FMT_NUM),
        ("Members needed to meet the DSCR covenant", d["members_to_meet_covenant"], FMT_NUM),
        ("Annual dues (modeled)", d["dues_base"], FMT_USD),
        ("Annual dues needed to meet the covenant", d["dues_to_meet_covenant"], FMT_USD),
        ("Annual debt service", d["annual_debt_service"], FMT_USD),
        ("Annual property tax", d["annual_property_tax"], FMT_USD),
        ("Fixed cost incl. tax", d["fixed_cost_incl_tax"], FMT_USD),
        ("Contribution per member", d["per_member_contribution"], FMT_USD),
    ]:
        ws.cell(row=row, column=1, value=lbl).font = BODY_FONT
        c = ws.cell(row=row, column=4, value=_safe(v))
        c.number_format, c.border = fmt, BORDER
        c.font = Font(name="Calibri", size=10, bold=True)
        row += 1

    need = d["members_to_meet_covenant"]
    cap = d["membership_cap"]
    if need and need > cap:
        row += 1
        cell = ws.cell(row=row, column=1, value=(
            f"The covenant requires {need:,.0f} members against a cap of {cap:,.0f}. "
            f"It is not reachable at this membership cap on these assumptions — the cap, the "
            f"dues, or the leverage has to move."))
        cell.font = Font(name="Calibri", size=10, bold=True)
        cell.fill = RED
        row += 1

    row += 2
    hdr = row
    headers = ["Test", "Driver", "Break-even value", "Move required from base", "Reachable", "Note"]
    _header_row(ws, headers, row=hdr)
    for i, be in enumerate(rk.break_even_suite(cfg, land_price), start=hdr + 1):
        if be.reachable:
            val = (f"{be.break_even_value:+.0f} bps" if be.driver in rk.RATE_DRIVERS
                   else f"{be.break_even_value:.3f}x base")
            move = (f"{be.headroom_pct:+.0f} bps" if be.driver in rk.RATE_DRIVERS
                    else f"{be.headroom_pct:+.1%}")
        else:
            val, move = "UNREACHABLE", "—"
        vals = [be.metric, be.driver, val, move, "yes" if be.reachable else "NO", be.note]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=c, value=v)
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        if not be.reachable:
            ws.cell(row=i, column=5).fill = RED

    end = hdr + len(rk.break_even_suite(cfg, land_price))
    _finish(ws, freeze=f"A{hdr+1}", ncols=len(headers), nrows=end, header_row=hdr,
            widths={"A": 24, "B": 24, "C": 20, "D": 24, "E": 11, "F": 70})


# =============================================================================
# Tab: Tornado
# =============================================================================

def _tab_tornado(wb: Workbook, cfg: dict[str, Any]) -> None:
    ws = wb.create_sheet("Tornado")
    ws["A1"] = "DRIVER SENSITIVITY — WHERE TO SPEND DILIGENCE DOLLARS"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    swing = cfg["tornado"]["swing_pct"]
    bps = cfg["tornado"]["rate_swing_bps"]
    ws["A2"] = (f"Each driver flexed +/-{swing:.0%} ({bps:.0f} bps for rate drivers), one at a "
                f"time, ranked by how far it moves the maximum supportable land price. "
                f"Univariate by design — Scenarios handles correlated stress.")
    ws["A2"].font = NOTE_FONT

    bars, base, name = rk.tornado(cfg)
    ws["A4"] = f"Base {name} = ${base:,.0f}"
    ws["A4"].font = SEC_FONT

    headers = ["Rank", "Driver", "Low input", "High input", "Value at low", "Value at high",
               "Swing", "Share of total swing"]
    _header_row(ws, headers, row=6)
    total = sum(b.swing_abs for b in bars) or 1.0
    for i, b in enumerate(bars, start=1):
        r = 6 + i
        lo_in = f"{b.low_input:+.0f} bps" if b.driver in rk.RATE_DRIVERS else f"{b.low_input:.2f}x"
        hi_in = f"{b.high_input:+.0f} bps" if b.driver in rk.RATE_DRIVERS else f"{b.high_input:.2f}x"
        vals = [i, b.driver, lo_in, hi_in, b.low_value, b.high_value, b.swing_abs,
                b.swing_abs / total]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=r, column=c, value=_safe(v))
            cell.font = BODY_FONT
            cell.border = BORDER
        for col in (5, 6, 7):
            ws.cell(row=r, column=col).number_format = FMT_USD
        ws.cell(row=r, column=8).number_format = FMT_PCT

    end = 6 + len(bars)
    ws.conditional_formatting.add(f"G7:G{end}", ColorScaleRule(
        start_type="min", start_color="FFFFFF", end_type="max", end_color="FCA5A5"))
    _finish(ws, freeze="A7", ncols=len(headers), nrows=end, header_row=6,
            widths={"A": 6, "B": 24, "C": 14, "D": 14, "E": 18, "F": 18, "G": 18, "H": 20})


# =============================================================================
# Tab: Monte Carlo
# =============================================================================

def _tab_monte_carlo(wb: Workbook, cfg: dict[str, Any], land_price: float) -> None:
    ws = wb.create_sheet("Monte Carlo")
    ws["A1"] = "MONTE CARLO — PROBABILITY THE PROGRAM CLEARS"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    mc = rk.monte_carlo(cfg, land_price)
    ws["A2"] = (f"{mc.iterations:,} joint draws, triangular distributions. Drivers are drawn "
                f"INDEPENDENTLY, which understates the tail because real drivers co-move in "
                f"stress — read this with the Scenarios tab, not instead of it.")
    ws["A2"].font = NOTE_FONT
    ws["A3"] = ("Several driver modes are deliberately adverse to the base case, so the median "
                "draw sits below the base case by construction. This is not an unbiased "
                "estimate of the base case; it is a stress distribution.")
    ws["A3"].font = NOTE_FONT

    row = 5
    for lbl, v, fmt in [
        ("P(clears GROSS basis)", mc.p_feasible_gross, FMT_PCT),
        ("P(clears NET basis)", mc.p_feasible_net, FMT_PCT),
        ("P(DSCR covenant holds every year)", mc.p_covenant_holds, FMT_PCT),
        ("Mean max supportable land (net)", mc.mean, FMT_USD),
        ("Standard deviation", mc.stdev, FMT_USD),
        ("Draws that failed to evaluate", mc.failures, FMT_NUM),
    ]:
        ws.cell(row=row, column=1, value=lbl).font = BODY_FONT
        c = ws.cell(row=row, column=4, value=_safe(v))
        c.number_format, c.border = fmt, BORDER
        c.font = Font(name="Calibri", size=10, bold=True)
        if fmt == FMT_PCT and isinstance(v, float):
            c.fill = GREEN if v >= 0.6 else (AMBER if v >= 0.25 else RED)
        row += 1

    row += 1
    ws.cell(row=row, column=1, value="DISTRIBUTION OF MAX SUPPORTABLE LAND (NET)").font = SEC_FONT
    row += 1
    _header_row(ws, ["Percentile", "Max supportable land — net"], row=row)
    pr = row
    for k in ("p5", "p10", "p25", "p50", "p75", "p90", "p95"):
        row += 1
        ws.cell(row=row, column=1, value=k.upper()).font = BODY_FONT
        c = ws.cell(row=row, column=2, value=_safe(mc.percentiles.get(k)))
        c.number_format, c.border = FMT_USD, BORDER
    _finish(ws, freeze=f"A{pr+1}", ncols=2, nrows=row, header_row=pr,
            widths={"A": 34, "B": 28})


# =============================================================================
# Tab: Plausibility
# =============================================================================

def _tab_plausibility(wb: Workbook, cfg: dict[str, Any], land_price: float) -> None:
    ws = wb.create_sheet("Plausibility")
    ws["A1"] = "INTERNAL CONSISTENCY AUDIT"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True)
    ws["A2"] = ("Changes no number. Catches the failure mode where every input block looks "
                "defensible alone and the combination is impossible.")
    ws["A2"].font = NOTE_FONT

    rep = rk.plausibility_report(cfg, land_price)
    ws["A4"] = rep["verdict"]
    ws["A4"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A4"].fill = GREEN if rep["coherent"] and not rep["warn_count"] else (
        AMBER if rep["coherent"] else RED)

    headers = ["Severity", "Check", "Value", "Plausible band", "Why it matters"]
    _header_row(ws, headers, row=6)
    for i, c in enumerate(rep["checks"], start=7):
        band = f"{c.band[0]:,.4g} to {c.band[1]:,.4g}"
        vals = [c.severity, c.name, c.value, band, c.message]
        for j, v in enumerate(vals, start=1):
            cell = ws.cell(row=i, column=j, value=_safe(v))
            cell.font = BODY_FONT
            cell.border = BORDER
            cell.alignment = Alignment(vertical="top", wrap_text=True)
        sev = ws.cell(row=i, column=1)
        sev.fill = {"OK": GREEN, "WARN": AMBER, "FAIL": RED}[c.severity]

    end = 6 + len(rep["checks"])
    _finish(ws, freeze="A7", ncols=len(headers), nrows=end, header_row=6,
            widths={"A": 10, "B": 28, "C": 14, "D": 20, "E": 85})


# =============================================================================
# Orchestration
# =============================================================================

def enrich(parcels: list[dict[str, Any]], cfg: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    """Screen, underwrite, and score every parcel. Returns (universe, unverified)."""
    universe: list[dict[str, Any]] = []
    unverified: list[dict[str, Any]] = []

    for raw in parcels:
        p = coerce(raw)
        ok, missing = gates.has_required_identifiers(p)
        if not ok:
            p["_missing"] = missing
            unverified.append(p)
            continue

        sr = gates.screen(p, cfg)
        if str(p.get("confidence", "")).strip() == gates.TARGET_PROFILE_CONFIDENCE:
            sr.flags.insert(0, "TARGET-PROFILE — modeled acquisition target, NOT a "
                               "parcel under contract; identifiers pending county GIS")
        p["killed_at_gate"] = sr.killed_at.name if sr.killed_at else ""
        p["rejection_reasons"] = " | ".join(sr.reasons)
        p["flags"] = " | ".join(sr.flags)

        uw = None
        if sr.survived:
            premium = float(p.get("site_cost_premium_usd") or 0.0)
            uw = two_stack.underwrite(cfg, p["parcel_id"], ask_price=p.get("ask_price"),
                                      site_cost_premium=premium)
            p.update({
                "stabilized_noi": uw.stabilized_noi,
                "stabilization_year": uw.stabilization_year,
                "max_land_gross": uw.max_land_gross,
                "max_land_net": uw.max_land_net,
                "yoc_gross_at_ask": uw.yoc_gross_at_ask,
                "yoc_net_at_ask": uw.yoc_net_at_ask,
                "yoc_gross_year5": uw.yoc_gross_year5,
                "yoc_net_year5": uw.yoc_net_year5,
                "dev_spread_gross_bps": uw.dev_spread_gross_bps,
                "required_yield": uw.required_yield,
                "binding_constraint": uw.binding_constraint,
                "dscr_gross_at_ask": uw.dscr_gross_at_ask,
                "dscr_net_at_ask": uw.dscr_net_at_ask,
                "dscr_cleared": uw.dscr_cleared,
                "headroom_to_ask": uw.headroom_gross,
                "price_infeasible": uw.price_infeasible,
                "hurdle_cleared": uw.hurdle_cleared,
            })

        cs = scoring.composite_score(p, cfg, uw, sr)
        p["composite_score"] = cs.total
        p["grade"] = cs.grade
        p["why_wins"], p["what_kills"] = scoring.narrative(cs, p, uw)
        for src, dst in [
            ("entitlement_probability", "score_entitlement"),
            ("yield_on_cost", "score_yield"),
            ("physical_suitability", "score_physical"),
            ("market_catchment", "score_catchment"),
            ("infrastructure_burden", "score_infrastructure"),
            ("deal_control", "score_deal_control"),
            ("optionality", "score_optionality"),
        ]:
            p[dst] = cs.components[src]

        universe.append(p)

    universe.sort(key=lambda x: x.get("composite_score") or 0, reverse=True)
    return universe, unverified


def build(parcels: list[dict[str, Any]], cfg: dict[str, Any],
          sources: list[dict[str, Any]] | None = None,
          out_dir: Path | str = "dist") -> Path:
    universe, unverified = enrich(parcels, cfg)
    survivors = [p for p in universe if not p.get("killed_at_gate")]
    diag = two_stack.feasibility_diagnostic(cfg)

    wb = Workbook()
    wb.remove(wb.active)

    _tab_exec_summary(wb, survivors, cfg, diag)
    _tab_universe(wb, universe)
    _tab_underwriting(wb, survivors, cfg)
    _tab_sensitivity(wb, cfg)
    _tab_noise(wb, universe)
    _tab_physical(wb, universe)
    _tab_comps(wb)
    _tab_land_comps(wb)
    _tab_risk(wb, universe)
    # Analytical depth beyond the eleven §9 tabs: correlated downside, funding
    # and coverage through time, margin of safety, driver attribution,
    # distribution of outcomes, and an internal-consistency audit.
    ref_land = next((p.get("ask_price") for p in survivors if p.get("ask_price")), 0.0) or 0.0
    ref_premium = next((float(p.get("site_cost_premium_usd") or 0.0)
                        for p in survivors if p.get("ask_price")), 0.0)
    _tab_scenarios(wb, cfg, ref_land or None, ref_premium)
    _tab_cashflow(wb, cfg, ref_land)
    _tab_breakeven(wb, cfg, ref_land)
    _tab_tornado(wb, cfg)
    _tab_monte_carlo(wb, cfg, ref_land)
    _tab_plausibility(wb, cfg, ref_land)
    _tab_sources(wb, sources or _default_sources())
    _tab_unverified(wb, unverified)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"Car_Community_Site_Radar_{dt.date.today():%Y-%m-%d}.xlsx"
    wb.save(path)
    return path


SOURCES_CSV = Path(__file__).resolve().parent.parent / "data" / "sources.csv"


def _default_sources() -> list[dict[str, Any]]:
    """
    The citation register is data, not code. If it is missing, emit a single
    row saying so rather than silently shipping an empty Sources tab.
    """
    if SOURCES_CSV.exists():
        with SOURCES_CSV.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    return [{
        "no": 0,
        "name": "MISSING CITATION REGISTER",
        "cited_for": f"{SOURCES_CSV} not found — no claim in this workbook is traceable.",
        "url": "",
        "accessed": f"{dt.date.today():%Y-%m-%d}",
        "tier": "n/a",
        "confidence": "Unverified",
        "note": "Restore data/sources.csv before circulating this workbook.",
    }]


def load_parcels_csv(path: Path | str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the Track Boss site radar workbook.")
    ap.add_argument("--parcels", type=Path, help="CSV of parcels (see data/parcels.csv)")
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=Path("dist"))
    ap.add_argument("--demo", action="store_true", help="build with no parcels (skeleton)")
    args = ap.parse_args()

    cfg = two_stack.load_config(args.config)
    parcels = load_parcels_csv(args.parcels) if args.parcels else []
    if not parcels and not args.demo:
        print("No parcels supplied. Use --parcels data/parcels.csv, or --demo for a skeleton.")

    path = build(parcels, cfg, out_dir=args.out)
    diag = two_stack.feasibility_diagnostic(cfg)
    print(f"Wrote {path}")
    print(f"Parcels in:  {len(parcels)}")
    print(f"Feasibility: {diag['verdict']}")


if __name__ == "__main__":
    main()
