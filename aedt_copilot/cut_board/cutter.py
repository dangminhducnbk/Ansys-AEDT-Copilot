"""Cắt MỘT channel. Được gọi trong tiến trình riêng (worker) để lỗi không làm dừng cả loạt.

Quy tắc (đã chốt với người dùng, xem templates/autocut_template.csv):
  extent như AEDT Auto Generate Extent (conformal, round, hệ số không đơn vị) -> cutout
  giữ 2 linh kiện đầu + linh kiện nối tiếp (gán R = 0 ohm)
  linh kiện SMD: pin dời về đầu pad phía thân IC + plane GND gom via thành pin, tạo lại component
  dọn GND: lớp plane bỏ mảnh vụn; lớp signal chỉ giữ shield coplanar (gần trace, đủ lớn, có via)
  BGA giữ pin GND quanh pin tín hiệu; xoá via/microvia GND xa tín hiệu hoặc treo
  coax port, solder ball (95% cạnh ngắn pad, cao 0.2 mm), setup/sweep/airbox
"""
import inspect as _inspect
import math
import os
import time

from . import geometry as G

MM = 1e-3


class Log:
    def __init__(self, fn=print):
        self.t0 = time.time()
        self.fn = fn
        self.times = {}

    def __call__(self, *a):
        self.fn(f"[{time.time() - self.t0:7.1f}s] " + " ".join(str(x) for x in a))

    def step(self, name):
        log = self

        class _S:
            def __enter__(s):
                s.t = time.time()
                log(">>", name)

            def __exit__(s, *exc):
                log.times[name] = round(time.time() - s.t, 1)
                log("<<", name, log.times[name], "s")
        return _S()


# ----------------------------------------------------------------------------- helpers
def is_bga_or_th(comp, nets):
    if "BGA" in (comp.partname or "").upper():
        return True
    pins = [p for p in comp.pins.values() if p.net_name in nets] or list(comp.pins.values())
    return pins[0].start_layer != pins[0].stop_layer


def comp_bbox(comp):
    xs, ys = [], []
    for p in comp.pins.values():
        (x0, y0), (x1, y1) = p.bounding_box
        xs += [x0, x1]
        ys += [y0, y1]
    return min(xs), min(ys), max(xs), max(ys)


def layers_of(v):
    try:
        r = list(v.layer_range_names)
        if r:
            return r
    except Exception:
        pass
    return [v.start_layer, v.stop_layer]


def set_layout_pin(v):
    try:
        v.is_pin = True
        if v.is_pin:
            return True
    except Exception:
        pass
    for a in ("_edb_object", "_edb_padstackinstance", "core"):
        o = getattr(v, a, None)
        if o is not None and hasattr(o, "SetIsLayoutPin"):
            o.SetIsLayoutPin(True)
            return True
    return False


def call_filtered(fn, **kw):
    """Gọi hàm PyEDB chỉ với các tham số mà phiên bản đang cài hỗ trợ."""
    try:
        params = _inspect.signature(fn).parameters
        if not any(p.kind == p.VAR_KEYWORD for p in params.values()):
            kw = {k: v for k, v in kw.items() if k in params}
    except (TypeError, ValueError):
        pass
    return fn(**kw)


def signal_segments(edb, nets):
    """{layer: [(x0,y0,x1,y1,half_width)]} + vị trí padstack tín hiệu."""
    segs = {}
    for p in edb.layout.paths:
        if p.net_name in nets:
            cl = p.center_line
            segs.setdefault(p.layer_name, []).extend(
                (cl[i][0], cl[i][1], cl[i + 1][0], cl[i + 1][1], p.width / 2) for i in range(len(cl) - 1))
    pts = [v.position for v in edb.padstacks.instances.values() if v.net_name in nets]
    return segs, pts


def dist_point_signal(x, y, segs, pts):
    d = 1.0
    for lst in segs.values():
        for s in lst:
            d = min(d, G.point_seg_dist(x, y, *s[:4]) - s[4])
    for a, b in pts:
        d = min(d, math.hypot(x - a, y - b))
    return d


def dist_poly_layer_signal(poly_pts, layer_segs):
    """Khoảng cách mép polygon tới trace tín hiệu trên cùng lớp (trừ nửa bề rộng trace)."""
    if not layer_segs:
        return 1.0
    bx0, by0, bx1, by1 = G.bbox_of(poly_pts)
    d = 1.0
    eds = G.edges(poly_pts)
    for s in layer_segs:
        # lọc nhanh theo bbox
        if min(s[0], s[2]) - s[4] > bx1 + d or max(s[0], s[2]) + s[4] < bx0 - d or \
           min(s[1], s[3]) - s[4] > by1 + d or max(s[1], s[3]) + s[4] < by0 - d:
            continue
        if G.point_in_poly(s[0], s[1], poly_pts) or G.point_in_poly(s[2], s[3], poly_pts):
            return 0.0
        for e in eds:
            d = min(d, G.seg_seg_dist(e, s[:4]) - s[4])
    return max(d, 0.0)


# ----------------------------------------------------------------------------- extent
def compute_extent_mm(edb, P, nets, log, factor=None):
    """factor (022): hệ số thay cutout.expansion (vùng đầu mở rộng); None = template."""
    c = P["cutout"]
    ET = edb.core.Geometry.ExtentType
    etype = {"conformal": ET.Conforming, "conforming": ET.Conforming, "convex_hull": ET.ConvexHull,
             "convexhull": ET.ConvexHull, "bounding_box": ET.BoundingBox, "boundingbox": ET.BoundingBox}[
        str(c["extent_type"]).lower()]
    unitless = bool(c["expansion_unitless"])
    e = float(c["expansion"] if factor is None else factor)
    f = e if unitless else e * MM
    pd = edb.layout.expanded_extent([edb.nets.nets[n] for n in nets], etype, f, unitless,
                                    bool(c["round_corner"]), int(c["increments"]))
    try:
        pd = pd.GetPolygonWithoutArcs()
    except Exception as ex:
        log("GetPolygonWithoutArcs lỗi, dùng điểm thô:", ex)
    pts = [(p.X.ToDouble() / MM, p.Y.ToDouble() / MM) for p in pd.Points if abs(p.Y.ToDouble()) < 1e3]
    x0, y0, x1, y1 = G.bbox_of(pts)
    log(f"extent {len(pts)} điểm, bbox mm [{x0:.2f}, {y0:.2f}, {x1:.2f}, {y1:.2f}]")
    return pts


# ----------------------------------------------------------------------------- SMD
def plan_smd_pin(edb, pin, layer, paths=None):
    """Pad end opposite the trace leaving the pad on its layer -> (pos | None, W, bbox). None: via in pad or no
    trace exit. paths (041): candidate paths (default every path of the layout; the config page passes the net's)."""
    (x0, y0), (x1, y1) = pin.bounding_box
    cx, cy = pin.position
    Lx, Ly = x1 - x0, y1 - y0
    long_x = Lx >= Ly
    L, W = (Lx, Ly) if long_x else (Ly, Lx)
    bbox = (x0, y0, x1, y1)
    try:
        cand = edb.nets.nets[pin.net_name].padstack_instances
    except Exception:
        cand = edb.padstacks.instances.values()
    for v in cand:
        if not v.is_pin and math.hypot(v.position[0] - cx, v.position[1] - cy) < W / 2:
            return None, W, bbox                                   # via-in-pad -> port tại tâm
    nxt = None
    for pth in (edb.layout.paths if paths is None else paths):
        if pth.net_name != pin.net_name or pth.layer_name != layer:
            continue
        cl = pth.center_line
        for a, b in ((cl[0], cl[1]), (cl[-1], cl[-2])):
            if x0 - 1e-9 <= a[0] <= x1 + 1e-9 and y0 - 1e-9 <= a[1] <= y1 + 1e-9:
                nxt = b
                break
        if nxt:
            break
    if nxt is None:
        return None, W, bbox
    s = (nxt[0] - cx) if long_x else (nxt[1] - cy)
    d = (L / 2 - W / 2) * (-1 if s > 0 else 1)                    # ngược hướng trace = phía thân IC
    return ((cx + d, cy) if long_x else (cx, cy + d)), W, bbox


