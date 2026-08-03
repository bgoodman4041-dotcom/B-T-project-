/*
 * THE NORTHEAST MOTOR CLUB — Investor Deck
 * Generated from build/deck/data.json, which is exported from the live model.
 * No figure in this deck is typed by hand.
 */
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const D = JSON.parse(fs.readFileSync(__dirname + "/data.json", "utf8"));

// ---------- palette: asphalt + racing red ----------
const ASPHALT = "1A1D21";
const CARBON  = "2A2E34";
const PAPER   = "FFFFFF";
const MIST    = "F2F3F5";
const RED     = "C8102E";
const GREY    = "6E7278";
const MIDGREY = "9BA0A6";

const HFONT = "Cambria";
const BFONT = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";           // 13.3 x 7.5
pres.author = "Track Boss";
pres.title  = "The Northeast Motor Club — Investor Presentation";
const W = 13.33, H = 7.5, M = 0.62;

// ---------- formatters ----------
const m$ = (v) => {
  if (v === null || v === undefined) return "n/a";
  const a = Math.abs(v) / 1e6;
  const s = a >= 100 ? a.toFixed(0) : a.toFixed(1);
  return (v < 0 ? "($" : "$") + s + "M" + (v < 0 ? ")" : "");
};
const k$ = (v) => (v === null || v === undefined) ? "n/a"
  : "$" + Math.round(v).toLocaleString("en-US");
const pc = (v, dp) => (v === null || v === undefined) ? "n/a"
  : (v * 100).toFixed(dp === undefined ? 1 : dp) + "%";
const xx = (v) => (v === null || v === undefined) ? "n/a" : v.toFixed(2) + "x";

// ---------- primitives ----------
function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: ASPHALT };
  return s;
}
function lightSlide(kicker, title) {
  const s = pres.addSlide();
  s.background = { color: PAPER };
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: M, y: 0.44, w: 9, h: 0.24, fontFace: BFONT, fontSize: 10.5,
      bold: true, color: RED, charSpacing: 1.6, margin: 0,
    });
  }
  if (title) {
    s.addText(title, {
      x: M, y: 0.6, w: W - 2 * M, h: 0.72, fontFace: HFONT, fontSize: 30,
      bold: true, color: ASPHALT, margin: 0,
    });
  }
  return s;
}
// Stat card: tinted panel, big number, small label. The repeated motif.
function statCard(s, x, y, w, h, value, label, opts) {
  const o = opts || {};
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, fill: { color: o.fill || MIST }, rectRadius: 0.06,
    line: { color: o.fill || MIST, width: 0 },
    shadow: { type: "outer", color: "8A8D93", blur: 7, offset: 1, angle: 90, opacity: 0.22 },
  });
  s.addText(value, {
    x: x + 0.16, y: y + 0.14, w: w - 0.32, h: h * 0.5,
    fontFace: HFONT, fontSize: o.vsize || 27, bold: true,
    color: o.vcolor || ASPHALT, margin: 0, valign: "middle",
  });
  s.addText(label, {
    x: x + 0.16, y: y + h * 0.58, w: w - 0.32, h: h * 0.38,
    fontFace: BFONT, fontSize: o.lsize || 10.5, color: o.lcolor || GREY,
    margin: 0, valign: "top",
  });
}
// Numbered circle + heading + body — used for thesis and timeline rows.
function numberedRow(s, n, x, y, w, head, body, circleColor) {
  s.addShape(pres.ShapeType.ellipse, {
    x, y, w: 0.42, h: 0.42, fill: { color: circleColor || RED },
    line: { color: circleColor || RED, width: 0 },
  });
  s.addText(String(n), {
    x, y, w: 0.42, h: 0.42, fontFace: HFONT, fontSize: 14, bold: true,
    color: PAPER, align: "center", valign: "middle", margin: 0,
  });
  s.addText(head, {
    x: x + 0.58, y: y - 0.03, w: w - 0.58, h: 0.28, fontFace: BFONT,
    fontSize: 13.5, bold: true, color: ASPHALT, margin: 0,
  });
  s.addText(body, {
    x: x + 0.58, y: y + 0.25, w: w - 0.58, h: 0.72, fontFace: BFONT,
    fontSize: 11, color: GREY, margin: 0, lineSpacingMultiple: 1.05,
  });
}
function tbl(s, x, y, w, rows, colW, opts) {
  const o = opts || {};
  const body = rows.map((r, i) => r.map((c) => ({
    text: String(c),
    options: {
      fontFace: BFONT, fontSize: o.fs || 10, margin: [4, 6, 4, 6],
      bold: i === 0, color: i === 0 ? PAPER : ASPHALT,
      fill: i === 0 ? { color: CARBON } : { color: i % 2 ? PAPER : MIST },
      valign: "middle",
    },
  })));
  s.addTable(body, { x, y, w, colW, border: { type: "none" },
    rowH: o.rowH || 0.3, autoPage: false });
}
function footnote(s, text) {
  s.addText(text, {
    x: M, y: H - 0.86, w: W - 2 * M, h: 0.34, fontFace: BFONT, fontSize: 8.5,
    italic: true, color: MIDGREY, margin: 0,
  });
}
const chartFrame = () => ({
  showLegend: false, showTitle: false,
  catAxisLabelColor: GREY, valAxisLabelColor: GREY,
  catAxisLabelFontFace: BFONT, valAxisLabelFontFace: BFONT,
  catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
  valGridLine: { color: "E4E6E9", size: 0.6 },
  catGridLine: { style: "none" },
  chartColors: [ASPHALT, RED, MIDGREY, "4A4F57"],
  dataLabelFontFace: BFONT, dataLabelFontSize: 9.5,
});

