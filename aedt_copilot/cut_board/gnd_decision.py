"""Đầu không có pin GND (feature 015): code đo + liệt kê các cách làm được + vẽ ảnh; NGƯỜI DÙNG chọn.

Dùng chung cho cutter (dựng lại SMD), end check (interface sim, design tool) và propose (luồng Excel), để hình chữ nhật
đề xuất trong ảnh đúng bằng hình apply sẽ vẽ (contract: specs/015-no-gnd-end-decision/contracts/gnd-decision.md).
"""
import math
import os

from ..core.errors import CopilotInputError

MM = 1e-3
PLATE, COPPER, KEEP, STOP, OTHER = "gnd_plate_vias", "gnd_existing_copper", "keep_component", "stop_interface", "other"
KEEP_PAD = "gnd_keep_pad"                                # 019: mở rộng vùng cutout để giữ pad GND (exposed pad)
OPTIONS = (PLATE, COPPER, KEEP_PAD, KEEP, STOP, OTHER)
EXECUTABLE = (PLATE, COPPER, KEEP_PAD, KEEP, STOP)       # 'other' chỉ là câu hỏi: agent map về 1 option trên
LABELS = {PLATE: "Draw a GND rectangle bounding the GND vias in the body; the vias become GND pins",
          COPPER: "Use the existing GND copper on that layer: GND vias on it become GND pins (no new copper)",
          KEEP_PAD: "Extend the cut extent to keep the component's GND pad(s) (pad + margin); the pad is the GND pin, "
                    "no plate",
          KEEP: "Keep the component as is, no rebuild (port may have no near GND reference)",
          STOP: "Stop this interface",
          OTHER: "Other: your instruction (agent maps it to an option above, or says no tool exists)"}


def options_for(n_vias, n_copper_vias, keep_pad=None):
    """-> (options, omitted[{option, reason}]). Thuần.
    keep_pad (019): None = như 0.14.0 (luồng Excel); {offered, reason} -> gnd_keep_pad sau gnd_existing_copper / omitted."""
    for k, v in (("n_vias", n_vias), ("n_copper_vias", n_copper_vias)):
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise CopilotInputError(k, "int >= 0", v)
    opts, omitted = [], []
    if n_vias:
        opts.append(PLATE)
    else:
        omitted.append({"option": PLATE, "reason": "no GND via inside the component body"})
    if n_copper_vias:
        opts.append(COPPER)
    else:
        omitted.append({"option": COPPER, "reason": "no GND via in the body lands on existing GND copper of the layer"
                        if n_vias else "no GND via inside the component body"})
    if keep_pad is not None:
        if keep_pad.get("offered"):
            opts.append(KEEP_PAD)
        else:
            omitted.append({"option": KEEP_PAD, "reason": keep_pad.get("reason") or "not available"})
    return opts + [KEEP, STOP, OTHER], omitted


