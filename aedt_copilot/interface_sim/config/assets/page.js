"use strict";
// 038 cut configuration page (approved mock config_demo_v5). Data = cfg-data (read only), state = cfg-state (saved).
// State values are the codes of the tool (conformal, conforming, mixed, linear_step, flip_chip ...); labels here only.
const D = JSON.parse(document.getElementById("cfg-data").textContent);
const S = JSON.parse(document.getElementById("cfg-state").textContent);
const RO = !!D.readonly, NAMES = Object.keys(D.channels);
let cur = NAMES.includes(S.current) ? S.current : NAMES[0], ADV = false;
const C = () => S.channels[cur], DC = () => D.channels[cur], DF = () => D.defaults[cur];
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const clone = o => JSON.parse(JSON.stringify(o));
const LBL = {
  cut: {bounding_box: "Bounding box", convex_hull: "Convex hull", conformal: "Conformal"},
  model: {bounding_box: "Bounding Box", conforming: "Conformal", convex_hull: "Convex Hull"},
  basis: {zero: "Zero Order", first: "First Order", second: "Second Order", mixed: "Mixed Order"},
  dist: {linear_step: ["Linear Step", "Step size", "0.01GHz"], linear_count: ["Linear Count", "Count", "1001"],
         log_scale: ["Log Scale", "Samples per decade", "10"]},
  die: {none: "None", flip_chip: "Flip chip", wire_bond: "Wire bond"},
  orient: {chip_down: "Chip down", chip_up: "Chip up"},
  shape: {cylinder: "Cylinder", spheroid: "Spheroid", none: "None"},
  sweep: {interpolation: "Interpolating", discrete: "Discrete"}};
const opts = (map, v) => Object.entries(map).map(([k, l]) => `<option value="${k}" ${k === v ? "selected" : ""}>${esc(Array.isArray(l) ? l[0] : l)}</option>`).join("");
function changed(n) { const a = clone(S.channels[n]), b = clone(D.defaults[n]); delete a.folder; delete b.folder; return !same(a, b) }

// ============================================================================ header + content frame
function header() {
  document.getElementById("subLine").innerHTML = `Request <b>${esc(D.request_id)}</b> · Board <b>${esc(D.board_name)}</b>`;
  document.getElementById("chsel").innerHTML = NAMES.map((n, i) => `<button class="${n === cur ? "on" : ""}" onclick="setCh(${i})">${changed(n) ? '<span class="dot"></span>' : ""}${esc(n)}</button>`).join("");
  const b = document.getElementById("roBanner");
  if (RO) { b.hidden = false; b.innerHTML = esc(D.ro_note || "Read-only record of the approved configuration.") }
}
function setCh(i) { cur = NAMES[i]; S.current = cur; render() }
function contentFrame() {
  const c = DC().content || {}, e = DC().ends || {}, st = C();
  const endRow = rd => { const x = e[rd] || {}; return `<tr><td class="m">${esc(rd)}</td><td>${esc(x.part || "")}</td><td>${esc(x.type || "")}</td><td>${x.bga ? "BGA / round pads" : "SMD / connector"}</td><td>${esc(x.layer || "")}</td></tr>` };
  const groups = (c.diff_groups || []).map(g => `<tr><td class="m">${g.map(esc).join(" / ")}</td></tr>`).join("") || `<tr><td>none</td></tr>`;
  const series = Object.entries(c.series || {}).map(([rd, v]) => `<tr><td class="m">${esc(rd)}</td><td class="m">${(v.nets || []).map(esc).join(" ↔ ")}</td></tr>`).join("") || `<tr><td colspan="2">none</td></tr>`;
  const diffs = (c.schematic_diffs || []).map((d, i) => `<tr><td class="m">${esc(d.item)}</td><td>${esc(d.kind || "")} (board ${esc(d.board ?? "-")}, schematic ${esc(d.schematic ?? "-")})</td>
     <td><select onchange="C().diffs[${JSON.stringify(d.item).replace(/"/g, "&quot;")}]=this.value;header()">${opts({board: "Follow the board", schematic: "Follow the schematic", drop: "Drop the net"}, (st.diffs || {})[d.item])}</select></td></tr>`).join("");
  const ch = DC().choices || {};
  const choices = Object.entries(ch).map(([rd, x]) => `<tr><td class="m">${esc(rd)}</td><td>${esc(x.label || x.rule)}</td>
     <td><select onchange="C().choices[${JSON.stringify(rd).replace(/"/g, "&quot;")}]=this.value;header()">${(x.options || []).map(o => `<option value="${esc(o)}" ${o === (st.choices || {})[rd] ? "selected" : ""}>${esc((x.option_labels || {})[o] || o)}</option>`).join("")}</select></td></tr>`).join("");
  document.getElementById("contentBody").innerHTML = `
   <div><h4>End components</h4><table><tr><th>Ref des</th><th>Part</th><th>Type</th><th>Pads</th><th>Layer</th></tr>${endRow(c.comp_a)}${endRow(c.comp_b)}</table>
    <h4 style="margin-top:12px">Differential groups</h4><table>${groups}</table></div>
   <div><h4>Series parts (kept, modelled as R)</h4><table><tr><th>Ref des</th><th>Nets</th></tr>${series}</table>
    ${diffs ? `<h4 style="margin-top:12px">Board / schematic differences</h4><table><tr><th>Net</th><th>Difference</th><th>Use</th></tr>${diffs}</table>` : ""}
    ${choices ? `<h4 style="margin-top:12px">End decisions</h4><table><tr><th>Ref des</th><th>Case</th><th>Handling</th></tr>${choices}</table>` : ""}</div>
   <div><h4>Notes for Claude (optional)</h4><textarea ${RO ? "readonly" : ""} oninput="C().content_note=this.value">${esc(st.content_note || "")}</textarea>
    <div style="font-size:12px;margin-top:4px">Nets of the channel: Include in the Nets table of Auto Generate Extent.</div></div>`;
}

// ============================================================================ Auto Generate Extent
const TYPES = ["bounding_box", "convex_hull", "conformal"];
const ICON = {bounding_box: '<rect x="4" y="4" width="36" height="18" rx="1" fill="currentColor" fill-opacity=".15" stroke="currentColor"/><path d="M9 17 L18 9 L27 13 L35 8" stroke="currentColor" stroke-width="1.6" fill="none"/>',
  convex_hull: '<path d="M5 18 L15 5 L37 4 L40 12 L30 22 L8 22 Z" fill="currentColor" fill-opacity=".15" stroke="currentColor"/><path d="M9 17 L18 9 L27 13 L35 8" stroke="currentColor" stroke-width="1.6" fill="none"/>',
  conformal: '<path d="M9 17 L18 9 L27 13 L35 8" stroke="currentColor" stroke-opacity=".2" stroke-width="9" stroke-linejoin="round" stroke-linecap="round" fill="none"/><path d="M9 17 L18 9 L27 13 L35 8" stroke="currentColor" stroke-width="1.6" fill="none"/>'};