SPAN_MIN_M = 1e-6                       # 041 slider: pads with L - W below this have no slider (round / square)


def port_span(pin, body_bbox):
    """041 slider: travel of the port centre along the pad's long axis -> ((p0, p1) | None, reason), metres.
    p0 = W/2 from the pad end on the body side (centre of body_bbox, comp_bbox on the source board), p1 = W/2 from the
    far end. None: square / round pad, no body, pad on the body centre line."""
    (x0, y0), (x1, y1) = pin.bounding_box
    cx, cy = pin.position
    Lx, Ly = x1 - x0, y1 - y0
    long_x = Lx >= Ly
    L, W = (Lx, Ly) if long_x else (Ly, Lx)
    if L - W <= max(SPAN_MIN_M, 1e-3 * W):
        return None, "square / round pad (no long axis)"
    if not body_bbox:
        return None, "no component body"
    s = ((body_bbox[0] + body_bbox[2]) / 2 - cx) if long_x else ((body_bbox[1] + body_bbox[3]) / 2 - cy)
    if abs(s) < W / 2:
        return None, "pad on the body centre line (no side)"
    d = (L / 2 - W / 2) * (1 if s > 0 else -1)
    p0 = (cx + d, cy) if long_x else (cx, cy + d)
    p1 = (cx - d, cy) if long_x else (cx, cy - d)
    return (p0, p1), "body"


def port_at(span, pct):
    """041 slider: point at pct % of the span (0 = body side, 50 = pad centre, 100 = far side)."""
    (a, b), t = span, max(0.0, min(100.0, float(pct))) / 100.0
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def pad_end_toward(pin, body_bbox):
    """041: pad end on the body side for a pad without trace exit (via in pad ...): along the pad's long axis, towards
    the centre of body_bbox (x0, y0, x1, y1 m = comp_bbox on the source board). -> (pos | None, reason)."""
    span, how = port_span(pin, body_bbox)
    return (span[0], how) if span else (None, how)


def port_end(edb, pin, layer, body_bbox, paths=None):
    """041: THE pad-end position of a signal pin (build + config page): trace exit -> opposite end; else the end
    towards the body centre. -> (pos | None, how): how = 'trace' | 'body' | reason when no position."""
    pos, _, _ = plan_smd_pin(edb, pin, layer, paths)
    if pos is not None:
        return pos, "trace"
    return pad_end_toward(pin, body_bbox)


def _pad_box(p):
    """021: khung pad (x0, y0, x1, y1) m của pin; đọc lỗi -> tâm (x, y)."""
    try:
        (x0, y0), (x1, y1) = p.bounding_box
        return (float(x0), float(y0), float(x1), float(y1))
    except Exception:
        return tuple(p.position)


def prune_own_gnd_pins(P, rd, sig_pins, gnd_pins, protect_names=()):
    """021: chọn pin GND riêng của đầu cần giữ (gnd_pins.select). -> (pin giữ, pin bỏ, report). Không sửa EDB."""
    from . import gnd_pins as GP
    keyed = {}
    for p in gnd_pins:
        k = str(p.pin_number)
        while k in keyed:                                               # tên trùng (hiếm): vẫn phân biệt
            k += "'"
        keyed[k] = p
    sel = GP.select([tuple(p.position) for p in sig_pins], {k: _pad_box(p) for k, p in keyed.items()},
                    GP.keep_m(P), {str(n) for n in protect_names or ()})
    rep = GP.report(rd, len(keyed), sel, round(GP.keep_m(P) / MM, 4),
                    {i: str(p.pin_number) for i, p in enumerate(sig_pins)})
    return [keyed[k] for k in sel["keep"]], [keyed[k] for k in sel["removed"]], rep


def comp_model(P, rd):
    """038: component model of one end = template rows (solder_ball.*, component.*) overridden by
    component.model JSON {refdes: {...}}. Keys: die_type die_orientation die_height_mm ball_shape ball_ratio
    ball_height_mm ball_material port_location."""
    import json
    sb, c = P.get("solder_ball") or {}, P.get("component") or {}
    m = {"die_type": c.get("die_type") or "flip_chip", "die_orientation": c.get("die_orientation") or "chip_down",
         "die_height_mm": c.get("die_height_mm") or 0,
         "ball_shape": (sb.get("shape") or "cylinder") if sb.get("enable", True) else "none",
         "ball_ratio": sb.get("diameter_ratio"), "ball_height_mm": sb.get("height_mm"),
         "ball_material": sb.get("material"), "port_location": c.get("port_location") or "end",
         "port_location_explicit": False}
    raw = c.get("model")
    if raw:
        try:
            per = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except ValueError:
            per = {}
        own = {k: v for k, v in (per.get(rd) or {}).items() if v not in (None, "")}
        m.update(own)
        m["port_location_explicit"] = "port_location" in own or "port_pct" in own   # 041: the user's choice
    m["port_pct"] = port_pct_of(m) if m["port_location_explicit"] else None
    return m


def port_pct_of(m):
    """041 slider: % of the port travel from a component model (port_pct wins; 5.2.0 end -> 0, centre -> 50)."""
    v = m.get("port_pct")
    if v not in (None, ""):
        try:
            return max(0.0, min(100.0, float(v)))
        except (TypeError, ValueError):
            pass
    return 50.0 if str(m.get("port_location") or "end").lower() == "centre" else 0.0


