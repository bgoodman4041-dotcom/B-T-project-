# Comparable Club Economics — Verified Set

**Analyst:** Comp Analyst · **As-of:** 2026-08-06 · **Data:** `data/comps_clubs.csv`
**Config tested:** `config/underwriting_inputs.yaml` v2.0 — `income` and `for_sale` blocks

---

## 0. Retrieval caveat — read this before quoting any figure

**Direct URL fetch was blocked environment-wide.** Every `WebFetch` call in this
session returned HTTP 403, on operator sites, trade press, wikis and PDFs alike.
Every figure below was retrieved through the search index instead.

Consequence: **no figure in this set reaches strict `Verified` status** under the
§10 rule ("if a URL will not load, mark the figure UNVERIFIED"). The project has
one prior precedent for this — `sources.csv` row 1 records the same blockage and
uses "Verified — secondary retrieval." I have followed that precedent but graded
harder, splitting into `Operator-Claim (2ndary retrieval)`, `Third-Party (2ndary
retrieval)`, `Inferred`, `Unverified` and `UNRESEARCHED`.

**A single human browsing session would upgrade roughly 70% of this table to
Verified.** That is a cheap, high-value follow-on. Six phone calls would close
most of the rest.

---

## 1. The headline: the hypothesis is refuted, and the truth is worse

**The brief said Thermal's dues were ~$7,200 and that real estate, not dues, is
the engine. That is wrong on the number and right on the structure.**

Thermal's dues are **$3,200/month = $38,400/year**, plus a **$450/month per-lot
ground maintenance fee = $5,400/year**. All-in recurring: **~$43,800/year** —
**29% ABOVE** the model's $34,000 assumption, not 79% below. The $7,200 figure
does not appear in any source I could reach. Thermal's dues were $2,400/month
($28,800/yr) at the 2024 IndyCar test and have risen since.

But the structural point survives in a sharper form, and it is the finding that
should change the model:

> **Every club in the comp set that sustains dues above $34,000 either makes
> real-estate purchase MANDATORY, or is invitation-only in Miami.**
>
> There are exactly two. Thermal ($43,800 all-in) requires you to buy a lot and
> build within five years. The Concours Club ($35,000) is invitation-only inside
> Opa-locka Executive Airport with a 200+ waitlist.
>
> **Every club where real estate is optional prices dues at $18,500 or below.**
> Monticello Gold $18,500 · Apex Platinum $15,000 · Autobahn $6,600 · Spring
> Mountain $6,000 · M1 $3,750 · Lime Rock $3,630 · Club Motorsports $1,500–2,500.
> No exceptions in the set.

The model currently takes Thermal's dues without Thermal's gate. `mandate.hold_structure`
is a merchant build with **140 garage condos + 50 homesites against a 340-member
cap** — 190 units for 340 members. Real estate *cannot* be mandatory at that
ratio. So the model is charging mandatory-purchase dues on an optional-purchase
membership, in the shortest-season, highest-tax region in the country.

### The refundable-deposit problem, which is bigger than the dues question

Two independent accounts state that Thermal's initiation fee **includes a 70%
refundable deposit** returnable on exit. If that structure is normal at this
price point — and $150,000+ initiation fees at golf country clubs are frequently
refundable — then **70% of an initiation fee is a liability, not revenue, and
cannot be amortized into NOI at all.**

The model amortizes the full $150,000 over 12 years: **340 × $150,000 / 12 =
$4.25M/yr of NOI**. Under a 70%-refundable structure only $45,000 per member is
income: **$1.275M/yr**. That is a **−$2.98M/yr** swing, on top of everything in
§3 below, and `income.initiation_treatment` has no switch for it.