const val = k => C().cut[k], dval = k => DF().cut[k], chg = k => String(val(k)) !== String(dval(k));
function setv(k, v) { C().cut[k] = String(v); render() }
function bump(s) { const f = Math.min(.2, Math.max(.02, Math.round((parseFloat(val("cutout.expansion")) + s * .01) * 100) / 100)); setv("cutout.expansion", f.toFixed(2)) }
const AEDT = ["#00ffff", "#b8860b", "#87cefa", "#00c060", "#9370db", "#00ffff", "#800080", "#ff00ff", "#808000", "#ffff00", "#808080", "#ffffff", "#800080", "#008080", "#c0c0c0", "#ff8c00"];
const COL = {sig: "#ff4fa3", gnd: "#3b82f6", oth: "#9aa0a6"};
const GEO = {};
function geo() {
  if (GEO[cur]) return GEO[cur];
  const L = DC().layers || {box: [0, 0, 10, 10], order: [], routed: [], layers: {}};
  const BB = L.box, PADV = 1, W0 = BB[2] - BB[0], H0 = BB[3] - BB[1], ROT = H0 > W0;
  const VW = (ROT ? H0 : W0) + 2 * PADV, VH = (ROT ? W0 : H0) + 2 * PADV, SC = Math.max(VW, VH) / 120;
  const MAT = ROT ? `matrix(0,1,1,0,${PADV - BB[1]},${PADV - BB[0]})` : `matrix(1,0,0,-1,${PADV - BB[0]},${BB[3] + PADV})`;
  const T = (x, y) => ROT ? [y - BB[1] + PADV, x - BB[0] + PADV] : [x - BB[0] + PADV, BB[3] - y + PADV];
  const ORDER = L.order || [];
  return GEO[cur] = {L, BB, ROT, VW, VH, SC, MAT, T, ORDER, LC: Object.fromEntries(ORDER.map((l, i) => [l, AEDT[i % AEDT.length]])),
    ON: Object.fromEntries(ORDER.map(l => [l, (L.routed || []).includes(l)])), ACT: (L.routed || [])[0] || ORDER[0], VB: null};
}
function copper(g) {
  const vis = g.ORDER.filter(l => g.ON[l] && l !== g.ACT).reverse();
  if (g.ON[g.ACT]) vis.push(g.ACT);
  return `<g fill-rule="evenodd">` + vis.map(l => { const d = g.L.layers[l] || {}, a = l === g.ACT;
    return `${d.gnd ? `<path d="${d.gnd}" fill="${COL.gnd}" fill-opacity="${a ? .55 : .16}"/>` : ""}${d.oth ? `<path d="${d.oth}" fill="${COL.oth}" fill-opacity="${a ? .6 : .16}"/>` : ""}` }).join("") +
    vis.map(l => { const d = g.L.layers[l] || {}, a = l === g.ACT; return d.sig ? `<path d="${d.sig}" fill="${COL.sig}" fill-opacity="${a ? 1 : .6}"/>` : "" }).join("") + `</g>`;
}
function compBoxes(g) {
  return (DC().comps || []).filter(c => c.end).map(c => { const [x0, y0, x1, y1] = c.box, a = g.T(x0, y0), b = g.T(x1, y1);
    const u0 = Math.min(a[0], b[0]), v1 = Math.max(a[1], b[1]), u1 = Math.max(a[0], b[0]), v0 = Math.min(a[1], b[1]);
    return `<rect x="${u0}" y="${v0}" width="${u1 - u0}" height="${v1 - v0}" fill="none" stroke="#fff" stroke-opacity=".55" stroke-dasharray="${g.SC} ${.6 * g.SC}" stroke-width="${.2 * g.SC}"/>
     <text x="${u0 + g.SC}" y="${v0 + 3 * g.SC}" font-size="${2.6 * g.SC}" font-family="Segoe UI,sans-serif" fill="#fff">${esc(c.refdes)}</text>` }).join("");
}
function layerPanel(g) {
  document.getElementById("layers").innerHTML = `<h4>Layers</h4><table><tr><th>Active</th><th></th><th></th><th>Visible</th></tr>
    <tr class="all"><td></td><td class="n"><b>All layers</b></td><td></td><td><input type="checkbox" title="All layers on / off" ${g.ORDER.every(l => g.ON[l]) ? "checked" : ""} onchange="layAll(this.checked)"></td></tr>
    ${g.ORDER.map((l, i) => `<tr class="${l === g.ACT ? "act" : ""} ${(g.L.routed || []).includes(l) ? "routed" : ""}">
      <td><input type="radio" name="act" ${l === g.ACT ? "checked" : ""} onchange="layAct(${i})"></td>
      <td class="n">${esc(l)}</td><td><span class="lsw" style="background:${g.LC[l]}"></span></td>
      <td><input type="checkbox" ${g.ON[l] ? "checked" : ""} onchange="layOn(${i},this.checked)"></td></tr>`).join("")}</table>
    <div class="btns"><button onclick="layPreset('all')">All</button><button onclick="layPreset('routed')">Routed</button><button onclick="layPreset('active')">Active</button></div>`;
}
function layAll(v) { const g = geo(); g.ORDER.forEach(l => g.ON[l] = v); draw() }
function layAct(i) { const g = geo(); g.ACT = g.ORDER[i]; g.ON[g.ACT] = true; draw() }
function layOn(i, v) { const g = geo(); g.ON[g.ORDER[i]] = v; draw() }
function layPreset(p) { const g = geo(); g.ORDER.forEach(l => g.ON[l] = p === "all" || (p === "routed" ? (g.L.routed || []).includes(l) : l === g.ACT)); draw() }
function netTable() {
  const c = DC().content || {}, st = C().nets, df = DF().nets, refs = DC().ref_nets || ["GND"];
  const nch = Object.keys(st).filter(n => st[n] !== df[n]).length;
  document.getElementById("labNets").innerHTML = "Nets" + (nch ? `<span class="chg">${nch} changed</span>` : "");
  document.getElementById("nets").innerHTML = `<table><tr><th>Net</th><th class="c">Include</th><th class="c">Clip at extents</th></tr>
   ${refs.map(n => `<tr class="ref"><td>${esc(n)}</td><td class="c"><input type="checkbox" checked disabled></td><td class="c"><input type="checkbox" checked disabled></td></tr>`).join("")}
   ${(c.nets || []).map((n, i) => `<tr class="${st[n] !== df[n] ? "chg" : ""}"><td>${esc(n)}</td>
     <td class="c"><input type="checkbox" ${st[n] ? "checked" : ""} onchange="netInc(${i},this.checked)"></td><td class="c"><input type="checkbox" disabled></td></tr>`).join("")}</table>`;
}
function netInc(i, v) { const n = DC().content.nets[i]; C().nets[n] = v; netTable(); header() }
function extentPts() { const E = DC().extents || {}, t = val("cutout.extent_type"), f = parseFloat(val("cutout.expansion")).toFixed(2); return (E[t] || {})[f] || null }
function draw() {
  const g = geo(), svg = document.getElementById("svg"), E = extentPts();
  zoomInit(svg); setVB();
  svg.innerHTML = `<g transform="${g.MAT}">${copper(g)}${E ? `<polygon points="${E.map(p => p.join(",")).join(" ")}" fill="#34d399" fill-opacity=".08" stroke="#34d399" stroke-width="${.35 * g.SC}"/>` : ""}</g>${compBoxes(g)}
    ${E ? "" : `<text x="${g.VW / 2}" y="${g.VH / 2}" text-anchor="middle" font-size="${3 * g.SC}" fill="#fff">No pre-computed region for this type / step</text>`}`;
  layerPanel(g); if (typeof exDraw === "function") exDraw();
}
function setVB() { const g = geo(); if (!g.VB) g.VB = [0, 0, g.VW, g.VH]; document.getElementById("svg").setAttribute("viewBox", g.VB.map(v => v.toFixed(3)).join(" "));
  const z = document.getElementById("zlev"); if (z) z.textContent = Math.round(g.VW / g.VB[2] * 100) + " %" }
function zoomAt(k, cx, cy) { const g = geo(), w = Math.min(g.VW * 1.5, Math.max(g.VW / 200, g.VB[2] * k)), h = w * g.VH / g.VW;
  g.VB = [cx - (cx - g.VB[0]) * w / g.VB[2], cy - (cy - g.VB[1]) * h / g.VB[3], w, h]; setVB() }
function zoomBtn(k) { const g = geo(); zoomAt(k, g.VB[0] + g.VB[2] / 2, g.VB[1] + g.VB[3] / 2) }
function zoomFit() { const g = geo(); g.VB = [0, 0, g.VW, g.VH]; setVB() }
function zoomInit(svg) {
  if (svg.dataset.z) return; svg.dataset.z = 1; svg.style.cursor = "grab";
  const pt = e => { const g = geo(), r = svg.getBoundingClientRect(), s = Math.max(g.VB[2] / r.width, g.VB[3] / r.height),
    ox = (r.width - g.VB[2] / s) / 2, oy = (r.height - g.VB[3] / s) / 2; return [g.VB[0] + (e.clientX - r.left - ox) * s, g.VB[1] + (e.clientY - r.top - oy) * s, s] };
  svg.addEventListener("wheel", e => { e.preventDefault(); const [x, y] = pt(e); zoomAt(e.deltaY < 0 ? 1 / 1.25 : 1.25, x, y) }, {passive: false});
  let drag = null;
  svg.addEventListener("pointerdown", e => { const g = geo(); drag = [e.clientX, e.clientY, g.VB[0], g.VB[1], pt(e)[2]]; svg.setPointerCapture(e.pointerId); svg.style.cursor = "grabbing" });
  svg.addEventListener("pointermove", e => { if (!drag) return; const g = geo(); g.VB[0] = drag[2] - (e.clientX - drag[0]) * drag[4]; g.VB[1] = drag[3] - (e.clientY - drag[1]) * drag[4]; setVB() });
  const up = () => { drag = null; svg.style.cursor = "grab" }; svg.addEventListener("pointerup", up); svg.addEventListener("pointercancel", up);
  svg.addEventListener("dblclick", zoomFit);
}
function cutFrame() {
  const t = val("cutout.extent_type");
  document.getElementById("extHint").textContent = "Non-clipped nets · reference net " + (DC().ref_nets || ["GND"]).join(", ");
  document.getElementById("tiles").innerHTML = TYPES.map(v => `<button class="tile ${t === v ? "on" : ""}" onclick="setv('cutout.extent_type','${v}')"><svg viewBox="0 0 44 26">${ICON[v]}</svg>${LBL.cut[v]}</button>`).join("");
  document.getElementById("labType").innerHTML = "Expansion type" + (chg("cutout.extent_type") ? `<span class="chg">default ${LBL.cut[dval("cutout.extent_type")] || dval("cutout.extent_type")}</span>` : "");
  const e = val("cutout.expansion"), r = document.getElementById("rng"); r.value = e; r.style.setProperty("--p", ((e - .02) / .18 * 100) + "%");
  document.getElementById("expV").textContent = parseFloat(e).toFixed(2);
  document.getElementById("tickDef").textContent = parseFloat(dval("cutout.expansion")).toFixed(2);
  document.getElementById("labExp").innerHTML = "Expansion" + (chg("cutout.expansion") ? `<span class="chg">default ${dval("cutout.expansion")}</span>` : "");
  const rows = D.template.adv || [], na = rows.filter(x => chg(x.key)).length;
  const b = document.getElementById("advBtn"); b.className = "advbtn" + (ADV ? " open" : "");
  b.innerHTML = `<span class="chev">›</span>Advanced · corner style, increments, GND cleanup, series parts${na ? `<span class="n">${na} changed</span>` : ""}`;
  const a = document.getElementById("advBody"); a.className = "adv" + (ADV ? " open" : "");
  const groups = [["cutout.", "Extent"], ["cleanup.", "GND cleanup"], ["series.", "Series parts"]];
  a.innerHTML = groups.map(([pre, gname]) => `<div class="agrp"><h3>${gname}</h3>${rows.filter(x => x.key.startsWith(pre)).map(x => { const v = val(x.key), c = chg(x.key), i = rows.indexOf(x);
    const inp = x.type === "bool" ? `<label class="tsw"><input type="checkbox" ${v === "true" ? "checked" : ""} onchange="setAdv(${i},this.checked)"><span></span></label><span class="u"></span>`
      : `<input type="text" value="${esc(v)}" onchange="setAdv(${i},this.value.trim())"><span class="u">${esc(x.unit || "")}</span>`;
    return `<div class="kv ${c ? "c" : ""}" title="${esc(x.key)}"><label>${esc(x.label)}</label><span class="d">${c ? "def " + esc(dval(x.key)) : ""}</span><div class="in">${inp}</div></div>` }).join("")}</div>`).join("");
  netTable(); draw();
}
function setAdv(i, v) { setv(D.template.adv[i].key, v) }
document.getElementById("rng").oninput = e => setv("cutout.expansion", parseFloat(e.target.value).toFixed(2));

