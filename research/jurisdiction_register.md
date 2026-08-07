# Jurisdiction Register — Track Boss nationwide target set

**Compiled** 2026-08-06 · **Scope** 15 target profiles, 9 states
**Companion machine-readable file** `data/jurisdictions.csv`
**Citations** numbered `[n]` against `data/sources.csv` entries 4–70

---

## Retrieval limitation — read this before you rely on any number

WebFetch was blocked at the proxy for every host in this environment (HTTP 403 on
municode, eLaws, Justia, statutes.capitol.texas.gov, dep.nj.gov, and Wikipedia
alike). Every finding below therefore rests on **search-index retrieval of the
primary page**, not on direct reading of the primary page. That is the same
posture `data/sources.csv` entry 1 already documents for the Thermal Club.

Consequence for the discipline that matters: **nine of fifteen jurisdictions carry
a blank daytime dBA figure.** Six of those nine are blank because no limit is
published; three are blank because the limit is published in a table I could not
open. Both are marked, and both are a phone call, not a number.

Confidence grades used throughout: `Verified` (primary text quoted in retrieval),
`Inferred` (secondary or summarised retrieval of a named primary section),
`Assumed` (reasoned, unsourced).

---

# PART I — THE TWO CLAIMS THE MODEL RESTS ON

## Claim 1 — "Texas counties have no zoning authority, so an unincorporated Hood / Waller / Caldwell site is as-of-right."

**Verdict: half right, and the wrong half is the lead Texas site.**

### The general rule holds

Texas counties have no general zoning power. Chapter 231 of the Local Government
Code confers zoning authority only on named counties in named areas the
Legislature has singled out. Outside those grants, county regulatory authority in
the unincorporated area is confined to subdivision platting (LGC Ch. 232),
building codes in limited circumstances (Ch. 233), on-site sewage, floodplain,
and public nuisance abatement (H&S Code Ch. 343). [4][7]

### Hood County is one of the named exceptions — the claim is REFUTED for TP-07

**LGC Ch. 231, Subchapter K — "Development Regulations in Hood County"**,
§§ 231.221–231.234. [4][5] The Legislature found that all of Hood County drains
to Lake Granbury and the Brazos River and that development without regulation
endangers the area's use for recreation, and granted the Hood County
Commissioners Court authority to regulate lot coverage, water and wastewater
facilities, drainage facilities, and recreational areas. The subchapter
establishes:

| Section | Effect |
|---|---|
| § 231.221 | Legislative findings; purpose (Lake Granbury / Brazos watershed) |
| § 231.222 | Areas subject to regulation |
| § 231.223 | Development regulations generally |
| § 231.225 | **Districts** |
| § 231.228 | **Special exception** |
| — | **Hood County Development Commission** (a standing board, seated) |

Hood County operates a Development Department administering Development,
Subdivision and Floodplain Regulations, and seats a Hood County Development
Commission. [6] That is a discretionary land-use body with a special-exception
docket. **TP-07 is not as-of-right.** The correct posture is `special_permit`
(statutory special exception), and 12 months is not a credible entitlement
period.

**Verify before IC:** § 231.222 defines the *geographic* reach of Subchapter K.
If it is limited to a corridor around Lake Granbury rather than the whole county,
a Cresson / SH-144 parcel in the far north of the county may sit outside it. This
is the single highest-value open question in the Texas set. Call the **Hood County
Development Department, (817) 408-2515.**

### Waller (TP-09) and Caldwell (TP-13) are genuinely unzoned — and still not frictionless

No Chapter 231 subchapter reaches either county. [4] But "no zoning" is not "no
discretion." The hooks that exist anyway:

1. **Plat approval, LGC Ch. 232, by the Commissioners Court.** A merchant build
   selling homesites *and* garage condominiums must plat. Waller County's adopted
   regulations require the application to be filed with Commissioners Court, a
   **public hearing date set, and notice published by the County Engineer**, with
   construction plans for streets, drainage, signage, landscaping, irrigation and
   utilities approved by the County Engineer before final plat. [16] Plat approval
   is nominally ministerial; a noticed public hearing in front of an elected court
   is not politically ministerial.
2. **TxDOT access permit, 43 TAC §§ 11.50–11.58.** Any connection to a state
   highway (SH-144, US-290, SH-130 frontage) requires a Permit to Construct Access
   Driveway Facilities on Highway ROW, with terms prescribed by the district
   engineer. [12] TxDOT can, and for an event venue will, require deceleration
   lanes, turn lanes or signalisation as a condition. This is the real cost hook.
3. **TCEQ Construction General Permit TXR150000** (TPDES) plus SWPPP for the
   disturbance. [11]
4. **On-site sewage facility permit, 30 TAC Ch. 285**, issued by the county as
   TCEQ's authorised agent. TP-09's perc rate of 45 min/in and TP-13's 40 min/in
   are at the punishing end for conventional OSSF.
5. **Mass gathering permit, H&S Code Ch. 751.** Any event outside a municipality
   expected to draw **more than 2,500 people** requires a permit from the **County
   Judge**, applied for at least 45 days ahead, **with a public hearing no later
   than 10 days before the event**, and inspection rights for the county health
   authority, sheriff and fire marshal. [10] For a club running spectator
   weekends this is a **recurring annual political hook with a public hearing
   attached** — the closest thing Texas has to an ongoing conditional use permit.
6. **Common-law nuisance.** No zoning also means no zoning defence. Texas
   nuisance actions support permanent injunctive relief, and injunction is the
   remedy neighbours seek against a racetrack.
7. **USACE Section 404** for TP-09's ditch network — an individual permit is a
   12–24 month path on its own and is the schedule driver, not the plat.
8. **Groundwater conservation district** permitting for non-exempt wells.
   Confirm the district of record for each parcel.

### Caldwell County and the Edwards Aquifer — the model's stated path is wrong

`sites_targets.csv` gives TP-13 a permitting path including "Edwards Aquifer
contributing-zone plan if the boundary is crossed." **TCEQ's Edwards Aquifer
Protection Program under 30 TAC Ch. 213 reaches Kinney, Uvalde, Medina, Bexar,
Comal, Hays, Travis and Williamson counties. Caldwell County is not on the
list.** [13] Delete the line. It overstates the friction and misdirects the
diligence budget away from the Blackland vertisol geotech, which is the actual
problem at TP-13.

### Texas noise — the honest position

**Texas counties have no authority to enact a noise ordinance.** [9] There is
therefore no county dBA standard to cite in Hood, Waller or Caldwell. The only
statewide provision is **Texas Penal Code § 42.01(c)(2)**: noise is *presumed*
unreasonable if it exceeds **85 dB after the person making it has received notice
from a magistrate or peace officer that the noise is a public nuisance.** [8]

Read that carefully before anyone puts it in a memo as a limit. It is (a) a
criminal disorderly-conduct presumption, not a land-use performance standard;
(b) conditional on a prior warning; (c) specifies no measurement point, no
descriptor, and no time-of-day split. It is not a design criterion and it will
not protect the project from a nuisance injunction. **The Texas noise position is
"no applicable ordinance standard, unlimited private nuisance exposure"** — which
is worse than a published cap, not better.

---

## Claim 2 — "The 50% abatement is a New York IDA mechanism with no FL / NV / AZ equivalent reaching this use."

**Verdict: correct on FL, NV and AZ. Incomplete elsewhere — CT, TN and NC all have
statutes that do reach this use, and two of the three are mis-sized in the model.**

| State | Mechanism | Reaches a private motorsport club? | Model | Researched |
|---|---|---|---|---|
| **NY** | GML Art. 18-A IDA PILOT | Yes — **but see the § 862 caveat below** | 50% | 50%, flagged |
| **CT** | **CGS § 12-65b** | **Yes — "(9) recreation facilities" is a named eligible use** [37] | 35% / 25% | 35% / 25%, sound |
| **NJ** | N.J.S.A. 40A:20 Long Term Tax Exemption | Yes, via redevelopment designation + urban renewal entity [43] | 50% | **40%** |
| **AZ** | A.R.S. § 42-6201 GPLET | **No, practically** [48] | 0% | **0% — CONFIRMED** |
| **TX** | Tax Code Ch. 312 | Statutorily open, off-profile in practice; **sunsets 2029-09-01** [14][15] | 35/35/30% | **15%** |
| **FL** | § 196.1995 / § 196.012(14) | **No — "new business" means manufacturing at an industrial plant** [62] | 0% | **0% — CONFIRMED** |
| **NV** | NRS 360.750 GOED | **No — and it abates personal property/sales/MBT, not real property** [54] | 0% | **0% — CONFIRMED** |
| **NC** | **N.C.G.S. § 105-277.13 brownfields exclusion** | **Yes — TP-12 already has the agreement** [66][67] | 10% | **20%** |
| **TN** | **T.C.A. § 7-53-101 IDB PILOT** | **Yes — "recreation and amusement park facilities" is in the project definition** [69] | 40% | 40%, sound |