**This is the single most consequential unresolved question in the income block.**
§10 says "never capitalize initiation fees into NOI"; it does not say "test
whether the fee is income at all." It should. `RESEARCH TASK: establish
refundability convention at Monticello, Concours and Thermal by direct call.`

---

## 2. Derived figure 1 — the Northeast initiation ceiling is $125,000, and it is one data point

| Northeast club | Initiation | Dues |
|---|---:|---:|
| Monticello Motor Club — Gold | **$125,000** | $18,500 |
| Monticello Motor Club — Silver | $92,500 | $8,600 |
| Monticello Motor Club — Junior | $45,000 | $5,000 |
| Club Motorsports (NH) — Silver | $25,000 | $2,500 |
| Palmer Motorsports Park (MA) | $22,500 | $2,500 |
| Lime Rock Drivers Club (CT) | $16,500 | $3,630 |
| Club Motorsports (NH) — Bronze | $15,000 | $1,500 |
| New Jersey Motorsports Park | **$0** | $20,000 (dues-only) |
| Thompson Speedway (CT) | not published | not published |

**The ceiling is $125,000. The model assumes $150,000 — 20% above it.**

Two risks sit behind that sentence, and they run in opposite directions.

**Risk one: the ceiling is soft data.** The $125,000/$18,500 pair comes from
Grokipedia, an **AI-generated wiki — not a primary source**. Monticello's own
membership page does not publish pricing. The best-sourced Northeast figure is
Robb Report's 2018 Gold tier at **$115,000 / $17,700**, which escalates
consistently to the wiki's $125,000/$18,500 at ~1.0%/yr initiation and ~0.5%/yr
dues. The two agree, which is reassuring, but neither is Verified.

**Risk two: there is no Northeast market, there is one club.** The gap between #1
($125,000) and #2 ($25,000) is **5x**. Monticello is a monopoly datum, not a
distribution. A single operator's rate card is not proof of what the market will
pay — it is proof of what one operator charges when nobody competes.

**What I would underwrite to:** $125,000, flagged as unverified, with the memo
saying plainly that the Northeast initiation ceiling rests on one AI-wiki figure
about one club and that a call to MMC membership is a condition precedent to IC.
`RESEARCH TASK: MMC membership office, (845) 796-2500. Highest-value call in the project.`

---

## 3. Derived figure 2 — the dues-to-initiation ratio, and where the model sits

Recurring-to-upfront across every club-tier where both are published:

| Ratio | Clubs |
|---:|---|
| 8.0% | Spring Mountain |
| 9.3% | Monticello Silver |
| 9.6% | Thermal 2026 (club dues only) · MotorSport Ranch Executive |
| 10.0% | Club Motorsports Bronze · Club Motorsports Silver |
| 11.1% | Monticello Junior · Palmer |
| 11.4% | Apex Gold |
| 13.2% | Autobahn Full |
| 14.8% | Monticello Gold |
| 16.5% | Thermal 2024 |
| 16.7% | Apex Platinum |
| 18.8% | M1 Concourse · Motorsports Gateway Howell |
| 22.0% | Lime Rock Drivers Club |
| 23.3% | Concours Club Standard |
| **22.7%** | **MODEL ($34,000 / $150,000)** |

**Median 11.4% · mean 13.8% · interquartile ~10–17%.**

The model sits at the **94th percentile** of the set. Only Lime Rock (22.0%) and
Concours (23.3%) match or exceed it. Lime Rock is a 1.5-mile club-day product with
a $16,500 initiation — a different business. Concours is Miami.

Two ways to make the pair internally consistent with the comp set:

- Hold initiation at $150,000 → **dues fall to $17,100** at the median ratio.
- Hold dues at $34,000 → **initiation rises to $298,000** — 2.4x the Northeast ceiling.

**Either way the current pair does not exist anywhere in the observed market.**

There is a capital-stack consequence, not just a revenue one. A comp-typical mix
collects *more* upfront and *less* annually. Upfront cash funds the build and
compresses peak equity ($98.1M in year 4). Recurring cash arrives after
stabilisation at month 123. Shifting the mix toward the comp median is not
revenue-neutral to the equity check — it is favourable to it. Worth modelling.

Note also the two clubs that price the trade explicitly. **MotorSport Ranch**
charges $7,800 more initiation for $600/yr of dues relief — a 13-year payback.
**Concours** sells a $350,000 founding membership with **zero** dues in
perpetuity. Both say the market prices upfront-vs-recurring at roughly the
model's 12-year `expected_tenure_years`. That assumption survives.

---

## 4. Derived figure 3 — garage condo $/SF, and the 3x flex spread does not exist

**The model assumes $530/SF sale on $350/SF cost (1.51x).**

### New-build track garage condos — the direct comps

| Club | $/SF | Basis |
|---|---:|---|
| Atlanta Motorsports Park | **$352** | $225,000 / 640 SF — **shell**, buyer finishes |
| Apex Motor Club (AZ) | **$344** | $430,000 / 1,250 SF |
| M1 Concourse (2016 offering) | $210 | $105,000 / 500 SF — stale |
| NJMP (pre-construction, historic) | $125 | $62,500 base — stale |
| Motorsports Gateway Howell (MI) | n/a | from $515,000/unit; **SF not published — no psf derivable** |

### Resale / current market

| Market | $/SF |
|---|---:|
| M1 Concourse trackside suites, current | **$600** |
| Scottsdale premier resale | >$630 |
| Arizona standard inventory | $185–$450 |
| Iron Gate Motor Condos, Naperville IL — **no track**, sold out | $227–$386 |

**Finding A: the two operating new-build track comps price at $344–$352/SF. That
is the model's HARD COST of $350/SF.** Apex and AMP are selling product at
what the model assumes it costs to build. The model's $530/SF is 1.5x both.

**Finding B: the model's average unit is priced above the comp set's top unit at
most clubs.** 1,800 SF × $530 = **$954,000 per unit**. Against: Apex $430,000
base · AMP $225,000 base · Motorsports Gateway $515,000 base · M1 published range
topping out at $650,000 for 3,000 SF. 140 units × $954,000 = **$133.6M of condo
revenue to absorb in one Northeast submarket.**

**Finding C: the 3x spread over industrial flex is not demonstrated in any
matched submarket pair.**

| Matched pair | Condo $/SF | Local industrial/flex $/SF | Multiple |
|---|---:|---:|---:|
| Apex vs Phoenix infill industrial | $344 | $252–$283 | **1.2–1.4x** |
| Apex vs Phoenix bulk distribution | $344 | $122–$147 | 2.3–2.8x |
| **Model vs Suffolk County flex (asking avg)** | **$530** | **$268** | **1.98x** |
| **Model vs Long Island industrial (asking avg)** | **$530** | **$509** | **1.04x** |

The only pair reaching 3x is condo-vs-bulk-distribution, which is not a comp —
a 1.2M SF Dollar Tree box at $122/SF is not the alternative use for a trackside
garage buyer. Against **small-bay infill**, which is the honest comparison, the
spread is **1.2x to 2.0x**.

And the Long Island line is the sharpest contradiction in this document. **On
Long Island, industrial square footage already asks ~$509/SF.** The model is not
pricing a premium product at a premium. It is pricing at the going rate for
industrial space, in the most expensive industrial market in the United States.
There is no spread to harvest at the lead site.

Caveat, stated because it matters: the Suffolk/Long Island figures are
**asking-price averages from listing aggregators**, mixing product types and
sizes. They are `Inferred`, not trades. A CoStar comp set of small-bay Suffolk
County sale trades would sharpen this materially and could move it either way.
`RESEARCH TASK: CoStar or a Suffolk industrial broker — 5,000–20,000 SF sale comps, trailing 24 months.`

**Finding D: the strongest evidence FOR the for-sale thesis is a buyer's return,
not a developer's margin.** M1 went from a $210/SF offering in 2016 to ~$600/SF
today — **~2.9x in ten years**. That is a spectacular hold return for the people
who bought in 2016. It is not a merchant-build margin. The developer captured
$210/SF; the appreciation accrued to the buyers. A merchant build sells at the
offering price, not the tenth-year resale price. Do not let this number migrate
into the sale assumption.

**Homesites: $740,000/unit is defensible in level, unprecedented in the region.**
Thermal's lots run $700,000 (condo sites) to $785,000 (track-front). The model's
$740,000 sits exactly between them. But Thermal's lots carry a **mandatory build**
that guarantees the buyer pool is committed, and Coachella Valley has a
year-round season. More to the point: **no Northeast club has ever delivered a
for-sale trackside homesite.** Monticello's trackside product was announced as
**long-term LEASE**, not sale. Club Motorsports has advertised trackside condos
since 2018 and has not delivered one. The only completed Northeast for-sale
trackside product in the entire set is NJMP's garages.

---

## 5. Derived figure 4 — members per track mile: the band is wrong at the top

**Model: 340 / 4.0 = 85. Plausibility band: [40, 90].**

Only four clubs publish both a member count/cap and a track length:

| Club | Members ÷ miles | = per mile |
|---|---|---:|
| Apex Motor Club | 425 cap ÷ 2.27 | **187** |
| Club Motorsports (NH) | ~300 ÷ 2.5 | **120** |
| The Concours Club | 200 cap ÷ 2.0 | **100** |
| The Thermal Club | 210 ÷ 5.1 | **41** |
| **MODEL** | 340 ÷ 4.0 | **85** |

**The band's ceiling of 90 is contradicted by three of four observations.** It
should widen to roughly **[40, 190]**. As written, `plausibility.members_per_track_mile`
would flag Apex — a profitable operating club — as implausible.

But widening the band is the small point. The large one:

> **Density is inversely priced.** Thermal, at $43,800/yr, runs **41** members per
> mile. Apex, at $8,000–$15,000, runs **187**. Low density *is* the product at the
> top of the market; you are buying an empty track. The model wants Thermal-tier
> dues at roughly twice Thermal's density.

The invariant that actually travels is **dues revenue per track mile**:

| Club | Dues revenue / track mile |
|---|---:|
| The Concours Club | $3.50M |
| **MODEL** | **$2.89M** |
| Apex Motor Club (blended) | $2.15M |
| The Thermal Club (all-in recurring) | $1.80M |
| The Thermal Club (club dues only) | $1.58M |
| Club Motorsports (NH) | $0.30M |

The model is second in the set, behind only invitation-only Miami, and **1.6x
Thermal** — in the Northeast, on a 210-day season. Repriced to the Northeast
ceiling, 340 × $18,500 / 4.0 = **$1.57M/mile**, which lands precisely on Thermal.
That coincidence is not proof, but it is the first configuration in this analysis
where the model stops being an outlier.

---

## 6. Season days — the 210-day Northeast baseline is at the top of its support

**Model: `season.baseline_days: 210`, national range 195–320.**

Published figures, separating **facility days** from **member entitlement days**
because the model conflates them and they are not the same thing:

| Club | Days | Type |
|---|---:|---|
| Apex Motor Club (AZ) | 275 | facility-equivalent (Platinum unlimited) — **operator marketing claim** |
| Autobahn (IL) | ~214 | **derived** from published "April through October" |
| Club Motorsports (NH) | **150** | facility ("open to members 150 days a year") |
| Atlanta Motorsports Park | 140 | **member entitlement**, not facility |
| Lime Rock Drivers Club (CT) | 60 | member entitlement |
| Thompson Speedway (CT) | 30 | member entitlement |
| Monticello — Silver | 15 | member entitlement |

**The only published facility-day figure for a Northeast club is 150.** That is
**29% below** the model's 210. Tamworth NH is materially colder than Long Island,
so 150 is a floor rather than a read-through — but 150 is published and 210 is
not. Chicago's Autobahn at ~214 brackets it from above.

`season_days` drives ancillary revenue *and* `opex_season_factor`, so the error is
partially self-cancelling — but `ancillary_elasticity` is 0.70 and
`opex_elasticity` is 0.28, so a season overstatement is **net revenue-positive**
by construction. **Run 180 days in the sensitivity.**

Arizona's 275 matches the model's AZ figure, which is good — but note it is an
operator marketing claim repeated by trade press, not an audited calendar.

---

## 7. Absorption — 23 units/year is above every realized pace except one

**Model: `garage_condos.absorption_units_per_year: 23` (140 units ≈ 6.1 years);
`homesites: 8/yr` (50 units ≈ 6.25 years).**

| Program | Realized pace |
|---|---|
| Atlanta Motorsports Park | **$8M of condos in two months**; phases 1–3 sold out — fastest in the set |
| M1 Concourse | 80 units then 175+ over ~10 years ≈ **17.5/yr** |
| The Thermal Club | 135 lots over ~10 years ≈ **13.5 lots/yr**; 210 members ≈ 21 members/yr |
| NJMP Exotic Car Garages | **nine phases in ~15 years**; Phases VIII+IX = 14 units total ≈ **10–15/yr** |
| Iron Gate (Naperville, no track) | 185+ units, sold out; period not established |

**23/yr is ~31% above M1's realized rate and 1.5–2.3x NJMP's.** Only AMP supports
it — and AMP's unit is a **$225,000 shell**, less than a quarter of the model's
$954,000 unit. Velocity at $225,000 does not underwrite velocity at $954,000.

**NJMP is the comp that should worry you most.** It is the closest structural
analogue available: a 500+ acre Northeast facility with an operating for-sale
garage program, in a state with the same tax and entitlement environment. It has
delivered its garage stack across **nine phases over fifteen years**, and Phases
VIII and IX together are **fourteen units**. That is what Northeast trackside
for-sale absorption actually looks like.

**Carry consequence.** `carry_years = max(development_years, sellout_years)` and
`follows_absorption: true`. At M1's realized 17.5/yr, 140 units is **8.0 years**
of sell-out against the model's 6.1 — carry period extends **31%**. Per §10, do
not simply scale `k`: `avg_outstanding_pct` of 55% was calibrated to a ~3.5-year
draw and overstates exposure across a long tail. Re-run it properly.

---

## 8. What the comp set contradicts, and by how much

Hand-computed from config values at the 340-member cap. **This is arithmetic on
`underwriting_inputs.yaml`, not a model run** — the model takes NOI at the actual
ramp count in the stabilisation year, which overshoots the cap slightly, so its
own figures will differ modestly. The direction and magnitude hold.

### Base case as configured

| Line | $ |
|---|---:|
| Dues — 340 × $34,000 | 11,560,000 |
| Initiation amortized — 340 × $150,000 / 12 | 4,250,000 |
| Ancillary (five lines) | 6,200,000 |
| **EGI** | **22,010,000** |
| Opex ex-tax (six lines) | 8,946,000 |
| Management fee @ 4.0% EGI | 880,400 |
| Replacement reserve @ 3.4% EGI | 748,340 |
| **Total opex** | **10,574,740** (48.0% of EGI) |
| **NOI before property tax** | **11,435,260** |

### Repriced to the Northeast ceiling (Monticello Gold: $125,000 / $18,500)

| Line | $ |
|---|---:|
| Dues — 340 × $18,500 | 6,290,000 |
| Initiation amortized — 340 × $125,000 / 12 | 3,541,667 |
| Ancillary — unchanged | 6,200,000 |
| **EGI** | **16,031,667** |
| **Total opex** | **10,132,344** (**63.2%** of EGI) |
| **NOI before property tax** | **5,899,323** |

### The delta

**NOI falls $5,535,937 — a 48.4% cut.**

Capitalized at the binding yield: `h` = max(6.50%, 1.30 × 0.30 × 8.674%) = **6.50%**;
`τ` = 0.65 × 0.70 × 2.25% × (1 − 0.50) = **0.512%**; `y` = **7.012%**.

| | Supportable gross basis |
|---|---:|
| As configured | **$163.1M** |
| At the Northeast ceiling | **$84.1M** |
| **Delta** | **−$79.0M** |

**A $79M hole in supportable basis on a project whose lead site is asked at $14.0M
and whose peak equity is $98.1M.** This is not a calibration point. It is the
difference between a financeable deal and one that cannot carry its own vertical.

**And the plausibility audit will not catch it.** The repriced operating ratio is
63.2%, comfortably inside `plausibility.opex_ratio_of_egi: [0.45, 0.80]`. The
audit reports 0 FAIL either way. The guardrails are not guarding this.

### Intermediate case — what I would actually recommend the principal consider

Dues $24,000, initiation $135,000 — above the Northeast ceiling but defensible as
a *new-build premium* against a 2008-vintage incumbent, and inside the comp set's
dues-to-initiation interquartile at 17.8%:

| | $ |
|---|---:|
| EGI | 18,185,000 |
| Total opex | 10,291,690 (56.6% of EGI) |
| **NOI before property tax** | **7,893,310** |
| Supportable gross basis | **$112.6M** |
| **Delta vs base** | **−$50.5M** |

---

## 9. Recommended changes — the principal decides, I do not

`config/underwriting_inputs.yaml` **was not edited.**

| Key | Current | Recommend | Basis | Confidence |
|---|---:|---:|---|---|
| `income.membership.annual_dues_usd` | 34,000 | **18,500–24,000** | Northeast ceiling $18,500 (Monticello Gold); $34,000 exists only where real estate is mandatory or in Miami | High — the whole set agrees |
| `income.membership.initiation_fee_usd` | 150,000 | **125,000–135,000** | Northeast ceiling $125,000; $150,000 is 20% above it | Medium — ceiling is one AI-wiki datum |
| `income.initiation_treatment` | amortized (100%) | **add a `refundable_share` switch** | Thermal reportedly refunds 70% on exit; if that convention holds, initiation NOI falls from $4.25M to $1.275M/yr | Low on the fact, high on the consequence |
| `for_sale.garage_condos.sale_price_psf` | 530 | **400–450** | Operating new-build track comps price at $344–$352/SF | High |
| `for_sale.garage_condos.hard_cost_psf` | 350 | **re-bid** | Equals two competitors' *sale* price — one of the two numbers is wrong | High |
| `for_sale.garage_condos.absorption_units_per_year` | 23 | **15–18** | M1 realized 17.5/yr; NJMP 10–15/yr over nine phases | High |
| `income.season.baseline_days` | 210 | **keep 210, sensitivity at 180** | Only published NE facility figure is 150 (NH); Chicago ~214 | Medium |
| `plausibility.members_per_track_mile` | [40, 90] | **[40, 190]** | Apex operates at 187/mile; band would flag a real club as implausible | High |
| `for_sale.homesites.price_per_unit_usd` | 740,000 | **hold, flag** | Level matches Thermal's $700k–$785k lots — but no Northeast club has ever sold a trackside homesite | Medium |
| `sensitivity.annual_dues_usd` | [16k–28k] | **already right** | The sensitivity grid tops out at $28,000, **below the base case of $34,000**. The grid does not contain the base case. That is a bug. | High |

**Note the last row.** `sensitivity.annual_dues_usd: [16000, 19000, 22000, 25000, 28000]`
against `annual_dues_usd: 34000`. The sensitivity axis does not span the base case
— it tops out 18% below it. Whoever built the grid was working from a lower dues
figure than the one now in the income block, and the grid is closer to the comp
set than the base case is.

---

## 10. What is still open

**Not delivered:** county-level large-acreage land comps. County clerk record
systems are not reachable through a blocked-fetch search index, and MLS-derived
$/acre without a deed reference fails the §10 four-identifier rule. This needs a
records session, not a research agent.

**Phone calls, in priority order:**

1. **Monticello Motor Club membership office** — the current rate card, tier
   structure, member count, cap, and **whether initiation is refundable**. Sets the
   Northeast ceiling. Everything in §8 hangs on it.
2. **NJMP, (856) 327-7248** — Phase VIII/IX garage pricing and realized per-phase
   absorption. The only Northeast for-sale trackside comp that has actually closed units.
3. **Apex Motor Club** — Phase 2 garage pricing (published as rising) and current
   member count against the 425 cap.
4. **Atlanta Motorsports Park, (678) 381-8527** — annual dues (initiation is
   published, dues are not) and Circuit Villas pricing.
5. **Thompson Speedway, (860) 923-2280** — dues amount, never published.
6. **A Suffolk County industrial broker** — 5,000–20,000 SF small-bay *sale trades*,
   trailing 24 months. Kills or confirms §4's Long Island spread finding.

**Records requests:** Will County Recorder (Autobahn condominium plat) and Sullivan
County Clerk (Monticello) for realized garage/homesite trades and absorption.
Cumberland County NJ for the NJMP garage phases.

**Unresearched in the set:** MSR Houston, The Ridge Motorsports Park, The Club at
Mount Meridian (no pricing published), Motorsports Country Club of Cincinnati (may
be a karting facility and not a comp at all).

---

## 11. One number to take away

**The comp set says the model is carrying $5.5M/yr of dues and initiation revenue
that no club outside Miami and Coachella has demonstrated it can collect — and
$79M of supportable basis rests on it.**

The for-sale stack does not rescue it. At $344–$352/SF for operating new-build
track product against a $350/SF assumed cost and a $509/SF Long Island industrial
market, **the for-sale spread that the thesis depends on is the thinnest number
in the file, not the thickest.**
