# Risk Register — Noise Litigation, Opposition, Environmental and Title

**Date:** 2026-08-06
**Scope:** the 15 target profiles in `data/sites_targets.csv`
**Companion file:** `data/risk_register.csv` (machine-readable, ranked by expected cost)

---

## 0. Retrieval limitation — read this before you rely on a citation

Direct page retrieval was blocked for every host attempted in this environment
(HTTP 403 from the egress proxy — an organization policy denial, not a transient
error). Court opinions at `masscases.com`, `jud.ct.gov`, `courts.nh.gov`,
`law.justia.com` and `caselaw.findlaw.com` could not be fetched and read in
full. Every finding below was assembled through the search index, which returns
substantive extracts from those same pages.

The practical consequence: **case holdings below are reported at one remove, not
read from the slip opinion.** Every row in `data/risk_register.csv` carries an
`evidence_basis` of `Adjudicated`, `Reported` or `Inferred`, and I have kept the
distinction strictly. Before IC, counsel must pull the four opinions that carry
the most weight — *Weeks v. Palmer Motorsports Park* (Mass. Land Ct. MISC
17-000493), *Lime Rock Park, LLC v. Planning & Zoning Comm'n* (Conn. 2020, SC
20237), *Motorsports Holdings, LLC v. Town of Tamworth* (N.H. 2010, No.
2008-632), and *Brackett v. Moler Raceway Park* (Ohio App. 12th Dist.
2011-Ohio-4469) — and confirm the holdings characterized here. Budget for that:
it is a $15–25k memo, not a research project.

---

## 1. The headline number, and the correction to the plan

**The business plan says noise litigation after permits issue is "High and the
classic failure mode for this asset class." The record does not support that
sentence as written. It supports a different, more expensive sentence.**

Across the eight US road-course and club facilities examined, **zero were shut
down by a neighbor nuisance suit after permits issued.** What actually happened:

| Facility | Who sued | Theory | Outcome |
|---|---|---|---|
| Palmer Motorsports Park (MA) | **The town's own zoning-enforcement officer** | Violation of special-permit Condition #10 | Track found non-compliant; judgment Jan 14 2020 ordering mitigation + testing; contempt complaint filed Sept 20 2020; court later found mitigation compliant, testing not. **Track open.** |
| New Jersey Motorsports Park | TrackRacket (organized neighbor non-profit), 2009 | Nuisance | Settled 2011. NJMP altered PA system and **start/end times**, funded a standing Sound Committee, **and paid TrackRacket's legal fees**. City dismissed as a defendant. **Track open.** |
| Atlanta Motorsports Park (GA) | Adjacent horse-farm owners, pre-construction | **Anticipatory** nuisance, to enjoin construction | **Denied**, Nov 2010 — plaintiffs failed to show "reasonable certainty" of nuisance. Defense expert testified track noise would not affect horse behavior. **Track built.** |
| Moler Raceway Park (OH) | Adjacent residents, 2008 | Nuisance; sought damages, diminution, and **complete shutdown** | Trial court denied permanent injunction and found no nuisance. Appellate court reversed the *restrictions* the trial court imposed for want of findings and remanded. **Track open.** |
| Apex Motor Club (AZ) | Resident (rep. by a former AZ Attorney General) + a referendum committee | CUP procedurally defective; referendum on the CUP | Referendum blocked — the CUP was an **administrative, not legislative, act** and therefore not referable. Court of Appeals ruled for the club and the city; **AZ Supreme Court denied review.** Opened March 2019. |
| Club Motorsports (NH) | The town's own planning board / conservation constituency | Wetlands Conservation Ordinance; multiple appeals | Two trips to the NH Supreme Court. Court found the planning board's record "flawed." Voters later repealed the wetlands ordinance and adopted a noise ordinance by 85%. **Opened 2018 — roughly 12–15 years after inception.** |
| Monticello Motor Club (NY) | Neighbors, informally + through the Town of Thompson | Complaints; town-commissioned sound study | 2013 town study found "serious" levels on Rupp Rd, up to a **20 dB race-day increase**; a ~$1M sound barrier was called for. Club **voluntarily stopped hosting car and motorcycle club events** — a revenue concession. **Club open.** |
| Lime Rock Park (CT) | Lime Rock Protective Association + Trinity Church, 1959 | Nuisance / Sunday racing | **Permanent injunction against Sunday racing, affirmed by the Conn. Supreme Court, still in force 67 years later.** Amended 1968 to bar unmuffled racing. Re-litigated 1966, 1988, 2015–2020. Conn. Supreme Court, May 22 2020: **towns may regulate auto racing, including a Sunday ban.** |

### What this actually teaches

**a) The injunction risk is real but it is a 1950s-vintage risk, and it is
permanent when it lands.** Lime Rock is the one facility in the set carrying a
true operating injunction, and it has carried it for 67 years and lost the
attempt to lift it as recently as 2020. That is the tail: not closure, but a
permanent, court-supervised cut to the operating envelope that no subsequent
owner can buy out. Underwrite the tail as *a permanent day-of-week or
hours-of-operation cut*, not as a shutdown.

