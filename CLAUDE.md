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
> Where real estate is OPTIONAL, the highest dues outside that Miami club is
> **$20,000** — NJMP, which charges *no initiation fee at all* — and the highest
> optional-purchase club that also charges a six-figure initiation is Monticello
> Gold at **$18,500** against our $150,000/$34,000. This programme sells 190
> units against a 340-member cap, so purchase cannot be mandatory.
> **The model takes Thermal's dues without Thermal's gate.**

The first draft of that claim said "$18,500 or below, no exceptions." It had two:
Concours at $35,000 (carved out as invitation-only) and **NJMP at $20,000, which
no carve-out covered**. `test_the_optional_real_estate_dues_claim_matches_the_data`
now pins the sentence to the register.

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

`scoring.lead_site_fragility()` asks TWO questions, because they have different
answers. Does the composite change hands? No — write the $9.5M credit to zero and
EPCAL still leads Pinal by 2.5 points. Does the runner-up out-EARN it? **Yes: at
zero credit EPCAL returns 7.4% against Pinal's 9.2%, 180 bp worse.**

That gap is the finding. The composite spends 20 of its 100 points on yield, so a
$9.5M swing worth 145 bp of IRR moves the ranking by two points and changes
nothing. Rank on the composite if you like; fund the one that earns more. The
credit is not moved to zero in the base case — a Phase II has not been ordered and
inventing the answer either way is the same error — and both finalists go into
Tranche 1.

Other precedents worth knowing: Lime Rock carries a **permanent injunction against
Sunday racing**; Apex's opponents referred its conditional use permit to the
ballot; **7 of 9 pipeline states have no right-to-race nuisance immunity statute**.

## v2.2c — the jurisdiction register

`research/jurisdiction_register.md`, 15 jurisdictions. Same retrieval caveat:
search-index, not primary text. **Nine of fifteen sites carry a blank daytime dBA** — seven because nothing is
published, two because the ordinance exists and its table would not open. Both
stay blank and both name the office to call. The six that ARE published are now
recorded with their citation and measurement point: Riverhead 65, CT 61 (both
sites), NJAC 7:29 65, Marion 65, Cabarrus 65. §10 cuts both ways — never invent
one, and do not leave a cited one blank either, because that applies an
unverified-ordinance discount to a site whose regime is on the record.

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
survivable than an absolute cap, and entirely political — so `noise_exemption`
carries it and `score_entitlement` applies ×0.88 rather than the ×0.75
tight-ordinance penalty a bare 61 would trigger.

`data/jurisdictions.csv` (15 rows, 18 columns) is the machine-readable register
and drives the **Jurisdictions** tab.

## v2.3 — mis-priced, or mis-specified?

The comp study says the revenue line is half again too high. The obvious reading
is that the deal is dead; that reading skips a step. `model/respec.py` holds the
comp-supported PRICING fixed and searches the PROGRAMME.

| At comp pricing | As configured | Re-specified |
|---|---|---|
| Cap / miles / condos | 340 / 4.0 / 140 | **510 / 2.25 / 110** |
| Equity IRR | −0.1% | **13.5%** |
| Min DSCR | 0.88× | **2.29×** |
| Value / retained cost | 0.58× | **1.28×** |

Three things the search settles, two of them counterintuitive:

- **Track length is not the lever.** The circuit is 7% of non-land cost; 2.25→4.0
  miles is worth ~107 bp of IRR. A shorter course is a smaller parcel and a
  cheaper entitlement — real, but not the answer.
- **More for-sale product makes it WORSE** — ~776 bp, moving the wrong way.
- **Member count is the lever, and `demand.py` bounds it, not design.**

**The defect that hid this.** `for_sale.gross_margin_pct` reported 35.5% against
a fully-loaded 17.9%: it ignored the 1.298× soft-cost-and-contingency load the
model itself applies to the same vertical dollars. So the plausibility band
warned the margin was too HIGH on a figure that is fine once loaded, while the
real exposure went unreported. A garage condo costs **$454/SF** to deliver, not
$350. At $530 that is +$84k a unit; at the $344–352 operating comps achieve it is
**−$226k a unit**, and in a merchant build the carry runs until the last one
sells. `loaded_margin_pct`, `loaded_cost_psf` and `condo_margin_per_unit` are now
reported and audited.

## v2.4 — IC readiness

`tests/test_ic_ready.py` asks the questions a committee chair asks, and fails on
things that are true but badly presented. Three defects it caught:

- **The memo's recommendation ran on the RETIRED gross-basis hurdle.** The single
  most important sentence in the IC document read DO NOT PROCEED, on a test the
  workbook already reports as secondary and §13 recommends retiring, while equity
  IRR, covenant coverage and value-to-retained-cost all said otherwise. It now
  runs on the governing tests and carries the gross line labelled beneath.
- **The plan never REPORTED the gross-basis verdict where the numbers are read.**
  Recommending its retirement in §13 is not the same as showing the committee the
  figure and saying what it is. §1 now does both and asks for a ruling.
