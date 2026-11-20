"""Skill PI-DC: voltage distribution (guides/pidc_voltage_distribution.md).

1 ảnh VLT_ALL_POWER.png: điện áp mọi rail nguồn (không GND), TẤT CẢ lớp kim loại chồng lên nhau (lớp dưới vẽ trước,
TOP vẽ sau cùng = nhìn từ trên xuống như GUI), một thang màu tuyến tính chung (mV) cho cả ảnh.
Ghép từ ảnh VLT_<layer>.png của job ALL_POWER (thang màu tự động mỗi lớp -> OCR -> điện áp mỗi pixel -> tô lại).
Khoanh điểm Vmin của mỗi tải (refdes + rail + Vmin), ghi điện áp tại VRM (refdes). Chỉ thông tin, không kết luận.
Nguồn số liệu: report.htm (ALL_NETS) bảng Current Sources (điện áp tại chân tải) / Voltage Sources (VRM);
toạ độ chân: .siw (CSRC "<tải>" x+ y+ ..., dòng X ... <part> <refdes> <pin>, B_PIN_GROUP).
"""
from __future__ import annotations

import re
import time
from collections import defaultdict

import numpy as np
from PIL import Image, ImageDraw

from .. import common, imaging

NAME = "voltage_distribution"
ORDER = 30
NEEDS_EXPORT = True
TITLE = "Voltage distribution"


def _siw_geometry(siw):
    """-> (csrc {name: (x, y) mm cực +}, pins {(refdes, pin): (x, y)}, groups {group: [pins]})."""
    t = open(siw, encoding="latin-1").read()
    csrc = {m.group(1): (float(m.group(2)), float(m.group(3)))
            for m in re.finditer(r'^\s*CSRC\s+"([^"]+)"\s+(\S+)\s+(\S+)', t, re.M)}
    pins = {}
    # X idx a b c x y rot part refdes pin <cờ '\' hoặc 'F'> ...
    for m in re.finditer(r"^\s*X\s+\d+\s+\d+\s+\d+\s+\d+\s+(\S+)\s+(\S+)\s+\S+\s+\S+\s+(\S+)\s+(\S+)\s+\S\s", t, re.M):
        pins[(m.group(3), m.group(4))] = (float(m.group(1)), float(m.group(2)))
    groups = {m.group(1): m.group(2).split() for m in re.finditer(r"^B_PIN_GROUP\s+(\S+)[^\n]*\n([^\n]*)\n", t, re.M)}
    return csrc, pins, groups


def _sources(ctx):
    """Tải (từ Current Sources) và VRM (Voltage Sources có dòng) trong report.htm của ALL_NETS."""
    from ..report import load_sources, siwave_tables, vrm_sources
    tabs = siwave_tables(ctx.reports / "ALL_NETS" / "report.htm")
    ls, w1 = load_sources(tabs)                                         # 016: cột theo tên header
    vs, w2 = vrm_sources(tabs)
    loads = []
    for L in ls:
        m = re.match(r"(.+)\((.+)\)$", L["terminal"])                   # "AA6(U13)" -> pin, refdes
        loads.append({"name": L["name"], "net": L["net"], "pin": m.group(1) if m else "",
                      "refdes": m.group(2) if m else L["name"], "I_A": L["I_A"], "V": L["V"]})
    vrms = []
    for s in vs:
        m = re.match(r"(.+)\((.+)\)$", s["terminal"])
        vrms.append({"name": s["name"], "net": s["net"], "group": m.group(1) if m else "",
                     "refdes": m.group(2) if m else s["name"], "V_set": s["V_set"], "I_A": s["I_A"], "V": s["V"],
                     "V_source": s["V_source"]})
    return loads, vrms, [w for w in (w1, w2) if w]


def _composite(ctx, layers):
    """Điện áp (V) mỗi pixel, chồng lớp: lớp dưới trước, TOP sau cùng (đè lên). -> (Vmap, template image, info)."""
    V, tpl, info, todo = None, None, [], []
    for lay in reversed(layers):                                          # BOTTOM ... TOP
        p = ctx.cur_png("ALL_POWER", "VLT", lay)
        if p is None:
            info.append({"layer": lay, "status": "missing"})
            continue
        im = imaging.open_rgb(p)
        cb = imaging.read_colorbar(im)
        if not cb["ok"]:
            info.append({"layer": lay, "status": "ocr_failed", "err": cb["err"]})
            continue
        todo.append((lay, im, cb))
    vtop = max((cb["vmax"] for _, _, cb in todo), default=0)
    for lay, im, cb in todo:
        if cb["vmax"] < 0.5 * vtop:                                       # lớp chỉ có GND (vài mV) -> bỏ
            info.append({"layer": lay, "status": "skipped (GND only)", "vmax": cb["vmax"]})
            continue
        Jv, x0 = imaging.jmap(im, cb["vmin"], cb["vmax"])              # cùng phép đổi màu -> giá trị như current density
        if V is None:
            V = np.full((im.size[1], im.size[0]), np.nan, np.float32)
            tpl = im
        sub = V[:, x0:]
        ok = np.isfinite(Jv)
        sub[ok] = Jv[ok]
        info.append({"layer": lay, "status": "ok", "vmin": cb["vmin"], "vmax": cb["vmax"], "px": int(ok.sum())})
    return V, tpl, info


