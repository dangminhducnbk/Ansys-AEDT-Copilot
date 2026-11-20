"""Skill PI-DC: via current (guides/pidc_via_current.md).

Dữ liệu: <run>.vias (r_inner, r_drill mm) + <run>.vcd (J A/m² mỗi đoạn via). I đoạn = |J| x pi(r_drill² - r_inner²);
via vật lý = cùng net + x,y; đánh giá theo đoạn xấu nhất. I_cap = 0.024 dT^0.44 (3.14 r_mil²)^0.725 (r = bán kính lỗ hoàn thiện).
FAIL util > 1, WARN > via_warn_util. Ảnh: VIACUR (A) của SIwave, khoanh FAIL/WARN + top-N theo dòng tại lớp đó.
016: dT = nhiệt độ mô phỏng (run cfg GlobalTemperature) - via_base_temp_C; thiếu nhiệt độ hoặc dT <= 0 -> dừng.
"""
from __future__ import annotations

import math
import shlex
import time

import numpy as np

from ...core.units import MM
from .. import common, imaging

NAME = "via_current"
ORDER = 20
NEEDS_EXPORT = True
TITLE = "Via current"


def ipc_cap(r_mm: float, dT: float) -> float:
    r_mil = r_mm / 0.0254
    return 0.024 * dT ** 0.44 * (3.14 * r_mil ** 2) ** 0.725


def temperature(ctx, P) -> dict:
    """{T_sim_C, T_base_C, dT_C, source, warnings}. dT <= 0 -> lỗi (công thức IPC không có khả năng tải)."""
    t_sim, cfg = common.sim_temperature(ctx.run_dir)
    t_base = float(P["via_base_temp_C"])
    dT = t_sim - t_base
    if dT <= 0:
        raise RuntimeError(f"Via dT = T_sim {t_sim:g} - T_base {t_base:g} = {dT:g} degC <= 0 ({cfg}): the IPC capacity "
                           "needs a temperature rise. Check the DC sim temperature or pidc.via_base_temp_C.")
    w = [] if 10 <= dT <= 100 else [f"dT {dT:g} degC outside the IPC-2221 chart range 10..100 degC"]
    return {"T_sim_C": t_sim, "T_base_C": t_base, "dT_C": dT, "source": str(cfg), "warnings": w}


def load_vias(base, metals, P, dT):
    idx = {n: i for i, n in enumerate(metals)}
    rad = {}
    for ln in open(str(base) + ".vias", encoding="latin-1"):
        t = ln.split()
        if t:
            rad[t[0]] = (float(t[1]), float(t[2]))
    vias = {}
    for ln in open(str(base) + ".vcd", encoding="latin-1"):
        if not ln.strip():
            continue
        name, net, x, y, lf, lt, j = shlex.split(ln)
        ri, ro = rad[name]
        i_a = abs(float(j)) * math.pi * ((ro * MM) ** 2 - (ri * MM) ** 2)
        key = (net, round(float(x) * 1e3, 3), round(float(y) * 1e3, 3))
        v = vias.setdefault(key, {"net": net, "gnd": bool(common.GND_RE.search(net)), "x_mm": key[1], "y_mm": key[2],
                                  "drill_mm": round(2 * ro, 4), "I_A": 0.0, "worst_seg": "", "I_at": {}, "lo": 99, "hi": -1})
        for L in (lf, lt):
            v["I_at"][L] = max(v["I_at"].get(L, 0.0), i_a)
            v["lo"], v["hi"] = min(v["lo"], idx.get(L, 99)), max(v["hi"], idx.get(L, -1))
        if i_a > v["I_A"]:
            v["I_A"], v["worst_seg"] = i_a, f"{lf}-{lt}"
    out = list(vias.values())
    last = len(metals) - 1
    for v in out:
        v["span"] = f"{metals[v['lo']]}-{metals[v['hi']]}" if v["hi"] >= 0 else ""
        v["type"] = ("through" if v["lo"] == 0 and v["hi"] == last else
                     "blind" if v["lo"] == 0 or v["hi"] == last else "buried")
        v["I_cap_A"] = ipc_cap(v["drill_mm"] / 2, dT)
        v["util"] = v["I_A"] / v["I_cap_A"]
        v["verdict"] = "FAIL" if v["util"] > 1 else ("WARN" if v["util"] > float(P["via_warn_util"]) else "PASS")
        del v["lo"], v["hi"]
    out.sort(key=lambda v: -v["I_A"])
    return out