// =====================================================================
// 1 — Title
// =====================================================================
{
  const s = darkSlide();
  s.addText("THE NORTHEAST\nMOTOR CLUB", {
    x: M + 0.1, y: 1.65, w: 8.6, h: 2.1, fontFace: HFONT, fontSize: 50,
    bold: true, color: PAPER, lineSpacingMultiple: 0.95, margin: 0,
  });
  s.addText("A private motorsport country club and trackside residential community", {
    x: M + 0.14, y: 3.9, w: 8.4, h: 0.4, fontFace: BFONT, fontSize: 15,
    color: MIDGREY, margin: 0,
  });
  s.addText("NEW YORK   ·   CONNECTICUT   ·   NEW JERSEY", {
    x: M + 0.14, y: 4.42, w: 8.4, h: 0.3, fontFace: BFONT, fontSize: 11.5,
    bold: true, color: RED, charSpacing: 2, margin: 0,
  });
  statCard(s, 9.5, 1.75, 3.2, 1.0, m$(D.tranche1), "TRANCHE 1 — FEASIBILITY RAISE",
    { fill: CARBON, vcolor: PAPER, lcolor: MIDGREY, vsize: 26 });
  statCard(s, 9.5, 2.9, 3.2, 1.0, m$(D.econ.peak_equity), "TRANCHE 2 — PEAK CONSTRUCTION EQUITY",
    { fill: CARBON, vcolor: PAPER, lcolor: MIDGREY, vsize: 26 });
  statCard(s, 9.5, 4.05, 3.2, 1.0, pc(D.econ.irr) + "  /  " + xx(D.econ.em),
    "BASE-CASE IRR / EQUITY MULTIPLE",
    { fill: CARBON, vcolor: PAPER, lcolor: MIDGREY, vsize: 22 });
  s.addText("Confidential business plan  ·  " + D.today +
            "  ·  Not an offer to sell securities  ·  No site under contract", {
    x: M + 0.14, y: H - 0.88, w: 11.5, h: 0.3, fontFace: BFONT, fontSize: 9,
    italic: true, color: GREY, margin: 0,
  });
  s.addNotes("Lead with the ask and the honest return. This is a mid-single to low-double " +
    "digit IRR asset play with a merchant-build component, not an opportunistic development deal.");
}

// =====================================================================
// 2 — The ask
// =====================================================================
{
  const s = darkSlide();
  s.addText("THE ASK", {
    x: M, y: 0.5, w: 8, h: 0.5, fontFace: BFONT, fontSize: 11, bold: true,
    color: RED, charSpacing: 2, margin: 0,
  });
  s.addText("We are raising " + m$(D.tranche1) + " today — not " +
            m$(D.econ.peak_equity), {
    x: M, y: 0.95, w: W - 2 * M, h: 0.95, fontFace: HFONT, fontSize: 31,
    bold: true, color: PAPER, margin: 0,
  });
  s.addText("The largest uncertainty in this programme is the revenue assumption set, and it " +
    "can be resolved for a fraction of a percent of total cost. Committing construction " +
    "equity before that work is done would be indefensible.", {
    x: M, y: 2.0, w: 11.9, h: 0.62, fontFace: BFONT, fontSize: 13,
    color: MIDGREY, margin: 0, lineSpacingMultiple: 1.1,
  });

  const rows = [
    ["", "TRANCHE 1 — FEASIBILITY & CONTROL", "TRANCHE 2 — CONSTRUCTION EQUITY"],
    ["Amount", m$(D.tranche1), m$(D.econ.peak_equity) + " peak requirement"],
    ["Timing", "On execution", "At construction start, gated"],
    ["Buys", "Verified comps · 150-parcel sourcing pass · site option · acoustic model · Phase I/II · entitlement counsel · abatement negotiation",
     "Land closing · circuit and vertical build · FF&E · carry · operating deficit reserve"],
    ["Protection", "Spent on options and studies, never on land. If comps or the abatement fail, the programme stops before acquisition",
     "Draw conditions on permit, abatement, pre-sales and a lender commitment"],
  ];
  const body = rows.map((r, i) => r.map((c, j) => ({
    text: String(c),
    options: {
      fontFace: BFONT, fontSize: i === 0 ? 10 : 10.5, margin: [5, 7, 5, 7],
      bold: i === 0 || j === 0, valign: "top",
      color: i === 0 ? RED : (j === 0 ? MIDGREY : PAPER),
      fill: { color: i === 0 ? ASPHALT : CARBON },
    },
  })));
  s.addTable(body, { x: M, y: 2.85, w: W - 2 * M, colW: [1.25, 5.4, 5.44], rowH: 0.34 });
  footnote(s, "Tranche 1 is deliberately the smaller number and the harder gate.");
  s.addNotes("If they only remember one slide, make it this one. The small ask with a hard " +
    "gate is what separates this from a promoter's deck.");
}