# ----------------------------------------------------------------------------- 019 keep pad
def outside_pads(edb, P, rd, nets, extent_mm, margin_mm=None):
    """Board gốc (chỉ đọc): linh kiện có pin tín hiệu, 0 pin GND trong vùng cutout và >= 1 pin GND ngoài vùng ->
    {pads, rects_mm (pad +- margin), touches, other_nets (net khác trong phần mở rộng), margin_mm}; khác -> None."""
    from shapely.geometry import Point, Polygon, box
    from shapely.ops import unary_union
    refs = set(P["cutout"]["reference_nets"])
    pins = list(edb.components.instances[rd].pins.values())
    keep = inside(extent_mm)
    gp = [p for p in pins if p.net_name in refs]
    if not any(p.net_name in nets for p in pins) or not gp or any(keep(*p.position) for p in gp):
        return None
    m = float(margin_mm if margin_mm is not None else
              (P.get("interface_sim") or {}).get("keep_pad_margin_mm", 0.5))
    E = Polygon([tuple(q) for q in extent_mm]).buffer(0)
    pads, boxes = [], []
    for p in gp:
        (x0, y0), (x1, y1) = p.bounding_box
        pb = box(x0 / MM, y0 / MM, x1 / MM, y1 / MM)
        boxes.append(pb)
        pads.append({"pin": str(p.pin_number), "layer": p.start_layer if p.start_layer == p.stop_layer else
                     f"{p.start_layer}-{p.stop_layer}", "pad_mm": [round(v, 3) for v in pb.bounds],
                     "size_mm": [round(pb.bounds[2] - pb.bounds[0], 3), round(pb.bounds[3] - pb.bounds[1], 3)],
                     "inside_frac": round(pb.intersection(E).area / max(pb.area, 1e-12), 3), "vias_mm": []})
    rects = [box(b.bounds[0] - m, b.bounds[1] - m, b.bounds[2] + m, b.bounds[3] + m) for b in boxes]
    added = unary_union(rects).difference(E)
    keep_nets = set(nets) | refs
    other = set()
    ax0, ay0, ax1, ay1 = unary_union(rects).bounds
    for v in edb.padstacks.instances.values():
        x, y = v.position[0] / MM, v.position[1] / MM
        if not (ax0 <= x <= ax1 and ay0 <= y <= ay1):
            continue
        pt = Point(x, y)
        if v.net_name in refs and not v.is_pin:
            for pd, b in zip(pads, boxes):
                if b.contains(pt):
                    pd["vias_mm"].append([round(x, 3), round(y, 3)])
        if v.net_name and v.net_name not in keep_nets and added.intersects(pt):
            other.add(v.net_name)
    if not added.is_empty:
        from ..core.geometry_edb import prim_points
        for pr in edb.modeler.primitives:
            try:
                n = pr.net_name
                if not n or n in keep_nets or n in other:
                    continue
                b = pr.bbox
                if b[2] / MM < ax0 or b[0] / MM > ax1 or b[3] / MM < ay0 or b[1] / MM > ay1:
                    continue
                g = Polygon([(x / MM, y / MM) for x, y in prim_points(pr)]).buffer(0)
                if g.intersects(added):
                    other.add(n)
            except Exception:
                continue
    return {"pads": pads, "rects_mm": [[round(v, 4) for v in r.bounds] for r in rects],
            "touches": all(r.intersects(E) for r in rects), "other_nets": sorted(other), "margin_mm": m}


def extend_extent(extent_mm, rects_mm):
    """Vùng cutout ∪ các hình chữ nhật (mm) -> điểm mm. Không còn 1 đa giác -> CopilotInputError. Thuần (shapely)."""
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    U = unary_union([Polygon([tuple(q) for q in extent_mm]).buffer(0)] + [box(*r) for r in rects_mm])
    if U.geom_type != "Polygon":
        raise CopilotInputError("extent", "GND pad touching the cut extent (union must be one polygon)", rects_mm)
    return [[x, y] for x, y in list(U.exterior.coords)[:-1]]


def keep_pad_entry(facts, extent_mm=None, why_none="no GND pin of the component outside the cut extent"):
    """facts (outside_pads) -> mục keep_pad của finding: {offered, reason, pads, other_nets, ...}. Thuần."""
    if not facts:
        return {"offered": False, "reason": why_none}
    e = dict(facts)
    if not facts.get("touches"):
        e.update(offered=False, reason="GND pad does not touch the cut extent (extension would be a separate island)")
        return e
    e.update(offered=True, reason="")
    if extent_mm:
        e["extent_mm"] = [list(q) for q in extent_mm]
        e["extended_mm"] = extend_extent(extent_mm, facts["rects_mm"])
    return e


