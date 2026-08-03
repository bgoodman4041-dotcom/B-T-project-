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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import formulas
from openpyxl import load_workbook

from build import build_workbook as B
from model import two_stack

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
    out = Path("dist")
    path = B.build(parcels, cfg, out_dir=out)

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
        ("STABILIZED NOI", cell("STABILIZED NOI"), py.stabilized_noi),
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

    # Per-parcel block: max supportable land, computed in Excel, vs Python.
    wb = load_workbook(path)["Underwriting"]
    hdr = None
    for row in range(1, wb.max_row + 1):
        if wb.cell(row=row, column=1).value == "Max supportable land — GROSS":
            hdr = row
            break

    print()
    if hdr is None:
        print("per-parcel block: NOT FOUND  FAIL")
        failed += 1
    else:
        for col in range(4, wb.max_column + 1):
            pid = wb.cell(row=hdr - 3, column=col).value
            if not pid:
                continue
            ask = wb.cell(row=hdr - 1, column=col).value
            per_parcel = [
                (0, "max land GROSS", py.max_land_gross),
                (1, "max land NET", py.max_land_net),
            ]
            if isinstance(ask, (int, float)):
                per_parcel += [
                    (6, "DSCR gross", two_stack.dscr_at(
                        py.stabilized_noi, float(ask), py.cost, py.for_sale, cfg, "gross")),
                    (7, "DSCR net", two_stack.dscr_at(
                        py.stabilized_noi, float(ask), py.cost, py.for_sale, cfg, "net")),
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

    print(f"\n{'PASS — Excel matches Python' if not failed else f'{failed} MISMATCH(ES)'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