// ============================================================================ Component Model
const VIEW3 = {}, CMTAB = {};
const ENDS = () => DC().ends || {};
const CM = rd => C().cm[rd], CMD = rd => DF().cm[rd];
const RDS = () => Object.keys(ENDS());
function shortSide(rd) { const s = (ENDS()[rd].signal || [])[0]; return s ? Math.min(s.box[2] - s.box[0], s.box[3] - s.box[1]) : 0 }
function bodyC(rd) { const e = ENDS()[rd], all = [...e.signal, ...e.gnd, ...(e.other || [])]; return [all.reduce((a, q) => a + q.x, 0) / all.length, all.reduce((a, q) => a + q.y, 0) / all.length] }
const TRACE_LAYER_COLS = ["#ffd166", "#06d6a0", "#4cc9f0", "#c77dff", "#ff9f1c", "#90be6d"];
function innerLayers() { const out = []; for (const rd of RDS()) for (const t of ENDS()[rd].traces || []) if (t.inner && !out.includes(t.layer)) out.push(t.layer); return out }
const layerCol = l => TRACE_LAYER_COLS[Math.max(0, innerLayers().indexOf(l)) % TRACE_LAYER_COLS.length];   // 044
const pctOf = c => (c.port_pct === undefined || c.port_pct === null || c.port_pct === "") ? (c.port_location === "centre" ? 50 : 0) : Math.max(0, Math.min(100, +c.port_pct));
function portXY(rd, p) {
  const e = ENDS()[rd]; if (e.bga) return [p.x, p.y];
  if ("port_span" in p) {                                  // 041 slider: same interpolation as the build (cutter.port_at)
    if (!p.port_span) return [p.x, p.y];
    const t = pctOf(CM(rd)) / 100, [a, b] = p.port_span; return [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])];
  }
  if (CM(rd).port_location === "centre") return [p.x, p.y];
  if ("port_end" in p) return p.port_end || [p.x, p.y];   // 041: position computed by the tool (same as the build)
  const [cx, cy] = bodyC(rd), [x0, y0, x1, y1] = p.box, L = Math.max(x1 - x0, y1 - y0), W = Math.min(x1 - x0, y1 - y0), d = (L - W) / 2;
  const ab = x1 - x0 >= y1 - y0 ? [[p.x - d, p.y], [p.x + d, p.y]] : [[p.x, p.y - d], [p.x, p.y + d]];
  return Math.hypot(ab[0][0] - cx, ab[0][1] - cy) < Math.hypot(ab[1][0] - cx, ab[1][1] - cy) ? ab[0] : ab[1];
}
const ballXY = (rd, p, sig) => sig ? portXY(rd, p) : [p.x, p.y];
function frame(rd) { const e = ENDS()[rd], sel = [...e.signal, ...e.gnd];
  const x0 = Math.min(...sel.map(p => p.box[0])), y0 = Math.min(...sel.map(p => p.box[1])), x1 = Math.max(...sel.map(p => p.box[2])), y1 = Math.max(...sel.map(p => p.box[3]));
  const m = Math.max(x1 - x0, y1 - y0) * .12 + .3; return [x0 - m, y0 - m, x1 + m, y1 + m] }
