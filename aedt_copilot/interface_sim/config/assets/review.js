"use strict";
// 045 review page (approved mock specs/045-review-resolve-page/mock). Data = cfg-data (config data + review per
// channel), state = cfg-state (config settings + review resolutions). Settings tab = the 038 config page in a frame.
const D = JSON.parse(document.getElementById("cfg-data").textContent);
const ST = JSON.parse(document.getElementById("cfg-state").textContent);
const NAMES = Object.keys(D.channels);
const CH = NAMES.map(n => { const c = D.channels[n], r = (D.review || {})[n] || {};
  return {name: n, comp_a: (c.content || {}).comp_a, comp_b: (c.content || {}).comp_b, layers: c.layers, comps: c.comps || [],
          extents: c.extents || {}, points: r.points || [], sections: r.sections || {}, topo: r.topo || "",
          stackup: r.stackup || c.stackup || [], measured_at: r.measured_at || "", review_html: r.review_html || ""} });
ST.review = Object.fromEntries(CH.map(c => { const r = (ST.review || {})[c.name];   // resolutions count only for the current review
  return [c.name, r && r.measured_at === c.measured_at && r.resolved ? r : {measured_at: c.measured_at, resolved: {}}] }));
const S = {ch: Math.max(0, NAMES.indexOf(ST.current)), unit: "mil", sel: null, view: "review", wv: "board"};
try { const u = localStorage.getItem("rv_unit"); if (u) S.unit = u } catch (e) {}
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const RES = i => ST.review[CH[i].name].resolved;
const isRes = (i, id) => !!RES(i)[id];
const FAMCOL = {ref: "var(--c-ref)", via: "var(--c-via)", rt: "var(--c-rt)", stk: "var(--c-stk)", ts: "var(--c-ts)"};
// 043 frame style per issue (colour, dash pattern in mm)
const FRAME = {"Loss of reference": ["#e83e8c", "0.12 0.06"], "Near plane edge": ["#fd7e14", "0.02 0.05"], "Signal over void (SOV)": ["#6f42c1", "0.15 0.05 0.03 0.05"],
  "Reference to another net": ["#8b5a2b", "0.25 0.08"], "Trace over via clearance": ["#0d9488", "0.05 0.05"], "Via stub": ["#38bdf8", "0.1 0.05"], "Serpentine": ["#f59e0b", "0.2 0.06"]};

// ---------------------------------------------------------------- units (lengths in text: "x mm")
function fmtMM(mm, d) { if (S.unit === "mil") return (mm / 0.0254).toFixed(d ?? 2) + " mil"; if (S.unit === "um") return (mm * 1000).toFixed(d ?? 1) + " µm"; return mm.toFixed(d ?? 3) + " mm" }
const U = t => esc(t).replace(/(-?\d+(?:\.\d+)?) mm\b/g, (_, v) => fmtMM(parseFloat(v)));
const XY = (x, y) => S.unit === "mm" ? `(${x.toFixed(3)}, ${y.toFixed(3)}) mm` : `(${fmtMM(x).split(" ")[0]}, ${fmtMM(y).split(" ")[0]}) ${S.unit === "um" ? "µm" : "mil"}`;
const UF = {mil: [1 / 0.0000254, 1, "mil"], um: [1e6, 0, "µm"], mm: [1e3, 3, "mm"]};
function units(root) { const f = UF[S.unit] || UF.mil;   // report rows: <span data-m="metres"> (data-n = number only)
  root.querySelectorAll("[data-m]").forEach(e => { e.textContent = (e.dataset.k || "") + (+e.dataset.m * f[0]).toFixed(f[1]) + (e.dataset.n ? "" : " " + f[2]) });
  root.querySelectorAll(".uu").forEach(e => e.textContent = f[2]) }

// ---------------------------------------------------------------- settings state (frame when open, else the page state)
const FR = () => { const f = $("stFrame"); try { return f.dataset.ready && f.contentWindow.cfgState ? f.contentWindow : null } catch (e) { return null } };
function cfgState() { const w = FR(); return w ? w.cfgState() : ST }
function cutOf(i) {   // cut region of the channel for the CURRENT settings (type + expansion of the Settings tab)
  const c = (cfgState().channels[CH[i].name] || {}).cut || {}, E = CH[i].extents || {};
  const f = parseFloat(c["cutout.expansion"]); if (!(f > 0)) return [null, ""];
  return [(E[c["cutout.extent_type"]] || {})[f.toFixed(2)] || null, `${c["cutout.extent_type"]} ${c["cutout.expansion"]}`] }

