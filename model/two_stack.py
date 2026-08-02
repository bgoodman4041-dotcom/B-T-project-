"""
TRACK BOSS — Two-Stack Underwriting Model
=========================================

Stack A (for-sale): garage condos + homesites. Velocity, not yield.
Stack B (income):   dues, track rental, school, storage, F&B, service. The 6.5% test.

The land price is never an input. It is the SOLVED variable: for every parcel we
report the maximum supportable land price -- the price at which YoC lands exactly
on the hurdle. The ask is then measured against that number.

Cost algebra
------------
    hard  = track + paddock + vertical + site infrastructure + for-sale vertical
    soft  = soft_pct x hard
    cont  = cont_pct x (hard + soft)
    S     = hard + soft + entitlement + ffe + cont          (all non-land cost)
    k     = rate x avg_outstanding x years                  (carry factor)

    gross_basis(L) = (L + S) x (1 + k)
    net_basis(L)   = gross_basis(L) - P - G

where P is net for-sale proceeds after cost of sale and G is any capital
incentive offset. Carry accrues on land too, which is why it multiplies the sum
rather than sitting inside S.

Inverting YoC = NOI / basis = h for L:

    gross:  L* = NOI / (h x (1 + k)) - S
    net:    L* = (NOI / h + P + G) / (1 + k) - S

Both are exact. No solver, no iteration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "underwriting_inputs.yaml"

InitiationMode = Literal["amortized", "excluded", "capitalized"]
YoCBasis = Literal["gross", "net"]


# =============================================================================
# Config loading
# =============================================================================

def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load the underwriting inputs. Fails loud -- a missing config is a bug."""
    p = Path(path) if path else CONFIG_PATH
    with p.open() as fh:
        cfg = yaml.safe_load(fh)
    _validate_config(cfg)
    return cfg


def _validate_config(cfg: dict[str, Any]) -> None:
    weights = cfg["scoring"]["weights"]
    total = sum(weights.values())
    if total != 100:
        raise ValueError(f"Composite score weights must total 100, got {total}")

    acre = cfg["mandate"]["acreage"]
    if acre["hard_floor_acres"] > acre["preferred_floor_acres"]:
        raise ValueError("hard_floor_acres cannot exceed preferred_floor_acres")

    dt = cfg["mandate"]["drive_time"]
    if dt["prize_minutes"] > dt["max_minutes"]:
        raise ValueError("prize_minutes cannot exceed max_minutes")

    if not 0 < cfg["meta"]["hurdle_yoc"] < 1:
        raise ValueError("hurdle_yoc must be a decimal fraction, e.g. 0.065")


# =============================================================================
# Stack B -- income
# =============================================================================

@dataclass
class YearResult:
    """One operating year of Stack B."""
    year: int
    members: int
    member_fraction: float
    dues_revenue: float
    initiation_recognized: float
    ancillary_revenue: float
    egi: float
    opex: float
    management_fee: float
    replacement_reserve: float
    noi: float


def membership_schedule(cfg: dict[str, Any], years: int) -> list[int]:
    """Cumulative member count by operating year, clamped at cap."""
    m = cfg["income"]["membership"]
    cap = m["cap"]
    ramp = m["ramp"]
    out: list[int] = []
    cum = 0
    for i in range(years):
        add = ramp[i] if i < len(ramp) else 0
        cum = min(cap, cum + add)
        out.append(cum)
    return out


def stabilization_year(cfg: dict[str, Any], horizon: int = 20) -> int:
    """
    First operating year in which membership reaches the stabilization
    threshold (default 85% of cap). Returns -1 if the ramp never gets there.
    """
    m = cfg["income"]["membership"]
    target = m["cap"] * m["stabilization_threshold"]
    for i, members in enumerate(membership_schedule(cfg, horizon), start=1):
        if members >= target:
            return i
    return -1


def _initiation_recognized(
    cfg: dict[str, Any],
    year: int,
    schedule: list[int],
    mode: InitiationMode,
) -> float:
    """
    Initiation fee recognized in `year`.

    §3 forbids capitalizing initiation into NOI. Base case amortizes each
    joining cohort straight-line over expected tenure. `capitalized` and
    `excluded` exist only to draw the sensitivity bookends.
    """
    m = cfg["income"]["membership"]
    fee = m["initiation_fee_usd"]
    tenure = m["expected_tenure_years"]

    joins_this_year = schedule[year - 1] - (schedule[year - 2] if year >= 2 else 0)

    if mode == "excluded":
        return 0.0
    if mode == "capitalized":
        return joins_this_year * fee
    if mode != "amortized":
        raise ValueError(f"unknown initiation mode: {mode}")

    # Amortized: sum the slice from every cohort still inside its tenure window.
    recognized = 0.0
    for y in range(max(1, year - tenure + 1), year + 1):
        cohort = schedule[y - 1] - (schedule[y - 2] if y >= 2 else 0)
        recognized += cohort * fee / tenure
    return recognized


