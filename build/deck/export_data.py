"""Export live model figures for the investor deck. Run before make_deck.js."""
from __future__ import annotations
import datetime, copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from build.build_workbook import enrich, load_parcels_csv
from model import gates, scoring
from model import cashflow as cfm, demand as dmd, markets as mk, respec as rsp, risk as rk, roadmap as rmap, scenarios as sc, two_stack as ts

PARCELS = Path("data/sites_targets.csv")
OUT = Path(__file__).resolve().parent / "data.json"


def main() -> None:
    cfg = ts.load_config()
    universe, _ = enrich(load_parcels_csv(PARCELS), cfg)
    live = sorted([p for p in universe if not p.get("killed_at_gate")],
                  key=lambda p: p.get("composite_score") or 0, reverse=True)
    lead = live[0]
    ask = float(lead["ask_price"]); prem = float(lead["site_cost_premium_usd"] or 0)

    # Everything the deck says describes the LEAD SITE, so it runs on that site's
    # season and ad valorem regime rather than the national defaults.
    lcfg = ts.site_config(cfg, lead)

    uw = ts.underwrite(lcfg, "LEAD", ask_price=ask, site_cost_premium=prem)
    cf = cfm.project_cash_flow(lcfg, ask, horizon_operating_years=12, site_cost_premium=prem)
    stab = ts.stabilization_year(lcfg)
    dev = int(round(cfg["cost"]["carry"]["development_years"]))
    cov = cfm.covenant_report(cf, cfg["debt"]["min_dscr"], tested_from_year=dev + stab)
    plaus = rk.plausibility_report(lcfg, ask)
    bev = rk.direct_break_evens(lcfg, ask)
    br = rk.return_bridge(lcfg, ask, target_irr=0.15, site_cost_premium=prem)
    t1b = ts.tranche_1_budget(cfg)
    tor, _b, _n = rk.tornado(lcfg)
    mc = rk.monte_carlo(lcfg, ask, site_cost_premium=prem)
    scen = sc.run_all(lcfg, ask_price=ask, site_cost_premium=prem)
    T = rmap.timing(lcfg)
    lt = rmap.listing_readiness(lcfg, ask, prem)
    m = cfg["income"]["membership"]; fs = cfg["for_sale"]; d = cfg["debt"]

    lev = []
    for ltc in (0.0, 0.15, 0.30, 0.45, 0.60, 0.70):
        c = copy.deepcopy(lcfg); c["debt"]["target_ltc"] = ltc
        x = cfm.project_cash_flow(c, ask, horizon_operating_years=12, site_cost_premium=prem)
        xc = cfm.covenant_report(x, c["debt"]["min_dscr"], tested_from_year=dev + stab)
        lev.append({"ltc": ltc, "irr": x.equity_irr, "dscr": xc["min_dscr_tested"]})

    sites = []
    for p in live:
        pr = float(p.get("site_cost_premium_usd") or 0); a = float(p.get("ask_price") or 0)
        pcfg = ts.site_config(cfg, p)
        scf = cfm.project_cash_flow(pcfg, a, horizon_operating_years=12, site_cost_premium=pr)
        scv = cfm.covenant_report(scf, d["min_dscr"], tested_from_year=dev + stab)
        puw = ts.underwrite(pcfg, p["parcel_id"], ask_price=a, site_cost_premium=pr)
        sites.append(dict(id=p["parcel_id"].replace("TP-", ""), muni=p.get("municipality"),
            county=f"{p.get('county')}, {p.get('state')}",
            metro=p.get("market_metro"), region=p.get("market_region"),
            tier=p.get("market_tier"), season=p.get("season_days"),
            tax_rate=p.get("property_tax_effective_rate"),
            abate=p.get("property_tax_abatement_pct"),
            yoc=puw.yoc_net_at_ask, max_land=puw.max_land_net,
            acres=p.get("contiguous_developable_acres"),
            prior=str(p.get("prior_use", "")).replace("_", " "), ask=a, premium=pr,
            drive=p.get("best_drive_min"), irr=scf.equity_irr,
            dscr=scv["min_dscr_tested"], score=p.get("composite_score"),
            why=p.get("why_wins"), kill=p.get("what_kills"),
            note=p.get("site_cost_basis_note"), zoning=p.get("zoning_posture"),
            months=p.get("permitting_timeline_months"),
            abate_path=p.get("tax_abatement_path")))

    killed = [dict(id=p["parcel_id"].replace("TP-", ""), metro=p.get("market_metro"),
                   gate=str(p.get("killed_at_gate", "")).replace("_", " ").title(),
                   why=str(p.get("rejection_reasons") or "")[:170])
              for p in universe if p.get("killed_at_gate")]

    nat = mk.national_summary()

    dem = []
    for r in dmd.portfolio(cfg, live):
        be = dmd.demand_break_even(cfg, next(p for p in live if p["parcel_id"] == r.parcel_id))
        dem.append(dict(id=r.parcel_id.replace("TP-", ""), hnw=r.hnw_households,
                        capturable=r.capturable, coverage=r.coverage,
                        joins=r.joins_per_year, incumbent=r.incumbent_capture,
                        be_collector=be["collector_share"],
                        verdict=r.verdict.split("—")[0].strip(),
                        full=r.verdict))

    yrs = ts.project_income(lcfg, years=12)
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
        deficit=cf.sources_uses.operating_deficit_funded, tau=ts.tax_load(lcfg),
        req=uw.required_yield, ltc=d["target_ltc"],
        mc=ts.mortgage_constant(d["permanent_rate"], d["amortization_years"], 12),
        perm_rate=d["permanent_rate"], amort=d["amortization_years"],
        retained_yield=uw.stabilized_noi_after_tax / max(1.0, cf.retained_cost)),
      hnw=int(lead.get("hnw_households_90min") or 0),
      lead=dict(id=lead["parcel_id"].replace("TP-", ""), metro=lead.get("market_metro"),
        county=f"{lead.get('county')}, {lead.get('state')}", season=lead.get("season_days"),
        muni=lead.get("municipality")),
      national=dict(screened=nat["markets_screened"], proven=nat["proven_markets"],
        ne_rank=nat["northeast_rank"], ne_score=nat["northeast_score"],
        top=nat["top"].market.metro, top_score=nat["top"].total,
        season_lo=nat["season_spread"][0], season_hi=nat["season_spread"][1],
        anc_elast=cfg["income"]["season"]["ancillary_elasticity"],
        opex_elast=cfg["income"]["season"]["opex_elasticity"],
        tier1=[dict(metro=r.market.metro, states=r.market.states,
                    season=r.market.season_days, score=r.total,
                    clubs=r.market.existing_clubs, white=r.market.whitespace,
                    typ=r.market.candidate_typologies) for r in nat["tier1"]],
        tier2=[dict(metro=r.market.metro, states=r.market.states,
                    season=r.market.season_days, score=r.total,
                    clubs=r.market.existing_clubs) for r in nat["tier2"][:6]]),
      rollout=[dict(phase=r.phase, horizon=r.horizon, markets=r.markets,
        rationale=r.rationale, capital=r.capital) for r in mk.rollout(lead_site=lead)],
      killed=killed,
      noise=[dict(id=p["parcel_id"].replace("TP-", ""),
                  dba=p.get("noise_ordinance_dba_day"),
                  cit=p.get("noise_ordinance_citation") or "",
                  exempt=bool(p.get("noise_exemption")),
                  std=p.get("noise_standard_type") or "")
             for p in live],
      fragility=(lambda f: None if f is None else dict(
          lead=f.lead_id.replace("TP-", ""), up=f.runner_up_id.replace("TP-", ""),
          gap=f.gap, flips=f.flips, flip_at=f.flip_value, verdict=f.verdict))(
          scoring.lead_site_fragility(universe, cfg, ts.underwrite, gates.screen,
                                      ts.site_config)),
      demand=dem,
      respec=(lambda R: dict(
          n=len(R.variants), verdict=R.verdict,
          track_bps=R.track_sensitivity_bps, condo_bps=R.condo_sensitivity_bps,
          base=dict(cap=R.baseline.member_cap, mi=R.baseline.track_miles,
                    condos=R.baseline.condo_units, irr=R.baseline.equity_irr,
                    dscr=R.baseline.min_dscr, vc=R.baseline.value_to_cost,
                    permi=R.baseline.members_per_mile, cov=R.baseline.demand_coverage),
          best=None if R.best_feasible is None else dict(
                    cap=R.best_feasible.member_cap, mi=R.best_feasible.track_miles,
                    condos=R.best_feasible.condo_units, irr=R.best_feasible.equity_irr,
                    dscr=R.best_feasible.min_dscr, vc=R.best_feasible.value_to_cost,
                    permi=R.best_feasible.members_per_mile,
                    cov=R.best_feasible.demand_coverage)))(
          rsp.search(lcfg, ask, prem, parcel=lead)),
      condo=dict(loaded_psf=uw.for_sale.loaded_cost_psf,
                 raw_psf=cfg["for_sale"]["garage_condos"]["hard_cost_psf"],
                 sale_psf=cfg["for_sale"]["garage_condos"]["sale_price_psf"],
                 unit_margin=uw.for_sale.condo_margin_per_unit,
                 raw_margin=uw.for_sale.gross_margin_pct,
                 loaded_margin=uw.for_sale.loaded_margin_pct),
      comp=next((dict(irr=x.equity_irr, dscr=x.min_dscr_tested, vc=x.value_to_cost,
                      land=x.max_land_net, verdict=x.verdict, label=x.label)
                 for x in scen if x.name == "comp_repriced"), None),
      bridge=dict(base=br.base_irr, target=br.target_irr, verdict=br.verdict,
        n=br.combined_drivers, label=br.combined_label, irr=br.combined_irr,
        vc=br.combined_value_to_cost,
        rungs=[dict(driver=r.driver, move=r.move, irr=r.irr, vc=r.value_to_cost,
                    reaches=r.reaches_target) for r in br.rungs]),
      demand_cfg=dict(collector=cfg["demand"]["collector_share"],
        track_active=cfg["demand"]["track_active_share"],
        thin=cfg["demand"]["coverage_thin"],
        comfortable=cfg["demand"]["coverage_comfortable"],
        decay_mi=cfg["demand"]["incumbent_decay_radius_mi"],
        ramp1=m["ramp"][0]),
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
      tranche1=t1b["total"],
      t1=dict(subtotal=t1b["subtotal"], contingency=t1b["contingency"],
        pct=t1b["contingency_pct"], months=t1b["months"],
        items=[dict(month=i["month"], name=i["name"], usd=i["usd"],
                    vendor=i["vendor"], resolves=i["resolves"]) for i in t1b["items"]]),
      timing=dict(entitlement=T.entitlement_months, construction=T.construction_months,
        opening=T.opening_month, stabilised=T.stabilisation_month,
        opening_year=T.opening_year, stabilised_year=T.stabilisation_year),
      milestones=[dict(horizon=x.horizon, month=x.month, phase=x.phase,
        objective=x.objective, deliverables=x.deliverables, gate=x.gate, kpi=x.kpi,
        capital=x.capital) for x in rmap.milestones(lcfg)],
      platform=[dict(clubs=x.clubs, noi=x.stabilised_noi, value=x.asset_value,
        cost=x.cumulative_dev_cost) for x in rmap.platform_scale(lcfg, ask, prem, 7)],
      listing=dict(need=lt.clubs_required, by_noi=lt.clubs_required_by_noi,
        by_value=lt.clubs_required_by_value, by_div=lt.clubs_required_by_diversification,
        ground_up_year=lt.ground_up_year, acq_year=lt.acquisition_year,
        listable_10=lt.listable_by_year_10, verdict=lt.verdict,
        min_noi=lt.thresholds["min_recurring_noi_usd"],
        min_value=lt.thresholds["min_equity_value_usd"],
        min_assets=lt.thresholds["min_stabilised_assets"]),
      exits=[dict(rank=e.rank, route=e.route, timing=e.timing, basis=e.proceeds_basis,
        requires=e.requires, assessment=e.assessment) for e in rmap.exit_paths(lcfg, ask, prem)],
    )
    OUT.write_text(json.dumps(data, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