def plate_rect(vias, pads, gap):
    """Hình chữ nhật GND bao các via (+ bán kính via lớn nhất + gap), co lại tránh pad tín hiệu. m. Thuần.
    vias [(x, y, đường kính)], pads [(x0, y0, x1, y1)]. Công thức chuyển nguyên văn từ rebuild_smd_component."""
    if not vias:
        return None
    r = max(d for _, _, d in vias) / 2 + gap
    rx0, ry0 = min(v[0] for v in vias) - r, min(v[1] for v in vias) - r
    rx1, ry1 = max(v[0] for v in vias) + r, max(v[1] for v in vias) + r
    cxr, cyr = (rx0 + rx1) / 2, (ry0 + ry1) / 2
    for (px0, py0, px1, py1) in pads:
        if px1 + gap > rx0 and px0 - gap < rx1 and py1 + gap > ry0 and py0 - gap < ry1:
            pcx, pcy = (px0 + px1) / 2, (py0 + py1) / 2
            if abs(pcy - cyr) >= abs(pcx - cxr):
                if pcy > cyr: ry1 = min(ry1, py0 - gap)
                else: ry0 = max(ry0, py1 + gap)
            else:
                if pcx > cxr: rx1 = min(rx1, px0 - gap)
                else: rx0 = max(rx0, px1 + gap)
    return rx0, ry0, rx1, ry1


def _in_poly(x, y, outline, voids):
    from ..core.geometry import point_in_poly
    return point_in_poly(x, y, outline) and not any(point_in_poly(x, y, v) for v in voids)


def inside(extent_mm):
    """extent (điểm mm) -> hàm (x, y m) -> nằm trong vùng cutout? None = luôn True (design đã cắt)."""
    if not extent_mm:
        return lambda x, y: True
    from ..core.geometry import point_in_poly
    pts = [tuple(p) for p in extent_mm]
    return lambda x, y: point_in_poly(x / MM, y / MM, pts)


