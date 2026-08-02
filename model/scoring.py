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

    dba = parcel.get("noise_ordinance_dba_day")
    if dba is None:
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
    max_land = (
        underwriting.max_land_gross if rank_basis == "gross" else underwriting.max_land_net
    )
    ask = underwriting.ask_price
    yoc = underwriting.yoc_gross_at_ask if rank_basis == "gross" else underwriting.yoc_net_at_ask

    if max_land <= 0:
        notes.append(
            f"max supportable land price is {max_land:,.0f} on {rank_basis} basis -- "
            f"income stack cannot carry the vertical at any land price"
        )
        return 0.0, notes

    headroom_ratio = (max_land - ask) / ask if ask else 0.0
    # -50% headroom -> 0.0 ; at the money -> 0.60 ; +50% headroom -> 1.0
    if headroom_ratio >= 0:
        s = 0.60 + 0.40 * _clamp(headroom_ratio / 0.50)
    else:
        s = 0.60 * _clamp(1 + headroom_ratio / 0.50)

    notes.append(
        f"{rank_basis} basis: max supportable ${max_land:,.0f} vs ask ${ask:,.0f} "
        f"({headroom_ratio:+.1%} headroom), YoC {yoc:.2%}"
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