def rebuild_smd_component(edb, P, rd, nets, body_bbox, protect_polys, log, gnd_choice=None, protect_names=(),
                          port_location="end", explicit=False, port_report=None, port_pct=None):
    """Trả (id các pin GND cần bảo vệ, cạnh ngắn pad tín hiệu, gnd_ref).
    015: không có pin GND -> gnd_choice của NGƯỜI DÙNG: gnd_plate_vias (tấm GND bao via, như trước) |
    gnd_existing_copper (via GND trên đồng có sẵn -> pin, không vẽ đồng). Khác -> RuntimeError, chưa sửa gì.
    021: pin GND riêng xa mọi pin tín hiệu (> cleanup.smd_gnd_pin_keep_dist_mm) bị xoá trước khi dựng lại; giữ pin
    gần nhất của mỗi pin tín hiệu và protect_names (pin / pad GND của luật 022, pad 019). gnd_ref.gnd_pin_cleanup."""
    from . import gnd_decision as GD
    ctx = GD.context(edb, P, rd, nets, body_bbox)
    comp = edb.components.instances[rd]
    layer, part, plan = ctx["layer"], ctx["part"], ctx["plan"]          # ctx plan (trace) also drives the GND logic
    loc = str(port_location).lower()
    rep = {"requested": loc, "explicit": bool(explicit), "pins": len(plan), "moved": 0, "not_moved": []}
    if explicit:                                                        # 041 slider: the user's % for EVERY signal pad
        pct = port_pct_of({"port_pct": port_pct, "port_location": loc})
        rep.update(pct=pct, targets=[])
        new = []
        for p, _, w, bb in plan:
            span, how = port_span(p, body_bbox)
            pos = None
            if span is None:
                if abs(pct - 50.0) > 1e-9:
                    rep["not_moved"].append({"pin": str(p.pin_number), "net": p.net_name, "reason": how})
                    log(f"  CẢNH BÁO {rd}.{p.pin_number}: vị trí port {pct:g} % không áp dụng được ({how}) -> tâm pad")
                else:
                    rep["targets"].append({"pin": str(p.pin_number), "net": p.net_name,
                                           "at_mm": [round(v / MM, 6) for v in p.position], "offset_mm": None})
            else:
                t = port_at(span, pct)
                rep["targets"].append({"pin": str(p.pin_number), "net": p.net_name,
                                       "at_mm": [round(v / MM, 6) for v in t],
                                       "offset_mm": round((math.hypot(t[0] - span[0][0], t[1] - span[0][1]) + w / 2)
                                                          / MM, 4)})
                if math.hypot(t[0] - p.position[0], t[1] - p.position[1]) > 1e-6:
                    pos = t                                             # 50 % = pad centre = pin kept
            new.append((p, pos, w, bb))
        plan = new
        log(f"  {rd}: port at {pct:g} % of the pad (0 = body side, 50 = centre, 100 = outer)")
    elif loc == "centre":                                               # 038: port at the pad centre = pin not moved
        plan = [(p, None, w, bb) for p, _, w, bb in plan]
        log(f"  {rd}: port at the pad centre (pins not moved)")
    else:                                                               # no per-end choice: as before 041
        rep["not_moved"] = [{"pin": str(p.pin_number), "net": p.net_name,
                             "reason": "no trace exit (via in pad / no trace), no per-end choice"}
                            for p, pos, _, _ in plan if pos is None]
    gnd_pins, gvias, refs = ctx["gnd_pins"], ctx["gvias"], set(P["cutout"]["reference_nets"])
    W = min(w for _, _, w, _ in plan)
    log(f"  {rd}: {len(gnd_pins)} pin GND sẵn có, {len(gvias)} via GND trong thân")
    cleanup_rep = None
    if gnd_pins:                                                        # 021: chỉ pin GND riêng (không tấm / đồng)
        gnd_pins, drop, cleanup_rep = prune_own_gnd_pins(P, rd, [p for p, _, _, _ in plan], gnd_pins, protect_names)
        for p in drop:
            p.delete()
        log(f"  {rd}: pin GND {cleanup_rep['gnd_pins_before']} -> {cleanup_rep['gnd_pins_after']} "
            f"(giữ <= {cleanup_rep['keep_dist_mm']} mm quanh pin tín hiệu)" +
            ("; " + "; ".join(cleanup_rep["warnings"] + cleanup_rep["info"])
             if cleanup_rep["warnings"] or cleanup_rep["info"] else ""))
    if not gnd_pins:
        ok_choice = (gnd_choice == GD.PLATE and gvias) or (gnd_choice == GD.COPPER and ctx["copper_vias"])
        if not ok_choice:
            f = GD.finding(ctx)
            raise RuntimeError(f"{rd}: no GND pin - GND decision needed (got {gnd_choice!r}; options "
                               f"{f['options']}; omitted {[o['option'] for o in f['omitted']]})")

    dname = f"cutpin_{W * 1e6:.0f}um_{layer.replace(' ', '_')}"
    if any(pos is not None for _, pos, _, _ in plan) and dname not in edb.padstacks.definitions:
        edb.padstacks.create(padstackname=dname, holediam="0um", paddiam=f"{W * 1e6:.3f}um", antipaddiam="0um",
                             has_hole=False, start_layer=layer, stop_layer=layer)
    # Pin giữ lại (via-in-pad, pin GND sẵn có) phải tách khỏi component trước khi xoá component,
    # nếu không EDB xoá luôn pin theo nhóm (lỗi thấy ở connector J25: component mới 0 pin).
    reuse = [p for p, pos, _, _ in plan if pos is None] + list(gnd_pins)
    detach_pins(edb, comp, reuse, rd, log)
    edb.components.delete(rd)
    newpins, moved = [], []
    for p, pos, w, bb in plan:
        pname, net = p.pin_number, p.net_name
        if pos is None:
            newpins.append(p)
            continue
        edb.modeler.create_rectangle(layer, net, [bb[0], bb[1]], [bb[2], bb[3]])   # giữ copper pad cũ
        p.delete()
        newpins.append(edb.padstacks.place([pos[0], pos[1]], dname, net_name=net, via_name=pname,
                                           fromlayer=layer, tolayer=layer, is_pin=True))
        moved.append(pname)
    gnd_ref = {"kind": "own_pins", "pins": len(gnd_pins)}
    if cleanup_rep:
        gnd_ref["gnd_pin_cleanup"] = cleanup_rep
    if not gnd_pins and gnd_choice == GD.PLATE:
        rx0, ry0, rx1, ry1 = ctx["rect"]
        rect = edb.modeler.create_rectangle(layer, sorted(refs)[0], [rx0, ry0], [rx1, ry1])
        protect_polys.add(rect.id)
        ok = [set_layout_pin(v) for v in gvias]
        gnd_pins = gvias
        log(f"  {rd}: plane GND [{rx0/MM:.2f}, {ry0/MM:.2f}, {rx1/MM:.2f}, {ry1/MM:.2f}] mm, {sum(ok)} via -> pin")
        gnd_ref = {"kind": "plate_vias", "rect_mm": [round(v / MM, 2) for v in ctx["rect"]], "pins": len(gvias)}
    elif not gnd_pins:                                                  # gnd_existing_copper
        cv = ctx["copper_vias"]
        ok = [set_layout_pin(v) for v in cv]
        gnd_pins = cv
        log(f"  {rd}: dùng đồng GND có sẵn trên {layer}, {sum(ok)} via -> pin (không vẽ đồng mới)")
        gnd_ref = {"kind": "existing_copper", "pins": len(cv)}
    allp = [x for x in newpins + gnd_pins if x is not None]
    edb.components.create(allp, component_name=rd, placement_layer=layer,
                          component_part_name=unique_def_name(edb, f"{part}_cut"))
    edb.components.refresh_components()
    if edb.components.instances[rd].numpins != len(allp):
        raise RuntimeError(f"{rd}: component mới có {edb.components.instances[rd].numpins} pin, cần {len(allp)}")
    log(f"  {rd}: {len(moved)} pin dời về đầu pad, component mới {len(newpins)} sig + {len(gnd_pins)} GND")
    rep["moved"] = len(moved)
    if port_report is not None:
        port_report.update(rep)
    return {v.id for v in gnd_pins}, W, gnd_ref


def vias_in_gnd_pads(edb, P, rd):
    """019: id via GND (không phải pin) nằm trong khung pad GND của linh kiện rd (exposed pad giữ lại)."""
    refs = set(P["cutout"]["reference_nets"])
    boxes = [p.bounding_box for p in edb.components.instances[rd].pins.values() if p.net_name in refs]
    return {v.id for v in edb.padstacks.instances.values() if v.net_name in refs and not v.is_pin
            and any(b[0][0] <= v.position[0] <= b[1][0] and b[0][1] <= v.position[1] <= b[1][1] for b in boxes)}


def unique_def_name(edb, base):
    """Tên component definition chưa có trong database.
    Definition dùng chung cả database (mọi design). Nếu trùng tên với definition có sẵn (vd. U26 đã merge vào
    project gốc dùng QFN64..._cut), components.create dùng lại definition cũ, pin không khớp tên -> component 0 pin
    (lỗi thấy ở U21 khi cắt lại sau merge)."""
    CD = edb.core.Definition.ComponentDef
    name, i = base, 2
    while not CD.FindByName(edb.active_db, name).IsNull():
        name = f"{base}_{i}"
        i += 1
    return name


