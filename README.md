# Track Boss

Car community site sourcing agent for **NY / CT / NJ** — private motorsport
country club with an attached for-sale residential and garage-condominium
component. Hurdle: **6.50% yield on cost, stabilized.**

Say **`run track radar`** to execute a full cycle.

---

## Quick start

```bash
pip install pyyaml openpyxl reportlab

python3 tests/test_model.py                                       # 70 tests
python3 build/build_workbook.py --parcels data/parcels.example.csv --out dist/
python3 build/build_memo.py --parcels data/parcels.example.csv --rank 1 --out dist/
```

`data/parcels.example.csv` contains **five synthetic fixture rows** (`SYNTH-*`,
all marked `confidence: Assumed`). They exercise the funnel — two survivors, a
Gate 1 Highlands kill, an undersized kill, and one row missing lat/long that
routes to `Unverified` — and are not sourced parcels. Real intake goes in
`data/parcels.csv`.

---

## What it does

**Sources** land across active listings, off-market and distressed channels,
and county GIS — biased hard toward parcels with an inherited noise floor
(quarries, airfields, capped landfills, existing motorsport, closed golf
courses).

**Screens** through five gates. Gate 1 is hard knockouts — acreage, excluded
jurisdictions, setback, constrained land, slope, legal access. Gate 2 is the
real filter: noise and entitlement viability. Expect 80–90% mortality.

**Underwrites** in two stacks and solves, for every parcel, the *maximum
supportable land price* — the price at which yield on cost lands exactly on
6.50%. That number is the deliverable; the ask is only measured against it.

**Delivers** an 11-tab Excel workbook with live formulas and a one-page IC memo.

---

## The mandate

| | |
|---|---|
| YoC basis | Compute gross **and** net; **rank on gross** |
| Hold structure | Merchant build — condos and homesites both sold |
| Acreage | Hard reject < 250 ac · 250–350 flagged `SUB-SCALE` · 350–700 target |
| Drive time | 120 min ceiling, 90 min prize |
| Minimum DSCR | **1.30×** confirmed — runs alongside the hurdle, tighter one binds |
| Capital stack | **Open** — 60% LTC, 7.25% coupon, 25-yr amortization all assumed |

---

## Read this before quoting a number

The income and cost assumptions in `config/underwriting_inputs.yaml` are
**structural placeholders**, not estimates — every block marked
`basis: assumed` exists so the model runs end to end.

On those placeholders the program **fails before land is priced at all**:
stabilized NOI of ~$8.1M against a ~$200.9M non-land basis needs to reach
~$16.7M (2.06×) for *free land* to clear the binding test.

```
binding test:                     6.77%  (DSCR, not the 6.50% hurdle)
max supportable land — gross:   −$103,455,052
max supportable land — net:     +$18,487,126
```

The **DSCR covenant binds before the equity hurdle**: 1.30× at 60% LTC on an
assumed 7.25% / 25-year note implies a 6.77% required yield. Land prices are
solved at 6.77%, not 6.50%.

That is a program finding, not a parcel finding. Run `comp-analyst` and re-base
the revenue assumptions before treating any ranking as actionable.

```bash
python3 -c "from model.two_stack import load_config, feasibility_diagnostic; \
print(feasibility_diagnostic(load_config())['verdict'])"
```

---

## Agents

`parcel-scout` · `jurisdiction-router` · `site-physician` · `comp-analyst` ·
`underwriter` · `risk-marshal` · `deliverable-smith`

See `.claude/agents/`. Full specification in `docs/SPEC.md`; working rules in
`CLAUDE.md`.

---

## Tests

```bash
python3 tests/test_model.py               # fast — round-trips, DSCR, gates, scoring
python3 tests/test_workbook_formulas.py   # slow — evaluates the real xlsx, Excel vs Python
```

The second one exists because the Excel formulas and the Python model once
disagreed: the sheet derived members at stabilization as `cap × 85%` while
Python used the actual ramp count in that year. Same concept, ~10% different
NOI, and nothing else would have caught it.
