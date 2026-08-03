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

## Current state — read this before reporting any number

The income and cost assumptions in `config/underwriting_inputs.yaml` are
**structural placeholders**, not estimates. Every block carrying
`basis: assumed` exists so the model runs end to end. They have not been
researched.

On those placeholders the program is **infeasible on the gross basis**:
stabilized NOI of ~$8.1M against a non-land cost basis of ~$200.9M means NOI
must reach ~$16.7M (2.06×) before *free land* clears the binding test. The
maximum supportable land price is about **−$103.5M** gross, **+$18.5M** net.

**The DSCR covenant binds before the equity hurdle.** 1.30× at 60% LTC on an
assumed 7.25% / 25-year note implies a **6.77%** required yield, not 6.50%.
Every land price is solved at 6.77%. If leverage, coupon, or amortization
move, so does the binding test — check `binding_constraint` before quoting.

That is a program finding, not a parcel finding, and no site in the three-state
search can cure it. **Run `comp-analyst` and re-base the revenue assumptions
before treating any parcel ranking as actionable.**

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
build/build_workbook.py           11-tab xlsx, live formulas on the Underwriting tab
build/build_memo.py               One-page IC memo PDF
data/parcels.csv                  Intake template (88 intake columns)
data/parcels.example.csv          5 SYNTHETIC fixture rows — never treat as sourced parcels
data/sources.csv                  Citation register. Every claim traces here; assumptions are NOT sourced.
tests/test_model.py               70 tests; fast
tests/test_workbook_formulas.py   Excel-vs-Python drift test; slow
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

Two constraints, made commensurable:
    h_equity = the 6.50% hurdle
    h_dscr   = min_DSCR × LTC × mortgage_constant       (DSCR-implied yield)
    h        = max(h_equity, h_dscr)                    (the binding test)

Inverting YoC = NOI / basis = h for the land price L:
    gross:  L* = NOI / (h × (1 + k)) − S
    net:    L* = (NOI / h + P + G) / (1 + k) − S

DSCR = NOI / (LTC × basis × mortgage_constant), reported on both bases.
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
- **Never invent a dBA limit.** An unpublished ordinance is a research task and
  a named phone call, not a number.
- **The four identifiers are non-negotiable.** Live URL, APN, lat/long,
  municipality — or the parcel goes to `Unverified`.
- **No merged cells inside filter ranges.** A filter range overlapping a merge
  yields a workbook Excel refuses to open.

---

## Commands

```bash
python3 build/build_workbook.py --parcels data/parcels.csv --out dist/
python3 build/build_memo.py --parcels data/parcels.csv --rank 1 --out dist/

python3 tests/test_model.py               # 70 tests, fast
python3 tests/test_workbook_formulas.py   # Excel vs Python, slow
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