def detach_pins(edb, comp, pins, rd, log):
    """Tách pin khỏi component cũ mà GIỮ NGUYÊN vị trí tuyệt đối.
    Toạ độ pin trong EDB là toạ độ cục bộ theo transform của component: chỉ RemoveMember thì pin bị dời đi đúng
    bằng vị trí đặt component (U14 board1 lệch -69.5, -85 mm). Nên: đọc vị trí/góc tuyệt đối -> RemoveMember
    -> đặt lại vị trí/góc tuyệt đối. Component mới (components.create, pin không thuộc component) có transform gốc."""
    tr = comp._edb_object.GetTransform()
    try:
        crot = tr.Rotation.ToDouble()
        mirror = bool(tr.Mirror)
    except Exception:
        crot, mirror = 0.0, False
    saved = []
    for p in pins:
        ok, _, lrot = p._edb_object.GetPositionAndRotationValue()
        x, y = p.position                                     # đã cộng transform component
        r = crot + (-lrot.ToDouble() if mirror else lrot.ToDouble()) if ok else crot
        saved.append((p, x, y, r))
    worst = 0.0
    for p, x, y, r in saved:
        try:
            comp._edb_object.RemoveMember(p._edb_object)
        except Exception as ex:
            log(f"  {rd}: RemoveMember lỗi: {ex}")
        pt = edb.core.Geometry.PointData(edb.edb_value(x), edb.edb_value(y))
        p._edb_object.SetPositionAndRotation(pt, edb.edb_value(r))
        nx, ny = p.position
        worst = max(worst, math.hypot(nx - x, ny - y))
    if worst > 1e-7:
        raise RuntimeError(f"{rd}: pin bị dời {worst / MM:.4f} mm khi tách khỏi component")
    if saved and (abs(crot) > 1e-9 or mirror):
        log(f"  {rd}: component xoay {math.degrees(crot):.1f}° mirror={mirror} -> pin đặt lại theo góc tuyệt đối")


def rebuild_kept_component(edb, rd, log):
    """BGA / through-hole: dựng lại component từ các pin còn lại để khung (bbox) ôm sát pin.
    Sau cutout EDB vẫn giữ khung thân linh kiện gốc (U14 board1: 45 x 45 mm thay vì ~5 x 7 mm)."""
    comp = edb.components.instances[rd]
    part, layer, ctype = comp.partname, comp.placement_layer, comp.type
    pins = list(comp.pins.values())
    if not pins:
        return
    before = comp.bounding_box
    detach_pins(edb, comp, pins, rd, log)
    edb.components.delete(rd)
    edb.components.create(pins, component_name=rd, placement_layer=layer,
                          component_part_name=unique_def_name(edb, f"{part}_cut"))
    edb.components.refresh_components()
    c = edb.components.instances[rd]
    if c.numpins != len(pins):
        raise RuntimeError(f"{rd}: component mới có {c.numpins} pin, cần {len(pins)}")
    try:
        if str(ctype).lower() == "ic":
            c.type = "IC"
    except Exception:
        pass
    b = c.bounding_box
    log(f"  {rd}: dựng lại component {len(pins)} pin, khung {(before[2] - before[0]) / MM:.1f}x{(before[3] - before[1]) / MM:.1f}"
        f" -> {(b[2] - b[0]) / MM:.1f}x{(b[3] - b[1]) / MM:.1f} mm")


# ----------------------------------------------------------------------------- GND cleanup
def cleanup_gnd(edb, P, nets, ends, bga_ends, extent_area, protect_ids, protect_polys, log, smd_ends=(),
                smd_protect=None, smd_reports=None):
    """smd_ends / smd_protect {refdes: tên pin} (021, chỉ design_cleanup): dọn pin GND riêng của đầu SMD / connector
    như lúc dựng lại (gnd_pins.select), report thêm vào list smd_reports; mặc định () = như trước."""
    cl = P["cleanup"]
    refs = set(P["cutout"]["reference_nets"])
    segs, pts = signal_segments(edb, nets)
    prims = [p for p in edb.modeler.primitives if p.net_name in refs and type(p).__name__ not in ("EdbPath", "Path")]
    area = {}
    for p in prims:
        area[p.layer_name] = area.get(p.layer_name, 0) + p.area()
    planes = {l for l, a in area.items() if a > 0.5 * extent_area}
    log("  lớp plane GND:", sorted(planes))
    biggest = {}
    for p in prims:
        if p.layer_name in planes:
            biggest[p.layer_name] = max(biggest.get(p.layer_name, 0), p.area())

    Dsh = float(cl["shield_keep_dist_mm"]) * MM
    Amin = float(cl["shield_min_area_mm2"]) * MM * MM
    shields = {}                                            # id -> (layer, pts)
    n_frag = n_far = n_small = 0
    for p in prims:
        if p.id in protect_polys:
            continue
        a = p.area()
        if p.layer_name in planes:
            if a < float(cl["island_min_ratio"]) * biggest[p.layer_name]:
                p.delete(); n_frag += 1
            continue
        if a < Amin:
            p.delete(); n_small += 1
            continue
        ppts = G.prim_points(p)
        if dist_poly_layer_signal(ppts, segs.get(p.layer_name, [])) > Dsh:
            p.delete(); n_far += 1
            continue
        shields[p.id] = (p.layer_name, ppts)
    n_path = 0
    for p in list(edb.layout.paths):
        if p.net_name not in refs or p.layer_name in planes:
            continue
        c = p.center_line
        ppts = [(c[i][0], c[i][1]) for i in range(len(c))]
        lsegs = segs.get(p.layer_name, [])
        d = min((G.seg_seg_dist((ppts[i][0], ppts[i][1], ppts[i + 1][0], ppts[i + 1][1]), s[:4]) - s[4]
                 for i in range(len(ppts) - 1) for s in lsegs), default=1.0) - p.width / 2
        if d > Dsh:
            p.delete(); n_path += 1
    log(f"  GND: xoá {n_frag} mảnh vụn lớp plane, {n_small} mảnh nhỏ + {n_far} mảng xa tín hiệu lớp signal, "
        f"{n_path} path GND xa; giữ {len(shields)} shield")

    # BGA: chỉ giữ pin GND quanh pin tín hiệu
    R = float(cl["bga_gnd_pin_keep_dist_mm"]) * MM
    n_pin = 0
    for rd in bga_ends:
        c = edb.components.instances[rd]
        sp = [p.position for p in c.pins.values() if p.net_name in nets]
        for p in list(c.pins.values()):
            if p.net_name in refs and min(math.hypot(p.position[0] - a, p.position[1] - b) for a, b in sp) > R:
                p.delete(); n_pin += 1
    for rd in smd_ends:                                                 # 021: đầu SMD / connector (design_cleanup)
        c = edb.components.instances[rd]
        sig = [p for p in c.pins.values() if p.net_name in nets]
        gp = [p for p in c.pins.values() if p.net_name in refs and p.id not in protect_ids]
        _, drop, rep = prune_own_gnd_pins(P, rd, sig, gp, (smd_protect or {}).get(rd) or ())
        for p in drop:
            p.delete()
        if smd_reports is not None:
            smd_reports.append(rep)
        log(f"  {rd}: pin GND {rep['gnd_pins_before']} -> {rep['gnd_pins_after']}" +
            ("; " + "; ".join(rep["warnings"] + rep["info"]) if rep["warnings"] or rep["info"] else ""))

    # đồng GND còn lại trên lớp signal: pad GND của linh kiện, plane tự tạo, shield
    copper_boxes, copper_polys = {}, {}
    for rd in ends:
        for p in edb.components.instances[rd].pins.values():
            if p.net_name in refs:
                for lay in (p.start_layer, p.stop_layer):
                    copper_boxes.setdefault(lay, []).append(p.bounding_box)
    for p in edb.modeler.primitives:
        if p.id in protect_polys:
            copper_polys.setdefault(p.layer_name, []).append(G.prim_points(p))
    for lay, ppts in shields.values():
        copper_polys.setdefault(lay, []).append(ppts)

    def has_copper(lay, x, y):
        return (lay in planes
                or any(b[0][0] <= x <= b[1][0] and b[0][1] <= y <= b[1][1] for b in copper_boxes.get(lay, []))
                or any(G.point_in_poly(x, y, q) for q in copper_polys.get(lay, [])))

    order = list(edb.stackup.signal_layers)
    D = float(cl["gnd_via_keep_dist_mm"]) * MM
    Dm = float(cl["gnd_microvia_keep_dist_mm"]) * MM
    n_via = n_uvia = 0
    for v in list(edb.padstacks.instances.values()):
        if v.net_name not in refs or v.is_pin or v.id in protect_ids:
            continue
        x, y = v.position
        d = dist_point_signal(x, y, segs, pts)
        if v.start_layer == order[0] and v.stop_layer == order[-1]:
            if d > D:
                v.delete(); n_via += 1
        elif d > Dm or not (has_copper(v.start_layer, x, y) and has_copper(v.stop_layer, x, y)):
            v.delete(); n_uvia += 1

    # shield phải còn via/pin GND nối vào
    n_float = 0
    if cl["shield_need_via"] and shields:
        gnd_ps = [(v.position, layers_of(v)) for v in edb.padstacks.instances.values() if v.net_name in refs]
        for p in list(edb.modeler.primitives):
            if p.id in shields:
                lay, ppts = shields[p.id]
                if not any(lay in lays and G.point_in_poly(pos[0], pos[1], ppts) for pos, lays in gnd_ps):
                    p.delete(); n_float += 1
    log(f"  xoá {n_pin} pin GND BGA (> {R / MM:g} mm), {n_via} via PTH GND (> {D / MM:g} mm), "
        f"{n_uvia} microvia GND (xa/treo), {n_float} shield không có via")
    return planes