def project_year(
    cfg: dict[str, Any],
    year: int,
    schedule: list[int],
    initiation_mode: InitiationMode | None = None,
) -> YearResult:
    """Build one operating year of Stack B."""
    inc = cfg["income"]
    m = inc["membership"]
    cap = m["cap"]
    esc = m["dues_escalator"]
    mode: InitiationMode = initiation_mode or inc["initiation_treatment"]["mode"]

    members = schedule[year - 1]
    frac = members / cap if cap else 0.0
    infl = (1 + esc) ** (year - 1)

    dues = members * m["annual_dues_usd"] * infl
    initiation = _initiation_recognized(cfg, year, schedule, mode)

    # Ancillary scales with member penetration -- an empty club sells no track days.
    ancillary = sum(inc["ancillary_annual_usd"].values()) * frac * infl

    egi = dues + initiation + ancillary

    # Opex does NOT ramp. You insure, mow, and maintain the full circuit from
    # day one regardless of how many members have joined. Conservative and true.
    opex = sum(inc["opex_annual_usd"].values()) * infl

    mgmt = egi * inc["management_fee_pct_egi"]
    reserve = egi * inc["replacement_reserve_pct_egi"]
    noi = egi - opex - mgmt - reserve

    return YearResult(
        year=year,
        members=members,
        member_fraction=frac,
        dues_revenue=dues,
        initiation_recognized=initiation,
        ancillary_revenue=ancillary,
        egi=egi,
        opex=opex,
        management_fee=mgmt,
        replacement_reserve=reserve,
        noi=noi,
    )


def project_income(
    cfg: dict[str, Any],
    years: int = 10,
    initiation_mode: InitiationMode | None = None,
) -> list[YearResult]:
    schedule = membership_schedule(cfg, years)
    return [project_year(cfg, y, schedule, initiation_mode) for y in range(1, years + 1)]


# =============================================================================
# Stack A -- for-sale
# =============================================================================

@dataclass
class ForSaleResult:
    condo_gross_revenue: float
    condo_vertical_cost: float
    homesite_gross_revenue: float
    homesite_improvement_cost: float
    total_gross_revenue: float
    cost_of_sale: float
    net_proceeds: float            # after cost of sale, BEFORE vertical cost
    gross_margin_pct: float        # margin on the for-sale component alone
    sellout_years: float

    @property
    def total_vertical_cost(self) -> float:
        return self.condo_vertical_cost + self.homesite_improvement_cost


def project_for_sale(cfg: dict[str, Any]) -> ForSaleResult:
    """
    Stack A. Note the accounting boundary: vertical cost for the for-sale
    component lives in the HARD COST bucket (it is part of `S`), so
    `net_proceeds` is revenue net of selling cost only. Subtracting vertical
    cost here as well would double-count it.
    """
    fs = cfg["for_sale"]
    c, h = fs["garage_condos"], fs["homesites"]

    condo_rev = c["units"] * c["avg_sf"] * c["sale_price_psf"]
    condo_cost = c["units"] * c["avg_sf"] * c["hard_cost_psf"]
    condo_cos = condo_rev * c["cost_of_sale_pct"]

    home_rev = h["units"] * h["price_per_unit_usd"]
    home_cost = h["units"] * h["improvement_cost_per_unit_usd"]
    home_cos = home_rev * h["cost_of_sale_pct"]

    gross_rev = condo_rev + home_rev
    cos = condo_cos + home_cos
    net = gross_rev - cos
    vertical = condo_cost + home_cost
    margin = (net - vertical) / gross_rev if gross_rev else 0.0

    sellout = max(
        c["units"] / c["absorption_units_per_year"] if c["absorption_units_per_year"] else 0.0,
        h["units"] / h["absorption_units_per_year"] if h["absorption_units_per_year"] else 0.0,
    )

    return ForSaleResult(
        condo_gross_revenue=condo_rev,
        condo_vertical_cost=condo_cost,
        homesite_gross_revenue=home_rev,
        homesite_improvement_cost=home_cost,
        total_gross_revenue=gross_rev,
        cost_of_sale=cos,
        net_proceeds=net,
        gross_margin_pct=margin,
        sellout_years=sellout,
    )


