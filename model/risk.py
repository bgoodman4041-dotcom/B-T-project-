"""
TRACK BOSS — Break-Evens, Tornado, Monte Carlo, Plausibility
============================================================

Four things a point estimate cannot tell you:

* **Break-even** — not "what is the answer" but "how wrong can I be before the
  answer changes sign". The distance to the break-even is the actual margin of
  safety, and it is the only sensitivity number a credit committee remembers.
* **Tornado** — which single driver moves the answer most. Ranking drivers by
  swing tells you where to spend diligence dollars. Researching a variable that
  moves the answer by $2M while ignoring one that moves it by $60M is the most
  common way analytical effort gets wasted.
* **Monte Carlo** — the probability the program clears, given honest ranges on
  every driver at once. A deal that clears the base case and fails 80% of draws
  is not a deal that clears.
* **Plausibility** — whether the pro forma is internally coherent at all. This
  is the check that catches the failure mode where every block looks defensible
  in isolation and the combination is impossible.

Distributions are triangular. That is deliberate: triangular is the honest shape
when you have a floor, a ceiling, and a best guess, but nothing that justifies
assuming a variance.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from typing import Any, Callable

from . import cashflow as cf_mod
from . import scenarios as sc
from . import two_stack as ts

# Drivers expressed as basis-point deltas rather than multipliers.
RATE_DRIVERS = {"exit_cap_bps", "perm_rate_bps"}
# Drivers where "more" is worse for the deal.
INVERSE_DRIVERS = {"hard_cost_factor", "opex_factor", "absorption_slowdown",
                   "exit_cap_bps", "perm_rate_bps"}


# =============================================================================
# Metrics
# =============================================================================

def metric_max_land_net(cfg: dict[str, Any]) -> float:
    return ts.underwrite(cfg, "M").max_land_net


def metric_max_land_gross(cfg: dict[str, Any]) -> float:
    return ts.underwrite(cfg, "M").max_land_gross


def metric_stabilized_noi_after_tax(cfg: dict[str, Any]) -> float:
    return ts.underwrite(cfg, "M").stabilized_noi_after_tax


def make_metric_min_dscr(land_price: float, horizon: int = 12) -> Callable:
    def _m(cfg: dict[str, Any]) -> float:
        cf = cf_mod.project_cash_flow(cfg, land_price, horizon_operating_years=horizon)
        return cf.min_dscr if cf.min_dscr is not None else float("inf")
    return _m


def make_metric_equity_irr(land_price: float, horizon: int = 12) -> Callable:
    def _m(cfg: dict[str, Any]) -> float:
        cf = cf_mod.project_cash_flow(cfg, land_price, horizon_operating_years=horizon)
        return cf.equity_irr if cf.equity_irr is not None else -1.0
    return _m


def make_metric_value_to_cost(land_price: float, horizon: int = 12) -> Callable:
    def _m(cfg: dict[str, Any]) -> float:
        return cf_mod.project_cash_flow(
            cfg, land_price, horizon_operating_years=horizon).value_to_cost
    return _m


# =============================================================================
# Break-even solver
# =============================================================================

@dataclass
class BreakEven:
    driver: str
    metric: str
    target: float
    break_even_value: float | None      # driver value where metric == target
    base_value: float                   # the driver's base setting (1.0 or 0 bps)
    headroom_pct: float | None          # how far the driver can move, signed
    reachable: bool
    note: str = ""


def solve_break_even(
    cfg: dict[str, Any],
    driver: str,
    metric: Callable[[dict[str, Any]], float],
    target: float,
    metric_name: str = "metric",
    lo: float | None = None,
    hi: float | None = None,
    tol: float = 1e-4,
    max_iter: int = 60,
) -> BreakEven:
    """
    Bisect on a single scenario driver until `metric` crosses `target`.

    Returns reachable=False rather than a fabricated number when the target
    cannot be reached anywhere in the search range -- which is itself the
    finding: no achievable value of that driver fixes the deal.
    """
    is_rate = driver in RATE_DRIVERS
    base = 0.0 if is_rate else 1.0
    if lo is None:
        lo = -300.0 if is_rate else 0.20
    if hi is None:
        hi = 300.0 if is_rate else 4.00

    def at(v: float) -> float:
        return metric(sc.apply_scenario(cfg, {driver: v}))

    f_lo, f_hi = at(lo) - target, at(hi) - target
    if f_lo * f_hi > 0:
        return BreakEven(
            driver=driver, metric=metric_name, target=target, break_even_value=None,
            base_value=base, headroom_pct=None, reachable=False,
            note=(f"{metric_name} does not cross {target:,.4g} for {driver} in "
                  f"[{lo:g}, {hi:g}] — no achievable value of this driver alone "
                  f"changes the outcome"),
        )

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        f_mid = at(mid) - target
        if abs(f_mid) < tol:
            break
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    be = (lo + hi) / 2

    if is_rate:
        headroom = be - base
    else:
        headroom = (be - base) / base if base else None

    return BreakEven(
        driver=driver, metric=metric_name, target=target, break_even_value=be,
        base_value=base, headroom_pct=headroom, reachable=True,
    )


def break_even_suite(
    cfg: dict[str, Any], land_price: float, horizon: int = 12
) -> list[BreakEven]:
    """The break-evens an IC will ask for, in the order they ask."""
    min_dscr = cfg["debt"]["min_dscr"]
    out: list[BreakEven] = []

    # What has to happen for the program to clear at all (net basis, land = 0).
    for driver in ("dues_factor", "cap_factor", "ancillary_factor",
                   "hard_cost_factor", "opex_factor"):
        out.append(solve_break_even(
            cfg, driver, metric_max_land_net, 0.0, "max_land_net = 0"))

    # What has to happen for the covenant to hold in every year.
    m = make_metric_min_dscr(land_price, horizon)
    for driver in ("dues_factor", "cap_factor", "ancillary_factor", "perm_rate_bps"):
        out.append(solve_break_even(
            cfg, driver, m, min_dscr, f"min DSCR = {min_dscr:.2f}x"))

    # What has to happen for the asset to be worth what it cost.
    v = make_metric_value_to_cost(land_price, horizon)
    for driver in ("dues_factor", "exit_cap_bps", "hard_cost_factor"):
        out.append(solve_break_even(cfg, driver, v, 1.0, "value / cost = 1.00x"))

    return out


def direct_break_evens(cfg: dict[str, Any], land_price: float) -> dict[str, Any]:
    """
    Closed-form break-evens that do not need a solver, stated in the units the
    principal thinks in: members, dollars of dues, and a cap rate.
    """
    uw = ts.underwrite(cfg, "BE")
    m = cfg["income"]["membership"]
    inc = cfg["income"]
    tau = ts.tax_load(cfg)
    gross = uw.cost.gross_basis(land_price)
    net = uw.cost.net_basis(land_price, uw.for_sale.net_proceeds)

    mc = ts.mortgage_constant(
        cfg["debt"]["permanent_rate"], cfg["debt"]["amortization_years"],
        cfg["debt"].get("periods_per_year", 12))
    debt_service = cfg["debt"]["target_ltc"] * max(0.0, net) * mc
    noi_needed_for_covenant = cfg["debt"]["min_dscr"] * debt_service
    tax = tau * max(0.0, gross)

    # Per-member marginal contribution at stabilization: dues plus the ancillary
    # that scales with penetration, plus amortized initiation.
    cap = m["cap"]
    per_member = (
        m["annual_dues_usd"]
        + sum(inc["ancillary_annual_usd"].values()) / cap
        + m["initiation_fee_usd"] / m["expected_tenure_years"]
    )
    load = 1 - inc["management_fee_pct_egi"] - inc["replacement_reserve_pct_egi"]
    fixed = sum(inc["opex_annual_usd"].values()) + tax

    be_members_cov = ((noi_needed_for_covenant + fixed) / (per_member * load)
                      if per_member * load > 0 else None)
    be_members_zero = fixed / (per_member * load) if per_member * load > 0 else None
    be_dues_cov = (
        ((noi_needed_for_covenant + fixed) / load - (per_member - m["annual_dues_usd"]) * cap) / cap
        if cap and load > 0 else None
    )

    return {
        "members_to_cover_opex_and_tax": be_members_zero,
        "members_to_meet_covenant": be_members_cov,
        "members_at_stabilization": ts.membership_schedule(cfg, 20)[uw.stabilization_year - 1],
        "membership_cap": cap,
        "dues_to_meet_covenant": be_dues_cov,
        "dues_base": m["annual_dues_usd"],
        "annual_debt_service": debt_service,
        "annual_property_tax": tax,
        "fixed_cost_incl_tax": fixed,
        "per_member_contribution": per_member,
        "covenant_noi_required": noi_needed_for_covenant,
    }


# =============================================================================
# Tornado
# =============================================================================

@dataclass
class TornadoBar:
    driver: str
    low_value: float
    high_value: float
    base: float
    swing: float
    low_input: float
    high_input: float

    @property
    def swing_abs(self) -> float:
        return abs(self.swing)


def tornado(
    cfg: dict[str, Any],
    metric: Callable[[dict[str, Any]], float] | None = None,
    metric_name: str = "max_land_net",
    drivers: list[str] | None = None,
) -> tuple[list[TornadoBar], float, str]:
    """
    One-at-a-time driver ranking. Returns (bars sorted by swing, base, name).

    This is deliberately univariate -- its job is attribution, not downside.
    Scenarios handle correlated stress; the tornado tells you where the
    sensitivity lives so diligence money goes to the right variable.
    """
    metric = metric or metric_max_land_net
    t = cfg["tornado"]
    swing = t["swing_pct"]
    bps = t["rate_swing_bps"]
    drivers = drivers or [
        "dues_factor", "cap_factor", "ancillary_factor", "condo_psf_factor",
        "homesite_price_factor", "hard_cost_factor", "opex_factor",
        "absorption_slowdown", "exit_cap_bps", "perm_rate_bps",
    ]

    base = metric(cfg)
    bars: list[TornadoBar] = []
    for d in drivers:
        if d in RATE_DRIVERS:
            lo_in, hi_in = -bps, bps
        else:
            lo_in, hi_in = 1 - swing, 1 + swing
        lo_v = metric(sc.apply_scenario(cfg, {d: lo_in}))
        hi_v = metric(sc.apply_scenario(cfg, {d: hi_in}))
        bars.append(TornadoBar(
            driver=d, low_value=lo_v, high_value=hi_v, base=base,
            swing=hi_v - lo_v, low_input=lo_in, high_input=hi_in,
        ))
    bars.sort(key=lambda b: b.swing_abs, reverse=True)
    return bars, base, metric_name


# =============================================================================
# Monte Carlo
# =============================================================================

@dataclass
class MonteCarloResult:
    iterations: int
    metric_name: str
    samples: list[float] = field(default_factory=list)
    p_feasible_gross: float = 0.0
    p_feasible_net: float = 0.0
    p_covenant_holds: float = 0.0
    percentiles: dict[str, float] = field(default_factory=dict)
    mean: float = 0.0
    stdev: float = 0.0
    failures: int = 0


def _triangular(rng: random.Random, spec: list[float]) -> float:
    lo, mode, hi = spec
    return rng.triangular(lo, hi, mode)


def monte_carlo(
    cfg: dict[str, Any],
    land_price: float,
    iterations: int | None = None,
    horizon: int = 12,
    seed: int | None = None,
    site_cost_premium: float = 0.0,
) -> MonteCarloResult:
    """
    Joint draw across every driver, reporting the DISTRIBUTION of the answer and
    the probability the program clears each test.

    Drivers are drawn independently, which understates tail risk because real
    drivers are positively correlated in stress. The scenario bundles exist to
    cover that; read the two together, not either alone.
    """
    mc = cfg["monte_carlo"]
    n = iterations or mc["iterations"]
    rng = random.Random(seed if seed is not None else mc["seed"])
    specs = mc["drivers"]

    lands: list[float] = []
    feas_g = feas_n = cov_ok = 0
    failures = 0

    for _ in range(n):
        draw = {k: _triangular(rng, v) for k, v in specs.items()}
        try:
            c = sc.apply_scenario(cfg, draw)
            uw = ts.underwrite(c, "MC")
            lands.append(uw.max_land_net)
            if uw.max_land_gross > 0:
                feas_g += 1
            if uw.max_land_net > 0:
                feas_n += 1
            cf = cf_mod.project_cash_flow(c, land_price, horizon_operating_years=horizon,
                                          site_cost_premium=site_cost_premium)
            # Test the covenant FROM CONVERSION, exactly as cashflow, scenarios
            # and the workbook do. `cf.min_dscr` is the whole-hold minimum and
            # includes lease-up years, when the note is interest-only, a funded
            # reserve is carrying it and NOI has not arrived. Measured that way
            # every draw fails and the reported probability is a structural
            # zero, not a result -- it read "0% of 4,000 draws hold the
            # covenant" on a deck whose base case covers at 2.02x.
            rep = cf_mod.covenant_report(
                cf, c["debt"]["min_dscr"],
                tested_from_year=int(round(c["cost"]["carry"]["development_years"]))
                + ts.stabilization_year(c))
            if rep["passes_every_year"]:
                cov_ok += 1
        except (ValueError, ZeroDivisionError):
            failures += 1

    lands.sort()
    if not lands:
        return MonteCarloResult(iterations=n, metric_name="max_land_net", failures=failures)

    def pct(p: float) -> float:
        idx = min(len(lands) - 1, max(0, int(round(p * (len(lands) - 1)))))
        return lands[idx]

    ok = len(lands)
    return MonteCarloResult(
        iterations=n,
        metric_name="max_land_net",
        samples=lands,
        p_feasible_gross=feas_g / ok,
        p_feasible_net=feas_n / ok,
        p_covenant_holds=cov_ok / ok,
        percentiles={"p5": pct(0.05), "p10": pct(0.10), "p25": pct(0.25),
                     "p50": pct(0.50), "p75": pct(0.75), "p90": pct(0.90),
                     "p95": pct(0.95)},
        mean=statistics.fmean(lands),
        stdev=statistics.pstdev(lands) if len(lands) > 1 else 0.0,
        failures=failures,
    )


# =============================================================================
# Plausibility
# =============================================================================

@dataclass
class Check:
    name: str
    value: float
    band: tuple[float, float]
    severity: str            # "OK" | "WARN" | "FAIL"
    message: str

    @property
    def passed(self) -> bool:
        return self.severity == "OK"


def _band_check(name: str, value: float | None, band: list[float], fmt: str,
                why: str, hard_factor: float = 1.5) -> Check:
    lo, hi = band
    if value is None:
        return Check(name, float("nan"), (lo, hi), "WARN", f"{name}: not computable")
    if lo <= value <= hi:
        sev, msg = "OK", f"{name} = {value:{fmt}} inside [{lo:{fmt}}, {hi:{fmt}}]"
    else:
        # Outside the band is a WARN; far outside is a FAIL.
        far = value > hi * hard_factor or (lo > 0 and value < lo / hard_factor)
        sev = "FAIL" if far else "WARN"
        direction = "above" if value > hi else "below"
        msg = (f"{name} = {value:{fmt}} is {direction} the plausible band "
               f"[{lo:{fmt}}, {hi:{fmt}}] — {why}")
    return Check(name, value, (lo, hi), sev, msg)


def plausibility_report(
    cfg: dict[str, Any], land_price: float | None = None, horizon: int = 12
) -> dict[str, Any]:
    """
    Internal-consistency audit. Changes no number; catches pro formas that
    cannot be true.

    The motivating case: a for-sale stack carrying a 53% gross margin while the
    income stack cannot cover its own operating expense. Each block read as
    defensible alone. Together they were impossible, and nothing was checking.
    """
    p = cfg["plausibility"]
    uw = ts.underwrite(cfg, "PLAUS")
    fs = uw.for_sale
    land = land_price if land_price is not None else max(0.0, uw.max_land_net)

    years = ts.project_income(cfg, years=max(horizon, uw.stabilization_year))
    stab = years[uw.stabilization_year - 1]
    tax = ts.property_tax_annual(cfg, uw.cost.gross_basis(land))

    condo = cfg["for_sale"]["garage_condos"]
    miles = cfg["cost"]["track"]["miles"]

    checks = [
        _band_check("For-sale gross margin", fs.gross_margin_pct,
                    p["for_sale_gross_margin"], ".1%",
                    "merchant-build development does not clear this; the for-sale "
                    "stack is subsidising the income stack"),
        _band_check("Condo price / hard cost", condo["sale_price_psf"] / condo["hard_cost_psf"],
                    p["condo_price_to_cost_ratio"], ".2f",
                    "implies a spread over cost that local flex-industrial comps "
                    "must actually support"),
        _band_check("Opex ratio of EGI", stab.opex / stab.egi if stab.egi else None,
                    p["opex_ratio_of_egi"], ".1%",
                    "private club operating ratios cluster tightly; an outlier "
                    "means opex or revenue is mis-scaled"),
        _band_check("Property tax % of EGI", tax / stab.egi if stab.egi else None,
                    p["property_tax_pct_of_egi"], ".1%",
                    "effective rates run from ~0.65% of value in NV to ~2.6% in CT, "
                    "and abatement reaches this use in some states and not others -- "
                    "the band spans the national range, so a miss means the tau inputs "
                    "are wrong, not that the jurisdiction is unusual"),
        # The two checks the audit was missing. Everything else here tests a
        # RATIO the configuration produces; these test the PRICING PAIR that
        # produces them, which is where the comparable study found the problem.
        _band_check("Dues / initiation ratio",
                    (cfg["income"]["membership"]["annual_dues_usd"]
                     / cfg["income"]["membership"]["initiation_fee_usd"]
                     if cfg["income"]["membership"]["initiation_fee_usd"] else None),
                    p["dues_to_initiation_ratio"], ".1%",
                    "clubs price the upfront-versus-recurring trade inside a tight "
                    "band; a pair outside it is not aggressive or conservative, it "
                    "is a pair no operator has demonstrated it can collect"),
        _band_check("Dues revenue per track mile",
                    (cfg["income"]["membership"]["cap"]
                     * cfg["income"]["membership"]["annual_dues_usd"] / miles
                     if miles else None),
                    p["dues_revenue_per_track_mile_usd"], ",.0f",
                    "the invariant that travels across clubs, because density is "
                    "inversely priced -- low member-per-mile IS the product at the "
                    "top of the market"),
        _band_check("Members per track mile",
                    cfg["income"]["membership"]["cap"] / miles if miles else None,
                    p["members_per_track_mile"], ".0f",
                    "too high degrades track time and renewals; too low wastes pavement"),
        _band_check("Reserve per track mile",
                    stab.replacement_reserve / miles if miles else None,
                    p["reserve_per_track_mile_usd"], ",.0f",
                    "a circuit needs repaving on a 10-15 year cycle; a thin reserve "
                    "defers a seven-figure capital event into the hold"),
    ]

    cf = cf_mod.project_cash_flow(cfg, land, horizon_operating_years=horizon)
    checks.append(_band_check("Value / cost", cf.value_to_cost, p["value_to_cost"], ".2f",
                              "below 1.0x the program destroys value at the assumed "
                              "exit cap regardless of the yield on cost"))

    fails = [c for c in checks if c.severity == "FAIL"]
    warns = [c for c in checks if c.severity == "WARN"]
    return {
        "checks": checks,
        "fail_count": len(fails),
        "warn_count": len(warns),
        "ok_count": sum(1 for c in checks if c.passed),
        "coherent": not fails,
        "verdict": (
            "Pro forma is internally coherent."
            if not fails and not warns
            else (f"{len(fails)} implausible and {len(warns)} questionable input "
                  f"relationship(s) — the assumptions do not hang together and "
                  f"must be re-based before any land price is quoted.")
        ),
    }


# =============================================================================
# Return bridge — what would have to be true to earn an opportunistic return
# =============================================================================

@dataclass
class Rung:
    driver: str
    move: str
    irr: float | None
    value_to_cost: float | None
    peak_equity: float
    reaches_target: bool


@dataclass
class ReturnBridge:
    base_irr: float | None
    target_irr: float
    rungs: list[Rung]
    combined_label: str
    combined_irr: float | None
    combined_value_to_cost: float | None
    combined_drivers: int
    any_single_driver_reaches: bool
    verdict: str


# One favourable move per driver, each sized at roughly the top of what the
# scenario set already treats as an upside outcome. Nothing here is a stretch
# on its own; the point of the exercise is what it takes when you need several.
_BRIDGE_MOVES: list[tuple[str, str, dict[str, Any]]] = [
    ("Initiation fee", "+50%", {"initiation_factor": 1.50}),
    ("Annual dues", "+25%", {"dues_factor": 1.25}),
    ("Condo price", "+30% / SF", {"condo_psf_factor": 1.30}),
    ("Absorption", "1.5x faster", {"absorption_slowdown": 1 / 1.5}),
    ("Hard cost", "-10%", {"hard_cost_factor": 0.90}),
    ("Exit cap", "-100 bp", {"exit_cap_bps": -100}),
    ("Ancillary", "+20%", {"ancillary_factor": 1.20}),
    ("Permanent leverage", "to zero", {"ltc_delta": -1.0}),
]


def return_bridge(
    cfg: dict[str, Any],
    land_price: float,
    target_irr: float = 0.15,
    horizon: int = 12,
    site_cost_premium: float = 0.0,
) -> ReturnBridge:
    """
    The base case earns a CORE return for OPPORTUNISTIC risk, and pretending
    otherwise is the fastest way to lose a reader who prices deals for a living.

    Ground-up development with entitlement risk is conventionally underwritten
    to 18%+; a stabilised core asset to 6-9%. This programme lands at the top of
    core. That is a real objection and it deserves an arithmetic answer rather
    than an adjective, so this walks every favourable driver one at a time,
    reports which of them reaches the target ALONE, and then prices the
    combination.

    The finding it exists to surface: no single driver gets there. Reaching an
    opportunistic return needs several independent favourable outcomes at once,
    which is not a base case -- it is the upside scenario, and the scenario set
    already prices it.
    """
    base_cf = cf_mod.project_cash_flow(cfg, land_price, horizon_operating_years=horizon,
                                       site_cost_premium=site_cost_premium)
    rungs: list[Rung] = []
    for driver, move, override in _BRIDGE_MOVES:
        c = sc.apply_scenario(cfg, override)
        cf = cf_mod.project_cash_flow(c, land_price, horizon_operating_years=horizon,
                                      site_cost_premium=site_cost_premium)
        rungs.append(Rung(
            driver=driver, move=move, irr=cf.equity_irr,
            value_to_cost=cf.value_to_cost, peak_equity=cf.peak_equity_requirement,
            reaches_target=cf.equity_irr is not None and cf.equity_irr >= target_irr,
        ))
    rungs.sort(key=lambda r: -(r.irr if r.irr is not None else -1e9))

    # The MINIMAL combination that reaches the target, added strongest-first.
    #
    # Stacking every favourable move at once is not an answer to "what would
    # have to be true" -- seven maxima compounded returned a 24.8% IRR at 5.8x
    # value-to-cost, which is not a scenario anyone should quote. The useful
    # statement is the shortest list of things that have to go right.
    #
    # De-levering is excluded: it is a capital-structure choice rather than a
    # business outcome, and it is already the base case's own finding.
    by_strength = [r for r in rungs
                   if not any("ltc_delta" in o for d, mv, o in _BRIDGE_MOVES
                              if d == r.driver and "ltc_delta" in o)]
    override_by_driver = {d: o for d, mv, o in _BRIDGE_MOVES}
    move_by_driver = {d: mv for d, mv, o in _BRIDGE_MOVES}

    combo: dict[str, Any] = {}
    labels: list[str] = []
    ccf = base_cf
    for r in by_strength:
        combo.update(override_by_driver[r.driver])
        labels.append(f"{r.driver} {move_by_driver[r.driver]}")
        c = sc.apply_scenario(cfg, combo)
        ccf = cf_mod.project_cash_flow(c, land_price, horizon_operating_years=horizon,
                                       site_cost_premium=site_cost_premium)
        if ccf.equity_irr is not None and ccf.equity_irr >= target_irr:
            break

    any_single = any(r.reaches_target for r in rungs)
    best = rungs[0]
    if any_single:
        verdict = (f"{best.driver} {best.move} reaches {target_irr:.0%} on its own "
                   f"({best.irr:.1%}). Test that driver hardest.")
    elif ccf.equity_irr is not None and ccf.equity_irr >= target_irr:
        verdict = (
            f"No single driver reaches {target_irr:.0%}. The best is {best.driver} "
            f"{best.move} at {best.irr:.1%} against a {base_cf.equity_irr:.1%} base. "
            f"It takes {len(labels)} of them together — {' + '.join(labels)} — to reach "
            f"{ccf.equity_irr:.1%}. That is not a base case; it is {len(labels)} "
            f"independent things going right at once, and the scenario set already "
            f"prices that as the upside."
        )
    else:
        verdict = (
            f"Neither any single driver nor all {len(labels)} together reach "
            f"{target_irr:.0%} (combined {ccf.equity_irr:.1%} if defined). At the "
            f"assumed programme this is structurally a core-plus return and should "
            f"be marketed as one."
        )

    return ReturnBridge(
        base_irr=base_cf.equity_irr, target_irr=target_irr, rungs=rungs,
        combined_label=" + ".join(labels), combined_irr=ccf.equity_irr,
        combined_value_to_cost=ccf.value_to_cost, combined_drivers=len(labels),
        any_single_driver_reaches=any_single, verdict=verdict,
    )