# ----------------------------------------------------------------------------- series / solder ball
def set_series_zero_ohm(edb, P, series, log):
    r = float(P["series"]["model_r_ohm"])
    for rd in series:
        ok = False
        try:
            ok = call_filtered(edb.components.set_component_rlc, componentname=rd, res_value=r, ind_value=None,
                               cap_value=None, isparallel=False)
        except Exception as ex:
            log(f"  set_component_rlc {rd} lỗi: {ex}")
        try:
            c = edb.components.instances[rd]
            if str(c.type).lower() != "resistor":
                c.type = "Resistor"
            c.res_value = r
            ok = True
        except Exception as ex:
            log(f"  đặt R {rd} lỗi: {ex}")
        log(f"  {rd}: R = {r:g} ohm {'OK' if ok else 'LỖI'}")


def set_solder_ball(edb, P, rd, nets, short_side=None, log=print):
    sb = P["solder_ball"]
    cm = comp_model(P, rd)                                              # 038: per-end values (default = template)
    comp = edb.components.instances[rd]
    if short_side is None:
        sig = [p for p in comp.pins.values() if p.net_name in nets]
        (x0, y0), (x1, y1) = sig[0].bounding_box
        short_side = min(x1 - x0, y1 - y0)
    diam = float(cm["ball_ratio"]) * short_side
    h = float(cm["ball_height_mm"]) * MM
    extra = {}
    if str(cm["ball_material"] or "") != str(sb.get("material") or ""):   # template material: as before (not written)
        extra["material_name"] = str(cm["ball_material"])
    try:
        call_filtered(edb.components.set_solder_ball, component=rd, sball_diam=diam, sball_height=h,
                      shape=str(cm["ball_shape"]).capitalize(), auto_reference_size=True, **extra)
        # PyEDB ghi số không đơn vị (0.0002) -> AEDT hiểu sai. Ghi lại đường kính / chiều cao kèm "mm".
        c = edb.components.instances[rd]._edb_object
        cp = c.GetComponentProperty().Clone()
        sbp = cp.GetSolderBallProperty().Clone()
        ds, hs = f"{round(diam / MM, 4):g}mm", f"{round(h / MM, 4):g}mm"
        sbp.SetDiameter(edb.edb_value(ds), edb.edb_value(ds))
        sbp.SetHeight(edb.edb_value(hs))
        cp.SetSolderBallProperty(sbp)
        if not c.SetComponentProperty(cp):
            raise RuntimeError("SetComponentProperty trả False")
        log(f"  {rd}: solder ball {sb['shape']} Ø{diam / MM:.3f} mm, cao {h / MM:.2f} mm")
        return diam
    except Exception as ex:
        log(f"  CẢNH BÁO {rd}: không đặt được solder ball: {ex}")
        return None


DIE_DEFAULT = ("flip_chip", "chip_down")                               # what PyEDB set_solder_ball writes on an IC


def set_die(edb, P, rd, log=print):
    """038: die type / orientation / height of an IC end (Component Model). Template default (flip chip, chip
    down, no height) = nothing written (as before). Non-IC component: nothing to set."""
    cm = comp_model(P, rd)
    dt, do, dh = str(cm["die_type"]), str(cm["die_orientation"]), float(cm["die_height_mm"] or 0)
    if (dt, do) == DIE_DEFAULT and not dh:
        return None
    try:
        c = edb.components.instances[rd]._edb_object
        D = edb.api_class.Definition
        if c.GetComponentType() != D.ComponentType.IC:
            log(f"  {rd}: die properties only for IC components (skipped)")
            return None
        cp = c.GetComponentProperty().Clone()
        dp = cp.GetDieProperty().Clone()
        dp.SetType({"none": D.DieType.NoDie, "flip_chip": D.DieType.FlipChip, "wire_bond": D.DieType.WireBond}[dt])
        dp.SetOrientation(D.DieOrientation.ChipUp if do == "chip_up" else D.DieOrientation.ChipDown)
        if dt == "wire_bond":
            dp.SetHeight(edb.edb_value(f"{dh:g}mm"))
        cp.SetDieProperty(dp)
        if not c.SetComponentProperty(cp):
            raise RuntimeError("SetComponentProperty returned False")
        log(f"  {rd}: die {dt}, {do}" + (f", height {dh:g} mm" if dt == "wire_bond" else ""))
        return dt
    except Exception as ex:
        log(f"  CẢNH BÁO {rd}: không đặt được die: {ex}")
        return None


# ----------------------------------------------------------------------------- setup / airbox
def apply_setup(edb, P, log):
    import json
    s, w = P["setup"], P["sweep"]
    stop = f"{w['stop_ghz']}GHz"
    af = stop if str(s["adaptive_freq"]).lower() in ("auto", "max", "") else f"{s['adaptive_freq']}GHz"
    st = edb.create_hfss_setup(s["name"])
    multi = json.loads(s["multi_freqs"]) if s.get("solution_mode") == "multi" and s.get("multi_freqs") else None
    if multi:                                                           # 038: Multi-Frequencies, ΔS per row
        a = st.adaptive_settings
        a.adapt_type = "kMultiFrequencies"
        a.clean_adaptive_frequency_data_list()
        for f, ds in multi:
            a.add_adaptive_frequency_data(f"{float(f):g}GHz", int(s.get("multi_max_passes") or 10), float(ds))
        af = ", ".join(f"{float(f):g}GHz" for f, _ in multi)
    else:
        st.set_solution_single_frequency(af, max_num_passes=int(s["max_passes"]), max_delta_s=float(s["max_delta_s"]))
    a = st.adaptive_settings
    for k, v in (("max_refine_per_pass", int(s["max_refine_per_pass"])), ("min_passes", int(s["min_passes"])),
                 ("min_converged_passes", int(s["min_converged_passes"]))):
        try: setattr(a, k, v)
        except Exception as ex: log("  setup", k, "lỗi", ex)
    hs = st.hfss_solver_settings
    try:
        hs.order_basis = str(s["basis_order"]).lower()
    except Exception:
        core = getattr(hs, "_hfss_solver_settings", None)
        if core is not None:
            core.OrderBasis = {"zero": 0, "first": 1, "second": 2, "mixed": -1}[str(s["basis_order"]).lower()]
    try:
        st.hfss_port_settings.max_delta_z0 = float(s["max_delta_zo"])
    except Exception as ex:
        log("  delta Zo lỗi", ex)
    if s.get("arc_step_deg") is not None:                       # Advanced Meshing: circle / arc approximation (004)
        try:
            st.curve_approx_settings.arc_angle = f"{float(s['arc_step_deg']):g}deg"
        except Exception as ex:
            log("  arc step lỗi", ex)
    apply_vias(st, s, log)
    apply_sweep(st, P, log)
    log(f"  setup adaptive {af} ΔS={s['max_delta_s']} | sweep {w['start_ghz']}-{w['stop_ghz']} GHz bước {w['step_ghz']} GHz")


