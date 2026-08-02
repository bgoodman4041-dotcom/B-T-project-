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

from model import gates, scoring, two_stack
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
        f"NY / CT / NJ  ·  {hurdle:.2%} YoC hurdle  ·  ranked on {rank_basis.upper()} basis  ·  "
        f"generated {dt.date.today():%Y-%m-%d}"
    )
    ws["A2"].font = NOTE_FONT

    # Program-level feasibility banner. If the program cannot clear on the
    # ranking basis, that fact outranks any parcel ranking beneath it.
    ws["A4"] = "PROGRAM FEASIBILITY"
    ws["A4"].font = SEC_FONT
    ws["A5"] = diag["verdict"]
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws["A5"].fill = GREEN if diag["program_feasible"] else RED
    ws.merge_cells("A5:J7")
    ws.row_dimensions[5].height = 18

    for i, (label, val, fmt) in enumerate([
        ("Stabilized NOI", diag["stabilized_noi"], FMT_USD),
        ("NOI required at zero land cost", diag["noi_required_at_zero_land"], FMT_USD),
        ("NOI gap", diag["noi_gap"], FMT_USD),
        ("Non-land cost basis", diag["non_land_cost"], FMT_USD),
        ("For-sale net proceeds", diag["for_sale_net_proceeds"], FMT_USD),
        ("Max supportable land (ranking basis)", diag["max_supportable_land"], FMT_USD),
    ], start=9):
        ws.cell(row=i, column=1, value=label).font = BODY_FONT
        c = ws.cell(row=i, column=3, value=val)
        c.number_format = fmt
        c.font = Font(name="Calibri", size=10, bold=True)

    start = 17
    ws.cell(row=start - 1, column=1, value="TOP 10 RANKED").font = SEC_FONT
    headers = [
        "Rank", "Parcel ID", "Municipality", "County", "ST", "Acres", "Prior Use",
        "Best Drive (min)", "Ask", "Max Land — Gross", "Max Land — Net",
        "YoC @ Ask — Gross", "YoC @ Ask — Net", "Headroom", "Composite", "Grade",
        "Why this one wins", "What would kill it", "Link",
    ]
    _header_row(ws, headers, row=start)

    for i, r in enumerate(rows[:10], start=1):
        rr = start + i
        vals = [
            i, r.get("parcel_id"), r.get("municipality"), r.get("county"), r.get("state"),
            r.get("contiguous_developable_acres"), r.get("prior_use"), r.get("best_drive_min"),
            r.get("ask_price"), r.get("max_land_gross"), r.get("max_land_net"),
            r.get("yoc_gross_at_ask"), r.get("yoc_net_at_ask"), r.get("headroom_to_ask"),
            r.get("composite_score"), r.get("grade"),
            r.get("why_wins", ""), r.get("what_kills", ""), r.get("listing_url"),
        ]
        for c, v in enumerate(vals, start=1):
            cell = ws.cell(row=rr, column=c, value=v)
            cell.font = BODY_FONT
            cell.border = BORDER
        for col in (9, 10, 11, 14):
            ws.cell(row=rr, column=col).number_format = FMT_USD
        for col in (12, 13):
            ws.cell(row=rr, column=col).number_format = FMT_PCT
        ws.cell(row=rr, column=15).number_format = FMT_DEC
        if r.get("listing_url"):
            link = ws.cell(row=rr, column=19)
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
    ws.conditional_formatting.add(
        f"O{start + 1}:O{last}",
        ColorScaleRule(start_type="num", start_value=35, start_color="FEE2E2",
                       mid_type="num", mid_value=60, mid_color="FEF3C7",
                       end_type="num", end_value=85, end_color="D1FAE5"),
    )

    _finish(ws, freeze=f"A{start + 1}", ncols=len(headers), nrows=last, header_row=start,
            widths={"A": 6, "B": 14, "C": 20, "D": 14, "E": 5, "F": 9, "G": 20,
                    "H": 12, "I": 14, "J": 18, "K": 18, "L": 15, "M": 15, "N": 14,
                    "O": 11, "P": 22, "Q": 50, "R": 50, "S": 32})


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
            cell = ws.cell(row=i, column=c, value=v)
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
    hurdle_ref = put_input("HURDLE YoC", hurdle, FMT_PCT)

    # --- Per-parcel block ----------------------------------------------------
    r += 2
    _section(ws, r, "PER-PARCEL — LIVE FORMULAS", 3 + len(top))
    hdr = r
    ws.cell(row=hdr, column=1, value="PER-PARCEL — LIVE FORMULAS")
    labels = [
        "Parcel ID", "Municipality", "Ask price",
        "Max supportable land — GROSS", "Max supportable land — NET",
        "Gross cost basis @ ask", "Net cost basis @ ask",
        "YoC @ ask — GROSS", "YoC @ ask — NET",
        "Headroom vs ask (ranking basis)", "Ask ÷ max supportable",
        "PRICE-INFEASIBLE (>20% over)", "Clears hurdle",
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
        # Closed-form inversions, written as Excel:
        #   gross: NOI / (h*(1+k)) - S
        #   net:   (NOI/h + P + G) / (1+k) - S
        f = {
            hdr + 4: f"={noi}/({hurdle_ref}*(1+{k}))-{S}",
            hdr + 5: f"=({noi}/{hurdle_ref}+{fs_net}+{incent})/(1+{k})-{S}",
            hdr + 6: f"=({A}+{S})*(1+{k})",
            hdr + 7: f"=({A}+{S})*(1+{k})-{fs_net}-{incent}",
            hdr + 8: f"=IF({L}{hdr + 6}<=0,\"n/a\",{noi}/{L}{hdr + 6})",
            hdr + 9: f"=IF({L}{hdr + 7}<=0,\"n/a\",{noi}/{L}{hdr + 7})",
        }
        max_ref = f"{L}{hdr + 4}" if rank_basis == "gross" else f"{L}{hdr + 5}"
        yoc_ref = f"{L}{hdr + 8}" if rank_basis == "gross" else f"{L}{hdr + 9}"
        f[hdr + 10] = f"={max_ref}-{A}"
        f[hdr + 11] = f"=IF({max_ref}<=0,\"n/a\",{A}/{max_ref})"
        f[hdr + 12] = f"=IF({max_ref}<=0,\"YES\",IF({A}>{max_ref}*1.2,\"YES\",\"no\"))"
        f[hdr + 13] = f"=IF(ISNUMBER({yoc_ref}),IF({yoc_ref}>={hurdle_ref},\"YES\",\"no\"),\"no\")"

        for row_i, formula in f.items():
            cell = ws.cell(row=row_i, column=col, value=formula)
            cell.border = BORDER
            cell.font = BODY_FONT
            if row_i in (hdr + 8, hdr + 9, hdr + 11):
                cell.number_format = FMT_PCT
            elif row_i in (hdr + 12, hdr + 13):
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.number_format = FMT_USD

    if top:
        end = get_column_letter(3 + len(top))
        yoc_rng = f"D{hdr + 8}:{end}{hdr + 9}"
        ws.conditional_formatting.add(yoc_rng, CellIsRule(
            operator="greaterThanOrEqual", formula=[str(hurdle)], fill=GREEN))
        ws.conditional_formatting.add(yoc_rng, CellIsRule(
            operator="lessThan", formula=[str(hurdle * 0.85)], fill=RED))
        ws.conditional_formatting.add(f"D{hdr + 12}:{end}{hdr + 12}", CellIsRule(
            operator="equal", formula=['"YES"'], fill=RED))
        ws.conditional_formatting.add(f"D{hdr + 13}:{end}{hdr + 13}", CellIsRule(
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
                cell = ws.cell(row=row, column=2 + xi, value=grid["cells"][yi][xi])
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
            cell = ws.cell(row=i, column=c, value=v)
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
    headers = ["No.", "Source Name", "Cited For", "URL", "Accessed", "Tier"]
    data = [[s.get("no"), s.get("name"), s.get("cited_for"), s.get("url"),
             s.get("accessed"), s.get("tier")] for s in sources]
    ws = _simple_tab(wb, "Sources", headers, data,
                     widths={"A": 6, "B": 34, "C": 50, "D": 55, "E": 12, "F": 8},
                     note="§10: every claim in this workbook traces to a numbered row here.")
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
        p["killed_at_gate"] = sr.killed_at.name if sr.killed_at else ""
        p["rejection_reasons"] = " | ".join(sr.reasons)
        p["flags"] = " | ".join(sr.flags)

        uw = None
        if sr.survived:
            uw = two_stack.underwrite(cfg, p["parcel_id"], ask_price=p.get("ask_price"))
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
    _tab_sources(wb, sources or _default_sources())
    _tab_unverified(wb, unverified)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"Car_Community_Site_Radar_{dt.date.today():%Y-%m-%d}.xlsx"
    wb.save(path)
    return path


def _default_sources() -> list[dict[str, Any]]:
    return [{
        "no": 1,
        "name": "The Thermal Club",
        "cited_for": ("Reference program — 426 private acres, over five miles of track, "
                      "homesites/villas/luxury residences, clubhouse with dining, fitness, "
                      "spa, and resort pools."),
        "url": "https://www.thermal.cc/",
        "accessed": f"{dt.date.today():%Y-%m-%d}",
        "tier": "Primary",
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