### The three confirmations

**Florida — 0% confirmed.** § 196.1995 permits a county economic development ad
valorem exemption only for a "new business" or "expansion of an existing
business" as defined in § 196.012. A "new business" must create 10+ full-time
jobs at above-area-average wage **and principally engage in manufacturing,
processing, compounding, fabricating or producing tangible personal property at a
fixed location comprising an industrial or manufacturing plant**, or be a
§ 288.106 target industry. [62] A private club is neither. **TP-08, TP-10 and
TP-15 at 0% are right.**

**Nevada — 0% confirmed, but the model's stated reason is wrong.**
`sites_targets.csv` credits "the 3% assessed-value cap." That is **NRS 361.4723**,
which caps the annual tax *bill* increase on an owner-occupied primary residence.
Non-residential land, commercial buildings and business personal property fall
under **NRS 361.4722 at an up-to-8% cap** on the year-over-year tax bill — a
growth cap, not an assessed-value cap, and not an abatement. [53] Nevada's real
abatement programme, NRS 360.750, abates personal property, sales/use and modified
business tax for wage- and industry-qualified companies — **it does not abate real
property tax at all.** [54] **TP-11 at 0% is right; fix the note.**

**Arizona — 0% confirmed, with a nuance.** GPLET substitutes an excise tax for
property tax on government-owned property leased to a private prime lessee.
Counties *can* be government lessors, but **abatement of the GPLET to zero
requires the property to sit in a single central business district of a city or
town** and to more than double in value. [48] Outside an incorporated CBD there is
no abatement, and the structure would require conveying fee title to Pinal County
and leasing back — no precedent for this use. **TP-06 at 0% is right.**

### The three the model gets wrong

**Texas — cut 35/35/30 to ~15, and note the sunset.** Ch. 312 is real but is
*entirely discretionary*: the county must opt in by resolution, adopt guidelines
and criteria (**which expire and must be re-adopted every two years**), hold a
noticed public hearing, designate a reinvestment zone, and then execute an
agreement. [15] County guidelines in practice screen for capital-intensive,
job-creating industrial projects; a private recreation club with a for-sale
residential component is off-profile on both the job test and the
residential-exclusion most guidelines carry. Then the timing problem:
**Ch. 312 expires 2029-09-01.** [14] At a researched 18–20 month entitlement plus
42 months of construction, an agreement signed at the *end* of entitlement is
already inside the sunset window and any renewal is a legislative act nobody
controls. Model 15% and flag the sunset in the memo.

**North Carolina — raise 10% to ~20%.** The claim that "NC has no abatement
statute" is true as a general matter (Art. V uniformity), and One NC / Building
Reuse are cash grants that belong in incentives `Γ`, not in `τ`. Cabarrus County's
own economic development grant programme lists **motorsports facilities as
eligible** — worth pursuing, but as a grant. The abatement that *does* exist is
**N.C.G.S. § 105-277.13, taxation of improvements on brownfields**: qualifying
improvements on a property under a brownfields agreement are a special class,
excluded on a declining schedule over **the first five taxable years after
completion**. [66][67] TP-12 already carries an NC Brownfields agreement. On the
model's 12-year operating horizon the level-equivalent of a five-year declining
exclusion on improvements is roughly **20%**, not 10% — and it is **front-loaded
into exactly the years when DSCR is tightest**. A flat 10% both understates the
level and hides the covenant benefit. Recommend 20% with a note that the profile
is declining, not flat.

**New Jersey — trim 50% to ~40%.** N.J.S.A. 40A:20 is a genuine 30-year PILOT
route, but it is not a percentage abatement. It requires a Local Redevelopment
and Housing Law "area in need of redevelopment" designation, formation of an
urban renewal entity, and a financial agreement setting an **annual service
charge** measured against gross revenue or total project cost. [43] A closed
municipal landfill is a strong candidate for the designation. The for-sale
component largely falls outside. 40% is the defensible level-equivalent; 50% is
the optimistic end of a negotiation with no term sheet behind it.

### The New York caveat nobody has priced

CLAUDE.md states the PILOT is a **condition precedent** — without ~50% the
covenant breaches and supportable land goes negative. That makes the following
worth a legal opinion before IC, not a footnote:

**GML § 862** restricts IDA financial assistance to projects where the
predominant purpose is making retail sales or providing services to customers who
personally visit the project, absent specific findings (highly distressed area, or
a predominantly non-local customer base). A private membership club providing
services to members who personally visit is squarely in the zone of that
restriction. EPCAL's job-creation disposition mandate and distress history may
support the findings. **Status: `Assumed` — I did not retrieve § 862 in this
session. It is named here as a research task because the whole capital structure
hangs on it.** Riverhead IDA / Suffolk County IDA counsel opinion required.

---

# PART II — JURISDICTION BY JURISDICTION

---

## TP-01 · Town of Riverhead (Calverton / EPCAL), Suffolk County, NY

**Zoning.** Riverhead Town Code **Ch. 301, Zoning and Land Development**. The
governing articles depend on which side of the EPCAL line the parcel sits:
- **Art. LXIII — Planned Development (PD) Zoning Use District** [19], adopted for
  the EPCAL property; site plan applications must conform to the Reuse and
  Revitalization Plan and are **subject to Town Board approval**.
- **Art. XXV — Calverton Industrial (CI)** for the area outside Enterprise Park;
  the district's stated purpose expressly **"allows and encourages commercial
  recreation businesses."** [18]
- **Art. LVII — Special Permits**; special permits are issued by the **Town
  Board**, not the Planning Board. [17]
- **Art. XLI — Pine Barrens Overlay District** [20].

**Posture: `special_permit`**, with a live risk of `map_amendment_required` if the
program falls outside the PD's Reuse Plan envelope. Confidence `Inferred`.

**Approval body.** **Riverhead Town Board** (special permit, PD site plan, and
SEQRA lead agency), on referral to the **Riverhead Planning Board** and to the
**Suffolk County Planning Commission** under GML § 239-m [26]. Land control at
EPCAL runs through the **Riverhead Community Development Agency** as fee owner —
a public disposition process sitting *in front of* the entitlement, not beside it.

**Noise.** **Riverhead Town Code, Noise, Article I** [21] — published.
- **65 dBA daytime**, commercial or residential receiving property
- 75 dBA industrial receiving property
- 50 dBA residential, night
- a motor vehicle is deemed to cause unreasonable noise at **80 dBA or more**
- **Absolute**, by receiving-property category. Confidence `Inferred`.

Layered on top: **NYSDEC Program Policy DEP-00-1** [25] governs the SEQRA noise
assessment and is **ambient-relative** — increases above ambient of 0–3 dBA have
no appreciable effect, 3–6 dBA matter only at the most sensitive receptors, and
**more than 6 dBA at the receptor requires closer analysis**. At a 5,200 ft
nearest residence the ambient-relative test is the survivable one; the municipal
65 dBA absolute cap at the receiving property line is the binding constraint.

**State overlays.**
- **SEQRA.** Type I and a positive declaration should be the planning assumption.
  The precedent is on the ground: a **15-acre motocross track proposed at 2822
  River Road, Calverton** drew a Town Board determination that it would have
  significant environmental impacts, triggering a full EIS. [24] A 620-acre road
  course with residential will not do better.
- **The offsetting fact.** EPCAL has an accepted **Final Supplemental Generic EIS
  (March 2016)** and an updated **SEQRA Consistency Analysis (2020-10-12)**
  covering a subdivision and a mix of uses that expressly includes **recreation**.
  [22][23] If the program can be brought inside the FSGEIS envelope, 6 NYCRR
  § 617.10 supports a **consistency determination instead of a fresh DEIS**. That
  is the single largest schedule lever at this site and it is worth a scoping
  meeting with the Town before anything else.