VIA_ON, VIA_OFF = "k25DViaMesh", "k25DViaWirebond"


def apply_vias(st, s, log):
    """038: Advanced / Vias. via_mesh_3d true + 6 sides = AEDT default of a new setup: nothing written (as before)."""
    on = s.get("via_mesh_3d")
    sides = s.get("via_num_sides")
    if on is None or (on and (sides is None or int(sides) == 6)):
        return
    try:
        v = st.via_settings
        v.via_style = VIA_ON if on else VIA_OFF
        if on:
            v.via_num_sides = int(sides)
        log(f"  vias: {'3D mesh' if on else 'not meshed'}" + (f", {int(sides)} sides" if on else ""))
    except Exception as ex:
        log("  via settings lỗi", ex)


def sweep_frequency_set(w):
    """038: frequency set of the sweep: sweep.ranges JSON [[dist, start, end, step|count|samples]] else start/stop/step."""
    import json
    rg = json.loads(w["ranges"]) if w.get("ranges") else None
    if not rg:
        return [["linear scale", f"{w['start_ghz']}GHz", f"{w['stop_ghz']}GHz", f"{w['step_ghz']}GHz"]]
    out = []
    for d, a, b, v in rg:
        if d == "linear_step":
            out.append(["linear scale", f"{float(a):g}GHz", f"{float(b):g}GHz", f"{float(v):g}GHz"])
        elif d == "linear_count":
            out.append(["linear count", f"{float(a):g}GHz", f"{float(b):g}GHz", int(v)])
        elif d == "log_scale":
            out.append(["log scale", f"{float(a):g}GHz", f"{float(b):g}GHz", int(v)])
        else:
            raise ValueError(f"sweep.ranges: unknown distribution {d!r}")
    return out


def apply_sweep(st, P, log):
    """Xoá mọi sweep của setup st, tạo sweep theo P['sweep'] (tách từ apply_setup, 007 - cùng lệnh, cùng kết quả).
    038: nhiều dải (sweep.ranges), Q3D cho điểm DC (sweep.use_q3d_dc)."""
    w = P["sweep"]
    for k in list(st.sweeps):
        st.delete_frequency_sweep(st.sweeps[k])                  # sweep mặc định của PyEDB
    st.add_sweep(name=w["name"], frequency_set=sweep_frequency_set(w),
                 discrete=str(w["type"]).lower() == "discrete")
    sw = st.sweeps[w["name"]]
    if w.get("use_q3d_dc"):
        try:
            sw.use_q3d_for_dc = True
        except Exception as ex:
            log("  sweep use_q3d_for_dc lỗi", ex)
    for k, v in (("max_solutions", int(w["max_solutions"])), ("relative_s_error", float(w["error_tolerance_pct"]) / 100),
                 ("enforce_causality", bool(w["enforce_causality"])), ("enforce_passivity", bool(w["enforce_passivity"])),
                 ("passivity_tolerance", float(w["passivity_tolerance"]))):
        try: setattr(sw, k, v)
        except Exception as ex: log("  sweep", k, "lỗi", ex)


def port_name(rd, pin_key, p):
    return f"{rd}.{p.pin_number or pin_key}.{p.net_name}"


def create_ports(edb, rd, nets, log=None, replace=False, existing=None):
    """Coax port cho mỗi pin của rd thuộc nets, tên <refdes>.<pin>.<net> (tách từ apply_stage, 007).
    existing: tên port đã có (None = đọc từ edb.ports); trùng tên -> bỏ qua, hoặc xoá trước khi replace."""
    nets = set(nets)
    if existing is None:
        try:
            existing = set(dict(edb.ports))
        except Exception:
            existing = set()
    created, skipped = [], []
    for pn, p in edb.components.instances[rd].pins.items():
        if p.net_name not in nets:
            continue
        name = port_name(rd, pn, p)
        if name in existing:
            if not replace:
                skipped.append({"item": name, "reason": "port exists"})
                continue
            try:
                dict(edb.ports)[name].delete()
            except Exception as ex:
                skipped.append({"item": name, "reason": f"cannot delete old port: {ex}"})
                continue
        p.create_coax_port(name=name)
        created.append(name)
    if log:
        log(f"  {rd}: {len(created)} coax port, {len(skipped)} skipped")
    return {"created": created, "skipped": skipped}


def reapply_sim(edb, P_old, P_new, log):
    """006: chỉ ghi lại setup / sweep / arc step / airbox của thiết kế đã apply (không đụng hình học, linh kiện,
    port, solder ball). Xoá setup cũ (tên cũ và tên mới) rồi tạo lại như lần apply đầu. Người gọi lưu EDB."""
    names = {n for n in ((P_old or {}).get("setup", {}).get("name"), P_new["setup"]["name"]) if n}
    for n in sorted(names):
        try:
            st = dict(edb.setups).get(n)
            if st is not None:
                st.delete()
                log("  xoá setup cũ:", n)
        except Exception as ex:
            log("  xoá setup", n, "lỗi", ex)
    apply_setup(edb, P_new, log)
    apply_airbox(edb, P_new)


def apply_airbox(edb, P):
    a = P["airbox"]
    h = edb.hfss.hfss_extent_info
    h.extent_type = a["extent_type"]
    h.dielectric_extent_type = a["dielectric_extent_type"]
    h.air_box_horizontal_extent = float(a["horizontal"])
    h.air_box_positive_vertical_extent = float(a["positive_z"])
    h.air_box_negative_vertical_extent = float(a["negative_z"])     # 038 Sync: the config writes negative = positive
    if a.get("dielectric_horizontal"):                                  # 038: dielectric padding (0 = as before)
        h.set_dielectric_extent(float(a["dielectric_horizontal"]), True)
    if hasattr(h, "use_xy_data_extent_for_vertical_expansion"):
        h.use_xy_data_extent_for_vertical_expansion = not bool(a["z_from_stackup"])
    h.open_region_type = a["open_region"]
    h.operating_freq = a["operating_freq"]


# ----------------------------------------------------------------------------- metrics
def collect_metrics(edb, P, nets, ends):
    refs = set(P["cutout"]["reference_nets"])
    try:
        edb.components.refresh_components()        # cache PyEDB còn giữ linh kiện đã xoá -> cảnh báo giả
    except Exception:
        pass
    gnd = {}
    for p in edb.modeler.primitives:
        if p.net_name in refs and type(p).__name__ not in ("EdbPath", "Path"):
            g = gnd.setdefault(p.layer_name, [0, 0.0])
            g[0] += 1
            g[1] += p.area() / (MM * MM)
    comps = {}
    for rd, c in edb.components.instances.items():
        comps[rd] = {"part": c.partname, "pins": c.numpins,
                     "gnd_pins": sum(1 for p in c.pins.values() if p.net_name in refs)}
        try:                                       # khung component vs vùng chứa pin (phát hiện khung thân gốc còn sót)
            b = c.bounding_box
            ps = [p.position for p in c.pins.values()]
            comps[rd]["bbox_mm"] = [round((b[2] - b[0]) / MM, 2), round((b[3] - b[1]) / MM, 2)]
            if ps:
                comps[rd]["pins_extent_mm"] = [round((max(q[0] for q in ps) - min(q[0] for q in ps)) / MM, 2),
                                               round((max(q[1] for q in ps) - min(q[1] for q in ps)) / MM, 2)]
        except Exception:
            pass
    inst = list(edb.padstacks.instances.values())
    return {
        "nets": sorted(edb.nets.netlist),
        "components": comps,
        "ports": len(edb.ports),
        "gnd_by_layer": {k: {"count": v[0], "area_mm2": round(v[1], 2)} for k, v in gnd.items()},
        "gnd_vias": sum(1 for v in inst if v.net_name in refs and not v.is_pin),
        "padstacks": len(inst),
    }


