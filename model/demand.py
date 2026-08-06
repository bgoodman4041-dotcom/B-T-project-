"""
TRACK BOSS — Membership Demand
==============================

The plan has been asserting that demand risk is "a marketing question rather
than a market-size question" because the required membership is a few basis
points of the high-net-worth pool. That is true and it is not an argument. A
few basis points of a pool you cannot reach is still zero members, and the
statement is identical for a 520,000-household catchment and a 98,000-household
one, which is exactly the discrimination a nationwide pipeline needs.

This module builds the pool DOWN to a capturable count and compares it against
what the club actually has to sell. Two numbers come out:

    coverage      capturable prospects per seat that must be filled
    fill_years    the FLOOR on time to fill, set by the pool -- not a forecast

Coverage is the honest form of the penetration argument. At 8x you may talk
about marketing; at 1.5x the market size IS the risk and the ramp in the config
is fiction.

`fill_years` is a ceiling on speed, not a prediction. A club does not fill as
fast as its catchment allows -- members join after the circuit is built and the
thing is proven, which is what the ramp in the config encodes. Read fill_years
as "the pool cannot fill it faster than this", and if it exceeds the ramp the
config is promising something the market cannot supply.

THE FUNNEL, and why each step is where it is
--------------------------------------------

    HNW households within 90 minutes           the pool, a site attribute
      x collector_share                        own a car worth tracking
      x track_active_share                     actually drive it on a circuit
      = addressable

    addressable
      x (1 - incumbent_capture)                seats the competition already has
      x reachable_share                        will consider a club at this price
      = capturable

Incumbent capture is derived, not assumed flat: a club 9 miles away competes for
the same wallet far harder than one 100 miles away, and the model says so.

EVERY RATE HERE IS ASSUMED. They are benchmark-shaped judgments, not measured
conversion rates, and they are the second-largest open item in the project after
the club economics comps. The point of the module is not that 2.4% is right; it
is that the same 2.4% applied to fifteen catchments ranks them honestly, and
that `demand_break_even` reports what the rate would have to fall to before the
deal fails. That number is decision-relevant even when the input is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Marque clubs and collector dealers are a recruiting CHANNEL, not additional
# demand -- their members are already inside the HNW pool. They change how much
# of the pool you can actually reach, so they lift `reachable_share` rather than
# adding to `addressable`. Double-counting them was the obvious wrong turn here.
CHANNEL_LIFT_PER_MARQUE_CLUB = 0.012
CHANNEL_LIFT_PER_DEALER = 0.008
MAX_CHANNEL_LIFT = 0.35


@dataclass
class DemandResult:
    parcel_id: str
    hnw_households: int
    addressable: float
    capturable: float
    required_members: int
    coverage: float
    incumbent_capture: float
    reachable_share: float
    joins_per_year: float
    fill_years: float            # FLOOR on time to fill, set by pool size
    ramp_supported: bool
    verdict: str
    notes: list[str] = field(default_factory=list)


def _cfg(cfg: dict[str, Any]) -> dict[str, Any]:
    d = cfg.get("demand")
    if not d:
        raise KeyError("config is missing the `demand` block")
    return d


def incumbent_capture(cfg: dict[str, Any], parcel: dict[str, Any]) -> float:
    """
    Share of the addressable pool already sitting in a competing club.

    Distance-decayed, because proximity is what makes a competitor a competitor.
    A club at 9 miles takes the full share; one at or beyond the decay radius
    takes none of it. `nearest_motorsport_club_mi` of 100 in the target file is
    the sentinel for "nothing in the club format within 100 miles", so a site
    with no competitor correctly lands at zero.
    """
    d = _cfg(cfg)
    full = float(d["incumbent_capture_at_zero_mi"])
    radius = float(d["incumbent_decay_radius_mi"])
    miles = parcel.get("nearest_motorsport_club_mi")
    if miles is None:
        return full * 0.5          # unknown competitor distance: split the difference
    frac = max(0.0, 1.0 - float(miles) / radius)
    return full * frac


def reachable_share(cfg: dict[str, Any], parcel: dict[str, Any]) -> float:
    """
    Share of the un-captured addressable pool that a founding campaign can
    actually put in front of an offer, lifted by the recruiting infrastructure
    already in the catchment.
    """
    d = _cfg(cfg)
    base = float(d["reachable_share_base"])
    lift = (CHANNEL_LIFT_PER_MARQUE_CLUB * float(parcel.get("marque_clubs_in_catchment") or 0)
            + CHANNEL_LIFT_PER_DEALER * float(parcel.get("exotic_dealers_in_catchment") or 0))
    return base * (1.0 + min(lift, MAX_CHANNEL_LIFT))


def assess(cfg: dict[str, Any], parcel: dict[str, Any]) -> DemandResult:
    d = _cfg(cfg)
    m = cfg["income"]["membership"]
    cap = int(m["cap"])
    notes: list[str] = []

    hnw = int(parcel.get("hnw_households_90min") or 0)
    addressable = hnw * float(d["collector_share"]) * float(d["track_active_share"])

    inc = incumbent_capture(cfg, parcel)
    reach = reachable_share(cfg, parcel)
    capturable = addressable * (1.0 - inc) * reach

    coverage = capturable / cap if cap else 0.0

    # The ramp is a config input; this asks whether the catchment can feed it.
    # Joins are limited by how fast a sales team converts a reachable prospect,
    # not by how fast the club would like to fill.
    joins = capturable * float(d["annual_join_rate"])
    fill_years = (cap / joins) if joins > 0 else float("inf")

    ramp = list(m["ramp"])
    first_year_ask = float(ramp[0]) if ramp else 0.0
    ramp_supported = joins >= first_year_ask

    notes.append(f"{hnw:,} HNW households -> {addressable:,.0f} addressable at "
                 f"{d['collector_share']:.1%} collector x {d['track_active_share']:.0%} "
                 f"track-active")
    miles = parcel.get("nearest_motorsport_club_mi")
    notes.append(
        f"incumbent capture {inc:.0%}"
        + (f" ({parcel.get('nearest_motorsport_club_name') or 'competitor'} at "
           f"{float(miles):.0f} mi)" if miles is not None else " (competitor distance unknown)"))
    notes.append(f"reachable {reach:.0%} after channel lift from "
                 f"{int(parcel.get('marque_clubs_in_catchment') or 0)} marque clubs and "
                 f"{int(parcel.get('exotic_dealers_in_catchment') or 0)} dealers")
    notes.append(f"capturable {capturable:,.0f} against {cap} seats -> {coverage:.1f}x coverage")
    notes.append(f"{joins:,.0f} joins/yr at a {d['annual_join_rate']:.0%} annual conversion; "
                 f"ramp year 1 asks for {first_year_ask:.0f}")

    thin, comfortable = d["coverage_thin"], d["coverage_comfortable"]
    if coverage < thin:
        verdict = (f"DEMAND-CONSTRAINED — {coverage:.1f}x coverage is below the {thin:.0f}x "
                   f"floor. Market size is the risk here, not marketing.")
    elif not ramp_supported:
        verdict = (f"RAMP-CONSTRAINED — {coverage:.1f}x coverage is adequate but the catchment "
                   f"feeds {joins:,.0f} joins a year against a year-1 ramp of {first_year_ask:.0f}. "
                   f"The pool is there; the config fills it faster than a sales team can.")
    elif coverage >= comfortable:
        verdict = (f"DEMAND-COMFORTABLE — {coverage:.1f}x coverage and {joins:,.0f} joins a year "
                   f"against a {first_year_ask:.0f} year-1 ramp.")
    else:
        verdict = (f"DEMAND-ADEQUATE — {coverage:.1f}x coverage, above the {thin:.0f}x floor and "
                   f"below the {comfortable:.0f}x comfortable mark.")

    return DemandResult(
        parcel_id=str(parcel.get("parcel_id", "UNKNOWN")),
        hnw_households=hnw, addressable=addressable, capturable=capturable,
        required_members=cap, coverage=coverage, incumbent_capture=inc,
        reachable_share=reach, joins_per_year=joins, fill_years=fill_years,
        ramp_supported=ramp_supported, verdict=verdict, notes=notes,
    )


def demand_break_even(cfg: dict[str, Any], parcel: dict[str, Any]) -> dict[str, float]:
    """
    How wrong can the funnel be before the club cannot be filled?

    This is the number that survives the inputs being assumed. It reports the
    collector share, the track-active share and the reachable share at which
    coverage falls to exactly 1.0x -- one capturable prospect per seat, which is
    the point where the club sells out only if literally everyone reachable
    joins. Anything at or below that is not a marketing problem.
    """
    d = _cfg(cfg)
    r = assess(cfg, parcel)
    if r.coverage <= 0:
        return {"shrink_factor": 0.0, "collector_share": 0.0,
                "track_active_share": 0.0, "reachable_share": 0.0}
    shrink = 1.0 / r.coverage       # multiply any one rate by this to reach 1.0x
    return {
        "shrink_factor": shrink,
        "collector_share": float(d["collector_share"]) * shrink,
        "track_active_share": float(d["track_active_share"]) * shrink,
        "reachable_share": r.reachable_share * shrink,
    }


def portfolio(cfg: dict[str, Any], parcels: list[dict[str, Any]]) -> list[DemandResult]:
    return sorted((assess(cfg, p) for p in parcels), key=lambda r: -r.coverage)
