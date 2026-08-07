# Track Boss — Car Community Site Sourcing Agent

Sources, screens, and underwrites land **nationwide** for a private motorsport
country club with an attached for-sale residential and garage-condominium
component. Reference typology: The Thermal Club. [1]

The mandate began in NY / CT / NJ and went national in v2.1. The Northeast is
still in the pipeline — it has the deepest investable wealth in the country and
one club serving it — but it ranks **23rd of 23** metros on the supply side.

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
| Geography | **Nationwide** (2026-08-05). 23 metros screened; 15 target profiles across 11 markets and 9 states. |

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

### The ten-year horizon and the IPO question

Timing is derived, not asserted: entitlement 33 months + construction 42 months
puts opening at **month 75** and stabilisation at **month 123 — year 10.2**.
Year 10 is when the *first* asset finishes ramping.

`model/roadmap.py::listing_readiness` tests the IPO question with arithmetic
against screening thresholds. Result: **5 stabilised clubs** are needed
($40M recurring NOI, $500M equity value, 4-asset diversification minimum).
Ground-up at a 36-month cadence reaches that in **year 22**; acquiring existing
facilities after club 1 opens reaches it in **year 12**. Neither is year 10.

**Do not let the deck or plan promise a year-10 listing.** The strategy
implication is real: club 1 is the proof, and growth beyond club 2 has to be
acquisitive to reach listing scale inside a fund life.

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

## v2.1 — the nationwide layer

Three things travel with the dirt rather than the program, and each site is
underwritten at its own values via `two_stack.site_config(cfg, parcel)`:

| Site driver | Why it matters |
|---|---|
| `season_days` | 195–320 across the screened set. The single largest geographic difference. |
| `property_tax_effective_rate` | ~0.65% in NV to ~2.6% in CT. |
| `property_tax_abatement_pct` | **The 50% base case is a NY IDA mechanism. It does not travel.** No FL/NV/AZ equivalent reaches this use; the low statutory rate is the offset instead. |

`model/markets.py` scores 23 metros on six drivers (season 26, wealth 22, land
16, friction 16, whitespace 14, incentive 6). Phoenix–Scottsdale leads at 89.2;
New York metro is last at 40.8. 13 of 23 already carry an operating club.

**Season cuts both ways, and the model says so.** `season_factor` lifts
ancillary revenue with days open; `opex_season_factor` lifts crew, consumables
and track prep with it, attenuated by member penetration because a half-full
club open 310 days does not run a full calendar. Lifting only the revenue side
handed every Sun Belt site a margin it had not earned; charging the opex uplift
at full force against a penetration-discounted revenue line erased the advantage
entirely and put a 210-day Northeast site above a 310-day one. Both failures
have tests in `tests/test_markets.py`.

**The lead is a dead heat and the plan says so.** TP-01-EPCAL scores 65.9 to
TP-06-PINAL-303's 65.3 — noise on a 100-point scale. EPCAL wins on catchment and
infrastructure already in the ground; Pinal wins on yield and is the only target
supporting a positive land price on the retained basis. The asymmetry that
matters: Pinal carries a priced cost *premium*, EPCAL a $9.5M cost *credit* that
depends on a Phase II result nobody has ordered. Halve it and EPCAL's IRR falls
to 8.1%.

## v2.2 — what the comparable study found

`research/comps_findings.md` + `data/comps_clubs.csv` (41 rows, 22 clubs). **No
figure reached `Verified`**: direct URL fetch was blocked environment-wide, so
everything came through a search index and carries its own confidence grade.

**The Thermal $7,200 dues figure was wrong.** Thermal is $3,200/mo = $38,400/yr
plus $450/mo ground maintenance — ~$43,800 all-in, 29% *above* the model, not
79% below. The structural point survives in a sharper form:

> Every club in the set sustaining dues above $34,000 either makes real-estate
> purchase **mandatory** (Thermal) or is invitation-only in Miami (Concours).
> Every club where real estate is optional prices dues at **$18,500 or below**.
> This programme sells 190 units against a 340-member cap, so purchase cannot be
> mandatory. **The model takes Thermal's dues without Thermal's gate.**

