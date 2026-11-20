"""Đọc EDB (đã mở CHỈ ĐỌC bởi người gọi) ra index / window của snapshot (feature 023).

Gọi .NET trực tiếp (không bọc PyEDB từng object trong vòng lặp lớn); các giá trị mà review đọc qua PyEDB được tính
bằng CÙNG lời gọi .NET / cùng làm tròn như PyEDB 0.85 (bbox 9 số, vị trí via/pin 6 số + transform linh kiện, độ dài
path = tổng ArcData + đầu tròn). Không lưu EDB.
"""
import time
from array import array

import shapely

from . import SCHEMA_VERSION
from .arcs import to_coords
from .key import overlap
from .store import pack


def _bbox9(pd):
    bb = pd.GetBBox()
    return [round(bb.Item1.X.ToDouble(), 9), round(bb.Item1.Y.ToDouble(), 9),
            round(bb.Item2.X.ToDouble(), 9), round(bb.Item2.Y.ToDouble(), 9)]


def _raw(pd):
    return [(q.X.ToDouble(), q.Y.ToDouble()) for q in list(pd.Points)]


class _Timer:
    def __init__(self):
        self.t, self.times = time.perf_counter(), {}

    def lap(self, name):
        now = time.perf_counter()
        self.times[name] = round(now - self.t, 2)
        self.t = now


# ----------------------------------------------------------------------------- index (cả board)
def build_index(edb, key, refs, log=None):
    """-> (index dict, live) ; live = {prim id: .NET primitive} để build_window dùng lại trong cùng phiên."""
    log = log or (lambda *a: None)
    T = _Timer()
    layout = edb.active_layout
    st = edb.stackup
    metal = list(st.signal_layers)
    layers = [[n, float(st.layers[n].lower_elevation), float(st.layers[n].thickness)] for n in metal]
    nets, power = [], []
    for n in list(layout.Nets):
        name = n.GetName()
        nets.append(name)
        try:
            if n.IsPowerGround():
                power.append(name)
        except Exception:
            pass
    T.lap("nets")
    prims, live = [], {}
    for p in list(layout.Primitives):
        if not p:
            continue
        pid = p.GetId()
        try:
            kind = p.GetPrimitiveType().ToString()
        except Exception:
            kind = "?"
        try:
            lay = p.GetLayer().GetName()
        except Exception:
            lay = ""
        try:
            net = p.GetNet().GetName()
        except Exception:
            net = ""
        try:
            bb = _bbox9(p.GetPolygonData())
        except Exception:
            bb = None
        prims.append([pid, kind, lay, net, bool(p.IsVoid()), bb])
        live[pid] = p
    T.lap("primitives")
    log(f"[snapshot] {len(prims)} primitives ({T.times['primitives']} s)")
    insts = []
    for v in list(layout.PadstackInstances):
        iid = v.GetId()
        try:
            net = v.GetNet().GetName()
        except Exception:
            net = ""
        try:
            pdef = v.GetPadstackDef().GetName()
        except Exception:
            pdef = ""
        x = y = None
        comp = v.GetComponent()
        out = v.GetPositionAndRotationValue()
        if out[0]:
            pt = out[1]
            if comp:                                            # như PyEDB EDBPadstackInstance.position
                t = comp.GetTransform()
                if t is not None:
                    pt = t.TransformPoint(pt)
            x, y = round(pt.X.ToDouble(), 6), round(pt.Y.ToDouble(), 6)
        _, a, b = v.GetLayerRange()
        cname = "" if comp is None or comp.IsNull() else comp.GetName()
        insts.append([iid, net, pdef, x, y, a.GetName() if a else None, b.GetName() if b else None,
                      bool(v.IsLayoutPin()), cname, v.GetName()])
    T.lap("padstack_instances")
    log(f"[snapshot] {len(insts)} padstack instances ({T.times['padstack_instances']} s)")
    comps = {}
    for rd, c in edb.components.instances.items():
        try:
            comps[rd] = {"type": c.type, "part": c.partname, "numpins": c.numpins, "layer": c.placement_layer,
                         "pins": [el.GetId() for el in c.pinlist]}
        except Exception as ex:
            log(f"[snapshot] component {rd}: {ex}")
    _comp_boxes(edb, comps, log)
    T.lap("components")
    # diện tích polygon lớn nhất (net tham chiếu, lớp) - cả board (luật lớp plane)
    plane = {}
    for rn in refs:
        rows = [r for r in prims if r[3] == rn and not r[4] and r[1] != "Path" and r[5]]
        rows.sort(key=lambda r: -(r[5][2] - r[5][0]) * (r[5][3] - r[5][1]))
        best = {}
        for r in rows:
            lay, bb = r[2], r[5]
            if (bb[2] - bb[0]) * (bb[3] - bb[1]) <= best.get(lay, [0.0])[0]:
                continue
            try:
                p = live[r[0]]
                a = p.GetPolygonData().Area()
                for el in p.Voids:
                    a -= el.GetPolygonData().Area()
            except Exception:
                continue
            if a > best.get(lay, [0.0])[0]:
                best[lay] = [a, r[0], bb]
        if best:
            plane[rn] = best
    T.lap("plane_area")
    defs = _pad_defs(edb, sorted({r[2] for r in insts if r[2]}))
    from ..edit_layout.extract import pad_table
    try:
        names = sorted(edb.padstacks.definitions)
    except Exception:
        names = sorted({r[2] for r in insts if r[2]})
    ptab = pad_table(edb, names, scale=1.0)                 # 029: số gốc (layout_region chia MM như live)
    T.lap("padstack_defs")
    index = {"schema_version": SCHEMA_VERSION, "kind": "index", "key": key, "refs": list(refs),
             "built_at": time.strftime("%Y-%m-%d %H:%M:%S"), "layers": layers, "nets": nets, "power_nets": power,
             "prims": prims, "insts": insts, "comps": comps, "plane_area": plane, "pad_defs": defs, "pad_table": ptab,
             "times": T.times}
    return index, live