const rid = rd => RDS().indexOf(rd);
function topStatic(rd) {
  const e = ENDS()[rd], [x0, y0, x1, y1] = frame(rd), W = x1 - x0, H = y1 - y0, s = Math.max(W, H) / 100;
  const X = x => (x - x0).toFixed(4), Y = y => (y1 - y).toFixed(4);
  const near = (e.other || []).filter(p => p.box[2] > x0 && p.box[0] < x1 && p.box[3] > y0 && p.box[1] < y1);
  const padEl = (p, fill, op) => { const [a, b, c, d] = p.box; return e.bga ? `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="${((c - a) / 2).toFixed(4)}" fill="${fill}" fill-opacity="${op}"/>`
    : `<rect x="${X(a)}" y="${Y(d)}" width="${(c - a).toFixed(4)}" height="${(d - b).toFixed(4)}" fill="${fill}" fill-opacity="${op}"/>` };
  const lbl = e.signal.map(p => `<text x="${(+X(p.box[2]) + .6 * s).toFixed(3)}" y="${(+Y(p.y) + 1.2 * s).toFixed(3)}" font-size="${2.6 * s}" fill="#fff" font-family="Segoe UI,sans-serif">${esc(p.pin)}</text>`).join("");
  const trs = [...(e.traces || [])].sort((a, b) => (b.inner ? 1 : 0) - (a.inner ? 1 : 0)).map(t => { const pl = `points="${t.pts.map(([x, y]) => X(x) + "," + Y(y)).join(" ")}" fill="none"`;
    return t.inner   // 044: inner-layer trace leaving a via in the pad = dashed, colour of its layer
      ? `<polyline ${pl} stroke="${layerCol(t.layer)}" stroke-opacity=".9" stroke-width="${Math.max(t.w_mm * .7, .15 * s).toFixed(4)}" stroke-dasharray="${(1.6 * s).toFixed(3)} ${(1 * s).toFixed(3)}" stroke-linecap="round" stroke-linejoin="round"/>`
      : `<polyline ${pl} stroke="#ff8cc6" stroke-opacity=".6" stroke-width="${Math.max(t.w_mm, .2 * s).toFixed(4)}" stroke-linecap="round" stroke-linejoin="round"/>` }).join("");
  return `<svg viewBox="0 0 ${W.toFixed(3)} ${H.toFixed(3)}" preserveAspectRatio="xMidYMid meet"><rect width="${W}" height="${H}" fill="#151a22"/>
    ${trs}${near.map(p => padEl(p, "#9aa0a6", .35)).join("")}${e.gnd.map(p => padEl(p, "#3b82f6", .9)).join("")}${e.signal.map(p => padEl(p, "#ff4fa3", .95)).join("")}
    <g id="tb-${rid(rd)}"></g>${lbl}</svg>`;
}
function topBalls(rd) {
  const e = ENDS()[rd], [x0, y0, x1, y1] = frame(rd), s = Math.max(x1 - x0, y1 - y0) / 100, c = CM(rd);
  const X = x => (x - x0).toFixed(4), Y = y => (y1 - y).toFixed(4), r = (+c.ball_ratio || 0) * shortSide(rd) / 2;
  const balls = c.ball_shape === "none" ? "" : [...e.signal.map(p => [p, 1]), ...e.gnd.map(p => [p, 0])].map(([p, sg]) => { const [u, v] = ballXY(rd, p, sg);
    return `<circle cx="${X(u)}" cy="${Y(v)}" r="${r.toFixed(4)}" fill="#fff" fill-opacity=".18" stroke="#fff" stroke-width="${.3 * s}" stroke-dasharray="${.8 * s} ${.5 * s}"/>` }).join("");
  const ports = e.signal.map(p => { const [u, v] = portXY(rd, p), k = .9 * s;
    return `<g stroke="#fff" stroke-width="${.35 * s}"><line x1="${+X(u) - k}" y1="${Y(v)}" x2="${+X(u) + k}" y2="${Y(v)}"/><line x1="${X(u)}" y1="${+Y(v) - k}" x2="${X(u)}" y2="${+Y(v) + k}"/></g>
      <circle cx="${X(u)}" cy="${Y(v)}" r="${.45 * s}" fill="#111" stroke="#fff" stroke-width="${.2 * s}"/>` }).join("");
  const el = document.getElementById("tb-" + rid(rd)); if (el) el.innerHTML = balls + ports;
}
function draw3d(rd) {
  const cv = document.getElementById("c3-" + rid(rd)); if (!cv) return;
  const e = ENDS()[rd], c = CM(rd), key = cur + "|" + rd, V = VIEW3[key] || (VIEW3[key] = {yaw: -35, pitch: 58, zoom: 1});
  const dpr = window.devicePixelRatio || 1, Wc = cv.clientWidth, Hc = cv.clientHeight; cv.width = Wc * dpr; cv.height = Hc * dpr;
  const g = cv.getContext("2d"); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.fillStyle = "#151a22"; g.fillRect(0, 0, Wc, Hc);
  const [x0, y0, x1, y1] = frame(rd), cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, span = Math.max(x1 - x0, y1 - y0);
  const sc = Math.min(Wc, Hc) / span * 0.95 * V.zoom, ya = V.yaw * Math.PI / 180, pa = V.pitch * Math.PI / 180;
  const cyw = Math.cos(ya), syw = Math.sin(ya), cp = Math.cos(pa), sp = Math.sin(pa);
  const H = +c.ball_height_mm || 0, r = (+c.ball_ratio || 0) * shortSide(rd) / 2, ballOn = c.ball_shape !== "none" && r > 0;
  const P = (x, y, z) => { const dx = x - cx, dy = y - cy, u = dx * cyw - dy * syw, v = dx * syw + dy * cyw; return [Wc / 2 + u * sc, Hc / 2 + (-v * cp - z * sp) * sc, v * sp - z * cp] };
  const poly = (pts, fill, stroke) => { g.beginPath(); pts.forEach((q, i) => i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1])); g.closePath();
    if (fill) { g.fillStyle = fill; g.fill() } if (stroke) { g.strokeStyle = stroke; g.lineWidth = .6; g.stroke() } };
  const N = 28, circ = (x, y, z, rr) => Array.from({length: N}, (_, i) => { const a = i / N * 2 * Math.PI; return P(x + rr * Math.cos(a), y + rr * Math.sin(a), z) });
  const trs = e.traces || [], zi = -span * .1;              // 044: traces (inner plane under the board, surface)
  const line3 = (pts, z, col, w, dash) => { g.beginPath(); pts.forEach(([x, y], k) => { const q = P(x, y, z); k ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]) });
    g.strokeStyle = col; g.lineWidth = w; g.setLineDash(dash || []); g.lineCap = "round"; g.lineJoin = "round"; g.stroke(); g.setLineDash([]) };
  trs.filter(t => t.inner).forEach(t => line3(t.pts, zi, layerCol(t.layer), Math.max(2.2, t.w_mm * sc), [7, 4]));
  poly([P(x0, y0, 0), P(x1, y0, 0), P(x1, y1, 0), P(x0, y1, 0)], trs.some(t => t.inner) ? "rgba(29,36,48,.45)" : "#1d2430", "#2c3542");
  trs.filter(t => !t.inner).forEach(t => line3(t.pts, 0, "rgba(255,140,198,.6)", Math.max(1.2, t.w_mm * sc)));
  for (const t of trs) {                                     // via: vertical dashed segment pad (z 0) -> inner plane
    if (!t.inner || !t.via) continue;
    const a = P(t.via[0], t.via[1], 0), b = P(t.via[0], t.via[1], zi);
    g.strokeStyle = layerCol(t.layer); g.lineWidth = 1.8; g.setLineDash([3, 3]);
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); g.setLineDash([]);
  }
  const near = (e.other || []).filter(p => p.box[2] > x0 && p.box[0] < x1 && p.box[3] > y0 && p.box[1] < y1);
  const pad = (p, col) => { const [a, b, cc, d] = p.box; if (e.bga) poly(circ(p.x, p.y, 0, (cc - a) / 2), col); else poly([P(a, b, 0), P(cc, b, 0), P(cc, d, 0), P(a, d, 0)], col) };
  near.forEach(p => pad(p, "rgba(154,160,166,.35)")); e.gnd.forEach(p => pad(p, "#3b82f6")); e.signal.forEach(p => pad(p, "#ff4fa3"));
  const items = [...e.signal.map(p => [p, 1]), ...e.gnd.map(p => [p, 0])].map(([p, sg]) => { const [u, v] = ballXY(rd, p, sg); return {p, u, v, d: P(u, v, 0)[2], sig: sg} }).sort((a, b) => a.d - b.d);
  for (const it of items) {
    if (ballOn) {
      if (c.ball_shape === "spheroid") {
        const ctr = P(it.u, it.v, H / 2), rx = r * sc, ry = Math.sqrt((r * cp) ** 2 + ((H / 2) * sp) ** 2) * sc;
        const gr = g.createRadialGradient(ctr[0] - rx * .35, ctr[1] - ry * .35, rx * .1, ctr[0], ctr[1], Math.max(rx, ry));
        gr.addColorStop(0, "#f5f6f8"); gr.addColorStop(1, "#8b929c"); g.fillStyle = gr;
        g.beginPath(); g.ellipse(ctr[0], ctr[1], rx, ry, 0, 0, 2 * Math.PI); g.fill();
      } else {
        const bot = circ(it.u, it.v, 0, r), top = circ(it.u, it.v, H, r);
        for (let i = 0; i < N; i++) { const j = (i + 1) % N, a = i / N * 2 * Math.PI + Math.PI / N;
          const nx = Math.cos(a), ny = Math.sin(a), face = (nx * syw + ny * cyw) * sp;
          if (face < -1e-6) continue; const sh = Math.round(150 + 80 * Math.max(0, nx * cyw - ny * syw));
          poly([bot[i], bot[j], top[j], top[i]], `rgb(${sh},${sh + 4},${sh + 10})`) }
        poly(top, "#e9ecf1", "#9aa3ae");
      }
    }
    if (it.sig) { const b = P(it.u, it.v, ballOn ? H : 0), t = P(it.u, it.v, (ballOn ? H : 0) + span * .06);
      g.strokeStyle = "#fff"; g.lineWidth = 1.4; g.beginPath(); g.moveTo(b[0], b[1]); g.lineTo(t[0], t[1]); g.stroke();
      g.fillStyle = "#111"; g.beginPath(); g.arc(t[0], t[1], 3.2, 0, 2 * Math.PI); g.fill(); g.strokeStyle = "#fff"; g.lineWidth = 1.2; g.stroke();
      g.fillStyle = "#fff"; g.font = "11px Segoe UI"; g.fillText(it.p.pin, t[0] + 5, t[1] - 4) }
  }
  if (c.die_type !== "none") { const zb = ballOn ? H : 0, zt = zb + span * .05, m = span * .05;
    poly([[x0 + m, y0 + m], [x1 - m, y0 + m], [x1 - m, y1 - m], [x0 + m, y1 - m]].map(q => P(q[0], q[1], zt)), "rgba(120,130,150,.18)", "rgba(255,255,255,.35)") }
}
function init3d(rd) {
  const cv = document.getElementById("c3-" + rid(rd)); if (!cv || cv.dataset.i) return; cv.dataset.i = 1;
  const V = () => VIEW3[cur + "|" + rd];
  let d = null; cv.addEventListener("pointerdown", ev => { d = [ev.clientX, ev.clientY, V().yaw, V().pitch]; cv.setPointerCapture(ev.pointerId) });
  cv.addEventListener("pointermove", ev => { if (!d) return; V().yaw = d[2] + (ev.clientX - d[0]) * .4; V().pitch = Math.max(5, Math.min(89, d[3] - (ev.clientY - d[1]) * .3)); draw3d(rd) });
  cv.addEventListener("pointerup", () => d = null);
  cv.addEventListener("dblclick", () => { VIEW3[cur + "|" + rd] = {yaw: -35, pitch: 58, zoom: 1}; draw3d(rd) });
  cv.addEventListener("wheel", ev => { ev.preventDefault(); V().zoom = Math.max(.5, Math.min(8, V().zoom * (ev.deltaY < 0 ? 1.15 : 1 / 1.15))); draw3d(rd) }, {passive: false});
}
function cmUpdate(rd) {
  topBalls(rd); draw3d(rd); const c = CM(rd), i = rid(rd), mm = ((+c.ball_ratio || 0) * shortSide(rd)).toFixed(3);
  const q = id => document.getElementById(id + "-" + i); if (!q("rv")) return;
  q("rv").textContent = (+c.ball_ratio).toFixed(2); q("rmm").textContent = mm; q("mid").value = mm; q("rs").style.setProperty("--rr", c.ball_ratio);
  q("rl").classList.toggle("c", String(c.ball_ratio) !== String(CMD(rd).ball_ratio)); header();
}
function cmRatio(i, v) { const rd = RDS()[i]; CM(rd).ball_ratio = (+v).toFixed(2); cmUpdate(rd) }
function cmSet(i, k, v) { const rd = RDS()[i]; CM(rd)[k] = v; cmRender(); header() }
function portOffsets(rd) {                                 // 041 slider: port centre distance from the body-side pad end
  const e = ENDS()[rd], t = pctOf(CM(rd)) / 100, g = {}; let fixed = 0;
  for (const p of e.signal || []) {
    if (!("port_span" in p)) continue;
    if (!p.port_span) { fixed++; continue }
    const L = Math.max(p.box[2] - p.box[0], p.box[3] - p.box[1]), W = Math.min(p.box[2] - p.box[0], p.box[3] - p.box[1]);
    const k = L.toFixed(3) + " × " + W.toFixed(3); g[k] = (g[k] || 0) + 1; g[k + "|o"] = W / 2 + t * (L - W);
  }
  const rows = Object.keys(g).filter(k => !k.endsWith("|o")).map(k => `Pad ${k} mm (${g[k]}): port centre ${g[k + "|o"].toFixed(3)} mm (${(g[k + "|o"] / .0254).toFixed(1)} mil) from the body-side end`);
  if (fixed) rows.push(`${fixed} pad(s) square / round: port at the pad centre`);
  return rows.join("<br>");
}
function cmPort(i, v) {
  const rd = RDS()[i], c = CM(rd), q = id => document.getElementById(id + "-" + i);
  c.port_pct = Math.round(+v); c.port_location = c.port_pct === 50 ? "centre" : "end";
  if (q("pp")) { q("pp").value = c.port_pct; q("pp").style.setProperty("--rr", c.port_pct / 100); q("ppv").textContent = c.port_pct + " %"; q("ppo").innerHTML = portOffsets(rd);
    q("ppl").classList.toggle("c", String(pctOf(c)) !== String(pctOf(CMD(rd)))) }
  topBalls(rd); draw3d(rd); header();
}
function cmTab(i, t) { CMTAB[cur + "|" + RDS()[i]] = t; cmRender() }
function cmRender() {
  document.getElementById("cmBody").innerHTML = RDS().map((rd, i) => {
    const e = ENDS()[rd], c = CM(rd), d = CMD(rd), ch = k => String(c[k]) !== String(d[k]) ? ' class="c"' : "";
    const sel = (k, map) => `<select onchange="cmSet(${i},'${k}',this.value)">${opts(map, c[k])}</select>`;
    const T = CMTAB[cur + "|" + rd] || "info", dot = ks => ks.some(k => String(c[k]) !== String(d[k])) ? '<span class="tdot"></span>' : "";
    const ss = shortSide(rd), dm = ((+c.ball_ratio || 0) * ss).toFixed(3);
    const info = `<h3>Component Info</h3>
      <div class="kv2"><span>Part name</span><b>${esc(e.part)}_cut</b></div><div class="kv2"><span>Part type</span><b>${esc(e.type)}</b></div>
      <div class="kv2"><span>Ref des</span><b>${esc(rd)}</b></div><div class="kv2"><span>No. pins</span><b>${e.pins_cut} <small>(${e.signal.length} signal + ${e.gnd.length} GND kept, of ${e.pins_total})</small></b></div>
      <h3>Die Properties</h3>
      <div class="kv2"><span${ch("die_type")}>Type</span>${sel("die_type", LBL.die)}</div>
      <div class="kv2"><span${ch("die_orientation")}>Orientation</span>${sel("die_orientation", LBL.orient)}</div>
      <div class="kv2"><span${ch("die_height_mm")}>Height</span><div class="u"><input value="${esc(c.die_height_mm)}" ${c.die_type === "wire_bond" ? "" : "disabled"} onchange="cmSet(${i},'die_height_mm',this.value.trim())"><i>mm</i></div></div>`;
    const ball = `<h3>Solder Ball Properties</h3>
      <div class="kv2"><span${ch("ball_shape")}>Shape</span>${sel("ball_shape", LBL.shape)}</div>
      <div class="kv2"><span id="rl-${i}"${ch("ball_ratio")}>Diameter</span><div class="ratio"><input type="range" id="rs-${i}" style="--rr:${c.ball_ratio}" min="0" max="1" step="0.01" value="${c.ball_ratio}" ${c.ball_shape === "none" ? "disabled" : ""}
        oninput="cmRatio(${i},this.value)"><b id="rv-${i}">${(+c.ball_ratio).toFixed(2)}</b><i>× pad</i></div></div>
      <div class="kv2"><span></span><div class="u"><i>= <b id="rmm-${i}">${dm}</b> mm diameter (pad ${ss.toFixed(3)} mm)</i></div></div>
      <div class="kv2"><span>Mid diameter</span><div class="u"><input id="mid-${i}" value="${dm}" disabled><i>mm</i></div></div>
      <div class="kv2"><span${ch("ball_height_mm")}>Height</span><div class="u"><input value="${esc(c.ball_height_mm)}" ${c.ball_shape === "none" ? "disabled" : ""} onchange="cmSet(${i},'ball_height_mm',this.value.trim())"><i>mm</i></div></div>
      <div class="kv2"><span${ch("ball_material")}>Material</span><input value="${esc(c.ball_material)}" onchange="cmSet(${i},'ball_material',this.value.trim())"></div>
      <h3>Port location</h3>
      ${e.bga ? `<div class="note2">Round pads (BGA): port at the pad centre.</div>`
        : `<div class="kv2"><span id="ppl-${i}"${String(pctOf(c)) !== String(pctOf(d)) ? ' class="c"' : ""}>Position</span><div class="ratio"><i>Body side</i><input type="range" id="pp-${i}" style="--rr:${pctOf(c) / 100}" min="0" max="100" step="1" value="${pctOf(c)}"
             oninput="cmPort(${i},this.value)"><i>Outer</i><b id="ppv-${i}">${pctOf(c)} %</b></div></div>
           <div class="seg2" style="margin:4px 0 6px"><button onclick="cmPort(${i},0)">Body end (0 %)</button><button onclick="cmPort(${i},50)">Centre = pin (50 %)</button><button onclick="cmPort(${i},100)">Outer end (100 %)</button></div>
           <div class="note2" id="ppo-${i}">${portOffsets(rd)}</div>
           ${e.no_trace_exit ? `<div class="note2">Via in pad / no trace on the pad layer: the via is not the port; 50 % = pad centre = pin position.</div>` : ""}`}`;
    return `<div class="cmdev"><div class="cmhead">${esc(rd)}:${esc(e.part)}_cut · ${esc(e.layer)}</div><div class="cm">
     <div class="cmpic"><div class="cmviews"><div class="cmtop">${topStatic(rd)}<div class="vt">Top view</div></div>
       <div class="cm3"><canvas id="c3-${i}"></canvas><div class="vt">3D view · drag = rotate, wheel = zoom, double-click = reset</div></div></div>
       <div class="legend"><span><i style="background:#ff4fa3"></i>Signal pad</span><span><i style="background:#ff8cc6;opacity:.6;height:4px"></i>Trace (${esc(e.layer)})</span>${innerLayers().filter(l => (e.traces || []).some(t => t.inner && t.layer === l)).map(l => `<span><i style="background:none;border-top:3px dashed ${layerCol(l)};height:0"></i>Trace ${esc(l)} (via in pad)</span>`).join("")}<span><i style="background:#3b82f6"></i>GND pad kept</span>
        <span><i style="background:#9aa0a6;opacity:.5"></i>Pad removed by the cut</span>
        <span><i style="background:#fff;border:1px dashed #555;border-radius:50%"></i>Solder ball</span><span>⊕ Port</span></div></div>
     <div class="cmform"><div class="astabs cmt"><button class="${T === "info" ? "on" : ""}" onclick="cmTab(${i},'info')">Component Info${dot(["die_type", "die_orientation", "die_height_mm"])}</button>
       <button class="${T === "ball" ? "on" : ""}" onclick="cmTab(${i},'ball')">Solder Ball Properties${dot(["ball_shape", "ball_ratio", "ball_height_mm", "ball_material", "port_location", "port_pct"])}</button></div>
      <div class="cmtab">${T === "info" ? info : ball}</div></div></div></div>`;
  }).join("") || `<div style="padding:14px 20px">No end component data.</div>`;
  for (const rd of RDS()) { topBalls(rd); init3d(rd); draw3d(rd) }
}
window.addEventListener("resize", () => { for (const rd of RDS()) draw3d(rd); if (typeof ex3d === "function") ex3d() });

