"""Luật GND ở 2 đầu khi cắt (feature 022, contract: specs/022-cut-keeps-end-gnd/contracts/end-gnd.md).

Bước 1: phát hiện pin GND (pin trên cutout.reference_nets, gồm exposed pad) của mỗi đầu trên board gốc.
Cả interface cắt với hệ số của kỹ sư (cutout.expansion). Đầu có pin GND nhưng không pin nào NẰM TRỌN trong vùng cutout
-> CHỈ vùng đầu (khung pin + cutout.end_region_margin_mm) được mở rộng: hệ số + cutout.end_expansion_step mỗi lần,
KHÔNG có mức tối đa, tới khi có 1 pin GND nằm trọn. Vùng đầu chứa mọi pin nên vòng lặp luôn dừng; phủ hết vùng mà vẫn
không có -> lỗi hình học (nêu đầu + pin). Đầu không có pin GND trên board -> không mở rộng, câu hỏi 015 như cũ.
Hàm thuần dùng shapely, đơn vị mm.
"""
import os

MM = 1e-3
TOL = 1e-6                                                          # mm


def params(P):
    c = P["cutout"]
    return {"base": float(c["expansion"]), "step": float(c.get("end_expansion_step") or 0.02),
            "margin_mm": float(c["end_region_margin_mm"]) if c.get("end_region_margin_mm") is not None else 1.0,
            "unitless": bool(c.get("expansion_unitless", True))}


MAX_TRIES = 500                                                     # chặn an toàn (hình học lỗi), không phải luật


def factor(base, step, k):
    """Hệ số lần thử k (1, 2 ...) = base + k*step. Thuần."""
    return round(base + k * step, 6)


def covers(pts, region_box):
    """Vùng cutout phủ trọn vùng đầu. Thuần."""
    return fully_inside(pts, region_box)


def region(body_mm, margin_mm):
    x0, y0, x1, y1 = body_mm
    return [x0 - margin_mm, y0 - margin_mm, x1 + margin_mm, y1 + margin_mm]


def _poly(pts):
    from shapely.geometry import Polygon
    return Polygon([tuple(q) for q in pts]).buffer(0)


def fully_inside(extent_mm, box_mm):
    """Khung pad (mm) nằm trọn trong vùng cutout. Thuần."""
    from shapely.geometry import box
    return _poly(extent_mm).buffer(TOL).contains(box(*box_mm))


def grow(extent_mm, ext_f_mm, region_box):
    """extent ∪ (ext_f ∩ vùng đầu) -> (điểm, đa giác thêm, mm2 thêm); không còn 1 đa giác -> None. Thuần.
    Ngoài vùng đầu, kết quả = extent (SC-002)."""
    from shapely.geometry import box
    E = _poly(extent_mm)
    U = E.union(_poly(ext_f_mm).intersection(box(*region_box)))
    if U.geom_type != "Polygon":
        return None
    add = U.difference(E)
    polys = [add] if add.geom_type == "Polygon" else [g for g in getattr(add, "geoms", []) if g.geom_type == "Polygon"]
    added = [[[round(x, 4), round(y, 4)] for x, y in list(g.exterior.coords)[:-1]] for g in polys if g.area > 1e-9]
    return [(x, y) for x, y in list(U.exterior.coords)[:-1]], added, round(add.area, 4)


# ----------------------------------------------------------------------------- EDB (chỉ đọc)
def gnd_pads(comp, refs, extent_mm):
    """-> (pin nằm trọn hoặc None, [{pin, pad_mm}] mọi pin GND khi chưa có pin nằm trọn).
    Pin có tâm trong vùng cutout đọc trước, dừng ở pin đầu tiên nằm trọn (BGA nhiều pin GND: bounding_box chậm)."""
    from shapely.geometry import Point
    E = _poly(extent_mm).buffer(TOL)
    gp = [p for p in comp.pins.values() if p.net_name in refs]
    if not gp:
        return None, []
    first = sorted(gp, key=lambda p: not E.contains(Point(p.position[0] / MM, p.position[1] / MM)))
    pads = []
    for p in first:
        (x0, y0), (x1, y1) = p.bounding_box
        b = [x0 / MM, y0 / MM, x1 / MM, y1 / MM]
        if fully_inside(extent_mm, b):
            return str(p.pin_number), []
        pads.append({"pin": str(p.pin_number), "pad_mm": [round(v, 4) for v in b]})
    return None, pads