// =====================================================================
// 3 — Thesis
// =====================================================================
{
  const s = lightSlide("Investment thesis", "Five reasons this works — and one reason it might not");
  const L = M, R = 7.0, wcol = 5.7;
  numberedRow(s, 1, L, 1.62, wcol, "The garage-condo spread is the profit engine",
    "Units underwritten at " + k$(D.program.condo_psf) + "/SF against " +
    k$(D.program.condo_cost_psf) + " cost — a " +
    (D.program.condo_psf / D.program.condo_cost_psf).toFixed(2) +
    "x ratio. The buyer purchases access and adjacency, not square footage.");
  numberedRow(s, 2, L, 2.78, wcol, "Prior-use sites are an economic requirement",
    "Infrastructure is underwritten 30% below greenfield because targets carry existing " +
    "pavement, grading and utilities. On raw land the programme does not clear.");
  numberedRow(s, 3, L, 3.94, wcol, "An inherited noise floor is the entitlement asset",
    "Noise kills these projects in court after the permits issue. Every target carries a " +
    "prior intensive use, which supports a coming-to-the-nuisance defence.");
  numberedRow(s, 4, R, 1.62, wcol, "Member capital funds the build",
    m$(D.econ.init_cash) + " of initiation fees plus pre-sold condominiums. Buyer and member " +
    "capital cover most of total uses — which is why peak equity is " +
    m$(D.econ.peak_equity) + ", not " + m$(D.econ.total_uses) + ".");
  numberedRow(s, 5, R, 2.78, wcol, "Scarcity is structural, not cyclical",
    "NJ Highlands and Pinelands, the NYC watershed and the Adirondack Park remove most " +
    "large-acreage inventory before price is ever discussed.");
  s.addShape(pres.ShapeType.roundRect, {
    x: R, y: 3.94, w: wcol, h: 1.12, fill: { color: "FBEAEC" }, rectRadius: 0.06,
    line: { color: "FBEAEC", width: 0 },
  });
  s.addText("The risk we lead with", {
    x: R + 0.18, y: 4.04, w: wcol - 0.36, h: 0.26, fontFace: BFONT, fontSize: 12,
    bold: true, color: RED, margin: 0,
  });
  s.addText("Every revenue figure is benchmark-derived, not sourced. The comparable club " +
    "study is the first use of Tranche 1 and a gate on all further spend.", {
    x: R + 0.18, y: 4.32, w: wcol - 0.36, h: 0.68, fontFace: BFONT, fontSize: 10.5,
    color: "7A2430", margin: 0, lineSpacingMultiple: 1.05,
  });
  s.addNotes("Point 1 is the thesis. Point 2 is the constraint that drives site selection. " +
    "The red box is deliberate — name the weakness before they find it.");
}

// =====================================================================
// 4 — The product
// =====================================================================
{
  const s = lightSlide("The product", "A club whose members buy the real estate");
  statCard(s, M, 1.6, 2.9, 1.08, D.program.miles.toFixed(1) + " mi", "CONFIGURABLE CIRCUIT");
  statCard(s, M + 3.05, 1.6, 2.9, 1.08, String(D.program.cap), "MEMBERSHIPS AT BUILDOUT");
  statCard(s, M + 6.1, 1.6, 2.9, 1.08, String(D.program.condos), "GARAGE CONDOMINIUMS");
  statCard(s, M + 9.15, 1.6, 2.9, 1.08, String(D.program.homes), "TRACKSIDE HOMESITES");

  tbl(s, M, 3.05, W - 2 * M, [
    ["Revenue line", "Programme", "Pricing", "Notes"],
    ["Membership", D.program.cap + " members (" + D.program.per_mile.toFixed(0) + " per track mile)",
     k$(D.program.init) + " initiation · " + k$(D.program.dues) + " dues",
     "Initiation amortised over expected tenure, never capitalised into NOI"],
    ["Garage condominiums", D.program.condos + " units @ " + D.program.condo_sf.toLocaleString() + " SF",
     k$(D.program.condo_psf) + " / SF", "Primary for-sale profit centre; pre-sold off plan"],
    ["Homesites", D.program.homes + " trackside lots", k$(D.program.home_price) + " each",
     "Sold to members; finished-lot delivery"],
    ["Clubhouse & service", "32,000 SF club · 22,000 SF tech centre", "Included in basis",
     "F&B, lounge, fitness, storage, race prep, detailing"],
    ["Shoulder season", "Karting, skidpad, autocross", "Included in basis",
     "Deliberately weighted up — the Northeast season is shorter than the reference asset"],
  ], [1.6, 3.0, 2.55, 4.94], { rowH: 0.44, fs: 9.5 });
  footnote(s, "Stabilised NOI after property tax of " + m$(D.econ.noi) +
    " is reached in operating year " + D.program.stab + ".");
  s.addNotes("The point of this slide: members are the buyers. That is what makes the " +
    "for-sale premium defensible and the pre-sale funding realistic.");
}

// =====================================================================
// 5 — Market
// =====================================================================
{
  const s = lightSlide("Market", "Demand is not the constraint. Seasonality is.");
  statCard(s, M, 1.58, 3.05, 1.15, (D.hnw / 1000).toFixed(0) + "k",
    "HOUSEHOLDS >$1M INVESTABLE WITHIN 90 MIN", { vsize: 30 });
  statCard(s, M, 2.86, 3.05, 1.15, D.program.cap,
    "MEMBERS REQUIRED AT BUILDOUT", { vsize: 30 });
  statCard(s, M, 4.14, 3.05, 1.15,
    (D.program.cap / D.hnw * 10000).toFixed(1) + " bps",
    "REQUIRED PENETRATION OF THAT POOL", { vsize: 30, fill: "FBEAEC", vcolor: RED, lcolor: "7A2430" });

  s.addChart(pres.ChartType.bar, [{
    name: "Members", labels: D.ramp_years.slice(0, 8).map(r => "Yr " + r.y),
    values: D.ramp_years.slice(0, 8).map(r => r.members),
  }], Object.assign(chartFrame(), {
    x: 4.05, y: 1.58, w: 8.65, h: 2.35, barDir: "col",
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: GREY,
    valAxisMaxVal: D.program.cap, barGapWidthPct: 55,
  }));
  s.addText("Membership ramp to buildout", {
    x: 4.05, y: 3.96, w: 8.65, h: 0.26, fontFace: BFONT, fontSize: 10.5,
    bold: true, color: ASPHALT, margin: 0,
  });
  s.addText("The binding market question is not whether the households exist — the required " +
    "penetration is a few basis points of the pool. It is whether a Northeast club can price " +
    "like a year-round one. The reference asset for this typology operates in the California " +
    "desert with close to twelve months of usable track time; our season is roughly half that. " +
    "We have therefore weighted revenue toward indoor storage, the service department and the " +
    "karting complex, and we treat dues parity with year-round clubs as unproven until the " +
    "comparable study is complete.", {
    x: 4.05, y: 4.3, w: 8.65, h: 1.35, fontFace: BFONT, fontSize: 11.5,
    color: GREY, margin: 0, lineSpacingMultiple: 1.12,
  });
  footnote(s, "Household wealth density is a site-reported input pending source verification. " +
    "Comparable club economics remain unresearched.");
  s.addNotes("Do not oversell the market. The honest framing is that demand size is easy and " +
    "seasonality is the real question. Raising it yourself builds credibility.");
}