- **Central Pine Barrens** Compatible Growth Area / Riverhead Pine Barrens Overlay
  [20]; **Suffolk County Sanitary Code Article 6** groundwater and nitrogen
  standards [27] — mitigated here by EPCAL's municipal sewer.
- GML § 239-m referral; NYSDEC SPDES construction stormwater.

**Prior comparables.** Two, both instructive. Drag racing operates at EPCAL today
under a **Town Code Ch. 255 special event permit** approved unanimously by the
Town Board for the 2027 season — motorsport is politically acceptable at EPCAL
*as a temporary event*, which is not the same as a permanent land-use
entitlement. [24] And the Calverton motocross application drew the positive
declaration described above.

**Timeline. Assumed 30 months. Researched 42.** Contradicts, by +12. The stack is
CDA disposition → Town Board scoping → DEIS/FEIS or consistency finding →
GML 239-m → special permit + PD site plan → Planning Board subdivision. If the
FSGEIS consistency route works, 30–33 is reachable; underwrite 42 and treat the
consistency finding as upside.

**Abatement.** GML Art. 18-A, Riverhead IDA PILOT, 50% retained — subject to the
**GML § 862 opinion** above.

---

## TP-02 · "Ulster County Route 9W quarry belt," Ulster County, NY

**This is not a jurisdiction.** New York has no county zoning. Ulster County
cannot grant, deny or condition this use. Until the profile names a **town** —
the 9W corridor runs through Saugerties, Ulster, Kingston, Esopus, Lloyd and
Marlborough — there is no zoning citation, no approval body and no noise
ordinance to cite, and the 36-month assumption has no jurisdiction attached to it.

**Posture: `UNDETERMINED`.** Do not carry `special_permit` as though it were
established.

**Approval body (structural).** The Town Planning Board or Town Board of the
unnamed municipality; **Ulster County Planning Board** referral under GML § 239-m
[26] with the supermajority-plus-one override rule if the county recommends
modification or disapproval.

**Noise. BLANK — UNVERIFIED.** No municipality, no ordinance. **NYSDEC DEP-00-1**
[25] applies at the DEC-permit and SEQRA layer as an **ambient-relative** test
(+6 dBA at the receptor). **Call: the Ulster County Planning Department, and the
land use office of whichever town the parcel lands in, once named.**

**State overlays.**
- **SEQRA** Type I, positive declaration, DEIS.
- **NYSDEC Mined Land Reclamation Law**, ECL Art. 23 Title 27 — an active or
  reclaimed hard-rock quarry carries a mined land use plan and a reclamation bond;
  conversion requires DEC sign-off on release or modification. Confidence
  `Assumed`; not retrieved this session.
- **NYC DEP West-of-Hudson watershed — the flag in the data is probably wrong.**
  `in_woh_watershed = yes` for TP-02. The West-of-Hudson system in Ulster County
  is the **Ashokan / Rondout basins in the western half of the county**; the
  Route 9W corridor is the Hudson shoreline, east of the divide. [28] A 9W
  quarry-belt parcel is **very likely outside** the Catskill/Delaware watershed
  and should not carry `WATERSHED-SEVERE`. Confidence `Inferred`. **Confirm the
  actual parcel against the DEP watershed map before the flag drives anything** —
  it is a near-fatal overlay if true and a free 6–9 months of schedule if false.
- NY Ag District § 305-a review and rollback if enrolled: not established.

**Timeline. Assumed 36. Researched 42, confidence Low.** A SEQRA DEIS on a quarry
conversion with an organised watershed constituency (`opposition_risk = high`) does
not resolve in 36 months in the Hudson Valley.

**Abatement.** Ulster County IDA PILOT under GML Art. 18-A, 50% — same § 862
caveat as TP-01, and without EPCAL's distress and job-mandate facts to support
the findings. Weaker than TP-01 on identical numbers.

---

## TP-03 · Town of Thompson (Putnam), Windham County, CT

**Zoning.** **Town of Thompson Zoning Regulations**, effective 2020-09-15 [29];
**Article 14, Use Regulations** [30]; special permits proceed as **"Special Permit
— Commission Review"** with a mandatory public hearing, applications filed with
the Zoning Enforcement Officer. Confidence `Inferred` — I could not retrieve the
Art. 14 use table line for motor vehicle racing. **Call the Town of Thompson Land
Use Office, (860) 923-9561**, and ask for the use-table citation for a motor
vehicle course and for the status of the existing Thompson Speedway approval.

**Posture: `special_permit`.**

**Approval body.** **Thompson Planning and Zoning Commission** (special permit and
site plan) and, separately and independently, the **Thompson Inland Wetlands and
Watercourses Commission** under CGS §§ 22a-36 to 22a-45. There is no county layer
and no state appeal board. Five people are the entitlement.

**Noise — and this is the most important finding in the Connecticut file.**

The published standard is state, not municipal: **RCSA §§ 22a-69-1.1 et seq.,
Control of Noise** [31][32]. It is **absolute** and set by emitter class →
receptor class:

| Emitter → Receptor | Daytime limit |
|---|---|
| Class C (industrial) → Class A (residential) | **61 dBA** |
| Class B (commercial) → Class A (residential) | 55 dBA |
| Class C → Class C | 70 dBA |

Sources exhibiting discrete tones take a further **−5 dBA**. Municipal ordinances
must be **at least as stringent** as the state plan (CGS § 22a-73); since
2022-07-01 they no longer require DEEP approval. [34]

**61 dBA at a residential receptor would end a road course.** Except:

> **RCSA § 22a-69-1.8 exempts "noise created by the use of property for purposes
> of conducting speed or endurance events involving motor vehicles," effective
> only during the specific periods within which such use is authorised by the
> political subdivision having lawful jurisdiction to sanction it.** [33]

That inverts the entire analysis. In Connecticut the state noise standard **does
not bind racing during town-authorised hours**. The hours-of-operation condition
in the P&Z special permit *is* the noise entitlement — there is no independent
dBA ceiling to design to and no state agency to appeal to. Everything turns on
what the Commission writes into the condition. This is materially **more
survivable than an absolute cap**, and it is also entirely political.

For reference on what an operator self-imposes: Thompson Speedway Motorsports Park
currently runs a **103 dB** sound limit for participants.

**State overlays.**
- **CEPA does not apply.** The brief assumes a Connecticut environmental review.
  CGS §§ 22a-1 et seq. reaches **state agency actions and state-funded or
  state-approved projects** — not private development. [38] There is no CT
  equivalent of a SEQRA DEIS here. Remove CEPA from the TP-03 and TP-05
  permitting paths and reallocate the contingency to the wetlands commission.
- **CGS § 14-311, Major Traffic Generator certificate**, CT DOT Office of State
  Traffic Administration. Triggered at **200+ parking spaces or 100,000 sf**; a
  club of this scale trips it on the first metric. A mandatory pre-application
  meeting is required by § 14-311(f), and the plan **must already have been
  submitted for local P&Z approval before Step 1** — i.e. **sequential, not
  parallel.** [35] Add 4–8 months after the local approval.
- Municipal Inland Wetlands (CGS § 22a-36 et seq.); CT DEEP construction
  stormwater general permit.
- **PA 490 — the parcel is enrolled** (`pa_490_enrolled = yes`). CGS § 12-504a
  imposes a conveyance tax on change of use: **10% of fair market value in year
  one of ownership/classification, declining one point per year to zero after the
  tenth.** [36] Model it against the acquisition date; on a $9.8M ask this is a
  six-figure to seven-figure line item that does not currently appear anywhere.

**Prior comparables.** The inherited motorsport use cuts both ways, as the profile
says. The governing Connecticut precedent is TP-05's — see below — and it applies
statewide.

**Timeline. Assumed 27. Researched 30.** Broadly supports, +3, and Thompson is the
fastest Northeast path in the set. The +3 is the OSTA certificate sitting behind
the local approval. Not modelled and material: a CGS § 8-8 appeal to Superior
Court by any aggrieved person within 15 days of publication adds **12–24 months**
if it happens.

