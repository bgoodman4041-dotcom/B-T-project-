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

Property tax is ad valorem, so NOI depends on the basis. That does NOT break
the closed form -- because the tax is proportional, it is equivalent to adding
tau to the required yield:

    (NOI_0 - tau*B) / B = h   =>   B = NOI_0 / (h + tau)

Inverting for L, with y = h + tau:

    gross:  G* = NOI_0 / y                        then L* = G*/(1+k) - S
    net:    G* = (NOI_0 + h*(P + Y)) / y          then L* = G*/(1+k) - S

Both are exact. No solver, no iteration.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "underwriting_inputs.yaml"

InitiationMode = Literal["amortized", "excluded", "capitalized"]
YoCBasis = Literal["gross", "net"]

# Pass/fail decisions compare floats against a threshold. A deal solved to sit
# exactly ON its covenant lands a couple of ulps below it -- 1.2999999999999998
# against a 1.30 floor -- and an exact `>=` then reports a compliant deal as a
# breach. Every threshold comparison goes through `_at_least`.
_BOUNDARY_TOL = 1e-9


def _at_least(value: float, floor: float) -> bool:
    """True when `value` meets `floor` within floating-point tolerance."""
    if value != value:                      # nan never clears
        return False
    return value >= floor - abs(floor) * _BOUNDARY_TOL - _BOUNDARY_TOL


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


def season_factor(cfg: dict[str, Any]) -> float:
    """
    Multiplier on track-dependent ancillary revenue for the site's usable season.

    Only `ancillary_elasticity` of ancillary revenue moves with the season --
    indoor storage and the service department earn year-round, track rental and
    driving school do not. Returns 1.0 when no season block is configured.
    """
    sn = cfg["income"].get("season")
    if not sn:
        return 1.0
    days = float(cfg["income"].get("season_days") or sn["baseline_days"])
    base = float(sn["baseline_days"])
    e = float(sn["ancillary_elasticity"])
    return (1 - e) + e * (days / base)


def opex_season_factor(cfg: dict[str, Any], member_fraction: float = 1.0) -> float:
    """
    Multiplier on club opex for the site's usable season.

    The counterpart to `season_factor`. `opex_elasticity` is the usage-variable
    share -- safety crew, corner workers, consumables, track prep, hourly staff.
    The remainder (insurance, admin, fixed maintenance) is indifferent to how
    many days the gates are open.

    The uplift is attenuated by member penetration for the same reason the
    revenue side is: a half-full club open 310 days does not run a full calendar
    of events, so it does not spend the full incremental crew cost. Applying the
    uplift at full force against an ancillary line already discounted by `frac`
    is a one-sided charge -- it erased the entire long-season advantage and put
    a 210-day Northeast site back on top of a 310-day one, which is not what the
    physical difference between those two sites actually is.

    Returns exactly 1.0 at the baseline season, so the flat-opex rule is
    preserved unchanged for any site at 210 days and for any config without a
    season block.
    """
    sn = cfg["income"].get("season")
    if not sn:
        return 1.0
    days = float(cfg["income"].get("season_days") or sn["baseline_days"])
    base = float(sn["baseline_days"])
    e = float(sn.get("opex_elasticity", 0.0))
    return 1.0 + e * (days / base - 1.0) * member_fraction