// ============================================================================ Analysis Setup
const AST = {stab: "General", wtab: "Edit Frequency Sweep", sel: 0};
const UNITS = ["GHz", "MHz", "kHz", "Hz"];
const AS = () => C().setup, SW = () => C().sweep;
function fGHz(s) { const m = /^\s*([0-9]*\.?[0-9]+(?:e[+-]?\d+)?)\s*(GHz|MHz|kHz|Hz)?\s*$/i.exec(String(s ?? "")); return m ? +m[1] * {ghz: 1, mhz: 1e-3, khz: 1e-6, hz: 1e-9}[(m[2] || "GHz").toLowerCase()] : NaN }
function rowPts(r) {
  const s = fGHz(r.start), e = fGHz(r.end);
  if (!(s >= 0) || !(e > s)) return {err: "Start must be >= 0 and below End"};
  if (r.dist === "linear_step") { const v = fGHz(r.value); if (!(v > 0) || v > e - s) return {err: "0 < step <= End - Start"}; return {n: Math.floor((e - s) / v + 1e-9) + 1} }
  const n = +r.value;
  if (r.dist === "linear_count") { if (!(Number.isInteger(n) && n >= 2)) return {err: "Count: whole number >= 2"}; return {n} }
  if (!(s > 0)) return {err: "Log Scale needs Start > 0"}; if (!(Number.isInteger(n) && n >= 1)) return {err: "Samples per decade >= 1"};
  return {n: Math.ceil(Math.log10(e / s) * n - 1e-9) + 1};
}
function sweepEnd() { let m = NaN; SW().rows.forEach(r => { const e = fGHz(r.end); if (e > 0 && !(e <= m)) m = e }); return m }
const asCh = (sec, k) => !same(C()[sec][k], DF()[sec][k]) ? ' class="c"' : "";
function asSet(sec, k, v) { C()[sec][k] = v; if (sec === "setup" && k === "freq_ghz") C().setup.freq_linked = false;
  if (sec === "sweep" && k === "type" && v === "discrete" && AST.wtab === "Interpolation") AST.wtab = "Edit Frequency Sweep"; asRender(); header() }