# =============================================================================
# Cost stack
# =============================================================================

@dataclass
class CostStack:
    hard: float
    soft: float
    entitlement: float
    ffe: float
    contingency: float
    non_land_subtotal: float       # S
    carry_factor: float            # k
    incentives: float              # G

    def gross_basis(self, land_price: float) -> float:
        return (land_price + self.non_land_subtotal) * (1 + self.carry_factor)

    def net_basis(self, land_price: float, for_sale_net_proceeds: float) -> float:
        return self.gross_basis(land_price) - for_sale_net_proceeds - self.incentives

    def carry_dollars(self, land_price: float) -> float:
        return (land_price + self.non_land_subtotal) * self.carry_factor


def build_cost_stack(
    cfg: dict[str, Any],
    for_sale: ForSaleResult,
    track_cost_per_mile: float | None = None,
) -> CostStack:
    """`track_cost_per_mile` override exists so the sensitivity grid can flex it."""
    cost = cfg["cost"]
    tr = cost["track"]
    per_mile = track_cost_per_mile if track_cost_per_mile is not None else tr["hard_cost_per_mile_usd"]

    hard = (
        tr["miles"] * per_mile
        + tr["paddock_and_pit_usd"]
        + sum(cost["vertical_hard_usd"].values())
        + sum(cost["site_infrastructure_usd"].values())
        + for_sale.total_vertical_cost
    )
    soft = hard * cost["soft_cost_pct_of_hard"]
    contingency = (hard + soft) * cost["contingency_pct"]
    entitlement = cost["entitlement_budget_usd"]
    ffe = cost["ffe_usd"]

    S = hard + soft + entitlement + ffe + contingency

    ca = cost["carry"]
    k = ca["interest_rate"] * ca["avg_outstanding_pct"] * ca["development_years"]

    return CostStack(
        hard=hard,
        soft=soft,
        entitlement=entitlement,
        ffe=ffe,
        contingency=contingency,
        non_land_subtotal=S,
        carry_factor=k,
        incentives=cost["incentives_usd"],
    )


# =============================================================================
# The 6.5% test
# =============================================================================

@dataclass
class UnderwritingResult:
    """Everything the workbook and the memo need for one parcel."""
    parcel_id: str
    ask_price: float | None

    stabilization_year: int
    stabilized_noi: float
    year5_noi: float

    cost: CostStack = field(repr=False)
    for_sale: ForSaleResult = field(repr=False)

    max_land_gross: float
    max_land_net: float

    yoc_gross_at_ask: float | None
    yoc_net_at_ask: float | None
    yoc_gross_year5: float | None
    yoc_net_year5: float | None

    dev_spread_gross_bps: float | None
    dev_spread_net_bps: float | None

    headroom_gross: float | None   # max supportable - ask, on the ranking basis
    price_infeasible: bool
    hurdle_cleared: bool

    @property
    def ranking_yoc(self) -> float | None:
        return self.yoc_gross_at_ask


def max_supportable_land_price(
    noi: float,
    cost: CostStack,
    for_sale: ForSaleResult,
    hurdle: float,
    basis: YoCBasis,
) -> float:
    """
    The price at which YoC equals the hurdle exactly. This number is the
    deliverable -- the ask is only ever measured against it.

    Can and does go negative on weak sites: that means the income stack cannot
    carry the vertical even if the dirt were free. A negative result is a real
    answer, not an error, and gets reported as such.
    """
    if basis == "gross":
        return noi / (hurdle * (1 + cost.carry_factor)) - cost.non_land_subtotal
    if basis == "net":
        return (
            (noi / hurdle + for_sale.net_proceeds + cost.incentives)
            / (1 + cost.carry_factor)
            - cost.non_land_subtotal
        )
    raise ValueError(f"unknown basis: {basis}")


def yield_on_cost(
    noi: float,
    land_price: float,
    cost: CostStack,
    for_sale: ForSaleResult,
    basis: YoCBasis,
) -> float:
    """YoC at a stated land price. Negative basis returns -inf, not a crash."""
    if basis == "gross":
        b = cost.gross_basis(land_price)
    elif basis == "net":
        b = cost.net_basis(land_price, for_sale.net_proceeds)
    else:
        raise ValueError(f"unknown basis: {basis}")
    if b <= 0:
        return float("-inf")
    return noi / b


