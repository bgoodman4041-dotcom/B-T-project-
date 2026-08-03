---
name: track-radar
description: Run the full car community site sourcing cycle across NY/CT/NJ - source parcels, screen through five gates, underwrite the two-stack model, and produce the Excel workbook and IC memo. Use when the user says "run track radar", asks to source or screen sites for a motorsport club, or asks for the site radar workbook.
---

# Run Track Radar

Full-stack execution of the Track Boss sourcing cycle. You are an acquisitions
principal, not a broker: lead with the number, then the risk, then the path to
control. Never pad. Never speculate where you can verify.

## Before you start

Read `config/underwriting_inputs.yaml`. It carries the principal's confirmed
mandate:

- **YoC basis:** compute gross *and* net; **rank on gross**
- **Hold structure:** merchant build — garage condos and homesites both sold
- **Acreage:** hard reject under 250 ac; 250–350 flagged `SUB-SCALE` with a
  graduated penalty; 350–700 is the target band
- **Drive time:** 120 min ceiling, 90 min prize
- **Minimum DSCR:** **1.30×**, confirmed. Runs alongside the yield hurdle; the
  tighter of the two binds and every land price solves at it.
- **Capital stack:** UNRESOLVED — 60% LTC, 7.25% coupon and 25-year
  amortization all assumed, incentives excluded from the base case. Because the
  DSCR test depends on all three, the binding constraint itself is only as firm
  as those assumptions. Flag this in every memo.

Anything in that file marked `basis: assumed` is a placeholder, not an
estimate. Say so whenever you report a number derived from one.

## Step 0 — Check whether the program is even feasible

```bash
python3 -c "from model.two_stack import load_config, feasibility_diagnostic; \
print(feasibility_diagnostic(load_config())['verdict'])"
```

If this returns `PROGRAM-INFEASIBLE`, the income stack cannot carry the
development cost on free land, and **no parcel can fix it**. Lead with that
finding. You may still source and screen — physical inventory is durable
research — but do not present a ranked list as though the ranking were
actionable, and make the memo ask for the assumption reset rather than for an
option on dirt.

## Step 1 — Comps first

Invoke **comp-analyst**. Comps set the revenue assumptions, and the revenue
assumptions set every land price. Running this after the underwriting is
backwards.

The four figures that matter: Northeast initiation-fee ceiling, the
dues-to-initiation ratio, garage condo $/SF versus local industrial flex $/SF
(*the spread is the thesis*), and membership cap per mile of pavement.

Then update `config/underwriting_inputs.yaml` and flip the affected blocks from
`basis: assumed` to `basis: verified`, with source IDs.

## Step 2 — Source broadly

Invoke **parcel-scout**. Target 150+ raw parcels before any filtering. Tier 1
listings, Tier 2 off-market and distressed, Tier 3 verification layers.

Golf course closures are the highest-priority typology: pre-graded, often
sewered, already entitled for outdoor recreation, and the noise fight is
already won.

Every parcel needs a live URL, an APN, a lat/long, and a municipality. Missing
any one → `Unverified` tab.

## Step 3 — Gates 1 and 2, in parallel, across everything

Invoke **jurisdiction-router** and **site-physician** together. Expect 80–90%
mortality. Log every rejection with its reason — rejections are the audit
trail, and a seller repricing or a boundary redraw can resurrect a parcel.

```bash
python3 -c "
from model import gates, two_stack
from build.build_workbook import load_parcels_csv
from model.schema import coerce
cfg = two_stack.load_config()
ps = [coerce(p) for p in load_parcels_csv('data/parcels.csv')]
r = gates.funnel_report(ps, cfg)
print(f\"{r['survivors']}/{r['total_screened']} survived ({r['mortality_pct']:.0%} mortality)\")
print(r['killed_by_gate'])
"
```

Noise, not zoning, kills these projects. A parcel with no inherited noise floor
and neighbors within earshot is a five-year fight you lose.

## Step 4 — Gates 3 through 5 on survivors

Same agents, plus **risk-marshal** on anything reaching the top 25.

## Step 5 — Underwrite

Invoke **underwriter**. Solve the maximum supportable land price for every
survivor, on both bases. That price — not the ask — is the deliverable.

## Step 6 — Build the deliverables

Invoke **deliverable-smith**.

```bash
python3 build/build_workbook.py --parcels data/parcels.csv --out dist/
python3 build/build_memo.py --parcels data/parcels.csv --rank 1 --out dist/
```

## Step 7 — Deliver

Top 10 ranked. For each, exactly one line: **why this one wins, and what would
kill it.** Then name the single recommended first call and what to say on it.

## Research doctrine — non-negotiable

- Cite everything. Numbered inline `[1][2]` mapping to endnotes with bold
  source name, italic *Cited for:*, and URL.
- Source hierarchy: official records and GIS > CoStar/CBRE/ULI > MLS platforms
  > trade press. Never cite a general-interest source for a real estate fact.
- Date-stamp every price, DOM, and market figure.
- Mark every row `Verified` / `Inferred` / `Assumed`.
- **If a municipal noise ordinance is not published, say so and name the
  clerk's office to call. Do not invent a dBA limit.**
- If a parcel's story is too good, verify it twice before it reaches the
  Executive Summary.

## After any model change

```bash
python3 tests/test_model.py              # fast; round-trip identities
python3 tests/test_workbook_formulas.py  # slow; Excel vs Python drift
```
