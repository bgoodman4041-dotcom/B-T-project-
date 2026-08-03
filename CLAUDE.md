# Track Boss — Car Community Site Sourcing Agent

Sources, screens, and underwrites land in **NY / CT / NJ** for a private
motorsport country club with an attached for-sale residential and
garage-condominium component. Reference typology: The Thermal Club. [1]

**Hurdle: 6.50% yield on cost, stabilized.**

**Trigger:** `run track radar` → invokes the `track-radar` skill.

---

## Voice

Write like an acquisitions principal, not a broker. Lead with the number, then
the risk, then the path to control. Never pad. Never speculate where you can
verify.

---

## The mandate (confirmed by the principal, 2026-08-02)

| Open item | Resolution |
|---|---|
| YoC basis | Compute **gross and net**; **rank on gross** |
| Hold structure | **Merchant build** — garage condos and homesites both sold |
| Acreage floor | **Hard reject < 250 ac**; 250–350 flagged `SUB-SCALE` with a graduated penalty; 350–700 target band |
| Drive-time ceiling | **120 min** max, 90 min prize |
| Minimum DSCR | **1.30×** (confirmed 2026-08-03). Runs alongside the yield hurdle; the tighter binds. |
| Capital stack | **PARTIAL.** DSCR confirmed; 60% LTC, 7.25% coupon and 25-yr amortization all assumed. Flag in every memo. |

Ranking on the gross basis is the hard test: income NOI must carry the entire
development cost including the for-sale vertical, with no sell-out offset.

---

## Current state — v2.0 institutional base case

`config/underwriting_inputs.yaml` v2.0 replaced the v1.0 structural placeholders
with a calibrated base case that **passes the plausibility audit and clears the
governing tests**. Every figure is still `ASSUMED` unless marked otherwise —
benchmark-derived and internally consistent, NOT verified comps.

**Lead site TP-01-EPCAL, at a $14.0M ask:**

| | |
|---|---|
| Equity IRR / multiple | **8.8% / 2.49×** (12 operating years) |
| Peak equity | **$98.1M** in year 4 |
| Min DSCR from conversion | **2.02×** vs a 1.30× covenant, 0 breaches |
| Value / retained cost | **1.21×** at a 7.25% exit cap |
| Plausibility audit | **0 FAIL**, 1 WARN |
| Scenarios clearing | upside + base; downside and severe fail the covenant |

### Three findings that shaped v2.0

1. **Negative leverage.** The mortgage constant (8.67%) exceeds the retained
   club's yield on cost (~7%), so borrowing destroys equity value. IRR *rises*
   as leverage falls — 11.7% unlevered, 7.5% at 70% LTC. Permanent leverage is
   held at **30%** deliberately.
2. **The PILOT is a condition precedent, not upside.** Without a ~50% abatement
   the covenant breaches and max supportable land goes negative.
3. **Plausible operating costs cap the return.** Configurations showing 13–14%
   IRR all required a club operating ratio near 31% of EGI, far below what
   private clubs run at. They were rejected. At a defensible ~48% ratio the
   honest answer is 8–9%.

### The gross-basis YoC test is retired

The 6.50% gross-basis hurdle still reports **infeasible**, and that is expected:
it charges the retained club with the full cost of garage condos and homesites
that are **sold**. The workbook reports it as a secondary, explained line beneath
the governing verdict. See business plan §13.

```bash
python3 -c "from model.two_stack import load_config, feasibility_diagnostic; \
print(feasibility_diagnostic(load_config())['verdict'])"
```

---

## Layout

```
config/underwriting_inputs.yaml   Single source of truth. Change assumptions HERE, never inline.
model/two_stack.py                Two-stack model; closed-form max supportable land price
model/gates.py                    Gates 1-5 screening funnel
model/scoring.py                  Composite 100-point ranking (§11 weights)
model/schema.py                   119-column parcel schema; CSV intake coercion
build/build_workbook.py           17-tab xlsx, live formulas on the Underwriting tab
build/build_memo.py               One-page IC memo PDF
build/build_business_plan.py      14-page formal business plan PDF
build/deck/make_deck.js           16-slide investor deck (pptxgenjs)
data/sites_targets.csv            5 acquisition TARGET PROFILES — not parcels under contract
data/parcels.csv                  Intake template (88 intake columns)
data/parcels.example.csv          5 SYNTHETIC fixture rows — never treat as sourced parcels
data/sources.csv                  Citation register. Every claim traces here; assumptions are NOT sourced.
model/cashflow.py                 Timeline, sources/uses, peak funding, DSCR by year, IRR
model/scenarios.py                Base/Downside/Severe/Upside correlated bundles
model/risk.py                     Break-evens, tornado, Monte Carlo, plausibility audit
tests/test_model.py               72 tests; fast
tests/test_analytics.py           56 tests; tax, cashflow, scenarios, risk
tests/test_workbook_formulas.py   Excel-vs-Python drift, 29 checks; slow
.claude/agents/                   The seven §8 agents
.claude/skills/track-radar/       The `run track radar` entry point
```

---

## The model in one screen

