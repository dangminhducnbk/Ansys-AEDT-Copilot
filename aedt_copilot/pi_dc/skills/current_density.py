"""Skill PI-DC: current density (guides/pidc_current_density.md).

Mỗi ảnh CUR_<layer>.png (ALL_POWER + mỗi net nguồn): J theo pixel từ thang màu -> trung bình theo ô vuông
cd_window_mm (chỉ đồng, bỏ ô < cd_min_copper_frac đồng) -> J_avg_max. Nền lớp = trung vị các ô.
Vùng nổi bật: J_avg_max >= cd_warn_frac x limit HOẶC >= cd_bg_factor x nền, tối đa cd_max_regions.
Kết luận theo J_avg_max: FAIL > limit, WARN > cd_warn_frac x limit. Đỉnh 1 điểm (vmax thang màu) chỉ là INFO.
016 đồng mảnh (trace RDL 20-40 µm): không ô cd_window_mm nào đủ đồng (hoặc < 0.05 mm² đồng) -> ô cd_narrow_window_mm,
trung bình J chỉ trên pixel đồng; mảnh đồng < cd_tiny_area_mm2 không xét -> chỉ còn mảnh nhỏ = INFO (không PASS/FAIL).
Không cặp nào được đánh giá -> verdict NO_DATA (không bao giờ PASS với 0 cặp).
"""
from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from scipy import ndimage

from .. import common, imaging

NAME = "current_density"
ORDER = 10
NEEDS_EXPORT = True
TITLE = "Current density"


def _short(layer):
    return {"TOP": "T", "BOTTOM": "B"}.get(layer.upper(), layer.split("_")[0])


def load_pads(base) -> dict:
    """Pad linh kiện lớp ngoài từ <run>.ppb: {layer: [polygon mm]} ('PAD_n TOP_2 POLYGON k' + k dòng toạ độ µm)."""
    out, L, i = {}, open(str(base) + ".ppb", encoding="latin-1").read().splitlines(), 0
    while i < len(L):
        t = L[i].split()
        if len(t) >= 4 and t[2] == "POLYGON":
            k = int(t[3])
            pts = [tuple(float(v) / 1000 for v in L[i + 1 + j].split()[:2]) for j in range(k)]
            out.setdefault(t[1].rsplit("_", 1)[0], []).append(pts)
            i += k + 1
        else:
            i += 1
    return out


def pin_mask(shape, x0, f, calib, pads, keep_px):
    """Mask (theo lưới J) của pad + keep-out: dòng vào/ra chân linh kiện được SIwave đặt vào 1 node -> J ở đó không thật."""
    from PIL import Image as _I, ImageDraw as _D
    m = _I.new("1", (shape[1], shape[0]), 0)
    d = _D.Draw(m)
    for poly in pads:
        pts = [calib.to_px(x, y, f) for x, y in poly]
        d.polygon([(X - x0, Y) for X, Y in pts], fill=1)
    a = np.asarray(m, dtype=bool)
    if keep_px > 0 and a.any():
        a = ndimage.binary_dilation(a, structure=ndimage.generate_binary_structure(2, 2), iterations=int(keep_px))
    return a