// ---------------------------------------------------------------- board view (same drawing as the config page)
const AEDT = ["#00ffff", "#b8860b", "#87cefa", "#00c060", "#9370db", "#00ffff", "#800080", "#ff00ff", "#808000", "#ffff00", "#808080", "#ffffff", "#800080", "#008080", "#c0c0c0", "#ff8c00"];
const COL = {sig: "#ff4fa3", gnd: "#3b82f6", oth: "#9aa0a6"};
const GEO = {};
const DC = () => CH[S.ch];
function geo() {
  if (GEO[S.ch]) return GEO[S.ch];
  const L = DC().layers || {box: [0, 0, 10, 10], order: [], routed: [], layers: {}};
  const BB = L.box, PADV = 1, W0 = BB[2] - BB[0], H0 = BB[3] - BB[1], ROT = H0 > W0;
  const VW = (ROT ? H0 : W0) + 2 * PADV, VH = (ROT ? W0 : H0) + 2 * PADV, SC = Math.max(VW, VH) / 120;
  const MAT = ROT ? `matrix(0,1,1,0,${PADV - BB[1]},${PADV - BB[0]})` : `matrix(1,0,0,-1,${PADV - BB[0]},${BB[3] + PADV})`;
  const T = (x, y) => ROT ? [y - BB[1] + PADV, x - BB[0] + PADV] : [x - BB[0] + PADV, BB[3] - y + PADV];
  const ORDER = L.order || [];
  return GEO[S.ch] = {L, BB, ROT, VW, VH, SC, MAT, T, ORDER, LC: Object.fromEntries(ORDER.map((l, i) => [l, AEDT[i % AEDT.length]])),
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
const clampUV = (g, u, v) => [Math.min(g.VW - .2, Math.max(.2, u)), Math.min(g.VH - .2, Math.max(.2, v))];   // point outside the area: at the edge
const PUV = (g, p) => clampUV(g, ...g.T(p.x, p.y));
function frames(g) {   // fault frames of the selected point, one style per issue (043)
  if (S.sel == null) return "";
  const p = DC().points[S.sel], [u, v] = PUV(g, p);
  return p.items.map((it, k) => { const [c, dash] = FRAME[it.check] || ["#fff", "0.1 0.05"], h = .7 + k * .12;
    return `<rect x="${u - h}" y="${v - h}" width="${2 * h}" height="${2 * h}" fill="none" stroke="${c}" stroke-width=".05" stroke-dasharray="${dash}"/>` }).join("");
}
function draw() {
  const g = geo(), svg = $("svg"), [E] = cutOf(S.ch);
  zoomInit(svg); setVB();
  svg.innerHTML = `<g transform="${g.MAT}">${copper(g)}${E ? `<polygon points="${E.map(p => p.join(",")).join(" ")}" fill="#34d399" fill-opacity=".06" stroke="#34d399" stroke-width="${.25 * g.SC}" stroke-dasharray="${g.SC} ${.6 * g.SC}"/>` : ""}</g>${compBoxes(g)}${frames(g)}`;
  layerPanel(g); marks();
}
function setVB() { const g = geo(); if (!g.VB) g.VB = [0, 0, g.VW, g.VH]; $("svg").setAttribute("viewBox", g.VB.map(v => v.toFixed(4)).join(" "));
  $("zlev").textContent = Math.round(g.VW / g.VB[2] * 100) + " %"; marks() }
function zoomAt(k, cx, cy) { const g = geo(), w = Math.min(g.VW * 1.5, Math.max(g.VW / 2000, g.VB[2] * k)), h = w * g.VH / g.VW;
  g.VB = [cx - (cx - g.VB[0]) * w / g.VB[2], cy - (cy - g.VB[1]) * h / g.VB[3], w, h]; setVB() }
function zoomBtn(k) { const g = geo(); zoomAt(k, g.VB[0] + g.VB[2] / 2, g.VB[1] + g.VB[3] / 2) }
function zoomFit() { const g = geo(); g.VB = [0, 0, g.VW, g.VH]; setVB() }
function zoomTo(u, v, w) { const g = geo(), h = w * g.VH / g.VW; g.VB = [u - w / 2, v - h / 2, w, h]; setVB() }
function zoomInit(svg) {
  if (svg.dataset.z) return; svg.dataset.z = 1; svg.style.cursor = "grab";
  const pt = e => { const g = geo(), r = svg.getBoundingClientRect(), s = Math.max(g.VB[2] / r.width, g.VB[3] / r.height),
    ox = (r.width - g.VB[2] / s) / 2, oy = (r.height - g.VB[3] / s) / 2; return [g.VB[0] + (e.clientX - r.left - ox) * s, g.VB[1] + (e.clientY - r.top - oy) * s, s] };
  svg.addEventListener("wheel", e => { e.preventDefault(); const [x, y] = pt(e); zoomAt(e.deltaY < 0 ? 1 / 1.25 : 1.25, x, y) }, {passive: false});
  let drag = null;
  svg.addEventListener("pointerdown", e => { const g = geo(); drag = [e.clientX, e.clientY, g.VB[0], g.VB[1], pt(e)[2]]; svg.setPointerCapture(e.pointerId); svg.style.cursor = "grabbing" });
  svg.addEventListener("pointermove", e => { if (!drag) return; const g = geo(); g.VB[0] = drag[2] - (e.clientX - drag[0]) * drag[4]; g.VB[1] = drag[3] - (e.clientY - drag[1]) * drag[4]; setVB() });
  svg.addEventListener("pointerup", () => { drag = null; svg.style.cursor = "grab" });
  svg.addEventListener("dblclick", e => { e.preventDefault(); zoomFit() });   // double-click = whole cut area (as the config page)
}
// markers: HTML flags over the svg; points closer than 28 px on screen are grouped (click = zoom in)
function scr(u, v) { const svg = $("svg"), m = svg.getScreenCTM(), r = $("marks").getBoundingClientRect(), p = svg.createSVGPoint(); p.x = u; p.y = v; const q = p.matrixTransform(m); return [q.x - r.left, q.y - r.top] }
function marks() {
  const g = geo(), box = $("marks"); if (!box || !$("svg").getScreenCTM()) return;
  const P = DC().points.map((p, i) => { const [u, v] = PUV(g, p), [x, y] = scr(u, v); return {i, p, u, v, x, y} });
  const groups = [];
  for (const q of P) { const gp = groups.find(G => Math.hypot(G[0].x - q.x, G[0].y - q.y) < 28); gp ? gp.push(q) : groups.push([q]) }
  const W = box.clientWidth, H = box.clientHeight;
  box.innerHTML = groups.filter(G => G[0].x > -20 && G[0].x < W + 20 && G[0].y > -20 && G[0].y < H + 40).map(G => {
    if (G.length === 1 || G.some(q => q.i === S.sel)) return G.map(q => flag(q)).join("");
    const done = G.every(q => isRes(S.ch, q.p.id));
    return `<div class="mk grp ${done ? "res" : ""}" data-g="${G.map(q => q.i).join(",")}" style="left:${G[0].x}px;top:${G[0].y}px"><div class="flag">${G.length} points</div><div class="tail"></div><div class="pt"></div></div>` }).join("");
}
function flag(q) { const done = isRes(S.ch, q.p.id), f = q.p.items[0]?.fam || "rt";
  return `<div class="mk ${done ? "res" : ""} ${S.sel === q.i ? "sel" : ""}" data-i="${q.i}" style="left:${q.x}px;top:${q.y}px"><div class="flag" style="background:${FAMCOL[f]}">${esc(q.p.id)}${q.p.items.length > 1 ? " ×" + q.p.items.length : ""}</div><div class="tail"></div><div class="pt"></div></div>` }

// ---------------------------------------------------------------- layer panel = config Layers table + stackup
function layerPanel(g) {
  const st = DC().stackup || [], inv = S.sel != null ? DC().points[S.sel].inv : [];
  const th = n => { const r = st.find(x => x.name === n); return r ? fmtMM(r.thickness_um / 1000, S.unit === "mm" ? 3 : 1) : "" };
  let rows = "";
  g.ORDER.forEach((l, i) => {
    rows += `<tr class="${l === g.ACT ? "act" : ""} ${(g.L.routed || []).includes(l) ? "routed" : ""} ${inv.includes(l) ? "inv" : ""}">
      <td><input type="radio" name="act" ${l === g.ACT ? "checked" : ""} onchange="layAct(${i})"></td>
      <td class="n">${esc(l)}</td><td class="th">${th(l)}</td><td><span class="lsw" style="background:${g.LC[l]}"></span></td>
      <td><input type="checkbox" ${g.ON[l] ? "checked" : ""} onchange="layOn(${i},this.checked)"></td></tr>`;
    const k = st.findIndex(x => x.name === l), d = k >= 0 ? st[k + 1] : null;
    if (d && d.type === "dielectric") rows += `<tr class="di"><td colspan="5">${esc(d.material)} · ${fmtMM(d.thickness_um / 1000, S.unit === "mm" ? 3 : 1)}</td></tr>`;
  });
  $("layers").innerHTML = `<h4>Layers / stackup</h4><div class="scroll"><table><tr><th>Active</th><th style="text-align:left">Layer</th><th>Thick.</th><th></th><th>Visible</th></tr>
    <tr class="all"><td></td><td class="n"><b>All layers</b></td><td></td><td></td><td><input type="checkbox" ${g.ORDER.every(l => g.ON[l]) ? "checked" : ""} onchange="layAll(this.checked)"></td></tr>${rows}</table></div>
    <div class="btns"><button onclick="layPreset('all')">All</button><button onclick="layPreset('routed')">Routed</button><button onclick="layPreset('active')">Active</button></div>
    <div style="font-size:11px;margin-top:6px">• = routed layer of the channel · yellow = layers of the selected point</div>`;
}
function layAll(v) { const g = geo(); g.ORDER.forEach(l => g.ON[l] = v); draw() }
function layAct(i) { const g = geo(); g.ACT = g.ORDER[i]; g.ON[g.ACT] = true; draw() }
function layOn(i, v) { const g = geo(); g.ON[g.ORDER[i]] = v; draw() }
function layPreset(p) { const g = geo(); g.ORDER.forEach(l => g.ON[l] = p === "all" || (p === "routed" ? (g.L.routed || []).includes(l) : l === g.ACT)); draw() }

// ---------------------------------------------------------------- side panel: list / detail
const CAM = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:block;flex:none"><path d="M4 7h3l2-3h6l2 3h3a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1z"/><circle cx="12" cy="13" r="4"/></svg>`;
function side() {
  const ch = DC(), left = ch.points.filter(p => !isRes(S.ch, p.id)).length;
  if (S.sel == null) {
    if (!ch.points.length) { $("side").innerHTML = `<div class="shead"><span class="g">${esc(ch.name)}</span></div><div style="padding:14px;font-size:13px">No NOT OK point in the layout review of this channel: its Settings tab is open.<br><br>Review report: <span style="font-family:var(--mono);font-size:11.5px">${esc(ch.review_html)}</span></div>`; return }
    $("side").innerHTML = `<div class="shead"><span class="g">${ch.points.length} NOT OK points · ${esc(ch.name)}</span>${left ? `<button class="btn sm okb" data-a="all">Resolve all</button>` : ""}</div><ul class="plist">` +
      ch.points.map((p, i) => { const done = isRes(S.ch, p.id);
        return `<li data-i="${i}"><span class="pid" style="background:${done ? "var(--ok)" : FAMCOL[p.items[0]?.fam]}">${esc(p.id)}</span>
          <div class="pl2">${p.items.map(x => esc(x.check)).join(" + ")}<div class="m">${(p.rep || []).map(r => esc(r.rid)).join(", ")} · ${esc(p.net)} · ${esc(p.act || "")}</div></div>
          <span class="st ${done ? "yes" : "no"}">${done ? "Resolved" : "NOT OK"}</span></li>` }).join("") + `</ul>
      <div style="padding:6px 14px 14px;font-size:12px">Point to a marker to see what it is; click it (or a row) for the details and Resolve.
      The Settings tab of this channel unlocks when every point is resolved.</div>`;
    return;
  }
  const p = ch.points[S.sel], r = RES(S.ch)[p.id];
  let h = `<div class="shead"><button class="btn sm" data-a="back">← All points</button><span class="g"></span>
    <button class="btn sm" data-a="prev">‹</button><span style="font-weight:400">${S.sel + 1} / ${ch.points.length}</span><button class="btn sm" data-a="next">›</button></div>
    <div class="det rp"><h3><span class="pid" style="background:${r ? "var(--ok)" : FAMCOL[p.items[0]?.fam]}">${esc(p.id)}</span>${r ? "Resolved" : "NOT OK"}<button class="btn sm" data-a="png" style="margin-left:auto;font-size:13px;font-weight:600;display:inline-flex;align-items:center;gap:6px;line-height:1" title="PNG: overview of the cut area with the issue circled + zoom at the issue">${CAM}<span>Print issue to image</span></button></h3>
    <div class="loc">Net <b>${esc(p.net)}</b> · ${XY(p.x, p.y)} · ${esc(p.items.map(i => i.layer).filter((v, k, a) => a.indexOf(v) === k).join(", "))}</div>`;
  for (const rw of (p.rep || [])) {   // the old report row(s) of this point: section, Issue / Recommendation, picture with the measured values
    const sec = (ch.sections || {})[rw.sec] || "";
    h += `<div class="rsec"><div class="sh"><span class="g">${esc(rw.sec)}</span><span class="rid">${esc(rw.rid)}</span><b class="nok">NOT OK</b></div>
      ${sec ? `<details class="chk"><summary>What this section checks</summary>${sec}</details>` : ""}
      <div class="bd">${rw.desc}${p.items.filter(it => it.value && it.fam !== "rt").map(it => `<div class="mv">${esc(it.check)}: ${U(it.value)}</div>`).join("")}<div class="pic2">${rw.pic}</div></div></div>`;
  }
  if (!(p.rep || []).length) for (const it of p.items) h += `<div class="rsec"><div class="sh"><span class="g">${esc(it.check)}</span><b class="nok">NOT OK</b></div>
      <div class="bd"><div class="iss2"><div><b>Issue:</b> ${U(it.issue)}</div>${it.rec ? `<div><b>Recommendation:</b> ${U(it.rec)}</div>` : ""}</div><div class="mv">${U(it.value)}</div></div></div>`;
  h += `<div class="xs"><div class="cap">Cross-section at ${esc(p.id)} · board stackup to scale</div>${xsec(p)}</div>`;
  h += r ? `<div class="rnote">✓ Resolved ${esc(r.time)}${r.note ? ` — “${esc(r.note)}”` : ""}${r.carried ? " (carried over from the previous review: Save to confirm)" : ""}</div><div class="acts"><button class="btn sm" data-a="unres">Unresolve</button></div>`
         : `<textarea class="note" id="note" placeholder="Note (optional): why this point can be ignored"></textarea>
            <div class="acts"><button class="btn okb" data-a="res">✓ Resolve — accept this NOT OK</button></div>`;
  $("side").innerHTML = h + `</div>`;
  units($("side"));
}
function xsec(p) {   // stackup at the point: real thicknesses (copper min 3 px), layers of the point highlighted
  const st = DC().stackup || [], g = geo(); if (!st.length) return "<i>no stackup</i>";
  const K = .14, W = 330, X0 = 92, X1 = W - 6, ys = {};
  let y = 4, s = "";
  for (const L of st) { const hgt = Math.max(L.type === "dielectric" ? 2 : 3, L.thickness_um * K), inv = p.inv.includes(L.name);
    if (L.type === "dielectric") s += `<rect x="${X0}" y="${y}" width="${X1 - X0}" height="${hgt}" fill="#e8dcbc" opacity=".6"/>`;
    else { ys[L.name] = [y, y + hgt]; s += `<rect x="${X0}" y="${y}" width="${X1 - X0}" height="${hgt}" fill="${inv ? (g.LC[L.name] || "#888") : "#b9c0ca"}" stroke="${inv ? "#000" : "none"}" stroke-width=".6"/>
      <text x="${X0 - 4}" y="${y + hgt / 2 + 3.3}" text-anchor="end" font-size="9" font-weight="${inv ? 700 : 400}" fill="${inv ? "#000" : "#777"}">${esc(L.name)}</text>` }
    y += hgt }
  const cx = (X0 + X1) / 2, metal = st.filter(L => L.type !== "dielectric").map(L => L.name);
  for (const it of p.items) {
    if (it.fam === "via") { const [a, b] = (it.layer.includes(" → ") ? it.layer.split(" → ") : [metal[0], metal[metal.length - 1]]), u = it.used[it.used.length - 1];
      if (!ys[a] || !ys[b]) continue;
      const y0 = ys[a][0], y1 = ys[b][1], yu = ys[u] ? ys[u][1] : y1;
      s += `<rect x="${cx - 7}" y="${y0}" width="14" height="${yu - y0}" fill="#475569"/><rect x="${cx - 7}" y="${yu}" width="14" height="${y1 - yu}" fill="#fecaca" stroke="#dc2626" stroke-dasharray="3 2"/>
        <text x="${cx + 12}" y="${(yu + y1) / 2 + 3}" font-size="10" font-weight="700" fill="#dc2626">stub ${U((it.value.match(/stub ([\d.]+) mm/) || [, "0"])[1] + " mm")}</text>
        <text x="${cx + 12}" y="${(y0 + yu) / 2 + 3}" font-size="9" fill="#334155">used ${esc(it.used.join(" → "))}</text>`; continue }
    const sl = it.layer; if (!ys[sl]) continue;
    const [t0, t1] = ys[sl]; s += `<rect x="${cx - 22}" y="${t0 - 1}" width="16" height="${t1 - t0 + 2}" fill="#000"/><rect x="${cx + 6}" y="${t0 - 1}" width="16" height="${t1 - t0 + 2}" fill="#000"/>`;
    for (const rp of (it.ref || "").split(",").map(x => x.trim()).filter(x => ys[x])) { const [r0, r1] = ys[rp], [c] = FRAME[it.check] || ["#e83e8c"];
      if (it.check === "Near plane edge") s += `<rect x="${cx + 34}" y="${r0 - 1}" width="${X1 - cx - 34}" height="${r1 - r0 + 2}" fill="#fff" stroke="${c}" stroke-dasharray="1.5 2"/><text x="${cx + 38}" y="${r1 + 9}" font-size="8.5" fill="${c}">plane edge</text>`;
      else s += `<rect x="${cx - 40}" y="${r0 - 1}" width="80" height="${r1 - r0 + 2}" fill="#fff" stroke="${c}" stroke-dasharray="4 2"/><text x="${cx}" y="${r1 + 9}" text-anchor="middle" font-size="8.5" fill="${c}">no GND (${esc(rp)})</text>` }
  }
  return `<svg width="100%" viewBox="0 0 ${W} ${y + 6}">${s}</svg>`;
}

// ---------------------------------------------------------------- Print issue to image: PNG = header + overview (issue circled) | zoom at the issue
function svgImage(vb, extra, w, h) {   // the board picture (current layers) rendered with another viewBox
  const sv = $("svg").cloneNode(true), bg = getComputedStyle($("svg")).backgroundColor || "#151a22";
  sv.setAttribute("xmlns", "http://www.w3.org/2000/svg"); sv.setAttribute("viewBox", vb.join(" ")); sv.setAttribute("width", w); sv.setAttribute("height", h);
  sv.setAttribute("preserveAspectRatio", "xMidYMid meet"); sv.removeAttribute("style");
  sv.insertAdjacentHTML("afterbegin", `<rect x="${vb[0] - vb[2]}" y="${vb[1] - vb[3]}" width="${3 * vb[2]}" height="${3 * vb[3]}" fill="${bg}"/>`);
  sv.insertAdjacentHTML("beforeend", extra);
  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(sv)], {type: "image/svg+xml"}));
  return new Promise((ok, bad) => { const im = new Image(); im.onload = () => { URL.revokeObjectURL(url); ok(im) }; im.onerror = bad; im.src = url });
}
async function issuePng() {
  const g = geo(), ch = DC(), p = ch.points[S.sel], [u, v] = PUV(g, p);
  const PW = 900, PH = 680, GAP = 24, M = 24, ZW = 6;
  // overview: whole cut area, issue circled (no point id); the zoom area shown as a dashed box; arrow circle -> zoom
  const ov = [0, 0, g.VW, g.VH], s = Math.max(g.VW / PW, g.VH / PH), R = Math.max(1.2, 26 * s);
  const zh = ZW * PH / PW;
  const ovx = `<rect x="${u - ZW / 2}" y="${v - zh / 2}" width="${ZW}" height="${zh}" fill="none" stroke="#fde047" stroke-width="${1.5 * s}" stroke-dasharray="${6 * s} ${4 * s}"/>
    <circle cx="${u}" cy="${v}" r="${R}" fill="none" stroke="#ff2d55" stroke-width="${4 * s}"/>`;
  // zoom: point in the middle, same frames as the page (043 styles), no point id
  const zv = [u - ZW / 2, v - zh / 2, ZW, zh], zs = ZW / PW;
  const zx = `<circle cx="${u}" cy="${v}" r="${4 * zs}" fill="#fff" stroke="#000" stroke-width="${1.5 * zs}"/>`;
  const [a, b] = await Promise.all([svgImage(ov, ovx, PW, PH), svgImage(zv, zx, PW, PH)]);
  // header (user template 2026-11-17): Issue / Layout version / Issue description - labels bold, all text black
  const F = "Segoe UI, Arial", LS = 15, LH = 22, LW = 2 * PW + GAP, KEYW = 150;
  const desc = p.items.map(i => i.issue).join(" ").replace(/(-?\d+(?:\.\d+)?) mm\b/g, (_, x) => fmtMM(parseFloat(x)))
    + ` Channel ${ch.name} (${ch.comp_a} → ${ch.comp_b}), location ${XY(p.x, p.y)}.`;
  const rows = [["Issue:", `${p.items.map(i => i.check).join(" + ")}`], ["Layout version:", D.board_name], ["Issue description:", desc]];
  const cv = document.createElement("canvas"), c = cv.getContext("2d");
  const wrap = (txt, w) => { c.font = `${LS}px ${F}`; const out = []; let ln = "";
    for (const wd of txt.split(/\s+/)) { const tr = ln ? ln + " " + wd : wd; if (c.measureText(tr).width > w && ln) { out.push(ln); ln = wd } else ln = tr }
    return ln ? [...out, ln] : out };
  const lines = rows.map(([k, t]) => [k, wrap(t, LW - KEYW)]);
  const HEAD = lines.reduce((n, [, l]) => n + l.length, 0) * LH + 14;
  cv.width = 2 * PW + GAP + 2 * M; cv.height = HEAD + PH + 2 * M + 30;
  c.fillStyle = "#fff"; c.fillRect(0, 0, cv.width, cv.height); c.fillStyle = "#000"; c.textBaseline = "alphabetic";
  let ty0 = M + LS;
  for (const [k, l] of lines) {
    c.font = `700 ${LS}px ${F}`; c.fillText(k, M, ty0);
    c.font = `${LS}px ${F}`; l.forEach((t, n) => c.fillText(t, M + KEYW, ty0 + n * LH));
    ty0 += l.length * LH;
  }
  const y0 = HEAD + M;
  c.drawImage(a, M, y0); c.drawImage(b, M + PW + GAP, y0);
  c.strokeStyle = "#999"; c.lineWidth = 1; c.strokeRect(M + .5, y0 + .5, PW, PH); c.strokeRect(M + PW + GAP + .5, y0 + .5, PW, PH);
  c.fillStyle = "#000"; c.font = "700 16px Segoe UI, Arial";
  c.textAlign = "center";   // captions centred under each picture
  c.fillText("Overview", M + PW / 2, y0 + PH + 22);
  c.fillText("Zoom in", M + PW + GAP + PW / 2, y0 + PH + 22);
  c.textAlign = "left";
  // arrow: from the circle (overview) to the edge of the zoom picture
  const k = 1 / s, cx = M + (PW - g.VW * k) / 2 + u * k, cy = y0 + (PH - g.VH * k) / 2 + v * k, rr = R * k + 3;
  const tx = M + PW + GAP - 2, ty = y0 + PH / 2, an = Math.atan2(ty - cy, tx - cx);
  const sx = cx + rr * Math.cos(an), sy = cy + rr * Math.sin(an), HL = 18;
  c.save(); c.strokeStyle = c.fillStyle = "#ff2d55"; c.lineWidth = 4; c.lineCap = "round"; c.shadowColor = "#000"; c.shadowBlur = 3;
  c.beginPath(); c.moveTo(sx, sy); c.lineTo(tx - HL * .8 * Math.cos(an), ty - HL * .8 * Math.sin(an)); c.stroke();
  c.beginPath(); c.moveTo(tx, ty); c.lineTo(tx - HL * Math.cos(an - .45), ty - HL * Math.sin(an - .45));
  c.lineTo(tx - HL * Math.cos(an + .45), ty - HL * Math.sin(an + .45)); c.closePath(); c.fill(); c.restore();
  // scale bar on the zoom (1 mm)
  const px = PW / ZW, bx = M + PW + GAP + 20, by = y0 + PH - 22;
  c.fillStyle = "#ffffffdd"; c.fillRect(bx - 8, by - 24, px + 16, 34); c.fillStyle = "#000"; c.fillRect(bx, by, px, 5);
  c.font = "13px Segoe UI, Arial"; c.fillText(fmtMM(1, 1), bx, by - 8);
  const link = document.createElement("a"); link.download = `${ch.name}_${p.id}_issue.png`; link.href = cv.toDataURL("image/png");
  document.body.appendChild(link); link.click(); link.remove();
  return {w: cv.width, h: cv.height, name: link.download};
}