function asRow(i, k, v, live) { SW().rows[i][k] = v; if (k === "dist") SW().rows[i].value = LBL.dist[v][2]; if (live) { asPts(); return } asRender(); header() }
function asRowOp(op) { const r = {dist: "linear_step", start: "", end: "", value: ""}, i = AST.sel, rows = SW().rows;
  if (op === "above") rows.splice(i, 0, r); else if (op === "below") { rows.splice(i + 1, 0, r); AST.sel = i + 1 }
  else if (rows.length > 1) { rows.splice(i, 1); AST.sel = Math.max(0, i - 1) } asRender(); header() }
function asSel(i, tr) { AST.sel = i; tr.parentNode.querySelectorAll("tr").forEach(x => x.classList.toggle("sel", x === tr)) }
function asMulti(i, k, v) { const m = AS().multi; if (i === "add") m.push({f: "", unit: "GHz", ds: "0.02"}); else if (i === "del") { if (m.length > 1) m.pop() } else m[i][k] = v; asRender(); header() }
function asPts() {
  let tot = 0, bad = 0;
  SW().rows.forEach((r, i) => { const p = rowPts(r), el = document.getElementById("pe-" + i);
    if (el) { el.textContent = p.err ? "⚠ " + p.err : p.n + " points"; el.className = p.err ? "pe bad" : "pe" } if (p.err) bad++; else tot += p.n });
  const h = document.getElementById("ptot"); if (h) h.textContent = bad ? "Frequency Sweeps — fix the rows marked ⚠" : `Frequency Sweeps [${tot} points defined]`;
  const f = document.getElementById("asfreq"); if (f && AS().freq_linked) { const e = sweepEnd(); f.value = e > 0 ? String(+e.toFixed(6)) : "" }
}
const tabs = (curT, list, fn) => `<div class="astabs">${list.map(t => `<button class="${t === curT ? "on" : ""}" onclick="${fn}('${t}')">${t}</button>`).join("")}</div>`;
const chk = (sec, k, lab) => `<label class="ck"><input type="checkbox" ${C()[sec][k] ? "checked" : ""} onchange="asSet('${sec}','${k}',this.checked)"><span${asCh(sec, k)}>${lab}</span></label>`;
const inum = (sec, k, w) => `<input value="${esc(C()[sec][k])}" style="width:${w || 110}px" onchange="asSet('${sec}','${k}',this.value.trim())">`;
function asSetup() {
  const t = AST.stab, s = AS(); let h = "";
  if (t === "General") {
    h = `<div class="grp"><h4>Adaptive Solutions</h4>
     <div class="kv2"><span${asCh("setup", "mode")}>Solution Frequency</span><div class="seg2">
      <button class="${s.mode === "single" ? "on" : ""}" onclick="asSet('setup','mode','single')">Single</button>
      <button class="${s.mode === "multi" ? "on" : ""}" onclick="asSetMulti()">Multi-Frequencies</button></div></div>`;
    if (s.mode === "single") h += `
     <div class="kv2"><span${asCh("setup", "freq_ghz")}>Frequency</span><div class="u"><input id="asfreq" value="${esc(s.freq_linked ? "" : s.freq_ghz)}" style="width:110px" onchange="asSet('setup','freq_ghz',this.value.trim())"><i>GHz</i>
      ${s.freq_linked ? "<i>= sweep end</i>" : `<button class="btn" style="padding:2px 8px" onclick="C().setup.freq_linked=true;asRender()">= sweep end</button>`}</div></div>
     <div class="kv2"><span${asCh("setup", "max_passes")}>Maximum Number of Passes</span>${inum("setup", "max_passes")}</div>
     <div class="kv2"><span${asCh("setup", "max_delta_s")}>Maximum Delta S</span>${inum("setup", "max_delta_s")}</div>`;
    else h += `<table class="ft"><tr><th>#</th><th>Frequency</th><th>Units</th><th>Max Delta S</th></tr>${s.multi.map((m, i) => `<tr><td>${i + 1}</td>
      <td><input value="${esc(m.f)}" onchange="asMulti(${i},'f',this.value.trim())"></td>
      <td><select onchange="asMulti(${i},'unit',this.value)">${UNITS.map(u => `<option${u === m.unit ? " selected" : ""}>${u}</option>`).join("")}</select></td>
      <td><input value="${esc(m.ds)}" onchange="asMulti(${i},'ds',this.value.trim())"></td></tr>`).join("")}</table>
     <div class="btnrow"><button onclick="asMulti('add')">Add</button><button onclick="asMulti('del')" ${s.multi.length > 1 ? "" : "disabled"}>Remove</button></div>
     <div class="kv2"><span${asCh("setup", "multi_passes")}>Maximum Number of Passes</span>${inum("setup", "multi_passes")}</div>`;
    h += "</div>";
  }
  if (t === "Options") h = `<div class="grp"><h4>Adaptive Options</h4>
     <div class="kv2"><span${asCh("setup", "refine_pct")}>Maximum Refinement Per Pass</span><div class="u">${inum("setup", "refine_pct")}<i>%</i></div></div></div>
     <div class="grp"><h4>Solution Options</h4><div class="kv2"><span${asCh("setup", "basis")}>Order of Basis Functions</span>
     <select onchange="asSet('setup','basis',this.value)">${opts(LBL.basis, s.basis)}</select></div></div>`;
  if (t === "Advanced") h = `<div class="grp"><h4>Vias</h4>${chk("setup", "via_mesh_3d", "Mesh as a 3D via (only permitted for no-load vias)")}
     <div class="kv2 ind"><span${asCh("setup", "via_sides")}>Number of sides for meshed vias</span><input type="number" min="3" max="64" value="${esc(s.via_sides)}" style="width:80px" ${s.via_mesh_3d ? "" : "disabled"} onchange="asSet('setup','via_sides',this.value)"></div></div>`;
  if (t === "Solver") h = `<div class="grp"><h4>Port Options</h4>
     <div class="kv2"><span${asCh("setup", "delta_zo")}>Maximum Delta Zo</span><div class="u">${inum("setup", "delta_zo")}<i>%</i></div></div></div>`;
  return tabs(t, ["General", "Options", "Advanced", "Solver"], "asTab") + `<div class="asp">${h}</div>`;
}
function asSetMulti() { const s = AS(); s.mode = "multi"; if (!s.multi.length) { const e = sweepEnd(); s.multi.push({f: e > 0 ? String(+e.toFixed(6)) : "", unit: "GHz", ds: "0.02"}) } asRender(); header() }
function asSweep() {
  const t = AST.wtab, w = SW(); let h = "";
  if (t === "Edit Frequency Sweep") h = `<div class="kv2"><span${asCh("sweep", "type")}>Sweep Type</span>
     <select onchange="asSet('sweep','type',this.value)">${opts(LBL.sweep, w.type)}</select></div>
     ${chk("sweep", "q3d_dc", "Use Q3D to solve DC point")}
     <div class="grp"><h4 id="ptot"></h4><table class="ft"><tr><th>#</th><th>Distribution</th><th>Start</th><th>End</th><th></th><th></th><th></th></tr>
     ${w.rows.map((r, i) => `<tr class="${i === AST.sel ? "sel" : ""}" onclick="asSel(${i},this)"><td>${i + 1}</td>
      <td><select class="dist" onchange="asRow(${i},'dist',this.value)">${opts(LBL.dist, r.dist)}</select></td>
      <td><input value="${esc(r.start)}" placeholder="0GHz" oninput="asRow(${i},'start',this.value,1)" onchange="asRender();header()"></td>
      <td><input value="${esc(r.end)}" placeholder="20GHz" oninput="asRow(${i},'end',this.value,1)" onchange="asRender();header()"></td>
      <td class="lb">${LBL.dist[r.dist][1]}</td><td><input value="${esc(r.value)}" placeholder="${LBL.dist[r.dist][2]}" oninput="asRow(${i},'value',this.value,1)" onchange="asRender();header()"></td>
      <td><span class="pe" id="pe-${i}"></span></td></tr>`).join("")}</table>
     <div class="btnrow"><button onclick="asRowOp('above')">Add Above</button><button onclick="asRowOp('below')">Add Below</button>
      <button onclick="asRowOp('del')" ${w.rows.length > 1 ? "" : "disabled"}>Delete Selection</button></div></div>`;
  if (t === "Interpolation") h = `<div class="kv2"><span${asCh("sweep", "max_solutions")}>Max Solutions</span>${inum("sweep", "max_solutions")}</div>
     <div class="kv2"><span${asCh("sweep", "error_pct")}>Error Tolerance</span><div class="u">${inum("sweep", "error_pct")}<i>%</i></div></div>
     <div class="grp"><h4>Advanced Options</h4>${chk("sweep", "passivity", "Enforce Passivity")}
     <div class="kv2 ind"><span${asCh("sweep", "passivity_tol")}>Passivity Error Tolerance</span><input value="${esc(w.passivity_tol)}" style="width:110px" ${w.passivity ? "" : "disabled"} onchange="asSet('sweep','passivity_tol',this.value.trim())"></div>
     ${chk("sweep", "causality", "Enforce Causality (DC point required)")}</div>`;
  return tabs(t, w.type === "discrete" ? ["Edit Frequency Sweep"] : ["Edit Frequency Sweep", "Interpolation"], "asWtab") + `<div class="asp">${h}</div>`;
}
function asTab(t) { AST.stab = t; asRender() }
function asWtab(t) { AST.wtab = t; asRender() }
function asRender() {
  if (AST.sel >= SW().rows.length) AST.sel = 0;
  document.getElementById("asBody").innerHTML = `<div class="as"><div class="asbox"><div class="ash">Setup</div>${asSetup()}</div><div class="asbox"><div class="ash">Sweep</div>${asSweep()}</div></div>`;
  asPts();
}