**Abatement.** **CGS § 12-65b** — a municipality may fix the assessment by
agreement for up to 30 years where the property is used for one of twelve named
purposes, and **"(9) recreation facilities" is on the list**. For improvements
over $3M the statute supports **up to 100% of the increased assessment for up to
seven years.** [37] The mechanism is real and expressly reaches this use.
**35% is defensible on a 12-year operating horizon** — seven years at ~60% of the
increment level-equivalents to roughly 35% — but it is a negotiated outcome with a
willing town, not a precedent. Confidence `Inferred`, quantum `Assumed`.

---

## TP-04 · Upper Deerfield / Hopewell Township, Cumberland County, NJ

**Zoning.** Municipal, under the Municipal Land Use Law, N.J.S.A. 40:55D. The
profile's `Agricultural / Institutional` designation with a
`map_amendment_required` posture is the right shape: the two routes are a
**rezoning by the Township Committee** or a **use variance (d-variance) from the
Zoning Board of Adjustment requiring five affirmative votes of seven**. For a
project of this scale, pursue the rezoning; the variance route is a coin flip on
board attendance. Confidence `Inferred` — I could not retrieve either township's
use table.

**Posture: `map_amendment_required`. Confirmed as the correct posture.**

**Approval body.** **Township Committee of Upper Deerfield Township** (or
**Hopewell Township Committee**) for the rezoning, on referral to and
recommendation from the municipal **Planning Board**; then Planning Board
preliminary and final site plan and subdivision. Plus the **Cumberland County
Planning Board** under N.J.S.A. 40:27-6.2/6.6 for county road access and drainage.

**Noise — published, statewide, and strict.** **N.J.A.C. 7:29, Noise Control**
[40][41]:

| Standard | Value |
|---|---|
| Continuous airborne sound, industrial/commercial/community service facility, **at any residential property line**, 7:00 a.m.–10:00 p.m. | **65 dBA** |
| Same, 10:00 p.m.–7:00 a.m. | 50 dBA |
| Impulsive sound | 80 dBA max |
| Octave-band limits | 96 dB at 31.5 Hz down to 53 dB at 8000 Hz |

**Absolute**, measured **at or within the real property line of the receiving
property** (N.J.A.C. 7:29-1.2), by the procedures in N.J.A.C. 7:29B, and enforced
by certified Noise Control Officers. The octave-band table is the sleeper: a road
course's low-frequency content is measured against a **96 dB limit at 31.5 Hz**
that most acoustic reports for recreational uses never model. Confidence
`Inferred`.

At 2,100 ft to the nearest residence and 52 residences within a mile, this is the
tightest noise setting in the target set after TP-05.

**State overlays.**
- **Highlands: not applicable.** The Preservation Area is northern New Jersey.
  Cumberland County is outside it. No statutory bar.
- **Pinelands: probably not applicable, and must be confirmed on the parcel.** The
  Pinelands Area reaches the **eastern edge** of Cumberland County; Upper
  Deerfield and Hopewell sit in the **northwest**, along the Route 55/77 corridor.
  Cumberland County publishes **Map 7 — Pinelands and CAFRA** [44]. Confidence
  `Inferred`. **Municipal boundaries do not track the overlay line — confirm the
  parcel directly with the Pinelands Commission before spending a dollar.**
- **CAFRA: probably not applicable.** The coastal area in Cumberland covers the
  Delaware Bay townships (Downe, Fairfield, Commercial, Maurice River). Same map,
  same instruction. [44]
- **The landfill is the real gate.** **N.J.A.C. 7:26-2A.9** — closure and
  post-closure care of sanitary landfills. **Any future disruption of a closed
  landfill requires prior NJDEP approval**, the closure is recorded with the deed
  in the county recording office, and a professional engineer must certify
  compliance with every provision of the disruption approval afterwards. [42] The
  profile already knows the cap cannot carry pavement; the schedule consequence is
  that the disruption approval is a discrete NJDEP action with its own review
  clock, sitting alongside the CEA/deed notice compliance.
- NJDEP Freshwater Wetlands (N.J.A.C. 7:7A), Flood Hazard Area Control
  (N.J.A.C. 7:13), Stormwater (N.J.A.C. 7:8), NJPDES, Treatment Works Approval,
  Water Allocation.

**Timeline. Assumed 42. Researched 48.** Contradicts, by +6. Rezoning (12–18) →
site plan (9–12) → NJDEP permit set including the landfill disruption approval
(18–30, partly parallel). New Jersey is the hardest of the three original states
and this is the hardest site in it, even without a statutory bar.

**Abatement.** N.J.S.A. 40A:20 long-term exemption via LRHL redevelopment
designation and an urban renewal entity. [43] **Trim 50% → 40%.**

---

## TP-05 · "Litchfield County golf corridor," Litchfield County, CT

**This is not a jurisdiction either.** Connecticut has no county government and no
county zoning — the brief says so and the data does not honour it. Litchfield
County cannot approve anything. Name the town (the Route 8 / Route 202 corridor
runs through Torrington, Litchfield, Harwinton, Thomaston and Watertown) and the
whole file changes.

**Posture: `map_amendment_required`** as profiled — a closed golf course in a
`Residential / Recreation` district converting to a motorsport use is a zone
change, not a special permit. Confidence `Assumed` pending the municipality.

**Approval body (structural).** The **Planning and Zoning Commission** of the
unnamed town — which in Connecticut both **writes the map and grants the
permit** — and the town's **Inland Wetlands and Watercourses Commission**. Plus
CT DOT OSTA under § 14-311. [35] There is nobody above them.

**Noise.** Same state framework as TP-03: **RCSA § 22a-69** [31][32], **61 dBA**
Class C emitter → Class A receptor daytime, absolute, −5 dBA for discrete tones,
**with the § 22a-69-1.8 motor-vehicle speed-event exemption operative only during
town-authorised hours** [33]. At **800 ft to the nearest residence and 110
residences within one mile, abutting a residential subdivision on the property
line**, the exemption is the only thing standing between the project and a
physical impossibility — and the exemption is granted by the same five people who
must first rezone the land. Confidence `Inferred` for the state table; the
municipal ordinance is **UNVERIFIED** pending the town.

**The precedent that governs this site, and it is bad.**

**Lime Rock Park, Salisbury — 19 miles away, same county, same state, and the
Connecticut Supreme Court has ruled on it.** [39] The track opened in 1957; a 1959
Litchfield Superior Court permanent injunction obtained by the Lime Rock
Protective Association banned Sunday racing and was upheld by the Connecticut
Supreme Court in 1963; a 1968 order prohibited unmuffled racing; the Salisbury
P&Z later folded the injunction into its zoning regulations; the owner's 2015–2018
effort to lift the Sunday ban won at Superior Court and was **reversed by the
Connecticut Supreme Court, which held that towns may regulate auto racing,
including a ban on racing on a given day of the week.**

Two conclusions follow. First, the operating calendar in Litchfield County is a
zoning variable, not an operating assumption — and `season_days = 200` for TP-05
already assumes days the town may simply remove. Second, an organised abutter
association in this county has a **sixty-seven-year, Supreme-Court-affirmed track
record of winning.** TP-05 carries `opposition_risk = severe`, an abutting
subdivision on the property line, and two prior failed contracts. The precedent
and the facts agree.

**State overlays.** No CEPA [38]. Inland wetlands. CGS § 14-311 OSTA [35].
**PA 490 enrolled** — § 12-504a conveyance tax recapture on change of use [36].
CT DEEP stormwater. Pesticide-legacy soil handling is a diligence item, not a
permit gate.

**Timeline. Assumed 33. Researched 54.** Contradicts hard, by **+21**. A
use-driven map amendment (15–24) → special permit and site plan (9–12) → wetlands
(concurrent) → OSTA (6, sequential) → **a CGS § 8-8 appeal to Superior Court that
should be treated as near-certain given the abutters and the county's history
(+12–24)**. 33 months is the no-appeal, willing-town case. Nothing about this site
supports assuming a willing town.

**Abatement.** CGS § 12-65b(a)(9) recreation facilities [37]. 25% is inside the
achievable band but assumes a town that wants the project. Confidence `Low`.

---

## TP-06 · Pinal County, AZ (I-10 corridor, Casa Grande to the West Valley)

**Zoning.** **Pinal County Development Services Code, Title 2 — Zoning**,
**Ch. 2.40 GR General Rural Zone** (and Ch. 2.50 GR-10) [45], with special use
permits governed by **Ch. 2.151**. Confidence `Inferred` — I could not retrieve the
GR use table entry for a racetrack.

