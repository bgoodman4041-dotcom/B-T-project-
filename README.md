# Track Boss

Car community site sourcing agent for **NY / CT / NJ** — private motorsport
country club with an attached for-sale residential and garage-condominium
component. Hurdle: **6.50% yield on cost, stabilized.**

Say **`run track radar`** to execute a full cycle.

---

## Quick start

```bash
pip install pyyaml openpyxl reportlab

python3 tests/test_model.py                                       # 72 tests
python3 tests/test_analytics.py                                   # 56 tests
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

**Stress-tests** it four ways: correlated scenario bundles, break-evens, a
driver tornado, and a Monte Carlo — plus an internal-consistency audit that
catches pro formas which cannot be true.

**Delivers** a 17-tab Excel workbook with live formulas and a one-page IC memo.

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

On those placeholders the program **fails on both bases, and not narrowly**:

```
equity hurdle                     6.50%
DSCR-implied yield                6.77%   <- binds
property tax load (tau)          +1.02%
effective test                    7.79%   <- what the deal must earn

max supportable land — gross:  −$119,320,987
max supportable land — net:     −$13,405,866
peak equity requirement:        $193,432,618  (year 4)
min DSCR across the hold:              −0.61x
value / cost @ 7.25% exit cap:          0.32x
members needed for covenant:      291  (cap is 250)
P(clears), 4,000 MC draws:                 0%
```

Three findings, none about a parcel:

1. **DSCR binds before the hurdle, and property tax binds on top.** An
   ad-valorem tax is equivalent to adding τ to the required yield — the real
   test is 7.79%.
2. **The covenant is unreachable at the configured cap** — 291 members needed
   against 250 available.
3. **The pro forma is not internally coherent.** A 53% for-sale gross margin
   against a 10–35% band was the only reason the net basis looked survivable.

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
python3 tests/test_model.py               # fast — round-trips, DSCR, tax, gates, scoring
python3 tests/test_analytics.py           # fast — cashflow, scenarios, break-evens, MC
python3 tests/test_workbook_formulas.py   # slow — evaluates the real xlsx, 29 checks
```

The analytics suite leans on identities rather than golden numbers: an
ad-valorem tax must equal adding τ to the yield, sources must equal uses, an
amortizing note must retire to zero at term, and a Monte Carlo with every
driver pinned at neutral must reproduce the base case to the cent.

The second one exists because the Excel formulas and the Python model once
disagreed: the sheet derived members at stabilization as `cap × 85%` while
Python used the actual ramp count in that year. Same concept, ~10% different
NOI, and nothing else would have caught it.