// ============================================================================ Set HFSS Model Extents
const EX = () => C().extents, EXD = () => DF().extents;
const exCh = k => !same(EX()[k], EXD()[k]) ? ' class="c"' : "";
function exSet(k, v) { EX()[k] = v; exRender(); header() }
const exSel = k => `<select onchange="exSet('${k}',this.value)">${opts(LBL.model, EX()[k])}</select>`;
const exNum = k => `<input value="${esc(EX()[k])}" style="width:110px" onchange="exSet('${k}',this.value.trim())">`;
function exRender() {
  const x = EX();
  document.getElementById("exBody").innerHTML = `<div class="as"><div class="asbox"><div class="asp">
   <div class="grp"><h4>Dielectric</h4>
    <div class="kv2"><span${exCh("dielectric_type")}>Type</span>${exSel("dielectric_type")}</div>
    <div class="kv2"><span${exCh("dielectric_pad")}>Horizontal Padding</span>${exNum("dielectric_pad")}</div></div>
   <div class="grp"><h4>Airbox</h4>
    <div class="kv2"><span${exCh("airbox_type")}>Type</span>${exSel("airbox_type")}</div>
    <div class="kv2"><span${exCh("airbox_pad")}>Horizontal Padding</span>${exNum("airbox_pad")}</div>
    <div class="grp"><h4>Vertical</h4>
     <div class="kv2"><span${exCh("z_pos")}>Positive Padding</span><div class="u">${exNum("z_pos")}
      <label class="ck"><input type="checkbox" ${x.z_sync ? "checked" : ""} onchange="exSet('z_sync',this.checked)"><span${exCh("z_sync")}>Sync</span></label></div></div>
     ${x.z_sync ? "" : `<div class="kv2"><span${exCh("z_neg")}>Negative Padding</span>${exNum("z_neg")}</div>`}</div></div>
   </div></div>
   <div class="asbox expic"><div class="cmtop"><span class="vt">Top view</span><svg id="exTop"></svg></div>
    <div class="cm3"><span class="vt">3D view · drag = rotate, wheel = zoom, double-click = reset</span><canvas id="ex3"></canvas></div>
    <div class="exleg"><span><i style="border:1.5px dashed #34d399"></i>Cut region</span><span><i style="background:#3a3322;border:1.5px solid #fbbf24"></i>Dielectric</span>
     <span><i style="background:#17324a;border:1.5px solid #7dd3fc"></i>Airbox</span><span><i style="background:#ff4fa3"></i>Signal nets</span></div></div></div>`;
  exDraw();
}
function hull(P) { const q = [...P].sort((a, b) => a[0] - b[0] || a[1] - b[1]), cr = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lo = [], up = []; for (const p of q) { while (lo.length > 1 && cr(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p) }
  for (const p of q.reverse()) { while (up.length > 1 && cr(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p) }
  return lo.slice(0, -1).concat(up.slice(0, -1)) }
function bbx(P) { const x = P.map(p => p[0]), y = P.map(p => p[1]); return [Math.min(...x), Math.min(...y), Math.max(...x), Math.max(...y)] }
const XR = {conforming: 0, convex_hull: 1, bounding_box: 2};
function xshape(t, E) { if (t === "conforming") return E; if (t === "convex_hull") return hull(E); const [a, b, c, d] = bbx(E); return [[a, b], [c, b], [c, d], [a, d]] }
function ring(P, d, line, fill, lw, join) { const pts = P.map(p => p.join(",")).join(" ");
  return `<polygon points="${pts}" fill="${line}" stroke="${line}" stroke-width="${2 * d + lw}" stroke-linejoin="${join}"/>
   <polygon points="${pts}" fill="${fill}" stroke="${fill}" stroke-width="${Math.max(0, 2 * d - lw)}" stroke-linejoin="${join}"/>` }
let EXL = null;
function exDraw() {
  const svg = document.getElementById("exTop"); if (!svg) return;
  const E = extentPts(), g = geo(); if (!E) { svg.innerHTML = ""; EXL = null; ex3d(); return }
  const [x0, y0, x1, y1] = bbx(E), size = Math.max(x1 - x0, y1 - y0), x = EX();
  const dd = Math.max(0, +x.dielectric_pad || 0) * size, da = Math.max(0, +x.airbox_pad || 0) * size;
  const dt = x.dielectric_type, at = XR[x.airbox_type] >= XR[dt] ? x.airbox_type : dt, DB = xshape(dt, E), AB = xshape(at, E), lw = .12 * size / 40;
  const jn = k => k === "bounding_box" ? "miter" : "round", m = dd + da + size * .06;
  const c = [g.T(x0 - m, y0 - m), g.T(x1 + m, y1 + m)];
  svg.setAttribute("viewBox", [Math.min(c[0][0], c[1][0]), Math.min(c[0][1], c[1][1]), Math.abs(c[1][0] - c[0][0]), Math.abs(c[1][1] - c[0][1])].map(v => v.toFixed(3)).join(" "));
  const sig = (g.L.routed || []).map(l => (g.L.layers[l] || {}).sig ? `<path d="${g.L.layers[l].sig}" fill="#ff4fa3"/>` : "").join("");
  svg.innerHTML = `<g transform="${g.MAT}">${ring(AB, dd + da, "#7dd3fc", "#17324a", lw, jn(at))}${ring(DB, dd, "#fbbf24", "#3a3322", lw, jn(dt))}
    <g fill-rule="evenodd">${sig}</g><polygon points="${E.map(p => p.join(",")).join(" ")}" fill="none" stroke="#34d399" stroke-width="${lw * 1.5}" stroke-dasharray="${lw * 6} ${lw * 4}"/></g>`;
  EXL = {E, DB, AB, dd, da, dt, at, size, bb: [x0, y0, x1, y1]}; ex3d();
}
const VX = {yaw: -30, pitch: 55, zoom: 1}, PATHS = {};
function ex3d() {
  const cv = document.getElementById("ex3"); if (!cv) return;
  if (!cv.dataset.i) { cv.dataset.i = 1; let d = null;
    cv.addEventListener("pointerdown", e => { d = [e.clientX, e.clientY, VX.yaw, VX.pitch]; cv.setPointerCapture(e.pointerId) });
    cv.addEventListener("pointermove", e => { if (!d) return; VX.yaw = d[2] + (e.clientX - d[0]) * .4; VX.pitch = Math.max(5, Math.min(89, d[3] - (e.clientY - d[1]) * .3)); ex3d() });
    cv.addEventListener("pointerup", () => d = null);
    cv.addEventListener("wheel", e => { e.preventDefault(); VX.zoom = Math.max(.3, Math.min(8, VX.zoom * (e.deltaY < 0 ? 1.15 : 1 / 1.15))); ex3d() }, {passive: false});
    cv.addEventListener("dblclick", () => { VX.yaw = -30; VX.pitch = 55; VX.zoom = 1; ex3d() }) }
  const dpr = window.devicePixelRatio || 1, Wc = cv.clientWidth, Hc = cv.clientHeight; cv.width = Wc * dpr; cv.height = Hc * dpr;
  const g = cv.getContext("2d"); g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = "#151a22"; g.fillRect(0, 0, cv.width, cv.height);
  const L = EXL; if (!L || !Wc) return;
  const [x0, y0, x1, y1] = L.bb, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2, span = L.size + 2 * (L.dd + L.da);
  const sc = Math.min(Wc, Hc) / span * .9 * VX.zoom * dpr, ya = VX.yaw * Math.PI / 180, pa = VX.pitch * Math.PI / 180;
  const cw = Math.cos(ya), sw = Math.sin(ya), cp = Math.cos(pa), sp = Math.sin(pa), x = EX();
  const Hb = L.size * .05, pz = Math.max(0, +x.z_pos || 0), nz = Math.max(0, +(x.z_sync ? x.z_pos : x.z_neg) || 0);
  const setZ = (c, z) => c.setTransform(sc * cw, -sc * cp * sw, -sc * sw, -sc * cp * cw, cv.width / 2 - sc * (cx * cw - cy * sw), cv.height / 2 + sc * cp * (cx * sw + cy * cw) - z * sp * sc + Hb * sp * sc / 2);
  const layer = () => { const c = document.createElement("canvas"); c.width = cv.width; c.height = cv.height; return c.getContext("2d") };
  const shape = (c, P, d, join, col) => { c.beginPath(); P.forEach((q, i) => i ? c.lineTo(q[0], q[1]) : c.moveTo(q[0], q[1])); c.closePath();
    c.fillStyle = c.strokeStyle = col; c.lineJoin = join; c.fill(); if (d > 0) { c.lineWidth = 2 * d; c.stroke() } };
  const lwm = 1.3 * dpr / sc;
  function solid(P, d, join, z0, z1, side, top, edge, alpha) { const c = layer(), e = layer();
    const N = Math.max(2, Math.min(90, Math.ceil((z1 - z0) * sp * sc / 1.5)));
    for (let k = 0; k <= N; k++) { const z = z0 + (z1 - z0) * k / N; setZ(c, z); shape(c, P, d, join, k < N ? side : top) }
    for (const z of [z0, z1]) { setZ(e, z); shape(e, P, d + lwm / 2, join, edge); e.globalCompositeOperation = "destination-out"; shape(e, P, Math.max(0, d - lwm / 2), join, "#000"); e.globalCompositeOperation = "source-over" }
    g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = alpha; g.drawImage(c.canvas, 0, 0); g.globalAlpha = 1; g.drawImage(e.canvas, 0, 0) }
  const jn = k => k === "bounding_box" ? "miter" : "round", G = geo(), n = G.ORDER.length;
  solid(L.DB, L.dd, jn(L.dt), 0, Hb, "#6b5a2e", "#8a7640", "#fbbf24", .75);
  (G.L.routed || []).forEach(l => { const d = (G.L.layers[l] || {}).sig; if (!d) return; const z = Hb * (1 - G.ORDER.indexOf(l) / Math.max(1, n - 1));
    setZ(g, z); g.fillStyle = "#ff4fa3"; g.fill(PATHS[cur + l] || (PATHS[cur + l] = new Path2D(d)), "evenodd") });
  setZ(g, Hb); g.beginPath(); L.E.forEach((q, i) => i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1])); g.closePath();
  g.setLineDash([6 * lwm, 4 * lwm]); g.lineWidth = 1.5 * lwm; g.strokeStyle = "#34d399"; g.stroke(); g.setLineDash([]);
  solid(L.AB, L.dd + L.da, jn(L.at), -nz * Hb, Hb + pz * Hb, "#3b82c4", "#7dd3fc", "#7dd3fc", .22);
  g.setTransform(1, 0, 0, 1, 0, 0);
}