**Posture: `special_permit` (statutory special use permit). Confirmed.**

**Approval body.** **Pinal County Board of Supervisors, on recommendation of the
Pinal County Planning and Zoning Commission.** [45]

**Noise. BLANK — the ordinance is published but the table was not retrievable.**

Pinal County has a real, adopted, unincorporated-area-only noise ordinance:
**Ordinance No. 050306-ENO as amended by 031611-ENO-01** [46]. What is confirmed:
land use classes are **Residential, Commercial, Rural and Industrial**; limits
are set by class and by time of day; sound levels in **Table 1** are applied as
**L­eq**; the published summary range across all classes and times is **55 to 70
dBA**; vehicle-operation limits run 82–90 dBA measured up to 50 ft from street
centreline; the ordinance **does not apply inside any incorporated city, town or
Indian reservation**; violation is a Class ? misdemeanour plus a civil penalty up
to $750/day. [47]

**I will not write a Rural daytime number I have not read.** Table 1 is in the
ordinance PDF. **Call Pinal County Planning and Development, (520) 509-3555**, and
ask for the Table 1 Rural and Residential daytime Leq values and the measurement
point. `noise_standard_type = absolute, Leq, by land use class`.

**State overlays.**
- ADEQ **Aquifer Protection Permit** (A.R.S. § 49-241) for the package treatment
  plant and effluent reuse, plus **AZPDES** construction stormwater.
- **ADOT** access permit for the state highway connection.
- Sonoran desert tortoise survey (profiled).
- **The overlay that could break the merchant build — Assured Water Supply.**
  The parcel is described as "no municipal water or sewer: deep well." Arizona's
  Assured Water Supply Rules require a subdivision inside an Active Management
  Area to demonstrate a **100-year assured supply** before the plat can be
  recorded and homes sold. **ADWR's 2019 Pinal model projected 8.1 million
  acre-feet of unmet demand over the 100-year horizon — roughly 10% of total
  projected demand — with the consequence that ADWR cannot approve new
  subdivisions in the Pinal AMA intending to rely on groundwater.** [49]

  TP-06's for-sale homesites are the entire merchant-build thesis at this site.
  If the parcel is in the **Pinal AMA**, the residential component may be
  **unplattable on groundwater**, and the fix is CAGRD membership or an acquired
  renewable supply — a cost and a schedule nobody has priced. If it is in the
  **Phoenix AMA** (the profile also says "Loop 303," which is Maricopa County),
  the same rules apply against a supply picture that is not in deficit.

  **The profile straddles two AMAs and the answer differs between them.**
  Establish the AMA of record before Pinal is carried as the co-lead. Confidence
  `Verified` on the ADWR finding; `Assumed` on which AMA the parcel sits in.

**Timeline. Assumed 18. Researched 24** on the zoning path alone — contradicts by
+6. The special use permit is genuinely fast (P&Z recommendation → BOS, one to two
hearing cycles). The 24 reflects the APP and the ADOT permit. **The AWS
determination is not in the 24 and is potentially unbounded for the residential
component.**

**Abatement. 0% — confirmed** [48]. See Part I.

---

## TP-07 · Hood County, TX (SH-144 corridor near Cresson)

**Zoning. The "UNZONED" designation in the data is wrong.**

**Texas Local Government Code Ch. 231, Subchapter K — Development Regulations in
Hood County**, §§ 231.221–231.234 [4][5], implemented as the **Hood County
Development Rules and Regulations** administered by the Hood County Development
Department [6]. The subchapter authorises **districts** (§ 231.225) and a
**special exception** process (§ 231.228), and seats a **Hood County Development
Commission**.

**Posture: `special_permit`, not `as_of_right`. This is the single ranking-relevant
correction in the file.**

**Approval body.** **Hood County Commissioners Court**, with the **Hood County
Development Commission** in the recommending/special-exception role, plus
Commissioners Court plat approval under LGC Ch. 232.

**Noise. BLANK — no county authority exists.** Texas counties cannot enact noise
ordinances [9]. The only statewide provision is the **Penal Code § 42.01(c)(2)**
85 dB post-warning presumption [8], which is a criminal presumption and not a
land-use standard. `noise_standard_type = none — private nuisance exposure only`.
**Call the Hood County Development Department, (817) 408-2515** to confirm whether
any Subchapter K district regulation imposes a performance standard.

**State overlays.** TCEQ CGP TXR150000 [11]; TxDOT access permit 43 TAC
§§ 11.50–11.58 [12]; OSSF 30 TAC Ch. 285; county floodplain permit; H&S Code
Ch. 751 mass gathering permit from the County Judge with a public hearing before
each 2,500+ event [10]. No Edwards Aquifer program. Lake Granbury / Brazos
watershed is the express legislative basis for Subchapter K and will colour the
drainage review.

**Timeline. Assumed 12. Researched 20.** Contradicts by **+8**. Special exception
plus plat plus TxDOT is not a 12-month path, and the 12-month assumption was
derived from a no-zoning premise that does not hold in this county.

**Abatement.** Tax Code Ch. 312, **cut 35% → 15%**, sunset 2029-09-01. [14][15]

---

## TP-08 · Marion County, FL (I-75 / US-27, northwest of Ocala)

**Zoning.** **Marion County Land Development Code, Article 4, Division 2,
§ 4.2.3 — General Agriculture (A-1)** [55]. The A-1 use list carries a defined
use, **"Motorized Vehicle Racetrack or Practice Facility: a place where ATV's,
Motocross Bikes, Go Carts, Off Road Vehicles, or any similar vehicles, gather to
compete against each other or against time."** The use is enumerated; the posture
(permitted vs special use) I could not confirm from the retrieval, and the
profile's `special_permit` is the sensible reading. Confidence `Inferred`.

**Posture: `special_permit` (Marion County special use permit).**

**Approval body.** **Marion County Board of County Commissioners, on
recommendation of the Marion County Planning and Zoning Commission**, with a
required **comprehensive-plan consistency finding**.

**Noise — published.** **Marion County Code of Ordinances, Chapter 13, Noise and
Vibration Control**: **§ 13-7** (maximum permissible sound levels, land use
acoustic categories, times, measurement descriptors, adjustment for character of
sound), **§ 13-8** (measurement procedure), **§ 13-10** (prohibited acts). [56]

- **65 dB(A) for residential-use receiving property, 7:00 a.m. to 10:00 p.m.**
- 75 dB(A) reported for industrial/manufacturing categories, 24 hours
- 55 dB(A) in designated noise-sensitive zones
- **Absolute**, by receiving land-use acoustic category, measured per § 13-8, with
  an adjustment for character of sound (the tonal penalty analogue)

Confidence `Inferred` — § 13-7's full table was not retrievable; the 65 dB(A)
daytime residential figure is quoted from § 13-10's cross-reference. **Verify the
§ 13-7 table and the § 13-8 measurement point before design.**

**State overlays.**
- **Comprehensive plan consistency, Fla. Stat. § 163.3194** — every development
  order must be consistent with the adopted plan, and **§ 163.3215 gives any
  aggrieved or adversely affected party the exclusive route to challenge
  consistency in circuit court.** [60] In Marion County that route is used.
- **Water Management District ERP** (SWFWMD / SJRWMD) [61] — with no off-site
  outfall, retention on site, and karst.
- FDEP springs-protection nutrient limits on irrigation; gopher tortoise
  relocation permit.

**Prior comparables — the organised opposition is real and has won before.**
The **Double Gate ATV Park** application (Blitch Plantation / International
Property Services) proposed an ATV racetrack, trails, sales and repair, and event
facilities **inside Marion County's Farmland Preservation Area**, and drew
sustained opposition on noise grounds — "racing ATVs are loud, with people in a
5-mile radius able to hear them." [57] Separately, the **Horse Farms Forever
amendment, effective 2022-04-30, requires that all zoning requests and special use
permits be consistent with the goals of the Farmland Preservation Area.** [57]

That amendment converts the FPA boundary from a planning line into an approval
standard. The profile already says the FPA boundary must be avoided. Treat it as a
hard site-selection constraint, not a mitigation item.