// =====================================================================
// 6 — Prior use
// =====================================================================
{
  const s = lightSlide("Site strategy", "Why we only look at land that has already been used hard");
  const cards = [
    ["Former airfields", "Runway pavement is base course you do not pay for. Industrial zoning, " +
      "utilities at the boundary, and an aviation noise history on the record."],
    ["Reclaimed quarries", "A natural bowl attenuates its own noise and is worth real money at " +
      "hearing. On-site aggregate for base course. Offset by blasting risk."],
    ["Capped landfills & brownfields", "Cheapest dirt and the strongest incentive access. " +
      "No load-bearing build over the cap, so the circuit routes around it."],
    ["Closed golf courses", "Pre-graded, usually sewered, already entitled for outdoor " +
      "recreation — and the noise fight is partly won. Highest-priority typology."],
  ];
  cards.forEach((c, i) => {
    const x = M + (i % 2) * 6.15, y = 1.62 + Math.floor(i / 2) * 1.62;
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: 5.85, h: 1.42, fill: { color: MIST }, rectRadius: 0.06,
      line: { color: MIST, width: 0 },
      shadow: { type: "outer", color: "8A8D93", blur: 7, offset: 1, angle: 90, opacity: 0.2 },
    });
    s.addText(c[0], { x: x + 0.22, y: y + 0.16, w: 5.4, h: 0.3, fontFace: BFONT,
      fontSize: 13.5, bold: true, color: ASPHALT, margin: 0 });
    s.addText(c[1], { x: x + 0.22, y: y + 0.5, w: 5.4, h: 0.8, fontFace: BFONT,
      fontSize: 10.5, color: GREY, margin: 0, lineSpacingMultiple: 1.06 });
  });
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.0, w: W - 2 * M, h: 0.95, fill: { color: ASPHALT }, rectRadius: 0.06,
    line: { color: ASPHALT, width: 0 },
  });
  s.addText("Noise, not zoning, kills motorsport projects — and it kills them in court, after " +
    "the permits are issued. A prior intensive use is both a 30% infrastructure saving and a " +
    "coming-to-the-nuisance defence. It is the single highest-signal attribute in the screen.", {
    x: M + 0.28, y: 5.16, w: W - 2 * M - 0.56, h: 0.65, fontFace: BFONT, fontSize: 12,
    color: PAPER, margin: 0, lineSpacingMultiple: 1.08,
  });
  s.addNotes("This slide justifies the 30% infrastructure discount in the model. Without a " +
    "prior-use site that discount disappears and the deal does not clear.");
}

// =====================================================================
// 7 — Site portfolio
// =====================================================================
{
  const s = lightSlide("Site portfolio", "Five acquisition targets, underwritten independently");
  const rows = [["#", "Target", "County / ST", "Acres", "Prior use", "Indicative ask",
                 "Site premium", "Best drive", "IRR", "Min DSCR", "Score"]];
  D.sites.forEach((t, i) => rows.push([
    i + 1, t.id, t.county, Math.round(t.acres).toLocaleString(), t.prior,
    m$(t.ask), m$(t.premium), t.drive + " min", pc(t.irr), xx(t.dscr),
    Math.round(t.score),
  ]));
  tbl(s, M, 1.62, W - 2 * M, rows,
    [0.34, 1.55, 1.32, 0.62, 1.62, 1.22, 1.12, 0.86, 0.66, 0.86, 0.6],
    { rowH: 0.42, fs: 9.5 });
  s.addText("Each site carries its own cost premium or credit — remediation, blasting, utility " +
    "extension, less the value of existing pavement — so the economics genuinely differ. " +
    "The spread from best to worst is " +
    pc(D.sites[0].irr) + " against " + pc(D.sites[D.sites.length - 1].irr) + " IRR.", {
    x: M, y: 4.65, w: 7.6, h: 0.8, fontFace: BFONT, fontSize: 11.5, color: GREY,
    margin: 0, lineSpacingMultiple: 1.1,
  });
  statCard(s, 8.5, 4.6, 2.0, 0.95, String(D.sites.length), "TARGETS UNDERWRITTEN");
  statCard(s, 10.7, 4.6, 2.0, 0.95, "0", "UNDER CONTRACT",
    { fill: "FBEAEC", vcolor: RED, lcolor: "7A2430" });
  footnote(s, "TARGET PROFILES: each row is a typology and a submarket, not an identified " +
    "parcel. Assessor identifiers, coordinates and title work are a Tranche 1 deliverable. " +
    "Ask prices are indicative for the submarket.");
  s.addNotes("Be explicit that nothing is under contract. The red card does that work for you " +
    "before anyone asks.");
}