def context(edb, P, rd, nets, body_bbox, extent_mm=None):
    """Đo trên EDB (chỉ đọc): lớp, part, kế hoạch pin tín hiệu, pin GND, via GND trong thân (cùng bộ lọc cũ),
    hình chữ nhật đề xuất, đồng GND có sẵn của lớp chạm vùng thân, via GND nằm trên đồng đó.
    extent_mm (propose, trên board gốc): chỉ tính pin / via GND nằm trong vùng cutout (như design sẽ cắt ra)."""
    keep = inside(extent_mm)
    from ..core.geometry_edb import prim_points
    from .cutter import layers_of, plan_smd_pin
    pc = P["port"]
    comp = edb.components.instances[rd]
    layer, part = comp.placement_layer, comp.partname
    refs = set(P["cutout"]["reference_nets"])
    sig = [p for p in comp.pins.values() if p.net_name in nets]
    gnd_pins = [p for p in comp.pins.values() if p.net_name in refs and keep(*p.position)]
    plan = [(p, *plan_smd_pin(edb, p, layer)) for p in sig]

    m = float(pc["smd_gnd_search_margin_mm"]) * MM
    padL = max(max(bb[2] - bb[0], bb[3] - bb[1]) for _, _, _, bb in plan)
    bx0, by0, bx1, by1 = body_bbox
    ix0, iy0, ix1, iy1 = bx0 + padL - m, by0 + padL - m, bx1 - padL + m, by1 - padL + m
    dirs = [((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2, pos[0] - (bb[0] + bb[2]) / 2, pos[1] - (bb[1] + bb[3]) / 2)
            for _, pos, _, bb in plan if pos is not None]

    def body_side(x, y):
        if not dirs:
            return True
        pcx, pcy, ux, uy = min(dirs, key=lambda d: math.hypot(x - d[0], y - d[1]))
        return (x - pcx) * ux + (y - pcy) * uy > 0

    gvias = [v for v in edb.padstacks.instances.values()
             if v.net_name in refs and not v.is_pin and layer in layers_of(v)
             and ix0 <= v.position[0] <= ix1 and iy0 <= v.position[1] <= iy1 and body_side(*v.position)
             and keep(*v.position)]
    gap = float(pc["smd_gnd_plane_gap_mm"]) * MM
    vdat = [(v.position[0], v.position[1], v.bounding_box[1][0] - v.bounding_box[0][0]) for v in gvias]
    rect = plate_rect(vdat, [bb for _, _, _, bb in plan], gap)
    copper = []
    prims = []
    for n in sorted(refs):
        try:
            prims += list(edb.modeler.get_primitives(net_name=n, layer_name=layer))
        except Exception:
            prims += [p for p in edb.modeler.primitives if p.net_name == n]
    for pr in prims:
        try:
            if pr.net_name not in refs or pr.layer_name != layer:
                continue
            b = pr.bbox
            if b[2] < bx0 or b[0] > bx1 or b[3] < by0 or b[1] > by1:
                continue
            voids = []
            for vd in getattr(pr, "voids", None) or []:
                try:
                    voids.append(prim_points(vd))
                except Exception:
                    pass
            copper.append({"outline": prim_points(pr), "voids": voids})
        except Exception:
            continue
    copper_vias = [v for v in gvias if any(_in_poly(v.position[0], v.position[1], c["outline"], c["voids"])
                                           for c in copper)]
    return {"refdes": rd, "layer": layer, "part": part, "plan": plan, "gnd_pins": gnd_pins, "gvias": gvias,
            "vias": vdat, "rect": rect, "copper": copper, "copper_vias": copper_vias, "body": tuple(body_bbox),
            "gap": gap}


def _clip_copper(copper, body, margin=0.5 * MM):
    """Đồng GND cắt theo vùng thân (+0.5 mm) -> (đường bao mm, diện tích mm2 trong vùng thân). Thuần (shapely)."""
    from shapely.geometry import Polygon, box
    bx0, by0, bx1, by1 = body
    view, inner = box(bx0 - margin, by0 - margin, bx1 + margin, by1 + margin), box(bx0, by0, bx1, by1)
    outs, area = [], 0.0
    for c in copper:
        try:
            g = Polygon(c["outline"], [v for v in c["voids"] if len(v) >= 3]).buffer(0)
        except Exception:
            continue
        area += g.intersection(inner).area
        clip = g.intersection(view)
        for part in getattr(clip, "geoms", [clip]):
            if part.geom_type == "Polygon" and not part.is_empty:
                outs.append([[round(x / MM, 3), round(y / MM, 3)] for x, y in part.exterior.coords])
    return outs, round(area / MM / MM, 3)


def _r(v, n=4):
    return round(v / MM, n)


def finding(ctx, keep_pad=None):
    """ctx -> dict JSON (mm): dữ liệu cho ảnh, bảng, câu hỏi. Thuần. keep_pad (019): keep_pad_entry(...) hoặc None."""
    cv = {(round(v.position[0], 9), round(v.position[1], 9)) for v in ctx.get("copper_vias") or []}
    opts, omitted = options_for(len(ctx.get("vias") or []), len(cv), keep_pad)
    cu, area = _clip_copper(ctx.get("copper") or [], ctx["body"])
    rect = ctx.get("rect")
    return {"refdes": ctx["refdes"], "part": ctx.get("part"), "layer": ctx.get("layer"),
            "body_mm": [_r(v) for v in ctx["body"]],
            "pads_mm": [[_r(b[0]), _r(b[1]), _r(b[2]), _r(b[3]), getattr(p, "net_name", "")]
                        for p, _, _, b in ctx.get("plan") or []],
            "vias_mm": [[_r(x), _r(y), _r(d), (round(x, 9), round(y, 9)) in cv] for x, y, d in ctx.get("vias") or []],
            "rect_mm": [round(v / MM, 2) for v in rect] if rect else None,
            "rect_size_mm": [round((rect[2] - rect[0]) / MM, 2), round((rect[3] - rect[1]) / MM, 2)] if rect else None,
            "copper_mm": cu, "copper_area_mm2": area,
            "n_vias": len(ctx.get("vias") or []), "n_copper_vias": len(cv),
            "options": opts, "omitted": omitted, "labels": {o: LABELS[o] for o in opts},
            **({"keep_pad": keep_pad} if keep_pad is not None else {})}


def _font(size):
    from PIL import ImageFont
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render(f, path, px=900):
    """Ảnh PNG vùng thân linh kiện (PIL, không cần AEDT GUI). f = finding(...). Trả path."""
    from PIL import Image, ImageDraw
    bx0, by0, bx1, by1 = f["body_mm"]
    pad = 0.5
    x0, y0, x1, y1 = bx0 - pad, by0 - pad, bx1 + pad, by1 + pad
    kp = f.get("keep_pad") or {}
    for r in kp.get("rects_mm") or []:                                  # 019: khung nhìn chứa cả pad + lề
        x0, y0, x1, y1 = min(x0, r[0] - pad), min(y0, r[1] - pad), max(x1, r[2] + pad), max(y1, r[3] + pad)
    w = px
    h = max(300, int(px * (y1 - y0) / max(x1 - x0, 1e-6)))
    top = 64 if kp.get("pads") else 46
    s = w / (x1 - x0)
    im = Image.new("RGB", (w, h + top), (255, 255, 255))
    d = ImageDraw.Draw(im)

    def P(x, y):
        return (x - x0) * s, top + (y1 - y) * (h / (y1 - y0))

    for poly in f.get("copper_mm") or []:
        if len(poly) >= 3:
            d.polygon([P(x, y) for x, y in poly], fill=(190, 215, 240), outline=(31, 119, 180))
    d.rectangle([*P(bx0, by1), *P(bx1, by0)], outline=(150, 150, 150), width=1)
    for x0_, y0_, x1_, y1_, _ in f.get("pads_mm") or []:
        d.rectangle([*P(x0_, y1_), *P(x1_, y0_)], fill=(214, 39, 40), outline=(120, 0, 0))
    for x, y, dia, on_cu in f.get("vias_mm") or []:
        cx, cy = P(x, y)
        r = max(3, dia / 2 * s)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(31, 119, 180),
                  outline=(0, 0, 0) if on_cu else (31, 119, 180), width=3 if on_cu else 1)
    if kp.get("pads"):                                                   # 019: pad GND ngoài vùng cutout
        for pd in kp["pads"]:
            a0, b0, a1, b1 = pd["pad_mm"]
            d.rectangle([*P(a0, b1), *P(a1, b0)], outline=(44, 160, 44), width=3)
            for x, y in pd.get("vias_mm") or []:
                cx, cy = P(x, y)
                d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(31, 119, 180), outline=(44, 160, 44), width=2)
        if kp.get("extent_mm"):
            pts = [P(x, y) for x, y in kp["extent_mm"]]
            d.line(pts + pts[:1], fill=(150, 150, 150), width=2)
        if kp.get("extended_mm"):
            pts = [P(x, y) for x, y in kp["extended_mm"]]
            d.line(pts + pts[:1], fill=(44, 160, 44), width=2)
    if f.get("rect_mm"):
        rx0, ry0, rx1, ry1 = f["rect_mm"]
        (ax, ay), (bx, by) = P(rx0, ry1), P(rx1, ry0)
        for (sx, sy, ex, ey) in ((ax, ay, bx, ay), (bx, ay, bx, by), (bx, by, ax, by), (ax, by, ax, ay)):
            n = max(1, int(math.hypot(ex - sx, ey - sy) / 8))
            for i in range(0, n, 2):
                d.line([sx + (ex - sx) * i / n, sy + (ey - sy) * i / n,
                        sx + (ex - sx) * (i + 1) / n, sy + (ey - sy) * (i + 1) / n], fill=(0, 0, 0), width=2)
        d.text((ax + 4, ay + 4), f"proposed GND {f['rect_size_mm'][0]} x {f['rect_size_mm'][1]} mm",
               fill=(0, 0, 0), font=_font(14))
    d.rectangle([0, 0, w, top - 2], fill=(245, 245, 245))
    d.text((6, 4), f"{f['refdes']}  {f.get('part') or ''}  layer {f.get('layer')}  - no GND pin", fill=(0, 0, 0),
           font=_font(16))
    d.text((6, 24), f"red signal pads | blue GND vias ({f['n_vias']}, black ring = on GND copper "
                    f"{f['n_copper_vias']}) | light blue GND copper {f['copper_area_mm2']} mm2 | dashed = proposed",
           fill=(60, 60, 60), font=_font(12))
    if kp.get("pads"):
        pins = ", ".join(f"{p['pin']} {p['size_mm'][0]}x{p['size_mm'][1]} mm" for p in kp["pads"])
        d.text((6, 42), f"green: GND pad outside the cut ({pins}) | grey line = cut extent | green line = extended "
                        f"(+{kp.get('margin_mm')} mm) | other nets in extension: {nets_text(kp.get('other_nets'), 3)}",
               fill=(30, 110, 30), font=_font(12))
    bar = 1.0 * s
    d.line([w - 20 - bar, h + top - 16, w - 20, h + top - 16], fill=(0, 0, 0), width=3)
    d.text((w - 20 - bar, h + top - 34), "1 mm", fill=(0, 0, 0), font=_font(13))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    im.save(path)
    return path