**Timeline. Assumed 22. Researched 30.** Contradicts by +8: special use permit
(9–12) → comp-plan consistency finding → ERP with a karst grouting program
(12–18, partly parallel) → the § 163.3215 challenge window.

**Abatement. 0% — confirmed** [62].

---

## TP-09 · Waller County, TX (US-290 corridor)

**Zoning. None — genuinely unzoned.** No Chapter 231 subchapter reaches Waller
County. [4] `as_of_right` is **correct as to zoning** and misleading as to
discretion.

**Posture: `as_of_right`.**

**Approval body.** **Waller County Commissioners Court** — for the plat, under
adopted **Subdivision and Development Regulations (rev. 2023-12-06)**, which
require the application to be filed with the Court, **a public hearing date set
and notice published by the County Engineer**, and County Engineer approval of
street, drainage, signage, landscaping, irrigation and utility construction plans
before final plat. [16] Also the **County Judge** for each mass gathering permit
[10].

**Noise. BLANK — no county authority.** Penal Code § 42.01(c)(2) 85 dB
post-warning presumption only [8][9]. `noise_standard_type = none`.

**State overlays.** TCEQ CGP TXR150000 [11]; TxDOT US-290 access permit [12];
OSSF 30 TAC Ch. 285 against a 45 min/in perc rate; NFIP floodplain permit — the
pad must clear the 100-year floodplain per the profile; **USACE Section 404 for
the ditch network, and this is the schedule driver, not the plat**; Ch. 751 mass
gatherings [10].

**Timeline. Assumed 13. Researched 18.** Contradicts by +5, driven entirely by the
404 individual permit, not by the county.

**Abatement.** Ch. 312, **cut 35% → 15%**, sunset 2029-09-01 [14][15]. Waller's
active precedent is industrial; a private club is off-profile against county
guidelines.

---

## TP-10 · Hendry County, FL (SR-82 corridor)

**Zoning.** **Hendry County Code of Ordinances, Chapter 1-53 — Zoning**;
**§ 1-53-2** establishes the districts, including **A-2 General Agriculture**,
where uses such as camping facilities are allowed by special exception. [58]

**One retrieval flag worth chasing:** the search index surfaced language to the
effect that **firing ranges and facilities associated with motor sports are
specifically excluded** from certain Hendry land use categories. I could not
confirm the section or the scope. If motorsport is affirmatively excluded from
A-2, TP-10's posture is not `special_exception` but
`prohibited_no_amendment_path` short of an LDC text amendment. **This is a
material open item.** Confidence `UNVERIFIED`.

**Posture: `special_permit` (special exception) — pending the exclusion check.**

**Approval body.** **Hendry County Board of County Commissioners**, on
recommendation of the **Hendry County Local Planning Agency / Planning
Commission**. **Call Hendry County Planning & Zoning, LaBelle, (863) 675-5240.**

**Noise. BLANK — UNVERIFIED.** No Hendry County noise ordinance was located. Note
that **Florida has no statewide stationary-source noise standard** — unlike New
Jersey and Connecticut, there is no state floor to fall back on, so if the county
has no ordinance there is **no published dBA standard at all** and the exposure is
comp-plan compatibility findings plus common-law nuisance. **Call Hendry County
Planning & Zoning, (863) 675-5240**, and ask specifically whether Chapter 1-53
carries performance standards for noise and whether the county has a separate
nuisance ordinance.

**State overlays.**
- **SFWMD ERP**, high water table, existing citrus canal network.
- **Comprehensive plan consistency, § 163.3194 / § 163.3215** [60].
- **Florida panther primary zone — the binding constraint, and the assumed
  timeline does not reflect it.** The profile correctly identifies USFWS
  consultation. The mechanism matters: **Section 7 consultation only exists if
  there is a federal nexus** (a USACE 404 permit, federal funding). A state ERP is
  not a federal nexus. Absent a 404 permit, take authorisation runs through an
  **ESA § 10(a)(1)(B) incidental take permit with a Habitat Conservation Plan** —
  which is *slower* than Section 7, routinely 24–48 months, and carries its own
  NEPA document. Panther mitigation credits are the cost; the HCP is the
  schedule.

**Timeline. Assumed 24. Researched 42.** Contradicts by **+18**, and the variance
is almost entirely the federal species pathway. The county approval is the easy
part here — `opposition_risk = low locally` is right and irrelevant.

**Abatement. 0% — confirmed** [62].

---

## TP-11 · Clark County, NV (Apex / I-15 north corridor)

**Zoning.** **Clark County Code Title 30, Unified Development Code** (effective
2024-11-20) [52]; **§ 30.40.230**, purpose of the **M-D Designed Manufacturing
District** — "light manufacturing establishments with limited outside uses," with
a stated purpose of **prohibiting incompatible uses** [51]; the use table is at
**Ch. 30.44**. Whether a motorsport facility is a permitted, conditional or use-
permit use in M-D was not retrievable. Confidence `Inferred`.

Note the tension: M-D's own purpose clause limits **outside uses**. A 620-acre
outdoor circuit in a district designed for limited outdoor activity is a
plausible re-designation candidate, not an obvious use-permit candidate. Confirm
before carrying `special_permit`.

**Posture: `special_permit` (use permit), with re-designation risk.**

**Approval body.** **Clark County Board of County Commissioners, on recommendation
of the Clark County Planning Commission.**

**Noise. BLANK — the standard is published but the table was not retrievable.**

**Clark County Code § 30.68.020, Noise**, within Ch. 30.68 Site Environmental
Standards. [50] What is confirmed:
- limits are set **by time period and zoning district in Table 30.68-1**
- **measured at all property lines, at a height of at least four feet above
  ground** — an emitter-side property-line standard
- the limits **may be exceeded by 10 dB for a single period of not more than 15
  minutes in any one day**
- where emitting and receiving premises are in different districts, **the more
  restrictive district's limits govern** noise entering that district
- ±2 dB meter-fluctuation convention

`noise_standard_type = absolute, property line, with a 10 dB / 15-minute
allowance`. **Call Clark County Comprehensive Planning, (702) 455-4314**, and ask
for Table 30.68-1 by district and time period.

The 10 dB / 15-minute allowance and the 11,000 ft nearest residence make this the
most permissive noise setting in the target set on the facts, whatever the table
says. The `more restrictive district governs` rule is the one to watch if any
adjoining land is residentially designated.

**State overlays.** NDEP water pollution control and construction stormwater;
**BLM right-of-way under FLPMA Title V** for the 3.2-mile water main and access
alignment — a ROW grant with an Environmental Assessment is a **12–24 month
federal action** and is the long pole here, not the use permit; **Nevada Division
of Water Resources water rights** in the Apex/Garnet Valley basin, which is the
substantive constraint behind the $5.4M water line; Clark County **Desert
Conservation Program / MSHCP** land-disturbance fee for desert tortoise habitat
(confirm the current per-acre rate — I did not verify it and will not quote one).

**Timeline. Assumed 16. Researched 22.** Contradicts by +6. The use permit is fast;
the BLM ROW is not.

**Abatement. 0% — confirmed** [53][54]. Correct the stated rationale: the cap is
**NRS 361.4722 at up to 8%** on non-residential property and it caps the annual
tax-bill increase, not assessed value. The 3% figure is NRS 361.4723 and applies
to owner-occupied primary residences.

---

## TP-12 · Cabarrus County, NC (US-29 corridor northeast of Concord)

**Zoning.** **Cabarrus County Development Ordinance, Chapter 8** [63], under
N.C.G.S. Ch. 160D. The profile's **LI Light Industrial** base with a **conditional
district** route is the right instrument: a conditional district under
N.C.G.S. § 160D-703(b) is a **legislative rezoning with applicant-proposed,
site-specific conditions**, requiring the applicant's written consent and a
plan-consistency statement under § 160D-605. Confidence `Inferred`.

**Posture: `map_amendment_required` in form (it is a rezoning), `special_permit`
in effect (conditions are negotiated, not standardised).** The data's
`special_permit` with a "conditional district" path is a fair description;
recognise that it is procedurally a legislative act, which means **no
quasi-judicial evidentiary record and no certiorari standard — but also broad
discretion to say no.**

**Approval body.** **Cabarrus County Board of Commissioners, on recommendation of
the Cabarrus County Planning and Zoning Commission**, with a written plan-
consistency statement. (Setback, buffer, fencing and parking conditions for
special use permits are set by the **Board of Adjustment** — a different track,
not this one.)