def _comp_boxes(edb, comps, log):
    """029: comps[rd]['bbox'] = PyEDB Component.bounding_box (LayoutObjInstance.GetBBox, round 6, m); LayoutInstance
    lấy MỘT lần (PyEDB lấy lại mỗi linh kiện). Lỗi -> None (layout_region bỏ linh kiện như live)."""
    try:
        li = edb.active_layout.GetLayoutInstance()
        inst = edb.components.instances
    except Exception as ex:
        log(f"[snapshot] component boxes: {ex}")
        li, inst = None, {}
    for rd, d in comps.items():
        d["bbox"] = None
        try:
            bb = li.GetLayoutObjInstance(inst[rd].edbcomponent, None).GetBBox()
            d["bbox"] = [round(bb.Item1.X.ToDouble(), 6), round(bb.Item1.Y.ToDouble(), 6),
                         round(bb.Item2.X.ToDouble(), 6), round(bb.Item2.Y.ToDouble(), 6)]
        except Exception:
            pass


def _pad_defs(edb, names):
    """Giá trị mà Board.padstack_dims đọc (hole_diameter / hole_properties[0] / pad_by_layer[..].parameters_values),
    chuỗi có đơn vị -> số qua edb_value như si() làm. Thiếu khoá = PyEDB báo lỗi khi đọc."""
    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            try:
                return float(edb.edb_value(str(v)).ToDouble())
            except Exception:
                return None
    out = {}
    defs = edb.padstacks.definitions
    for n in names:
        d = {}
        try:
            pd = defs[n]
        except Exception:
            continue
        try:
            d["hole_diameter"] = num(pd.hole_diameter)
        except Exception:
            pass
        try:
            d["hole_props0"] = num(pd.hole_properties[0])
        except Exception:
            pass
        try:
            pads = getattr(pd, "pad_by_layer", {}) or {}
            d["pads"] = {}
            for l, pad in pads.items():
                try:
                    d["pads"][l] = [num(v) for v in (pad.parameters_values or [])][:2]
                except Exception:
                    d["pads"][l] = None
        except Exception:
            d["pads"] = None
        out[n] = d
    return out


# ----------------------------------------------------------------------------- window
def _path_length(p):
    """Như PyEDB Path.length: tổng ArcData của center line + nửa bề rộng ở mỗi đầu không phẳng."""
    L = 0.0
    for arc in list(p.GetCenterLine().GetArcData()):
        L += arc.GetLength()
    caps = p.GetEndCapStyle()
    if caps[0]:
        w = p.GetWidth()
        if not caps[1].value__ == 1:
            L += w / 2
        if not caps[2].value__ == 1:
            L += w / 2
    return L


def _poly_wkb(pd, tol):
    """-> (wkb, số điểm, invalid, điểm gốc float64 bytes). Điểm gốc = PolygonData.Points (cả điểm đánh dấu cung):
    029 layout_region đổi cung như PyEDB points() -> y hệt live."""
    raw = _raw(pd)
    ext = to_coords(raw, tol)
    holes = []
    try:
        for h in list(pd.Holes):
            hc = to_coords(_raw(h), tol)
            if len(hc) >= 3:
                holes.append(hc)
    except Exception:
        pass
    if len(ext) < 3:
        raise ValueError(f"{len(ext)} points")
    g = shapely.Polygon(ext, holes)                         # không make_valid (dời cạnh); chỉ đếm
    return (shapely.to_wkb(g), len(ext) + sum(len(h) for h in holes), not g.is_valid,
            array("d", [c for q in raw for c in q]).tobytes())


