"""
TRACK BOSS — Parcel Schema
==========================

One definition of a parcel, consumed by the CSV intake, the gates, the scoring
engine, and the workbook writer. If a field is not here, it does not reach the
Executive Summary.

§9 requires 60+ columns on `Full Parcel Universe`. §10 requires every row to
carry a Confidence marker and every claim to be traceable to a numbered source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

FieldKind = Literal["str", "float", "int", "bool", "pct", "usd", "json"]


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: FieldKind
    group: str
    required: bool = False
    note: str = ""


# §5 non-negotiable: all four or the parcel goes to `Unverified`.
IDENTITY: list[Field] = [
    Field("parcel_id", "Parcel ID", "str", "Identity", True, "Internal key, unique"),
    Field("apn", "APN / Tax Map ID", "str", "Identity", True, "Required identifier"),
    Field("listing_url", "Listing / Record URL", "str", "Identity", True, "Must be live"),
    Field("latitude", "Latitude", "float", "Identity", True, "Required identifier"),
    Field("longitude", "Longitude", "float", "Identity", True, "Required identifier"),
    Field("municipality", "Municipality", "str", "Identity", True, "Required identifier"),
    Field("county", "County", "str", "Identity"),
    Field("state", "State", "str", "Identity"),
    Field("address", "Address / Locus", "str", "Identity"),
    Field("source_tier", "Source Tier", "str", "Identity", note="Tier 1 / 2 / 3 per §5"),
    Field("confidence", "Confidence", "str", "Identity", note="Verified / Inferred / Assumed"),
    Field("source_ids", "Source IDs", "str", "Identity", note="Comma-separated §10 citation nos."),
    Field("date_stamp", "Data As-Of", "str", "Identity", note="Every price and DOM is dated"),
]

PHYSICAL: list[Field] = [
    Field("gross_acres", "Gross Acres", "float", "Physical"),
    Field("contiguous_developable_acres", "Contiguous Developable Acres", "float", "Physical", True),
    Field("contiguous_acres_under_8pct_grade", "Contiguous Acres <8% Grade", "float", "Physical"),
    Field("elevation_change_ft", "Elevation Change (ft)", "float", "Physical"),
    Field("natural_amphitheater", "Natural Bowl / Amphitheater", "bool", "Physical"),
    Field("pct_wetlands", "% NWI Wetlands", "pct", "Physical"),
    Field("pct_floodway", "% FEMA Zone A/AE Floodway", "pct", "Physical"),
    Field("pct_watercourse_buffer", "% Watercourse Buffer", "pct", "Physical"),
    Field("soil_class", "Dominant Soil Class", "str", "Physical"),
    Field("bedrock_depth_ft", "Bedrock Depth (ft)", "float", "Physical"),
    Field("blasting_risk", "Blasting Risk", "str", "Physical"),
    Field("cutfill_balance_cy", "Est. Cut/Fill Imbalance (CY)", "float", "Physical"),
    Field("assemblage_possible", "Assemblage Required", "bool", "Physical"),
    Field("assemblage_adjacent_acres", "Assemblage Adjacent Acres", "float", "Physical"),
    Field("expansion_land_adjacent_acres", "Expansion Land Adjacent (ac)", "float", "Physical"),
    Field("site_cost_premium_usd", "Site Cost Premium / (Credit)", "usd", "Physical",
          note="Site-specific delta to non-land cost: earthwork, utilities, "
               "remediation, blasting, less the value of existing pavement"),
    Field("site_cost_basis_note", "Site Cost Basis Note", "str", "Physical"),
    Field("season_days", "Usable Track Days / Year", "int", "Physical",
          note="ESTIMATED from climate. Drives ancillary revenue — the single "
               "largest geographic economic difference."),
    Field("market_metro", "Target Metro", "str", "Identity"),
    Field("market_region", "Region", "str", "Identity"),
    Field("market_tier", "Market Tier", "str", "Identity"),
]

NOISE_ENTITLEMENT: list[Field] = [
    Field("prior_use", "Prior / Inherited Use", "str", "Noise & Entitlement", True),
    Field("nearest_residence_ft", "Nearest Occupied Residence (ft)", "float", "Noise & Entitlement"),
    Field("residences_within_1mi", "Residences Within 1 mi", "int", "Noise & Entitlement"),
    Field("has_intervening_buffer", "Intervening Topo/Forest Buffer", "bool", "Noise & Entitlement"),
    Field("noise_ordinance_citation", "Noise Ordinance Citation", "str", "Noise & Entitlement"),
    Field("noise_ordinance_dba_day", "Daytime dBA Limit", "float", "Noise & Entitlement",
          note="NEVER invent. Blank means unpublished -- name the clerk to call."),
    Field("noise_measurement_point", "Measurement Point", "str", "Noise & Entitlement"),
    Field("noise_standard_type", "Absolute or Ambient-Relative", "str", "Noise & Entitlement"),
    Field("zoning_district", "Zoning District", "str", "Noise & Entitlement"),
    Field("zoning_posture", "Outdoor Rec Posture", "str", "Noise & Entitlement",
          note="as_of_right / special_permit / map_amendment_required / prohibited_no_amendment_path"),
    Field("permitting_path", "Permitting Path", "str", "Noise & Entitlement"),
    Field("permitting_timeline_months", "Permitting Timeline (mo)", "int", "Noise & Entitlement"),
    Field("prior_denial_same_use", "Prior Denial of Comparable Use", "bool", "Noise & Entitlement"),
    Field("opposition_risk", "Opposition Risk", "str", "Noise & Entitlement"),
    Field("jurisdiction_flags", "Jurisdiction Flags", "str", "Noise & Entitlement",
          note="e.g. nj_highlands_preservation, adirondack_park"),
    Field("in_woh_watershed", "NYC DEP West-of-Hudson Watershed", "bool", "Noise & Entitlement"),
]

CATCHMENT: list[Field] = [
    # Anchors are named per site, not fixed. A nationwide pipeline cannot measure
    # a Phoenix parcel against Manhattan; Gate 3 and §11 both read the *dict*, so
    # the anchor identity travels with the row.
    Field("drive_anchor_1_name", "Drive Anchor 1", "str", "Catchment",
          note="Wealth node the primary drive time is measured to"),
    Field("drive_anchor_1_min", "Drive Anchor 1 (min)", "int", "Catchment"),
    Field("drive_anchor_2_name", "Drive Anchor 2", "str", "Catchment"),
    Field("drive_anchor_2_min", "Drive Anchor 2 (min)", "int", "Catchment"),
    Field("drive_anchor_3_name", "Drive Anchor 3", "str", "Catchment"),
    Field("drive_anchor_3_min", "Drive Anchor 3 (min)", "int", "Catchment"),
    Field("best_drive_min", "Best Drive Time (min)", "int", "Catchment"),
    Field("hnw_households_90min", "HNW Households <90 min", "int", "Catchment",
          note=">$1M investable; cite source"),
    Field("nearest_jet_fbo_mi", "Nearest Jet FBO (mi)", "float", "Catchment"),
    Field("nearest_jet_fbo_name", "Nearest Jet FBO", "str", "Catchment"),
    Field("nearest_motorsport_club_mi", "Nearest Motorsport Club (mi)", "float", "Catchment"),
    Field("nearest_motorsport_club_name", "Nearest Motorsport Club", "str", "Catchment"),
    Field("exotic_dealers_in_catchment", "Exotic/Collector Dealers", "int", "Catchment"),
    Field("marque_clubs_in_catchment", "Marque Clubs", "int", "Catchment"),
]

# Derived by model/demand.py, written back onto the row by the workbook builder.
DEMAND_OUT: list[Field] = [
    Field("demand_capturable", "Capturable Prospects", "float", "Catchment",
          note="HNW pool built down through collector, track-active, incumbent "
               "and reachable shares"),
    Field("demand_coverage", "Demand Coverage (x seats)", "float", "Catchment",
          note="Capturable prospects per seat. Below 2.0x market size IS the risk."),
    Field("demand_verdict", "Demand Verdict", "str", "Catchment"),
]

INFRASTRUCTURE: list[Field] = [
    Field("three_phase_power_distance_mi", "3-Phase Power (mi)", "float", "Infrastructure"),
    Field("water_source", "Water Source", "str", "Infrastructure",
          note="municipal / well_proven / well_unproven / none"),
    Field("sewer", "Sewer", "str", "Infrastructure", note="municipal / septic / none"),
    Field("perc_rate_min_per_inch", "Perc Rate (min/in)", "float", "Infrastructure"),
    Field("fiber_available", "Fiber Available", "bool", "Infrastructure"),
    Field("existing_paved_runway", "Existing Pavement Converts", "bool", "Infrastructure"),
    Field("existing_structures_sf", "Existing Structures (SF)", "float", "Infrastructure"),
    Field("road_frontage_ft", "Road Frontage (ft)", "float", "Infrastructure"),
    Field("has_legal_road_frontage", "Legal Public Road Access", "bool", "Infrastructure"),
    Field("curb_cut_existing", "Existing Curb Cut", "bool", "Infrastructure"),
]

ENVIRONMENTAL: list[Field] = [
    Field("phase_i_status", "Phase I Status", "str", "Environmental"),
    Field("has_ust", "USTs of Record", "bool", "Environmental"),
    Field("remediation_status", "Remediation Status", "str", "Environmental"),
    Field("ag_chemical_legacy", "Ag Chemical Legacy", "bool", "Environmental"),
    Field("te_species_habitat", "T&E Species Habitat", "bool", "Environmental"),
    Field("historic_archaeological_flag", "Historic / Archaeological Flag", "bool", "Environmental"),
]

DEAL: list[Field] = [
    Field("owner_name", "Owner of Record", "str", "Deal"),
    Field("owner_type", "Owner Type", "str", "Deal",
          note="individual / estate / probate / llc / corporate / institutional / municipal / land_trust"),
    Field("ask_price", "Ask Price", "usd", "Deal"),
    Field("ask_price_per_acre", "Ask $/Acre", "usd", "Deal"),
    Field("days_on_market", "Days on Market", "int", "Deal"),
    Field("price_reduced", "Price Reduction on Record", "bool", "Deal"),
    Field("prior_failed_contracts", "Prior Failed Contracts", "int", "Deal"),
    Field("conservation_easement", "Conservation Restriction", "bool", "Deal"),
    Field("right_of_first_refusal", "ROFR of Record", "bool", "Deal"),
    Field("mineral_rights_severed", "Mineral Rights Severed", "bool", "Deal"),
    Field("pa_490_enrolled", "CT PA 490 Enrolled", "bool", "Deal"),
    Field("ag_district_305a", "NY Ag District 305-a", "bool", "Deal"),
    Field("tax_abatement_path", "Abatement Path", "str", "Deal",
          note="NY IDA PILOT / NJ EDA / CT enterprise zone / TX Ch.312 / TN IDB PILOT"),
    # Ad valorem load is the second-largest geographic economic difference after
    # season length, and unlike season it is a matter of statute, not weather.
    # A NY parcel carries ~2.25% effective; AZ and NV carry a third of that.
    Field("property_tax_effective_rate", "Effective Tax Rate", "pct", "Deal",
          note="Local rate on assessed value. Overrides the config default."),
    Field("property_tax_abatement_pct", "Assumed Abatement", "pct", "Deal",
          note="0.0 where no PILOT or abatement statute reaches this use. "
               "The 50% base case is NY-IDA-specific and does not travel."),
    Field("option_feasible", "Option or Long PSA Feasible", "bool", "Deal"),
    Field("seller_motivation", "Seller Motivation Signal", "str", "Deal"),
    Field("phaseable", "Phaseable Program", "bool", "Deal"),
    Field("alternate_use", "Alternate Use if Club Fails", "str", "Deal"),
]

UNDERWRITING_OUT: list[Field] = [
    Field("stabilized_noi", "Stabilized NOI", "usd", "Underwriting"),
    Field("stabilization_year", "Stabilization Year", "int", "Underwriting"),
    Field("max_land_gross", "Max Supportable Land — Gross", "usd", "Underwriting"),
    Field("max_land_net", "Max Supportable Land — Net", "usd", "Underwriting"),
    Field("yoc_gross_at_ask", "YoC at Ask — Gross", "pct", "Underwriting"),
    Field("yoc_net_at_ask", "YoC at Ask — Net", "pct", "Underwriting"),
    Field("yoc_gross_year5", "YoC Year 5 — Gross", "pct", "Underwriting"),
    Field("yoc_net_year5", "YoC Year 5 — Net", "pct", "Underwriting"),
    Field("dev_spread_gross_bps", "Dev Spread — Gross (bps)", "float", "Underwriting"),
    Field("required_yield", "Required Yield (binding)", "pct", "Underwriting"),
    Field("binding_constraint", "Binding Constraint", "str", "Underwriting",
          note="YIELD or DSCR — whichever is tighter"),
    Field("dscr_gross_at_ask", "DSCR at Ask — Gross", "float", "Underwriting"),
    Field("dscr_net_at_ask", "DSCR at Ask — Net", "float", "Underwriting"),
    Field("dscr_cleared", "Clears Min DSCR", "bool", "Underwriting"),
    Field("headroom_to_ask", "Headroom vs Ask", "usd", "Underwriting"),
    Field("price_infeasible", "PRICE-INFEASIBLE", "bool", "Underwriting"),
    Field("hurdle_cleared", "Clears 6.50%", "bool", "Underwriting"),
]

SCREEN_OUT: list[Field] = [
    Field("killed_at_gate", "Killed at Gate", "str", "Screen"),
    Field("rejection_reasons", "Rejection Reasons", "str", "Screen"),
    Field("flags", "Flags", "str", "Screen"),
    Field("composite_score", "Composite Score (100)", "float", "Screen"),
    Field("grade", "Grade", "str", "Screen"),
    Field("why_wins", "Why This One Wins", "str", "Screen", note="§11 one-liner"),
    Field("what_kills", "What Would Kill It", "str", "Screen", note="§11 one-liner"),
    Field("score_entitlement", "Score: Entitlement (25)", "float", "Screen"),
    Field("score_yield", "Score: Yield (20)", "float", "Screen"),
    Field("score_physical", "Score: Physical (15)", "float", "Screen"),
    Field("score_catchment", "Score: Catchment (15)", "float", "Screen"),
    Field("score_infrastructure", "Score: Infrastructure (10)", "float", "Screen"),
    Field("score_deal_control", "Score: Deal Control (10)", "float", "Screen"),
    Field("score_optionality", "Score: Optionality (5)", "float", "Screen"),
]

PARCEL_SCHEMA: list[Field] = (
    IDENTITY
    + PHYSICAL
    + NOISE_ENTITLEMENT
    + CATCHMENT
    + DEMAND_OUT
    + INFRASTRUCTURE
    + ENVIRONMENTAL
    + DEAL
    + UNDERWRITING_OUT
    + SCREEN_OUT
)

SCHEMA_BY_KEY: dict[str, Field] = {f.key: f for f in PARCEL_SCHEMA}
COLUMN_KEYS: list[str] = [f.key for f in PARCEL_SCHEMA]


def blank_parcel() -> dict[str, Any]:
    return {f.key: None for f in PARCEL_SCHEMA}


def coerce(parcel: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize a raw intake row into model types. Unparseable values become None
    rather than raising -- a bad cell must not kill a 150-parcel run, it must
    surface as an unverified field.
    """
    out: dict[str, Any] = {}
    for f in PARCEL_SCHEMA:
        v = parcel.get(f.key)
        if v is None or v == "":
            out[f.key] = None
            continue
        try:
            if f.kind in ("float", "pct", "usd"):
                out[f.key] = float(str(v).replace(",", "").replace("$", "").replace("%", ""))
            elif f.kind == "int":
                out[f.key] = int(float(str(v).replace(",", "")))
            elif f.kind == "bool":
                out[f.key] = str(v).strip().lower() in {"1", "true", "yes", "y", "t"}
            else:
                out[f.key] = str(v)
        except (TypeError, ValueError):
            out[f.key] = None

    # Reassemble the composites the gates expect. Anchor names are per-row.
    times: dict[str, int] = {}
    for i in (1, 2, 3):
        name = out.get(f"drive_anchor_{i}_name") or f"Anchor {i}"
        mins = out.get(f"drive_anchor_{i}_min")
        if mins is not None:
            times[str(name)] = mins
    out["drive_times_min"] = times
    if times:
        out["best_drive_min"] = min(times.values())

    raw_flags = parcel.get("jurisdiction_flags") or ""
    if isinstance(raw_flags, str):
        out["jurisdiction_flags"] = [s.strip() for s in raw_flags.split(",") if s.strip()]
    else:
        out["jurisdiction_flags"] = list(raw_flags)

    return out