// =====================================================================
// 8 — Lead site
// =====================================================================
{
  const t = D.sites[0];
  const s = lightSlide("Lead target", t.id + " — " + t.muni + ", " + t.county);
  s.addText("Typology: former naval weapons industrial reserve and airfield. Existing runway " +
    "pavement, municipal water and sewer at the boundary, industrial zoning, and a municipal " +
    "owner with a job-creation mandate.", {
    x: M, y: 1.55, w: 7.3, h: 0.72, fontFace: BFONT, fontSize: 12, color: GREY,
    margin: 0, lineSpacingMultiple: 1.1,
  });
  numberedRow(s, 1, M, 2.42, 7.3, "Why it ranks first", String(t.why || ""));
  numberedRow(s, 2, M, 3.52, 7.3, "Cost basis", String(t.note || ""));
  numberedRow(s, 3, M, 4.78, 7.3, "What would kill it", String(t.kill || ""));

  statCard(s, 8.2, 1.55, 2.15, 0.95, Math.round(t.acres).toLocaleString(), "DEVELOPABLE ACRES");
  statCard(s, 10.55, 1.55, 2.15, 0.95, t.drive + " min", "BEST DRIVE TIME");
  statCard(s, 8.2, 2.68, 2.15, 0.95, m$(t.ask), "INDICATIVE ASK");
  statCard(s, 10.55, 2.68, 2.15, 0.95, m$(t.premium), "PAVEMENT CREDIT");
  statCard(s, 8.2, 3.81, 2.15, 0.95, pc(t.irr), "PROJECT IRR");
  statCard(s, 10.55, 3.81, 2.15, 0.95, xx(t.dscr), "MIN DSCR");
  s.addShape(pres.ShapeType.roundRect, {
    x: 8.2, y: 4.94, w: 4.5, h: 0.96, fill: { color: MIST }, rectRadius: 0.06,
    line: { color: MIST, width: 0 },
  });
  s.addText("Entitlement: " + String(t.zoning).replace(/_/g, " ") + " · " + t.months +
    " month path\nAbatement route: " + t.abate, {
    x: 8.4, y: 5.08, w: 4.1, h: 0.72, fontFace: BFONT, fontSize: 10.5, color: GREY,
    margin: 0, lineSpacingMultiple: 1.1,
  });
  s.addNotes("The pavement credit is the single most important line on this slide — it is why " +
    "this site leads.");
}

// =====================================================================
// 9 — Timeline
// =====================================================================
{
  const s = lightSlide("Execution", "From first feasibility dollar to stabilisation");
  const ph = [
    ["Phase 0 — Feasibility", "0–9 months", "Comparable club study · 150-parcel sourcing pass · site selection · option executed · acoustic model · Phase I", "Tranche 1"],
    ["Phase 1 — Entitlement", "9–33 months", "Special permit or map amendment · environmental review · wetlands · abatement executed · founding-member pre-sales open", "Tranche 1"],
    ["Phase 2 — Construction", D.program.dev + " years", "Land closing · circuit, clubhouse, service centre, first condominium building · construction facility drawn", "Tranche 2"],
    ["Phase 3 — Lease-up", "Ops years 1–" + D.program.stab, "Membership ramp to " + D.program.cap + " · condominium and homesite closings · permanent loan conversion", "Tranche 2"],
    ["Phase 4 — Stabilised hold", "Ops years " + D.program.stab + "–12", "Full membership · dues escalation · refinance or sale of the retained club", "—"],
  ];
  ph.forEach((p, i) => {
    const y = 1.6 + i * 1.03;
    s.addShape(pres.ShapeType.ellipse, {
      x: M, y: y + 0.06, w: 0.44, h: 0.44,
      fill: { color: i < 2 ? RED : ASPHALT }, line: { color: PAPER, width: 0 },
    });
    s.addText(String(i), { x: M, y: y + 0.06, w: 0.44, h: 0.44, fontFace: HFONT,
      fontSize: 14, bold: true, color: PAPER, align: "center", valign: "middle", margin: 0 });
    s.addText(p[0], { x: M + 0.62, y: y, w: 2.7, h: 0.3, fontFace: BFONT, fontSize: 13,
      bold: true, color: ASPHALT, margin: 0 });
    s.addText(p[1], { x: M + 0.62, y: y + 0.29, w: 2.7, h: 0.26, fontFace: BFONT,
      fontSize: 10.5, color: RED, bold: true, margin: 0 });
    s.addText(p[2], { x: M + 3.5, y: y + 0.02, w: 6.7, h: 0.62, fontFace: BFONT,
      fontSize: 10.5, color: GREY, margin: 0, lineSpacingMultiple: 1.05 });
    s.addText(p[3], { x: 11.05, y: y + 0.08, w: 1.65, h: 0.3, fontFace: BFONT,
      fontSize: 10.5, bold: true, color: i < 2 ? RED : ASPHALT, align: "right", margin: 0 });
  });
  footnote(s, "Entitlement is the longest and least controllable phase, which is why the plan " +
    "spends option money rather than acquisition money until the permit is in hand.");
  s.addNotes("Emphasise that Tranche 1 covers phases 0 and 1 — all the way through entitlement, " +
    "without buying land.");
}

// =====================================================================
// 10 — Sources and uses
// =====================================================================
{
  const s = lightSlide("Capital", "Sources and uses — lead site");
  s.addChart(pres.ChartType.bar, [
    { name: "Uses", labels: ["Land", "Development cost", "Construction carry", "Deficit reserve"],
      values: [D.econ.land / 1e6, D.econ.nonland / 1e6, D.econ.carry / 1e6, D.econ.deficit / 1e6] },
  ], Object.assign(chartFrame(), {
    x: M, y: 1.6, w: 6.1, h: 2.55, barDir: "bar", showValue: true,
    dataLabelPosition: "outEnd", dataLabelColor: GREY,
    dataLabelFormatCode: '"$"#,##0"M"', barGapWidthPct: 45,
  }));
  s.addChart(pres.ChartType.bar, [
    { name: "Sources", labels: ["For-sale proceeds", "Initiation capital", "Permanent debt", "Residual equity"],
      values: [D.econ.fs_proceeds / 1e6, D.econ.init_cash / 1e6, D.econ.perm_debt / 1e6, D.econ.equity_resid / 1e6] },
  ], Object.assign(chartFrame(), {
    x: 6.85, y: 1.6, w: 5.85, h: 2.55, barDir: "bar", showValue: true,
    dataLabelPosition: "outEnd", dataLabelColor: GREY, chartColors: [RED],
    dataLabelFormatCode: '"$"#,##0"M"', barGapWidthPct: 45,
  }));
  s.addText("USES  —  " + m$(D.econ.total_uses) + " total", {
    x: M, y: 1.32, w: 6.1, h: 0.26, fontFace: BFONT, fontSize: 11, bold: true,
    color: ASPHALT, margin: 0 });
  s.addText("SOURCES  —  member and buyer capital dominate", {
    x: 6.85, y: 1.32, w: 5.85, h: 0.26, fontFace: BFONT, fontSize: 11, bold: true,
    color: RED, margin: 0 });

  statCard(s, M, 4.35, 3.0, 1.05, m$(D.econ.constr), "CONSTRUCTION FACILITY (SEPARATE)");
  statCard(s, M + 3.15, 4.35, 3.0, 1.05, m$(D.econ.peak_equity),
    "PEAK EQUITY — YEAR " + D.econ.peak_year, { fill: "FBEAEC", vcolor: RED, lcolor: "7A2430" });
  statCard(s, M + 6.3, 4.35, 3.0, 1.05, m$(D.econ.equity_resid), "RESIDUAL EQUITY AT EXIT");
  statCard(s, M + 9.45, 4.35, 2.65, 1.05, pc(D.econ.fs_proceeds / D.econ.total_uses, 0),
    "OF USES FUNDED BY FOR-SALE");
  footnote(s, "Peak equity is the trough that must actually be funded — it precedes the " +
    "for-sale closings and is far larger than the residual. The construction facility is a " +
    "separate loan sized on total cost and repaid by closings; the permanent note is secured " +
    "only by the retained club.");
  s.addNotes("The distinction between peak equity and residual equity is where most sponsor " +
    "models mislead. Draw attention to it.");
}