def underwrite(
    cfg: dict[str, Any],
    parcel_id: str,
    ask_price: float | None = None,
    initiation_mode: InitiationMode | None = None,
    track_cost_per_mile: float | None = None,
    horizon: int = 10,
) -> UnderwritingResult:
    """Run both stacks on one parcel and solve the land price."""
    hurdle = cfg["meta"]["hurdle_yoc"]
    rank_basis: YoCBasis = cfg["mandate"]["yoc_basis"]["rank_on"]

    years = project_income(cfg, years=horizon, initiation_mode=initiation_mode)
    stab_year = stabilization_year(cfg, horizon=horizon)
    if stab_year == -1:
        raise ValueError(
            f"Membership ramp never reaches "
            f"{cfg['income']['membership']['stabilization_threshold']:.0%} of cap "
            f"within {horizon} years -- fix the ramp before underwriting."
        )

    stabilized_noi = years[stab_year - 1].noi
    year5_noi = years[min(5, horizon) - 1].noi

    for_sale = project_for_sale(cfg)
    cost = build_cost_stack(cfg, for_sale, track_cost_per_mile)

    max_gross = max_supportable_land_price(stabilized_noi, cost, for_sale, hurdle, "gross")
    max_net = max_supportable_land_price(stabilized_noi, cost, for_sale, hurdle, "net")

    if ask_price is None:
        yg = yn = yg5 = yn5 = None
        spread_g = spread_n = None
        headroom = None
        infeasible = False
        cleared = False
    else:
        yg = yield_on_cost(stabilized_noi, ask_price, cost, for_sale, "gross")
        yn = yield_on_cost(stabilized_noi, ask_price, cost, for_sale, "net")
        yg5 = yield_on_cost(year5_noi, ask_price, cost, for_sale, "gross")
        yn5 = yield_on_cost(year5_noi, ask_price, cost, for_sale, "net")

        exit_cap = cfg["income"]["exit_cap"]
        spread_g = (yg - exit_cap) * 10_000 if yg != float("-inf") else None
        spread_n = (yn - exit_cap) * 10_000 if yn != float("-inf") else None

        max_on_rank = max_gross if rank_basis == "gross" else max_net
        headroom = max_on_rank - ask_price
        # §3: ask exceeding max supportable by >20% is PRICE-INFEASIBLE.
        # A non-positive max means no price clears -- infeasible by definition.
        infeasible = max_on_rank <= 0 or ask_price > max_on_rank * 1.20
        cleared = (yg if rank_basis == "gross" else yn) >= hurdle

    return UnderwritingResult(
        parcel_id=parcel_id,
        ask_price=ask_price,
        stabilization_year=stab_year,
        stabilized_noi=stabilized_noi,
        year5_noi=year5_noi,
        cost=cost,
        for_sale=for_sale,
        max_land_gross=max_gross,
        max_land_net=max_net,
        yoc_gross_at_ask=yg,
        yoc_net_at_ask=yn,
        yoc_gross_year5=yg5,
        yoc_net_year5=yn5,
        dev_spread_gross_bps=spread_g,
        dev_spread_net_bps=spread_n,
        headroom_gross=headroom,
        price_infeasible=infeasible,
        hurdle_cleared=cleared,
    )


# =============================================================================
# Sensitivity
# =============================================================================

