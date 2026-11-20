"""PI-DC report: gộp results/<skill>.json -> <out>/PIDC_report_<time>.html + report.md + summary.json + *.csv.

Ảnh nằm sẵn trong <out>/images/ (tên rõ ràng, kéo thẳng vào PowerPoint). Text/số liệu: report.md, summary.json, csv.
HTML tiếng Anh: header -> Summary (chỉ điểm bất thường) -> DC IR -> từng skill -> dữ liệu tham chiếu (thu gọn).
"""
from __future__ import annotations

import csv
import html
import json
import re
import time
from collections import defaultdict
from pathlib import Path

from .. import __version__
from . import common

CSS = """
:root{--bg:#fff;--fg:#1d2330;--mut:#5d6675;--line:#d9dee7;--card:#f6f8fb;--fail:#c62828;--warn:#c77800;--pass:#2e7d32;--info:#2f6fb5}
@media (prefers-color-scheme:dark){:root{--bg:#14171c;--fg:#e6e9ef;--mut:#9aa3b2;--line:#2c323c;--card:#1b1f26}}
body{font:14px/1.45 system-ui,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--fg);margin:0 auto;max-width:1500px;padding:16px}
h1{font-size:22px;margin:4px 0}h2{font-size:18px;margin:28px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
h3{font-size:15px;margin:16px 0 6px}.mut{color:var(--mut)}a{color:var(--info)}
table{border-collapse:collapse;margin:6px 0 12px;font-size:13px}th,td{border:1px solid var(--line);padding:3px 7px;text-align:left;vertical-align:top}
th{background:var(--card)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;padding:1px 7px;border-radius:9px;font-weight:600;font-size:12px;color:#fff;white-space:nowrap}
.FAIL{background:var(--fail)}.WARN{background:var(--warn)}.PASS{background:var(--pass)}.INFO,.HIGH{background:var(--info)}.PENDING,.NO_DATA{background:#777}
.cards{display:flex;gap:12px;flex-wrap:wrap}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;min-width:220px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(680px,1fr));gap:12px}
figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:6px}
figure img{width:100%;height:auto;background:#fff}figcaption{font-size:12px;color:var(--mut);margin-top:3px}
details{margin:6px 0}summary{cursor:pointer;font-weight:600}nav a{margin-right:12px}.ok{color:var(--pass);font-weight:600}
"""
RANK = ["NO_DATA", "PASS", "HIGH", "INFO", "WARN", "PENDING", "FAIL"]


def _e(x):
    return html.escape(str(x))


def _t(s):
    return f'<span class="tag {s}">{s}</span>'


def _n(x, d=1):
    return "" if x is None else f"{x:.{d}f}"


def siwave_tables(htm: Path) -> dict:
    """Bảng <font size=6>Title</font><table> trong report.htm của SIwave -> {title: [[cells]]}."""
    if not htm.exists() or htm.stat().st_size == 0:
        return {}
    t = htm.read_text(encoding="latin-1", errors="replace")
    out = {}
    for m in re.finditer(r"<font size=6>(.*?)</font>\s*<table[^>]*>(.*?)</table>", t, re.S | re.I):
        rows = [[html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)]
                for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", m.group(2), re.S | re.I)]
        out[re.sub(r"<[^>]+>", "", m.group(1)).strip()] = rows
    return out


# 016: cột theo TÊN header (hàng 1, không có cột Name). Thứ tự cũ chỉ dùng khi thiếu header (kèm cảnh báo).
VS_COLS = ["Magnitude(V)", "Phase(degrees)", "Source Resistance(ohms)", "Positive Terminal Net", "Negative Terminal Net",
           "Positive Terminal", "Negative Terminal", "Current(A)", "Series R Voltage(V)"]
CS_COLS = ["Magnitude(A)", "Phase(degrees)", "Source Resistance(ohms)", "Positive Terminal Net", "Negative Terminal Net",
           "Positive Terminal", "Negative Terminal", "Parallel R Current(A)", "Voltage(V)"]