**b) The more common and more probable mechanism is the municipality, not the
neighbor.** At Palmer it was the *building inspector* who sued. At Club
Motorsports it was the *planning board*. Neighbors do not usually need to sue —
they need to persuade a code officer to enforce a permit condition the applicant
negotiated too loosely at hearing. **The permit condition you accept at the
Planning Board hearing is the instrument that will be used against you.** That
is where the money is made or lost, not in court.

**c) Pre-opening injunctions fail.** AMP and *Brackett* both confirm the
anticipatory-nuisance standard — clear and convincing evidence of reasonable
certainty — is a bar plaintiffs do not clear against a permitted road course. Do
not price a construction-stopping injunction. Price the *delay* from having to
defend one.

**d) The real cost is time, not damages.** Club Motorsports spent 12–15 years,
two Supreme Court appearances, and two town-wide ballot fights before site work.
The model assumes **33 months of entitlement.** Against the only directly
comparable Northeast private club build in the record, 33 months is optimistic
by roughly an order of magnitude. At 8.50% carry on a peak equity of $98.1M,
every incremental year of entitlement is real money and it compounds into the
carry factor `k` on the whole basis. **This is the largest single unpriced
number in the deal.**

**e) The settled outcomes converge on the same three concessions.** Hours
(NJMP start/end times; Lime Rock Sunday ban), program mix (Monticello dropping
club events; Lime Rock's unmuffled-event cap), and a standing monitoring body
(NJMP Sound Committee; Palmer's testing requirement). **That trio is your
downside operating case.** Not a shutdown — a haircut to season days, to
ancillary event revenue, and a permanent compliance cost line.

### The legislative development the plan does not reflect at all

Thirteen state legislatures have moved "right to race" nuisance-immunity bills
in the last year. **Enacted: Iowa (May 2025), North Carolina (HB 926, signed
Sept/Oct 2025), Kansas (April 2026), plus Michigan, Kentucky and Tennessee.
Oklahoma SB 1195 in 2026. Georgia's bill failed; Wisconsin's was vetoed.**

The North Carolina statute bars nuisance and takings actions by any surrounding
owner within a **three-mile radius** where the developer obtained all permits
and established a **vested right** before that owner purchased or built.
Tennessee's runs to **five miles** and additionally restrains local governments
from adopting rules that unreasonably restrict racing facility operations.

This is a first-order ranking input that is currently absent from the model:

- **TP-12-CABARRUS (NC)** and **TP-14-MAURY-QUARRY (TN)** are the only two
  targets in the pipeline sitting inside a statutory nuisance shield.
- **NY, CT, NJ, AZ, TX, FL and NV have none.** Nine of the fifteen targets have
  no statutory protection whatsoever.

**Two caveats that must go to counsel before this is treated as an asset:**

1. **Vesting sequence.** The statutes protect against owners who arrive *after*
   vesting. They do not bar an existing neighbor. TP-14 has 29 residences within
   a mile and TP-12 has 48 — those people are already there. What the statute
   *does* protect is the far more valuable thing for a merchant build: every
   future purchaser in a three- or five-mile ring, including the buyers of your
   own homesites and anyone who builds near you during a 12-year hold.
2. **Definitional fit — this is the sharp one.** The statutes define a "racing
   facility" as a place where **competitive** vehicle races are conducted. A
   Thermal-typology club running non-competitive HPDE and lapping days may sit
   *outside* the statutory definition and get nothing. **The cure is cheap:
   program a schedule of sanctioned competitive events sufficient to bring the
   facility inside the definition, and get a written opinion confirming it.**
   That is a $20–40k legal opinion protecting the single largest structural risk
   mitigant available at two sites. Do it at LOI.

### Where the prior-use defense is being over-credited

The brief asks how much protection an inherited noise floor confers. The honest
answer is **less than the plan assumes, and for a reason that is structural.**

"Coming to the nuisance" protects a facility against a plaintiff who arrived
later. **A new-build club is the newcomer.** Every neighbor at EPCAL, at the 9W
quarry, at Cumberland and at Litchfield was there first. The doctrine, which in
most modern courts is one factor rather than a bar, runs *against* us on day one
and only begins running *for* us once the club itself is the established use.
The English authority (*Coventry v. Lawrence*) required twenty years of
uninterrupted use before a right to emit could be established. A prior industrial
use does not transfer that clock to a successor operator with a different
emission profile.

What the prior use *does* confer is narrower and still worth money:

- **Character of the locality.** Nuisance is judged against the established
  character of the area. An airfield, a quarry or an operating raceway makes it
  materially harder for a plaintiff to argue that motorsport noise is out of
  character. This is a merits argument, not a bar.
- **Baseline evidence.** A pre-existing measured ambient makes the *incremental*
  dB from the club smaller, which is the number that decides these cases. This
  is the single most valuable thing a prior use gives you and it is only
  realized if you **measure the pre-acquisition ambient before you close.**
- **Zoning posture,** which is separate and real.

**The counter-example is the one that matters most.** Monticello Motor Club is a
4.1-mile road course **built on a former airport** in a rural NY county — the
exact prior-use thesis being applied to TP-01-EPCAL. It still drew a
town-commissioned sound study finding "serious" levels, a call for a ~$1M
barrier, and a voluntary surrender of club-event revenue. **The airfield history
did not prevent the outcome.** Discount the EPCAL prior-use credit accordingly.

The one place the thesis clearly does work is **The Concours Club**, built
between active runways at Miami-Opa Locka Executive Airport, where the ambient
is jet operations and the reported result is an absence of the noise
restrictions normally imposed on tracks. Note the distinction: Concours is
*inside an operating airport*, with a live, continuing noise source. EPCAL's
airfield is *closed*. A closed airfield confers character evidence; an open one
confers an actual masking ambient. Those are not the same asset.

---

## 2. Mitigants, ranked by evidence that they work

Ranked by whether the record shows them present at surviving facilities and
absent at damaged ones — not by first principles.

### Tier 1 — appears in the record at facilities that avoided the bad outcome

**1. Take the approval as a quasi-judicial act, never a legislative one.**
Apex Motor Club's referendum — which had the signatures — was killed because the
conditional use permit was an **administrative act not subject to referendum
under the Arizona Constitution.** That single structural choice defeated an
organized, funded opposition campaign outright. A map amendment or rezoning is
legislative and *is* referable in most states.

*Direct application to the pipeline:* **TP-04-CUMBERLAND, TP-05-LITCHFIELD and
TP-14-MAURY-QUARRY all carry `permitting_path = map_amendment_required`.** All
three are therefore referendum-exposed in a way that the ten special-permit
sites are not. This is not currently scored. It should be. TP-05 is the worst
case — a map amendment, a residential subdivision on the property line, 110
residences within a mile, `severe` opposition risk, and two prior failed
contracts already on the record.

**2. Commission a neutral, third-party acoustic study *before* application —
and let the town own it.** At Club Motorsports the **Tamworth Foundation**
retained HMMH to run a balanced evaluation, with reference measurements taken
from actual race vehicles at New Hampshire International Speedway and SoundPLAN
modeling of the proposed layout including earth berms. HMMH then **recommended
the property-line limits itself.** A limit that the town's own consultant
proposed is a limit the town cannot easily be persuaded to tighten later. That
project got built. Palmer, which negotiated its own Condition #10 and then had
to be told by a court what it meant, did not get that benefit.

*Cost:* a full pre-application acoustic model with reference measurements and
receptor mapping is a low six-figure item and sits inside the existing
`entitlement_budget_usd: 3500000`, which already names a noise study. **Do not
economize here.** It is the cheapest line in the deal relative to what it
protects.

**3. Write the permit condition yourself, in numbers you have measured.**
Palmer's Condition #10 required recorded noise readings within 90 days of
commencing operation. That condition — not a neighbor's lawsuit — is what put
the track in front of a judge for four years and into a contempt proceeding.
Conditions get enforced. Negotiate a condition expressed as a property-line
L-metric at a **named, surveyed measurement point** with a defined averaging
period and a defined exceedance protocol, and *never* accept a qualitative
condition or one referencing an unmeasured baseline.

**4. Earth berms before walls.** FHWA's guidance is explicit that earthen berms
work best and cost least, and that walls are chosen only where right-of-way is
short. On 400–700 acre parcels right-of-way is not short. Every one of these
sites has an earthwork budget already; **berming is a re-allocation of cut/fill,
not a new cost line, on any site with a positive cut/fill balance** —
TP-02-QUARRY-9W (850,000 cy), TP-14-MAURY (640,000 cy), TP-11-APEX (310,000 cy)
and TP-07-BRAZOS (240,000 cy) are all self-supplying. Reserve the wall budget
for the specific receptor bearings the model identifies.

**5. In-house sound enforcement with teeth.** Palmer's compliance rested on
"track-side monitoring and black flagging" being **continuously enforced** — the
court's own framing. Thompson Speedway and Atlanta Motorsports Park each run
reported facility sound limits of **103 dB**. (Measurement point unverified in
both cases; do not carry either number into a proforma or an application. This
is a research task and a named phone call, per §10.) A club by-law with a
published vehicle limit, a calibrated meter at a fixed station, and a written
black-flag/ejection protocol is close to free and is the thing that makes the
property-line number achievable on a bad day.

### Tier 2 — appears in the record, but as a response to damage rather than a preventative

**6. Physical barriers, post hoc.** Acoustiblok barrier product is documented at
both Palmer and Atlanta Motorsports Park. Both installed after opening, after
complaints. It works — Palmer's court found the physical mitigation, if
continuously maintained, "may keep the Park within Condition #10's noise
limits." But it was bought under a court order at Palmer and under HOA pressure
at AMP, which is the most expensive way to buy anything.

*Priced:* FHWA/state DOT inventory data puts noise barriers at an average
**$48.76 per square foot (2020–2022, 2022 dollars)**; Ohio DOT / VDOT figures
give **$140/LF for a 10-ft wall, $185/LF at 12 ft, $235/LF at 14 ft**, and
conventional highway noise walls at roughly **$2M per linear mile (~$379/LF)**.
For a perimeter treatment of 5,000–15,000 LF the range is **$0.7M–$3.5M** at the
DOT per-LF figures, up to **$2M–$6M** at the per-mile figure. Monticello's
reported ~$1M barrier proposal sits inside that band and cross-checks it.

**None of the fifteen site cost premiums in `sites_targets.csv` carries an
explicit acoustic mitigation line.** They should — at minimum on TP-05
(800 ft to nearest residence, 110 residences within a mile), TP-03 (1,900 ft),
TP-04 (2,100 ft), TP-12 (2,200 ft), TP-02 (2,400 ft) and TP-14 (2,600 ft).

**7. A standing joint monitoring committee.** The NJMP Sound Committee — park
officials, TrackRacket members and local citizens, meeting monthly — is the
durable output of that settlement and the reason the dispute has stayed out of
court since 2011. It is also a permanent operating cost and a permanent
constraint on program flexibility. Offer it *voluntarily at hearing* rather than
concede it in a settlement; it buys the same goodwill and you write the charter.

### Tier 3 — logical, but I found no US record of it being decisive at a road course

**8. Recorded right-to-operate covenants against neighboring land.** No instance
found in this record. The statutory route (NC/TN) has superseded it where it
exists. Where there is no statute, a recorded covenant obtained from abutters as
consideration is worth pursuing but should be priced as an acquisition cost, not
assumed.

**9. Buying the complaining neighbor.** No documented instance in the facilities
examined. Note the arithmetic against it: TP-05 has 110 residences within a
mile. This is a tool for a single motivated abutter, not a program.

**10. Buffer acreage alone.** Ambiguous. TP-11-APEX has **zero** residences
within a mile and 11,000 ft to the nearest — and that is genuinely protective.
But TP-01-EPCAL has 5,200 ft and only 18 residences within a mile, and the
closest analogue to it (Monticello) still took the hit. Distance reduces
likelihood; it does not eliminate the organized-opposition channel, which runs
through the hearing room, not the property line.

### What appears in the ones that went badly

Lime Rock: no pre-application acoustic record (1957 construction), a church and
an organized protective association within earshot, and a **Sunday** operating
pattern that gave the opposition a moral frame rather than a technical one.
Palmer: a permit condition it did not measure against before accepting.
Monticello: the town, not the applicant, commissioned the study — so the town
owned the number.

**The through-line: whoever commissions the acoustic study owns the number, and
whoever owns the number wins.**

---

## 3. Environmental and title exposure by typology

### 3.1 TP-01-EPCAL — former naval weapons industrial reserve. Three findings that change the underwriting.

**Finding 1 — the PFAS position is materially worse than "Phase I / II
required."** The Navy identified **fifteen new areas of concern for PFAS** at
the former NWIRP Calverton in 2023, concentrated **around the 10,000-foot
western runway.** Contamination of record includes VOCs, 1,4-dioxane and PFAS,
sourced to aqueous film-forming foam. As of February 2025 the Navy was reported
to be **at the beginning of the CERCLA site evaluation process** after 62
biannual restoration advisory board meetings — that is, decades in and not yet
at remedy selection. Suffolk County and the County Executive have pushed EPA for
priority Superfund designation; Suffolk County was still pressing the Navy on
the plumes in June 2026.

**The direct conflict with the model:** the parcel carries a **–$9,500,000 site
cost credit** whose stated basis is *"existing runway pavement usable as base
course."* The runway is where the PFAS AOCs are. Pulverizing and reusing
PFAS-impacted runway pavement as track base is not a credit — it is a waste
characterization problem, a potential generator liability, and, if the material
must be managed rather than reused, a cost. CLAUDE.md already notes that halving
the credit takes EPCAL's IRR from 8.8% to 8.1%. **The evidence here says model
the credit at zero until a Phase II with PFAS analytical on the runway
subgrade says otherwise.** That is a scenario, not a footnote.

*The offsetting fact, and it is a real one:* the Navy retains the CERCLA
obligation as the responsible party and has been remediating for 30+ years. DoD
puts its total PFAS investigation and cleanup liability above **$9.3 billion**
(tripled since 2022), with a broader Pentagon estimate of at least **$31
billion** since 2016. **We are not the PRP.** The exposure is not cleanup cost —
it is (i) timing, because you cannot build across an area under active CERCLA
investigation, (ii) the loss of the pavement credit, and (iii) a Superfund
listing headline landing on a luxury residential sell-out. **Item (iii) is the
one that is not in the model at all.** A merchant build selling homesites next
to a National Priorities List candidate has an absorption problem that no
remediation covenant solves.

**Finding 2 — title and control are contested.** Riverhead contracted to sell
1,644 acres at EPCAL to Calverton Aviation & Technology (Triple Five) for $40M
in 2018; the town declared the contract void in October 2023 after the IDA
denied CAT's assistance application; CAT sued in January 2024. In February 2026
Justice Reilly dismissed 16 of 17 causes of action but **let a tortious
interference with contractual relations claim proceed.** The land has been
described as "in limbo" for the duration. Any acquisition at EPCAL is an
acquisition into a live dispute with a well-capitalized competing claimant
represented by Kasowitz. **Price the title insurance affirmative coverage and
the litigation-hold delay, or wait for final judgment.**

**Finding 3 — NYSDEC has already refused the town's own subdivision here.** The
town sued DEC on 17 March 2021 over its refusal to deem the eight-lot EPCAL
subdivision application complete. The EPCAL property contains regulated
wetlands, land within the Wild, Scenic and Recreational River corridor for the
Peconic, and roughly **583 acres of maintained grassland committed as habitat
for short-eared owl and northern harrier** (512 existing plus 70.6 to be
created). Both are NY-listed species. On a 620-acre target with 560 "contiguous
developable" acres, a 583-acre grassland habitat commitment is not a constraint
at the margin — **it is potentially the entire site.** The `pct_wetlands: 0.06`
figure in the CSV does not capture this. **This is the item to resolve first at
EPCAL, before Phase II and before price.**

### 3.2 TP-04-CUMBERLAND — capped municipal landfill (NJ)

The regime is knowable and the constraint is already correctly stated in the CSV
("landfill cap cannot carry pavement — track alignment must avoid the
footprint"). The specifics:

- Closure requires a **detailed description recorded with the deed** at the
  county recording office — types, locations and depths of waste, cover depth
  and type, dates of operation — and notice that **any future disruption of the
  closed landfill requires prior NJDEP approval.**
- Caps are **Engineering Controls** under the NJDEP Site Remediation Program.
  Deed notices and groundwater Classification Exception Areas are **Institutional
  Controls** governed by N.J.A.C. 7:26C, requiring a **Remedial Action Permit**,
  periodic inspection, groundwater sampling, and **biennial
  protectiveness/certification filings** (form BRDN-001) in perpetuity.
- The deed notice extent is a mapped, public GIS layer. Anyone underwriting the
  homesite sell-out can find it in thirty seconds. **Disclosure is not optional
  and it will be priced by buyers.**

*What this means commercially:* the obligations run with the land and are
permanent. The cure is not remediation — it is **survey the deed-notice extent,
design every structure and every foot of pavement outside it, and carry the
permit compliance as a perpetual operating line.** Budget the biennial
certification and monitoring as opex, not as a one-time cost.

### 3.3 TP-15-HARDEE-PHOS — reclaimed phosphate (FL)

Two exposures, one of which the CSV names and one it does not price.

**Radiological is real and it is a sell-out problem, not a construction
problem.** Florida has 28 phosphate mines over 450,000 acres. Post-1975 mined
land is mandatory-reclamation land. The Florida Department of Health samples
soil, air and water pre-mining and post-reclamation for gamma radiation, soil
radon emanation and radium. Published research on central Florida's phosphate
district found **elevated radon (>4 pCi/L) in 8 of 27 homes built on reclaimed
phosphate-mined land**, and outdoor gamma levels significantly higher in
reclaimed than unmined areas. **A residential product on reclaimed phosphate
land requires radon-resistant construction and a disclosure position.** Manatee
County — immediately adjacent, and the county named in the target description —
requires reclaimed land to meet radiation standards under its Phosphate Mining
Code.

**Clay settling areas.** The CSV correctly requires preload/surcharge and
prohibits track alignment across them. That is the right instinct. It is not
priced separately inside the $5.9M premium.

**FDEP reclamation release is "pending" per the CSV.** Buy subject to release,
or hold back. An unreleased reclamation obligation on 680 acres is the seller's
problem until it becomes yours at closing.

### 3.4 Species — TP-08-MARION, TP-15-HARDEE, TP-10-HENDRY, TP-06-PINAL

**Gopher tortoise (TP-08, TP-15) is the one exposure in the entire pipeline with
a hard, current, per-unit market price, and it is worse than most developers
assume.** Recipient-site permittees in Florida are reported charging **up to
$8,000–$10,000 per tortoise**, up from roughly $900 when the relocation-agent
market opened, driven by a shortage of recipient sites. Reported contribution
schedules range from **$234 to $6,318 per tortoise** (Dec 2023 snapshot), and
county recipient sites publish their own fee policies. A single Indian River
County developer was reported facing **~$2 million** to relocate the tortoises
on its site.

**Do not carry this as a contingency line — carry it as a survey.** The cost is
linear in burrow count, and burrow count on 460–590 acres of sandy Florida
upland is exactly the kind of number that comes back at 40 animals or at 400.
**A pre-LOI burrow survey is a low-five-figure item that resolves a
seven-figure range.** That is the highest-return diligence dollar in the FL
portfolio.

**Florida panther (TP-10-HENDRY).** Panther Habitat Units are transacted through
mitigation banks — Big Cypress Mitigation Bank sits in southwest Hendry County
and prices PHUs, with each wetland credit reported to carry 8.96 PHUs. **I could
not source a defensible per-acre or per-PHU price and will not invent one.** The
structural point stands: TP-10 sits in the **primary zone**, which means formal
Section 7 consultation with USFWS, which means a federal timeline the county
special exception cannot shorten. The CSV's own assessment is right — *"the
binding risk is the federal species consultation, not the neighbours"* — and
the 24-month permitting estimate is the number to challenge, not the mitigation
cost.

**Sonoran desert tortoise (TP-06-PINAL)** is a survey requirement, not a listed-
species consultation; it is the mildest species exposure in the set.

### 3.5 Geotechnical — TP-08-MARION, TP-14-MAURY, TP-11-APEX

**Karst (Marion FL, Maury TN).** Compaction grouting is the standard remedy —
grout injected through steel pipes drilled to the limestone, filling from the
formation upward in 1–3 ft intervals — and it is documented as the least costly
of the available methods in west-central Florida karst. **I could not source a
credible per-acre cost and will not invent one; published USF/NCKRI work is
specifically about the difficulty of *predicting* compaction grout quantities in
sinkhole remediation.** That unpredictability *is* the finding: the quantity
risk is not estimable from desktop data.

*The cure is a scope, not a number:* a karst-specific geophysical program (GPR
plus electrical resistivity across the proposed circuit alignment, with
confirmation borings) before the alignment is fixed, so the circuit is routed
around anomalies rather than grouted through them. Route selection is free.
Grouting is not.

*The insurance angle is separate and material.* Florida insurers must offer
sinkhole coverage, but commercial policies differ sharply — most carry only
statutory catastrophic ground collapse, with true sinkhole coverage as a priced
endorsement. **A 4-mile ribbon of pavement is uninsurable against subsidence in
any practical sense; the buildings are insurable, the circuit is not.** That is
a retained risk on TP-08 and TP-14 and it should be stated to IC as such.

**Gypsiferous soils (TP-11-APEX).** Soils around Las Vegas are documented as
having very high soluble sulfate content. The engineering answer is settled:
characterize the exposure class per ASTM C1580, then specify ASTM C150 Type V
cement (≤5% C₃A) — and for severe exposure, Type V is often **insufficient
alone** and requires Class F fly ash at 25–35% replacement. **Sulfate
concentrations are not uniform across a site**, so the sampling grid matters
more than the mix design. The CSV already prices a "sulfate-resistant concrete
mix premium" inside the $7.1M premium; I could not source a defensible unit
premium to test it against. The risk here is **specification failure, not cost**
— a Type-V-only spec on a severe-exposure sub-area is a 15-year durability
problem on a circuit you cannot take out of service to repair.

### 3.6 TP-12-CABARRUS — the NC Brownfields Agreement is a genuine asset, and it travels

This is the cleanest environmental position in the pipeline and the CSV
understates it. Under the NC Brownfields Property Reuse Act (S.L. 1997-357):

- Liability protection **extends by statute to lenders, tenants, occupants and
  future owners**, provided they did not cause or contribute to the
  contamination — including any lender or fiduciary financing the remediation or
  redevelopment.
- Once the **Notice of Brownfields Property** is recorded with the Register of
  Deeds, the liability protections *and* the land use restrictions **run with the
  land.**
- The effect is to convert open-ended cleanup exposure into **defined liability**
  — which is precisely what a construction lender needs to see.

**The limitations, stated plainly:** protection is conditioned on not causing or
contributing to contamination (so construction-phase conduct matters), and
future owners inherit the **land use restrictions** — violation is the
responsibility of whoever owns at the time. **A motorsport circuit with a
residential and garage-condo component is a use change from textile-industrial.
The recorded land use restrictions must be read before LOI**, because a
restriction against residential use, against soil disturbance below a stated
depth, or against groundwater use would be fatal to the program and is not
curable at any price. That is a one-day document review. Do it first.

Combined with the Tennessee-style protection absent here but the **NC "right to
race" statute present**, and `opposition_risk = low` in the one market where a
racing facility is civic infrastructure, **TP-12 has by a wide margin the best
combined litigation-and-environmental posture in the fifteen.** Its problem is
the yield, not the risk. That deserves to be said to IC.

### 3.7 Title items

**CT PA 490 recapture (TP-03-THOMPSON, TP-05-LITCHFIELD).** Both are enrolled.
The conveyance-tax penalty on sale, transfer or change of use is **10% of fair
market value in year one of ownership/classification, declining one point per
year to 1% in year ten, and zero thereafter** (C.G.S. §12-504a et seq.). On
TP-05's $8.4M ask that is a **$840k** exposure at the top of the scale and
**~$0** if the current owner's clock has already run. **The clock is a public
record at the assessor's office and it changes the bid by up to 10%.** Confirm
the classification date before offering, on both.

**Severed mineral rights (TP-07-BRAZOS, TP-11-APEX, TP-14-MAURY,
TP-15-HARDEE).** Four sites carry severed minerals in the intake. A severed
mineral estate is generally **dominant** — the holder can access the surface to
extract. On a 4-mile fixed circuit that is not a title exception you can insure
around and live with; it is an existential surface-use problem. **The cure is a
surface waiver / non-disturbance agreement from the mineral owner, negotiated
before closing.** Cost is a negotiation, not a fee. Where the mineral owner
cannot be identified or will not sign, the site is not developable as a circuit.
This is not currently flagged in any gate.

**NY Ag District §305-a / rollback taxes** — none of the NY targets is in
agricultural classification (EPCAL is municipal industrial, 9W is a mining
parcel), so this does not bind in the current pipeline. Re-check on any new NY
intake.

---

## 4. Insurance — is $1,092,000 plausible?

**Short answer: yes in aggregate, but only just, and the composition is where
the risk sits.** The line is **12.2% of the $8.946M stabilized opex** and
**$3,212 per member per year** at the 340-member cap.

**The property test.** Insurable replacement value on the retained club, using
the config's own hard costs — clubhouse $18.275M, service/tech center $7.565M,
karting/skidpad $3.485M, paddock and pit $6.8M, FF&E $4.2M — is about **$40.3M
of structures and contents**, rising to roughly **$77M** if you insure the
circuit pavement and site infrastructure at cost, which most carriers will not
do at full replacement. Commercial property base rates run **$0.30–$0.80 per
$100 of TIV** generally, with high-risk and NY metro exposures reaching
$1.20–$3.00. That puts the property component at roughly **$120k–$620k**
depending on how much of the site works you schedule.

**Which leaves $470k–$970k for the casualty tower.** That has to carry general
liability, **participant legal liability** (a separate limit, not a GL
extension), excess/umbrella, liquor liability on a club with dining, D&O for the
club entity, hired/non-owned auto, and property-in-care for member vehicles in
the garage condos. For a facility running roughly 200–320 days with member-owned
high-performance cars, that is a plausible but **tight** number.

**Verdict: the total is the right order of magnitude and I would not move it
without a broker quote. But it is `ASSUMED`, and it is one of the assumptions
most likely to be wrong in the adverse direction.** Two reasons:

1. **Loss history prices this line, and this asset class has a body count.**
   SpeedVegas: two deaths in 2017 when a Lamborghini Aventador hit a wall and
   burned; the coroner found the instructor died on impact and the customer died
   in the fire. The track closed for 12 days and reopened. A separate suit by a
   SpeedVegas driving instructor sought a **court order closing the track** until
   safety protocols and a **track redesign** were implemented, alleging the track
   was "inherently, excessively and unnecessarily dangerous in design and
   operation" and that brakes were not properly maintained — settled
   confidentially. The Sherwood estate's wrongful-death case went to jury trial
   in **May 2022** (verdict amount not sourced; do not quote one). *This is the
   real SpeedVegas lesson and it is not a noise lesson: the theory that reaches
   the owner is **negligent track design**, and it survives a signed waiver
   because it is not a risk the participant assumed.* A named expert opinion on
   run-off, barrier and wall geometry at design stage is the mitigant, and it is
   an engineering fee, not an insurance premium.
2. **The exclusions run the wrong way by default.** Standard auto and general
   liability forms exclude "liability arising from the sponsoring or taking part
   in any organized or agreed-upon racing or speed contest," and common amateur
   formats — track days, autocross, HPDE — are excluded from ordinary auto
   policies. Coverage must be affirmatively bought through a motorsports program
   (K&K is the dominant market; Lockton and IGP also write it), where general
   liability is written with **separate limits for bodily injury to
   participants** and expanded BI definitions, with officials, drivers, crews and
   sponsors as additional insureds. **The member's own car is not covered by the
   club's policy.** Members need their own on-track physical damage cover
   (Hagerty and others write it). That is a member-experience and retention
   issue that belongs in the membership proposition, not the opex line.

**Ignore the aggregator quotes.** Small-business marketplaces quote racetrack GL
at $97–$139/month for $1M/$2M — that is a karting operator or a dirt oval, not a
4-mile road course with 340 members, a clubhouse restaurant and garage condos
full of other people's Ferraris. Cited here only to be dismissed.

**Action:** obtain a real indication from K&K or Lockton against the actual
program — track miles, member count, days of operation, event mix, whether
competitive events are run, food and beverage, and garage-condo bailee exposure.
It is a free call and it removes an `ASSUMED` from the second-largest
controllable opex line.

---

## 5. The single risk that kills each target

The composite ranking is not reproducible from this seat (no execution
environment); CLAUDE.md confirms TP-01 and TP-06 as the top two in a dead heat.
All fifteen are listed rather than a guessed top ten.

| Target | The one risk that kills it |
|---|---|
| **TP-01-EPCAL** | **The 583-acre grassland habitat commitment** (short-eared owl, northern harrier) on a 620-acre site — DEC has already refused the town's own subdivision here. PFAS on the western runway and the live Triple Five litigation are expensive; the habitat commitment is the one that means there is no site. |
| **TP-06-PINAL-303** | Water. No municipal water or sewer, `well_unproven`, ~$4.2M of deep well and package treatment in an Arizona groundwater regime. The Apex Motor Club precedent says the entitlement survives; the well may not. |
| **TP-02-QUARRY-9W** | The organized watershed constituency (`in_woh_watershed = yes`) — NYC watershed review adds a state-level intervenor with standing and no deadline, on top of a 36-month estimate. |
| **TP-03-THOMPSON** | The USTs of record. `remediation_status` says closure documentation required and it is an operating raceway — an unclosed UST on a CT motorsport site is a Transfer-Act-successor problem attached to a family operator with no next generation to manage it. |
| **TP-04-CUMBERLAND** | The map amendment. Legislative, therefore referendum-exposed, in front of NJDEP layered review, on a capped landfill, 11 miles from the state's most-litigated racetrack. Longest path in the pipeline at 42 months and the most ways to be stopped. |
| **TP-05-LITCHFIELD** | 800 feet to the nearest residence, 110 residences within a mile, a map amendment, `severe` opposition risk, two prior failed contracts — in the state whose Supreme Court affirmed in 2020 that towns may ban racing on a given day, and whose most famous track has carried a permanent injunction since 1959. **This is not a risk to mitigate. It is a pass.** |
| **TP-07-BRAZOS-XING** | Severed minerals. No zoning means no denial, but a dominant mineral estate under a fixed 4-mile circuit is not insurable around. |
| **TP-08-MARION-OCALA** | Karst. Unpredictable grout quantities under the circuit alignment plus an effectively uninsurable subsidence exposure on the pavement. The organized equestrian constituency is second — and the AMP precedent says horse-farm plaintiffs lose. |
| **TP-09-WALLER-290** | The 404 jurisdictional determination on the ditch network, on 6% floodway with high-plasticity clay. A federal permit on an otherwise as-of-right site. |
| **TP-10-HENDRY-75** | Section 7 consultation in the panther primary zone. Federal timeline, unpriced PHU mitigation, and a 24-month estimate that has no basis. |
| **TP-11-APEX-NV** | BLM right-of-way for the water and access alignment. Zero residences within a mile makes this the lowest litigation risk in the set; the federal ROW is the schedule. |
| **TP-12-CABARRUS** | The recorded Brownfields land use restrictions. If they bar residential use or soil disturbance, the program is dead and no money fixes it. If they do not, this is the best-protected site in the pipeline. **One-day document review, do it first.** |
| **TP-13-SH130** | Blackland vertisol under the circuit. Worst subgrade in the set, priced at $5.4M, on the highest ask per acre ($27,959). |
| **TP-14-MAURY-QUARRY** | The map amendment, in front of Williamson County wealth the CSV itself calls "litigation-capable." Tennessee's nuisance-immunity statute protects the *operation* and restrains local restriction — it does not get you the rezoning. |
| **TP-15-HARDEE-PHOS** | Clay settling area settlement across 680 acres of variable reclaimed overburden, with the FDEP reclamation release still pending. Radiological is a disclosure and construction-detail problem; settlement is a geometry problem, and a circuit needs geometry. |

---

## 6. What to change in the plan

1. **Rewrite the risk framing.** "Noise litigation after permits issue — High,
   the classic failure mode" is not supported. Replace with: *"Post-opening
   operating restriction — High likelihood, moderate severity. The mechanism is
   municipal enforcement of a permit condition we negotiated, not a neighbor
   suit. The tail is a permanent day-of-week or hours cut (Lime Rock, 67 years
   and counting), not closure. No US road course in the comparable set has been
   closed by neighbor litigation."*
2. **Add entitlement duration as a named risk with its own scenario.** 33 months
   against Club Motorsports' 12–15 years is the largest unpriced item in the
   deal, and it enters yield through the carry factor on the entire basis.
3. **Score `permitting_path` for referendum exposure.** Legislative approvals are
   referable; quasi-judicial ones are not. That is worth points and it currently
   scores nothing. TP-04, TP-05 and TP-14 are affected.
4. **Score state nuisance-immunity statutes.** TP-12 (NC) and TP-14 (TN) carry a
   statutory shield that the other thirteen do not. Also worth points.
5. **Add an acoustic mitigation capex line to the site cost premiums** on the six
   sites inside 2,600 ft of a residence. $0.7M–$3.5M is the sourced band.
6. **Model the EPCAL runway credit at zero in the downside case,** not at half.
7. **Get a broker indication on the insurance line.** Free, and it retires an
   assumption.

---

*Every citation in this file is registered in `data/sources.csv`, rows 4–36.*