def _render(V, tpl):
    """Tô lại Vmap (mV, đơn vị export) bằng 14 dải màu SIwave với một thang chung + thang màu bên trái (kiểu SIwave)."""
    bands = imaging.band_colors(tpl)                                     # index 0 = dải cao nhất
    vals = V[np.isfinite(V)]
    lo, hi = float(vals.min()), float(vals.max())
    k = np.clip((np.nan_to_num(hi - V, nan=0) / max(hi - lo, 1e-12) * 14).astype(np.int32), 0, 13)
    img = np.full(V.shape + (3,), 255, np.uint8)
    m = np.isfinite(V)
    img[m] = bands[k[m]]
    im = Image.fromarray(img)
    S = imaging.scale(im)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, int(0.45 * im.size[1]), im.size[1]], fill="white")
    f = imaging.font(int(24 * S))
    y0, y1 = 20 * S, 972 * S
    for i in range(14):
        a, b = y0 + i * (y1 - y0) / 14, y0 + (i + 1) * (y1 - y0) / 14
        d.rectangle([0, a, 98 * S, b], fill=tuple(int(c) for c in bands[i]), outline=(0, 0, 0))
    for i in range(15):
        v = hi - i * (hi - lo) / 14
        d.text((104 * S, y0 + i * (y1 - y0) / 14 - 14 * S), f"+{v:.3f} mV", fill="black", font=f)
    return im, lo, hi


def run(ctx, log=print) -> dict:
    t0 = time.time()
    layers = ctx.metals
    V, tpl, info = _composite(ctx, layers)
    if V is None or not np.isfinite(V).any():                          # 016: ảnh rỗng -> PENDING, không lỗi
        res = {"skill": NAME, "title": TITLE, "verdict": "PENDING", "counts": {"PENDING": 1}, "layers": info,
               "reason": "no VLT image for ALL_POWER (run pidc_export)" if V is None else
               "VLT images of ALL_POWER have no voltage pixel", "seconds": round(time.time() - t0)}
        ctx.save_result(NAME, res)
        return res
    im, lo, hi = _render(V, tpl)
    calib = imaging.Calib(imaging.best_ref(ctx), ctx.base.parent / (ctx.base.name + ".outline"))
    f = im.size[1] / calib.size[1]
    loads, vrms, warns = _sources(ctx)
    csrc, pins, groups = _siw_geometry(ctx.siw)
    # Vmin mỗi tải (refdes + rail)
    worst = {}
    for L in loads:
        k = (L["refdes"], L["net"])
        if k not in worst or L["V"] < worst[k]["V"]:
            worst[k] = L
    rails = defaultdict(lambda: {"vrm": [], "loads": []})
    vrm_v = {}
    for s in vrms:
        rails[s["net"]]["vrm"].append(s)
        vrm_v[s["net"]] = s["V"]
        xs = [pins[(s["refdes"], p)] for p in groups.get(s["group"], []) if (s["refdes"], p) in pins]
        s["xy_mm"] = [round(float(np.mean([x for x, _ in xs])), 3), round(float(np.mean([y for _, y in xs])), 3)] if xs else None
    v_ref = max(vrm_v.values()) if vrm_v else hi / 1000
    for (ref, net), L in sorted(worst.items(), key=lambda kv: kv[1]["V"]):
        xy = csrc.get(L["name"])
        vr = vrm_v.get(net, v_ref)
        rails[net]["loads"].append({"refdes": ref, "pin": L["pin"], "V_min": L["V"], "xy_mm": xy and [round(v, 3) for v in xy],
                                    "drop_mV": round((vr - L["V"]) * 1000, 2), "drop_pct": round((vr - L["V"]) / vr * 100, 2) if vr else None,
                                    "ref_V": vr, "ref": "VRM" if net in vrm_v else "highest VRM"})
    # ảnh: khung = phần lớn structure; khoanh Vmin mỗi tải; nhãn VRM
    box = imaging.main_box(im.reduce(4) if f > 2 else im)
    r = 4 if f > 2 else 1
    cv = imaging.Canvas(im, [box[0] * r, box[1] * r, box[2] * r, box[3] * r])
    pts = []
    for net, R in rails.items():
        for L in R["loads"]:
            if L["xy_mm"]:
                X, Y = calib.to_px(*L["xy_mm"], f)
                pts.append((X, Y, f"{L['refdes']}.{L['pin']} {net}: {L['V_min'] * 1000:.1f} mV"))
    for s in vrms:
        if s.get("xy_mm"):
            X, Y = calib.to_px(*s["xy_mm"], f)
            pts.append((X, Y, f"VRM {s['refdes']} ({s['net']}): {s['V'] * 1000:.1f} mV"))
    cv.circles(pts, r=18, color=(0, 0, 0), halo=True)          # đen + viền trắng: nổi trên nền đỏ/cam/xanh
    cv.title(f"Voltage distribution - all power rails, all layers overlaid (top layer on top), common scale "
             f"{lo:.1f}..{hi:.1f} mV")
    ctx.images.mkdir(parents=True, exist_ok=True)
    cv.save(ctx.images / "VLT_ALL_POWER.png")
    table = [{"net": net, "vrm": [{"refdes": s["refdes"], "V": s["V"], "V_set": s["V_set"], "I_A": s["I_A"],
                                   "V_source": s["V_source"]} for s in R["vrm"]],
              "loads": R["loads"]} for net, R in sorted(rails.items(), key=lambda kv: min([l["V_min"] for l in kv[1]["loads"]] or [9]))]
    res = {"skill": NAME, "title": TITLE, "verdict": "INFO", "counts": {"rails": len(table), "loads": sum(len(t["loads"]) for t in table)},
           "image": "VLT_ALL_POWER.png", "scale_mV": [round(lo, 3), round(hi, 3)], "layers": info, "rails": table,
           "note": "information only - no IR-drop spec", "warnings": warns, "seconds": round(time.time() - t0)}
    ctx.save_result(NAME, res)
    return res
