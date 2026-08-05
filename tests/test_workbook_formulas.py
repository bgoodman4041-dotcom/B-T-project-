"""
Formula-vs-Python drift test.

The `Underwriting` tab is built from live Excel formulas rather than pasted
values. That is only trustworthy if the formulas compute what model/two_stack.py
computes. This test evaluates the real workbook with an Excel formula engine and
asserts the two agree.

It exists because they once did not: the sheet derived members at stabilization
as `cap x 85%` while Python used the actual ramp count in that year. Same
concept, different number, and nothing else would have caught it.

Slow (spins up a formula graph). Run explicitly:
    python3 tests/test_workbook_formulas.py
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import formulas
from openpyxl import load_workbook

from build import build_workbook as B
from model import two_stack
from model.schema import coerce

TOL = 0.01  # one cent


def _label_map(path: Path) -> dict[str, str]:
    """Map the column-A label of each row to its column-B coordinate."""
    ws = load_workbook(path)["Underwriting"]
    out: dict[str, str] = {}
    for row in range(1, ws.max_row + 1):
        label = ws.cell(row=row, column=1).value
        if isinstance(label, str) and label.strip():
            out[label.strip()] = f"B{row}"
    return out


def _solve(path: Path) -> dict[str, float]:
    xl = formulas.ExcelModel().loads(str(path)).finish()
    sol = xl.calculate()
    vals: dict[str, float] = {}
    for k, v in sol.items():
        m = re.search(r"UNDERWRITING'!([A-Z]+\d+)$", k.upper())
        if not m:
            continue
        try:
            cell = v.value[0, 0]
        except Exception:  # noqa: BLE001 - ranges and non-scalars are not needed
            continue
        if isinstance(cell, (int, float)) and not isinstance(cell, bool):
            vals[m.group(1)] = float(cell)
    return vals


def main() -> int:
    cfg = two_stack.load_config()
    parcels = B.load_parcels_csv("data/parcels.example.csv")
    # NOT dist/. The builder names the file by date, so writing the SYNTH
    # fixture build there silently replaced the real 15-site deliverable with a
    # two-site test artifact that had the same name.
    tmp = tempfile.mkdtemp(prefix="drift-check-")
    path = B.build(parcels, cfg, out_dir=Path(tmp))

    labels = _label_map(path)
    vals = _solve(path)
    py = two_stack.underwrite(cfg, "VERIFY")

    def cell(label: str) -> float | None:
        coord = labels.get(label)
        return vals.get(coord) if coord else None

    checks: list[tuple[str, float | None, float]] = [
        ("Members at stabilization", cell("Members at stabilization"),
         float(two_stack.membership_schedule(cfg, 20)[py.stabilization_year - 1])),
        ("Stabilization year (derived)", cell("Stabilization year (derived)"),
         float(py.stabilization_year)),
        ("STABILIZED NOI (baseline)", cell("STABILIZED NOI (baseline season)"),
         py.stabilized_noi),
        ("NET FOR-SALE PROCEEDS", cell("NET FOR-SALE PROCEEDS"), py.for_sale.net_proceeds),
        ("For-sale vertical cost", cell("For-sale vertical cost"),
         py.for_sale.total_vertical_cost),
        ("TOTAL HARD COST", cell("TOTAL HARD COST"), py.cost.hard),
        ("Soft cost", cell("Soft cost"), py.cost.soft),
        ("Contingency", cell("Contingency"), py.cost.contingency),
        ("NON-LAND SUBTOTAL  (S)", cell("NON-LAND SUBTOTAL  (S)"), py.cost.non_land_subtotal),
        ("CARRY FACTOR  (k)", cell("CARRY FACTOR  (k)"), py.cost.carry_factor),
        ("Mortgage constant", cell("Mortgage constant"),
         two_stack.mortgage_constant(
             cfg["debt"]["permanent_rate"], cfg["debt"]["amortization_years"],
             cfg["debt"].get("periods_per_year", 12))),
        ("DSCR-implied yield", cell("DSCR-implied yield"),
         two_stack.dscr_implied_yield(cfg)),
        ("REQUIRED YIELD (binding)", cell("REQUIRED YIELD (binding)"), py.required_yield),
        ("TAX LOAD (tau)", cell("TAX LOAD (tau)"), two_stack.tax_load(cfg)),
        ("EFFECTIVE TEST (baseline)", cell("EFFECTIVE TEST (required + tau, baseline)"),
         py.required_yield + two_stack.tax_load(cfg)),
    ]

    failed = 0
    print(f"\nWorkbook: {path}\n")
    print(f"{'line item':38} {'excel':>18} {'python':>18}  result")
    print("-" * 88)
    for name, xl_val, py_val in checks:
        if xl_val is None:
            print(f"{name:38} {'NOT FOUND':>18} {py_val:>18,.2f}  FAIL")
            failed += 1
            continue
        ok = abs(xl_val - py_val) <= max(TOL, abs(py_val) * 1e-9)
        print(f"{name:38} {xl_val:>18,.2f} {py_val:>18,.2f}  {'ok' if ok else 'DRIFT'}")
        failed += 0 if ok else 1

    # Per-parcel block. Each column carries its OWN season, ad valorem regime
    # and site cost premium, so each is checked against Python underwritten at
    # that site's config -- not at the national base case. Checking every column
    # against one shared result is precisely how the sheet came to underwrite a
    # nationwide pipeline on a single site's economics without anything failing.
    wb = load_workbook(path)["Underwriting"]
    # Locate rows by their column-A label rather than by arithmetic offsets --
    # inserting a per-parcel line silently shifted every offset by one and the
    # test then compared an ask price against a parcel id.
    rows_by_label = {}
    for row in range(1, wb.max_row + 1):
        v = wb.cell(row=row, column=1).value
        if isinstance(v, str) and v.strip() and v.strip() not in rows_by_label:
            rows_by_label[v.strip()] = row
    hdr = rows_by_label.get("Max supportable land — GROSS")
    pid_row = rows_by_label.get("Parcel ID")
    ask_row = rows_by_label.get("Ask price")

    print()
    if hdr is None or pid_row is None or ask_row is None:
        print("per-parcel block: NOT FOUND  FAIL")
        failed += 1
    else:
        by_id = {str(p.get("parcel_id")): p for p in (coerce(r) for r in parcels)}
        seen_distinct = set()
        for col in range(4, wb.max_column + 1):
            pid = wb.cell(row=pid_row, column=col).value
            if not pid:
                continue
            parcel = by_id.get(str(pid), {})
            scfg = two_stack.site_config(cfg, parcel)
            prem = float(parcel.get("site_cost_premium_usd") or 0.0)
            spy = two_stack.underwrite(scfg, str(pid), ask_price=parcel.get("ask_price"),
                                       site_cost_premium=prem)
            seen_distinct.add(round(spy.stabilized_noi, 2))
            ask = wb.cell(row=ask_row, column=col).value
            per_parcel = [
                (-3, "stabilized NOI", spy.stabilized_noi),
                (-2, "tau", two_stack.tax_load(scfg)),
                (-1, "non-land S", spy.cost.non_land_subtotal),
                (0, "max land GROSS", spy.max_land_gross),
                (1, "max land NET", spy.max_land_net),
            ]
            if isinstance(ask, (int, float)):
                per_parcel += [
                    (4, "property tax", two_stack.property_tax_annual(
                        scfg, spy.cost.gross_basis(float(ask)))),
                    (5, "NOI after tax", two_stack.noi_after_tax(
                        spy.stabilized_noi, scfg, spy.cost.gross_basis(float(ask)))),
                    (8, "DSCR gross", two_stack.dscr_at(
                        spy.stabilized_noi, float(ask), spy.cost, spy.for_sale,
                        scfg, "gross")),
                    (9, "DSCR net", two_stack.dscr_at(
                        spy.stabilized_noi, float(ask), spy.cost, spy.for_sale,
                        scfg, "net")),
                ]
            for offset, label, expected in per_parcel:
                coord = f"{wb.cell(row=hdr + offset, column=col).column_letter}{hdr + offset}"
                got = vals.get(coord)
                if got is None:
                    print(f"{pid} {label:16} NOT FOUND  FAIL")
                    failed += 1
                    continue
                ok = abs(got - expected) <= max(TOL, abs(expected) * 1e-9)
                print(f"{pid} {label:16} {got:>18,.2f} {expected:>18,.2f}  "
                      f"{'ok' if ok else 'DRIFT'}")
                failed += 0 if ok else 1

        # A fixture where every site shares one NOI cannot detect the bug this
        # block exists for. Fail loudly rather than passing vacuously.
        if len(seen_distinct) < 2:
            print("fixture does not vary site economics — drift check is vacuous  FAIL")
            failed += 1

    print(f"\n{'PASS — Excel matches Python' if not failed else f'{failed} MISMATCH(ES)'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