- **A wipe-out and a covenant miss read identically.** Downside and severe both
  said "COVENANT FAILS" while one returns a fortieth of capital and the other
  returns none. Verdicts now separate, and any row without an IRR states how much
  capital comes back.

**An undefined IRR is never 0%.** `severe` contributes $455M and distributes
nothing, so no rate exists; `downside` returns a fortieth and then bleeds, so its
NPV is negative at every discount rate and no rate exists there either. Both print
`n/a`, never zero, and the verdict carries the multiple so the row is never bare.

**The package supports a TRANCHE 1 decision only** — $4.70M of feasibility capital
against options and studies. It does not support a construction commitment,
because the revenue assumptions the whole model rests on are unverified and the
comparable set contradicts them. Every artifact says so in the same voice.

## v2.5 — the diligence register: what is unverified, and what the answer is worth

Four registers each carried their own task list — ~48 open items with no
consolidated view and no sense of which mattered. `model/diligence.py` holds 20
numbered items and prices each one by flexing the model across the honest span
between what the evidence suggests and what the config assumes, then re-running
the governing tests at both ends.

**Downside is not range width, and conflating them flatters the wrong item.**
Hard cost is flexed −8%/+15% because nothing is bid, so most of its 561 bp range
sits *above* the base case; the dues assumption has no favourable end at all
because the model already sits at the top of it. Ranking on width put an unbid
cost block next to the one input the comparable set contradicts. The register
reports `downside_bps` — distance below the base case at the adverse end — and
ranks on that. `irr_swing_bps` is still reported, and a test pins them apart.

| Rank | Item | Cost | Downside | DSCR adv. |
|---|---|---|---|---|
| 1 | DD-01 dues $34,000 → $18,500 | $285k | **947 bp** | **0.78×** |
| 2 | DD-10 cap 340 → 272 achieved | $240k | 525 bp | **1.28×** |
| 3 | DD-08 hard cost unbid | $0 | 345 bp | 1.50× |
| 4 | DD-02 initiation 70% refundable | $0 | 314 bp | 1.38× |
| 5 | DD-05 absorption 23 → 15/yr | $0 | 297 bp | 1.57× |

**The finding that should change behaviour this month is free.** Eight of the
twenty items cost nothing — membership-office calls, county records requests,
nine municipal clerks who will read a noise table down a phone line — and
together they carry **1,448 bp of downside**, more than any funded study except
the comparable set. They are not in Tranche 1 because they do not cost anything.
They should still be done first, and every artifact now says so.

**The site cost premium had to become a flexed input.** The most-argued number in
the programme is EPCAL's −$9.5M pavement credit, and it is an argument to
`project_cash_flow`, not a config key. A flexer that could only reach the config
would have left it unpriced, so every flexer takes and returns the premium.
Writing the credit to zero costs **141 bp** — which reproduces the 7.4% already
quoted in v2.2b from a different direction. A credit can evaporate and a premium
can only be bid against, so on a site that already carries a *charge* the item
carries no flex rather than an invented multiplier.

**Reconciliation found a hole in the ask.** `reconcile()` checks both directions:
no item may spend money the ask does not contain, and no line of the ask may go
unclaimed by a numbered question. The risk register carried the lead site's
disposition as High/High — in litigation since 2024 — while Tranche 1 had no
title line at all. Added at $100k; the ask goes $4.59M → **$4.70M**. One line is
declared `NOT_A_QUESTION` (programme management) rather than absorbed into a
rounding note.

**Two transcribed figures were wrong.** The plan and deck both claimed the
comparable study and the acoustic model "land in months 3 and 7 — both before the
option payments are at real risk", against options in month **6**. The acoustic
model moved to month 5 and all three artifacts now derive the months. The deck
also closed on a hard-coded "129 unit tests" against a register that has since grown;
it counts them at export time now.

## v2.6 — margin of safety, and the test that actually binds

Pricing an item tells you what is at stake in the answer. It does not tell you
how much of the wrong answer the deal absorbs, and it cannot say what happens
when two of them land together. Every range in the register is now a `Span` in
its own natural units — dollars of dues, days of season, members of cap — with
`t=0` favourable and `t=1` adverse, which makes both questions answerable by
bisection instead of assertion.

**The covenant is not the binding test, and the whole package said it was.**
The 1.30× DSCR floor is the principal's confirmed number, so it is quoted in
every section of every artifact and the risk reads as a coverage story. Walk any
driver from the base case toward its adverse end and **value against retained
cost fails first — on all 6 items that bind at all, unanimously.** On 4 of those
6 the covenant never breaks *anywhere* in the range.

| | Exit test binds | Covenant holds to |
|---|---|---|
| DD-01 dues $34,000 | **$28,914** (33% of range) | $24,999 (58%) |
| DD-10 cap 340 | **300 members** (60%) | 272 (99%) |
| DD-04 condo $530/SF | **$404/SF** (69%) | never |
| DD-08 hard cost | **+10%** (77%) | never |
| DD-02 refundable | **56%** (80%) | never |
| DD-05 absorption 23/yr | **16/yr** (83%) | never |