// ============================================================================ folder + Save
const NAME_BAD = /[<>:"\/\\|?*;\s]/;
function foldErr(n) { const v = (S.channels[n].folder || "").trim(); if (!v) return "Required"; if (NAME_BAD.test(v) || !v.replace(/\./g, "")) return 'No space or < > : " / \\ | ? * ;';
  if (v.toLowerCase() === "_work") return "Reserved name";
  if (NAMES.some(m => m !== n && (S.channels[m].folder || "").trim().toLowerCase() === v.toLowerCase())) return "Already used by another channel"; return "" }
function foldRender() {
  if (RO) return;
  document.getElementById("fold").innerHTML = `<label for="foldin">Channel folder</label>
   <input id="foldin" value="${esc(C().folder || "")}" placeholder="e.g. ${esc(cur)}" oninput="C().folder=this.value;foldMsg()">
   <span class="path" id="foldpath"></span><span class="ferr" id="folderr"></span>`; foldMsg() }
function foldMsg() { const e = foldErr(cur), i = document.getElementById("foldin"); if (!i) return; i.classList.toggle("bad", !!e);
  document.getElementById("foldpath").textContent = `→ ${D.request_folder}\\${(C().folder || "").trim() || "<folder>"}\\`;
  document.getElementById("folderr").textContent = e }
function serialize() {
  const root = document.documentElement.cloneNode(true);
  for (const id of ["svg", "layers", "cmBody", "asBody", "exBody", "nets", "tiles", "advBody", "contentBody", "chsel", "fold", "subLine", "labNets", "labType", "labExp", "expV", "msg", "extHint", "advBtn"]) { const el = root.querySelector("#" + id); if (el) el.innerHTML = "" }
  root.querySelector("#cfg-state").textContent = JSON.stringify(S).replace(/</g, "\\u003c");
  return "<!doctype html>\n" + root.outerHTML;
}
let HANDLE = null;
// 040: page opened from the tool's link -> Save goes to the tool, which overwrites the generated config.html
const LINK = location.protocol === "http:" && /^\/r\/[^/]+\/[0-9a-f]{32}\//.test(location.pathname)
  ? location.pathname.replace(/(\/r\/[^/]+\/[0-9a-f]{32}\/).*$/, "$1") : null;
let BASE = (D.built_at || "") + "|" + (S.saved_at || "");
async function saveLink(m) {
  let r;
  try {
    r = await fetch(LINK + "save", {method: "POST", headers: {"Content-Type": "application/json"},
                                    body: JSON.stringify({state: S, base_rev: BASE})});
  } catch (e) { return false }                                   // tool not reachable -> browser fallback
  let j = {}; try { j = await r.json() } catch (e) {}
  if (r.ok) { BASE = j.rev; S.saved_at = j.saved_at;
    m.innerHTML = `Saved to <b>${esc(j.path)}</b> (${new Date().toLocaleTimeString()}) — tell Claude you are done.`; return true }
  m.innerHTML = `<b style="color:var(--err)">Not saved:</b> ${esc(j.error || ("error " + r.status))}`; return true;
}
let SAVING = false;                                              // a double click must not send two saves
async function saveCfg() {
  if (RO || SAVING) return;
  SAVING = true;
  try { await saveOnce() } finally { SAVING = false }
}
async function saveOnce() {
  const bad = NAMES.filter(n => foldErr(n)), m = document.getElementById("msg");
  if (bad.length) { if (!bad.includes(cur)) { cur = bad[0]; render() } foldRender(); document.getElementById("foldin").focus();
    m.innerHTML = `<b style="color:var(--err)">Not saved:</b> fill the channel folder of ${bad.map(esc).join(", ")}.`; return }
  S.current = cur;
  let note = "";
  if (LINK) { if (await saveLink(m)) return;
    note = "Cannot reach the tool — saved with the browser instead. " }
  S.saved_at = new Date().toISOString();
  const html = serialize();
  if (window.showSaveFilePicker) {
    try {
      if (!HANDLE) HANDLE = await window.showSaveFilePicker({suggestedName: "config.html", id: "aedtcopilotcfg", types: [{description: "HTML", accept: {"text/html": [".html"]}}]});
      const w = await HANDLE.createWritable(); await w.write(html); await w.close();
      m.innerHTML = note + `Saved <b>${esc(HANDLE.name)}</b> (${new Date().toLocaleTimeString()}) — tell Claude you are done.`; return;
    } catch (e) { if (e && e.name === "AbortError") { m.textContent = "Not saved (cancelled)."; return } }
  }
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([html], {type: "text/html"})); a.download = "config.html"; document.body.appendChild(a); a.click(); a.remove();
  m.innerHTML = note + `Downloaded <b>config.html</b> — tell Claude you are done.`;
}
function resetChannel() { const f = C().folder; S.channels[cur] = clone(D.defaults[cur]); C().folder = f; render() }

// 045: inside the review page (Settings tab, srcdoc frame) the outer page owns the header, the channel choice and Save
const EMB = (() => { try { return window.frameElement != null } catch (e) { return false } })();
window.cfgState = () => { S.current = cur; return S };
window.cfgFolderErrors = () => NAMES.filter(n => foldErr(n)).map(n => [n, foldErr(n)]);
window.cfgFocusFolder = n => { if (n && n !== cur) { cur = n; render() } foldRender(); const i = document.getElementById("foldin"); if (i) i.focus() };

// ============================================================================ render
function render() { header(); contentFrame(); cutFrame(); cmRender(); asRender(); exRender(); foldRender();
  const m = document.getElementById("msg"); if (m && !m.innerHTML) m.innerHTML = RO || EMB ? "" : LINK ? `Check every frame, then Save: it writes <span style="font-family:var(--mono)">${esc(D.request_folder)}\\config.html</span> directly. Tell Claude you are done.` : `Check every frame, then Save as <b>config.html</b> in <span style="font-family:var(--mono)">${esc(D.request_folder)}</span> and tell Claude you are done.` }
render();