def analyse(job, net, layer, png, lim, P, calib, img_out, pads=None):
    t0 = time.time()
    e = {"job": job, "net": net, "layer": layer, "spec": lim, "image_src": str(png)}
    im = imaging.open_rgb(png)
    cb = imaging.read_colorbar(im)
    e.update(vmax=cb["vmax"], vmin=cb["vmin"], ocr_ok=cb["ok"])
    if not cb["ok"]:
        e.update(status="PENDING", reason=f"colour bar OCR failed ({cb['err']})")
        return e
    if cb["vmax"] < 1e-3:
        e.update(status="NO_DATA", reason="no current")
        return e
    r = 1                                                    # phân tích ở độ phân giải gốc (6000 px)
    ia = im.reduce(r) if r > 1 else im
    J, x0 = imaging.jmap(ia, cb["vmin"], cb["vmax"])
    cu = np.isfinite(J)
    ppmm = calib.ppmm * (ia.size[1] / calib.size[1])
    if not cu.any():
        e.update(status="NO_DATA", reason="no copper with current")
        return e
    win_mm, avg = float(P["cd_window_mm"]), None
    if cu.sum() / ppmm ** 2 >= 0.05:                        # >= 0.05 mm² đồng có dòng: cách cũ (ô 0.5 mm)
        n = max(3, int(round(win_mm * ppmm)))
        Jz = np.where(cu, J, 0).astype(np.float32)
        s = ndimage.uniform_filter(Jz, n, mode="constant")
        fr = ndimage.uniform_filter(cu.astype(np.float32), n, mode="constant")
        minf = float(P["cd_min_copper_frac"])
        avg = np.where(fr >= minf, s / np.maximum(fr, 1e-9), np.nan)
        if not np.isfinite(avg).any():                     # chỉ có đồng hẹp hơn ô -> nới 20 %
            avg = np.where(fr >= 0.2, s / np.maximum(fr, 1e-9), np.nan)
            e["narrow_copper"] = True
        if not np.isfinite(avg).any():
            avg = None
    if avg is None:                                        # 016: đồng mảnh / ít -> ô nhỏ, chỉ pixel đồng
        nr = narrow_avg(J, cu, ppmm, P)
        if nr is None:
            e.update(status="INFO", reason=f"only tiny copper (< {float(P['cd_tiny_area_mm2'])} mm2)",
                     copper_mm2=round(float(cu.sum()) / ppmm ** 2, 4), peak_info=cb["vmax"] > lim,
                     peak_util=round(cb["vmax"] / lim, 3))
            _image(e, im, ia, r, [], None, net, layer, job, None, img_out)
            e["seconds"] = round(time.time() - t0, 1)
            return e
        avg, n = nr
        win_mm = float(P["cd_narrow_window_mm"])
        e.update(narrow_window=True, reason=f"narrow copper ({win_mm} mm window)")
    to_mm = lambda X, Y: calib.to_mm((X + x0) * r, Y * r)
    warn, bgf = float(P["cd_warn_frac"]), float(P["cd_bg_factor"])
    # ô nằm trên pad linh kiện (+ keep-out) = node chân linh kiện -> chỉ INFO, không vào kết luận
    pin = None
    if pads:
        pm = pin_mask(avg.shape, x0, ia.size[1] / calib.size[1], calib, pads,
                      round(float(P.get("cd_pin_keepout_mm", 0.25)) * ppmm))
        pav = np.where(pm, avg, np.nan)
        avg = np.where(pm, np.nan, avg)
        if np.isfinite(pav).any() and np.nanmax(pav) > warn * lim:
            pj = float(np.nanmax(pav))
            py, px = np.unravel_index(np.nanargmax(pav), pav.shape)
            lab1, _ = ndimage.label(pm & (np.nan_to_num(pav, nan=0) >= warn * lim))
            sl = ndimage.find_objects(lab1)[lab1[py, px] - 1]
            bx = [(sl[1].start + x0) * r, sl[0].start * r, (sl[1].stop + x0) * r, sl[0].stop * r]
            pin = {"J_avg_max": round(pj, 2), "util": round(pj / lim, 3), "bbox_px": bx,
                   "at_mm": [round(v, 2) for v in to_mm(px, py)], "note": "pin-node artefact (INFO)"}
        e["pin_node"] = pin
        if not np.isfinite(avg).any():
            e.update(status="PASS", reason="only pad copper (pin nodes)", J_avg_max=None, util=None, regions=[],
                     peak_info=cb["vmax"] > lim, peak_util=round(cb["vmax"] / lim, 3))
            avg = None
    if avg is None:
        regs, jmax, bg = [], None, None
    else:
        bg = float(np.nanmedian(avg))
        jmax = float(np.nanmax(avg))
        iy, ix = np.unravel_index(np.nanargmax(avg), avg.shape)
        mx, my = to_mm(ix, iy)
        regs = _regions(avg, lim, warn, bgf, bg, n, x0, r, calib, to_mm, layer, P)
        e.update(status="FAIL" if jmax > lim else ("WARN" if jmax > warn * lim else "PASS"),
                 J_avg_max=round(jmax, 2), util=round(jmax / lim, 3), at_mm=[round(mx, 2), round(my, 2)],
                 background=round(bg, 2), window_mm=win_mm, window_px=n, regions=regs,
                 peak_info=cb["vmax"] > lim, peak_util=round(cb["vmax"] / lim, 3))
    _image(e, im, ia, r, regs, pin, net, layer, job, jmax, img_out)
    e["seconds"] = round(time.time() - t0, 1)
    return e


def narrow_avg(J, cu, ppmm, P):
    """Đồng mảnh: bỏ mảnh đồng < cd_tiny_area_mm2 (8-liên thông); ô cd_narrow_window_mm, J trung bình trên pixel đồng,
    chỉ ô có tỉ lệ đồng >= 1/2 ô phủ đồng nhiều nhất (ô nằm trên trace). -> (avg, n px) hoặc None (chỉ còn mảnh nhỏ)."""
    lab, nl = ndimage.label(cu, structure=np.ones((3, 3), bool))
    if not nl:
        return None
    area = ndimage.sum(cu, lab, np.arange(1, nl + 1)) / ppmm ** 2
    big = np.flatnonzero(area >= float(P["cd_tiny_area_mm2"])) + 1
    keep = np.isin(lab, big)
    if not keep.any():
        return None
    n = max(3, int(round(float(P["cd_narrow_window_mm"]) * ppmm)))
    s = ndimage.uniform_filter(np.where(keep, J, 0).astype(np.float32), n, mode="constant")
    fr = ndimage.uniform_filter(keep.astype(np.float32), n, mode="constant")
    avg = np.where(fr >= 0.5 * float(fr.max()), s / np.maximum(fr, 1e-9), np.nan)
    return avg, n