**Noise — published, and the softest-looking number in the set. Verify it.**
**Cabarrus County Code of Ordinances, Chapter 30 (Environment), Article II,
§ 30-27**: **65 dB, 7:00 a.m.–10:00 p.m.; 55 dB, 10:00 p.m.–7:00 a.m., measured
from the property line of the source.** [64][65]

Two cautions. First, the figures come from secondary compilations of § 30-27, not
from the primary text I could open — confidence `Inferred`, **verify before
design**. Second, note the measurement point: **the property line of the source**,
not the receiving property. On a 430-acre parcel that is a very different — and
much more manageable — test than New Jersey's residential-receiving-line
standard, because the emitter controls the setback. This is the most favourable
measurement-point construction in the target set.

**State overlays.** **NCDEQ Brownfields Agreement** (already contemplated, and it
is what unlocks the tax exclusion below); NCDEQ construction stormwater and
erosion control; NCDOT driveway permit; sedimentation and pollution control
plan approval. No state environmental review analogue to SEQRA for private
development.

**Prior comparables.** None adverse. This is the one market in the country where a
racing facility reads as civic infrastructure, and the county's own economic
development grant programme **lists motorsports facilities as eligible projects.**

**Timeline. Assumed 19. Researched 20.** **Supports** — the only assumption in the
set that survives contact intact. A conditional district is one Planning
Commission cycle plus one Board of Commissioners cycle; the brownfields agreement
runs in parallel and is already in train.

**Abatement. Raise 10% → 20%.** **N.C.G.S. § 105-277.13** excludes a declining
share of the value of qualifying improvements on brownfields property for the
**first five taxable years after completion**, given a brownfields agreement and
improvements made after it. [66][67] On a 12-year operating horizon that
level-equivalents to roughly 20%, and it is **front-loaded into the first
operating years — precisely where the covenant is tightest**. Model it as a
declining schedule, not a flat rate, if the cash flow can carry the profile; the
DSCR benefit is worth more than the average suggests. The One NC / Building Reuse
and county motorsports grants are **cash and belong in `Γ`, not in `τ`.**

---

## TP-13 · Caldwell County, TX (SH-130 corridor near Lockhart)

**Zoning. None.** No Chapter 231 subchapter reaches Caldwell County. [4]
`as_of_right` correct as to zoning.

**Posture: `as_of_right`.**

**Approval body.** **Caldwell County Commissioners Court** for plat approval under
LGC Ch. 232; **County Judge** for mass gathering permits [10].

**Noise. BLANK — no county authority.** Penal Code § 42.01(c)(2) only [8][9].

**State overlays.**
- **The Edwards Aquifer line in the model's permitting path is wrong — delete
  it.** TCEQ's Edwards Aquifer Protection Program under **30 TAC Ch. 213** applies
  in Kinney, Uvalde, Medina, Bexar, Comal, Hays, Travis and Williamson counties.
  **Caldwell is not among them.** [13] No contributing-zone plan is required.
- TCEQ CGP TXR150000 [11]; TxDOT SH-130 corridor access permit [12] — note that
  SH-130 segments 5–6 are a **concession toll facility**, so access and frontage
  arrangements involve the concessionaire as well as TxDOT; OSSF 30 TAC Ch. 285
  against a 40 min/in perc rate; groundwater conservation district permitting for
  non-exempt wells (confirm the district of record).
- The profile's own note — "the political culture is more interventionist than
  the rest of Texas" — is the right instinct and has no legal hook to attach to.
  In an unzoned county that pressure expresses itself through the plat hearing,
  the mass gathering hearing, and nuisance litigation.

**Timeline. Assumed 14. Researched 18.** Contradicts by +4 — plat, TxDOT/
concessionaire access, and OSSF.

**Abatement.** Ch. 312, **cut 30% → 15%**, sunset 2029-09-01 [14][15].

---

## TP-14 · Maury County, TN (I-65 corridor south of Franklin)

**Zoning.** **Maury County Zoning Resolution**, original adoption 1986-04-21,
current text effective 2024-12-11 [68]. The **A-2 Rural Residential District**
operates on a closed list — **"all uses except those specifically permitted or
permitted upon approval as a special exception by the Board are prohibited."**
[68] Confidence `Inferred`; I could not retrieve the A-2 use list.

**Posture: `map_amendment_required`** as profiled, **unless** a motorsport or
outdoor commercial recreation use appears on the A-2 special-exception list — in
which case it drops to `special_permit` and the timeline improves materially.
**That is a one-page check worth making before anything else at this site.**

**Approval body.** For a map amendment: the **Maury County Board of
Commissioners**, on recommendation of the **Maury County Regional Planning
Commission**. For a special exception: the **Maury County Board of Zoning
Appeals**. The county's own guidance describes a zoning amendment as a multi-step
process involving the Planning Commission, the County Commission **and** the Board
of Zoning Appeals. [68]

**Noise. BLANK — UNVERIFIED.** No Maury County noise ordinance was located, and
Tennessee counties' noise authority is limited. **Call the Maury County Building
and Zoning Office** (Columbia, TN) and ask (a) whether the Zoning Resolution
carries performance standards for noise in A-2, and (b) whether the county has a
separate nuisance or noise ordinance. Phone number not verified in this
environment — do not use a number nobody has checked.

**State overlays.** **TDEC** mining reclamation release for the retired quarry;
TDEC construction stormwater (TNCGP) and aquatic resource alteration permit if
streams are affected; karst/sinkhole geotechnical review; TDOT access permit.
No state environmental review analogue for private development.

**Political read.** `opposition_risk = moderate-high` is right: Williamson County
wealth moving south, 2,600 ft to the nearest residence, 29 residences within a
mile, and a litigation-capable constituency. Maury County is not Williamson
County, and that is the whole reason the site is on the list — but the neighbours
increasingly are.

**Timeline. Assumed 24. Researched 30.** Contradicts by +6 for a map amendment
running Planning Commission → County Commission with a TDEC reclamation release in
parallel. If A-2 carries a special exception for this use, 18–22 is reachable.

**Abatement. 40% — confirmed as statutorily sound.** **T.C.A. § 7-53-101** defines
an IDB "project" to include **"recreation and amusement park facilities suitable
for use by private corporations or governmental units,"** and separately
**"tourism attractions involving an aggregate investment of public and private
funds in excess of $75,000,000"** including recreation and entertainment
facilities and related hotels and amenities. [69] Property owned by an Industrial
Development Board is tax exempt, and the local government may authorise the IDB to
negotiate and accept a PILOT from the lessee. [69][70] The structure requires the
**Industrial Development Board of Maury County** to take title and lease back, on
terms approved under the county's PILOT policy. This is the **strongest abatement
mechanism in the entire target set on statutory fit** — the statute names the use.
Confidence `Verified` on eligibility; `Assumed` on the 40% quantum.

---

## TP-15 · Hardee County, FL (SR-64 / SR-62 corridor)

**Zoning.** **Hardee County Unified Land Development Code**, adopted 2023-10-12 by
**Ordinance 2023-13**; **Article 3 — Zoning Districts and Uses**. [59] The code
runs on a closed **Table of Land Uses**: **"No use is permitted unless it is
listed as a Permitted (P), Permitted with Conditions (PWC), or Special Exception
(SE) in the Table of Land Uses."** [59] Whether a motorsport facility appears in
the table at all — in **A-1 Agricultural** or anywhere — I could not confirm.

**Posture: `special_permit` (special exception) if the use is in the table;
`prohibited_no_amendment_path` short of an LDC text amendment if it is not.**
Confidence `UNVERIFIED`. **This is the first call to make on this site.**

**Approval body.** **Hardee County Board of County Commissioners**, on
recommendation of the Planning and Zoning Board, with a comprehensive-plan
consistency finding. Which body holds the special-exception hearing was not
confirmed. **Call Hardee County Planning & Zoning, 110 S. 9th Ave, Wauchula,
(863) 767-1964.**

**Noise. BLANK — UNVERIFIED.** No Hardee County noise ordinance was located.
**Florida has no statewide stationary-source noise standard.** If Hardee has no
ordinance, there is **no published dBA limit governing this site**, and the
constraint is comp-plan compatibility plus nuisance. That is not the same as
"unconstrained" — it means the standard gets written at the hearing, by the board,
against whatever the opposition puts in the record. **Same call: (863) 767-1964.**