| Finding | Model | Comp set |
|---|---|---|
| Dues / initiation ratio | 22.7% — **94th percentile** | median 11.4%, max observed 23.3% |
| Northeast initiation ceiling | $150,000 | **$125,000** (Monticello Gold; one AI-wiki datum, 5× gap to #2) |
| Garage condo $/SF | $530 sale on $350 cost | operating new-build track comps sell at **$344–352** — the model's *cost* |
| Long Island industrial | assumed 3× spread | asks **~$509/SF**. No spread at the lead site |
| Absorption | 23 units/yr | M1 realised 17.5; NJMP 10–15 across nine phases in fifteen years |
| Members / track mile | 85, band [40, 90] | Apex runs **187**. The band rejected a real operating club |
| Refundable initiation | not modellable | Thermal reportedly refunds **70%** — $4.25M/yr of NOI becomes $1.28M |

`scenarios.comp_repriced` carries this into every artifact: **−0.1% IRR, 0.88×
DSCR against a 1.30× covenant, 0.58× value to retained cost.** The base case is
unchanged — that is the principal's call — but no artifact leads with the base
case without the comp warning beside it.

**Two defects the study exposed.** `sensitivity.annual_dues_usd` ran $16k–$28k
against a $34k base: the grid did not contain the deal. And the plausibility
audit tested only ratios the pricing pair *produces*, never the pair itself, so
it reported 0 FAIL on a configuration whose revenue was half again too high.
Both now have tests.

## v2.2b — the risk register, and the lead is not settled

`research/risk_register.md` + `data/risk_register.csv` (28 entries, each evidenced
against a named precedent, not a category). The two that move the ranking:

- **RR-02 EPCAL runway PFAS (Severe/High).** The Navy identified 15 new PFAS areas
  of concern at former NWIRP Calverton in 2023, around the western runway, sourced
  to AFFF; at the beginning of CERCLA site evaluation as of early 2025. The
  −$9.5M cost credit's whole basis is reusing that pavement as base course.
- **RR-04 EPCAL contested disposition (High/High).** In litigation since 2024; one
  cause of action survived dismissal in Feb 2026; land described as in limbo.

`scoring.lead_site_fragility()` prices what that means: **EPCAL leads Pinal by 0.6
points and losing $1.36M of the $9.5M credit — 14% — hands the lead to Pinal.**
The credit is not moved to zero; a Phase II has not been ordered and inventing the
answer either way is the same error. The artifacts say the ranking is unsettled
and that both finalists go into Tranche 1.

Other precedents worth knowing: Lime Rock carries a **permanent injunction against
Sunday racing**; Apex's opponents referred its conditional use permit to the
ballot; **7 of 9 pipeline states have no right-to-race nuisance immunity statute**.

## v2.2c — the jurisdiction register

`research/jurisdiction_register.md`, 15 jurisdictions. Same retrieval caveat:
search-index, not primary text. **Nine of fifteen sites carry a blank daytime
dBA** — six because nothing is published, three because the table would not
open. Both stay blank. Both are a phone call, not a number.

**Every researched entitlement path is longer than assumed.** Mean 23.4 → 31.3
months; 14 of 15 revise upward; Litchfield +21, Hendry +18, EPCAL +12. Applied
to `data/sites_targets.csv`. Sites more than 15% over the programme's 33-month
assumption now carry an `ENTITLEMENT-LONG` flag, because the roadmap runs one
period and the sites now span 18–54 months.

**Abatement corrected against the statute actually available.** TX Ch. 312 cut
0.35 → 0.15 (it sunsets 2029-09-01); NC 0.10 → 0.20 (NCGS 105-277.13, declining
five-year); NJ 0.50 → 0.40. **AZ, FL and NV confirmed at zero** — no mechanism
reaches a private recreation use, and a test now enforces that.

**The Connecticut finding inverts its own analysis.** RCSA § 22a-69 sets an
absolute 61 dBA industrial-to-residential daytime limit, which would end a road
course — but § 22a-69-1.8 exempts motorsport during hours the town authorises.
In CT the special-permit hours condition *is* the noise entitlement. More
survivable than an absolute cap, and entirely political.

## Layout

```
config/underwriting_inputs.yaml   Single source of truth. Change assumptions HERE, never inline.
model/two_stack.py                Two-stack model; closed-form max supportable land price
model/gates.py                    Gates 1-5 screening funnel
model/scoring.py                  Composite 100-point ranking (§11 weights)
model/schema.py                   119-column parcel schema; CSV intake coercion
build/build_workbook.py           17-tab xlsx, live formulas on the Underwriting tab
build/build_memo.py               One-page IC memo PDF
build/build_business_plan.py      19-page formal business plan PDF
build/deck/make_deck.js           19-slide investor deck (pptxgenjs)
data/sites_targets.csv            15 nationwide TARGET PROFILES — not parcels under contract
data/parcels.csv                  Intake template (88 intake columns)
data/parcels.example.csv          5 SYNTHETIC fixture rows — never treat as sourced parcels
data/sources.csv                  Citation register. Every claim traces here; assumptions are NOT sourced.
model/cashflow.py                 Timeline, sources/uses, peak funding, DSCR by year, IRR
model/scenarios.py                Base/Downside/Severe/Upside correlated bundles
model/risk.py                     Break-evens, tornado, Monte Carlo, plausibility audit
model/roadmap.py                  10-horizon milestones, platform scale, listing test, exit ladder
model/markets.py                  23 US metros, six-driver composite, rollout Phases A-D
model/demand.py                   HNW pool -> capturable seats; coverage and break-even
data/comps_clubs.csv              41 rows, 22 clubs. NOTHING is Verified — read the grade
research/comps_findings.md        The comparable study. Read before touching income assumptions
research/jurisdiction_register.md Entitlement regime per target jurisdiction
research/risk_register.md         Noise litigation and opposition history
tests/test_model.py               72 tests; fast
tests/test_analytics.py           70 tests; tax, cashflow, scenarios, risk, roadmap
tests/test_markets.py             40 tests; market screen, season, demand, fragility
tests/test_deck_layout.py         pptx geometry: bleed and text collision, with a self-test
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
- **Every artifact runs on the LEAD SITE's config, not the national default.**
  `site_config()` exists so the workbook, plan, memo and deck all describe the
  same site. Running the cash flow at 210 days while the Underwriting tab solves
  a 310-day site is drift, and it will not be caught by any test that compares
  one column against one shared result.
- **A site cost premium is a HARD cost.** It draws soft cost and contingency on
  top of itself. Adding it flat to `S` understates the basis on every premium
  site — the Excel did exactly that until the per-site drift check caught it.
- **The Monte Carlo's modal value MUST equal the base case on every driver.** A
  simulation centred beside the underwriting is two views of the world in one
  config; six adverse modes compounded into a 5% covenant-hold probability
  against a base case covering at 2.02x. Asymmetry belongs in the spread. If a
  pessimistic value is believed, put it in the base case.
- **Test the covenant from conversion everywhere, including in the Monte Carlo.**
  `cf.min_dscr` is the whole-hold minimum and includes lease-up. Used as the
  covenant test it makes every draw fail and reports a structural zero.
- **A sensitivity axis must span its own base case.** The dues axis ran $16k–$28k
  against a $34k base, so every cell described a different club and the base was
  an extrapolation off the end. `test_every_sensitivity_axis_spans_its_own_base_case`.
- **A refundable deposit is a liability, not deferred revenue.** It is cash in and
  cash out and never becomes income, so no share of it amortizes into NOI.
  `initiation_treatment.refundable_share`.
- **Audit the pricing PAIR, not only the ratios it produces.** Every plausibility
  check tested a downstream ratio, so a dues figure at the 94th percentile of the
  observed market passed while the repriced case cut NOI in half at a 63% opex
  ratio comfortably inside its band.
- **When the top two are inside a point, say so and price what would flip it.**
  `scoring.lead_site_fragility()`. A credit can evaporate; a premium can only be
  bid against. Only the credit direction is fragile.
- **A plausibility band that rejects a real operating club is broken, not strict.**
  Apex runs 187 members per track mile against a ceiling of 90.
- **Do not rank on a column that is negative for every candidate.** The mandated
  gross basis is negative for any merchant build regardless of the dirt, so the
  20-point yield component scored zero on all 15 sites and a fifth of the
  composite was inert. Score on the yield SPREAD, which is monotone through the
  point where supportable land crosses zero; dollar headroom is not.

---

## Commands

```bash
# Investor package — all three read from the same model, so they cannot drift
python3 build/build_workbook.py      --parcels data/sites_targets.csv --out dist/
python3 build/build_business_plan.py --parcels data/sites_targets.csv --out dist/
python3 build/build_memo.py          --parcels data/sites_targets.csv --rank 1 --out dist/
python3 build/deck/export_data.py && node build/deck/make_deck.js dist/deck.pptx

python3 tests/test_model.py               # 75 tests, fast
python3 tests/test_analytics.py           # 83 tests, fast
python3 tests/test_markets.py             # 40 tests, fast
python3 tests/test_workbook_formulas.py   # Excel vs Python, slow; writes to a temp dir
python3 tests/test_deck_layout.py         # deck geometry, after any deck change
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
