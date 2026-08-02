"""
TRACK BOSS — Screening Funnel (Gates 1-5)
=========================================

Parcels run the gates in order. Gate 1 and Gate 2 are the mortality filter;
nothing gets underwritten until it clears both. Expect 80-90% kill rate.

Every rejection is logged with a reason. A parcel that dies at Gate 1 still
occupies a row in `Full Parcel Universe` -- the rejection log IS the audit
trail, and a seller repricing or a boundary redraw can resurrect a parcel later.

Principal-confirmed thresholds (see config/underwriting_inputs.yaml):
  - Acreage:    hard reject < 250; 250-350 flagged SUB-SCALE with penalty
  - Drive time: hard reject > 120 min; full marks at <= 90 min
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

# -----------------------------------------------------------------------------
# Gate 1 constants that are physics or statute, not principal preference
# -----------------------------------------------------------------------------
MIN_RESIDENCE_SETBACK_FT = 1500        # unless intervening topo/forest buffer
MAX_CONSTRAINED_PCT = 0.35             # floodway + wetlands + watercourse buffer
MIN_FLAT_CONTIGUOUS_ACRES = 150        # acres under 8% grade
MAX_GRADE_FOR_FLAT = 8.0               # percent

# Jurisdictions that are an automatic no. Not negotiable, not worth a phone call.
EXCLUSION_ZONES = {
    "nj_highlands_preservation": "NJ Highlands Preservation Area — statutory bar",
    "nj_pinelands_preservation": "NJ Pinelands Preservation Area — statutory bar",
    "nj_pinelands_forest": "NJ Pinelands Forest Area — statutory bar",
    "adirondack_park": "Adirondack Park Agency jurisdiction — reject",
}

# NYC DEP West-of-Hudson watershed: reject or flag WATERSHED-SEVERE.
WATERSHED_WOH_COUNTIES = {"ulster", "sullivan", "delaware", "greene", "schoharie"}

# Gate 2: prior intensive use = an inherited noise floor. This is the single
# highest-signal attribute in the whole screen.
PRIOR_USE_TIERS = {
    # tier 1 -- already fought the noise fight, or never had to
    "existing_motorsport": 1,      # drag strip, dirt oval, motocross, speedway
    "airport_airfield": 1,
    "military_installation": 1,
    "shooting_range": 1,
    # tier 2 -- industrial noise floor, remediation overhead
    "active_quarry": 2,
    "reclaimed_quarry": 2,
    "sand_gravel_pit": 2,
    "mine": 2,
    "capped_landfill": 2,
    "brownfield": 2,
    # tier 3 -- adjacency rather than on-site history
    "interstate_adjacent": 3,
    "rail_freight_adjacent": 3,
    "heavy_industrial_adjacent": 3,
    # tier 4 -- pre-graded and pre-entitled for outdoor recreation
    "golf_course": 4,              # §5 calls this the highest-priority typology
    "camp_retreat": 4,
    "corporate_campus": 4,
    # tier 5 -- no inherited noise floor at all
    "greenfield_agricultural": 5,
    "greenfield_forest": 5,
}


class Gate(IntEnum):
    HARD_KNOCKOUT = 1
    NOISE_ENTITLEMENT = 2
    MARKET_CATCHMENT = 3
    PHYSICAL_INFRA = 4
    DEAL_CONTROL = 5


@dataclass
class GateResult:
    passed: bool
    gate: Gate
    reasons: list[str] = field(default_factory=list)   # why it died
    flags: list[str] = field(default_factory=list)     # survived, but note this

    def __bool__(self) -> bool:
        return self.passed


@dataclass
class ScreenResult:
    parcel_id: str
    passed_through: Gate | None        # deepest gate cleared; None = died at 1
    killed_at: Gate | None
    reasons: list[str]
    flags: list[str]

    @property
    def survived(self) -> bool:
        return self.killed_at is None


def _get(p: dict[str, Any], key: str, default: Any = None) -> Any:
    v = p.get(key, default)
    return default if v is None else v


# =============================================================================
# GATE 1 — Hard knockouts
# =============================================================================

def gate1_hard_knockouts(parcel: dict[str, Any], cfg: dict[str, Any]) -> GateResult:
    reasons: list[str] = []
    flags: list[str] = []
    acre_cfg = cfg["mandate"]["acreage"]
    hard_floor = acre_cfg["hard_floor_acres"]
    preferred = acre_cfg["preferred_floor_acres"]

    # --- Acreage -------------------------------------------------------------
    acres = _get(parcel, "contiguous_developable_acres", 0.0)
    if acres < hard_floor:
        if _get(parcel, "assemblage_possible", False):
            total = acres + _get(parcel, "assemblage_adjacent_acres", 0.0)
            if total >= hard_floor:
                flags.append(
                    f"ASSEMBLAGE — {acres:.0f} ac base + "
                    f"{total - acres:.0f} ac adjacent to reach {total:.0f} ac"
                )
                acres = total
            else:
                reasons.append(
                    f"Under acreage floor: {acres:.0f} ac (+{total - acres:.0f} ac "
                    f"assemblage) < {hard_floor} ac"
                )
        else:
            reasons.append(f"Under acreage floor: {acres:.0f} ac < {hard_floor} ac")

    if hard_floor <= acres < preferred:
        flags.append(
            f"SUB-SCALE — {acres:.0f} ac is inside the {hard_floor}-{preferred} ac "
            f"band; buffer is thin, physical score penalized"
        )

    # --- Excluded jurisdictions ---------------------------------------------
    for zone in _get(parcel, "jurisdiction_flags", []):
        z = str(zone).strip().lower()
        if z in EXCLUSION_ZONES:
            reasons.append(EXCLUSION_ZONES[z])

    # --- NYC DEP West-of-Hudson watershed ------------------------------------
    county = str(_get(parcel, "county", "")).strip().lower()
    state = str(_get(parcel, "state", "")).strip().upper()
    if state == "NY" and county in WATERSHED_WOH_COUNTIES:
        if _get(parcel, "in_woh_watershed", None) is True:
            reasons.append(
                f"NYC DEP West-of-Hudson watershed ({county.title()} Co.) — WATERSHED-SEVERE"
            )
        else:
            flags.append(
                f"WATERSHED-CHECK — {county.title()} Co. straddles the NYC DEP "
                f"West-of-Hudson boundary; confirm parcel sits outside before spending cycles"
            )

    # --- Distance to nearest occupied residence ------------------------------
    dist = _get(parcel, "nearest_residence_ft", None)
    if dist is not None:
        if dist < MIN_RESIDENCE_SETBACK_FT and not _get(parcel, "has_intervening_buffer", False):
            reasons.append(
                f"Nearest occupied residence {dist:.0f} ft < {MIN_RESIDENCE_SETBACK_FT} ft "
                f"with no intervening topographic or forested buffer"
            )
        elif dist < MIN_RESIDENCE_SETBACK_FT:
            flags.append(
                f"CLOSE-NEIGHBOR — residence at {dist:.0f} ft, relying on intervening "
                f"buffer; commission a noise study before going hard"
            )
    else:
        flags.append("UNVERIFIED — distance to nearest occupied residence not established")

    # --- Constrained land ----------------------------------------------------
    constrained = (
        _get(parcel, "pct_floodway", 0.0)
        + _get(parcel, "pct_wetlands", 0.0)
        + _get(parcel, "pct_watercourse_buffer", 0.0)
    )
    if constrained > MAX_CONSTRAINED_PCT:
        reasons.append(
            f"Constrained land {constrained:.0%} > {MAX_CONSTRAINED_PCT:.0%} "
            f"(floodway + wetlands + watercourse buffer)"
        )

    # --- Slope ---------------------------------------------------------------
    flat = _get(parcel, "contiguous_acres_under_8pct_grade", None)
    if flat is not None and flat < MIN_FLAT_CONTIGUOUS_ACRES:
        reasons.append(
            f"Only {flat:.0f} contiguous acres under {MAX_GRADE_FOR_FLAT:.0f}% grade "
            f"< {MIN_FLAT_CONTIGUOUS_ACRES} ac required"
        )
    elif flat is None:
        flags.append("UNVERIFIED — slope analysis not run; Site Physician must resolve")

    # --- Legal access --------------------------------------------------------
    if not _get(parcel, "has_legal_road_frontage", True):
        reasons.append("No legal frontage or deeded access to a public road")

    return GateResult(passed=not reasons, gate=Gate.HARD_KNOCKOUT, reasons=reasons, flags=flags)


# =============================================================================
# GATE 2 — Noise and entitlement viability
# =============================================================================

def gate2_noise_entitlement(parcel: dict[str, Any], cfg: dict[str, Any]) -> GateResult:
    """
    Noise, not zoning, kills these projects. A parcel with no inherited noise
    floor and no buffer is a five-year fight you lose. This gate does not reject
    on zoning -- map amendments are winnable -- it rejects on acoustic hopelessness.
    """
    reasons: list[str] = []
    flags: list[str] = []

    prior = str(_get(parcel, "prior_use", "greenfield_forest")).strip().lower()
    tier = PRIOR_USE_TIERS.get(prior, 5)

    residences_1mi = _get(parcel, "residences_within_1mi", None)
    dist = _get(parcel, "nearest_residence_ft", None)

    if tier == 5:
        # Greenfield. Survivable only on isolation: real distance and few neighbors.
        if residences_1mi is not None and residences_1mi > 40:
            reasons.append(
                f"Greenfield site with no inherited noise floor and "
                f"{residences_1mi} residences within 1 mi — acoustically unwinnable"
            )
        elif dist is not None and dist < 3000:
            reasons.append(
                f"Greenfield site with nearest residence at {dist:.0f} ft — "
                f"no prior-use noise precedent to inherit"
            )
        else:
            flags.append(
                "NO-NOISE-PRECEDENT — greenfield; entitlement rests entirely on "
                "isolation and a clean acoustic model, budget 30+ months"
            )
    elif tier <= 2:
        flags.append(f"NOISE-FLOOR-INHERITED — prior use `{prior}` (tier {tier})")
    else:
        flags.append(f"PARTIAL-NOISE-PRECEDENT — `{prior}` (tier {tier})")

    if prior == "golf_course":
        flags.append(
            "GOLF-CONVERSION — pre-graded, likely sewered, already entitled for "
            "outdoor recreation; §5 highest-priority typology"
        )

    # --- Noise ordinance -----------------------------------------------------
    # §10: never invent a dBA limit. Absent data is a research task, not a number.
    dba = _get(parcel, "noise_ordinance_dba_day", None)
    if dba is None:
        flags.append(
            "ORDINANCE-UNVERIFIED — daytime dBA limit not published online; "
            "Jurisdiction Router must call the municipal clerk and cite the call"
        )
    else:
        measure = str(_get(parcel, "noise_measurement_point", "unknown"))
        rel = str(_get(parcel, "noise_standard_type", "unknown"))
        if dba < 55 and rel == "absolute":
            reasons.append(
                f"Absolute {dba:.0f} dBA daytime limit at {measure} — "
                f"unachievable for a road course at any realistic setback"
            )
        elif dba < 65:
            flags.append(
                f"TIGHT-ORDINANCE — {dba:.0f} dBA {rel} at {measure}; "
                f"requires berming, sound walls, or a muffler rule"
            )

    # --- Zoning posture ------------------------------------------------------
    posture = str(_get(parcel, "zoning_posture", "unknown")).strip().lower()
    if posture == "prohibited_no_amendment_path":
        reasons.append("Outdoor recreation prohibited with no map amendment path available")
    elif posture in {"map_amendment_required", "unknown"}:
        flags.append(f"ZONING-LIFT — posture `{posture}`; treat as 24-36 month entitlement")

    if _get(parcel, "prior_denial_same_use", False):
        flags.append(
            "PRIOR-DENIAL — municipality has denied a comparable motorsport or "
            "outdoor amusement application; Risk Marshal must pull the record"
        )

    if str(_get(parcel, "state", "")).strip().upper() == "CT":
        flags.append(
            "CT-HOME-RULE — no county layer; the P&Z and IWWC are the entire fight"
        )

    return GateResult(passed=not reasons, gate=Gate.NOISE_ENTITLEMENT, reasons=reasons, flags=flags)


# =============================================================================
# GATE 3 — Market catchment
# =============================================================================

def gate3_market_catchment(parcel: dict[str, Any], cfg: dict[str, Any]) -> GateResult:
    reasons: list[str] = []
    flags: list[str] = []
    dt_cfg = cfg["mandate"]["drive_time"]
    max_min, prize_min = dt_cfg["max_minutes"], dt_cfg["prize_minutes"]

    times = _get(parcel, "drive_times_min", {}) or {}
    if not times:
        flags.append("UNVERIFIED — drive times not computed from any of the three origins")
        return GateResult(True, Gate.MARKET_CATCHMENT, reasons, flags)

    best = min(times.values())
    best_origin = min(times, key=times.get)

    if best > max_min:
        reasons.append(
            f"Best drive time {best:.0f} min (from {best_origin}) exceeds the "
            f"{max_min} min ceiling"
        )
    elif best <= prize_min:
        flags.append(f"PRIZE-CATCHMENT — {best:.0f} min from {best_origin}")
    else:
        flags.append(f"SECONDARY-CATCHMENT — {best:.0f} min from {best_origin}")

    fbo = _get(parcel, "nearest_jet_fbo_mi", None)
    if fbo is not None and fbo > 45:
        flags.append(f"FBO-DISTANT — nearest jet-capable FBO {fbo:.0f} mi")

    comp = _get(parcel, "nearest_motorsport_club_mi", None)
    if comp is not None and comp < 25:
        flags.append(
            f"COMPETITION — existing motorsport club {comp:.0f} mi away; "
            f"validates demand, splits it too"
        )

    return GateResult(passed=not reasons, gate=Gate.MARKET_CATCHMENT, reasons=reasons, flags=flags)


# =============================================================================
# GATE 4 — Physical and infrastructure
# =============================================================================

def gate4_physical_infra(parcel: dict[str, Any], cfg: dict[str, Any]) -> GateResult:
    """Gate 4 rarely kills. It prices. Findings here drive infrastructure burden."""
    reasons: list[str] = []
    flags: list[str] = []

    power = _get(parcel, "three_phase_power_distance_mi", None)
    if power is not None and power > 3:
        flags.append(f"POWER-BURDEN — 3-phase {power:.1f} mi away; extension is 7 figures")

    if str(_get(parcel, "water_source", "unknown")).lower() == "none":
        flags.append("WATER-BURDEN — no municipal water and no proven well yield")

    if str(_get(parcel, "sewer", "unknown")).lower() == "septic":
        perc = _get(parcel, "perc_rate_min_per_inch", None)
        if perc is not None and perc > 60:
            flags.append(f"SEPTIC-RISK — perc {perc:.0f} min/in; clubhouse flows may not site")

    bedrock = _get(parcel, "bedrock_depth_ft", None)
    if bedrock is not None and bedrock < 5:
        flags.append(f"BLASTING — bedrock at {bedrock:.0f} ft; cut/fill balance at risk")

    if _get(parcel, "existing_paved_runway", False):
        flags.append("RUNWAY-CONVERTS — existing pavement is base course you do not pay for")

    for key, label in (
        ("has_ust", "USTs on record"),
        ("te_species_habitat", "Threatened/endangered species habitat mapped"),
        ("historic_archaeological_flag", "Historic or archaeological resource flagged"),
    ):
        if _get(parcel, key, False):
            flags.append(f"ENV-{label}")

    return GateResult(passed=not reasons, gate=Gate.PHYSICAL_INFRA, reasons=reasons, flags=flags)


# =============================================================================
# GATE 5 — Deal and control
# =============================================================================

def gate5_deal_control(parcel: dict[str, Any], cfg: dict[str, Any]) -> GateResult:
    reasons: list[str] = []
    flags: list[str] = []

    owner = str(_get(parcel, "owner_type", "unknown")).strip().lower()
    if owner in {"land_trust", "conservation_org"}:
        reasons.append(f"Owner type `{owner}` — land is not acquirable for this use")
    elif owner in {"estate", "probate", "bankruptcy"}:
        flags.append(f"MOTIVATED-SELLER — `{owner}`; option or long PSA is realistic")
    elif owner == "municipal":
        flags.append("MUNICIPAL-OWNER — RFP or disposition process; slow but PILOT-friendly")

    if _get(parcel, "conservation_easement", False):
        reasons.append("Conservation restriction of record — encumbers the development right")

    if _get(parcel, "right_of_first_refusal", False):
        flags.append("ROFR — right of first refusal of record; verify holder and cure path")

    state = str(_get(parcel, "state", "")).strip().upper()
    if state == "CT" and _get(parcel, "pa_490_enrolled", False):
        flags.append("PA-490-RECAPTURE — CT ag/forest exemption; model conveyance tax recapture")
    if state == "NY" and _get(parcel, "ag_district_305a", False):
        flags.append("AG-DISTRICT-305A — NY Ag District; 305-a review and rollback taxes apply")

    dom = _get(parcel, "days_on_market", None)
    if dom is not None and dom > 540:
        flags.append(f"STALE-LISTING — {dom} DOM; the ask is a fiction, bid the model")

    if _get(parcel, "prior_failed_contracts", 0) >= 2:
        flags.append(
            f"{_get(parcel, 'prior_failed_contracts')} prior failed contracts — "
            f"diligence something; find out what killed them"
        )

    return GateResult(passed=not reasons, gate=Gate.DEAL_CONTROL, reasons=reasons, flags=flags)


# =============================================================================
# Funnel
# =============================================================================

GATE_FUNCS = {
    Gate.HARD_KNOCKOUT: gate1_hard_knockouts,
    Gate.NOISE_ENTITLEMENT: gate2_noise_entitlement,
    Gate.MARKET_CATCHMENT: gate3_market_catchment,
    Gate.PHYSICAL_INFRA: gate4_physical_infra,
    Gate.DEAL_CONTROL: gate5_deal_control,
}


def screen(parcel: dict[str, Any], cfg: dict[str, Any], stop_after: Gate | None = None) -> ScreenResult:
    """
    Run a parcel through the funnel. Stops at the first gate it fails and
    records why. `stop_after` runs only Gates 1-2 for the parallel mortality
    pass described in §8.
    """
    pid = str(parcel.get("parcel_id", parcel.get("apn", "UNKNOWN")))
    all_flags: list[str] = []
    deepest: Gate | None = None

    for gate in sorted(GATE_FUNCS):
        if stop_after is not None and gate > stop_after:
            break
        result = GATE_FUNCS[gate](parcel, cfg)
        all_flags.extend(result.flags)
        if not result.passed:
            return ScreenResult(
                parcel_id=pid,
                passed_through=deepest,
                killed_at=gate,
                reasons=result.reasons,
                flags=all_flags,
            )
        deepest = gate

    return ScreenResult(
        parcel_id=pid, passed_through=deepest, killed_at=None, reasons=[], flags=all_flags
    )


REQUIRED_IDENTIFIERS = ("listing_url", "apn", "latitude", "longitude", "municipality")


def has_required_identifiers(parcel: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    §5 non-negotiable: live URL, parcel/APN, lat/long, municipality. Missing any
    one and the parcel goes to the `Unverified` tab, not the workbook.
    """
    missing = [k for k in REQUIRED_IDENTIFIERS if not parcel.get(k)]
    return (not missing, missing)


def funnel_report(parcels: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, Any]:
    """Mortality accounting across a parcel set. §12.4 expects 80-90% kill."""
    results = [screen(p, cfg) for p in parcels]
    by_gate: dict[str, int] = {}
    for r in results:
        if r.killed_at:
            by_gate[r.killed_at.name] = by_gate.get(r.killed_at.name, 0) + 1

    survivors = [r for r in results if r.survived]
    total = len(results)
    return {
        "total_screened": total,
        "survivors": len(survivors),
        "mortality_pct": (1 - len(survivors) / total) if total else 0.0,
        "killed_by_gate": by_gate,
        "results": results,
    }