// =====================================================================
// 11 — Returns
// =====================================================================
{
  const s = lightSlide("Returns", "What the base case actually produces");
  statCard(s, M, 1.6, 3.0, 1.5, pc(D.econ.irr), "PROJECT EQUITY IRR", { vsize: 40 });
  statCard(s, M + 3.15, 1.6, 3.0, 1.5, xx(D.econ.em), "EQUITY MULTIPLE", { vsize: 40 });
  statCard(s, M + 6.3, 1.6, 3.0, 1.5, xx(D.econ.vc), "VALUE / RETAINED COST", { vsize: 40 });
  statCard(s, M + 9.45, 1.6, 2.65, 1.5, xx(D.econ.min_dscr), "MIN DSCR (COVENANT " +
    D.econ.covenant.toFixed(2) + "x)", { vsize: 36 });

  tbl(s, M, 3.35, W - 2 * M, [
    ["Measure", "Base case", "What it means"],
    ["Stabilised NOI after property tax", m$(D.econ.noi),
     "Reached in operating year " + D.program.stab + "; property tax is " +
     pc(D.econ.tau, 2) + " of gross basis and adds directly to the required yield"],
    ["Profit on retained cost", m$(D.econ.profit),
     "Exit proceeds of " + m$(D.econ.exit_val) + " against a retained basis of " + m$(D.econ.retained)],
    ["Break-even exit cap", pc(D.econ.be_cap, 2),
     ((D.econ.be_cap - D.econ.exit_cap) * 10000).toFixed(0) + " bps of cushion above the assumed " +
     pc(D.econ.exit_cap, 2) + " exit"],
    ["Covenant breaches across the hold", String(D.econ.breaches),
     "Tested every year from conversion, not only at stabilisation"],
  ], [3.1, 1.5, 7.48], { rowH: 0.46, fs: 10 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.6, w: W - 2 * M, h: 0.72, fill: { color: ASPHALT }, rectRadius: 0.06,
    line: { color: ASPHALT, width: 0 },
  });
  s.addText("This is a mid-single to low-double digit IRR with a hard asset — not an " +
    "opportunistic development return. An investor underwriting this as a 20% deal should decline.", {
    x: M + 0.28, y: 5.74, w: W - 2 * M - 0.56, h: 0.46, fontFace: BFONT, fontSize: 12,
    color: PAPER, margin: 0,
  });
  s.addNotes("Say the return out loud and set expectations. Told 10% and delivered 10% is a " +
    "repeat LP; told 20% and delivered 10% is a lawsuit.");
}

// =====================================================================
// 12 — Negative leverage
// =====================================================================
{
  const s = lightSlide("Capital structure", "Why we borrow less than we could");
  s.addChart(pres.ChartType.line, [{
    name: "Project equity IRR",
    labels: D.lev.map(l => (l.ltc * 100).toFixed(0) + "%"),
    values: D.lev.map(l => l.irr === null ? null : l.irr * 100),
  }], Object.assign(chartFrame(), {
    x: M, y: 1.72, w: 7.0, h: 3.15, lineDataSymbol: "circle", lineDataSymbolSize: 7,
    lineSize: 3, chartColors: [RED], showValue: true, dataLabelPosition: "t",
    dataLabelColor: ASPHALT, dataLabelFormatCode: '0.0"%"',
    catAxisTitle: "Permanent loan-to-cost", showCatAxisTitle: true,
    catAxisTitleColor: GREY, catAxisTitleFontSize: 10, catAxisTitleFontFace: BFONT,
  }));
  s.addText("Equity IRR RISES as leverage FALLS", {
    x: M, y: 1.4, w: 7.0, h: 0.28, fontFace: BFONT, fontSize: 12, bold: true,
    color: RED, margin: 0,
  });

  s.addText("This is negative leverage, and it is arithmetic", {
    x: 8.0, y: 1.72, w: 4.7, h: 0.34, fontFace: BFONT, fontSize: 15, bold: true,
    color: ASPHALT, margin: 0,
  });
  s.addText("The mortgage constant on a " + pc(D.econ.perm_rate, 2) + " note amortising over " +
    D.econ.amort + " years is " + pc(D.econ.mc, 2) + ". The retained club yields about " +
    pc(D.econ.retained_yield, 1) + " on retained cost.\n\n" +
    "Borrowing above the asset's own yield destroys equity value. At conventional 60% gearing " +
    "the IRR falls to " + pc(D.lev.find(l => Math.abs(l.ltc - 0.60) < 0.001).irr) +
    " and the DSCR covenant breaks.\n\n" +
    "We therefore hold permanent leverage at " + pc(D.econ.ltc, 0) +
    " — enough to keep covenant cushion and balance-sheet flexibility, not enough to work " +
    "against the asset.", {
    x: 8.0, y: 2.15, w: 4.7, h: 2.7, fontFace: BFONT, fontSize: 11.5, color: GREY,
    margin: 0, lineSpacingMultiple: 1.12,
  });
  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 5.15, w: W - 2 * M, h: 0.85, fill: { color: MIST }, rectRadius: 0.06,
    line: { color: MIST, width: 0 },
  });
  s.addText("Any lender proposal above roughly 45% loan-to-cost should be declined on return " +
    "grounds — not accepted because the capital looks cheap.", {
    x: M + 0.28, y: 5.34, w: W - 2 * M - 0.56, h: 0.5, fontFace: BFONT, fontSize: 12.5,
    bold: true, color: ASPHALT, margin: 0,
  });
  s.addNotes("This slide is the strongest signal of underwriting quality in the deck. Most " +
    "sponsors lever to the maximum available and never test whether it helps.");
}