def crosscheck(vias, table):
    tab = {}
    for ln in table.read_text(encoding="latin-1").splitlines()[2:]:
        c = ln.split("\t")
        try:
            key = (c[2], round(float(c[3]), 2), round(float(c[4]), 2))
            tab[key] = max(tab.get(key, 0.0), abs(float(c[5])))
        except (ValueError, IndexError):
            continue
    r = [v["I_A"] / tab[k] for v in vias if (k := (v["net"], round(v["x_mm"], 2), round(v["y_mm"], 2))) in tab and tab[k]]
    return {"matched": len(r), "table_vias": len(tab), "ratio_median": float(np.median(r)) if r else None,
            "ratio_min": float(min(r)) if r else None, "ratio_max": float(max(r)) if r else None}


def _image(ctx, calib, png, layer, groups, title, name):
    """groups = [(vias, top_n, label_fmt)]; khoanh FAIL/WARN + top-N theo dòng tại `layer`."""
    im = imaging.open_rgb(png)
    a = np.asarray(im)
    S = imaging.scale(im)
    box = imaging.main_box(im.reduce(4) if S > 2 else im)
    f = 4 if S > 2 else 1
    cv = imaging.Canvas(im, [box[0] * f, box[1] * f, box[2] * f, box[3] * f], thicken=True)
    pts, circled = [], []
    for vs, top, fmt in groups:
        on = sorted([v for v in vs if layer in v["I_at"]], key=lambda v: -v["I_at"][layer])
        sel, seen = [v for v in on if v["verdict"] != "PASS"] + on[:top], set()
        for v in sel:
            k = (v["net"], v["x_mm"], v["y_mm"])
            if k in seen:
                continue
            seen.add(k)
            X, Y = calib.to_px(v["x_mm"], v["y_mm"], im.size[1] / calib.size[1])
            X, Y = imaging.snap(a, X, Y, 8 * S)
            pts.append((X, Y, fmt(v, layer)))
            circled.append({k2: v[k2] for k2 in ("net", "x_mm", "y_mm", "verdict")} | {"I_at_layer_A": round(v["I_at"][layer], 4)})
    cv.circles(pts, r=20)
    cv.title(title)
    cv.save(ctx.images / name)
    return {"file": name, "layer": layer, "title": title, "circled": circled}


def run(ctx, log=print) -> dict:
    t0 = time.time()
    P = ctx.P
    tmp = temperature(ctx, P)
    for w in tmp["warnings"]:
        log("WARNING", w)
    allv = load_vias(ctx.base, ctx.metals, P, tmp["dT_C"])
    pw = [v for v in allv if not v["gnd"]]
    gnd = [v for v in allv if v["gnd"]]
    calib = imaging.Calib(imaging.best_ref(ctx), ctx.base.parent / (ctx.base.name + ".outline"))
    ctx.images.mkdir(parents=True, exist_ok=True)
    top = int(P["via_top_n"])
    lab = lambda v, L: f"{v['I_at'][L]:.2f} A  {v['net']}" + ("" if v["verdict"] == "PASS" else f"  {v['verdict']}")
    images, missing = [], []
    t, b = ctx.metals[0], ctx.metals[-1]
    for job, layer, groups, title, name in [
        ("ALL_POWER", t, [(pw, top, lab)], f"Power vias - via current at {t} (A)", f"VIA_POWER_{t}.png"),
        ("ALL_POWER", b, [(pw, top, lab)], f"Power vias - via current at {b} (A)", f"VIA_POWER_{b}.png"),
        ("ALL_NETS", t, [(pw, top, lab), (gnd, top, lab)], f"All vias (GND + power) - via current at {t} (A)",
         f"VIA_ALL_{t}.png")]:
        png = ctx.cur_png(job, "VIACUR", layer)
        if png is None:
            missing.append(f"{job} VIACUR_{layer}")
            continue
        images.append(_image(ctx, calib, png, layer, groups, title, name))
    vt = ctx.raw / "element_data" / "Vias.txt"
    xc = crosscheck(pw, vt) if vt.exists() and vt.stat().st_size else None
    vf = sum(v["verdict"] == "FAIL" for v in pw)
    vw = sum(v["verdict"] == "WARN" for v in pw)
    clean = lambda v: {k: (round(x, 5) if isinstance(x, float) else x) for k, x in v.items() if k != "I_at"}
    res = {"skill": NAME, "title": TITLE, "params": {k: P[k] for k in P if k.startswith("via_")}, "temperature": tmp,
           "verdict": "FAIL" if vf else ("WARN" if vw else "PASS"), "counts": {"FAIL": vf, "WARN": vw, "power_vias": len(pw)},
           "vias": [clean(v) for v in pw], "gnd_top": [clean(v) for v in gnd[:10]], "images": images,
           "missing_images": missing, "crosscheck": xc, "seconds": round(time.time() - t0)}
    ctx.save_result(NAME, res)
    return res