def check(metrics, ch, P):
    """Danh sách cảnh báo tự kiểm tra."""
    w = []
    ends = [ch["comp_a"], ch["comp_b"]]
    for rd in ends:
        c = metrics["components"].get(rd)
        if not c:
            w.append(f"Thiếu linh kiện {rd}")
        elif c["gnd_pins"] == 0:
            w.append(f"{rd} không có pin GND -> port không có tham chiếu")
    sig_pins = sum(metrics["components"].get(rd, {}).get("pins", 0) - metrics["components"].get(rd, {}).get("gnd_pins", 0)
                   for rd in ends)
    if metrics["ports"] != sig_pins:
        w.append(f"Số port {metrics['ports']} khác số pin tín hiệu ở 2 đầu {sig_pins}")
    for rd in ends:
        c = metrics["components"].get(rd) or {}
        b, e = c.get("bbox_mm"), c.get("pins_extent_mm")
        if b and e and (b[0] > e[0] + 3 or b[1] > e[1] + 3):
            w.append(f"{rd}: khung component {b[0]}x{b[1]} mm lớn hơn nhiều vùng pin {e[0]}x{e[1]} mm")
    if metrics.get("max_pin_shift_mm", 0) > 1.0:
        w.append(f"Pin tín hiệu bị dời {metrics['max_pin_shift_mm']} mm so với board gốc")
    extra = set(metrics["components"]) - set(ends) - set(ch.get("series", {}))
    if extra:
        w.append(f"Còn linh kiện thừa: {sorted(extra)}")
    for lay, g in metrics["gnd_by_layer"].items():
        if "GND" in lay.upper() and g["count"] > 1:
            w.append(f"Lớp {lay} còn {g['count']} mảnh GND")
    return w


# ----------------------------------------------------------------------------- main (1.0.0: cut_channel một lượt của luồng Excel đã bỏ; dùng cut_stage + apply_stage)
def remove_partial(dst, log=print):
    """Xoá .aedb làm dở do chính lần cắt này tạo (chỉ gọi khi dst chưa tồn tại trước khi cắt)."""
    import shutil
    if not os.path.isdir(dst):
        return False
    for i in range(5):                                   # EDB có thể còn giữ file vài giây sau close
        try:
            shutil.rmtree(dst)
            log(f"  đã xoá kết quả dở {dst}")
            return True
        except OSError as ex:
            err = ex
            time.sleep(2)
    log(f"  CẢNH BÁO: không xoá được kết quả dở {dst}: {err}")
    return False


def channel_sets(ch, P):
    """-> (nets, ends, keep, refs) như cut_channel tính (net 2 bên linh kiện nối tiếp, linh kiện giữ lại)."""
    nets = list(ch["nets"]) + [n for s in ch.get("series", {}).values() for n in s.get("nets", [])
                               if n not in P["cutout"]["reference_nets"]]
    nets = sorted(set(nets))
    ends = [ch["comp_a"], ch["comp_b"]]
    keep = set(ends) | (set(ch.get("series", {})) if P["series"]["keep"] else set())
    refs = list(P["cutout"]["reference_nets"])
    return nets, ends, keep, refs


def cut_extent(edb, P, nets, ends, log, end_factors=None, strict=True, extent=None):
    """022: vùng cutout = hệ số nền + luật GND ở 2 đầu (+ hệ số tay từng đầu). DÙNG CHUNG cho cut_stage và preview
    (isim_cut_preview) -> cùng thông số = cùng extent. -> (điểm mm, end_gnd).
    extent (027): extent(factor) thay compute_extent_mm (preview trên snapshot: extent của AEDT đã lưu cache);
    None = tính trên edb như trước (cut)."""
    from . import end_gnd as EG
    if extent is None:
        pts = compute_extent_mm(edb, P, nets, log)
        fn = lambda f: compute_extent_mm(edb, P, nets, lambda *a: None, factor=f)
    else:
        pts, fn = extent(None), extent
    return EG.apply_rule(edb, P, nets, ends, pts, fn, log, manual=end_factors, strict=strict)


def cut_stage(edb, ch, P, cell, dst, mode, log, nets, ends, keep, refs, keep_pads=None, end_factors=None):
    """Bước 1 (nặng): kiểm tra net/linh kiện, đo trên board gốc (BGA/TH, khung thân, vị trí pin tín hiệu), extent,
    cutout, xoá cell khác, đổi tên cell, xoá linh kiện không giữ. edb: board gốc (hoặc bản copy) mở ghi.
    Trả stage1 (dict; ghi JSON bằng stage1_to_json).
    019: stage1['gnd_pads_outside'] = pad GND của đầu SMD nằm ngoài vùng cutout (gnd_decision.outside_pads);
    keep_pads {refdes}: vùng cutout ∪ (pad + lề) -> giữ pad đó (extent_base_pts_mm, kept_pads).
    022: stage1['end_gnd'] = luật GND ở 2 đầu (end_gnd.apply_rule): vùng đầu mất pin GND được mở rộng riêng."""
    from . import gnd_decision as GD
    missing = [n for n in nets if n not in set(edb.nets.netlist)]
    if missing:
        raise RuntimeError(f"Net không có trong board: {missing}")
    for rd in ends:
        if rd not in edb.components.instances:
            raise RuntimeError(f"Không có linh kiện {rd}")
    bga_ends = [rd for rd in ends if is_bga_or_th(edb.components.instances[rd], nets)]
    bodies = {rd: comp_bbox(edb.components.instances[rd]) for rd in ends if rd not in bga_ends}
    sig_pos0 = {(rd, p.net_name): [] for rd in ends for p in edb.components.instances[rd].pins.values()
                if p.net_name in nets}
    for rd in ends:
        for p in edb.components.instances[rd].pins.values():
            if p.net_name in nets:
                sig_pos0[(rd, p.net_name)].append(tuple(p.position))
    from . import stackup_check as SC
    try:
        board_stackup = SC.read(edb)                                    # 042: reference for self-check / merge
    except Exception as ex:
        board_stackup = None
        log(f"  board stackup unreadable: {type(ex).__name__}: {ex}")
    with log.step("extent"):                             # 022: luật GND ở 2 đầu (+ hệ số tay), như preview
        pts, end_gnd = cut_extent(edb, P, nets, ends, log, end_factors=end_factors)
        facts = {rd: GD.outside_pads(edb, P, rd, set(nets), pts) for rd in ends if rd not in bga_ends}
        facts = {rd: f for rd, f in facts.items() if f}
        extra = {}
        if keep_pads:
            bad = [rd for rd in keep_pads if not (facts.get(rd) or {}).get("touches")]
            if bad:
                raise RuntimeError(f"gnd_keep_pad: {bad} has no GND pad outside the cut extent that touches it")
            base = pts
            pts = [tuple(q) for q in GD.extend_extent(pts, [r for rd in sorted(keep_pads) for r in facts[rd]["rects_mm"]])]
            extra = {"extent_base_pts_mm": [list(q) for q in base],
                     "kept_pads": {rd: [p["pin"] for p in facts[rd]["pads"]] for rd in sorted(keep_pads)}}
            log(f"  extent + pad GND {extra['kept_pads']}: {len(pts)} điểm")
            facts = {rd: f for rd, f in ((rd, GD.outside_pads(edb, P, rd, set(nets), pts)) for rd in facts) if f}
    with log.step("cutout"):
        kw = dict(signal_nets=nets, reference_nets=refs, custom_extent=pts, custom_extent_units="mm",
                  remove_single_pin_components=True, keep_voids=True, check_terminals=False,
                  preserve_components_with_model=False)
        if mode == "create_new":
            kw.update(output_aedb_path=dst, open_cutout_at_end=True)
        edb.cutout(**kw)
        if mode == "create_new":
            for c in list(edb.active_db.CircuitCells):
                if c.GetName() != cell:
                    c.Delete()
            edb.active_cell.SetName(ch["name"])
    with log.step("components"):
        for rd, c in list(edb.components.instances.items()):
            if rd in keep:
                continue
            pins = list(c.pins.values())
            edb.components.delete(rd)
            for p in pins:
                try: p.delete()
                except Exception: pass
    return {"nets": nets, "ends": ends, "keep": sorted(keep), "refs": refs, "bga_ends": bga_ends,
            "board_stackup": board_stackup,
            "bodies": bodies, "sig_pos0": sig_pos0, "extent_pts_mm": pts,
            "extent_area_m2": G.poly_area(pts) * MM * MM, "gnd_pads_outside": facts, "end_gnd": end_gnd, **extra}