def sensitivity_grid(
    cfg: dict[str, Any],
    x_key: str,
    y_key: str,
    basis: YoCBasis | None = None,
) -> dict[str, Any]:
    """
    Two-axis break-even surface. Each cell is the maximum supportable land price
    at that combination -- the surface the Sensitivity tab plots.

    Recognized axes: membership_cap, annual_dues_usd,
    track_hard_cost_per_mile_usd, absorption_years.
    """
    import copy

    hurdle = cfg["meta"]["hurdle_yoc"]
    basis = basis or cfg["mandate"]["yoc_basis"]["rank_on"]
    axes = cfg["sensitivity"]
    if x_key not in axes or y_key not in axes:
        raise ValueError(f"unknown sensitivity axis: {x_key} / {y_key}")

    def apply(base: dict[str, Any], key: str, val: Any) -> float | None:
        """Mutate a config copy for one axis value; return a per-mile override."""
        if key == "membership_cap":
            base["income"]["membership"]["cap"] = val
        elif key == "annual_dues_usd":
            base["income"]["membership"]["annual_dues_usd"] = val
        elif key == "track_hard_cost_per_mile_usd":
            return float(val)
        elif key == "absorption_years":
            fs = base["for_sale"]
            fs["garage_condos"]["absorption_units_per_year"] = max(
                1, round(fs["garage_condos"]["units"] / val)
            )
            fs["homesites"]["absorption_units_per_year"] = max(
                1, round(fs["homesites"]["units"] / val)
            )
        return None

    cells: list[list[float]] = []
    for yv in axes[y_key]:
        row: list[float] = []
        for xv in axes[x_key]:
            c = copy.deepcopy(cfg)
            per_mile = apply(c, x_key, xv) or apply(c, y_key, yv)
            try:
                r = underwrite(c, parcel_id="SENS", track_cost_per_mile=per_mile)
                row.append(r.max_land_gross if basis == "gross" else r.max_land_net)
            except ValueError:
                row.append(float("nan"))   # ramp broke at this cap; show as gap
        cells.append(row)

    return {
        "x_key": x_key,
        "y_key": y_key,
        "x_values": axes[x_key],
        "y_values": axes[y_key],
        "basis": basis,
        "hurdle": hurdle,
        "cells": cells,
    }


def noi_required_for_feasibility(
    cost: CostStack,
    for_sale: ForSaleResult,
    hurdle: float,
    basis: YoCBasis,
    land_price: float = 0.0,
) -> float:
    """Stabilized NOI needed to hit the hurdle at a given land price."""
    if basis == "gross":
        return hurdle * cost.gross_basis(land_price)
    if basis == "net":
        return hurdle * cost.net_basis(land_price, for_sale.net_proceeds)
    raise ValueError(f"unknown basis: {basis}")


def feasibility_diagnostic(cfg: dict[str, Any]) -> dict[str, Any]:
    """
    Program-level sanity check, run BEFORE any parcel is underwritten.

    If the max supportable land price is negative on the ranking basis, no
    parcel in NY/CT/NJ can clear the hurdle -- the problem is the program, not
    the dirt. This reports the NOI gap so the principal can see which lever
    (dues, cap, ancillary, or cost) has to move, and by how much.
    """
    hurdle = cfg["meta"]["hurdle_yoc"]
    rank_basis: YoCBasis = cfg["mandate"]["yoc_basis"]["rank_on"]

    r = underwrite(cfg, parcel_id="DIAGNOSTIC")
    required = noi_required_for_feasibility(r.cost, r.for_sale, hurdle, rank_basis, 0.0)
    actual = r.stabilized_noi
    max_land = r.max_land_gross if rank_basis == "gross" else r.max_land_net

    return {
        "basis": rank_basis,
        "hurdle": hurdle,
        "stabilized_noi": actual,
        "noi_required_at_zero_land": required,
        "noi_gap": required - actual,
        "noi_multiple_required": (required / actual) if actual > 0 else float("inf"),
        "max_supportable_land": max_land,
        "program_feasible": max_land > 0,
        "non_land_cost": r.cost.non_land_subtotal,
        "for_sale_net_proceeds": r.for_sale.net_proceeds,
        "verdict": (
            f"Program clears on {rank_basis} basis with "
            f"${max_land:,.0f} of land headroom."
            if max_land > 0
            else (
                f"PROGRAM-INFEASIBLE on {rank_basis} basis. Stabilized NOI of "
                f"${actual:,.0f} must reach ${required:,.0f} "
                f"({required / actual:.2f}x) before free land clears {hurdle:.2%}. "
                f"No parcel can fix this -- the revenue or cost assumptions must move."
            )
        ),
    }


def initiation_bookends(cfg: dict[str, Any], ask_price: float | None = None) -> dict[str, Any]:
    """
    §3 requires showing the initiation-fee sensitivity both ways. Returns the
    amortized base case flanked by fully-excluded and fully-capitalized.
    """
    out: dict[str, Any] = {}
    for mode in ("excluded", "amortized", "capitalized"):
        r = underwrite(cfg, parcel_id="INIT-SENS", ask_price=ask_price, initiation_mode=mode)
        out[mode] = {
            "stabilized_noi": r.stabilized_noi,
            "max_land_gross": r.max_land_gross,
            "max_land_net": r.max_land_net,
            "yoc_gross_at_ask": r.yoc_gross_at_ask,
            "yoc_net_at_ask": r.yoc_net_at_ask,
        }
    return out