```
S = hard + soft + entitlement + FF&E + contingency        (all non-land cost)
k = rate × avg_outstanding × carry_years                  (carry factor)
carry_years = max(development_years, sellout_years)       (merchant build)

gross_basis(L) = (L + S) × (1 + k)
net_basis(L)   = gross_basis(L) − for_sale_net_proceeds − incentives

Three constraints, made commensurable as yields:
    h_equity = the 6.50% hurdle
    h_dscr   = min_DSCR × LTC × mortgage_constant       (DSCR-implied yield)
    h        = max(h_equity, h_dscr)                    (the binding test)
    τ        = taxable_share × assessment × rate × (1−abatement)

Property tax is ad valorem, so NOI depends on the basis. That does NOT break
the closed form — because tax is proportional, it is equivalent to adding τ
to the required yield:

    (NOI₀ − τ·B) / B = h    ⟹    B = NOI₀ / (h + τ)

Inverting for the land price L, with y = h + τ:
    gross:  G* = NOI₀ / y                    then  L* = G*/(1+k) − S
    net:    G* = (NOI₀ + h·(P+Γ)) / y        then  L* = G*/(1+k) − S

DSCR = NOI_after_tax / (LTC × basis × mortgage_constant), on both bases.
```

Both exact, no solver. Carry accrues on land too, which is why it multiplies
the sum rather than sitting inside S.

**A negative `L*` is a real answer, not a bug.** It means the income stack
cannot carry the vertical even if the dirt were free.

---

## Rules the code enforces, and you must not quietly relax

- **Never capitalize initiation fees into NOI.** Amortized over expected
  tenure; Sensitivity carries the excluded and capitalized bookends.
- **Stabilization = the first year membership reaches 85% of cap.** NOI is
  taken at the *actual* ramp count in that year, not at `cap × 85%` — the ramp
  overshoots, and using the threshold understates NOI by roughly 10%.
- **Opex does not ramp.** You insure, mow, and maintain the full circuit from
  day one regardless of member count.
- **For-sale vertical cost sits in hard cost.** `net_proceeds` is revenue net
  of *selling cost only* — subtracting vertical cost there double-counts it.
- **Carry follows sell-out.** In a merchant build the capital is outstanding
  until the last unit sells, so `carry_years = max(development, sell-out)`.
  This is also the only channel by which absorption reaches yield — switch
  `follows_absorption` off and the Sensitivity absorption axis goes flat.
  Re-calibrate `avg_outstanding_pct` when sell-out extends the period; 55%
  average exposure across a long tail overstates carry.
- **DSCR is a second hurdle, not a footnote.** `binding_yield()` returns the
  tighter of the equity hurdle and the DSCR-implied yield, and every land price
  is solved at it. `hurdle_cleared` is True only when the yield test *and* the
  covenant both pass — a deal that yields 6.6% but covers at 1.15× is not
  financeable.
- **Never write inf or nan into a worksheet.** Coverage is infinite when there
  is no basis to lever; Excel cannot represent it and the file will not open.
  Everything numeric goes through `_safe()`.
- **Property tax is not a footnote — it is τ added to the required yield.**
  A zero tax line on a $200M NY/CT/NJ asset is simply wrong. The τ identity is
  what keeps the solve closed-form; do not replace it with a flat opex line.
- **Test the covenant in every year, not at stabilization.** Coverage is
  tightest in the first operating year, when opex is full and the ramp is not.
  `cashflow.covenant_report` reports every breach year.
- **Peak funding is not residual equity.** The trough is what must be written
  in checks ($193M here); the residual is what stays in at the end ($6.5M).
  Conflating them understated the check by two orders of magnitude.
- **Debt is a plug, not an additive source.** Sizing it at LTC × basis *and*
  counting sale proceeds separately funds the same dollars twice.
- **Size the permanent loan on the retained asset.** For-sale closings retire
  construction debt, so lending against a gross basis that includes sold
  collateral overstates coverage by ~2.4×. See `permanent_sizing_basis`.
- **Compare against thresholds with tolerance, never `>=` on raw floats.** A
  deal solved to sit exactly on its covenant computes to 1.2999999999999998 and
  an exact comparison called it a breach. Use `_at_least`.
- **Scenarios move drivers together; the tornado moves them one at a time.**
  They answer different questions. Never quote a one-at-a-time flex as downside.
- **Never invent a dBA limit.** An unpublished ordinance is a research task and
  a named phone call, not a number.
- **The four identifiers are non-negotiable.** Live URL, APN, lat/long,
  municipality — or the parcel goes to `Unverified`.
- **No merged cells inside filter ranges.** A filter range overlapping a merge
  yields a workbook Excel refuses to open.

---

## Commands

```bash
# Investor package — all three read from the same model, so they cannot drift
python3 build/build_workbook.py      --parcels data/sites_targets.csv --out dist/
python3 build/build_business_plan.py --parcels data/sites_targets.csv --out dist/
python3 build/build_memo.py          --parcels data/sites_targets.csv --rank 1 --out dist/
python3 build/deck/export_data.py && node build/deck/make_deck.js dist/deck.pptx

python3 tests/test_model.py               # 72 tests, fast
python3 tests/test_analytics.py           # 56 tests, fast
python3 tests/test_workbook_formulas.py   # Excel vs Python, 29 checks, slow
```

Run `test_model.py` after any change to the math — the round-trip identity
tests catch inversion errors that eyeballing will not. Run
`test_workbook_formulas.py` after any change to the Underwriting tab; it
evaluates the real workbook and asserts the live Excel formulas still agree
with Python to the cent. It exists because they once did not.

---

## Dependencies

`pyyaml` · `openpyxl` · `reportlab` · `formulas` (test only)

---

## Endnotes

**[1] The Thermal Club** — *Cited for: reference program — 426 private acres,
over five miles of track, homesites/villas/luxury residences, clubhouse with
dining, fitness, spa, and resort pools.* https://www.thermal.cc/