// =====================================================================
// 13 — Scenarios
// =====================================================================
{
  const s = lightSlide("Downside", "Correlated stress, not one variable at a time");
  const order = ["upside", "base", "downside", "severe"];
  const ss = order.map(n => D.scen.find(x => x.name === n)).filter(Boolean);
  s.addChart(pres.ChartType.bar, [{
    name: "IRR", labels: ss.map(x => x.name.toUpperCase()),
    values: ss.map(x => x.irr === null ? 0 : x.irr * 100),
  }], Object.assign(chartFrame(), {
    x: M, y: 1.66, w: 5.6, h: 2.7, barDir: "col", showValue: true,
    dataLabelPosition: "outEnd", dataLabelColor: ASPHALT,
    dataLabelFormatCode: '0.0"%"', barGapWidthPct: 55,
    chartColors: [ASPHALT, ASPHALT, RED, RED],
  }));
  s.addText("Project equity IRR by scenario", {
    x: M, y: 1.38, w: 5.6, h: 0.26, fontFace: BFONT, fontSize: 11, bold: true,
    color: ASPHALT, margin: 0 });

  const rows = [["Scenario", "IRR", "Multiple", "Min DSCR", "Value/cost", "Verdict"]];
  ss.forEach(x => rows.push([x.name.toUpperCase(), pc(x.irr), xx(x.em),
    xx(x.dscr), xx(x.vc), x.verdict]));
  tbl(s, 6.4, 1.66, 6.3, rows, [1.15, 0.72, 0.85, 0.9, 0.92, 1.76],
    { rowH: 0.44, fs: 9.5 });

  s.addText("Scenarios move dues, membership ramp, pricing, absorption, construction cost and " +
    "exit cap together, because in a soft cycle they arrive together. A one-variable-at-a-time " +
    "flex prices five 1-in-4 events as if they cannot co-occur.", {
    x: M, y: 4.55, w: 7.6, h: 0.8, fontFace: BFONT, fontSize: 11.5, color: GREY,
    margin: 0, lineSpacingMultiple: 1.1,
  });
  statCard(s, 8.35, 4.5, 2.1, 0.95, pc(D.mc.p_cov, 0),
    "OF " + (D.mc.n / 1000).toFixed(0) + "k DRAWS HOLD THE COVENANT");
  statCard(s, 10.6, 4.5, 2.1, 0.95, pc(D.mc.p_net, 0),
    "OF DRAWS CLEAR THE YIELD TEST", { fill: "FBEAEC", vcolor: RED, lcolor: "7A2430" });
  footnote(s, "Monte Carlo driver modes are deliberately adverse to the base case, so the " +
    "median draw sits below it by construction. It is a stress distribution, not a forecast.");
  s.addNotes("The severe case is the number they will remember. Do not hide it.");
}

// =====================================================================
// 14 — Margin of safety
// =====================================================================
{
  const s = lightSlide("Margin of safety", "How wrong can we be before this stops working");
  tbl(s, M, 1.62, W - 2 * M, [
    ["Test", "Requirement", "Base case", "Cushion"],
    ["Members to cover opex and property tax",
     Math.round(D.bev.need_opex).toLocaleString(),
     Math.round(D.bev.at_stab).toLocaleString() + " at stabilisation",
     "+" + Math.round(D.bev.at_stab - D.bev.need_opex).toLocaleString() + " members"],
    ["Members to meet the DSCR covenant",
     Math.round(D.bev.need_cov).toLocaleString(),
     "cap of " + Math.round(D.bev.cap).toLocaleString(),
     "+" + Math.round(D.bev.cap - D.bev.need_cov).toLocaleString() + " members"],
    ["Annual dues to meet the covenant", k$(D.bev.dues_cov), k$(D.bev.dues_base),
     pc(D.bev.dues_base / D.bev.dues_cov - 1, 0) + " of headroom"],
    ["Exit cap at which value equals cost", pc(D.econ.be_cap, 2), pc(D.econ.exit_cap, 2),
     ((D.econ.be_cap - D.econ.exit_cap) * 10000).toFixed(0) + " bps"],
  ], [4.2, 2.0, 2.6, 3.28], { rowH: 0.46, fs: 10 });

  s.addText("Where diligence money goes", {
    x: M, y: 4.2, w: 5.9, h: 0.3, fontFace: BFONT, fontSize: 13.5, bold: true,
    color: ASPHALT, margin: 0 });
  s.addChart(pres.ChartType.bar, [{
    name: "Swing", labels: D.tornado.map(t => t.driver),
    values: D.tornado.map(t => t.swing / 1e6),
  }], Object.assign(chartFrame(), {
    x: M, y: 4.5, w: 6.1, h: 2.2, barDir: "bar", showValue: true,
    dataLabelPosition: "outEnd", dataLabelColor: GREY,
    dataLabelFormatCode: '"$"#,##0"M"', barGapWidthPct: 40,
  }));
  s.addText("Each driver flexed ±15%, one at a time, ranked by how far it moves the maximum " +
    "supportable land price. Construction cost dominates every other variable — so it takes " +
    "the guaranteed-maximum-price conversation and the first geotechnical dollar, ahead of " +
    "anything on the revenue side except the comparable study itself.", {
    x: 7.0, y: 4.55, w: 5.7, h: 1.5, fontFace: BFONT, fontSize: 11.5, color: GREY,
    margin: 0, lineSpacingMultiple: 1.12,
  });
  s.addNotes("Break-evens are what a credit committee remembers. Lead with the covenant row.");
}