// ---------------------------------------------------------------- header / counters / actions
function counts() { let n = 0, d = 0; const per = []; CH.forEach((c, i) => { const k = c.points.filter(p => isRes(i, p.id)).length; n += c.points.length; d += k; per.push([c.name, c.points.length - k]) }); return {n, d, per} }
const leftOf = i => CH[i].points.filter(p => !isRes(i, p.id)).length;
let DIRTY = false;
function header() {
  const ch = DC(), lft = leftOf(S.ch), locked = lft > 0;
  if (locked && S.view === "settings") S.view = "review";
  $("subLine").innerHTML = `Request <b>${esc(D.request_id)}</b> · Board <b>${esc(D.board_name)}</b>`;
  const [, lab] = cutOf(S.ch);
  $("hint").textContent = S.view === "review" ? `${ch.comp_a} → ${ch.comp_b} · cut region ${lab} · review ${String(ch.measured_at).replace("T", " ")} · board data = layout snapshot`
    : `${ch.comp_a} → ${ch.comp_b} · cut configuration`;
  $("chsel").innerHTML = CH.map((c, i) => { const k = c.points.length - leftOf(i);
    return `<button class="${i === S.ch ? "on" : ""}" onclick="setCh(${i})">${esc(c.name)} <span class="pid" style="background:${k === c.points.length ? "var(--ok)" : "var(--err)"}">${k}/${c.points.length}</span></button>` }).join("");
  [...$("units").children].forEach(b => b.classList.toggle("on", b.dataset.u === S.unit));
  // tabs of the channel: Review layout | Settings (locked until every NOT OK point of the channel is resolved)
  $("tbCount").textContent = `${ch.points.length - lft}/${ch.points.length}`; $("tbCount").style.background = locked ? "var(--err)" : "var(--ok)";
  const tb = $("vtabs").querySelector("[data-v=settings]");
  tb.disabled = locked; tb.style.opacity = locked ? .55 : 1; tb.style.cursor = locked ? "not-allowed" : "pointer";
  tb.title = locked ? `Locked: resolve the ${lft} NOT OK point(s) of ${ch.name} first` : "";
  $("tbLock").textContent = locked ? "🔒" : "";
  $("vtabs").querySelectorAll("[data-v]").forEach(b => b.classList.toggle("on", b.dataset.v === S.view));
  $("paneReview").classList.toggle("on", S.view === "review"); $("paneSettings").classList.toggle("on", S.view === "settings");
  const {n, d, per} = counts();
  $("count").textContent = `Resolved ${d} / ${n}`; $("count").className = "cnt" + (d === n ? " done" : "");
  $("save").disabled = d !== n || SAVING; $("resAll").disabled = d === n;
  if (!MSG) $("msg").textContent = d === n ? "All NOT OK points resolved — check the Settings tab of each channel, Save, then tell Claude “xong”."
    : locked ? `Settings of ${ch.name} unlock when its ${lft} NOT OK point(s) are resolved. Save unlocks when every point is resolved.` : "Save unlocks when every NOT OK point of every channel is resolved.";
  $("why").className = "why" + (d !== n ? " show" : "");
  $("why").innerHTML = "Resolve every NOT OK point first:<br>" + per.filter(p => p[1]).map(p => `• ${esc(p[0])}: ${p[1]} left`).join("<br>");
}
let MSG = "";
function say(h) { MSG = h; $("msg").innerHTML = h }
function render() { header(); if (S.view === "review") { side(); draw(); topo() } else settings() }
function topo() {
  const box = $("topo"), ch = DC(); box.classList.toggle("on", S.wv === "topo");
  $("vsw").querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.w === (S.wv || "board")));
  if (box.dataset.ch === String(S.ch) && box.dataset.u === S.unit) return;
  box.dataset.ch = S.ch; box.dataset.u = S.unit;
  box.innerHTML = ch.topo || "<i>No routing data in the review report.</i>"; units(box);
  box.querySelectorAll("svg.tv").forEach(sv => {   // zoom lock per top view, as the review report
    const v0 = sv.getAttribute("viewBox").split(" ").map(Number); let v = v0.slice(), drag = null, lock = true;
    const bt = document.createElement("button"); bt.type = "button"; bt.className = "zb";
    const show = () => { bt.textContent = lock ? "Zoom locked (click to unlock)" : "Zoom unlocked (click to lock)"; bt.classList.toggle("on", !lock); sv.style.cursor = lock ? "default" : "crosshair" };
    bt.onclick = () => { lock = !lock; show() }; show(); sv.parentElement.insertBefore(bt, sv);
    const set = () => { sv.setAttribute("viewBox", v.join(" ")); const k = v[2] / v0[2]; sv.querySelectorAll("text[data-fs]").forEach(t => t.setAttribute("font-size", t.dataset.fs * k)) };
    const pt = e => { const r = sv.getBoundingClientRect(), s = Math.max(v[2] / r.width, v[3] / r.height), ox = (r.width - v[2] / s) / 2, oy = (r.height - v[3] / s) / 2; return [v[0] + (e.clientX - r.left - ox) * s, v[1] + (e.clientY - r.top - oy) * s, s] };
    sv.addEventListener("wheel", e => { if (lock) return; e.preventDefault(); const [x, y] = pt(e), k = e.deltaY < 0 ? .8 : 1.25; v = [x - (x - v[0]) * k, y - (y - v[1]) * k, v[2] * k, v[3] * k]; set() }, {passive: false});
    sv.addEventListener("mousedown", e => { if (lock) return; drag = [e.clientX, e.clientY, v.slice()]; e.preventDefault() });
    window.addEventListener("mousemove", e => { if (!drag) return; const s = pt(e)[2]; v = [drag[2][0] - (e.clientX - drag[0]) * s, drag[2][1] - (e.clientY - drag[1]) * s, v[2], v[3]]; set() });
    window.addEventListener("mouseup", () => drag = null);
    sv.addEventListener("dblclick", () => { if (lock) return; v = v0.slice(); set() }) });
}
$("vsw").addEventListener("click", e => { const w = e.target.dataset.w; if (!w) return; S.wv = w; topo() });
function setCh(i) { S.ch = i; S.sel = null; ST.current = NAMES[i]; render() }
function setView(v) { if (v === "settings" && leftOf(S.ch)) return; S.view = v; render() }
// Settings tab = the 038 config page of the request in a frame (built from the template block + this page's data / state)
function settings() {
  const f = $("stFrame");
  if (!f.dataset.on) { f.dataset.on = 1;
    const cfgD = Object.assign({}, D); delete cfgD.review; delete cfgD.kind;
    const js = o => JSON.stringify(o).replace(/</g, "\\u003c");
    const src = $("cfg-page").textContent.replaceAll("</scr@@ipt", "<\/script").replaceAll('id="cfg@@-', 'id="cfg-')
      .replace("__DATA__", () => js(cfgD)).replace("__STATE__", () => js(Object.assign({}, ST, {current: NAMES[S.ch]})))
      .replace("</head>", "<style>.top,.ro-banner,.foot .btn,.foot .msg{display:none!important}.app{max-width:none!important;padding:8px 18px 90px!important}</style></head>");
    f.onload = () => { f.dataset.ready = 1; $("stLoad").style.display = "none"; try { f.contentWindow.setCh(S.ch) } catch (_) {} };
    f.srcdoc = src; return }
  try { f.contentWindow.setCh(S.ch) } catch (_) {}
}
$("vtabs").addEventListener("click", e => { const b = e.target.closest("[data-v]"); if (b && !b.disabled) setView(b.dataset.v) });
function select(i) {
  S.sel = i; if (i != null) S.wv = "board";
  if (i != null) { const g = geo(), p = DC().points[i];
    if (p.act && g.ORDER.includes(p.act)) g.ACT = p.act;
    for (const l of p.inv) if (g.ORDER.includes(l)) g.ON[l] = true;
    const [u, v] = PUV(g, p); render(); zoomTo(u, v, 6); return }
  render();
}
const now = () => { const t = new Date(), z = n => String(n).padStart(2, "0"); return `${t.getFullYear()}-${z(t.getMonth() + 1)}-${z(t.getDate())} ${z(t.getHours())}:${z(t.getMinutes())}` };
const resolution = (p, note) => ({check: p.items.map(i => i.check).join("+"), net: p.net, x: p.x, y: p.y, time: now(), note});
$("side").addEventListener("click", e => {
  const li = e.target.closest("li[data-i]"); if (li) return select(+li.dataset.i);
  const a = e.target.closest("[data-a]")?.dataset.a, ch = DC(); if (!a) return;
  if (a === "all") return $("resAll").onclick();
  if (a === "back") { S.sel = null; render(); zoomFit() }
  if (a === "prev") select((S.sel - 1 + ch.points.length) % ch.points.length);
  if (a === "next") select((S.sel + 1) % ch.points.length);
  if (a === "res") { const p = ch.points[S.sel]; RES(S.ch)[p.id] = resolution(p, $("note").value.trim()); DIRTY = true; MSG = "";
    const nx = ch.points.findIndex((q, i) => i > S.sel && !isRes(S.ch, q.id)); select(nx >= 0 ? nx : S.sel) }
  if (a === "png") { issuePng().catch(err => { $("toast").textContent = "Image failed: " + err; $("toast").style.display = "block"; setTimeout(() => $("toast").style.display = "none", 6000) }); return }
  if (a === "unres") { delete RES(S.ch)[ch.points[S.sel].id]; DIRTY = true; MSG = ""; render() }
});
$("marks").addEventListener("click", e => { const m = e.target.closest(".mk"); if (!m) return;
  if (m.dataset.i != null) return select(+m.dataset.i);
  const ids = m.dataset.g.split(",").map(Number), g = geo(), uv = ids.map(i => PUV(g, DC().points[i]));
  const us = uv.map(q => q[0]), vs = uv.map(q => q[1]); zoomTo((Math.min(...us) + Math.max(...us)) / 2, (Math.min(...vs) + Math.max(...vs)) / 2, Math.max(1.5, (Math.max(...us) - Math.min(...us)) * 4, (Math.max(...vs) - Math.min(...vs)) * 4)) });