That is a direct consequence of the deliberate 30% permanent leverage: an asset
that borrows little is hard to break on coverage and is exposed instead on what
it is worth when it is sold. Both statements are true — the covenant does break
at the far end of the dues range — but only one describes the constraint the
deal operates against day to day. 8 of the 14 priced items absorb their entire
range and still clear every governing test at the far end.

**The deal survives ZERO adverse answers.** `survival()` compounds them
largest-first. DD-01 alone takes coverage from 2.02× to 0.78×. This is a joint
tail and not an expectation — every rung is an adverse end by construction, the
same distinction the project already enforces between a correlated scenario and
a one-at-a-time tornado flex — but the base case's headroom absorbs none of it.
That zero is the arithmetic behind the Tranche-1-only recommendation, and
`test_ic_ready` now fails if the register says zero while the plan asks for
construction equity.

**Never add the downside column up.** Each item is measured from the same base
case, so summing them double-counts every interaction — and it is the obvious
thing for a reader to do with the column. The top five sum to **2,426 bp**;
compounded they produce **no computable return at all and 0.00× of capital
back**. A test pins the non-additivity, and every artifact carrying the column
carries the warning.

**Two presentation defects the continuous spans exposed.** Rows that absorb
their whole range were reporting a break value — `breaks at 0% abated` on an
item that never breaks, a false negative dressed as a number. And the walk
table left the IRR cell blank where no rate exists, which reads as missing data
rather than as the wipe-out it is; it prints `n/a` now, per the standing rule.

## Layout

```
config/underwriting_inputs.yaml   Single source of truth. Change assumptions HERE, never inline.
model/two_stack.py                Two-stack model; closed-form max supportable land price
model/gates.py                    Gates 1-5 screening funnel
model/scoring.py                  Composite 100-point ranking (§11 weights)
model/schema.py                   119-column parcel schema; CSV intake coercion
build/build_workbook.py           22-tab xlsx, live formulas on the Underwriting tab
build/build_memo.py               One-page IC memo PDF
build/build_business_plan.py      35-page formal business plan PDF
build/deck/make_deck.js           29-slide investor deck (pptxgenjs)
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
model/respec.py                   Holds comp pricing fixed, searches the programme
model/diligence.py                Open items priced, their tolerance, and the joint tail
data/comps_clubs.csv              41 rows, 22 clubs. NOTHING is Verified — read the grade
research/comps_findings.md        The comparable study. Read before touching income assumptions
research/jurisdiction_register.md Entitlement regime per target jurisdiction
data/jurisdictions.csv            15 jurisdictions; noise, abatement, timeline, who to call
research/risk_register.md         Noise litigation and opposition history
tests/test_model.py               78 tests; the closed-form identities
tests/test_analytics.py           92 tests; tax, cashflow, scenarios, risk, roadmap
tests/test_markets.py             47 tests; market screen, season, demand, fragility
tests/test_data_integrity.py      23 tests; every data file against every other
tests/test_ic_ready.py            23 checks; is the package fit for a committee
tests/test_diligence.py           35 tests; the register, its spans, tolerance and survival
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
- **Never invent a dBA limit** — and never leave a cited one blank. An
  unpublished ordinance is a research task and a named phone call. A published
  one belongs on the row with its citation and measurement point; omitting it
  applies an unverified-ordinance discount to a regime that is on the record.
- **A statutory exemption displaces the numeric limit.** CT RCSA § 22a-69-1.8
  exempts motorsport during town-authorised hours, so scoring a bare 61 dBA
  penalises a constraint that does not apply. `noise_exemption`.
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
- **Report the FULLY LOADED for-sale margin.** Vertical cost sits in hard cost and
  draws soft cost and contingency, so a unit costs `hard × (1+soft) × (1+cont)` to
  deliver. The raw margin ran roughly double and made the audit flag the wrong
  direction.
- **Test whether the marginal unit is profitable, not just the blended margin.**
  At comp pricing the garage condos lose money on every sale, which is why the
  re-specification search wants fewer of them.
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
- **Ask whether the RANKING flips and whether the ECONOMICS flip. They differ.**
  `scoring.lead_site_fragility()`. Yield is 20 of 100 points, so a swing worth
  145 bp of IRR can move the composite two points and change nothing. Reporting
  only "the ranking holds" would be true and misleading. A credit can evaporate;
  a premium can only be bid against, so only the credit direction is fragile.
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

python3 tests/test_model.py               # 78 tests, fast
python3 tests/test_analytics.py           # 92 tests, fast
python3 tests/test_markets.py             # 47 tests, fast
python3 tests/test_data_integrity.py      # 23 tests, fast — run after ANY data edit
python3 tests/test_ic_ready.py            # 23 checks — run before any IC submission
python3 tests/test_diligence.py           # 35 tests, fast — the diligence register
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