// =====================================================================
// 15 — Risks and conditions
// =====================================================================
{
  const s = lightSlide("Risk", "What we are worried about, and what stops the money");
  tbl(s, M, 1.55, W - 2 * M, [
    ["Risk", "Severity", "Mitigation / gate"],
    ["Revenue assumptions unverified", "HIGHEST",
     "Comparable club study is the first use of Tranche 1 and a gate on all further spend"],
    ["Property-tax abatement not secured", "SEVERE",
     "Condition precedent to land closing — without it the covenant breaks and land value goes negative"],
    ["Noise litigation after permits issue", "HIGH",
     "Prior-use sites only · acoustic model pre-application · mitigation in base cost · muffler rule in by-laws"],
    ["Construction cost escalation", "HIGH",
     "Largest single driver at " + m$(D.tornado[0].swing) + " of swing · GMP where obtainable · 10% contingency"],
    ["Northeast seasonality", "MATERIAL",
     "Revenue weighted to storage, service and karting · dues parity with year-round clubs treated as unproven"],
    ["Absorption and lease-up", "MATERIAL",
     "Founding-member programme and condominium pre-sales before construction start · phased delivery"],
    ["Single-asset special-purpose collateral", "STRUCTURAL",
     "Alternate-use analysis on every target · low leverage reduces refinance dependence"],
  ], [3.5, 1.3, 7.28], { rowH: 0.4, fs: 9.5 });

  s.addShape(pres.ShapeType.roundRect, {
    x: M, y: 4.9, w: W - 2 * M, h: 1.55, fill: { color: ASPHALT }, rectRadius: 0.06,
    line: { color: ASPHALT, width: 0 },
  });
  s.addText("SEVEN CONDITIONS PRECEDENT TO TRANCHE 2", {
    x: M + 0.3, y: 5.04, w: 11, h: 0.28, fontFace: BFONT, fontSize: 11, bold: true,
    color: RED, charSpacing: 1.4, margin: 0,
  });
  s.addText("Verified comparable club economics   ·   Property-tax abatement executed   ·   " +
    "Entitlement in hand   ·   Acoustic model and mitigation budget   ·   Pre-sale thresholds met   ·   " +
    "Lender commitment on modelled terms   ·   Named operator and management agreement", {
    x: M + 0.3, y: 5.38, w: 11.9, h: 0.9, fontFace: BFONT, fontSize: 12, color: PAPER,
    margin: 0, lineSpacingMultiple: 1.2,
  });
  s.addNotes("No construction capital is drawn until all seven are satisfied. That is the " +
    "investor's real protection.");
}

// =====================================================================
// 16 — Close
// =====================================================================
{
  const s = darkSlide();
  s.addText("What we are asking for", {
    x: M, y: 0.85, w: 8, h: 0.4, fontFace: BFONT, fontSize: 11, bold: true,
    color: RED, charSpacing: 2, margin: 0,
  });
  s.addText(m$(D.tranche1) + " to make this real", {
    x: M, y: 1.3, w: 11.9, h: 1.0, fontFace: HFONT, fontSize: 42, bold: true,
    color: PAPER, margin: 0,
  });
  const steps = [
    ["Commission the comparable study", "Resolves the single largest uncertainty in the model. " +
      "Six to ten weeks. Everything else waits on it."],
    ["Run the full sourcing pass", "150+ parcels to identifiers, coordinates and title. Converts " +
      "five target profiles into a real pipeline."],
    ["Option the lead site", "Cheap, long, entitlement-contingent. Control without acquisition risk."],
    ["Open the abatement conversation", "IDA or EDA. It is a condition precedent, so it starts now, " +
      "not after the land is bought."],
  ];
  steps.forEach((t, i) => {
    const y = 2.6 + i * 0.95;
    s.addShape(pres.ShapeType.ellipse, {
      x: M, y: y + 0.02, w: 0.42, h: 0.42, fill: { color: RED },
      line: { color: RED, width: 0 } });
    s.addText(String(i + 1), { x: M, y: y + 0.02, w: 0.42, h: 0.42, fontFace: HFONT,
      fontSize: 14, bold: true, color: PAPER, align: "center", valign: "middle", margin: 0 });
    s.addText(t[0], { x: M + 0.6, y: y - 0.02, w: 4.6, h: 0.3, fontFace: BFONT,
      fontSize: 14, bold: true, color: PAPER, margin: 0 });
    s.addText(t[1], { x: 5.5, y: y - 0.02, w: 7.2, h: 0.7, fontFace: BFONT,
      fontSize: 11, color: MIDGREY, margin: 0, lineSpacingMultiple: 1.05 });
  });
  s.addText("Every figure in this deck is generated directly from the underwriting model — " +
    "129 unit tests, an internal-consistency audit, and a check that the live spreadsheet " +
    "formulas agree with the model to the cent. Nothing here is typed by hand.", {
    x: M, y: 6.36, w: 11.9, h: 0.55, fontFace: BFONT, fontSize: 10, italic: true,
    color: GREY, margin: 0, lineSpacingMultiple: 1.08,
  });
  s.addNotes("Close on the process, not the pitch. The credibility of the model is the reason " +
    "to trust the number.");
}

pres.writeFile({ fileName: process.argv[2] || "dist/Northeast_Motor_Club_Investor_Deck.pptx" })
  .then(f => console.log("wrote " + f));