$("marks").addEventListener("mousemove", e => { const m = e.target.closest(".mk"), tip = $("tip"); if (!m) { tip.style.display = "none"; return }
  const r = $("marks").getBoundingClientRect();
  if (m.dataset.g) tip.innerHTML = `<b>${m.dataset.g.split(",").length} points</b> close together — click to zoom in`;
  else { const p = DC().points[+m.dataset.i], done = isRes(S.ch, p.id);
    tip.innerHTML = `<b>${esc(p.id)}</b> · ${esc(p.net)}<br>` + p.items.map(it => `${esc(it.check)}: <span class="r">${U(it.value.length > 90 ? it.value.slice(0, 90) + "…" : it.value)}</span>`).join("<br>") +
      `<br><span style="color:${done ? "var(--ok)" : "#555"}">${done ? "✓ Resolved" : "Click for details / Resolve"}</span>` }
  tip.style.display = "block"; tip.style.left = Math.min(e.clientX - r.left + 14, r.width - 370) + "px"; tip.style.top = (e.clientY - r.top + 16) + "px" });
$("marks").addEventListener("mouseleave", () => $("tip").style.display = "none");
$("units").addEventListener("click", e => { const u = e.target.dataset.u; if (!u) return; S.unit = u; try { localStorage.setItem("rv_unit", u) } catch (_) {} render() });
// Resolve all = every NOT OK point of every channel
$("resAll").onclick = () => { const {n, d, per} = counts();
  $("mtext").innerHTML = `${n - d} NOT OK points are not resolved (${per.filter(p => p[1]).map(p => `${esc(p[0])}: ${p[1]}`).join(", ")}).<br>Resolving = you accept them all; the Settings tabs unlock.`;
  $("modal").classList.add("show") };