def question_md(f, image=None):
    """Câu hỏi nhiều lựa chọn cho agent trình bày (không tự chọn)."""
    lines = [f"**{f['refdes']}** ({f.get('part')}, {f.get('layer')}): no GND pin." +
             (f" Image: {image}" if image else ""),
             f"GND vias in body: {f['n_vias']}; on existing GND copper: {f['n_copper_vias']}; "
             f"proposed rectangle: {f['rect_mm']} mm ({f['rect_size_mm']} mm)" if f.get("rect_mm") else
             f"GND vias in body: {f['n_vias']}; no rectangle possible"]
    kp = f.get("keep_pad") or {}
    if kp.get("pads"):
        lines.append("GND pad(s) outside the cut extent: " + "; ".join(
            f"pin {p['pin']} {p['size_mm'][0]} x {p['size_mm'][1]} mm ({int(p['inside_frac'] * 100)} % inside the cut, "
            f"{len(p.get('vias_mm') or [])} GND vias in the pad)" for p in kp["pads"]) +
            f"; extension = pad + {kp.get('margin_mm')} mm; other nets in the extension (not kept by the cut): "
            f"{nets_text(kp.get('other_nets'), 10)}")
    if f.get("gnd_pins_outside_cut"):
        lines.append(f"Note: GND pin(s) {f['gnd_pins_outside_cut']} exist on the board but lie OUTSIDE the cut "
                     "extent (removed by the cutout).")
    lines.append("")
    for i, o in enumerate(f["options"], 1):
        lines.append(f"{i}. `{o}` - {LABELS[o]}")
    for o in f["omitted"]:
        lines.append(f"- not offered `{o['option']}`: {o['reason']}")
    return "\n".join(lines)


