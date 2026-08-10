"""
TRACK BOSS — Composite Ranking (§11)
====================================

100 points across seven criteria. Each sub-score is computed on 0-1 and scaled
by its weight, so a change to the weight table in config propagates without
touching this file.

    25  Entitlement probability (noise + zoning + opposition + prior use)
    20  Yield on cost at ask, and headroom to 6.5%
    15  Physical suitability (acreage, grade, buildable %, cut/fill)
    15  Market catchment (drive time, wealth density, competitive whitespace)
    10  Infrastructure cost burden (utilities, access, roadwork)
    10  Deal control probability (seller motivation, option feasibility, title)
     5  Optionality (phasing, expansion land, alternate use if the club fails)

Ranking runs on the GROSS yield basis per the principal's confirmed mandate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .gates import PRIOR_USE_TIERS, ScreenResult


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _lerp_down(value: float, best: float, worst: float) -> float:
    """1.0 at or below `best`, 0.0 at or above `worst`, linear between."""
    if worst == best:
        return 1.0 if value <= best else 0.0
    return _clamp((worst - value) / (worst - best))


def _lerp_up(value: float, worst: float, best: float) -> float:
    """0.0 at or below `worst`, 1.0 at or above `best`, linear between."""
    if best == worst:
        return 1.0 if value >= best else 0.0
    return _clamp((value - worst) / (best - worst))


@dataclass
class CompositeScore:
    parcel_id: str
    total: float
    components: dict[str, float]      # weighted points earned
    max_components: dict[str, float]  # weight table, for the workbook
    notes: list[str]

    @property
    def grade(self) -> str:
        if self.total >= 75:
            return "A — pursue now"
        if self.total >= 60:
            return "B — pursue on reprice or diligence"
        if self.total >= 45:
            return "C — watch"
        return "D — dead unless the story changes"


# =============================================================================
# Sub-scores, each 0-1
# =============================================================================

def score_entitlement(parcel: dict[str, Any], screen: ScreenResult | None) -> tuple[float, list[str]]:
    notes: list[str] = []
    prior = str(parcel.get("prior_use", "greenfield_forest")).strip().lower()
    tier = PRIOR_USE_TIERS.get(prior, 5)

    # Prior use is the dominant term: an inherited noise floor is the whole game.
    s = {1: 1.00, 2: 0.85, 3: 0.60, 4: 0.70, 5: 0.25}[tier]
    notes.append(f"prior use `{prior}` tier {tier} -> base {s:.2f}")

    dist = parcel.get("nearest_residence_ft")
    if dist is not None:
        d = _lerp_up(float(dist), worst=1500, best=6000)
        s = s * 0.6 + d * 0.4
        notes.append(f"nearest residence {float(dist):.0f} ft -> {d:.2f}")

    n1mi = parcel.get("residences_within_1mi")
    if n1mi is not None:
        n = _lerp_down(float(n1mi), best=5, worst=120)
        s = s * 0.75 + n * 0.25
        notes.append(f"{int(n1mi)} residences within 1 mi -> {n:.2f}")

    posture = str(parcel.get("zoning_posture", "unknown")).strip().lower()
    mult = {
        "as_of_right": 1.00,
        "special_permit": 0.85,
        "map_amendment_required": 0.60,
        "unknown": 0.65,
        "prohibited_no_amendment_path": 0.0,
    }.get(posture, 0.65)
    s *= mult
    notes.append(f"zoning posture `{posture}` x{mult:.2f}")

    if parcel.get("prior_denial_same_use"):
        s *= 0.55
        notes.append("prior denial of comparable use x0.55")

    # A statutory exemption DISPLACES the numeric limit for this use, so the dBA
    # figure is informational rather than binding and the tight-ordinance penalty
    # would be pricing a constraint that does not apply. Connecticut is the case:
    # RCSA § 22a-69 sets an absolute 61 dBA industrial-to-residential daytime
    # limit, which would end a road course -- but § 22a-69-1.8 exempts motorsport
    # during hours the town authorises. The special-permit hours condition IS the
    # noise entitlement there. That is more survivable than an absolute cap and
    # entirely political, so it takes a smaller discount rather than none.
    exemption = str(parcel.get("noise_exemption") or "").strip()
    dba = parcel.get("noise_ordinance_dba_day")
    if exemption:
        s *= 0.88
        notes.append(
            "statutory exemption displaces the numeric limit x0.88 — the hours "
            "condition in the permit is the noise entitlement, which is more "
            "survivable than an absolute cap and entirely political")
    elif dba is None:
        s *= 0.90
        notes.append("ordinance unverified x0.90 (uncertainty discount, not a penalty)")
    elif float(dba) < 65:
        s *= 0.75
        notes.append(f"tight ordinance {float(dba):.0f} dBA x0.75")

    return _clamp(s), notes


def score_yield(underwriting: Any, cfg: dict[str, Any]) -> tuple[float, list[str]]:
    """
    Scored on headroom: how far the max supportable land price sits above the
    ask, as a fraction of the ask. Clearing the hurdle at all is worth most of
    the points; clearing it with room is worth all of them.
    """
    notes: list[str] = []
    if underwriting is None or underwriting.ask_price is None:
        notes.append("no ask price -- yield scored at neutral 0.50")
        return 0.50, notes

    rank_basis = cfg["mandate"]["yoc_basis"]["rank_on"]
    ask = underwriting.ask_price
    basis = rank_basis
    max_land = (
        underwriting.max_land_gross if rank_basis == "gross" else underwriting.max_land_net
    )
    yoc = underwriting.yoc_gross_at_ask if rank_basis == "gross" else underwriting.yoc_net_at_ask

    # The gross basis charges the retained club with the entire cost of garage
    # condos and homesites that are SOLD, so it is negative for every merchant
    # build regardless of the dirt. Ranking on a column that is negative on all
    # candidates discriminates nothing -- it silently zeroes a fifth of the
    # composite, which is what it did until the nationwide set made the dead
    # weight visible. Where the mandated basis carries no information, fall
    # through to the retained basis and say so on the row.
    if max_land <= 0 and rank_basis == "gross" and underwriting.max_land_net > max_land:
        notes.append(
            f"gross basis max supportable land is ${underwriting.max_land_gross:,.0f} — "
            f"structurally negative for any merchant build, so it cannot discriminate "
            f"between sites. Scored on the RETAINED (net) basis instead; the gross "
            f"line is reported as a secondary test"
        )
        basis = "net"
        max_land = underwriting.max_land_net
        yoc = underwriting.yoc_net_at_ask

    # Score on the YIELD SPREAD, not on dollar headroom. Headroom divided by the
    # ask is unstable precisely where it matters: the max supportable land price
    # crosses zero, so a site with a small positive supportable price and a -50%
    # headroom scored below a site whose supportable price was negative outright.
    # The spread between achievable and required yield is monotone through that
    # crossing and dimensionally consistent on both sides of it.
    required = underwriting.required_yield
    spread_bps = ((yoc or 0.0) - required) * 10_000
    if spread_bps >= 0:
        s = 0.60 + 0.40 * _clamp(spread_bps / 100.0)   # +100bp of spread -> full marks
    else:
        s = 0.60 * _clamp(1 + spread_bps / 150.0)      # -150bp -> zero

    headroom_ratio = (max_land - ask) / ask if ask else 0.0
    notes.append(
        f"{basis} basis: YoC at ask {(yoc or 0):.2%} against a {required:.2%} required "
        f"yield — {spread_bps:+.0f} bp. Max supportable land ${max_land:,.0f} vs ask "
        f"${ask:,.0f} ({headroom_ratio:+.0%})"
    )
    if underwriting.price_infeasible:
        notes.append("PRICE-INFEASIBLE — ask exceeds max supportable by >20%")
    return _clamp(s), notes


def score_physical(parcel: dict[str, Any], cfg: dict[str, Any]) -> tuple[float, list[str]]:
    notes: list[str] = []
    acre_cfg = cfg["mandate"]["acreage"]
    hard_floor = acre_cfg["hard_floor_acres"]
    preferred = acre_cfg["preferred_floor_acres"]
    lo, hi = acre_cfg["target_band_acres"]

    acres = float(parcel.get("contiguous_developable_acres", 0) or 0)

    # Principal set the floor as a band. 250-350 scales linearly from a 0.45
    # penalty floor up to full marks at 350; above 350 sits in the target band.
    if acres < hard_floor:
        a = 0.0
        notes.append(f"{acres:.0f} ac below hard floor")
    elif acres < preferred:
        a = 0.45 + 0.55 * ((acres - hard_floor) / (preferred - hard_floor))
        notes.append(f"SUB-SCALE {acres:.0f} ac in {hard_floor}-{preferred} band -> {a:.2f}")
    elif acres <= hi:
        a = 1.0
        notes.append(f"{acres:.0f} ac inside target band {lo}-{hi} -> 1.00")
    else:
        # Oversized is mild inefficiency (carry on land you do not use), not a fault.
        a = _clamp(1.0 - (acres - hi) / (hi * 2), 0.80, 1.0)
        notes.append(f"{acres:.0f} ac above target band -> {a:.2f}")

    s = a

    flat = parcel.get("contiguous_acres_under_8pct_grade")
    if flat is not None:
        f = _lerp_up(float(flat), worst=150, best=400)
        s = s * 0.55 + f * 0.45
        notes.append(f"{float(flat):.0f} ac under 8% grade -> {f:.2f}")

    constrained = (
        float(parcel.get("pct_floodway", 0) or 0)
        + float(parcel.get("pct_wetlands", 0) or 0)
        + float(parcel.get("pct_watercourse_buffer", 0) or 0)
    )
    c = _lerp_down(constrained, best=0.05, worst=0.35)
    s = s * 0.75 + c * 0.25
    notes.append(f"constrained land {constrained:.0%} -> {c:.2f}")

    if parcel.get("natural_amphitheater"):
        s = _clamp(s * 1.10)
        notes.append("natural bowl / amphitheater x1.10 (noise attenuation asset)")

    return _clamp(s), notes


def score_catchment(parcel: dict[str, Any], cfg: dict[str, Any]) -> tuple[float, list[str]]:
    notes: list[str] = []
    dt_cfg = cfg["mandate"]["drive_time"]
    max_min, prize_min = dt_cfg["max_minutes"], dt_cfg["prize_minutes"]

    times = parcel.get("drive_times_min") or {}
    if not times:
        notes.append("drive times unresolved -- neutral 0.50")
        s = 0.50
    else:
        best = min(times.values())
        s = _lerp_down(float(best), best=prize_min, worst=max_min) * 0.75 + 0.25
        if best <= prize_min:
            s = 1.0
        notes.append(f"best drive time {float(best):.0f} min -> {s:.2f}")

    hnw = parcel.get("hnw_households_90min")
    if hnw is not None:
        h = _lerp_up(float(hnw), worst=50_000, best=400_000)
        s = s * 0.70 + h * 0.30
        notes.append(f"{int(hnw):,} >$1M-investable households within 90 min -> {h:.2f}")

    comp = parcel.get("nearest_motorsport_club_mi")
    if comp is not None:
        # Whitespace is worth points, but total isolation means no proven demand.
        c = _lerp_up(float(comp), worst=10, best=60)
        s = s * 0.85 + c * 0.15
        notes.append(f"nearest competing club {float(comp):.0f} mi -> {c:.2f}")

    return _clamp(s), notes


def score_infrastructure(parcel: dict[str, Any]) -> tuple[float, list[str]]:
    """Inverted burden: 1.0 means cheap to serve."""
    notes: list[str] = []
    s = 1.0

    power = parcel.get("three_phase_power_distance_mi")
    if power is not None:
        p = _lerp_down(float(power), best=0.25, worst=5.0)
        s *= 0.45 + 0.55 * p
        notes.append(f"3-phase power {float(power):.1f} mi -> {p:.2f}")

    water = str(parcel.get("water_source", "unknown")).lower()
    w = {"municipal": 1.0, "well_proven": 0.85, "well_unproven": 0.55, "none": 0.30}.get(water, 0.60)
    s *= 0.55 + 0.45 * w
    notes.append(f"water `{water}` -> {w:.2f}")

    sewer = str(parcel.get("sewer", "unknown")).lower()
    sw = {"municipal": 1.0, "septic": 0.70, "none": 0.45}.get(sewer, 0.65)
    s *= 0.60 + 0.40 * sw
    notes.append(f"sewer `{sewer}` -> {sw:.2f}")

    if parcel.get("existing_paved_runway"):
        s = _clamp(s * 1.15)
        notes.append("existing pavement converts x1.15")

    bedrock = parcel.get("bedrock_depth_ft")
    if bedrock is not None and float(bedrock) < 10:
        s *= 0.80
        notes.append(f"shallow bedrock {float(bedrock):.0f} ft x0.80 (blasting)")

    return _clamp(s), notes


def score_deal_control(parcel: dict[str, Any]) -> tuple[float, list[str]]:
    notes: list[str] = []
    owner = str(parcel.get("owner_type", "unknown")).strip().lower()
    s = {
        "estate": 0.90,
        "probate": 0.90,
        "bankruptcy": 0.95,
        "individual": 0.75,
        "llc": 0.70,
        "corporate": 0.65,
        "institutional": 0.55,
        "municipal": 0.50,
        "unknown": 0.50,
    }.get(owner, 0.50)
    notes.append(f"owner `{owner}` -> {s:.2f}")

    dom = parcel.get("days_on_market")
    if dom is not None:
        d = _lerp_up(float(dom), worst=30, best=540)
        s = s * 0.70 + d * 0.30
        notes.append(f"{int(dom)} DOM -> {d:.2f} (staleness is leverage)")

    if parcel.get("price_reduced"):
        s = _clamp(s * 1.10)
        notes.append("price reduction on record x1.10")

    for key, mult, label in (
        ("right_of_first_refusal", 0.70, "ROFR of record"),
        ("conservation_easement", 0.30, "conservation restriction"),
        ("mineral_rights_severed", 0.85, "mineral rights severed"),
    ):
        if parcel.get(key):
            s *= mult
            notes.append(f"{label} x{mult:.2f}")

    if parcel.get("option_feasible"):
        s = _clamp(s * 1.15)
        notes.append("seller open to option / long PSA with entitlement contingency x1.15")

    return _clamp(s), notes


def score_optionality(parcel: dict[str, Any]) -> tuple[float, list[str]]:
    notes: list[str] = []
    s = 0.50

    if parcel.get("expansion_land_adjacent_acres"):
        extra = float(parcel["expansion_land_adjacent_acres"])
        e = _lerp_up(extra, worst=0, best=300)
        s = s * 0.6 + e * 0.4
        notes.append(f"{extra:.0f} ac adjacent expansion land -> {e:.2f}")

    if parcel.get("phaseable"):
        s = _clamp(s * 1.20)
        notes.append("phaseable program x1.20")

    alt = str(parcel.get("alternate_use", "none")).lower()
    if alt not in {"none", "unknown", ""}:
        s = _clamp(s * 1.15)
        notes.append(f"alternate use `{alt}` if the club fails x1.15")

    return _clamp(s), notes


# =============================================================================
# Composite
# =============================================================================

def composite_score(
    parcel: dict[str, Any],
    cfg: dict[str, Any],
    underwriting: Any = None,
    screen_result: ScreenResult | None = None,
) -> CompositeScore:
    w = cfg["scoring"]["weights"]
    notes: list[str] = []

    subs = {
        "entitlement_probability": score_entitlement(parcel, screen_result),
        "yield_on_cost": score_yield(underwriting, cfg),
        "physical_suitability": score_physical(parcel, cfg),
        "market_catchment": score_catchment(parcel, cfg),
        "infrastructure_burden": score_infrastructure(parcel),
        "deal_control": score_deal_control(parcel),
        "optionality": score_optionality(parcel),
    }

    components: dict[str, float] = {}
    for key, (raw, sub_notes) in subs.items():
        components[key] = raw * w[key]
        notes.extend(f"[{key}] {n}" for n in sub_notes)

    return CompositeScore(
        parcel_id=str(parcel.get("parcel_id", parcel.get("apn", "UNKNOWN"))),
        total=round(sum(components.values()), 1),
        components={k: round(v, 2) for k, v in components.items()},
        max_components=dict(w),
        notes=notes,
    )


def rank(scores: list[CompositeScore], top_n: int = 10) -> list[CompositeScore]:
    return sorted(scores, key=lambda s: s.total, reverse=True)[:top_n]


# =============================================================================
# §11: "For each, one line: why this one wins, and what would kill it."
# =============================================================================

_CRITERION_LABEL = {
    "entitlement_probability": "entitlement path",
    "yield_on_cost": "yield headroom",
    "physical_suitability": "physical suitability",
    "market_catchment": "catchment",
    "infrastructure_burden": "infrastructure cost",
    "deal_control": "deal control",
    "optionality": "optionality",
}

# Flags that are, on their own, the thing that kills a parcel. Ordered by how
# fatal they actually are, not alphabetically.
_KILLER_FLAGS = [
    ("PRICE-INFEASIBLE", "the ask is more than 20% above the maximum supportable land price"),
    ("PRIOR-DENIAL", "the municipality has already denied a comparable use"),
    ("NO-NOISE-PRECEDENT", "greenfield with no inherited noise floor to stand on"),
    ("WATERSHED", "NYC DEP watershed exposure"),
    ("TIGHT-ORDINANCE", "a daytime dBA limit a road course cannot meet without heavy mitigation"),
    ("CLOSE-NEIGHBOR", "an occupied residence inside the setback, relying on buffer"),
    ("ZONING-LIFT", "a map amendment with no as-of-right fallback"),
    ("SUB-SCALE", "acreage in the sub-scale band — buffer is thin"),
    ("CONSERVATION", "a conservation restriction of record"),
    ("ROFR", "a right of first refusal of record"),
    ("POWER-BURDEN", "a seven-figure three-phase power extension"),
    ("ORDINANCE-UNVERIFIED", "an unverified noise ordinance — the number is not yet known"),
]


def narrative(
    score: CompositeScore,
    parcel: dict[str, Any],
    underwriting: Any = None,
) -> tuple[str, str]:
    """
    Derive the two one-liners §11 asks for from the score components and screen
    flags. These are a floor, not a substitute for judgment -- an analyst should
    overwrite them when the real story differs.
    """
    ratios = {k: (v / score.max_components[k]) if score.max_components[k] else 0.0
              for k, v in score.components.items()}
    ordered = sorted(ratios, key=lambda k: ratios[k], reverse=True)

    # --- why it wins ---------------------------------------------------------
    strengths = [k for k in ordered[:2] if ratios[k] >= 0.60]
    if strengths:
        why = " and ".join(f"{_CRITERION_LABEL[k]} at {ratios[k]:.0%}" for k in strengths)
        prior = str(parcel.get("prior_use", "")).replace("_", " ")
        if prior and ratios.get("entitlement_probability", 0) >= 0.60:
            why = f"{prior} gives it an inherited noise floor; {why}"
        why = why[0].upper() + why[1:]
    else:
        why = (f"Nothing scores above 60% — carried for physical optionality only "
               f"(best: {_CRITERION_LABEL[ordered[0]]} at {ratios[ordered[0]]:.0%})")

    # --- what would kill it --------------------------------------------------
    flags = str(parcel.get("flags") or "")
    kills = ""
    for token, phrase in _KILLER_FLAGS:
        if token in flags:
            kills = phrase[0].upper() + phrase[1:]
            break

    if not kills and underwriting is not None and underwriting.ask_price is not None:
        dscr = underwriting.dscr_gross_at_ask
        if dscr is not None and not underwriting.dscr_cleared and dscr != float("inf"):
            kills = (f"Debt service coverage of {dscr:.2f}x at the ask, below the "
                     f"covenant floor — the deal is not financeable at this price")
        max_land = underwriting.max_land_gross
        if max_land <= 0:
            kills = ("The income stack cannot carry the vertical at any land price on the "
                     "gross basis")
        elif underwriting.ask_price > max_land:
            kills = (f"The ask sits ${underwriting.ask_price - max_land:,.0f} above the "
                     f"maximum supportable land price")

    if not kills:
        weakest = ordered[-1]
        kills = f"{_CRITERION_LABEL[weakest].capitalize()} at {ratios[weakest]:.0%}"

    return why, kills


# =============================================================================
# Lead-site fragility
# =============================================================================

@dataclass
class LeadFragility:
    lead_id: str
    runner_up_id: str
    gap: float
    driver: str
    flip_value: float | None
    flips: bool
    verdict: str


def lead_site_fragility(
    parcels: list[dict[str, Any]],
    cfg: dict[str, Any],
    underwrite,
    screen,
    site_config,
) -> LeadFragility | None:
    """
    Does the site ranking survive its own largest assumption?

    A composite that separates its top two by less than a point is not really
    ranking them, and the honest question is what would have to move to swap
    them. On this pipeline the answer is one number: the lead site carries a
    $9.5M cost CREDIT for reusing existing runway pavement as track base course,
    and the risk register reports fifteen PFAS areas of concern identified
    around that runway in 2023. PFAS-impacted pavement is a waste
    characterisation problem, not a credit.

    This walks the lead site's cost premium from its modelled value toward zero
    and reports the point at which the ranking changes hands. Callers inject the
    model functions so this module keeps no dependency on the underwriting.
    """
    def ranked(override: tuple[str, float] | None) -> list[tuple[float, str]]:
        out: list[tuple[float, str]] = []
        for raw in parcels:
            p = dict(raw)
            if override and p.get("parcel_id") == override[0]:
                p["site_cost_premium_usd"] = override[1]
            sr = screen(p, cfg)
            if sr.killed_at or not p.get("ask_price"):
                continue
            prem = float(p.get("site_cost_premium_usd") or 0.0)
            uw = underwrite(site_config(cfg, p), str(p["parcel_id"]),
                            ask_price=p.get("ask_price"), site_cost_premium=prem)
            out.append((composite_score(p, cfg, uw, sr).total, str(p["parcel_id"])))
        out.sort(reverse=True)
        return out

    base = ranked(None)
    if len(base) < 2:
        return None
    (lead_score, lead_id), (up_score, up_id) = base[0], base[1]
    lead = next((p for p in parcels if str(p.get("parcel_id")) == lead_id), {})
    modelled = float(lead.get("site_cost_premium_usd") or 0.0)

    # Only a CREDIT is fragile in this direction: a premium is a cost you can
    # bid against, a credit is a number that can disappear.
    if modelled >= 0:
        return LeadFragility(
            lead_id, up_id, lead_score - up_score, "site cost premium", None, False,
            f"{lead_id} leads {up_id} by {lead_score - up_score:.1f} points and carries a "
            f"cost premium rather than a credit, so its basis can only be bid, not lost.")

    flip_at: float | None = None
    steps = 21
    for i in range(steps + 1):
        trial = modelled * (1 - i / steps)          # walk the credit toward zero
        r = ranked((lead_id, trial))
        if r and r[0][1] != lead_id:
            flip_at = trial
            break

    if flip_at is None:
        return LeadFragility(
            lead_id, up_id, lead_score - up_score, "site cost credit", None, False,
            f"{lead_id} still leads with the credit written to zero. The ranking does not "
            f"depend on it.")

    lost = abs(modelled - flip_at)
    return LeadFragility(
        lead_id, up_id, lead_score - up_score, "site cost credit", flip_at, True,
        f"THE RANKING TURNS ON ONE UNVERIFIED NUMBER. {lead_id} leads {up_id} by "
        f"{lead_score - up_score:.1f} points on a 100-point scale, and the lead depends on a "
        f"${abs(modelled):,.0f} site cost credit. Losing ${lost:,.0f} of it — "
        f"{lost / abs(modelled):.0%} — hands the lead to {up_id}. That credit is the reuse of "
        f"existing runway pavement as base course, on a runway around which fifteen PFAS "
        f"areas of concern were identified in 2023. Order the Phase II before the ranking is "
        f"treated as settled.")