def build_window(edb, index, live, window, tol, log=None):
    """window (m) hoặc None = cả board. -> (window dict, geom bytes)."""
    from pyedb.dotnet.database.edb_data.padstacks_data import EDBPadstackInstance
    log = log or (lambda *a: None)
    T = _Timer()
    metal = {l[0] for l in index["layers"]}
    power = set(index["power_nets"])
    blobs, geoms, paths, unsupported = [], {}, {}, []
    npts, invalid = 0, 0
    counts = {}
    for pid, kind, lay, net, is_void, bb in index["prims"]:
        if lay not in metal or bb is None or not overlap(window, bb):
            continue
        p = live.get(pid)
        if p is None:
            unsupported.append({"id": pid, "layer": lay, "net": net, "reason": "not found in the layout"})
            continue
        try:
            wkb, n, bad, rawb = _poly_wkb(p.GetPolygonData(), tol)
            invalid += bad
            g = {"o": len(blobs), "r": len(blobs) + 1}
            blobs += [wkb, rawb]
            npts += n
            vs = []
            for v in list(p.Voids):
                vpd = v.GetPolygonData()
                vb = _bbox9(vpd)
                if not overlap(window, vb):
                    continue
                vw, vn, vbad, vraw = _poly_wkb(vpd, tol)
                invalid += vbad
                vs.append([v.GetId(), vb, len(blobs)])
                blobs += [vw, vraw]
                npts += vn
            g["v"] = vs
            geoms[str(pid)] = g
            if kind == "Path":
                paths[str(pid)] = {"c": _raw(p.GetCenterLine()), "w": p.GetWidth(), "l": _path_length(p)}
            c = counts.setdefault(lay, {})
            c[kind] = c.get(kind, 0) + 1
        except Exception as ex:
            unsupported.append({"id": pid, "layer": lay, "net": net, "reason": str(ex)[:200]})
    T.lap("geometry")
    log(f"[snapshot] window: {len(geoms)} primitives, {npts} points ({T.times['geometry']} s)")
    backdrill, pin_bbox = {}, {}
    by_id = {}
    for v in list(edb.active_layout.PadstackInstances):
        by_id[v.GetId()] = v
    li = None
    for iid, net, pdef, x, y, a, b, is_pin, comp, name in index["insts"]:
        if x is None or net in power or not net or not overlap(window, (x, y, x, y)):
            continue
        w = EDBPadstackInstance(by_id[iid], edb)
        try:
            if is_pin:
                # = PyEDB bounding_box (layout object instance GetBBox); LayoutInstance lấy MỘT lần (PyEDB lấy lại
                # mỗi pin: 65 ms / pin, ở đây 12 µs)
                if li is None:
                    li = edb.active_layout.GetLayoutInstance()
                bb = li.GetLayoutObjInstance(by_id[iid], None).GetBBox()
                pin_bbox[str(iid)] = [[bb.Item1.X.ToDouble(), bb.Item1.Y.ToDouble()],
                                      [bb.Item2.X.ToDouble(), bb.Item2.Y.ToDouble()]]
            else:
                backdrill[str(iid)] = w.backdrill_parameters
        except Exception as ex:
            unsupported.append({"id": iid, "layer": a, "net": net, "reason": f"padstack: {str(ex)[:150]}"})
    T.lap("pins_vias")
    log(f"[snapshot] window: {len(pin_bbox)} pin boxes, {len(backdrill)} vias ({T.times['pins_vias']} s)")
    geom, refs = pack(blobs)
    for g in geoms.values():
        g["o"], g["r"] = list(refs[g["o"]]), list(refs[g["r"]])
        g["v"] = [[vid, vb, *refs[k], *refs[k + 1]] for vid, vb, k in g["v"]]
    win = {"schema_version": SCHEMA_VERSION, "kind": "window", "index_key": index["key"],
           "window": list(window) if window else None, "scope": "board" if window is None else "window",
           "arc_tol_um": round(tol * 1e6, 6), "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
           "geoms": geoms, "paths": paths, "backdrill": backdrill, "pin_bbox": pin_bbox,
           "unsupported": unsupported, "counts": {"by_layer": counts, "points": npts, "invalid_polygons": invalid,
                                                   "primitives": len(geoms), "pins": len(pin_bbox),
                                                   "vias": len(backdrill)},
           "geom_bytes": len(geom), "times": T.times}
    return win, geom