The physical facts are the best in the set: 8,200 ft to the nearest residence,
**two** residences within a mile, surrounded by mining and agriculture.

**State overlays.**
- **FDEP phosphate mine reclamation release** — the long pole. The profile flags
  it as pending. Reclamation release under the FDEP mandatory phosphate program is
  a discrete state action with its own record and its own clock, and no track
  alignment crosses the clay settling areas without a preload program the
  reclamation plan has to accommodate.
- **FDEP radiological / TENORM screening** on reclaimed phosphate land.
- **SWFWMD ERP** [61].
- **Comprehensive plan consistency, § 163.3194 / § 163.3215** [60].
- Gopher tortoise and crested caracara surveys.

**Timeline. Assumed 21. Researched 30.** Contradicts by +9, driven by the FDEP
reclamation release rather than the county.

**Abatement. 0% — confirmed** [62].

---

# PART III — WHAT SHOULD CHANGE, AND WHY

The principal decides. `data/sites_targets.csv` and the config were not touched.

## Ranking-relevant

1. **TP-07 Hood County is not as-of-right.** LGC Ch. 231 Subchapter K gives Hood
   County districts, development regulations, a special-exception process and a
   standing Development Commission. [4][5][6] Change `zoning_posture` from
   `as_of_right` to `special_permit`, `zoning_district` from `UNZONED` to
   `Hood County development regulations, LGC Ch. 231 Subch. K`, and
   `permitting_timeline_months` from 12 to 20. Hood's friction advantage over
   Waller and Caldwell disappears; the Texas ordering inside the set changes.
2. **TP-06 Pinal has an Assured Water Supply problem that reaches the merchant
   build.** ADWR's 2019 Pinal model found 8.1 MAF of unmet 100-year demand, with
   the result that new groundwater-reliant subdivisions cannot be approved in the
   Pinal AMA. [49] TP-06 is a groundwater site with for-sale homesites. Establish
   the AMA of record. Pinal is the co-lead at 65.3 against EPCAL's 65.9; this is
   the kind of finding that resolves a dead heat.
3. **TP-05 Litchfield is a 54-month site, not a 33-month site**, and the
   Connecticut Supreme Court has already held that towns may ban racing on a given
   day of the week. [39] `season_days = 200` for TP-05 assumes operating days that
   the entitlement may simply not grant.
4. **TP-10 Hendry's schedule is federal, not local.** Absent a 404 nexus, panther
   take authorisation runs through an ESA § 10 HCP: 42 months, not 24.

## Data corrections

| Field | Site | From | To | Basis |
|---|---|---|---|---|
| `zoning_posture` | TP-07 | `as_of_right` | `special_permit` | [4][5] |
| `zoning_district` | TP-07 | `UNZONED` | Subchapter K development regulations | [5][6] |
| `permitting_path` | TP-13 | includes Edwards Aquifer plan | delete that clause | [13] |
| `in_woh_watershed` | TP-02 | `yes` | likely `no` — confirm on the parcel | [28] |
| `tax_abatement_path` | TP-11 | "3% assessed-value cap" | NRS 361.4722, up to 8% cap on the annual tax bill | [53] |
| `permitting_path` | TP-03, TP-05 | implies CT state env. review | CEPA does not reach private development; add CGS § 14-311 OSTA | [35][38] |
| `municipality` | TP-02, TP-05 | county named | **town required** — NY and CT have no county zoning | — |

## Abatement re-sizing

| Site | Model | Researched | Statute |
|---|---|---|---|
| TP-07 | 0.35 | **0.15** | Tax Code Ch. 312, sunsets 2029-09-01 [14][15] |
| TP-09 | 0.35 | **0.15** | same |
| TP-13 | 0.30 | **0.15** | same |
| TP-12 | 0.10 | **0.20** | N.C.G.S. § 105-277.13, declining 5-yr, front-loaded [66] |
| TP-04 | 0.50 | **0.40** | N.J.S.A. 40A:20 annual service charge [43] |
| TP-06, TP-08, TP-10, TP-11, TP-15 | 0.00 | **0.00 — confirmed** | [48][53][54][62] |
| TP-14 | 0.40 | **0.40 — confirmed eligible** | T.C.A. § 7-53-101 names recreation facilities [69] |
| TP-03, TP-05 | 0.35 / 0.25 | **unchanged, mechanism confirmed** | CGS § 12-65b(a)(9) names recreation facilities [37] |
| TP-01, TP-02 | 0.50 | **0.50, flagged** | GML Art. 18-A — **obtain a § 862 opinion** |

Directionally the Texas cuts hurt three sites the model likes, the NC increase
helps one it under-rates, and the NY 50% — the one CLAUDE.md calls a condition
precedent — is the only abatement in the set with an unresolved statutory
eligibility question hanging over it.

## Timeline verdicts

| Site | Assumed | Researched | Δ | Verdict |
|---|---|---|---|---|
| TP-01 EPCAL | 30 | 42 | +12 | contradicts |
| TP-02 Ulster | 36 | 42 | +6 | contradicts, low confidence |
| TP-03 Thompson | 27 | 30 | +3 | broadly supports |
| TP-04 Cumberland | 42 | 48 | +6 | contradicts |
| TP-05 Litchfield | 33 | 54 | +21 | contradicts hard |
| TP-06 Pinal | 18 | 24 | +6 | contradicts; AWS unbounded |
| TP-07 Hood | 12 | 20 | +8 | contradicts — premise wrong |
| TP-08 Marion | 22 | 30 | +8 | contradicts |
| TP-09 Waller | 13 | 18 | +5 | contradicts |
| TP-10 Hendry | 24 | 42 | +18 | contradicts hard |
| TP-11 Clark | 16 | 22 | +6 | contradicts |
| TP-12 Cabarrus | 19 | 20 | +1 | **supports** |
| TP-13 Caldwell | 14 | 18 | +4 | contradicts |
| TP-14 Maury | 24 | 30 | +6 | contradicts |
| TP-15 Hardee | 21 | 30 | +9 | contradicts |

Mean assumed 23.4 months; mean researched 31.3. **The set is optimistic by about
eight months on average and fourteen of fifteen sites are optimistic.** The
config's 33-month entitlement default is close to the researched mean — the
per-site column is what drifts, and it drifts one way.

**Every researched figure here is `Inferred` from statutory paths and comparable
applications, not from a published municipal processing schedule.** No jurisdiction
in this set publishes a guaranteed timeline. Where the delta is large the driver
is named: a federal permit at TP-10 and TP-11, an appeal at TP-05, an EIS at
TP-01, a state reclamation release at TP-15.

## Calls to place — the nine blanks

| Site | Office | Number | Ask |
|---|---|---|---|
| TP-02 | Ulster County Planning Dept + the named town's land use office | not verified | which town; that town's noise ordinance |
| TP-06 | Pinal County Planning & Development | **(520) 509-3555** | Ord. 050306-ENO Table 1, Rural & Residential daytime Leq, measurement point |
| TP-07 | Hood County Development Dept | **(817) 408-2515** | § 231.222 geographic reach; any district performance standards |
| TP-09 | Waller County Engineer / Commissioners Court | not verified | plat hearing calendar; confirm no performance standards |
| TP-10 | Hendry County Planning & Zoning, LaBelle | **(863) 675-5240** | is motorsport excluded from A-2? any noise ordinance? |
| TP-11 | Clark County Comprehensive Planning | **(702) 455-4314** | Table 30.68-1 by district and time period |
| TP-13 | Caldwell County Commissioners Court | not verified | confirm no county noise or performance standards |
| TP-14 | Maury County Building & Zoning Office, Columbia | not verified | A-2 special-exception list; any noise ordinance |
| TP-15 | Hardee County Planning & Zoning, Wauchula | **(863) 767-1964** | is motorsport in the Table of Land Uses? any noise ordinance? |

TP-03's number is **(860) 923-9561**, Town of Thompson Land Use Office, as
supplied in the brief; not independently verified here.

**Numbers not listed above are not listed because nobody has checked them.** An
unverified phone number in an entitlement register is the same failure mode as an
invented decibel limit — it just fails one step later.
