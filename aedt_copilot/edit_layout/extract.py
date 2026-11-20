"""Đọc hình học một VÙNG của EDB (mm) -> dict JSON được. Không đọc cả board ra file như cách cũ (54 MB)."""
import time

from ..core.units import MM


def _inbox(b, xs, ys):
    return not (max(xs) < b[0] or min(xs) > b[2] or max(ys) < b[1] or min(ys) > b[3])


def _bbox_fast(p):
    """bbox (mm) qua .NET, không tessellate; None nếu không đọc được."""
    try:
        core = getattr(p, "core", None) or p._edb_object
        bb = core.GetPolygonData().GetBBox()
        a, b = bb.Item1, bb.Item2
        return a.X.ToDouble() / MM, a.Y.ToDouble() / MM, b.X.ToDouble() / MM, b.Y.ToDouble() / MM
    except Exception:
        return None


def signal_layers(edb):
    return [n for n, l in edb.stackup.layers.items() if l.type == "signal"]


def pad_table(edb, names, scale=MM):
    """scale: chia số đo (MM -> mm). 029: snapshot build gọi scale=1.0 (giữ số gốc, đọc lại chia MM -> y hệt live)."""
    MM = scale
    out = {}
    defs = edb.padstacks.definitions
    for name in names:
        pd = defs.get(name)
        if pd is None:
            continue
        dd, ap = {}, {}
        try:
            for ln, pad in pd.pad_by_layer.items():
                try:
                    dd[ln] = [str(getattr(pad, "geometry_type", pad.shape)), [float(x) / MM for x in pad.parameters_values]]
                except Exception:
                    dd[ln] = [str(pad.shape), []]
        except Exception as ex:
            dd["err"] = str(ex)
        try:
            for ln, pad in pd.antipad_by_layer.items():
                try:
                    ap[ln] = [str(pad.shape), [float(x) / MM for x in pad.parameters_values]]
                except Exception:
                    ap[ln] = [str(pad.shape), []]
        except Exception:
            pass
        try:
            hole = float(pd.hole_properties[0]) / MM
        except Exception:
            hole = None
        out[name] = {"pads": dd, "antipads": ap, "hole": hole}
    return out


def extract_region(edb, bbox, layers=None, extra_pdefs=(), log=None, arc_segments=16):
    """bbox = [x0, y0, x1, y1] mm. layers = None -> mọi lớp signal."""
    t0 = time.time()
    sig = signal_layers(edb)
    want = set(layers or sig)
    D = {"box": list(bbox), "signal_layers": sig, "prims": [], "instances": [], "comps": {}}
    # pyedb 0.85 chỉ dựng lại cache primitive khi SỐ LƯỢNG đổi -> sau khi sửa (tạo + xoá) danh sách cũ, sai
    try:
        edb.layout.clear_cache()
    except Exception:
        pass
    for p in edb.layout.primitives:
        try:
            ln = p.layer_name
            if ln not in want:
                continue
            bb = _bbox_fast(p)
            if bb and not _inbox(bbox, [bb[0], bb[2]], [bb[1], bb[3]]):
                continue
            t = str(p.type).lower()
            d = {"id": p.id, "layer": ln, "net": p.net_name, "type": t, "is_void": bool(p.is_void)}
            if t == "path":
                try:
                    d["center_line"] = [[q[0] / MM, q[1] / MM] for q in p.center_line]
                    d["width"] = p.width / MM
                except Exception:
                    pass
            xs, ys = p.points(arc_segments=arc_segments)
            xs = [x / MM for x in xs]
            ys = [y / MM for y in ys]
            if not xs or not _inbox(bbox, xs, ys):
                continue
            d["poly"] = [[x, y] for x, y in zip(xs, ys)]
            d["voids"] = []
            if t != "path":
                for vo in p.voids:
                    vx, vy = vo.points(arc_segments=arc_segments)
                    if vx and _inbox(bbox, [x / MM for x in vx], [y / MM for y in vy]):
                        d["voids"].append([[x / MM, y / MM] for x, y in zip(vx, vy)])
            D["prims"].append(d)
        except Exception as ex:
            D["prims"].append({"err": str(ex)[:200]})
    if log:
        log(f"  vùng: {len(D['prims'])} primitive ({time.time() - t0:.1f} s)")
    used = set(extra_pdefs)
    for pid, v in edb.padstacks.instances.items():
        try:
            x, y = v.position[0] / MM, v.position[1] / MM
            if not (bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]):
                continue
            comp = ""
            if v.is_pin:
                try:
                    comp = v.component.refdes
                except Exception:
                    comp = ""
            D["instances"].append([pid, v.padstack_definition, v.net_name, x, y, v.start_layer, v.stop_layer,
                                   comp, bool(v.is_pin)])
            used.add(v.padstack_definition)
        except Exception:
            pass
    D["pdefs"] = pad_table(edb, sorted(used))
    for rd in sorted({i[7] for i in D["instances"] if i[7]}):
        try:
            c = edb.components.instances[rd]
            D["comps"][rd] = {"layer": c.placement_layer, "bbox": [b / MM for b in c.bounding_box]}
        except Exception:
            pass
    if log:
        log(f"  vùng: {len(D['instances'])} via/pin, {len(D['comps'])} linh kiện ({time.time() - t0:.1f} s)")
    return D