def apply_stage(edb, stage1, ch, P, log, protect_polys=None, handling=None):
    """Bước 2: R nối tiếp 0 ohm, dựng lại component SMD, dọn GND, dựng lại BGA/TH, coax port, solder ball,
    setup/sweep, airbox, lưu, metrics. edb: thiết kế sau cut_stage (cùng phiên hoặc mở lại bản lưu), mở ghi.
    handling {refdes: 'keep_component' | 'no_solder_ball' | 'smd_rebuild' | 'gnd_plate_vias' |
    'gnd_existing_copper'}: None = như luồng cũ. 015: đầu SMD không pin GND cần gnd_plate_vias / gnd_existing_copper
    (người dùng chọn), không có -> RuntimeError. metrics['gnd_reference']: tham chiếu GND dùng cho từng đầu."""
    handling = handling or {}
    gnd_reference = {}
    protect_polys = set() if protect_polys is None else protect_polys
    nets, ends, bga_ends = stage1["nets"], stage1["ends"], stage1["bga_ends"]
    bodies, sig_pos0 = stage1["bodies"], stage1["sig_pos0"]
    with log.step("components_rebuild"):
        if P["series"]["keep"] and ch.get("series"):
            set_series_zero_ohm(edb, P, [rd for rd in ch["series"] if rd in edb.components.instances], log)
        protect_ids, short_sides, port_loc = set(), {}, {}
        for rd in ends:                                                 # 041: what happened to the port position
            cm = comp_model(P, rd)
            port_loc[rd] = ({"requested": "centre", "note": "BGA / through-hole: pad centre"} if rd in bga_ends else
                            {"requested": cm["port_location"], "explicit": cm["port_location_explicit"],
                             "note": "component kept (not rebuilt)"})
        if P["port"]["smd_new_component"]:
            for rd in ends:
                if rd not in bga_ends and handling.get(rd) != "keep_component":
                    from . import gnd_pins as GP                          # 021: pin GND không bao giờ xoá
                    cm, port_loc[rd] = comp_model(P, rd), {}
                    ids, W, gnd_reference[rd] = rebuild_smd_component(edb, P, rd, nets, bodies[rd], protect_polys,
                                                                      log, gnd_choice=handling.get(rd),
                                                                      protect_names=GP.protected_names(stage1, rd),
                                                                      port_location=cm["port_location"],
                                                                      explicit=cm["port_location_explicit"],
                                                                      port_report=port_loc[rd],
                                                                      port_pct=cm["port_pct"])
                    protect_ids |= ids
                    eg = ((stage1.get("end_gnd") or {}).get("ends") or {}).get(rd) or {}
                    if eg.get("result") in ("enlarged", "manual"):        # 022: pad GND giữ nhờ mở rộng vùng đầu
                        pv = vias_in_gnd_pads(edb, P, rd)
                        protect_ids |= pv
                        gnd_reference[rd] = dict(gnd_reference[rd], end_gnd={
                            "factor": eg.get("factor"), "pins": [p["pin"] for p in eg.get("gnd_pins_gained") or []],
                            "pad_vias": len(pv)})
                        log(f"  {rd}: {len(pv)} via GND trong pad GND (vùng đầu mở rộng) được giữ")
                    if handling.get(rd) == "gnd_keep_pad":                # 019: via GND trong pad giữ lại
                        pv = vias_in_gnd_pads(edb, P, rd)
                        protect_ids |= pv
                        gnd_reference[rd] = dict(gnd_reference[rd], pad_vias=len(pv))
                        log(f"  {rd}: {len(pv)} via GND trong pad GND được giữ (không dọn)")
                    short_sides[rd] = W
    with log.step("cleanup_gnd"):
        cleanup_gnd(edb, P, set(nets), ends, bga_ends, stage1["extent_area_m2"], protect_ids, protect_polys, log)
        for rd in bga_ends:                              # sau cleanup (đã xoá pin GND BGA xa)
            if handling.get(rd) != "keep_component":
                rebuild_kept_component(edb, rd, log)
    with log.step("ports_models_setup"):
        n = 0
        for rd in ends:
            n += len(create_ports(edb, rd, nets, existing=set())["created"])
        log("  coax port:", n)
        # pin tín hiệu không được dời xa vị trí trên board gốc (SMD chỉ dời trong pad, < 1 mm)
        shift = 0.0
        for (rd, net), olds in sig_pos0.items():
            news = [tuple(p.position) for p in edb.components.instances[rd].pins.values() if p.net_name == net]
            for o in olds:
                shift = max(shift, min((math.hypot(o[0] - q[0], o[1] - q[1]) for q in news), default=1.0))
        log(f"  pin tín hiệu lệch tối đa so với board gốc: {shift / MM:.3f} mm")
        if P["solder_ball"]["enable"]:
            for rd in ends:
                if handling.get(rd) != "no_solder_ball" and comp_model(P, rd)["ball_shape"] != "none":
                    set_solder_ball(edb, P, rd, set(nets), short_sides.get(rd), log)
        for rd in ends:                                                 # 038: die properties chosen per end
            set_die(edb, P, rd, log)
        apply_setup(edb, P, log)
        apply_airbox(edb, P)
    with log.step("save"):
        edb.save()
    metrics = collect_metrics(edb, P, nets, ends)
    metrics["max_pin_shift_mm"] = round(shift / MM, 4)
    metrics["arc_step_deg"] = read_arc_step(edb, P["setup"]["name"])
    for rd in ends:
        if rd not in gnd_reference:
            gnd_reference[rd] = {"kind": "own_pins" if rd in bga_ends else "none (kept component)"}
        elif handling.get(rd) == "gnd_keep_pad":                     # 019: pin GND = pad giữ lại nhờ mở rộng cutout
            gnd_reference[rd] = dict(gnd_reference[rd], kind="kept_pad")
    metrics["gnd_reference"] = gnd_reference
    metrics["port_location"] = port_loc                                 # 041: per end requested / moved / not moved
    metrics["gnd_pin_cleanup"] = [g["gnd_pin_cleanup"] for _, g in sorted(gnd_reference.items())   # 021
                                  if isinstance(g, dict) and g.get("gnd_pin_cleanup")]
    return metrics


def deg(text):
    """'10deg' / '10' / 10 -> 10.0."""
    t = str(text).strip().lower()
    return float(t[:-3] if t.endswith("deg") else t)


def read_arc_step(edb, setup_name):
    """Arc step (deg) đọc lại từ setup; None nếu không đọc được."""
    try:
        return deg(edb.setups[setup_name].curve_approx_settings.arc_angle)
    except Exception:
        return None


def stage1_to_json(stage1):
    """stage1 -> dict ghi JSON được (key (rd, net) -> 'rd|net', tuple -> list)."""
    d = dict(stage1)
    d["sig_pos0"] = {f"{rd}|{net}": [list(p) for p in v] for (rd, net), v in stage1["sig_pos0"].items()}
    d["bodies"] = {rd: (list(b) if b is not None else None) for rd, b in stage1["bodies"].items()}
    d["extent_pts_mm"] = [list(p) for p in stage1["extent_pts_mm"]]
    return d


def stage1_from_json(d):
    s = dict(d)
    s["sig_pos0"] = {tuple(k.split("|", 1)): [tuple(p) for p in v] for k, v in d["sig_pos0"].items()}
    s["bodies"] = {rd: (tuple(b) if b is not None else None) for rd, b in d["bodies"].items()}
    s["extent_pts_mm"] = [tuple(p) for p in d["extent_pts_mm"]]
    return s