def table_rows(tab, required, positional=None):
    """Bảng SIwave (hàng 0 = nhóm, hàng 1 = header không có Name, dữ liệu từ hàng 2) -> ([{Name, <header>: ô}], cảnh báo).
    Header thiếu tên trong `required` -> map theo thứ tự cũ `positional` (mặc định = required) + cảnh báo."""
    if len(tab) < 2:
        return [], None
    hdr, warn = [h.strip() for h in tab[1]], None
    if not all(r in hdr for r in required):
        hdr = list(positional or required)
        warn = f"header {tab[1]} lacks {[r for r in required if r not in tab[1]]}: columns taken by position"
    rows = []
    for c in tab[2:]:
        if len(c) < len(hdr) + 1:
            continue
        rows.append({"Name": c[0], **{h: c[i + 1] for i, h in enumerate(hdr)}})
    return rows, warn


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def vrm_output(v_set, r_ohm, i_a, series_v):
    """-> (V ra của VRM, cách tính). Cột 'Series R Voltage' = sụt áp trên R nguồn khi bằng I x R (19x19); khác I x R
    (VRM remote sense, vd. B04 VCC_0P8V: 0.8114 V) -> chính là điện áp ra."""
    if series_v is None:
        return v_set, "magnitude"
    ir = (i_a or 0.0) * (r_ohm or 0.0)
    if abs(series_v - ir) <= 1e-3 * max(abs(series_v), abs(ir)) + 1e-12:
        return v_set - series_v, "magnitude - series R drop"
    return series_v, "series R voltage column (remote sense)"


def vrm_sources(tabs, with_current=True) -> tuple:
    """Voltage Sources -> ([{name, net, terminal, V_set, R_ohm, I_A, series_V, V, V_source}], cảnh báo).
    with_current: chỉ nguồn có dòng (VRM thật); False = cả nguồn sense / không dùng (V = None)."""
    rows, warn = table_rows(tabs.get("Voltage Sources", []), ["Magnitude(V)", "Current(A)", "Series R Voltage(V)"], VS_COLS)
    out = []
    for r in rows:
        v_set, i_a = _f(r.get("Magnitude(V)")), _f(r.get("Current(A)"))
        if v_set is None or (i_a is None and with_current):
            continue
        R, s = _f(r.get("Source Resistance(ohms)")), _f(r.get("Series R Voltage(V)"))
        V, how = vrm_output(v_set, R, i_a, s) if i_a is not None else (None, "no current (sense / unused source)")
        out.append({"name": r["Name"], "net": r.get("Positive Terminal Net", ""), "terminal": r.get("Positive Terminal", ""),
                    "V_set": v_set, "R_ohm": R, "I_A": i_a, "series_V": s, "V": V, "V_source": how})
    return out, warn


def load_sources(tabs) -> tuple:
    """Current Sources -> ([{name, net, terminal, I_A, V}], cảnh báo)."""
    rows, warn = table_rows(tabs.get("Current Sources", []), ["Magnitude(A)", "Voltage(V)"], CS_COLS)
    out = []
    for r in rows:
        i_a, v = _f(r.get("Magnitude(A)")), _f(r.get("Voltage(V)"))
        if i_a is None or v is None:
            continue
        out.append({"name": r["Name"], "net": r.get("Positive Terminal Net", ""), "terminal": r.get("Positive Terminal", ""),
                    "I_A": i_a, "V": v})
    return out, warn


def dcir(ctx) -> dict:
    tabs = siwave_tables(ctx.reports / "ALL_NETS" / "report.htm")
    vs, w1 = vrm_sources(tabs, with_current=False)
    vrm = [{"name": v["name"], "V_set": v["V_set"], "R_ohm": v["R_ohm"], "net": v["net"], "I_A": v["I_A"],
            "series_V": v["series_V"], "V": v["V"], "V_source": v["V_source"]} for v in vs]
    sinks = defaultdict(list)
    ls, w2 = load_sources(tabs)
    for L in ls:
        sinks[L["net"]].append((L["I_A"], L["V"], L["name"]))
    per = [{"net": n, "sinks": len(x), "I_total_A": round(sum(i for i, _, _ in x), 4),
            "V_min": round(min(v for _, v, _ in x), 5), "at": min(x, key=lambda q: q[1])[2],
            "V_max": round(max(v for _, v, _ in x), 5)} for n, x in sinks.items()]
    per.sort(key=lambda r: -r["I_total_A"])
    res = []
    for c in tabs.get("Resistor Power losses", [])[1:]:
        if len(c) >= 4:
            try:
                res.append({"ref": c[0], "drop_mV": float(c[1]), "I_A": float(c[2]), "loss_mW": float(c[3])})
            except ValueError:
                pass
    res.sort(key=lambda r: -r["loss_mW"])
    return {"vrm": vrm, "sinks_per_net": per, "resistors": res, "stackup": tabs.get("Layer Stackup", []),
            "warnings": [w for w in (w1, w2) if w]}


def _dT_text(via):
    """016: dT = T_sim - T_base (results cũ: via_dT_C cố định)."""
    t = via.get("temperature")
    if not t:
        return f"dT = {via['params'].get('via_dT_C')} &deg;C"
    s = (f"dT = T_sim {t['T_sim_C']:g} &deg;C (DC sim temperature) &minus; T_base {t['T_base_C']:g} &deg;C = "
         f"{t['dT_C']:g} &deg;C")
    return s + "".join(f" <b>Warning: {_e(w)}</b>" for w in t.get("warnings", []))