def nets_in(edb, polys_mm, keep_nets):
    """Net khác (ngoài keep_nets) có via / primitive chạm các đa giác (mm). Chỉ đọc."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    A = unary_union([Polygon([tuple(q) for q in p]).buffer(0) for p in polys_mm if len(p) >= 3])
    if A.is_empty:
        return []
    ax0, ay0, ax1, ay1 = A.bounds
    other = set()
    for v in edb.padstacks.instances.values():
        n = v.net_name
        if not n or n in keep_nets or n in other:
            continue
        x, y = v.position[0] / MM, v.position[1] / MM
        if ax0 <= x <= ax1 and ay0 <= y <= ay1 and A.intersects(Point(x, y)):
            other.add(n)
    from ..core.geometry_edb import prim_points
    for pr in edb.modeler.primitives:
        try:
            n = pr.net_name
            if not n or n in keep_nets or n in other:
                continue
            b = pr.bbox
            if b[2] / MM < ax0 or b[0] / MM > ax1 or b[3] / MM < ay0 or b[1] / MM > ay1:
                continue
            if Polygon([(x / MM, y / MM) for x, y in prim_points(pr)]).buffer(0).intersects(A):
                other.add(n)
        except Exception:
            continue
    return sorted(other)


def _pin_key(n):
    return (0, int(n), "") if str(n).isdigit() else (1, 0, str(n))


def _body(comp):
    xs, ys = [], []
    for p in comp.pins.values():
        (x0, y0), (x1, y1) = p.bounding_box
        xs += [x0, x1]
        ys += [y0, y1]
    return [min(xs) / MM, min(ys) / MM, max(xs) / MM, max(ys) / MM]


def validate_end_factors(end_factors, ends):
    """Hệ số tay từng đầu (022 US5): {refdes: số > 0 | '' | None} -> ({refdes: float}, lỗi[]). Trống = tự động. Thuần."""
    out, err = {}, []
    if end_factors in (None, ""):
        return out, err
    if not isinstance(end_factors, dict):
        return out, [f"cutout.end_factor: JSON object {{refdes: factor}}, got {end_factors!r}"]
    for rd, v in end_factors.items():
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        k = f"cutout.end_factor.{rd}"
        if rd not in ends:
            err.append(f"{k}: not an end of this interface ({', '.join(ends)})")
            continue
        try:
            f = float(v)
            if isinstance(v, bool) or not f > 0:
                raise ValueError
        except (TypeError, ValueError):
            err.append(f"{k}: phải là số > 0 (cùng đơn vị với cutout.expansion), got {v!r}")
            continue
        out[rd] = round(f, 6)
    return out, err


def replace_region(extent_mm, ext_f_mm, region_box):
    """Hệ số tay: (extent − vùng đầu) ∪ (ext_f ∩ vùng đầu) -> (điểm, đa giác thêm, mm2 thêm, mm2 bớt) | None. Thuần."""
    from shapely.geometry import box
    E, R_ = _poly(extent_mm), box(*region_box)
    U = E.difference(R_).union(_poly(ext_f_mm).intersection(R_))
    if U.geom_type != "Polygon":
        return None
    add = U.difference(E)
    polys = [add] if add.geom_type == "Polygon" else [g for g in getattr(add, "geoms", []) if g.geom_type == "Polygon"]
    added = [[[round(x, 4), round(y, 4)] for x, y in list(g.exterior.coords)[:-1]] for g in polys if g.area > 1e-9]
    return ([(x, y) for x, y in list(U.exterior.coords)[:-1]], added, round(add.area, 4),
            round(E.difference(U).area, 4))


def all_gnd_pads(comp, refs):
    """Mọi pin GND của linh kiện -> [{pin, pad_mm}] (đọc bounding_box: chậm trên BGA lớn, chỉ dùng khi cần)."""
    out = []
    for p in comp.pins.values():
        if p.net_name in refs:
            (x0, y0), (x1, y1) = p.bounding_box
            out.append({"pin": str(p.pin_number), "pad_mm": [round(v, 4) for v in (x0 / MM, y0 / MM, x1 / MM, y1 / MM)]})
    return out


def apply_rule(edb, P, nets, ends, pts, extent_fn, log=print, body_fn=None, manual=None, strict=True):
    """-> (điểm extent cuối, info). extent_fn(factor) -> điểm mm (cache theo hệ số, 2 đầu dùng chung).
    body_fn(comp) -> khung mm (mặc định khung các pad pin). manual {refdes: hệ số} (022 US5): dùng đúng hệ số đó cho
    vùng đầu (không tăng dần), phải còn pin GND nằm trọn. strict=False (preview): lỗi ghi vào đầu + info['errors']."""
    pr = params(P)
    refs = set(P["cutout"]["reference_nets"])
    keep_nets = set(nets) | refs
    manual = manual or {}
    cache = {}

    def ext(f):
        if f not in cache:
            cache[f] = extent_fn(f)
        return cache[f]
    info = {"base_factor": pr["base"], "step": pr["step"], "margin_mm": pr["margin_mm"],
            "unitless": pr["unitless"], "base_pts_mm": [[round(x, 6), round(y, 6)] for x, y in pts], "ends": {},
            "errors": []}
    if manual:
        info["manual"] = dict(manual)
    cur = pts

    def fail(e, msg):
        if strict:
            raise RuntimeError(msg)
        e.update(result="error", error=msg)
        info["errors"].append(msg)
        log("  " + msg)
    for rd in ends:
        comp = edb.components.instances[rd]
        det = sorted((str(p.pin_number) for p in comp.pins.values() if p.net_name in refs), key=_pin_key)
        e = {"result": "met", "gnd_pins_on_board": len(det), "gnd_pins_detected": det[:30], "factor": pr["base"],
             "tries": 0, "region_mm": None, "added_mm2": 0.0, "added_mm": [], "gnd_pins_gained": [],
             "gnd_pin_inside": None, "other_nets": []}
        info["ends"][rd] = e
        if rd in manual:                                                # 022 US5: hệ số tay, dùng đúng giá trị
            f = manual[rd]
            e["factor"] = f
            if not det:
                fail(e, f"end factor {rd}: {rd} has no GND pin on the board: leave its end factor empty")
                continue
            hit, _ = gnd_pads(comp, refs, cur)
            pads = all_gnd_pads(comp, refs)
            reg = region((body_fn or _body)(comp), pr["margin_mm"])
            e.update(region_mm=[round(v, 4) for v in reg], gnd_pads_mm=pads[:50], base_inside=bool(hit), tries=1)
            g = replace_region(cur, ext(f), reg)
            got = [q for q in pads if g and fully_inside(g[0], q["pad_mm"])]
            if not got:
                fail(e, f"end factor {rd} = {f} leaves no GND pin / pad fully inside the cut extent "
                        f"(GND pins {', '.join(det[:10])}): raise it or clear it (automatic)")
                continue
            npts, added, area, removed = g
            e.update(result="manual", added_mm2=area, removed_mm2=removed, added_mm=added,
                     gnd_pins_gained=[q for q in got if q["pin"] != hit] if hit else got,
                     gnd_pin_inside=got[0]["pin"], other_nets=nets_in(edb, added, keep_nets))
            cur = npts
            log(f"  {rd}: hệ số tay {f}: +{area} mm2 / -{removed} mm2, pin GND {[q['pin'] for q in got]}")
            continue
        if not det:                                                     # bước 1: không có pin GND trên board
            e.update(result="no_gnd_pin_on_board", factor=None)
            log(f"  {rd}: không có pin GND trên board -> câu hỏi GND (015)")
            continue
        hit, pads = gnd_pads(comp, refs, cur)
        if hit:
            e["gnd_pin_inside"] = hit
            continue
        reg = region((body_fn or _body)(comp), pr["margin_mm"])
        e.update(region_mm=[round(v, 4) for v in reg], gnd_pads_mm=pads[:50])
        done, last = None, cur
        for k in range(1, MAX_TRIES + 1):
            f = factor(pr["base"], pr["step"], k)
            e["tries"] = k
            g = grow(cur, ext(f), reg)
            if g is None:
                continue
            last = g[0]
            got = [q for q in pads if fully_inside(g[0], q["pad_mm"])]
            if got:
                done = (f, g, got)
                break
            if covers(g[0], reg):
                break
        if not done:
            how = "fully covered" if covers(last, reg) else f"not covered after {e['tries']} tries"
            fail(e, f"end GND rule: {rd} has GND pin(s) {', '.join(q['pin'] for q in pads[:10])} but none "
                    f"lies fully inside the cut extent; end region {e['region_mm']} mm {how} "
                    f"(geometry error: check the pad shapes of {rd})")
            continue
        f, (npts, added, area), got = done
        e.update(result="enlarged", factor=f, added_mm2=area, added_mm=added, gnd_pins_gained=got,
                 gnd_pin_inside=got[0]["pin"], other_nets=nets_in(edb, added, keep_nets))
        cur = npts
        log(f"  {rd}: vùng đầu hệ số {pr['base']} -> {f}, +{area} mm2, pin GND {[q['pin'] for q in got]}"
            f", net khác trong phần thêm: {e['other_nets'] or 'none'}")
    return cur, info


# ----------------------------------------------------------------------------- preview (022 US4): cảnh + ảnh
def scene(edb, P, nets, ends, series, info, pts):
    """EDB (chỉ đọc) -> cảnh JSON (mm) cho ảnh vùng cut: tín hiệu, linh kiện, pin GND đầu, net khác vùng thêm."""
    from shapely.geometry import Point, Polygon, box
    from shapely.ops import unary_union
    from .cutter import is_bga_or_th
    from ..core.geometry_edb import prim_points
    refs = set(P["cutout"]["reference_nets"])
    nets = set(nets)
    F = _poly(pts)
    fx0, fy0, fx1, fy1 = F.bounds
    sc = {"base_pts": info.get("base_pts_mm"), "final_pts": [[round(x, 4), round(y, 4)] for x, y in pts],
          "signal": [], "vias": [], "gnd_vias": [], "comps": [], "gnd_pins": [], "other": [], "ends": {}}
    added = []
    for rd, e in (info.get("ends") or {}).items():
        sc["ends"][rd] = {k: e.get(k) for k in ("result", "factor", "added_mm2", "region_mm", "added_mm", "error")}
        added += [Polygon(q) for q in e.get("added_mm") or [] if len(q) >= 3]
    A = unary_union([g.buffer(0) for g in added]) if added else None
    for rd in list(ends) + [r for r in series if r not in ends]:
        c = edb.components.instances.get(rd) if hasattr(edb.components.instances, "get") else \
            edb.components.instances[rd]
        if c is None:
            continue
        try:
            sc["comps"].append({"refdes": rd, "box": [round(v, 4) for v in _body(c)], "end": rd in ends})
        except Exception:
            pass
        if rd not in ends:
            continue
        bga = is_bga_or_th(c, nets)
        for p in c.pins.values():
            if p.net_name not in refs:
                continue
            x, y = p.position[0] / MM, p.position[1] / MM
            if bga:
                sc["gnd_pins"].append({"refdes": rd, "pin": str(p.pin_number), "xy": [round(x, 4), round(y, 4)],
                                       "kept": F.buffer(TOL).contains(Point(x, y))})
            else:
                (x0, y0), (x1, y1) = p.bounding_box
                b = [x0 / MM, y0 / MM, x1 / MM, y1 / MM]
                sc["gnd_pins"].append({"refdes": rd, "pin": str(p.pin_number), "box": [round(v, 4) for v in b],
                                       "kept": F.buffer(TOL).contains(box(*b))})
    ax = A.bounds if A is not None and not A.is_empty else None
    names = {}
    for pr in edb.modeler.primitives:
        try:
            n = pr.net_name
            if not n:
                continue
            b = pr.bbox
            bx = (b[0] / MM, b[1] / MM, b[2] / MM, b[3] / MM)
            if n in nets:
                if bx[2] < fx0 - 1 or bx[0] > fx1 + 1 or bx[3] < fy0 - 1 or bx[1] > fy1 + 1:
                    continue
                sc["signal"].append([[round(x / MM, 4), round(y / MM, 4)] for x, y in prim_points(pr)])
            elif n not in refs and ax and not (bx[2] < ax[0] or bx[0] > ax[2] or bx[3] < ax[1] or bx[1] > ax[3]):
                g = Polygon([(x / MM, y / MM) for x, y in prim_points(pr)]).buffer(0).intersection(A)
                for q in ([g] if g.geom_type == "Polygon" else getattr(g, "geoms", [])):
                    if q.geom_type == "Polygon" and q.area > 1e-4:
                        sc["other"].append({"net": n, "pts": [[round(x, 4), round(y, 4)]
                                                              for x, y in list(q.exterior.coords)[:-1]]})
                        names[n] = names.get(n, 0) + q.area
        except Exception:
            continue
    gv = []
    for v in edb.padstacks.instances.values():
        try:
            n = v.net_name
            if n not in nets and n not in refs:
                continue
            x, y = v.position[0] / MM, v.position[1] / MM
            if not (fx0 - 1 <= x <= fx1 + 1 and fy0 - 1 <= y <= fy1 + 1):
                continue
            if n in nets:
                sc["vias"].append([round(x, 4), round(y, 4)])
            elif not v.is_pin and F.buffer(TOL).contains(Point(x, y)):
                gv.append((x, y))
        except Exception:
            continue
    # via GND (đường hồi tiếp): trong pad GND giữ được / vùng đầu, hoặc gần via tín hiệu (<= cleanup.gnd_via_keep_dist_mm)
    near = float((P.get("cleanup") or {}).get("gnd_via_keep_dist_mm") or 1.0)
    regs = [e["region_mm"] for e in (info.get("ends") or {}).values() if e.get("region_mm")]
    sig = sc["vias"]
    for x, y in gv:
        in_reg = any(r[0] <= x <= r[2] and r[1] <= y <= r[3] for r in regs)
        if in_reg or any((x - a) ** 2 + (y - b) ** 2 <= near * near for a, b in sig):
            sc["gnd_vias"].append([round(x, 4), round(y, 4)])
    sc["other_names"] = [n for n, _ in sorted(names.items(), key=lambda t: -t[1])]
    return sc


def _dash(d, a, b, col, width=1, on=6, off=4):
    import math as _m
    (x0, y0), (x1, y1) = a, b
    L = _m.hypot(x1 - x0, y1 - y0)
    if L <= 0:
        return
    t = 0.0
    while t < L:
        t1 = min(L, t + on)
        d.line([x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L, x0 + (x1 - x0) * t1 / L, y0 + (y1 - y0) * t1 / L],
               fill=col, width=width)
        t += on + off


def _bounds(sc):
    """Khung mm của vùng cut: extent nền / cuối + vùng đầu (khung linh kiện lớn như BGA không kéo rộng ảnh)."""
    xs, ys = [], []
    for pts in (sc.get("final_pts"), sc.get("base_pts")):
        for q in pts or []:
            xs.append(q[0])
            ys.append(q[1])
    for b in [e.get("region_mm") for e in (sc.get("ends") or {}).values()]:
        if b:
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 1, 1)


def _label(d, xy, text, font, fill=(0, 0, 0)):
    """Chữ có nền trắng (đọc được trên đường mạch)."""
    try:
        bb = d.textbbox(xy, text, font=font)
        d.rectangle([bb[0] - 2, bb[1] - 1, bb[2] + 2, bb[3] + 1], fill=(255, 255, 255))
    except Exception:
        pass
    d.text(xy, text, fill=fill, font=font)


OTHER_HATCH, OTHER_LINE, HATCH_STEP = (110, 110, 110), (70, 70, 70), 9   # 2.1.2: net khác gạch chéo xám + viền đậm
LEGEND = (("signal", "Signal"), ("final", "Cut region"), ("base", "Base cut"), ("added", "Added"),
          ("region", "End region"), ("gnd_pin", "GND pin"), ("gnd_via", "GND via"), ("other", "Other net"))


def final_scene(sc):
    """035: cảnh của VÙNG CUT CUỐI (phần tăng thêm đã gộp; không nét nền, không vùng thêm, không net khác - net khác
    trong phần thêm không được giữ khi cut). Thuần, không đổi sc."""
    import copy
    f = copy.deepcopy(sc)
    f["base_pts"] = None
    f["other"] = []
    f["other_names"] = []
    for e in (f.get("ends") or {}).values():
        e["added_mm"] = []
        e["region_mm"] = None
    return f


def legend_items(sc):
    """Mục chú thích có mặt trong ảnh (2.1.1: chỉ vẽ mục có; 035: 'Cut region' khi chỉ vẽ vùng cuối). Thuần."""
    ends = (sc.get("ends") or {}).values()
    have = {"signal": bool(sc.get("signal") or sc.get("vias")),
            "final": bool(sc.get("final_pts")) and not sc.get("base_pts"), "base": bool(sc.get("base_pts")),
            "added": any(e.get("added_mm") for e in ends), "region": any(e.get("region_mm") for e in ends),
            "gnd_pin": bool(sc.get("gnd_pins")), "gnd_via": bool(sc.get("gnd_vias")), "other": bool(sc.get("other"))}
    return [(k, t) for k, t in LEGEND if have[k]]


def _swatch(d, k, x, y):
    """Ô màu 26 x 14 px của mục chú thích k tại (x, y)."""
    if k == "signal":
        d.rectangle([x, y + 3, x + 26, y + 11], fill=(214, 39, 40))
    elif k == "final":
        d.line([x, y + 7, x + 26, y + 7], fill=(44, 160, 44), width=3)
    elif k == "base":
        _dash(d, (x, y + 7), (x + 26, y + 7), (60, 60, 60), width=3, on=7, off=4)
    elif k == "added":
        d.rectangle([x, y, x + 26, y + 14], fill=(170, 220, 170), outline=(44, 160, 44))
    elif k == "region":
        d.rectangle([x, y, x + 26, y + 14], outline=None)
        for a, b in (((x, y), (x + 26, y)), ((x + 26, y), (x + 26, y + 14)), ((x + 26, y + 14), (x, y + 14)),
                     ((x, y + 14), (x, y))):
            _dash(d, a, b, (0, 0, 0), width=1, on=4, off=3)
    elif k == "gnd_pin":
        d.rectangle([x + 4, y, x + 22, y + 14], fill=(31, 119, 180))
    elif k == "gnd_via":
        d.ellipse([x + 7, y + 1, x + 19, y + 13], fill=(90, 160, 230), outline=(10, 40, 90))
    elif k == "other":                                                  # cùng kiểu gạch chéo như trên ảnh
        for t in range(-14, 26, HATCH_STEP):
            a0 = max(t, 0)
            a1 = min(t + 14, 26)
            d.line([x + a0, y + 14 - (a0 - t), x + a1, y + 14 - (a1 - t)], fill=OTHER_HATCH, width=1)
        d.rectangle([x, y, x + 26, y + 14], outline=OTHER_LINE)


def render_scene(sc, path, view=None, title=None, px=1400):
    """Cảnh -> PNG (PIL, thuần). view [x0, y0, x1, y1] mm (None = vùng cut + vùng đầu + 2 mm). Trả path.
    2.1.1: ít chữ - tiêu đề 1 dòng, chú thích = ô màu ở chân ảnh cạnh thước, nhãn '<refdes> <hệ số>', net khác chỉ tô
    xám (tên net ở bảng preview / preview.json)."""
    from PIL import Image, ImageDraw
    from .gnd_decision import _font
    bx = _bounds(sc)
    fp = sc.get("final_pts") or sc.get("base_pts")
    W_mm, H_mm = (bx[2] - bx[0], bx[3] - bx[1])
    if fp:
        W_mm, H_mm = max(q[0] for q in fp) - min(q[0] for q in fp), max(q[1] for q in fp) - min(q[1] for q in fp)
    m = 2.0
    x0, y0, x1, y1 = view or (bx[0] - m, bx[1] - m, bx[2] + m, bx[3] + m)
    w = px
    h = max(400, min(4 * px, int(px * (y1 - y0) / max(x1 - x0, 1e-6))))
    top, foot = 34, 46
    sx, sy = w / (x1 - x0), h / (y1 - y0)
    im = Image.new("RGB", (w, top + h + foot), (255, 255, 255))
    d = ImageDraw.Draw(im)

    def T(x, y):
        return (x - x0) * sx, top + (y1 - y) * sy

    def poly(q, **kw):
        if len(q) >= 3:
            d.polygon([T(x, y) for x, y in q], **kw)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))                       # phần thêm: xanh lá bán trong suốt
    od = ImageDraw.Draw(ov)
    for rd, e in (sc.get("ends") or {}).items():
        for q in e.get("added_mm") or []:
            if len(q) >= 3:
                od.polygon([T(x, y) for x, y in q], fill=(60, 190, 60, 90), outline=(44, 160, 44, 255))
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    others = [[T(x, y) for x, y in o["pts"]] for o in sc.get("other") or [] if len(o["pts"]) >= 3]
    if others:                                                          # 2.1.2: net khác = gạch chéo + viền, KHÔNG tô
        mask = Image.new("L", im.size, 0)                               # -> phần thêm vẫn xanh bên dưới
        md = ImageDraw.Draw(mask)
        for q in others:
            md.polygon(q, fill=255)
        hatch = Image.new("L", im.size, 0)
        hd = ImageDraw.Draw(hatch)
        for k in range(-im.size[1], im.size[0], HATCH_STEP):
            hd.line([k, im.size[1], k + im.size[1], 0], fill=255, width=1)
        from PIL import ImageChops
        im.paste(OTHER_HATCH, mask=ImageChops.multiply(mask, hatch))
        d = ImageDraw.Draw(im)
        for q in others:
            d.line(q + q[:1], fill=OTHER_LINE, width=1)
    d = ImageDraw.Draw(im)
    for q in sc.get("signal") or []:
        poly(q, fill=(214, 39, 40))
    for x, y in sc.get("vias") or []:
        cx, cy = T(x, y)
        r = max(2, 0.15 * sx)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(214, 39, 40), outline=(120, 0, 0))
    for g in sc.get("gnd_pins") or []:
        out = (214, 39, 40) if not g["kept"] else (31, 119, 180)
        if g.get("box"):
            a0, b0, a1, b1 = g["box"]
            d.rectangle([*T(a0, b1), *T(a1, b0)], fill=(31, 119, 180), outline=out, width=1 if g["kept"] else 3)
        else:
            cx, cy = T(*g["xy"])
            r = max(2, 0.12 * sx)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(31, 119, 180), outline=out, width=1 if g["kept"] else 2)
    for x, y in sc.get("gnd_vias") or []:                               # via GND: đường hồi tiếp
        cx, cy = T(x, y)
        r = max(2.5, 0.12 * sx)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(90, 160, 230), outline=(10, 40, 90), width=1)
    if sc.get("final_pts"):
        q = [T(x, y) for x, y in sc["final_pts"]]
        d.line(q + q[:1], fill=(44, 160, 44), width=2 if sc.get("base_pts") else 3)   # 035: vùng cuối đậm hơn
    if sc.get("base_pts"):                                              # extent nền: nét đứt xám đậm, trên cùng
        q = [T(x, y) for x, y in sc["base_pts"]]
        for a, b in zip(q, q[1:] + q[:1]):
            _dash(d, a, b, (60, 60, 60), width=3, on=10, off=6)
    for c in sc.get("comps") or []:                                     # khung linh kiện cắt theo mép vùng vẽ
        a0, b0, a1, b1 = c["box"]
        (u0, v0), (u1, v1) = T(a0, b1), T(a1, b0)
        u0, v0, u1, v1 = max(u0, 1), max(v0, top + 1), min(u1, w - 2), min(v1, top + h - 2)
        if u1 <= u0 or v1 <= v0:
            continue
        d.rectangle([u0, v0, u1, v1], outline=(0, 0, 0), width=2 if c["end"] else 1)
        _label(d, (u0 + 3, v0 + 3), c["refdes"], _font(14 if c["end"] else 12))
    for rd, e in (sc.get("ends") or {}).items():
        r = e.get("region_mm")
        if not r:
            continue
        p0, p1, p2, p3 = T(r[0], r[3]), T(r[2], r[3]), T(r[2], r[1]), T(r[0], r[1])
        for a, b in ((p0, p1), (p1, p2), (p2, p3), (p3, p0)):
            _dash(d, a, b, (0, 0, 0))
        if e.get("result") in ("enlarged", "manual"):
            lab, col = f"{rd} {e.get('factor')}", (20, 100, 20)
        elif e.get("result") == "error":
            lab, col = f"{rd} error", (200, 0, 0)
        else:
            lab = None
        if lab:
            _label(d, (max(2, min(p0[0], w - 120)), max(top + 2, p0[1] - 20)), lab, _font(15), fill=col)
    d.rectangle([0, 0, w, top - 2], fill=(245, 245, 245))
    head = (title or "Cut preview") if view else f"{title or 'Cut preview'} · {W_mm:.0f} × {H_mm:.0f} mm"
    d.text((8, 7), head, fill=(0, 0, 0), font=_font(17))
    fy = top + h                                                        # chân ảnh: thước + chú thích màu
    d.rectangle([0, fy, w, fy + foot], fill=(248, 248, 248))
    d.line([0, fy, w, fy], fill=(200, 200, 200))
    mmv = next((v for v in (1, 2, 5, 10, 20, 50) if v * sx >= 60), 50)
    bar = mmv * sx
    d.line([12, fy + 30, 12 + bar, fy + 30], fill=(0, 0, 0), width=3)
    d.text((12, fy + 8), f"{mmv} mm", fill=(0, 0, 0), font=_font(13))
    x = 36 + bar
    for k, t in legend_items(sc):
        _swatch(d, k, x, fy + 16)
        d.text((x + 32, fy + 15), t, fill=(40, 40, 40), font=_font(13))
        x += 32 + 8 * len(t) + 22
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    im.save(path)
    return path


# ----------------------------------------------------------------------------- báo cáo
def end_entry(s1, rd):
    """Mục end_gnd của đầu rd từ stage1 (dict). stage1 trước 2.1.0 -> result cut_before_2.1.0."""
    eg = (s1 or {}).get("end_gnd")
    if not eg:
        return {"result": "cut_before_2.1.0"}
    e = dict((eg.get("ends") or {}).get(rd) or {"result": "not_checked"})
    e["base_factor"] = eg.get("base_factor")
    return e


def text(e):
    """Mô tả 1 dòng. Thuần."""
    r = e.get("result")
    if r == "enlarged":
        pins = ", ".join(p["pin"] for p in e.get("gnd_pins_gained") or [])
        return (f"{e.get('gnd_pins_on_board', '?')} GND pin(s) on board; factor {e.get('base_factor')} -> "
                f"{e.get('factor')}, +{e.get('added_mm2')} mm2, GND pin {pins} kept")
    if r == "met":
        return (f"{e.get('gnd_pins_on_board', '?')} GND pin(s) on board; pin {e.get('gnd_pin_inside')} inside at "
                f"factor {e.get('base_factor')}")
    if r == "no_gnd_pin_on_board":
        return "no GND pin detected on the board -> GND question"
    if r == "manual":
        pins = ", ".join(p["pin"] for p in e.get("gnd_pins_gained") or []) or e.get("gnd_pin_inside")
        return (f"{e.get('gnd_pins_on_board', '?')} GND pin(s) on board; manual factor {e.get('factor')}, "
                f"+{e.get('added_mm2')} mm2, GND pin {pins} inside")
    if r == "error":
        return "error: " + str(e.get("error"))
    if r == "cut_before_2.1.0":
        return "cut before 2.1.0: cut again to apply the end GND rule"
    return str(r)


def md_rows(ends_entries, images=None):
    """[[Refdes, Result, GND pins on board, Base, Factor used, Added mm2, GND pin gained, Other nets, Image]]."""
    images = images or {}
    rows = []
    for rd, e in sorted(ends_entries.items()):
        det = e.get("gnd_pins_detected") or []
        on = e.get("gnd_pins_on_board")
        on = f"{on} ({', '.join(det[:5])}{' ...' if len(det) > 5 else ''})" if on else (on if on is not None else "-")
        rows.append([rd, e.get("result"), on, e.get("base_factor", "-"), e.get("factor") if e.get("factor") is not None
                     else "-", e.get("added_mm2", "-") if e.get("result") == "enlarged" else "-",
                     ", ".join(p["pin"] for p in e.get("gnd_pins_gained") or []) or (e.get("gnd_pin_inside") or "-"),
                     ", ".join(e.get("other_nets") or []) or "-", images.get(rd) or ""])
    return rows


HEADER = ["Refdes", "Result", "GND pins on board", "Base factor", "Factor used", "Added mm2", "GND pin / pad", "Other nets in added area "
          "(not kept)", "Image"]


def render(rd, e, base_pts, final_pts, path, px=900):
    """Ảnh PNG vùng đầu (PIL): extent gốc (xám), phần thêm (xanh lá nhạt), extent cuối (xanh lá), vùng đầu (chấm),
    pad GND được giữ (viền xanh lá), pad GND khác (viền xám). Trả path."""
    from PIL import Image, ImageDraw
    from .gnd_decision import _font
    reg = e.get("region_mm")
    if not reg:
        return None
    x0, y0, x1, y1 = reg[0] - 1, reg[1] - 1, reg[2] + 1, reg[3] + 1
    w = px
    h = max(300, int(px * (y1 - y0) / max(x1 - x0, 1e-6)))
    top = 46
    s = w / (x1 - x0)
    im = Image.new("RGB", (w, h + top), (255, 255, 255))
    d = ImageDraw.Draw(im)

    def T(x, y):
        return (x - x0) * s, top + (y1 - y) * (h / (y1 - y0))
    for poly in e.get("added_mm") or []:
        if len(poly) >= 3:
            d.polygon([T(x, y) for x, y in poly], fill=(200, 235, 200))
    for pts, col in ((base_pts, (150, 150, 150)),
                     (final_pts if e.get("result") in ("enlarged", "manual") else None, (44, 160, 44))):
        if pts:
            q = [T(x, y) for x, y in pts]
            d.line(q + q[:1], fill=col, width=2)
    a, b = T(reg[0], reg[3]), T(reg[2], reg[1])
    for i in range(int(a[0]), int(b[0]), 10):
        d.line([i, a[1], i + 4, a[1]], fill=(0, 0, 0))
        d.line([i, b[1], i + 4, b[1]], fill=(0, 0, 0))
    for j in range(int(a[1]), int(b[1]), 10):
        d.line([a[0], j, a[0], j + 4], fill=(0, 0, 0))
        d.line([b[0], j, b[0], j + 4], fill=(0, 0, 0))
    gained = {p["pin"] for p in e.get("gnd_pins_gained") or []}
    for p in e.get("gnd_pads_mm") or []:
        p0, q0, p1, q1 = p["pad_mm"]
        d.rectangle([*T(p0, q1), *T(p1, q0)], outline=(44, 160, 44) if p["pin"] in gained else (120, 120, 120),
                    width=3 if p["pin"] in gained else 1)
    d.rectangle([0, 0, w, top - 2], fill=(245, 245, 245))
    d.text((6, 4), f"{rd}  end GND rule: {e.get('result')}  - {text(e)}", fill=(0, 0, 0), font=_font(15))
    d.text((6, 24), "grey = base cut extent | green fill = added area | green line = extent used | dotted = end region"
                    f" (body + {e.get('margin_mm', '')} mm) | other nets: {', '.join(e.get('other_nets') or []) or 'none'}",
           fill=(60, 60, 60), font=_font(12))
    bar = 1.0 * s
    d.line([w - 20 - bar, h + top - 16, w - 20, h + top - 16], fill=(0, 0, 0), width=3)
    d.text((w - 20 - bar, h + top - 34), "1 mm", fill=(0, 0, 0), font=_font(13))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    im.save(path)
    return path


def images(s1, out_dir):
    """Ảnh end_gnd_<rd>.png cho đầu enlarged từ stage1 -> {rd: path}."""
    eg = (s1 or {}).get("end_gnd") or {}
    out = {}
    for rd, e in (eg.get("ends") or {}).items():
        if e.get("result") in ("enlarged", "manual") and e.get("region_mm"):
            e2 = dict(e, base_factor=eg.get("base_factor"), margin_mm=eg.get("margin_mm"))
            try:
                out[rd] = render(rd, e2, eg.get("base_pts_mm"), s1.get("extent_pts_mm"),
                                 os.path.join(out_dir, f"end_gnd_{rd}.png"))
            except Exception as ex:                                     # ảnh không chặn end check
                out[rd] = None
                e2["image_error"] = str(ex)
    return out