def _regions(avg, lim, warn, bgf, bg, n, x0, r, calib, to_mm, layer, P):
    thr = min(warn * lim, bgf * bg)
    lab, nl = ndimage.label(ndimage.binary_dilation(np.nan_to_num(avg, nan=0) >= thr, iterations=max(1, n // 2)))
    regs = []
    for i, sl in enumerate(ndimage.find_objects(lab) if nl else [], 1):
        sub = np.where(lab[sl] == i, np.nan_to_num(avg[sl], nan=0), 0)
        jm = float(sub.max())
        if jm >= warn * lim or jm >= bgf * bg:
            yy, xx = np.unravel_index(sub.argmax(), sub.shape)
            bx = [(sl[1].start + x0) * r, sl[0].start * r, (sl[1].stop + x0) * r, sl[0].stop * r]   # px ảnh gốc
            regs.append({"J_avg_max": round(jm, 2), "bbox_px": bx,
                         "at_mm": [round(v, 2) for v in to_mm(sl[1].start + xx, sl[0].start + yy)],
                         "bbox_mm": [round(v, 2) for v in (*calib.to_mm(bx[0], bx[3]), *calib.to_mm(bx[2], bx[1]))],
                         "util": round(jm / lim, 3),
                         "tier": "FAIL" if jm > lim else ("WARN" if jm > warn * lim else "HIGH")})
    regs.sort(key=lambda q: -q["J_avg_max"])
    regs = regs[:int(P["cd_max_regions"])]
    for k, q in enumerate(regs, 1):
        q["id"] = f"{_short(layer)}-R{k}"
    return regs


def _image(e, im, ia, r, regs, pin, net, layer, job, jmax, img_out):
    """Ảnh kiểu báo cáo: khung đỏ = vùng nổi bật; khung xám nét đứt = node chân linh kiện (INFO)."""
    b = imaging.main_box(ia)
    box = [b[0] * r, b[1] * r, b[2] * r, b[3] * r]
    for bx in [q["bbox_px"] for q in regs] + ([pin["bbox_px"]] if pin else []):
        box = [min(box[0], bx[0]), min(box[1], bx[1]), max(box[2], bx[2]), max(box[3], bx[3])]
    cv = imaging.Canvas(im, box)
    for q in regs:
        cv.rect(q["bbox_px"], f"{q['id']}: {q['J_avg_max']:.1f} A/mm²")
    if pin:
        cv.rect_info(pin["bbox_px"], f"pin node (info): {pin['J_avg_max']:.1f} A/mm²")
    if not regs:
        cv.title(f"{net}  {layer}  -  no outstanding region" + (f" (J_avg_max {jmax:.1f} A/mm²)" if jmax else ""))
    else:
        cv.title(f"{net}  {layer}  current density")
    name = f"CD_{'ALL_POWER' if job == 'ALL_POWER' else common.safe(net)}_{layer}.png"
    cv.save(os.path.join(img_out, name))
    e["image"] = name


def verdict(cnt) -> str:
    """FAIL > PENDING > WARN > PASS; 0 cặp được đánh giá (chỉ NO_DATA / INFO) -> NO_DATA, không bao giờ PASS."""
    if cnt.get("FAIL"):
        return "FAIL"
    if cnt.get("PENDING"):
        return "PENDING"
    if cnt.get("WARN"):
        return "WARN"
    return "PASS" if cnt.get("PASS") else "NO_DATA"


def run(ctx, log=print) -> dict:
    t0 = time.time()
    P = ctx.P
    calib = imaging.Calib(imaging.best_ref(ctx), ctx.base.parent / (ctx.base.name + ".outline"))
    ctx.images.mkdir(parents=True, exist_ok=True)
    try:
        pads = load_pads(ctx.base)
    except OSError:
        pads = {}
        log("no .ppb pad file: pin-node exclusion disabled")
    tasks, pending = [], []
    for job, net in [("ALL_POWER", "ALL_POWER")] + [(common.safe(n), n) for n in ctx.power]:
        for lay in ctx.metals:
            png = ctx.cur_png(job, "CUR", lay)
            lim = common.spec(P, lay, ctx.outer)
            if png is None:
                pending.append({"job": job, "net": net, "layer": lay, "spec": lim, "status": "PENDING",
                                "reason": "image not exported"})
            else:
                tasks.append((job, net, lay, str(png), lim, P, calib, str(ctx.images), pads.get(lay)))
    log(f"current density: {len(tasks)} images")
    with ProcessPoolExecutor(max_workers=max(1, min(4, (os.cpu_count() or 2) - 1))) as ex:
        res = list(ex.map(analyse, *zip(*tasks)))
    res += pending
    pairs = [e for e in res if e["job"] != "ALL_POWER"]
    cnt = {k: sum(e["status"] == k for e in pairs) for k in ("FAIL", "WARN", "PENDING", "PASS", "NO_DATA", "INFO")}
    result = {"skill": NAME, "title": TITLE, "calib_ppmm": round(calib.ppmm, 3),
              "params": {k: P[k] for k in P if k.startswith("cd_")},
              "outer_layers": sorted(ctx.outer), "verdict": verdict(cnt), "counts": cnt,
              "all_power": [e for e in res if e["job"] == "ALL_POWER"], "pairs": pairs,
              "seconds": round(time.time() - t0)}
    ctx.save_result(NAME, result)
    return result

