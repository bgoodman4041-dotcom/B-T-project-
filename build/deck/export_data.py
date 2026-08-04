"""Export live model figures for the investor deck. Run before make_deck.js."""
from __future__ import annotations
import datetime, copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from build.build_workbook import enrich, load_parcels_csv
from model import cashflow as cfm, risk as rk, roadmap as rmap, scenarios as sc, two_stack as ts

PARCELS = Path("data/sites_targets.csv")
OUT = Path(__file__).resolve().parent / "data.json"


def main() -> None:
    cfg = ts.load_config()
    universe, _ = enrich(load_parcels_csv(PARCELS), cfg)
    live = sorted([p for p in universe if not p.get("killed_at_gate")],
                  key=lambda p: p.get("composite_score") or 0, reverse=True)
    lead = live[0]
    ask = float(lead["ask_price"]); prem = float(lead["site_cost_premium_usd"] or 0)

    uw = ts.underwrite(cfg, "LEAD", ask_price=ask, site_cost_premium=prem)
    cf = cfm.project_cash_flow(cfg, ask, horizon_operating_years=12, site_cost_premium=prem)
    stab = ts.stabilization_year(cfg)
    dev = int(round(cfg["cost"]["carry"]["development_years"]))
    cov = cfm.covenant_report(cf, cfg["debt"]["min_dscr"], tested_from_year=dev + stab)
    plaus = rk.plausibility_report(cfg, ask)
    bev = rk.direct_break_evens(cfg, ask)
    tor, _b, _n = rk.tornado(cfg)
    mc = rk.monte_carlo(cfg, ask)
    scen = sc.run_all(cfg, ask_price=ask, site_cost_premium=prem)
    T = rmap.timing(cfg)
    lt = rmap.listing_readiness(cfg, ask, prem)
    m = cfg["income"]["membership"]; fs = cfg["for_sale"]; d = cfg["debt"]

    lev = []
    for ltc in (0.0, 0.15, 0.30, 0.45, 0.60, 0.70):
        c = copy.deepcopy(cfg); c["debt"]["target_ltc"] = ltc
        x = cfm.project_cash_flow(c, ask, horizon_operating_years=12, site_cost_premium=prem)
        xc = cfm.covenant_report(x, c["debt"]["min_dscr"], tested_from_year=dev + stab)
        lev.append({"ltc": ltc, "irr": x.equity_irr, "dscr": xc["min_dscr_tested"]})

    sites = []
    for p in live:
        pr = float(p.get("site_cost_premium_usd") or 0); a = float(p.get("ask_price") or 0)
        scf = cfm.project_cash_flow(cfg, a, horizon_operating_years=12, site_cost_premium=pr)
        scv = cfm.covenant_report(scf, d["min_dscr"], tested_from_year=dev + stab)
        sites.append(dict(id=p["parcel_id"].replace("TP-", ""), muni=p.get("municipality"),
            county=f"{p.get('county')}, {p.get('state')}",
            acres=p.get("contiguous_developable_acres"),
            prior=str(p.get("prior_use", "")).replace("_", " "), ask=a, premium=pr,
            drive=p.get("best_drive_min"), irr=scf.equity_irr,
            dscr=scv["min_dscr_tested"], score=p.get("composite_score"),
            why=p.get("why_wins"), kill=p.get("what_kills"),
            note=p.get("site_cost_basis_note"), zoning=p.get("zoning_posture"),
            months=p.get("permitting_timeline_months"), abate=p.get("tax_abatement_path")))

    yrs = ts.project_income(cfg, years=12)
    data = dict(
      today=datetime.date.today().isoformat(),
      program=dict(miles=cfg["cost"]["track"]["miles"], cap=m["cap"],
        init=m["initiation_fee_usd"], dues=m["annual_dues_usd"],
        condos=fs["garage_condos"]["units"], condo_sf=fs["garage_condos"]["avg_sf"],
        condo_psf=fs["garage_condos"]["sale_price_psf"],
        condo_cost_psf=fs["garage_condos"]["hard_cost_psf"],
        homes=fs["homesites"]["units"], home_price=fs["homesites"]["price_per_unit_usd"],
        per_mile=m["cap"] / cfg["cost"]["track"]["miles"], stab=stab, dev=dev, ramp=m["ramp"]),
      econ=dict(gross_basis=uw.cost.gross_basis(ask), noi=uw.stabilized_noi_after_tax,
        peak_equity=cf.peak_equity_requirement, peak_year=cf.peak_funding_year,
        irr=cf.equity_irr, em=cf.equity_multiple, vc=cf.value_to_cost,
        profit=cf.profit_on_cost, be_cap=cf.breakeven_exit_cap,
        exit_cap=cfg["income"]["exit_cap"], min_dscr=cov["min_dscr_tested"],
        covenant=d["min_dscr"], breaches=cov["breach_count"], retained=cf.retained_cost,
        exit_val=cf.exit_net_proceeds, fs_proceeds=uw.for_sale.net_proceeds,
        init_cash=cf.sources_uses.initiation_cash, perm_debt=cf.sources_uses.debt,
        constr=cf.sources_uses.construction_facility,
        equity_resid=cf.sources_uses.equity_required,
        total_uses=cf.sources_uses.total_uses, land=cf.sources_uses.land,
        nonland=cf.sources_uses.non_land_cost, carry=cf.sources_uses.carry,
        deficit=cf.sources_uses.operating_deficit_funded, tau=ts.tax_load(cfg),
        req=uw.required_yield, ltc=d["target_ltc"],
        mc=ts.mortgage_constant(d["permanent_rate"], d["amortization_years"], 12),
        perm_rate=d["permanent_rate"], amort=d["amortization_years"],
        retained_yield=uw.stabilized_noi_after_tax / max(1.0, cf.retained_cost)),
      hnw=int(lead.get("hnw_households_90min") or 0),
      scen=[dict(name=s.name, label=s.label, irr=s.equity_irr, em=s.equity_multiple,
        vc=s.value_to_cost, land=s.max_land_net, dscr=s.min_dscr_tested,
        verdict=s.verdict, peak=s.peak_equity) for s in scen],
      lev=lev, sites=sites,
      bev=dict(need_cov=bev["members_to_meet_covenant"],
        need_opex=bev["members_to_cover_opex_and_tax"], cap=bev["membership_cap"],
        at_stab=bev["members_at_stabilization"], dues_cov=bev["dues_to_meet_covenant"],
        dues_base=bev["dues_base"]),
      tornado=[dict(driver=b.driver.replace("_", " "), swing=b.swing_abs) for b in tor[:6]],
      mc=dict(n=mc.iterations, p_net=mc.p_feasible_net, p_cov=mc.p_covenant_holds,
        p50=mc.percentiles.get("p50")),
      plaus=dict(fails=plaus["fail_count"], warns=plaus["warn_count"], ok=plaus["ok_count"]),
      ramp_years=[dict(y=y.year, members=y.members, noi=y.noi) for y in yrs],
      tranche1=4250000,
      timing=dict(entitlement=T.entitlement_months, construction=T.construction_months,
        opening=T.opening_month, stabilised=T.stabilisation_month,
        opening_year=T.opening_year, stabilised_year=T.stabilisation_year),
      milestones=[dict(horizon=x.horizon, month=x.month, phase=x.phase,
        objective=x.objective, deliverables=x.deliverables, gate=x.gate, kpi=x.kpi,
        capital=x.capital) for x in rmap.milestones(cfg)],
      platform=[dict(clubs=x.clubs, noi=x.stabilised_noi, value=x.asset_value,
        cost=x.cumulative_dev_cost) for x in rmap.platform_scale(cfg, ask, prem, 7)],
      listing=dict(need=lt.clubs_required, by_noi=lt.clubs_required_by_noi,
        by_value=lt.clubs_required_by_value, by_div=lt.clubs_required_by_diversification,
        ground_up_year=lt.ground_up_year, acq_year=lt.acquisition_year,
        listable_10=lt.listable_by_year_10, verdict=lt.verdict,
        min_noi=lt.thresholds["min_recurring_noi_usd"],
        min_value=lt.thresholds["min_equity_value_usd"],
        min_assets=lt.thresholds["min_stabilised_assets"]),
      exits=[dict(rank=e.rank, route=e.route, timing=e.timing, basis=e.proceeds_basis,
        requires=e.requires, assessment=e.assessment) for e in rmap.exit_paths(cfg, ask, prem)],
    )
    OUT.write_text(json.dumps(data, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