def site_config(cfg: dict[str, Any], parcel: dict[str, Any]) -> dict[str, Any]:
    """
    Overlay site-specific economics onto the national base case.

    Exactly three inputs travel with the dirt rather than with the program:

      season_days                  weather, and it moves ancillary revenue
      property_tax_effective_rate  local statute, and it moves tau directly
      property_tax_abatement_pct   whether a PILOT reaches this use at all

    The 50% abatement in the base case is NY-IDA-specific. Florida and Nevada
    have no comparable mechanism for a private recreation use, so a nationwide
    comparison that carries the abatement everywhere flatters the Sun Belt sites
    on top of an advantage they already have from the season. Sites that specify
    nothing get the national defaults, so this is a no-op for the base case.

    Returns `cfg` itself when there is nothing to override -- callers must not
    mutate the result.
    """
    keys = ("season_days", "property_tax_effective_rate", "property_tax_abatement_pct")
    if not any(parcel.get(k) is not None for k in keys):
        return cfg

    out = copy.deepcopy(cfg)
    if parcel.get("season_days") is not None:
        out["income"]["season_days"] = int(parcel["season_days"])
    pt = out["income"]["property_tax"]
    if parcel.get("property_tax_effective_rate") is not None:
        pt["effective_rate"] = float(parcel["property_tax_effective_rate"])
    if parcel.get("property_tax_abatement_pct") is not None:
        pt["abatement_pct"] = float(parcel["property_tax_abatement_pct"])
    return out


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

    # Ancillary scales with member penetration -- an empty club sells no track
    # days -- and with SEASON LENGTH, because a circuit that is unusable four
    # months a year cannot sell the same throughput. `season_factor` is 1.0 at
    # the baseline; a Sun Belt site above 300 usable days earns materially more
    # off the same physical plant, which is the whole economic case for going
    # national rather than staying in the Northeast.
    ancillary = sum(inc["ancillary_annual_usd"].values()) * frac * infl * season_factor(cfg)

    egi = dues + initiation + ancillary

    # Opex does NOT ramp with membership. You insure, mow, and maintain the full
    # circuit from day one regardless of how many members have joined.
    #
    # It DOES scale with season length, and only partly. Insurance, admin and
    # the debt-like fixed base are indifferent to how many days the gates are
    # open; safety crews, corner workers, consumables, track prep and hourly
    # staff are not. Lifting ancillary revenue with the season while holding
    # opex flat would hand every Sun Belt site a margin it has not earned --
    # a 310-day site would show a 44% operating ratio where a 210-day site
    # shows 48% off the identical cost base.
    opex = sum(inc["opex_annual_usd"].values()) * infl * opex_season_factor(cfg, frac)

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
    carry_years: float = 0.0       # the period k was actually built from

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
    site_cost_premium: float = 0.0,
) -> CostStack:
    """
    `track_cost_per_mile` override exists so the sensitivity grid can flex it.

    `site_cost_premium` carries the SITE-SPECIFIC delta to non-land cost --
    remediation, blasting, utility extension, less the credit for existing
    pavement. Without it every candidate site solves to an identical land price,
    which is the single fastest way to lose a reader's trust in a site ranking.
    """
    cost = cfg["cost"]
    tr = cost["track"]
    per_mile = track_cost_per_mile if track_cost_per_mile is not None else tr["hard_cost_per_mile_usd"]

    hard = (
        tr["miles"] * per_mile
        + tr["paddock_and_pit_usd"]
        + sum(cost["vertical_hard_usd"].values())
        + sum(cost["site_infrastructure_usd"].values())
        + for_sale.total_vertical_cost
        + site_cost_premium
    )
    soft = hard * cost["soft_cost_pct_of_hard"]
    contingency = (hard + soft) * cost["contingency_pct"]
    entitlement = cost["entitlement_budget_usd"]
    ffe = cost["ffe_usd"]

    S = hard + soft + entitlement + ffe + contingency

    ca = cost["carry"]
    # In a merchant build the capital stays outstanding until the last unit
    # sells, so a sell-out longer than the construction period extends the
    # carry. Without this the absorption axis of the sensitivity grid has no
    # channel to yield at all -- sell-out could stretch from 5 to 24 years and
    # the cost basis would not move.
    carry_years = ca["development_years"]
    if ca.get("follows_absorption", False):
        carry_years = max(carry_years, for_sale.sellout_years)
    k = ca["interest_rate"] * ca["avg_outstanding_pct"] * carry_years

    return CostStack(
        hard=hard,
        soft=soft,
        entitlement=entitlement,
        ffe=ffe,
        contingency=contingency,
        non_land_subtotal=S,
        carry_factor=k,
        incentives=cost["incentives_usd"],
        carry_years=carry_years,
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
    stabilized_noi: float            # PRE-TAX
    year5_noi: float                 # PRE-TAX
    tax_load: float                  # tau, as a fraction of gross basis
    property_tax_at_max_land: float
    stabilized_noi_after_tax: float

    cost: CostStack = field(repr=False)
    for_sale: ForSaleResult = field(repr=False)

    # Land prices are solved at the BINDING yield -- the tighter of the equity
    # hurdle and the DSCR-implied yield. `*_yield_only` isolates the hurdle so
    # the two constraints can be reported separately.
    max_land_gross: float
    max_land_net: float
    max_land_gross_yield_only: float
    max_land_gross_dscr_only: float
    required_yield: float
    binding_constraint: str          # "YIELD" | "DSCR"

    yoc_gross_at_ask: float | None
    yoc_net_at_ask: float | None
    yoc_gross_year5: float | None
    yoc_net_year5: float | None
    dscr_gross_at_ask: float | None
    dscr_net_at_ask: float | None
    dscr_cleared: bool

    dev_spread_gross_bps: float | None
    dev_spread_net_bps: float | None

    headroom_gross: float | None   # max supportable - ask, on the ranking basis
    price_infeasible: bool
    hurdle_cleared: bool

    @property
    def ranking_yoc(self) -> float | None:
        return self.yoc_gross_at_ask


def tax_load(cfg: dict[str, Any]) -> float:
    """
    Ad-valorem property tax expressed as a fraction of the GROSS cost basis.

        tau = taxable_share x assessment_ratio x effective_rate x (1 - abatement)

    Because the tax is proportional to the basis, netting it out of NOI is
    algebraically identical to adding tau to the required yield:

        (NOI_0 - tau*B) / B = h   =>   B = NOI_0 / (h + tau)

    That is why an omitted tax line does not just shave NOI -- it shifts the
    entire required-yield test, and why the closed-form land solve survives.
    """
    pt = cfg["income"]["property_tax"]
    return (
        pt["taxable_share_of_gross_basis"]
        * pt["assessment_ratio"]
        * pt["effective_rate"]
        * (1 - pt["abatement_pct"])
    )


def property_tax_annual(cfg: dict[str, Any], gross_basis: float) -> float:
    """Annual tax bill at a given gross basis. Never negative."""
    return tax_load(cfg) * max(0.0, gross_basis)


def noi_after_tax(noi_pretax: float, cfg: dict[str, Any], gross_basis: float) -> float:
    return noi_pretax - property_tax_annual(cfg, gross_basis)


def mortgage_constant(rate: float, amort_years: float, periods_per_year: int = 12) -> float:
    """
    Annual debt service per dollar of loan on a fully-amortizing note.

        MC = m * i / (1 - (1+i)^-n)      i = rate/m,  n = amort_years * m

    Interest-only is the rate itself; a zero rate is straight principal return.
    """
    if amort_years <= 0:
        raise ValueError("amortization_years must be positive")
    m = periods_per_year
    i = rate / m
    n = amort_years * m
    if i == 0:
        return 1.0 / amort_years
    return m * i / (1 - (1 + i) ** -n)


def dscr_implied_yield(cfg: dict[str, Any]) -> float:
    """
    The yield on cost a deal must produce just to satisfy the DSCR covenant.

        DSCR = NOI / (LTC x basis x MC) >= min_dscr
          =>  NOI / basis >= min_dscr x LTC x MC

    The right-hand side is a *yield*, directly comparable to the equity
    hurdle -- which makes the two constraints commensurable and lets the
    tighter one bind without a second inversion.
    """
    d = cfg["debt"]
    mc = mortgage_constant(
        d["permanent_rate"], d["amortization_years"], d.get("periods_per_year", 12)
    )
    return d["min_dscr"] * d["target_ltc"] * mc


def binding_yield(cfg: dict[str, Any]) -> tuple[float, str]:
    """Return (required yield, which constraint set it)."""
    hurdle = cfg["meta"]["hurdle_yoc"]
    implied = dscr_implied_yield(cfg)
    return (implied, "DSCR") if implied > hurdle else (hurdle, "YIELD")


def dscr_at(
    noi: float,
    land_price: float,
    cost: CostStack,
    for_sale: ForSaleResult,
    cfg: dict[str, Any],
    basis: YoCBasis,
) -> float:
    """
    Debt service coverage at a stated land price. Loan is sized as LTC x the
    same cost basis under test, so gross and net DSCR mirror gross and net YoC.
    """
    d = cfg["debt"]
    g = cost.gross_basis(land_price)
    b = g if basis == "gross" else cost.net_basis(land_price, for_sale.net_proceeds)
    if b <= 0:
        return float("inf")      # no basis to lever: coverage is unbounded
    # Property tax is an operating expense; coverage is tested after it.
    noi = noi_after_tax(noi, cfg, g)
    mc = mortgage_constant(
        d["permanent_rate"], d["amortization_years"], d.get("periods_per_year", 12)
    )
    debt_service = d["target_ltc"] * b * mc
    if debt_service <= 0:
        return float("inf")
    return noi / debt_service


def max_supportable_land_price(
    noi: float,
    cost: CostStack,
    for_sale: ForSaleResult,
    hurdle: float,
    basis: YoCBasis,
    cfg: dict[str, Any] | None = None,
) -> float:
    """
    The price at which YoC equals the hurdle exactly, solved AFTER property tax.
    This number is the deliverable -- the ask is only ever measured against it.

    `noi` is PRE-TAX NOI. With tau = tax_load(cfg), the gross test

        (NOI_0 - tau*G) / G = h

    solves to G* = NOI_0 / (h + tau), and the net test

        (NOI_0 - tau*G) / (G - P - Y) = h

    solves to G* = (NOI_0 + h*(P + Y)) / (h + tau). Both then unwind through
    the carry factor to a land price. Passing cfg=None sets tau to zero, which
    isolates the pre-tax answer for diagnostics.

    Can and does go negative on weak sites: that means the income stack cannot
    carry the vertical even if the dirt were free. A negative result is a real
    answer, not an error, and gets reported as such.
    """
    tau = tax_load(cfg) if cfg is not None else 0.0
    denom = hurdle + tau
    if denom <= 0:
        raise ValueError("required yield plus tax load must be positive")

    if basis == "gross":
        gross_star = noi / denom
    elif basis == "net":
        gross_star = (noi + hurdle * (for_sale.net_proceeds + cost.incentives)) / denom
    else:
        raise ValueError(f"unknown basis: {basis}")

    return gross_star / (1 + cost.carry_factor) - cost.non_land_subtotal


def yield_on_cost(
    noi: float,
    land_price: float,
    cost: CostStack,
    for_sale: ForSaleResult,
    basis: YoCBasis,
    cfg: dict[str, Any] | None = None,
) -> float:
    """
    YoC at a stated land price, computed on NOI AFTER property tax. `noi` is
    pre-tax. Negative basis returns -inf, not a crash.
    """
    g = cost.gross_basis(land_price)
    if basis == "gross":
        b = g
    elif basis == "net":
        b = cost.net_basis(land_price, for_sale.net_proceeds)
    else:
        raise ValueError(f"unknown basis: {basis}")
    if b <= 0:
        return float("-inf")
    if cfg is not None:
        noi = noi_after_tax(noi, cfg, g)
    return noi / b


def underwrite(
    cfg: dict[str, Any],
    parcel_id: str,
    ask_price: float | None = None,
    initiation_mode: InitiationMode | None = None,
    track_cost_per_mile: float | None = None,
    horizon: int = 10,
    site_cost_premium: float = 0.0,
) -> UnderwritingResult:
    """Run both stacks on one parcel and solve the land price."""
    hurdle = cfg["meta"]["hurdle_yoc"]
    rank_basis: YoCBasis = cfg["mandate"]["yoc_basis"]["rank_on"]
    required, binding = binding_yield(cfg)
    min_dscr = cfg["debt"]["min_dscr"]

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
    cost = build_cost_stack(cfg, for_sale, track_cost_per_mile, site_cost_premium)

    # Solve at the binding constraint, and keep the two components visible.
    max_gross = max_supportable_land_price(
        stabilized_noi, cost, for_sale, required, "gross", cfg)
    max_net = max_supportable_land_price(
        stabilized_noi, cost, for_sale, required, "net", cfg)
    max_gross_yield = max_supportable_land_price(
        stabilized_noi, cost, for_sale, hurdle, "gross", cfg)
    max_gross_dscr = max_supportable_land_price(
        stabilized_noi, cost, for_sale, dscr_implied_yield(cfg), "gross", cfg)

    if ask_price is None:
        yg = yn = yg5 = yn5 = None
        dscr_g = dscr_n = None
        dscr_ok = False
        spread_g = spread_n = None
        headroom = None
        infeasible = False
        cleared = False
    else:
        yg = yield_on_cost(stabilized_noi, ask_price, cost, for_sale, "gross", cfg)
        yn = yield_on_cost(stabilized_noi, ask_price, cost, for_sale, "net", cfg)
        yg5 = yield_on_cost(year5_noi, ask_price, cost, for_sale, "gross", cfg)
        yn5 = yield_on_cost(year5_noi, ask_price, cost, for_sale, "net", cfg)

        exit_cap = cfg["income"]["exit_cap"]
        spread_g = (yg - exit_cap) * 10_000 if yg != float("-inf") else None
        spread_n = (yn - exit_cap) * 10_000 if yn != float("-inf") else None

        dscr_g = dscr_at(stabilized_noi, ask_price, cost, for_sale, cfg, "gross")
        dscr_n = dscr_at(stabilized_noi, ask_price, cost, for_sale, cfg, "net")
        dscr_on_rank = dscr_g if rank_basis == "gross" else dscr_n
        dscr_ok = _at_least(dscr_on_rank, min_dscr)

        max_on_rank = max_gross if rank_basis == "gross" else max_net
        headroom = max_on_rank - ask_price
        # §3: ask exceeding max supportable by >20% is PRICE-INFEASIBLE.
        # A non-positive max means no price clears -- infeasible by definition.
        infeasible = max_on_rank <= 0 or ask_price > max_on_rank * 1.20
        # "Cleared" now means BOTH tests pass: the equity hurdle and the
        # covenant. A deal that yields 6.6% but covers at 1.15x is not financeable.
        cleared = _at_least(yg if rank_basis == "gross" else yn, hurdle) and dscr_ok

    return UnderwritingResult(
        parcel_id=parcel_id,
        ask_price=ask_price,
        stabilization_year=stab_year,
        stabilized_noi=stabilized_noi,
        year5_noi=year5_noi,
        tax_load=tax_load(cfg),
        property_tax_at_max_land=property_tax_annual(cfg, cost.gross_basis(max_gross)),
        stabilized_noi_after_tax=noi_after_tax(
            stabilized_noi, cfg, cost.gross_basis(max_gross)),
        cost=cost,
        for_sale=for_sale,
        max_land_gross=max_gross,
        max_land_net=max_net,
        max_land_gross_yield_only=max_gross_yield,
        max_land_gross_dscr_only=max_gross_dscr,
        required_yield=required,
        binding_constraint=binding,
        yoc_gross_at_ask=yg,
        yoc_net_at_ask=yn,
        yoc_gross_year5=yg5,
        yoc_net_year5=yn5,
        dscr_gross_at_ask=dscr_g,
        dscr_net_at_ask=dscr_n,
        dscr_cleared=dscr_ok,
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
            # Both axes must be applied. Chaining these with `or` short-circuits
            # the moment the x axis returns a per-mile override, silently
            # dropping the y axis and producing a grid with identical rows.
            per_mile_x = apply(c, x_key, xv)
            per_mile_y = apply(c, y_key, yv)
            per_mile = per_mile_x if per_mile_x is not None else per_mile_y
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
    cfg: dict[str, Any] | None = None,
) -> float:
    """PRE-TAX NOI needed to hit the hurdle at a given land price, after tax."""
    tau = tax_load(cfg) if cfg is not None else 0.0
    g = cost.gross_basis(land_price)
    if basis == "gross":
        return hurdle * g + tau * g
    if basis == "net":
        return hurdle * cost.net_basis(land_price, for_sale.net_proceeds) + tau * g
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
    req_yield, binding = binding_yield(cfg)
    implied = dscr_implied_yield(cfg)

    r = underwrite(cfg, parcel_id="DIAGNOSTIC")
    required = noi_required_for_feasibility(
        r.cost, r.for_sale, req_yield, rank_basis, 0.0, cfg)
    actual = r.stabilized_noi
    max_land = r.max_land_gross if rank_basis == "gross" else r.max_land_net

    test = (f"{hurdle:.2%} equity hurdle" if binding == "YIELD"
            else f"{implied:.2%} DSCR-implied yield "
                 f"({cfg['debt']['min_dscr']:.2f}x at {cfg['debt']['target_ltc']:.0%} LTC)")

    return {
        "basis": rank_basis,
        "hurdle": hurdle,
        "dscr_implied_yield": implied,
        "required_yield": req_yield,
        "binding_constraint": binding,
        "min_dscr": cfg["debt"]["min_dscr"],
        "mortgage_constant": mortgage_constant(
            cfg["debt"]["permanent_rate"], cfg["debt"]["amortization_years"],
            cfg["debt"].get("periods_per_year", 12)),
        "tax_load": tax_load(cfg),
        "stabilized_noi": actual,
        "stabilized_noi_after_tax": r.stabilized_noi_after_tax,
        "property_tax_annual": r.property_tax_at_max_land,
        "noi_required_at_zero_land": required,
        "noi_gap": required - actual,
        "noi_multiple_required": (required / actual) if actual > 0 else float("inf"),
        "max_supportable_land": max_land,
        "program_feasible": max_land > 0,
        "non_land_cost": r.cost.non_land_subtotal,
        "for_sale_net_proceeds": r.for_sale.net_proceeds,
        "verdict": (
            f"Program clears on {rank_basis} basis with ${max_land:,.0f} of land "
            f"headroom. Binding test: {test}."
            if max_land > 0
            else (
                f"PROGRAM-INFEASIBLE on {rank_basis} basis. Stabilized NOI of "
                f"${actual:,.0f} must reach ${required:,.0f} "
                f"({required / actual:.2f}x) before free land clears the binding "
                f"test ({test}). No parcel can fix this -- the revenue or cost "
                f"assumptions must move."
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