def _csv(path, rows, keys):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def build(folder: str, sim: str = "") -> dict:
    ctx = common.Ctx(folder, sim=sim)
    man = json.loads((ctx.raw / "manifest.json").read_text(encoding="utf-8")) if (ctx.raw / "manifest.json").exists() else {}
    cd = ctx.load_result("current_density")
    via = ctx.load_result("via_current")
    vd = ctx.load_result("voltage_distribution")
    pt = ctx.load_result("power_tree")
    dc = dcir(ctx)
    ctx.save_result("dcir", dc)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    img = "images"

    # ---------------- suspect points
    pts = []
    if cd:
        for e in cd["pairs"]:
            if e["status"] in ("FAIL", "WARN", "PENDING"):
                pts.append({"result": e["status"], "check": "Current density", "net": e["net"], "where": e["layer"],
                            "detail": (f"J_avg_max {e['J_avg_max']:.1f} A/mm2 = {e['util']:.2f} x limit {e['spec']:.0f} at "
                                       f"({e['at_mm'][0]}, {e['at_mm'][1]}) mm"
                                       + (f" (narrow copper, {e['window_mm']} mm window)" if e.get("narrow_window") else ""))
                            if e["status"] != "PENDING" else e.get("reason", ""),
                            "image": e.get("image")})
    if via:
        for v in via["vias"]:
            if v["verdict"] != "PASS":
                pts.append({"result": v["verdict"], "check": "Via current", "net": v["net"], "where": v["worst_seg"],
                            "detail": f"{v['I_A']:.3f} A / I_cap {v['I_cap_A']:.3f} A = {v['util']:.2f} at ({v['x_mm']}, {v['y_mm']}) mm",
                            "image": None})
    if pt and pt.get("loads"):
        for r in pt["loads"]:
            if r["result"] != "Pass":
                pts.append({"result": "FAIL", "check": f"Power tree ({r['result']})", "net": r["net"], "where": r["load"],
                            "detail": f"{r['V']:.3f} V, {r['I']:.3f} A, drop {r['drop_mV']:.1f} mV ({r['drop_pct']:.2f} %) vs "
                                      f"spec {r['spec']}", "image": pt.get("image")})
    for j in man.get("missing_jobs", []):
        pts.append({"result": "PENDING", "check": "Export", "net": j, "where": "", "detail": "report not exported", "image": None})
    pts.sort(key=lambda p: -RANK.index(p["result"]))
    info = [e for e in (cd or {}).get("pairs", []) if e.get("peak_info")]
    pins = [e for e in (cd or {}).get("pairs", []) if e.get("pin_node")]

    summary = {"tool": f"Ansys AEDT Copilot {__version__}", "time": time.strftime("%Y-%m-%d %H:%M"), "project": str(ctx.siw),
               "sim": ctx.sim, "verdicts": {"current_density": cd and cd["verdict"], "via_current": via and via["verdict"],
                                            "voltage_distribution": vd and vd["verdict"], "power_tree": pt and pt["verdict"]},
               "power_tree": pt and {"settings": pt.get("settings"), "loads": pt.get("loads")},
               "voltage_rails": vd and vd.get("rails"),
               "suspect_points": pts, "peak_info": [{k: e[k] for k in ("net", "layer", "vmax", "peak_util")} for e in info],
               "pin_node_info": [{"net": e["net"], "layer": e["layer"], **{k: e["pin_node"][k] for k in ("J_avg_max", "util", "at_mm")},
                                  "image": e.get("image")} for e in pins],
               "image_size": man.get("image_size"), "images_dir": str(ctx.images)}
    (ctx.out / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    if cd:
        _csv(ctx.out / "current_density.csv", cd["pairs"] + cd["all_power"],
             ["job", "net", "layer", "status", "spec", "J_avg_max", "util", "at_mm", "background", "vmax", "image", "reason"])
    if via:
        _csv(ctx.out / "vias.csv", via["vias"], ["net", "x_mm", "y_mm", "type", "span", "drill_mm", "worst_seg", "I_A",
                                                 "I_cap_A", "util", "verdict"])

    # ---------------- HTML
    H = [f"<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
         f"<title>PI-DC report</title><style>{CSS}</style></head><body>",
         f"<h1>PI-DC report &mdash; {_e(ctx.siw.stem)}</h1><div class=mut>Project {_e(ctx.siw)} &middot; DC simulation "
         f"<b>{_e(ctx.sim)}</b> &middot; {summary['time']} &middot; Ansys AEDT Copilot v{_e(__version__)} &middot; images "
         f"{_e(man.get('image_size'))} px &middot; every image is a separate PNG in <code>{img}/</code></div>",
         "<nav style='margin:10px 0'><a href='#summary'>Summary</a><a href='#dcir'>DC IR</a><a href='#pt'>Power tree</a>"
         "<a href='#vd'>Voltage distribution</a>"
         "<a href='#cd'>Current density</a><a href='#via'>Via current</a><a href='#ref'>Reference</a></nav>",
         "<h2 id=summary>Summary &mdash; suspect points</h2><div class=cards>"]
    if cd:
        c = cd["counts"]
        H.append(f"<div class=card>Current density {_t(cd['verdict'])}<br><span class=mut>FAIL {c['FAIL']} &middot; WARN {c['WARN']} "
                 f"&middot; PENDING {c['PENDING']} &middot; INFO {c.get('INFO', 0)} &middot; NO_DATA {c['NO_DATA']} of {sum(c.values())} "
                 "net-layer pairs</span></div>")
    if via:
        v0 = max(via["vias"], key=lambda v: v["util"]) if via["vias"] else None
        H.append(f"<div class=card>Via current {_t(via['verdict'])}<br><span class=mut>FAIL {via['counts']['FAIL']} &middot; "
                 f"WARN {via['counts']['WARN']} of {via['counts']['power_vias']} power vias"
                 + (f"<br>worst util {v0['util']:.2f} ({_e(v0['net'])} {v0['I_A']:.2f} A)" if v0 else "") + "</span></div>")
    if pt and pt.get("counts", {}).get("loads"):
        H.append(f"<div class=card>Power tree {_t(pt['verdict'])}<br><span class=mut>FAIL {pt['counts']['FAIL']} of "
                 f"{pt['counts']['loads']} loads (spec {pt['settings']['pt_voltage']:g} "
                 f"{'%' if str(pt['settings']['pt_voltage_type']).lower().startswith('perc') else 'V'}, "
                 f"{pt['settings']['pt_current_A']:g} A)</span></div>")
    H.append("</div>")
    if pts:
        H.append("<table><tr><th>Result</th><th>Check</th><th>Net</th><th>Layer / segment</th><th>Detail</th><th>Image</th></tr>" +
                 "".join(f"<tr><td>{_t(p['result'])}</td><td>{p['check']}</td><td>{_e(p['net'])}</td><td>{_e(p['where'])}</td>"
                         f"<td>{_e(p['detail'])}</td><td>" + (f"<a href='{img}/{_e(p['image'])}' target=_blank>{_e(p['image'])}</a>"
                                                             if p['image'] else "") + "</td></tr>" for p in pts) + "</table>")
    else:
        H.append("<p class=ok>No FAIL / WARN / PENDING point.</p>")
    if pins:
        H.append(f"<details><summary>INFO &mdash; pin-node artefacts on component pads (SIwave injects pin current at a node; "
                 f"high J there is not real, not used for the verdict): {len(pins)}</summary><table><tr><th>Net</th><th>Layer</th>"
                 "<th>J_avg_max on pad A/mm2</th><th>x limit</th><th>at (mm)</th><th>Image</th></tr>" + "".join(
                     f"<tr><td>{_e(e['net'])}</td><td>{_e(e['layer'])}</td><td class=n>{_n(e['pin_node']['J_avg_max'])}</td>"
                     f"<td class=n>{_n(e['pin_node']['util'], 2)}</td><td>{_e(e['pin_node']['at_mm'])}</td><td>"
                     + (f"<a href='{img}/{_e(e['image'])}' target=_blank>{_e(e['image'])}</a>" if e.get('image') else "") + "</td></tr>"
                     for e in sorted(pins, key=lambda e: -e['pin_node']['util'])) + "</table></details>")
    if info:
        H.append(f"<details><summary>INFO &mdash; single-point colour-bar peaks above the limit (pad/via edges, not used for the "
                 f"verdict): {len(info)}</summary><table><tr><th>Net</th><th>Layer</th><th>Peak A/mm2</th><th>Peak / limit</th>"
                 "<th>J_avg_max</th><th>Result</th></tr>" + "".join(
                     f"<tr><td>{_e(e['net'])}</td><td>{_e(e['layer'])}</td><td class=n>{_n(e['vmax'])}</td><td class=n>"
                     f"{_n(e['peak_util'], 2)}</td><td class=n>{_n(e.get('J_avg_max'))}</td><td>{_t(e['status'])}</td></tr>"
                     for e in sorted(info, key=lambda e: -e['peak_util'])) + "</table></details>")

    # ---------------- DC IR
    H.append("<h2 id=dcir>DC IR</h2>")
    if dc["vrm"]:
        H.append("<h3>Voltage sources (VRM)</h3><table><tr><th>Name</th><th>V set</th><th>R &Omega;</th><th>Net</th><th>I A</th>"
                 "<th>Series R voltage (SIwave column)</th><th>V out</th><th>V out from</th></tr>" + "".join(
                     f"<tr><td>{_e(v['name'])}</td><td class=n>{_e(v['V_set'])}</td><td class=n>{_e(v['R_ohm'])}</td><td>{_e(v['net'])}"
                     f"</td><td class=n>{_e(v['I_A'] if v['I_A'] is not None else '')}</td><td class=n>"
                     f"{_e(v['series_V'] if v['series_V'] is not None else '')}</td><td class=n>"
                     f"{'' if v['V'] is None else format(v['V'], '.5f')}</td><td>{_e(v['V_source'])}</td></tr>"
                     for v in dc["vrm"]) + "</table>")
        for w in dc.get("warnings", []):
            H.append(f"<p class=mut>Source table warning: {_e(w)}</p>")
    if dc["sinks_per_net"]:
        H.append("<h3>Current sinks per net</h3><table><tr><th>Net</th><th>Sinks</th><th>Total I A</th><th>Min V</th><th>at</th>"
                 "<th>Max V</th></tr>" + "".join(
                     f"<tr><td>{_e(r['net'])}</td><td class=n>{r['sinks']}</td><td class=n>{r['I_total_A']:.3f}</td><td class=n>"
                     f"{r['V_min']:.4f}</td><td>{_e(r['at'])}</td><td class=n>{r['V_max']:.4f}</td></tr>" for r in dc["sinks_per_net"])
                 + "</table>")
    if dc["resistors"]:
        H.append("<h3>Series resistor / ferrite drop and loss</h3><table><tr><th>Ref</th><th>Drop mV</th><th>I A</th><th>Loss mW</th></tr>"
                 + "".join(f"<tr><td>{_e(r['ref'])}</td><td class=n>{r['drop_mV']:.3f}</td><td class=n>{r['I_A']:.3f}</td>"
                           f"<td class=n>{r['loss_mW']:.3f}</td></tr>" for r in dc["resistors"]) + "</table>")

    # ---------------- power tree
    if pt and pt.get("loads"):
        s = pt["settings"]
        vtxt = f"{s['pt_voltage']:g} %" if str(s["pt_voltage_type"]).lower().startswith("perc") else f">= {s['pt_voltage']:g} V"
        H.append(f"<h2 id=pt>Power tree {_t(pt['verdict'])}</h2><p class=mut>SIwave Export DC Power Tree. Specification "
                 f"for every component: Include {s['pt_include']}, current threshold {s['pt_current_A']:g} A, voltage "
                 f"{s['pt_voltage_type']} {vtxt} of the VRM output ({_e(pt['vrm']['name'])} {pt['vrm']['V']:.3f} V); aggregate "
                 f"pins on a net within a component: {'on' if s['pt_aggregate_pins'] else 'off'}; power-loss list: "
                 f"{'on' if s['pt_output_power_loss'] else 'off'}. FAIL {pt['counts']['FAIL']} / {pt['counts']['loads']} loads.</p>"
                 f"<figure><a href='{img}/{pt['image']}' target=_blank><img loading=lazy src='{img}/{pt['image']}'></a>"
                 f"<figcaption><code>{pt['image']}</code></figcaption></figure>"
                 "<table><tr><th>Result</th><th>Load</th><th>Rail</th><th>Fed from</th><th>V</th><th>I A</th><th>Drop mV</th>"
                 "<th>Drop %</th><th>Spec</th></tr>" + "".join(
                     f"<tr><td>{_t('PASS' if r['result'] == 'Pass' else 'FAIL')} {_e(r['result'])}</td><td>{_e(r['load'])}</td>"
                     f"<td>{_e(r['net'])}</td><td>{_e(r['from'])}</td><td class=n>{r['V']:.3f}</td><td class=n>{r['I']:.3f}</td>"
                     f"<td class=n>{r['drop_mV']:.1f}</td><td class=n>{r['drop_pct']:.2f}</td><td>{_e(r['spec'])}</td></tr>"
                     for r in sorted(pt["loads"], key=lambda r: -(r["drop_pct"] or 0))) + "</table>")
        if pt.get("power_loss"):
            H.append("<details><summary>Power loss per net</summary><table><tr><th>Net</th><th>Loss mW</th></tr>" + "".join(
                f"<tr><td>{_e(x['net'])}</td><td class=n>{x['loss_mW']:.3f}</td></tr>"
                for x in sorted(pt["power_loss"], key=lambda x: -x["loss_mW"])) + "</table></details>")

    # ---------------- voltage distribution
    vrows = []
    if vd and vd.get("rails"):
        for t in vd["rails"]:
            vs = "; ".join(f"{v['refdes']} {v['V'] * 1000:.1f} mV" for v in t["vrm"]) or "(fed through series part)"
            for L in t["loads"]:
                vrows.append((t["net"], vs, L))
        H.append(f"<h2 id=vd>Voltage distribution</h2><p class=mut>All power rails (GND excluded), all metal layers overlaid "
                 f"(bottom first, top layer on top), one linear colour scale {vd['scale_mV'][0]:.1f}..{vd['scale_mV'][1]:.1f} mV "
                 "shared by all rails. Circles = minimum-voltage pin of each load (refdes.pin, rail, V); VRM = voltage at the "
                 "VRM output. Drop = VRM output voltage &minus; load Vmin (rails fed through ferrites/resistors: from the "
                 "upstream VRM). Information only, no IR-drop spec.</p>"
                 f"<figure><a href='{img}/{vd['image']}' target=_blank><img loading=lazy src='{img}/{vd['image']}'></a>"
                 f"<figcaption><code>{vd['image']}</code></figcaption></figure>"
                 "<table><tr><th>Rail</th><th>VRM (voltage at output)</th><th>Load</th><th>Vmin mV</th><th>Drop mV</th>"
                 "<th>Drop %</th></tr>" + "".join(
                     f"<tr><td>{_e(net)}</td><td>{_e(vs)}</td><td>{_e(L['refdes'])}.{_e(L['pin'])}</td><td class=n>"
                     f"{L['V_min'] * 1000:.2f}</td><td class=n>{L['drop_mV']:.2f}</td><td class=n>{_n(L['drop_pct'], 2)}</td></tr>"
                     for net, vs, L in vrows) + "</table>")

    # ---------------- current density
    if cd:
        P = cd["params"]
        H.append(f"<h2 id=cd>Current density</h2><p class=mut>J averaged over {P['cd_window_mm']} x {P['cd_window_mm']} mm windows "
                 f"(copper only, windows with &lt; {int(P['cd_min_copper_frac'] * 100)} % copper ignored). Verdict on the maximum window "
                 f"average J_avg_max: FAIL &gt; limit, WARN &gt; {int(P['cd_warn_frac'] * 100)} % (limit outer "
                 f"{P['cd_outer_A_mm2']} / inner {P['cd_inner_A_mm2']} A/mm&sup2;). Boxed regions: J_avg_max &ge; "
                 f"{int(P['cd_warn_frac'] * 100)} % of limit or &ge; {P['cd_bg_factor']} &times; layer background, max "
                 f"{P['cd_max_regions']} per image; label = region J_avg_max."
                 + (f" Narrow copper (no {P['cd_window_mm']} mm window with enough copper, e.g. thin RDL traces): mean J over "
                    f"copper pixels in {P['cd_narrow_window_mm']} mm windows, judged the same way; copper pieces &lt; "
                    f"{P['cd_tiny_area_mm2']} mm&sup2; are not judged (INFO)." if "cd_narrow_window_mm" in P else "")
                 + "</p>")
        rows = sorted([e for e in cd["pairs"] if e["status"] != "NO_DATA"], key=lambda e: (-RANK.index(e["status"]), -(e.get("util") or 0)))
        H.append("<table><tr><th>Result</th><th>Net</th><th>Layer</th><th>Limit</th><th>J_avg_max</th><th>util</th><th>at (mm)</th>"
                 "<th>Background</th><th>Regions</th><th>Peak (info)</th><th>Image</th></tr>" + "".join(
                     f"<tr><td>{_t(e['status'])}</td><td>{_e(e['net'])}</td><td>{_e(e['layer'])}</td><td class=n>{e['spec']:.0f}</td>"
                     f"<td class=n>{_n(e.get('J_avg_max'))}</td><td class=n>{_n(e.get('util'), 2)}</td><td>{_e(e.get('at_mm', ''))}</td>"
                     f"<td class=n>{_n(e.get('background'))}</td><td>{_e(', '.join(f'{q['id']}: {q['J_avg_max']}' for q in e.get('regions', [])))}</td>"
                     f"<td class=n>{_n(e.get('vmax'))}</td><td>" + (f"<a href='{img}/{_e(e['image'])}' target=_blank>{_e(e['image'])}</a>"
                                                                  if e.get('image') else _e(e.get('reason', ''))) + "</td></tr>"
                     for e in rows) + "</table>")
        H.append("<h3>ALL_POWER per layer</h3><div class=grid>")
        for e in cd["all_power"]:
            if e.get("image"):
                cap = "; ".join(f"{q['id']}: {q['J_avg_max']} A/mm2 ({q['tier']})" for q in e.get("regions", [])) or "no outstanding region"
                H.append(f"<figure><a href='{img}/{_e(e['image'])}' target=_blank><img loading=lazy src='{img}/{_e(e['image'])}'></a>"
                         f"<figcaption>{_e(e['layer'])} &middot; J_avg_max {_n(e.get('J_avg_max'))} A/mm&sup2; &middot; {_e(cap)} &middot; "
                         f"<code>{_e(e['image'])}</code></figcaption></figure>")
        H.append("</div><h3>Per net</h3>")
        by = defaultdict(list)
        for e in cd["pairs"]:
            if e.get("image"):
                by[e["net"]].append(e)
        for net, es in by.items():
            w = max((e["status"] for e in es), key=RANK.index)
            H.append(f"<details><summary>{_e(net)} {_t(w)} &middot; {len(es)} layer(s)</summary><div class=grid>" + "".join(
                f"<figure><a href='{img}/{_e(e['image'])}' target=_blank><img loading=lazy src='{img}/{_e(e['image'])}'></a><figcaption>"
                f"{_e(e['layer'])} {_t(e['status'])} J_avg_max {_n(e.get('J_avg_max'))} A/mm&sup2; &middot; <code>{_e(e['image'])}</code>"
                f"</figcaption></figure>" for e in es) + "</div></details>")

    # ---------------- via
    if via:
        P = via["params"]
        H.append(f"<h2 id=via>Via current</h2><p class=mut>I = |J| &times; &pi;(r_drill&sup2; &minus; r_inner&sup2;) per segment "
                 f"(.vcd/.vias); a via is rated by its worst segment. I_cap = 0.024&middot;dT<sup>0.44</sup>&middot;(3.14&middot;r_mil&sup2;)"
                 f"<sup>0.725</sup>, r = finished hole radius, {_dT_text(via)}. FAIL util &gt; 1, WARN &gt; {P['via_warn_util']}. "
                 f"Circled: FAIL/WARN and the top {P['via_top_n']} by current at the shown layer; label = current at that layer.</p><div class=grid>")
        for im in via["images"]:
            H.append(f"<figure><a href='{img}/{_e(im['file'])}' target=_blank><img loading=lazy src='{img}/{_e(im['file'])}'></a>"
                     f"<figcaption>{_e(im['title'])} &middot; <code>{_e(im['file'])}</code></figcaption></figure>")
        H.append("</div>")
        hdr = ("<tr><th>#</th><th>Net</th><th>x mm</th><th>y mm</th><th>Type</th><th>Span</th><th>Drill mm</th><th>Worst segment</th>"
               "<th>I A</th><th>I_cap A</th><th>util</th><th>Result</th></tr>")
        row = lambda i, v: (f"<tr><td class=n>{i}</td><td>{_e(v['net'])}</td><td class=n>{v['x_mm']}</td><td class=n>{v['y_mm']}</td>"
                            f"<td>{v['type']}</td><td>{_e(v['span'])}</td><td class=n>{v['drill_mm']}</td><td>{_e(v['worst_seg'])}</td>"
                            f"<td class=n>{v['I_A']:.3f}</td><td class=n>{v['I_cap_A']:.3f}</td><td class=n>{v['util']:.3f}</td>"
                            f"<td>{_t(v['verdict'])}</td></tr>")
        vs = sorted(via["vias"], key=lambda v: -v["util"])
        H.append("<h3>Top 15 power vias by utilisation</h3><table>" + hdr + "".join(row(i, v) for i, v in enumerate(vs[:15], 1)) + "</table>")
        H.append("<details><summary>All power vias</summary><table>" + hdr + "".join(row(i, v) for i, v in enumerate(vs, 1)) + "</table></details>")
        if via.get("gnd_top"):
            H.append("<details><summary>Highest-current GND vias (information, GND not rated)</summary><table>" + hdr +
                     "".join(row(i, v) for i, v in enumerate(via["gnd_top"], 1)) + "</table></details>")
        xc = via.get("crosscheck")
        if xc and xc.get("matched"):
            H.append(f"<p class=mut>Cross-check vs SIwave Element Data 'Vias': {xc['matched']} vias, I(.vcd)/I(table) median "
                     f"{xc['ratio_median']:.4f} (min {xc['ratio_min']:.3f}, max {xc['ratio_max']:.3f}).</p>")

    # ---------------- reference
    H.append("<h2 id=ref>Reference data</h2>")
    if dc["stackup"]:
        H.append("<details><summary>Layer stackup</summary><table>" + "".join(
            "<tr>" + "".join(f"<td>{_e(c)}</td>" for c in r[:10]) + "</tr>" for r in dc["stackup"]) + "</table></details>")
    H.append("<details><summary>Export</summary><ul>" + "".join(f"<li>{_e(k)}: {_e(man.get(k))}</li>" for k in
             ("siw", "sim_name", "run_dir", "image_size", "requested_size", "missing_jobs", "attempts", "seconds", "time")) + "</ul></details>")
    if cd:
        bad = [e for e in cd["pairs"] + cd["all_power"] if e.get("ocr_ok") is False]
        H.append(f"<p class=mut>Colour bars failing the OCR self-check (all 15 labels parsed, linear within 0.5 %): {len(bad)}. "
                 f"Pixel calibration {cd['calib_ppmm']} px/mm.</p>")
    H.append("</body></html>")
    hp = ctx.out / f"PIDC_report_{stamp}.html"
    hp.write_text("\n".join(H), encoding="utf-8")

    # ---------------- Markdown (text for slides)
    M = [f"# PI-DC report - {ctx.siw.stem}", "", f"- Project: `{ctx.siw}`", f"- DC simulation: {ctx.sim}",
         f"- Generated: {summary['time']} by Ansys AEDT Copilot {__version__}", ""]
    M.append("## Summary")
    M.append(f"- Current density: **{summary['verdicts']['current_density']}**")
    M.append(f"- Via current: **{summary['verdicts']['via_current']}**")
    if vd:
        M.append(f"- Voltage distribution: information only (image {vd.get('image', '-')})")
    if pt:
        M.append(f"- Power tree: **{pt['verdict']}** (image {pt.get('image', '-')})")
    M += [""] + ([f"| Result | Check | Net | Layer | Detail |", "|---|---|---|---|---|"] +
                 [f"| {p['result']} | {p['check']} | {p['net']} | {p['where']} | {p['detail']} |" for p in pts] if pts
                 else ["No FAIL / WARN / PENDING point."])
    if pt and pt.get("loads"):
        s = pt["settings"]
        M += ["", f"## Power tree: {pt['verdict']} (image {pt['image']}; {s['pt_current_A']:g} A, {s['pt_voltage_type']} "
                  f"{s['pt_voltage']:g})", "", "| Result | Load | Rail | V | I A | Drop mV | Drop % | Spec |",
              "|---|---|---|---|---|---|---|---|"]
        M += [f"| {r['result']} | {r['load']} | {r['net']} | {r['V']:.3f} | {r['I']:.3f} | {r['drop_mV']:.1f} | "
              f"{r['drop_pct']:.2f} | {r['spec']} |" for r in sorted(pt["loads"], key=lambda r: -(r["drop_pct"] or 0))]
    if vrows:
        M += ["", f"## Voltage distribution (image {vd['image']}, info only)", "",
              "| Rail | VRM | Load | Vmin mV | Drop mV | Drop % |", "|---|---|---|---|---|---|"]
        M += [f"| {net} | {vs} | {L['refdes']}.{L['pin']} | {L['V_min'] * 1000:.2f} | {L['drop_mV']:.2f} | {_n(L['drop_pct'], 2)} |"
              for net, vs, L in vrows]
    if cd:
        M += ["", "## Current density (J_avg_max per net/layer with current)", "", "| Net | Layer | J_avg_max A/mm2 | Limit | util | Result | Image |",
              "|---|---|---|---|---|---|---|"]
        M += [f"| {e['net']} | {e['layer']} | {_n(e.get('J_avg_max'))} | {e['spec']:.0f} | {_n(e.get('util'), 2)} | {e['status']} | "
              f"{e.get('image', '')} |" for e in rows]
    if via:
        M += ["", "## Via current (top 10 by utilisation)", "", "| Net | x mm | y mm | Drill mm | I A | I_cap A | util | Result |",
              "|---|---|---|---|---|---|---|---|"]
        M += [f"| {v['net']} | {v['x_mm']} | {v['y_mm']} | {v['drill_mm']} | {v['I_A']:.3f} | {v['I_cap_A']:.3f} | {v['util']:.3f} | "
              f"{v['verdict']} |" for v in sorted(via["vias"], key=lambda v: -v["util"])[:10]]
        M += ["", "Images: " + ", ".join(im["file"] for im in via["images"])]
    (ctx.out / "report.md").write_text("\n".join(M), encoding="utf-8")
    return {"html": str(hp), "report_md": str(ctx.out / "report.md"), "summary_json": str(ctx.out / "summary.json"),
            "images_dir": str(ctx.images), "images": len(list(ctx.images.glob("*.png"))), "verdicts": summary["verdicts"],
            "suspect_points": pts}
