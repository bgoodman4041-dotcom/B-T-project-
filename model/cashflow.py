"""
TRACK BOSS — Development Cash Flow, Funding, and Return
======================================================

The two-stack model answers "what can I pay for the dirt". It does not answer
the three questions an investment committee asks next:

  1. **How much capital do I actually need, and when is the hole deepest?**
     Stabilized yield is silent on peak funding. A program can clear its yield
     test and still be unfinanceable because the trough is too deep.
  2. **Does the covenant hold in every year, or only at stabilization?**
     Lenders size on stabilized NOI but test coverage from conversion onward.
     The binding year is almost never the stabilized year.
  3. **What is the equity return, and is the asset worth more than it cost?**
     Yield on cost is not a return. A 7% yield built into an 8% exit cap
     destroys value no matter how clean the yield looks.

Timeline conventions (stated because they are choices, not facts)
----------------------------------------------------------------
* Year 1 is the first year of construction. Non-land cost `S` is spread evenly
  across `development_years`; land is paid in full at close.
* Operations begin the year after construction completes. Operating year 1 of
  the membership ramp is the first operating year.
* For-sale closings begin with operations and run over the sell-out period.
* Initiation fees are CASH when a member joins. They are not NOI -- §3 forbids
  that -- but they are a genuine source of funds during the ramp, and leaving
  them out overstates the equity requirement.
* Debt is a PLUG, not an additive source: it funds the gap between uses and
  non-debt sources, capped at LTC x the sizing basis. Treating it as additive
  on top of sale proceeds funds the same dollars twice.
* The permanent note is sized on the RETAINED asset (see
  `debt.permanent_sizing_basis`), because for-sale closings retire construction
  debt and the lender's collateral is only what is left.

Every one of these is conservative-leaning but arguable. They are inputs to a
discussion, not settled facts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .two_stack import (
    CostStack,
    UnderwritingResult,
    build_cost_stack,
    membership_schedule,
    project_for_sale,
    project_income,
    property_tax_annual,
)


def _operating_deficit(cfg: dict[str, Any], income: list[Any], annual_tax: float,
                      years: int) -> float:
    """Total cash needed to cover years where NOI after tax is negative."""
    total = 0.0
    for oy in range(1, years + 1):
        nat = income[oy - 1].noi - annual_tax
        if nat < 0:
            total += -nat
    return total


@dataclass
class PeriodCash:
    """One annual period on the development and operating timeline."""
    year: int
    phase: str                      # "construction" | "operating"
    members: int
    noi_pretax: float
    property_tax: float
    noi_after_tax: float
    initiation_cash: float
    for_sale_net_cash: float
    construction_draw: float        # negative: cash out
    land_payment: float             # negative: cash out
    debt_draw: float
    debt_service: float             # negative: cash out
    net_cash_flow: float
    cumulative_cash: float
    dscr: float | None              # None while no debt service is due

    @property
    def unlevered_cash_flow(self) -> float:
        return (self.noi_after_tax + self.initiation_cash + self.for_sale_net_cash
                + self.construction_draw + self.land_payment)


@dataclass
class SourcesAndUses:
    land: float
    non_land_cost: float
    carry: float
    operating_deficit_funded: float
    total_uses: float

    debt: float
    initiation_cash: float
    for_sale_net_proceeds: float
    incentives: float
    equity_required: float
    total_sources: float
    debt_capacity: float = 0.0          # permanent LTC cap
    funding_surplus: float = 0.0        # sources exceeding uses -- debt undrawn
    construction_facility: float = 0.0  # build-phase loan, sized on total cost

    @property
    def equity_share(self) -> float:
        return self.equity_required / self.total_uses if self.total_uses else 0.0


@dataclass
class CashFlowResult:
    periods: list[PeriodCash]
    sources_uses: SourcesAndUses

    peak_funding_requirement: float     # deepest cumulative hole, positive number
    peak_funding_year: int
    cumulative_operating_deficit: float # sum of negative operating-year NOI after tax
    deficit_years: int

    min_dscr: float | None
    min_dscr_year: int | None
    dscr_by_year: dict[int, float] = field(default_factory=dict)

    exit_value: float = 0.0
    exit_net_proceeds: float = 0.0
    debt_balance_at_exit: float = 0.0
    equity_at_exit: float = 0.0
    profit_on_cost: float = 0.0          # exit net proceeds less RETAINED cost
    value_to_cost: float = 0.0           # exit net proceeds / retained (net) cost
    retained_cost: float = 0.0
    equity_multiple: float = 0.0
    equity_irr: float | None = None
    breakeven_exit_cap: float | None = None
    peak_equity_requirement: float = 0.0   # what must actually be written in checks
    residual_equity: float = 0.0           # what stays in the deal at the end
    total_contributions: float = 0.0
    total_distributions: float = 0.0


# =============================================================================
# Amortization
# =============================================================================

def amortization_schedule(
    principal: float, rate: float, amort_years: float, periods_per_year: int,
    years: int,
) -> list[tuple[float, float]]:
    """
    Annual (debt_service, ending_balance) for `years` years. Computed on the
    stated period frequency then aggregated, so the annual figure matches a real
    monthly-pay note rather than an annual approximation.
    """
    if principal <= 0:
        return [(0.0, 0.0) for _ in range(years)]
    m = periods_per_year
    i = rate / m
    n_total = int(round(amort_years * m))
    pmt = principal * (i / (1 - (1 + i) ** -n_total)) if i else principal / n_total

    out: list[tuple[float, float]] = []
    bal = principal
    for _ in range(years):
        paid = 0.0
        for _ in range(m):
            if bal <= 0:
                break
            interest = bal * i
            principal_part = min(pmt - interest, bal)
            bal -= principal_part
            paid += pmt
        out.append((paid, max(0.0, bal)))
    return out


# =============================================================================
# IRR
# =============================================================================

def irr(cash_flows: list[float], lo: float = -0.95, hi: float = 5.0,
        tol: float = 1e-7, max_iter: int = 300) -> float | None:
    """
    Bisection IRR on annual flows, cash_flows[0] at t=0.

    Returns None when no sign change exists (all-positive or all-negative
    streams have no real IRR) rather than inventing a number.
    """
    if not cash_flows or all(c >= 0 for c in cash_flows) or all(c <= 0 for c in cash_flows):
        return None

    def npv(r: float) -> float:
        return sum(c / (1 + r) ** t for t, c in enumerate(cash_flows))

    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < tol:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


# =============================================================================
# The timeline
# =============================================================================

def project_cash_flow(
    cfg: dict[str, Any],
    land_price: float,
    horizon_operating_years: int = 12,
    uw: UnderwritingResult | None = None,
    site_cost_premium: float = 0.0,
) -> CashFlowResult:
    """
    Build the full development and operating timeline at a stated land price.

    `land_price` is an input here, not a solve -- this answers "if I pay X, what
    does the capital stack and the return look like", which is the question the
    yield inversion cannot answer.
    """
    d = cfg["debt"]
    exit_cap = cfg["income"]["exit_cap"]

    for_sale = project_for_sale(cfg)
    cost: CostStack = build_cost_stack(cfg, for_sale, None, site_cost_premium)
    gross_basis = cost.gross_basis(land_price)

    dev_years = max(1, int(round(cfg["cost"]["carry"]["development_years"])))
    sellout_years = max(1, int(round(for_sale.sellout_years)))

    income = project_income(cfg, years=horizon_operating_years)
    schedule = membership_schedule(cfg, horizon_operating_years)
    fee = cfg["income"]["membership"]["initiation_fee_usd"]

    # Permanent loan is secured by the RETAINED asset. In a merchant build the
    # for-sale closings retire construction debt, so lending 60% against a gross
    # basis that includes already-sold collateral double-counts it.
    sizing_basis = d.get("permanent_sizing_basis", "net")
    basis_for_debt = (gross_basis if sizing_basis == "gross"
                      else cost.net_basis(land_price, for_sale.net_proceeds))
    loan_cap = d["target_ltc"] * max(0.0, basis_for_debt)

    # Construction facility: sized on TOTAL cost, drawn during the build, repaid
    # from for-sale closings and taken out by the permanent note. A different
    # loan from a different lender against different collateral.
    construction_facility = d.get("construction_ltc", 0.0) * max(0.0, gross_basis)
    annual_tax = property_tax_annual(cfg, gross_basis)
    fs_cash_per_year = for_sale.net_proceeds / sellout_years

    # ---- Funding waterfall --------------------------------------------------
    # Debt is a PLUG capped by leverage, not an independent source stacked on
    # top of sale proceeds. Treating it as additive was funding the same dollars
    # twice and produced a nonsensical zero-equity answer.
    total_initiation = float(schedule[horizon_operating_years - 1] * fee)
    deficit_probe = _operating_deficit(cfg, income, annual_tax, horizon_operating_years)
    uses_probe = (land_price + cost.non_land_subtotal
                  + cost.carry_dollars(land_price) + deficit_probe)
    non_debt_sources = for_sale.net_proceeds + total_initiation + cost.incentives
    funding_gap = uses_probe - non_debt_sources
    # Permanent debt outstanding after the for-sale component has repaid the
    # construction facility, capped by permanent leverage on the retained asset.
    loan = min(loan_cap, max(0.0, funding_gap))

    # Interest-only through lease-up, then amortizing. Debt service during the
    # I/O period is interest at the coupon; principal begins at conversion.
    io_years = d.get("interest_only_years")
    if io_years is None:
        from .two_stack import stabilization_year as _sy
        io_years = max(0, _sy(cfg, horizon=horizon_operating_years) - 1)
    io_years = int(min(io_years, horizon_operating_years))

    amort_tail = amortization_schedule(
        loan, d["permanent_rate"], d["amortization_years"],
        d.get("periods_per_year", 12), horizon_operating_years - io_years)
    io_payment = loan * d["permanent_rate"]
    amort = [(io_payment, loan)] * io_years + amort_tail

    # ---- Pre-sale proceeds during construction ------------------------------
    ps = cfg["for_sale"].get("presale", {})
    presale_share = ps.get("unit_presale_share", 0.0)
    deposit_pct = ps.get("deposit_pct", 0.0)
    founding_share = ps.get("founding_member_share", 0.0)
    founding_dep = ps.get("founding_deposit_pct", 0.0)

    # Deposits on pre-contracted units, collected across construction.
    presale_deposits = for_sale.net_proceeds * presale_share * deposit_pct
    # Founding memberships signed pre-opening, deposit portion collected now.
    total_init = float(schedule[-1] * fee)
    founding_deposits = total_init * founding_share * founding_dep
    construction_inflow_per_year = (presale_deposits + founding_deposits) / dev_years

    # Deposits already taken are not collected again later.
    fs_cash_per_year = (for_sale.net_proceeds - presale_deposits) / sellout_years

    periods: list[PeriodCash] = []
    cumulative = 0.0

    # ---- Construction phase -------------------------------------------------
    draw_per_year = (cost.non_land_subtotal + cost.carry_dollars(land_price)) / dev_years
    # The construction facility funds the build; the permanent note replaces it
    # at stabilization rather than adding to it.
    debt_draw_per_year = construction_facility / dev_years
    for y in range(1, dev_years + 1):
        land_pay = -land_price if y == 1 else 0.0
        dep_fs = presale_deposits / dev_years
        dep_init = founding_deposits / dev_years
        cf = -draw_per_year + land_pay + debt_draw_per_year + construction_inflow_per_year
        cumulative += cf
        periods.append(PeriodCash(
            year=y, phase="construction", members=0,
            noi_pretax=0.0, property_tax=0.0, noi_after_tax=0.0,
            initiation_cash=dep_init, for_sale_net_cash=dep_fs,
            construction_draw=-draw_per_year, land_payment=land_pay,
            debt_draw=debt_draw_per_year, debt_service=0.0,
            net_cash_flow=cf, cumulative_cash=cumulative, dscr=None,
        ))

    # ---- Operating phase ----------------------------------------------------
    dscr_by_year: dict[int, float] = {}
    cumulative_deficit = 0.0
    deficit_years = 0
    construction_repay_remaining = max(0.0, construction_facility - loan)

    for oy in range(1, horizon_operating_years + 1):
        cal_year = dev_years + oy
        yr = income[oy - 1]
        joins = schedule[oy - 1] - (schedule[oy - 2] if oy >= 2 else 0)
        # Founding deposits were collected during construction; collect only the
        # remainder as members convert.
        init_cash = joins * fee - (founding_deposits / horizon_operating_years
                                   if founding_deposits else 0.0)
        fs_cash = fs_cash_per_year if oy <= sellout_years else 0.0

        nat = yr.noi - annual_tax
        if nat < 0:
            cumulative_deficit += nat
            deficit_years += 1

        ds, _bal = amort[oy - 1]
        # For-sale closings first retire the construction facility down to the
        # permanent loan balance; only the excess is available to equity.
        repay = min(fs_cash, max(0.0, construction_repay_remaining))
        construction_repay_remaining -= repay
        cf = nat + init_cash + (fs_cash - repay) - ds
        cumulative += cf

        cover = (nat / ds) if ds > 0 else None
        if cover is not None:
            dscr_by_year[cal_year] = cover

        periods.append(PeriodCash(
            year=cal_year, phase="operating", members=yr.members,
            noi_pretax=yr.noi, property_tax=annual_tax, noi_after_tax=nat,
            initiation_cash=init_cash, for_sale_net_cash=fs_cash,
            construction_draw=0.0, land_payment=0.0,
            debt_draw=0.0, debt_service=-ds,
            net_cash_flow=cf, cumulative_cash=cumulative, dscr=cover,
        ))

    # ---- Peak funding -------------------------------------------------------
    trough = min(p.cumulative_cash for p in periods)
    peak_funding = -trough if trough < 0 else 0.0
    peak_year = min(periods, key=lambda p: p.cumulative_cash).year

    # ---- Sources and uses ---------------------------------------------------
    deficit_to_fund = -cumulative_deficit if cumulative_deficit < 0 else 0.0
    uses_total = (land_price + cost.non_land_subtotal
                  + cost.carry_dollars(land_price) + deficit_to_fund)
    sources_wo_equity = (loan + for_sale.net_proceeds
                         + sum(p.initiation_cash for p in periods) + cost.incentives)
    equity_required = max(0.0, uses_total - sources_wo_equity)
    surplus = max(0.0, sources_wo_equity - uses_total)

    su = SourcesAndUses(
        land=land_price,
        non_land_cost=cost.non_land_subtotal,
        carry=cost.carry_dollars(land_price),
        operating_deficit_funded=deficit_to_fund,
        total_uses=uses_total,
        debt=loan,
        initiation_cash=sum(p.initiation_cash for p in periods),
        for_sale_net_proceeds=for_sale.net_proceeds,
        incentives=cost.incentives,
        equity_required=equity_required,
        total_sources=sources_wo_equity + equity_required,
        debt_capacity=loan_cap,
        funding_surplus=surplus,
        construction_facility=construction_facility,
    )

    # ---- Exit ---------------------------------------------------------------
    terminal = periods[-1]
    exit_noi = terminal.noi_after_tax
    exit_value = exit_noi / exit_cap if exit_cap > 0 else 0.0
    exit_costs = exit_value * cfg["income"].get("exit_cost_pct", 0.02)
    exit_net = exit_value - exit_costs
    debt_bal = amort[horizon_operating_years - 1][1]
    equity_exit = exit_net - debt_bal

    # Value is tested against the RETAINED asset's cost, not the gross basis.
    # The gross basis includes garage condos and homesites that have been sold
    # and are no longer owned; comparing the club's exit value to a denominator
    # containing sold collateral is meaningless and understated value/cost by
    # roughly 2x. The retained cost is the net basis.
    retained_cost = cost.net_basis(land_price, for_sale.net_proceeds)
    profit_on_cost = exit_net - retained_cost
    value_to_cost = (exit_net / retained_cost) if retained_cost > 0 else 0.0

    # The exit cap at which value equals the retained cost -- the widening the
    # deal survives before it is worth less than it cost to keep.
    be_cap = (exit_noi / retained_cost) if retained_cost > 0 and exit_noi > 0 else None

    # ---- Equity return ------------------------------------------------------
    # Equity is the residual claimant on the whole timeline: it funds every
    # period that runs negative and takes out every period that runs positive.
    # Building the stream that way is self-consistent -- there is no separate
    # t=0 check to guess at, and the peak contribution falls out of the same
    # series that produces the IRR.
    #
    # The earlier construction used the END-OF-LIFE residual as the t=0 outflow,
    # which understated the check by two orders of magnitude ($6.5M against a
    # $193M trough) and produced a meaningless IRR.
    equity_flows: list[float] = [p.net_cash_flow for p in periods]
    equity_flows[-1] += equity_exit

    contributions = -sum(c for c in equity_flows if c < 0)
    distributions = sum(c for c in equity_flows if c > 0)
    multiple = (distributions / contributions) if contributions > 0 else 0.0
    peak_equity = peak_funding      # deepest cumulative hole after debt draws

    return CashFlowResult(
        periods=periods,
        sources_uses=su,
        peak_funding_requirement=peak_funding,
        peak_funding_year=peak_year,
        cumulative_operating_deficit=cumulative_deficit,
        deficit_years=deficit_years,
        min_dscr=min(dscr_by_year.values()) if dscr_by_year else None,
        min_dscr_year=(min(dscr_by_year, key=dscr_by_year.get) if dscr_by_year else None),
        dscr_by_year=dscr_by_year,
        exit_value=exit_value,
        exit_net_proceeds=exit_net,
        debt_balance_at_exit=debt_bal,
        equity_at_exit=equity_exit,
        profit_on_cost=profit_on_cost,
        value_to_cost=value_to_cost,
        retained_cost=retained_cost,
        equity_multiple=multiple,
        equity_irr=irr(equity_flows),
        breakeven_exit_cap=be_cap,
        peak_equity_requirement=peak_equity,
        residual_equity=equity_required,
        total_contributions=contributions,
        total_distributions=distributions,
    )


def covenant_report(cf: CashFlowResult, min_dscr: float,
                    tested_from_year: int | None = None) -> dict[str, Any]:
    """
    Which years breach the covenant.

    `tested_from_year` reflects the common structure where the covenant is not
    tested until conversion, with a funded debt-service reserve covering
    lease-up. Coverage BEFORE that year is still reported -- it drives the
    reserve -- it just is not a default.
    """
    tested = {y: v for y, v in cf.dscr_by_year.items()
              if tested_from_year is None or y >= tested_from_year}
    breaches = {y: v for y, v in tested.items() if v < min_dscr}
    return {
        "min_dscr": cf.min_dscr,
        "min_dscr_year": cf.min_dscr_year,
        "covenant": min_dscr,
        "breach_years": sorted(breaches),
        "breach_count": len(breaches),
        "worst_breach": min(breaches.values()) if breaches else None,
        "passes_every_year": not breaches,
        "tested_from_year": tested_from_year,
        "min_dscr_tested": min(tested.values()) if tested else None,
    }