$("mno").onclick = () => $("modal").classList.remove("show");
$("myes").onclick = () => { const note = $("mnote").value.trim() || "Resolve all";
  CH.forEach((c, i) => c.points.forEach(p => { if (!isRes(i, p.id)) RES(i)[p.id] = resolution(p, note) }));
  DIRTY = true; MSG = ""; $("modal").classList.remove("show"); render() };

// ---------------------------------------------------------------- Save: settings (frame) + resolutions -> config.html
const LINK = location.protocol === "http:" && /^\/r\/[^/]+\/[0-9a-f]{32}\//.test(location.pathname)
  ? location.pathname.replace(/(\/r\/[^/]+\/[0-9a-f]{32}\/).*$/, "$1") : null;
let BASE = (D.built_at || "") + "|" + (ST.saved_at || ""), HANDLE = null, SAVING = false;
function fullState() {
  const w = FR(), s = JSON.parse(JSON.stringify(w ? w.cfgState() : ST));
  s.review = JSON.parse(JSON.stringify(ST.review)); s.current = NAMES[S.ch]; s.saved_at = ST.saved_at || null;
  CH.forEach(c => Object.values(s.review[c.name].resolved).forEach(r => delete r.carried));   // saved = confirmed
  return s;
}
function folderErrors(s) {
  const w = FR(); if (w && w.cfgFolderErrors) return w.cfgFolderErrors();
  const bad = /[<>:"\/\\|?*;\s]/, seen = {};
  return NAMES.map(n => { const v = String((s.channels[n] || {}).folder || "").trim(), k = v.toLowerCase();
    const e = !v ? "Required" : bad.test(v) ? 'No space or < > : " / \\ | ? * ;' : k === "_work" ? "Reserved name" : seen[k] ? "Already used by another channel" : "";
    seen[k] = 1; return [n, e] }).filter(x => x[1]);
}
function serialize(s) {
  const root = document.documentElement.cloneNode(true);
  for (const id of ["side", "svg", "marks", "layers", "topo", "chsel", "subLine", "hint", "msg", "count", "why", "tip", "toast", "mtext"]) { const el = root.querySelector("#" + id); if (el) el.innerHTML = "" }
  const f = root.querySelector("#stFrame"); if (f) { f.removeAttribute("srcdoc"); f.removeAttribute("data-on"); f.removeAttribute("data-ready") }
  const ld = root.querySelector("#stLoad"); if (ld) ld.removeAttribute("style");
  root.querySelector("#cfg-state").textContent = JSON.stringify(s).replace(/</g, "\\u003c");
  return "<!doctype html>\n" + root.outerHTML;
}
async function saveLink(s) {
  let r;
  try { r = await fetch(LINK + "save", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({state: s, base_rev: BASE})}) }
  catch (e) { return false }                                     // tool not reachable -> browser fallback
  let j = {}; try { j = await r.json() } catch (e) {}
  if (r.ok) { BASE = j.rev; ST.saved_at = j.saved_at; done(); say(`Saved to <b>${esc(j.path)}</b> (${new Date().toLocaleTimeString()}) — tell Claude “xong”.`); return true }
  say(`<b style="color:var(--err)">Not saved:</b> ${esc(j.error || ("error " + r.status))}`); return true;
}
function done() { DIRTY = false; CH.forEach(c => Object.values(RES(CH.indexOf(c))).forEach(r => delete r.carried)) }
async function saveOnce() {
  if (counts().d !== counts().n) return;
  const s = fullState(), bad = folderErrors(s);
  if (bad.length) { const i = NAMES.indexOf(bad[0][0]); S.ch = i; S.view = "settings"; render();
    try { FR() && FR().cfgFocusFolder(bad[0][0]) } catch (_) {}
    say(`<b style="color:var(--err)">Not saved:</b> channel folder of ${bad.map(b => esc(b[0]) + " (" + esc(b[1]) + ")").join(", ")} (Settings tab, bottom).`); return }
  let note = "";
  if (LINK) { if (await saveLink(s)) return; note = "Cannot reach the tool — saved with the browser instead. " }
  s.saved_at = ST.saved_at = new Date().toISOString();
  const html = serialize(s);
  if (window.showSaveFilePicker) {
    try {
      if (!HANDLE) HANDLE = await window.showSaveFilePicker({suggestedName: "config.html", id: "aedtcopilotcfg", types: [{description: "HTML", accept: {"text/html": [".html"]}}]});
      const w = await HANDLE.createWritable(); await w.write(html); await w.close();
      done(); say(note + `Saved <b>${esc(HANDLE.name)}</b> (${new Date().toLocaleTimeString()}) — tell Claude “xong”.`); return;
    } catch (e) { if (e && e.name === "AbortError") { say("Not saved (cancelled)."); return } }
  }
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([html], {type: "text/html"})); a.download = "config.html"; document.body.appendChild(a); a.click(); a.remove();
  done(); say(note + `Downloaded <b>config.html</b> — tell Claude “xong”.`);
}
$("save").onclick = async () => { if (SAVING) return; SAVING = true; header(); try { await saveOnce() } finally { SAVING = false; header() } };
window.addEventListener("resize", () => marks());
window.rvState = fullState;                                       // tests / tools
render();
