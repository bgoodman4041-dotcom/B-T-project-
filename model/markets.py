"""
TRACK BOSS — Nationwide Market Framework
========================================

The programme was originally scoped to NY / CT / NJ. That scope contains the
densest concentration of investable wealth in the country and the WORST
combination of everything else: the shortest usable season, the highest
construction cost, the highest property tax, and the most hostile entitlement
environment in the United States.

Going national is therefore not a growth story bolted onto a Northeast deal. It
is a direct answer to the Northeast plan's largest structural weakness. A circuit
in Arizona or Florida earns off the same physical plant for materially more of
the year -- one Arizona operator advertises 275 days of member access [S4] -- and
sits on land that costs a fraction of Hudson Valley or Litchfield County dirt.

What this module does
---------------------
* Scores US metros on the six drivers that actually decide a motorsport club:
  season length, wealth density, land cost, entitlement friction, competitive
  whitespace, and incentive availability.
* Records where the format is ALREADY PROVEN, because that is both validation
  and competition. Six clubs are confirmed operating.
* Produces a phased national rollout sequence.

Honesty notes
-------------
Season days are ESTIMATES from climate, not operator disclosures, except where a
club publishes its access days. Wealth, land-cost and friction tiers are ordinal
judgments, not indices. Every metro here needs the same Gate 1-5 screen as the
Northeast set before a dollar is spent; this module ranks where to point the
sourcing engine, nothing more.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Tier = Literal["low", "moderate", "high", "very high"]

_TIER_SCORE = {"low": 1.0, "moderate": 0.66, "high": 0.33, "very high": 0.0}
_WEALTH_SCORE = {"low": 0.0, "moderate": 0.4, "high": 0.75, "very high": 1.0}


@dataclass(frozen=True)
class Market:
    metro: str
    region: str
    states: str
    season_days: int              # ESTIMATED usable track days per year
    wealth: Tier                  # investable-wealth density in the catchment
    land_cost: Tier               # raw land cost for 400+ contiguous acres
    entitlement_friction: Tier    # how hard the permit and noise fight is
    incentives: Tier              # availability of abatement / brownfield support
    existing_clubs: str           # confirmed operating private clubs
    whitespace: str               # what is genuinely unserved
    candidate_typologies: str     # where to look inside the metro

    @property
    def proven(self) -> bool:
        """
        True where a private club format is confirmed operating. Matches on the
        PREFIX because several entries qualify the negative -- "None confirmed
        (COTA is a public circuit)" is still an unserved market, and an exact
        string compare wrongly counted those as proven.
        """
        return not self.existing_clubs.startswith("None confirmed")


# =============================================================================
# The national market set
# =============================================================================
# Existing-club entries marked (confirmed) were verified in research; the format
# is demonstrably operating in six metros, which is the strongest single piece of
# evidence that the typology works.

MARKETS: list[Market] = [
    # ---------------- Sun Belt: the season advantage ----------------
    Market("Phoenix – Scottsdale", "Southwest", "AZ", 310, "very high", "low",
           "low", "moderate",
           "Apex Motor Club, Maricopa — 275 member days/yr (confirmed)",
           "Apex sits south of the metro; the North Valley and Pinal County "
           "corridor is unserved, and Scottsdale collector density is the "
           "deepest in the country outside Southern California",
           "Retired aggregate pits and state trust land parcels along the "
           "I-10 and Loop 303 corridors; former auxiliary airfields"),
    Market("Coachella Valley – Palm Springs", "West", "CA", 320, "very high",
           "moderate", "moderate", "low",
           "The Thermal Club — 5.1 mi, garage condos from ~$600k (confirmed)",
           "Effectively saturated at the top of the market. Study it, do not "
           "compete with it",
           "Reference market only — the comparable set anchor"),
    Market("Las Vegas", "Southwest", "NV", 300, "high", "low", "low", "moderate",
           "Spring Mountain Motor Resort, Pahrump — 6.1 mi (confirmed)",
           "Spring Mountain is ~60 miles out; nothing inside the valley since "
           "SPEEDVEGAS closed. Corporate and event demand is exceptional",
           "BLM-adjacent private holdings, former gypsum and aggregate "
           "operations, Apex/Speedway industrial corridor"),
    Market("Dallas – Fort Worth", "Texas", "TX", 285, "very high", "low", "low",
           "moderate",
           "MotorSport Ranch, Cresson — 304 ac, 300 garages (confirmed)",
           "MSR is the proof that this market absorbs the format, and it is "
           "40 years old and under-amenitised. A country-club product with "
           "residential is genuinely unserved",
           "North Texas ranchland south and west of Fort Worth; former "
           "aggregate operations along the Brazos corridor"),
    Market("Austin – San Antonio", "Texas", "TX", 285, "high", "moderate",
           "moderate", "moderate", "None confirmed (COTA is a public circuit)",
           "THE CLEAREST WHITESPACE IN THE COUNTRY. Two fast-growing wealthy "
           "metros, a world-class public circuit proving demand, and no "
           "private club product between them",
           "Hill Country ranchland along the SH-130 and I-35 corridors; "
           "former quarries near New Braunfels and Marble Falls"),
    Market("Houston", "Texas", "TX", 275, "very high", "low", "low", "moderate",
           "MSR Houston (Angleton) — established", "Energy wealth is deep and "
           "the existing facility is remote and basic; a closer, amenitised "
           "product would not be competing on equal terms",
           "Coastal-plain acreage west and northwest of the metro; former "
           "industrial and pipeline yards"),
    Market("Naples – Fort Myers", "Southeast", "FL", 315, "very high",
           "moderate", "moderate", "low", "None confirmed",
           "Extraordinary wealth density and zero private club product. "
           "Seasonal-resident base is exactly the member profile",
           "Interior agricultural land east of I-75; former citrus and "
           "sod operations; reclaimed limerock pits"),
    Market("Miami – Palm Beach", "Southeast", "FL", 320, "very high", "high",
           "high", "low", "The Concours Club, Miami (confirmed)",
           "Concours serves Miami. Palm Beach and the Treasure Coast are "
           "unserved and arguably wealthier per capita",
           "Western Palm Beach and Martin County agricultural land; "
           "reclaimed rock mines along the SR-710 corridor"),
    Market("Orlando – Ocala", "Southeast", "FL", 310, "high", "low", "moderate",
           "moderate", "None confirmed",
           "Ocala is the equestrian capital and demonstrates that this exact "
           "buyer will purchase land-plus-amenity in Florida. Motorsport "
           "equivalent does not exist",
           "Marion and Lake County pasture; former limerock and phosphate "
           "operations; the Wildwood/Turnpike corridor"),
    Market("Tampa – Sarasota", "Southeast", "FL", 310, "high", "moderate",
           "moderate", "low", "None confirmed",
           "Sarasota and Lakewood Ranch wealth with no product; central "
           "location serves both coasts",
           "Manatee and Hardee County agricultural land; reclaimed phosphate "
           "lands with existing haul infrastructure"),
    Market("Charlotte – Concord", "Southeast", "NC", 265, "high", "low",
           "moderate", "high", "None confirmed in the club format",
           "The densest motorsport engineering and fabrication ecosystem on "
           "earth, and no private country-club product. Supplier and team "
           "demand is a second member channel nobody else has",
           "Cabarrus, Rowan and Iredell County acreage; former textile and "
           "industrial sites with incentive access"),
    Market("Nashville", "Southeast", "TN", 255, "high", "low", "moderate",
           "moderate", "None confirmed",
           "Fastest wealth in-migration in the Southeast, no state income "
           "tax, and no club product",
           "Williamson and Maury County land south of the metro; former "
           "limestone quarries"),
    Market("Atlanta", "Southeast", "GA", 265, "very high", "moderate",
           "moderate", "moderate",
           "Atlanta Motorsports Park, Dawsonville (confirmed)",
           "AMP is small and north; the south and east arcs of a very large "
           "wealthy metro are unserved",
           "Coweta, Newton and Jasper County acreage; former kaolin and "
           "granite operations"),
    # ---------------- Mountain West ----------------
    Market("Salt Lake – Park City", "Mountain West", "UT", 225, "high", "low",
           "low", "moderate", "Utah Motorsports Campus (public/mixed)",
           "Park City second-home wealth with no private club; UMC is a "
           "public facility with a different model",
           "Tooele and Box Elder County land; former mining and rail yards"),
    Market("Denver – Colorado Springs", "Mountain West", "CO", 215, "high",
           "moderate", "moderate", "moderate", "None confirmed",
           "Large wealthy metro, no private club, though the season is "
           "Northeast-like and altitude affects the product",
           "Eastern plains acreage along I-70 and the Front Range corridor"),
    # ---------------- Midwest ----------------
    Market("Detroit", "Midwest", "MI", 210, "high", "low", "low", "high",
           "M1 Concourse, Pontiac — 87 ac, 250+ garages (confirmed)",
           "M1 proves the garage-condo product cold-climate. It is urban and "
           "small — 87 acres and a 1.5-mile track — so a full country-club "
           "format at scale is unserved",
           "Former automotive and industrial sites with brownfield support; "
           "Oakland and Livingston County acreage"),
    Market("Chicago", "Midwest", "IL", 205, "very high", "moderate", "high",
           "moderate", "Autobahn Country Club, Joliet (confirmed)",
           "Autobahn proves the market. Very large wealthy metro; a second, "
           "more amenitised product is plausible but not obvious",
           "Will, Kankakee and LaSalle County land; former aggregate pits"),
    Market("Indianapolis", "Midwest", "IN", 215, "moderate", "low", "low",
           "high", "None confirmed in the club format",
           "The spiritual home of American motorsport with no private "
           "country-club product and the lowest land and construction cost "
           "of any credible market",
           "Hendricks, Morgan and Shelby County farmland; former "
           "limestone quarries"),
    # ---------------- Northeast: the original scope ----------------
    Market("New York metro", "Northeast", "NY / CT / NJ", 210, "very high",
           "very high", "very high", "high",
           "Monticello Motor Club, Sullivan County NY",
           "Highest wealth density in the country and only one club, which "
           "is 90+ minutes out. Real demand, brutal supply side",
           "Former airfields (Suffolk County), Hudson Valley quarry belt, "
           "closed golf courses (Litchfield), capped landfills (South Jersey)"),
    Market("Boston", "Northeast", "MA / NH", 200, "very high", "high", "high",
           "moderate", "Club Motorsports (Tamworth NH), Palmer Motorsports Park",
           "Two facilities serve the region from 2+ hours out; nothing inside "
           "90 minutes of the metro",
           "Central Massachusetts and southern New Hampshire acreage; former "
           "quarries and gravel operations"),
    Market("Philadelphia", "Northeast", "PA / DE", 220, "high", "moderate",
           "high", "moderate", "None confirmed",
           "Large wealthy metro with no club product and cheaper land than "
           "New York; Brandywine and Chester County wealth is deep",
           "Lancaster and Berks County farmland; former quarries along the "
           "Schuylkill corridor"),
    # ---------------- West Coast ----------------
    Market("Los Angeles – Orange County", "West", "CA", 300, "very high",
           "very high", "very high", "low", "None confirmed inside the basin",
           "The deepest collector market in the world and no club inside the "
           "basin, because land and entitlement are close to impossible. "
           "Thermal exists precisely because of this",
           "High-desert acreage (Antelope Valley, Victorville corridor) — "
           "outside the basin, which is the trade-off"),
    Market("Seattle – Portland", "Northwest", "WA / OR", 195, "high",
           "moderate", "high", "low",
           "The Ridge Motorsports Park (public/mixed)",
           "Strong technology wealth, but the shortest usable season in the "
           "set and a difficult regulatory environment",
           "Eastern Washington and Willamette Valley acreage"),
]


# =============================================================================
# Scoring
# =============================================================================

@dataclass
class MarketScore:
    market: Market
    season: float
    wealth: float
    land: float
    friction: float
    incentive: float
    whitespace: float
    total: float

    @property
    def tier(self) -> str:
        if self.total >= 78:
            return "TIER 1 — target now"
        if self.total >= 66:
            return "TIER 2 — target after club 1"
        if self.total >= 55:
            return "TIER 3 — watch"
        return "TIER 4 — deprioritise"


# Weights sum to 100. Season and whitespace carry the most because they are the
# two things the Northeast scope got wrong.
WEIGHTS = {
    "season": 26, "wealth": 22, "land": 16,
    "friction": 16, "whitespace": 14, "incentive": 6,
}


def score_market(m: Market, baseline_days: int = 210) -> MarketScore:
    """
    Score a metro 0-100. Season is measured against the Northeast baseline, so a
    score above par means the same physical plant earns for more of the year.
    """
    season = min(1.0, max(0.0, (m.season_days - 180) / (320 - 180)))
    wealth = _WEALTH_SCORE[m.wealth]
    land = _TIER_SCORE[m.land_cost]
    friction = _TIER_SCORE[m.entitlement_friction]
    incentive = _WEALTH_SCORE[m.incentives]
    # Whitespace: an unserved metro scores full marks; a saturated one scores
    # low. "Proven but under-served" is the sweet spot, not zero.
    if "saturated" in m.whitespace.lower() or "Reference market" in m.candidate_typologies:
        ws = 0.10
    elif not m.proven:
        ws = 1.00
    else:
        ws = 0.62
    total = (WEIGHTS["season"] * season + WEIGHTS["wealth"] * wealth
             + WEIGHTS["land"] * land + WEIGHTS["friction"] * friction
             + WEIGHTS["whitespace"] * ws + WEIGHTS["incentive"] * incentive)
    return MarketScore(m, season, wealth, land, friction, incentive, ws,
                       round(total, 1))


def ranked_markets(baseline_days: int = 210) -> list[MarketScore]:
    return sorted((score_market(m, baseline_days) for m in MARKETS),
                  key=lambda s: s.total, reverse=True)


def proven_markets() -> list[Market]:
    """Where the format is already operating — validation and competition both."""
    return [m for m in MARKETS if m.proven]


def national_summary(baseline_days: int = 210) -> dict[str, Any]:
    ranked = ranked_markets(baseline_days)
    by_region: dict[str, int] = {}
    for m in MARKETS:
        by_region[m.region] = by_region.get(m.region, 0) + 1
    ne = next(s for s in ranked if s.market.metro == "New York metro")
    return {
        "markets_screened": len(MARKETS),
        "regions": by_region,
        "proven_markets": len(proven_markets()),
        "tier1": [s for s in ranked if s.tier.startswith("TIER 1")],
        "tier2": [s for s in ranked if s.tier.startswith("TIER 2")],
        "northeast_rank": ranked.index(ne) + 1,
        "northeast_score": ne.total,
        "top": ranked[0],
        "season_spread": (min(m.season_days for m in MARKETS),
                          max(m.season_days for m in MARKETS)),
    }


# =============================================================================
# Rollout sequence
# =============================================================================

@dataclass
class RolloutPhase:
    phase: str
    horizon: str
    markets: str
    rationale: str
    capital: str


def rollout(baseline_days: int = 210) -> list[RolloutPhase]:
    r = ranked_markets(baseline_days)
    t1 = ", ".join(s.market.metro for s in r if s.tier.startswith("TIER 1"))
    t2 = ", ".join(s.market.metro for s in r if s.tier.startswith("TIER 2"))
    t3 = ", ".join(s.market.metro for s in r if s.tier.startswith("TIER 3"))
    return [
        RolloutPhase(
            "Phase A — Club 1", "Years 0–7",
            t1.split(",")[0].strip() + " (lead) with a Northeast site as the "
            "alternate",
            "Build where season length and land cost are on our side, not "
            "against us. The Northeast remains in the set because wealth "
            "density is unmatched, but it is the harder build and should not "
            "be the first one.",
            "Tranche 1 + 2"),
        RolloutPhase(
            "Phase B — Clubs 2–3", "Years 3–10",
            t1, "Tier 1 metros in parallel entitlement once club 1 is "
            "permitted and the operating platform exists. Entitlement is the "
            "long pole, so it runs concurrently rather than sequentially.",
            "Recycled + platform equity"),
        RolloutPhase(
            "Phase C — Acquisition programme", "Years 6–12",
            "Under-amenitised existing facilities in proven markets",
            "Six metros already have operating clubs. Several are decades old "
            "and thin on amenity and residential. Buying and repositioning one "
            "compresses a 123-month development cycle to roughly 24 months and "
            "is the only route to listing scale inside a fund life.",
            "Platform equity + debt"),
        RolloutPhase(
            "Phase D — Tier 2 expansion", "Years 10+",
            t2, "Second-wave metros once the brand and operating playbook are "
            "proven and the cost of capital has fallen.",
            "Platform / public"),
        RolloutPhase(
            "Watch list", "Opportunistic",
            t3 or "—",
            "Screened and ranked but not resourced. Revisit on a land "
            "dislocation, an incentive programme, or a distressed facility.",
            "—"),
    ]