def nets_text(nets, n):
    """'a, b, c (+N more)' / 'none'. Thuần."""
    nets = list(nets or [])
    if not nets:
        return "none"
    return ", ".join(nets[:n]) + (f" (+{len(nets) - n} more, see keep_pad.other_nets)" if len(nets) > n else "")


def question(edb, P, rd, nets, body=None, image_path=None, extent_mm=None, keep_pad=None):
    """Đầu không pin GND -> finding + ảnh (image_path) + question_md. Cùng tính toán với apply. Chỉ đọc EDB.
    keep_pad (019): keep_pad_entry(...) (interface sim / design end check); None = luồng Excel như 0.14.0."""
    from .cutter import comp_bbox
    body = tuple(body) if body else comp_bbox(edb.components.instances[rd])
    f = finding(context(edb, P, rd, set(nets), body, extent_mm), keep_pad)
    if image_path:
        f["image"] = render(f, image_path)
    f["question_md"] = question_md(f, f.get("image"))
    return f


def needs_question(edb, P, rd, nets, bga_or_th, extent_mm=None):
    """True khi đầu không phải BGA / TH, có pin tín hiệu và 0 pin GND (reference nets) [trong vùng cutout]."""
    if bga_or_th:
        return False
    refs = set(P["cutout"]["reference_nets"])
    keep = inside(extent_mm)
    pins = list(edb.components.instances[rd].pins.values())
    return any(p.net_name in nets for p in pins) and not any(p.net_name in refs and keep(*p.position) for p in pins)
