"""Review layout TRƯỚC khi cắt (Phase 1): chỉ đọc board, xuất báo cáo HTML tự chứa (ảnh SVG, bảng sắp xếp được).

Kiểm tra (xem skill aedt-copilot-review-layout):
  SOV            đoạn trace mà lớp tham chiếu kề (trên/dưới) không có đồng GND bên dưới
  Loss of ref    đoạn trace không có đồng GND trên MỌI lớp tham chiếu kề
  Ref change     tín hiệu đổi lớp qua via và bộ lớp tham chiếu thay đổi; NOT OK nếu không có via GND <= ngưỡng
  Via stub       stub = phần thân via ngoài lớp dùng (sau backdrill)
  Nearest GND    via GND / pin GND gần nhất cho mỗi via tín hiệu
  Length         chiều dài trace + thân via giữa các lớp dùng; skew trong cặp/bộ 3 và giữa các nhóm

Định nghĩa dùng trong code:
  lớp plane      lớp có polygon GND lớn nhất >= plane_area_ratio x polygon GND lớn nhất của board
  lớp tham chiếu lớp plane gần nhất phía trên và phía dưới lớp trace (lớp ngoài chỉ có 1)
  via stack      các via cùng net, tâm cách nhau <= stack_merge_mm (microvia xếp chồng) gộp thành 1
"""
import datetime as dt
import html
import json
import math
import os

from ..core.unique import claim_file
from . import __version__, config, inspect_board, naming
from . import review_report as RR
from . import review_units as RU

MM = 1e-3
BIG = 1e3          # toạ độ > 1 km = dữ liệu cung tròn trong center_line, bỏ
NOK, OK = "NOT OK", "OK"                 # 036: mỗi luật chỉ OK / NOT OK theo ngưỡng (không còn mức nặng nhẹ)
STATUS_ORDER = {NOK: 0, OK: 1}


# ----------------------------------------------------------------------------- geometry helpers
def _bbox_hit(b, x, y):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def _bbox_overlap(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def _pts(path):
    return [(float(p[0]), float(p[1])) for p in path.center_line if abs(p[0]) < BIG and abs(p[1]) < BIG]


class Copper:
    """Hỏi nhanh: điểm (x, y) trên lớp L có đồng của net tham chiếu không (tính cả void)."""

    CELL = 0.5 * MM

    def __init__(self, edb, ref_prims, window):
        PD = edb.core.Geometry.PointData
        ev = edb.edb_value
        self._pt = lambda x, y: PD(ev(x), ev(y))
        self.ref_prims, self.window = ref_prims, window
        self.layers = {}
        self.n_calls = 0

    def _build(self, lay):
        """Dựng chỉ mục cho 1 lớp (lười: chỉ lớp nào được hỏi)."""
        window = self.window
        out = []
        for bb, prim in self.ref_prims.get(lay, []):
            if not _bbox_overlap(bb, window):
                continue
            voids, grid = [], {}
            try:
                vs = prim.voids
            except Exception:
                vs = []
            for v in vs:
                vb = v.bbox
                if not _bbox_overlap(vb, window):
                    continue
                k = len(voids)
                voids.append((vb, v.polygon_data.core))
                for gx in range(int(vb[0] // self.CELL), int(vb[2] // self.CELL) + 1):
                    for gy in range(int(vb[1] // self.CELL), int(vb[3] // self.CELL) + 1):
                        grid.setdefault((gx, gy), []).append(k)
            try:
                net = prim.net_name
            except Exception:
                net = ""
            out.append((bb, prim.polygon_data.core, voids, grid, net))
        self.layers[lay] = out
        return out

    def voids_at(self, lay, x, y):
        """{(i polygon, k void)} chứa điểm - dùng để nhận antipad của chính via tín hiệu."""
        items = self.layers.get(lay)
        if items is None:
            items = self._build(lay)
        pt, key, out = None, (int(x // self.CELL), int(y // self.CELL)), set()
        for i, (bb, pd, voids, grid, _n) in enumerate(items):
            for k in grid.get(key, ()):
                if _bbox_hit(voids[k][0], x, y):
                    pt = pt or self._pt(x, y)
                    if voids[k][1].PointInPolygon(pt):
                        out.add((i, k))
        return out

    def net_at(self, lay, x, y):
        """Tên net của đồng phủ điểm (x, y) trên lớp lay, None nếu không có đồng."""
        self.n_calls += 1
        items = self.layers.get(lay)
        if items is None:
            items = self._build(lay)
        if not items:
            return None
        pt = None
        key = (int(x // self.CELL), int(y // self.CELL))
        for bb, pd, voids, grid, net in items:
            if not _bbox_hit(bb, x, y):
                continue
            pt = pt or self._pt(x, y)
            if not pd.PointInPolygon(pt):
                continue
            if any(_bbox_hit(voids[k][0], x, y) and voids[k][1].PointInPolygon(pt) for k in grid.get(key, ())):
                continue
            return net or "?"
        return None

    def covered(self, lay, x, y):
        return self.net_at(lay, x, y) is not None

    def shape(self, lay, win):
        """R12: đồng của lớp lay trong khung win (m) = hợp các primitive trừ void, cắt theo khung (shapely; cung =
        dây cung mịn). Không đọc được -> None (ảnh vẽ lưới như cũ)."""
        try:
            from shapely.geometry import box
            from shapely.ops import unary_union
            clip = box(*win)
            out = []
            for bb, prim in self.ref_prims.get(lay, []):
                if not _bbox_overlap(bb, win):
                    continue
                g = _pd_geom(prim.polygon_data)
                try:
                    vs = prim.voids
                except Exception:
                    vs = []
                holes = [_pd_geom(v.polygon_data) for v in vs if _bbox_overlap(v.bbox, win)]
                holes = [h for h in holes if h is not None and not h.is_empty]
                if g is None or g.is_empty:
                    continue
                if holes:
                    g = g.difference(unary_union(holes))
                g = g.intersection(clip)
                if not g.is_empty:
                    out.append(g)
            return unary_union(out) if out else clip.difference(clip)
        except Exception:
            return None


def _pd_geom(pd):
    """polygon_data -> shapely Polygon (m). Snapshot: hình dây cung có sẵn; EDB live: polygon bỏ cung (.NET)."""
    from shapely.geometry import Polygon
    core = pd.core
    if hasattr(core, "geom"):
        g = core.geom()
    else:
        p = core.GetPolygonWithoutArcs()
        g = Polygon([(q.X.ToDouble(), q.Y.ToDouble()) for q in p.Points])
    return g if g.is_valid else g.buffer(0)


def _geom_path(g, fill, extra=""):
    """R12: hình shapely (m) -> 1 <path> SVG even-odd (y lật như _svg_open); rỗng -> ''."""
    if g is None or g.is_empty:
        return ""
    d = []
    for p in getattr(g, "geoms", [g]):
        if p.geom_type == "Polygon":
            for ring in (p.exterior, *p.interiors):
                d.append("M" + " L".join(f"{x / MM:.4f},{-y / MM:.4f}" for x, y in ring.coords) + "Z")
        elif hasattr(p, "geoms"):
            sub = _geom_path(p, fill)
            if sub:
                d.append(sub.split('d="', 1)[1].split('"', 1)[0])
    return f'<path d="{" ".join(d)}" fill="{fill}" fill-rule="evenodd"{extra}/>' if d else ""


def _plane_svg(cu, oc, pl, win, col, ngrid, gnd_extra="", other=False):
    """R12: đồng GND lớp pl (+ đồng net khác ngoài GND) trong khung: vector khi đọc được hình, không thì lưới cũ."""
    shape = getattr(cu, "shape", None)
    g = shape(pl, win) if callable(shape) else None
    og = None
    if other and oc is not None:
        oshape = getattr(oc, "shape", None)
        og = oshape(pl, win) if callable(oshape) else None
    if g is not None and (not other or oc is None or og is not None):
        s = [_geom_path(g, col, gnd_extra)]
        if og is not None:
            s.append(_geom_path(og.difference(g), "#f6c28b"))
        return "".join(s)
    x0, y0, x1, y1 = win                                       # lưới cũ (đồng giả không có hình)
    dx, dy = (x1 - x0) / ngrid, (y1 - y0) / ngrid
    s = []
    for j in range(ngrid):
        y = y0 + (j + 0.5) * dy
        row = [cu.covered(pl, x0 + (i + 0.5) * dx, y) for i in range(ngrid)]
        for i0, i1 in _runs(row):
            s.append(f'<rect x="{(x0 + i0 * dx) / MM:.4f}" y="{-(y0 + (j + 1) * dy) / MM:.4f}" '
                     f'width="{(i1 - i0 + 1) * dx / MM:.4f}" height="{dy * 1.05 / MM:.4f}" fill="{col}"{gnd_extra} '
                     f'shape-rendering="crispEdges"/>')
        if other and oc is not None:
            orow = [(not c) and oc.covered(pl, x0 + (i + 0.5) * dx, y) for i, c in enumerate(row)]
            for i0, i1 in _runs(orow):
                s.append(f'<rect x="{(x0 + i0 * dx) / MM:.4f}" y="{-(y0 + (j + 1) * dy) / MM:.4f}" '
                         f'width="{(i1 - i0 + 1) * dx / MM:.4f}" height="{dy * 1.05 / MM:.4f}" fill="#f6c28b" '
                         f'shape-rendering="crispEdges"/>')
    return "".join(s)


# ----------------------------------------------------------------------------- board model
class Board:
    def __init__(self, edb, refs, R):
        self.edb, self.refs, self.R = edb, set(refs), R
        st = edb.stackup
        self.metal = list(st.signal_layers)                      # trên -> dưới
        self.idx = {n: i for i, n in enumerate(self.metal)}
        self.elev = {}
        for n in self.metal:
            l = st.layers[n]
            lo = float(l.lower_elevation)
            self.elev[n] = (lo, lo + float(l.thickness))
        # đồng tham chiếu: polygon + path của net tham chiếu, theo lớp
        self.ref_prims, biggest = {}, {}
        for rn in self.refs:
            if rn not in edb.nets.nets:
                continue
            for p in edb.nets.nets[rn].primitives:
                try:
                    if p.is_void:
                        continue
                    lay = p.layer_name
                    bb = p.bbox
                except Exception:
                    continue
                self.ref_prims.setdefault(lay, []).append((bb, p))
                if type(p).__name__ not in ("EdbPath", "Path") and (bb[2] - bb[0]) * (bb[3] - bb[1]) > biggest.get(lay, 0.0):
                    try:
                        biggest[lay] = max(biggest.get(lay, 0.0), float(p.area()))   # diện tích thật (trừ void)
                    except Exception:
                        pass
        top = max(biggest.values(), default=0.0)
        self.planes = [n for n in self.metal if top and biggest.get(n, 0.0) >= float(R["plane_area_ratio"]) * top]
        # via/pin GND
        self.gnd_ps = []
        for rn in self.refs:
            if rn in edb.nets.nets:
                for v in edb.nets.nets[rn].padstack_instances:
                    try:
                        self.gnd_ps.append((float(v.position[0]), float(v.position[1]), v.is_pin))
                    except Exception:
                        pass

    def insts_in(self, window):
        """032: mọi padstack instance (via + pin, mọi net) có tâm trong cửa sổ -> [(x, y, net)] (đọc một lần)."""
        if getattr(self, "_insts", None) is None:
            out = []
            for v in self.edb.padstacks.instances.values():
                try:
                    out.append((float(v.position[0]), float(v.position[1]), v.net_name or ""))
                except Exception:
                    continue
            self._insts = out
        x0, y0, x1, y1 = window
        return [t for t in self._insts if x0 <= t[0] <= x1 and y0 <= t[1] <= y1]

    def other_prims(self, window, skip_nets):
        """Đồng của net KHÁC (không phải net tham chiếu, không thuộc channel) trên các lớp plane, trong window.
        Dùng để biết trace đang tham chiếu vào net nào khi lớp tham chiếu không có GND."""
        out = {}
        skip = set(skip_nets) | self.refs
        by_layer = getattr(self.edb.modeler, "primitives_by_layer", None)
        for lay in self.planes:
            try:
                prims = by_layer[lay] if by_layer is not None else [p for p in self.edb.modeler.primitives
                                                                      if p.layer_name == lay]
            except Exception:
                prims = []
            for p in prims:
                try:
                    if p.is_void or p.net_name in skip or not p.net_name:
                        continue
                    bb = p.bbox
                except Exception:
                    continue
                if _bbox_overlap(bb, window):
                    out.setdefault(lay, []).append((bb, p))
        return out

    def padstack_dims(self, name, layers=()):
        """(pad, hole) đường kính (m) của padstack definition; None nếu không đọc được. Có cache.
        pad = lớn nhất trên các lớp tín hiệu trong layers (bỏ lớp plane GND: ở đó pad = lỗ / antipad)."""
        layers = tuple(l for l in layers if l not in self.planes)
        cache = self.__dict__.setdefault("_ps_dims", {})
        if (name, layers) in cache:
            return cache[(name, layers)]

        def si(v):
            try:
                v = float(v)
            except (TypeError, ValueError):
                try:
                    v = float(self.edb.edb_value(str(v)).ToDouble())
                except Exception:
                    return None
            return v * MM if v > 0.05 else v        # > 5 cm thì chắc chắn đang ở mm
        pad = hole = None
        try:
            d = self.edb.padstacks.definitions[name]
            try:
                hole = si(d.hole_diameter)
            except Exception:
                try:
                    hole = si(d.hole_properties[0])
                except Exception:
                    pass
            pads = getattr(d, "pad_by_layer", {}) or {}
            use = [l for l in layers if l in pads] or [l for l in pads if l not in self.planes]
            sizes = []
            for l in use:
                try:
                    vals = [si(v) for v in (pads[l].parameters_values or [])][:2]
                    sizes += [v for v in vals if v]
                except Exception:
                    pass
            pad = max(sizes) if sizes else None
        except Exception:
            pass
        cache[(name, layers)] = (pad, hole)
        return pad, hole

    def ref_layers(self, lay):
        i = self.idx.get(lay)
        if i is None:
            return []
        up = [p for p in self.planes if self.idx[p] < i]
        dn = [p for p in self.planes if self.idx[p] > i]
        return ([up[-1]] if up else []) + ([dn[0]] if dn else [])

    def mid(self, lay):
        a, b = self.elev[lay]
        return (a + b) / 2

    def nearest_gnd(self, x, y):
        best = None
        for gx, gy, pin in self.gnd_ps:
            d = math.hypot(gx - x, gy - y)
            if best is None or d < best[0]:
                best = (d, gx, gy, pin)
        return best


# ----------------------------------------------------------------------------- channel data
def _chains(nets, series, start_nets, skip):
    """Gộp net qua linh kiện nối tiếp -> {net đầu: [net trong chuỗi]}."""
    parent = {n: n for n in nets}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for s in series.values():
        ns = [n for n in s.get("nets", []) if n in parent and n not in skip]
        for a, b in zip(ns, ns[1:]):
            parent[find(a)] = find(b)
    out = {}
    for s in start_nets:
        r = find(s)
        out[s] = sorted(n for n in nets if find(n) == r)
    return out


def _collect(edb, B, nets):
    paths, polys, vias, pins = [], [], [], []
    for n in nets:
        net = edb.nets.nets[n]
        for p in net.primitives:
            tn = type(p).__name__
            try:
                if tn in ("EdbPath", "Path"):
                    pts = _pts(p)
                    if len(pts) >= 2:
                        paths.append({"net": n, "layer": p.layer_name, "w": float(p.width), "pts": pts,
                                      "len": float(p.length)})
                elif not p.is_void:
                    polys.append({"net": n, "layer": p.layer_name, "bbox": p.bbox, "pd": p.polygon_data.core})
            except Exception:
                pass
        for v in net.padstack_instances:
            rng = [x for x in v.layer_range_names if x in B.idx] or [v.start_layer, v.stop_layer]
            item = {"net": n, "id": v.id, "x": float(v.position[0]), "y": float(v.position[1]),
                    "def": v.padstack_definition, "range": rng, "pin": v.is_pin}
            if v.is_pin:
                item["comp"] = v.component_name if hasattr(v, "component_name") else ""
                pins.append(item)
            else:
                try:
                    bd = v.backdrill_parameters
                except Exception:
                    bd = {}
                item["backdrill"] = bd
                vias.append(item)
    return paths, polys, vias, pins


def _stacks(vias, tol):
    """Gộp via cùng net xếp chồng / sát nhau."""
    out = []
    for v in sorted(vias, key=lambda a: (a["net"], a["x"], a["y"])):
        for s in out:
            if s["net"] == v["net"] and any(math.hypot(v["x"] - m["x"], v["y"] - m["y"]) <= tol for m in s["members"]):
                s["members"].append(v)
                break
        else:
            out.append({"net": v["net"], "members": [v]})
    return out


def _used_layers(B, stack, paths, polys, pins, pt):
    """Lớp mà tín hiệu thực sự nối vào stack (trace / polygon / pin), không tính nối via-via."""
    rng = sorted({l for m in stack["members"] for l in m["range"] if l in B.idx}, key=B.idx.get)
    used = set()
    for m in stack["members"]:
        r = 0.25 * MM                      # đầu trace / pin trong bán kính này quanh tâm via = nối vào via
        for p in paths:
            if p["net"] != stack["net"] or p["layer"] not in m["range"]:
                continue
            for q in (p["pts"][0], p["pts"][-1]):
                if math.hypot(q[0] - m["x"], q[1] - m["y"]) <= r + p["w"] / 2:
                    used.add(p["layer"])
        for g in polys:
            if g["net"] == stack["net"] and g["layer"] in m["range"] and _bbox_hit(g["bbox"], m["x"], m["y"]):
                try:
                    if g["pd"].PointInPolygon(pt(m["x"], m["y"])):
                        used.add(g["layer"])
                except Exception:
                    pass
        for q in pins:
            if q["net"] == stack["net"] and math.hypot(q["x"] - m["x"], q["y"] - m["y"]) <= r:
                used |= set(q["range"]) & set(m["range"])
    return rng, sorted(used, key=B.idx.get)


# ----------------------------------------------------------------------------- checks
def _runs(mask):
    """[(i0, i1)] các đoạn liên tiếp True."""
    out, s = [], None
    for i, m in enumerate(mask + [False]):
        if m and s is None:
            s = i
        elif not m and s is not None:
            out.append((s, i - 1))
            s = None
    return out


def _samples(pts, w, step):
    """Điểm mẫu dọc center line: [(x, y, [(x, y) tâm và 2 mép])]."""
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L <= 0:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy * w * 0.45, ux * w * 0.45
        n = max(1, int(L / step))
        for k in range(n):
            t = (k + 0.5) * L / n
            x, y = x0 + ux * t, y0 + uy * t
            out.append((x, y, ((x, y), (x + nx, y + ny), (x - nx, y - ny))))
    return out


CLEAR_TOL = 0.05 * MM               # 032: dung sai bán kính clearance quanh bao lồi các via trong void


def _void_info(B, cu, lay, i, k, cache):
    """032: void k của polygon i trên lớp lay -> {centers [(x, y, net)], r, hull, size (w, h)} hoặc None (không via)."""
    key = (lay, i, k)
    if key in cache:
        return cache[key]
    from shapely.geometry import MultiPoint
    vb, pd = cu.layers[lay][i][2][k]
    cs = []
    for x, y, net in B.insts_in(cu.window):
        if not net:                         # padstack không net (lỗ cơ khí / NPTH): void của nó là lỗ thật, không phải clearance
            continue
        if vb[0] <= x <= vb[2] and vb[1] <= y <= vb[3]:
            try:
                if pd.PointInPolygon(cu._pt(x, y)):
                    cs.append((x, y, net))
            except Exception:
                continue
    info = None
    if cs:
        w, h = vb[2] - vb[0], vb[3] - vb[1]
        info = {"centers": cs, "r": min(w, h) / 2 + CLEAR_TOL, "size": (w, h),
                "hull": MultiPoint([(x, y) for x, y, _ in cs]).convex_hull}
    cache[key] = info
    return info


def _classify(B, cu, oc, lay, pts, center, net, cache):
    """032: các điểm (tâm + 2 mép) chưa có GND trên lớp plane lay -> ('gap',) / ('onet', net khác) /
    ('other', via, info) / ('own',). Điểm ngoài mọi void có via (hoặc xa bao lồi các via) = khe thật."""
    from shapely.geometry import Point
    worst = None
    for x, y in pts:
        cls = None
        for i, k in sorted(cu.voids_at(lay, x, y)):
            info = _void_info(B, cu, lay, i, k, cache)
            if info is None or info["hull"].distance(Point(x, y)) > info["r"]:
                continue
            near = min(info["centers"], key=lambda c: (c[0] - x) ** 2 + (c[1] - y) ** 2)
            cls = ("own",) if near[2] == net else ("other", near, info)
            break
        if cls is None:
            k = (oc.net_at(lay, center[0], center[1]) if oc else None) or ""
            return ("onet", k) if k else ("gap",)
        if worst is None or (cls[0] == "other" and worst[0] == "own"):
            worst = cls
    return worst


def check_reference(B, cu, paths, excl_pts, R, step, oc=None):
    """SOV / tham chiếu sang net khác / loss of reference / trace qua clearance của via cho mọi trace của channel.
    032: mỗi mẫu, mỗi lớp plane tham chiếu: có GND / clearance via cùng net (không báo) / clearance via net khác /
    đồng net khác / khe thật. Một đoạn liên tiếp cùng nhãn = MỘT phát hiện: mọi lớp thiếu -> Loss of reference;
    một lớp thiếu -> SOV hoặc Ref to other net (NOT OK); chỉ clearance via net khác -> Trace over via clearance (OK,
    dữ liệu; 036: không còn mức HIGH / MEDIUM / INFO).
    oc: Copper của net khác trên lớp plane (None = không phân loại, mọi chỗ thiếu GND là khe)."""
    fs, cache = [], {}
    excl = float(R["pad_exclusion_mm"]) * MM
    for p in paths:
        refs = B.ref_layers(p["layer"])
        if not refs:
            continue
        smp = _samples(p["pts"], p["w"], step)
        if not smp:
            continue
        near = [(a, b) for a, b in excl_pts if any(math.hypot(x - a, y - b) <= 3 * MM for x, y, _ in smp[::20] + smp[-1:])]
        skip = [any(math.hypot(x - a, y - b) <= excl for a, b in near) for x, y, _ in smp]
        labels, info = [], []
        for (x, y, q), s in zip(smp, skip):
            if s:
                labels.append(None)
                info.append(None)
                continue
            st = {}
            for r in refs:
                bad = [b for b in q if not cu.covered(r, *b)]
                st[r] = _classify(B, cu, oc, r, bad, (x, y), p["net"], cache) if bad else ("cov",)
            miss = [r for r in refs if st[r][0] in ("gap", "onet")]
            if len(miss) == len(refs):
                lab = ("Loss of reference",)
            elif miss:
                r = miss[0]
                lab = ("Ref to other net", r, st[r][1]) if st[r][0] == "onet" else ("SOV", r)
            else:
                oth = tuple(r for r in refs if st[r][0] == "other")
                lab = ("Trace over via clearance", oth) if oth else None
            labels.append(lab)
            info.append(st)
        for lab in sorted({l for l in labels if l is not None}, key=str):
            for i0, i1 in _runs([l == lab for l in labels]):
                kind = lab[0]
                if kind == "Loss of reference":
                    f = _finding(kind, NOK, p, smp, i0, i1, step, ref=", ".join(refs))
                elif kind == "Ref to other net":
                    f = _finding(kind, NOK, p, smp, i0, i1, step, ref=f"{lab[1]}: {lab[2]}")
                    f["value"] = f"over {lab[2]} on {lab[1]} for {f['len_mm']:.3f} mm"
                    f["other_net"] = lab[2]
                elif kind == "SOV":
                    f = _finding(kind, NOK, p, smp, i0, i1, step, ref=lab[1])
                else:
                    vs, sz = {}, (0.0, 0.0)
                    for st in info[i0:i1 + 1]:
                        for r in lab[1]:
                            c, inf = st[r][1], st[r][2]
                            vs[(round(c[0], 9), round(c[1], 9))] = c
                            if inf["size"][0] * inf["size"][1] > sz[0] * sz[1]:
                                sz = inf["size"]
                    f = _finding(kind, OK, p, smp, i0, i1, step, ref=", ".join(lab[1]))
                    nets = sorted({c[2] for c in vs.values()})
                    f["value"] = (f"in the clearance of {len(vs)} via(s) of {', '.join(nets)} on {', '.join(lab[1])}; "
                                  f"void up to {sz[0] / MM:.2f} x {sz[1] / MM:.2f} mm over {f['len_mm']:.3f} mm")
                    f["void_mm"] = [round(sz[0] / MM, 3), round(sz[1] / MM, 3)]
                if kind != "Trace over via clearance":
                    vs = {}
                    for st in info[i0:i1 + 1]:
                        for r in refs:
                            if st[r][0] == "other":
                                c = st[r][1]
                                vs[(round(c[0], 9), round(c[1], 9))] = c
                f["vias"] = [[c[0], c[1], c[2]] for c in vs.values()]
                f["trace_pts"] = [(smp[i][0], smp[i][1]) for i in range(i0, i1 + 1)]
                fs.append(f)
    return fs


def _finding(check, status, p, smp, i0, i1, step, ref):
    a, b = smp[i0], smp[i1]
    L = (i1 - i0 + 1) * step
    return {"check": check, "status": status, "net": p["net"], "layer": p["layer"], "ref": ref,
            "x": (a[0] + b[0]) / 2, "y": (a[1] + b[1]) / 2, "start": (a[0], a[1]), "end": (b[0], b[1]),
            "value": f"no GND over {L / MM:.3f} mm", "len_mm": L / MM,
            "bbox": (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))}


def _mil_label(pad, hole):
    """Kiểu 18D8: pad 18 mil, lỗ khoan 8 mil (kèm mm)."""
    if not pad and not hole:
        return "size ?"

    def mil(v):
        if not v:
            return "?"
        return f"{v / 25.4e-6:.0f}"
    mm = "/".join(f"{v / MM:.3f}" if v else "?" for v in (pad, hole))
    return f"{mil(pad)}D{mil(hole)} ({mm} mm)"


def via_rows(B, stacks, paths, polys, pins, pt, R):
    rows, fs = [], []
    flag = float(R["gnd_via_flag_mm"]) * MM
    rc_lim = float(R["ref_change_gnd_via_mm"]) * MM
    for s in stacks:
        rng, used = _used_layers(B, s, paths, polys, pins, pt)
        x = sum(m["x"] for m in s["members"]) / len(s["members"])
        y = sum(m["y"] for m in s["members"]) / len(s["members"])
        bd = {}
        for m in s["members"]:
            bd.update(m.get("backdrill") or {})
        top, bot = rng[0], rng[-1]
        if len(used) >= 1:
            ut, ub = used[0], used[-1]
            stub_top = max(0.0, B.elev[top][1] - B.elev[ut][1])
            stub_bot = max(0.0, B.elev[ub][0] - B.elev[bot][0])
        else:
            ut = ub = None
            stub_top = stub_bot = 0.0
        if "from_bottom" in bd:
            try:
                stub_bot = float(str(bd["from_bottom"]["stub_length"]).replace("mm", "")) * (
                    MM if "mm" in str(bd["from_bottom"]["stub_length"]) else 1)
            except ValueError:
                pass
        if "from_top" in bd:
            try:
                stub_top = float(str(bd["from_top"]["stub_length"]).replace("mm", "")) * (
                    MM if "mm" in str(bd["from_top"]["stub_length"]) else 1)
            except ValueError:
                pass
        stub = stub_top + stub_bot
        barrel = abs(B.mid(ut) - B.mid(ub)) if ut else 0.0
        ng = B.nearest_gnd(x, y)
        outer = (B.metal[0], B.metal[-1])
        if len(s["members"]) > 1:
            kind = f"Stacked via x{len(s['members'])}"
        elif (top, bot) == outer:
            kind = "Through-hole via"
        elif top in outer or bot in outer:
            kind = "Blind via"
        else:
            kind = "Buried via"
        dims = []
        for m in sorted(s["members"], key=lambda m: B.idx.get(m["range"][0], 0)):
            pad, hole = B.padstack_dims(m["def"], m["range"])
            dims.append(_mil_label(pad, hole))
        row = {"net": s["net"], "x": x, "y": y, "defs": sorted({m["def"] for m in s["members"]}),
               "size": " + ".join(dict.fromkeys(dims)),
               "n_vias": len(s["members"]), "range": f"{top} → {bot}", "used": used, "kind": kind,
               "has_bd": bool(bd),
               "backdrill": "; ".join(f"{k}: {v.get('drill_to_layer')}" for k, v in bd.items()) or "no",
               "stub_mm": stub / MM, "barrel_mm": barrel / MM,
               "gnd": ng and {"x": ng[1], "y": ng[2], "d_mm": ng[0] / MM, "pin": ng[3]}}
        rows.append(row)
        bb = (x, y, x, y)
        if stub > 1e-9:
            fs.append({"check": "Via stub", "status": NOK, "net": s["net"], "layer": row["range"], "ref": "",
                       "x": x, "y": y, "value": f"stub {stub / MM:.3f} mm (top {stub_top / MM:.3f}, bottom {stub_bot / MM:.3f})",
                       "bbox": bb, "used": used})
        if ng and ng[0] > flag:
            fs.append({"check": "Nearest GND via", "status": NOK, "net": s["net"], "layer": row["range"],
                       "ref": "", "x": x, "y": y, "value": f"nearest GND via {ng[0] / MM:.3f} mm at "
                                                         f"({ng[1] / MM:.3f}, {ng[2] / MM:.3f})",
                       "bbox": (min(x, ng[1]), min(y, ng[2]), max(x, ng[1]), max(y, ng[2])), "used": used})
        if ut and ub and ut != ub:
            ra, rb = B.ref_layers(ut), B.ref_layers(ub)
            if set(ra) != set(rb):
                common = sorted(set(ra) & set(rb), key=B.idx.get)
                # Đổi lớp plane GND -> GND là bình thường nếu có via GND gần (đường hồi lưu).
                # NOT OK: không có via GND trong ngưỡng; có via GND trong ngưỡng -> OK (chỉ là dữ liệu).
                sev = NOK if (not ng or ng[0] > rc_lim) else OK
                val = f"nearest GND via {ng[0] / MM:.3f} mm" if ng else "no GND via"
                if common:
                    val += f"; shared reference {', '.join(common)}"
                fs.append({"check": "Ref plane change", "status": sev, "net": s["net"],
                           "layer": f"{ut} → {ub}", "ref": f"{', '.join(ra)} → {', '.join(rb)}", "x": x, "y": y,
                           "value": val,
                           "bbox": bb, "used": used})
    rows.sort(key=lambda r: -(r["gnd"]["d_mm"] if r["gnd"] else 1e9))
    return rows, fs


def _seg_dist(q, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((q[0] - ax) * dx + (q[1] - ay) * dy) / L2))
    return math.hypot(q[0] - ax - t * dx, q[1] - ay - t * dy)


def trace_stubs(paths, vias, pins, polys, pt):
    """Đầu trace hở (không nối pad/via/trace/polygon cùng net) và nhánh chữ T (đầu trace chạm giữa trace khác)."""
    fs = []
    r = 0.25 * MM
    for i, p in enumerate(paths):
        for q in (p["pts"][0], p["pts"][-1]):
            hw = p["w"] / 2
            ok = any(v["net"] == p["net"] and p["layer"] in v["range"] and
                     math.hypot(q[0] - v["x"], q[1] - v["y"]) <= r + hw for v in vias)
            ok = ok or any(v["net"] == p["net"] and p["layer"] in v["range"] and
                           math.hypot(q[0] - v["x"], q[1] - v["y"]) <= 2 * r + hw for v in pins)
            if not ok:
                for j, o in enumerate(paths):
                    if j == i or o["net"] != p["net"] or o["layer"] != p["layer"]:
                        continue
                    tol = hw + o["w"] / 2
                    if any(math.hypot(q[0] - e[0], q[1] - e[1]) <= tol for e in (o["pts"][0], o["pts"][-1])):
                        ok = True
                        break
                    if any(_seg_dist(q, a, b) <= tol for a, b in zip(o["pts"], o["pts"][1:])):
                        ok = "T"
                        break
            if not ok:
                for g in polys:
                    if g["net"] == p["net"] and g["layer"] == p["layer"] and _bbox_hit(g["bbox"], q[0], q[1]):
                        try:
                            if g["pd"].PointInPolygon(pt(q[0], q[1])):
                                ok = True
                                break
                        except Exception:
                            pass
            if ok is True:
                continue
            what = "trace branch (T-junction)" if ok == "T" else "open trace end"
            fs.append({"check": "Trace stub", "status": NOK, "net": p["net"], "layer": p["layer"], "ref": "",
                       "x": q[0], "y": q[1], "value": f"{what}; segment length {p['len'] / MM:.3f} mm",
                       "bbox": (q[0], q[1], q[0], q[1]), "used": [p["layer"]]})
    return fs


def lengths(chains, paths, vrows, groups):
    per_net = {}
    for p in paths:
        d = per_net.setdefault(p["net"], [0.0, 0.0])
        d[0] += p["len"] / MM
    for r in vrows:
        d = per_net.setdefault(r["net"], [0.0, 0.0])
        d[1] += r["barrel_mm"]
    by_lay, widths = {}, {}
    for p in paths:
        d = by_lay.setdefault(p["net"], {})
        d[p["layer"]] = d.get(p["layer"], 0.0) + p["len"] / MM
        widths.setdefault(p["layer"], set()).add(round(p["w"] / MM, 4))
    chain_len = {}
    for s, ns in chains.items():
        t = sum(per_net.get(n, [0, 0])[0] for n in ns)
        v = sum(per_net.get(n, [0, 0])[1] for n in ns)
        bl = {}
        for n in ns:
            for lay, L in by_lay.get(n, {}).items():
                bl[lay] = bl.get(lay, 0.0) + L
        chain_len[s] = {"nets": ns, "trace_mm": t, "via_mm": v, "total_mm": t + v, "by_layer": bl}
    intra = []
    for g in groups:
        L = [chain_len[n]["total_mm"] for n in g if n in chain_len]
        if L:
            lays = {n: tuple(sorted(l for l, v in chain_len[n]["by_layer"].items() if v > 0.01))
                    for n in g if n in chain_len}
            intra.append({"group": g, "lengths": {n: chain_len[n] for n in g if n in chain_len},
                          "skew_mm": max(L) - min(L), "mean_mm": sum(L) / len(L),
                          "same_layers": len(set(lays.values())) <= 1, "layers": lays})
    inter = None
    if len(intra) > 1:
        M = [x["mean_mm"] for x in intra]
        inter = {"means": {"/".join(x["group"]): x["mean_mm"] for x in intra}, "skew_mm": max(M) - min(M)}
    return chain_len, intra, inter, {k: sorted(v) for k, v in widths.items()}


# ----------------------------------------------------------------------------- SVG
def _svg_open(win, px=520):
    x0, y0, x1, y1 = win
    w, h = (x1 - x0) / MM, (y1 - y0) / MM
    H = px * h / w if w else px
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0 / MM:.4f} {-y1 / MM:.4f} {w:.4f} {h:.4f}" '
            f'width="{px}" height="{H:.0f}" class="lay" shape-rendering="geometricPrecision">'
            f'<rect x="{x0 / MM:.4f}" y="{-y1 / MM:.4f}" width="{w:.4f}" height="{h:.4f}" fill="#fff"/>')


def _poly(pts, w, color, op=1.0, dash=""):
    d = " ".join(f"{x / MM:.4f},{-y / MM:.4f}" for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{max(w / MM, 0.01):.4f}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{op}"{da}/>')


def _circle(x, y, r, fill, stroke="none", sw=0.0, op=1.0):
    return (f'<circle cx="{x / MM:.4f}" cy="{-y / MM:.4f}" r="{r / MM:.4f}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw:.4f}" opacity="{op}"/>')


def svg_overview(win, paths, vrows, gnd_ps, pts):
    """Toàn cảnh channel; chỉ đánh dấu điểm NOT OK (một màu), rê chuột để xem, bấm để mở."""
    s = [_svg_open(win, 1000)]
    span = max(win[2] - win[0], win[3] - win[1]) / MM
    for gx, gy, _ in gnd_ps:
        if _bbox_hit(win, gx, gy):
            s.append(_circle(gx, gy, 0.12 * MM, "#1f5fd6", op=0.5))
    for p in paths:
        s.append(_poly(p["pts"], p["w"], "#d62728"))
    for r in vrows:
        s.append(_circle(r["x"], r["y"], 0.15 * MM, "#000", op=0.8))
    rr = span / 110
    for p in pts:
        tip = "; ".join(issue_lines(p["items"]))
        col = "#d00000"
        s.append(f'<a href="#p{p["id"]}"><title>#{p["id"]} {html.escape(p["net"])} - {html.escape(tip)}</title>'
                 f'<circle cx="{p["x"] / MM:.4f}" cy="{-p["y"] / MM:.4f}" r="{rr:.4f}" fill="{col}" fill-opacity="0.15" '
                 f'stroke="{col}" stroke-width="{rr / 3:.4f}"/></a>')
    s.append(_scale(win, 1000))
    s.append("</svg>")
    return "".join(s)


def _scale(win, px):
    """Thước tỉ lệ góc dưới trái (px = bề rộng ảnh, để chữ ~11 px)."""
    x0, y0, x1, y1 = win
    span = (x1 - x0) / MM
    L = next((v for v in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50) if v >= span / 8), 50)
    h = 2.2 * span / px
    x, y = x0 / MM + h * 6, -y0 / MM - h * 4
    return (f'<rect x="{x - h * 2:.4f}" y="{y - h * 9:.4f}" width="{L + h * 4:.4f}" height="{h * 12:.4f}" fill="#fff" '
            f'opacity="0.8"/><rect x="{x:.4f}" y="{y - h:.4f}" width="{L:.4f}" height="{h * 2:.4f}" fill="#000"/>'
            f'<text x="{x:.4f}" y="{y - h * 3:.4f}" font-size="{h * 5:.4f}" fill="#000"{RU.attrs(L * MM)}>'
            f'{RU.fmt(L * MM)}</text>')


PLANE_COLORS = ("#8fb0ee", "#9fd6a8", "#c9b3ea", "#e8d98f")
SIGNAL_COLORS = ("#d62728", "#8c564b", "#e377c2", "#7f7f7f")


def svg_zoom(win, cu, planes, paths, signals, vrows, gnd_ps, items, ngrid=48, oc=None):
    """026: ảnh zoom CHỈ vẽ lớp liên quan: phủ GND của từng lớp plane trong planes, trace chỉ trên signals (không vẽ
    lớp khác). -> (svg, legend [(màu, chữ)])."""
    s = [_svg_open(win, 380)]
    x0, y0, x1, y1 = win
    legend = []
    other = {str(f.get("ref") or "").split(":")[0].strip() for f in items if f.get("other_net")}
    for k, pl in enumerate(planes):
        col = PLANE_COLORS[k % len(PLANE_COLORS)]
        legend.append((col, f"{pl} – GND (ref)"))
        s.append(_plane_svg(cu, oc, pl, win, col, ngrid, f' fill-opacity="{0.75 if len(planes) == 1 else 0.5}"',
                            other=pl in other))
        if oc is not None and pl in other:
            legend.append(("#f6c28b", f"{pl} – other net copper"))
    for gx, gy, _ in gnd_ps:
        if _bbox_hit(win, gx, gy):
            s.append(_circle(gx, gy, 0.1 * MM, "#1f5fd6"))
    for k, lay in enumerate(signals):
        col = SIGNAL_COLORS[k % len(SIGNAL_COLORS)]
        legend.append((col, f"{lay} – signal"))
        for p in paths:
            if p["layer"] == lay:
                s.append(_poly(p["pts"], p["w"], col))
    for r in vrows:
        if _bbox_hit(win, r["x"], r["y"]):
            s.append(_circle(r["x"], r["y"], 0.12 * MM, "#000"))
    rr = max(x1 - x0, y1 - y0) / 25 * 2.5                    # 033: vòng hồng nét đứt (không tô cam)
    span = (x1 - x0) / MM
    for f in items:
        s.append(_circle(f["x"], f["y"], rr, "none", FAULT_COLOR, rr / MM / 6).replace(
            "/>", f' stroke-dasharray="{span / 30:.4f} {span / 50:.4f}"/>'))
    legend += [("#1f5fd6", "GND via"), ("#000", "signal via"), (FAULT_COLOR, "issue")]
    s.append(_scale(win, 380))
    s.append("</svg>")
    return "".join(s), legend


REF_CHECKS = ("Loss of reference", "SOV", "Ref to other net", "Trace over via clearance", "Near plane edge")
MISS_COLOR, CLEAR_VIA_COLOR = "#ff7f0e", "#c2185b"
FAULT_COLOR = "#ff1493"                                  # 033: chỗ lỗi = khung / vòng hồng nét đứt


DEFAULT_PATTERN = (1, 0.6)
# 043: one frame style per issue type (colour, dash pattern as factors of the base dash, label)
FRAME_STYLES = {
    "Loss of reference": (FAULT_COLOR, DEFAULT_PATTERN, "dashed"),
    "Near plane edge": ("#ff8c00", (0.25, 0.45), "dotted"),
    "SOV": ("#8e44ad", (1, 0.35, 0.2, 0.35), "dash-dot"),
    "Ref to other net": ("#a0522d", (2, 0.6), "long dash"),
    "Trace over via clearance": ("#138d75", (0.6, 0.6), "short dash"),
}
FRAME_FALLBACK = [("#1f77b4", (1.5, 0.4, 0.2, 0.4), "dash-dot"), ("#7f7f7f", (0.4, 0.4), "dotted"),
                  ("#2ca02c", (1.2, 0.8), "dashed")]


def frame_style(check, seen):
    """043: (colour, pattern, label) of the frame of one issue type; seen = unknown checks already styled (order)."""
    if check in FRAME_STYLES:
        return FRAME_STYLES[check]
    if check not in seen:
        seen.append(check)
    return FRAME_FALLBACK[seen.index(check) % len(FRAME_FALLBACK)]


def _fault_rect(pts, pad, sw, dash, colour=FAULT_COLOR, pattern=DEFAULT_PATTERN):
    """033: khung nét đứt quanh các điểm (m). 043: colour + pattern per issue type (default = 033 pink dashed)."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    da = " ".join(f"{dash * k:.4f}" for k in pattern)
    return (f'<rect x="{x0 / MM:.4f}" y="{-y1 / MM:.4f}" width="{(x1 - x0) / MM:.4f}" height="{(y1 - y0) / MM:.4f}" '
            f'fill="none" stroke="{colour}" stroke-width="{sw:.4f}" stroke-dasharray="{da}"/>')


def _missing_on(f, plane):
    """Lớp plane này có thiếu tham chiếu ở đoạn của phát hiện f không (để tô sáng trên panel đó)."""
    if f["check"] == "Loss of reference":
        return True
    return plane in [r.split(":")[0].strip() for r in str(f.get("ref") or "").split(",")]


def svg_ref_panels(win, cu, planes, paths, signals, vrows, gnd_ps, items, ngrid=96, oc=None, px=280):
    """032: ảnh phát hiện tham chiếu = MỘT panel cho MỖI lớp plane, đặt cạnh nhau: GND của lớp đó (màu riêng), đồng net
    khác, trace, via tín hiệu / GND, via sở hữu clearance (vòng), đoạn thiếu tham chiếu tô sáng dọc theo mẫu.
    -> (html, legend)."""
    x0, y0, x1, y1 = win
    other = {str(f.get("ref") or "").split(":")[0].strip() for f in items if f.get("other_net")}
    cvias = {(round(v[0], 9), round(v[1], 9)): v for f in items for v in f.get("vias") or []}
    legend, out = [], []
    order, seen = [], []                                      # 043: issue types in order of first appearance
    for f in items:
        if f["check"] not in order:
            order.append(f["check"])
    styles = {c: frame_style(c, seen) for c in order}
    drawn = []
    for k, pl in enumerate(planes):
        col = PLANE_COLORS[k % len(PLANE_COLORS)]
        legend.append((col, f"{pl} – GND copper (panel {k + 1})"))
        s = [_svg_open(win, px), _plane_svg(cu, oc, pl, win, col, ngrid, other=pl in other)]
        for gx, gy, _ in gnd_ps:
            if _bbox_hit(win, gx, gy):
                s.append(_circle(gx, gy, 0.1 * MM, "#1f5fd6"))
        for p in paths:
            if p["layer"] in signals:
                s.append(_poly(p["pts"], p["w"], "#d62728"))
        span_ = (x1 - x0) / MM
        sw = span_ / px * 3.5
        for f in items:                                       # 033: đoạn thiếu = khung nét đứt quanh đoạn
            tp = f.get("trace_pts") or ([f["start"], f["end"]] if "start" in f else [(f["x"], f["y"])])
            if _missing_on(f, pl):
                w = max((p["w"] for p in paths if p["net"] == f["net"]), default=0.1 * MM)
                col, pat, _ = styles[f["check"]]
                k_ = order.index(f["check"])                  # 043: 2nd / 3rd type a little outside the previous
                s.append(_fault_rect(tp, max(w * 2, 0.08 * MM) + k_ * 1.5 * sw * MM, sw, span_ / 30, col, pat))
                if f["check"] not in drawn:
                    drawn.append(f["check"])
        for r in vrows:
            if _bbox_hit(win, r["x"], r["y"]):
                s.append(_circle(r["x"], r["y"], 0.12 * MM, "#000"))
        rr = max(x1 - x0, y1 - y0) / 40
        for v in cvias.values():
            s.append(_circle(v[0], v[1], rr * 2, "none", CLEAR_VIA_COLOR, rr / MM / 2))
        span = (x1 - x0) / MM
        h = 2.2 * span / px
        s.append(f'<rect x="{x0 / MM + h:.4f}" y="{-y1 / MM + h:.4f}" width="{span * 0.62:.4f}" height="{h * 7:.4f}" '
                 f'fill="#fff" opacity="0.85"/><text x="{x0 / MM + h * 2:.4f}" y="{-y1 / MM + h * 6:.4f}" '
                 f'font-size="{h * 5:.4f}" font-weight="bold" fill="#000">{html.escape(pl)}</text>')
        s.append(_scale(win, px))
        s.append("</svg>")
        out.append("".join(s))
    legend += [("#d62728", "signal trace (" + ", ".join(signals) + ")")]
    legend += [(styles[c][0], f"{c} ({styles[c][2]} frame)") for c in order if c in drawn]   # 043: one per issue
    legend += [(CLEAR_VIA_COLOR, "via owning the clearance (ring)"), ("#000", "signal via"), ("#1f5fd6", "GND via")]
    if other:
        legend.append(("#f6c28b", "other net copper"))
    key = ""
    if len(drawn) >= 2:                                       # 043: the report has no legend -> frame key line
        key = ("<div class='fkey' style='display:flex;flex-wrap:wrap;gap:4px 16px;margin:4px 0;font-size:12px'>"
               + "".join(f"<span><svg width='34' height='10' style='vertical-align:middle'><line x1='1' y1='5' "
                         f"x2='33' y2='5' stroke='{styles[c][0]}' stroke-width='2.2' stroke-dasharray='"
                         + " ".join(f"{6 * k:g}" for k in styles[c][1]) + f"'/></svg> {html.escape(c)}</span>"
                         for c in order if c in drawn) + "</div>")
    return ("<div class='rpanels' style='display:flex;gap:8px;flex-wrap:nowrap'>"
            + "".join(f"<div>{p}</div>" for p in out) + "</div>" + key), legend


def issue_lines(items):
    """012: dòng '<check>: <value>' của một điểm, mỗi dòng một lần (giữ thứ tự). Phát hiện / số đếm không đổi."""
    return list(dict.fromkeys(f"{f['check']}: {f['value']}" for f in items))


def points(fs, ci):
    """Gộp phát hiện NOT OK theo vị trí + net -> 1 điểm bất thường (1 ảnh, nhiều vấn đề)."""
    out, idx = [], {}
    for f in fs:
        if f["status"] != NOK:
            continue
        k = (f["net"], round(f["x"] / MM, 2), round(f["y"] / MM, 2))
        if k not in idx:
            idx[k] = len(out)
            out.append({"id": f"{ci}.{len(out) + 1}", "net": f["net"], "x": f["x"], "y": f["y"], "main": f,
                        "items": []})
        p = out[idx[k]]
        p["items"].append(f)
        f["point"] = p["id"]
    for p in out:
        p["status"] = NOK
    out.sort(key=lambda p: (p["main"]["check"], p["net"]))
    for i, p in enumerate(out, 1):
        p["id"] = f"{ci}.{i}"
        for f in p["items"]:
            f["point"] = p["id"]
    return out


# ----------------------------------------------------------------------------- main
SNAPSHOT_MODES = ("auto", "off")


def review(board, channels, cell=None, out_html=None, log=print, gate=None, snapshot="auto", series_values=None):
    """board: .aedt/.aedb. channels: 'U14-U26:CPHY_B02DEVA_*; U21-J25:...'. Trả dict tóm tắt + đường dẫn HTML.
    gate: không dùng (035 bỏ kết luận gate khỏi báo cáo; giữ tham số cho người gọi cũ).
    snapshot (027): 'auto' + review.use_snapshot -> đọc layout snapshot (như review_checks); không dùng được -> live
    + cảnh báo trong báo cáo; 'off' -> EDB live như trước.
    series_values (045): {refdes: giá trị} của linh kiện nối tiếp (netlist / board facts) -> nhãn topology."""
    import time
    if snapshot not in SNAPSHOT_MODES:
        raise ValueError(f"snapshot: expected {' / '.join(SNAPSHOT_MODES)}, got {snapshot!r}")
    m = config.machine()
    d = config.defaults()
    R = d["review"]
    refs = d["cutout"]["reference_nets"]
    aedb, _ = naming.board_paths(board)
    reqs = naming.parse_request(channels)
    if series_values is not None and not isinstance(series_values, dict):
        raise ValueError(f"series_values: expected dict refdes -> value, got {type(series_values).__name__}")
    for rq in reqs:
        rq["series_values"] = {str(k): str(v) for k, v in (series_values or {}).items() if v not in (None, "")}
    source, res = {"kind": "live"}, None
    t0 = time.perf_counter()
    if snapshot == "auto" and bool(R.get("use_snapshot", True)):
        from .. import layout_snapshot as LS
        from ..layout_snapshot import api as LSA
        try:
            edb, source = LSA.for_review(aedb, cell or "", reqs, m["aedt_version"], log)
            res = _review_edb(edb, reqs, R, refs, log, aedb)
        except (LS.SnapshotFallback, LS.SnapshotMissing) as ex:
            ids = getattr(ex, "ids", [])
            source = {"kind": "live", "warning": f"layout snapshot not used ({ex}); measured live" +
                      (f"; primitive ids {ids[:20]}" if ids else "")}
            res = None
    if res is None:
        edb = inspect_board.open_edb(aedb, cell=cell, readonly=True, version=m["aedt_version"])
        try:
            res = _review_edb(edb, reqs, R, refs, log, aedb)
        finally:
            edb.close()
    source["seconds"] = round(time.perf_counter() - t0, 2)
    cell, B, chans = res
    return _write_report(aedb, d, R, refs, cell, B, chans, out_html, gate, source)


def _review_edb(edb, reqs, R, refs, log, aedb=None):
    """Đo + vẽ trên edb đã mở (EDB live hoặc SnapEdb). -> (cell, Board, chans)."""
    step = float(R["sample_step_mm"]) * MM
    chans = []
    if True:
        cell = edb.active_cell.GetName()
        log("[review] đọc board...")
        B = Board(edb, refs, R)
        log(f"[review] lớp plane: {B.planes}")
        PD = edb.core.Geometry.PointData
        pt = lambda x, y: PD(edb.edb_value(x), edb.edb_value(y))
        names = set()
        for rq in reqs:
            ch = {"comp_a": rq["comp_a"], "comp_b": rq["comp_b"], "patterns": rq["patterns"], "findings": [],
                  "warnings": []}
            try:
                t = inspect_board.trace_channel(edb, rq["comp_a"], rq["comp_b"], rq["patterns"], refs)
            except Exception as ex:
                ch.update(name=f"{rq['comp_a']}_{rq['comp_b']}", error=str(ex))
                chans.append(ch)
                continue
            nm = naming.default_name(rq["comp_a"], rq["comp_b"], t["nets"])
            ch["name"] = naming.unique_name(nm, names)
            names.add(ch["name"].lower())
            ch.update(nets=t["nets"], series=t["series"], end_types=t["end_types"], warnings=t["warnings"])
            if not t["nets"]:
                ch["error"] = "No net connects the two components"
                chans.append(ch)
                continue
            log(f"[review] {ch['name']}: {len(t['nets'])} net")
            paths, polys, vias, pins = _collect(edb, B, t["nets"])
            allp = [q for p in paths for q in p["pts"]] + [(v["x"], v["y"]) for v in vias + pins]
            xs, ys = [p[0] for p in allp], [p[1] for p in allp]
            win = (min(xs) - 1 * MM, min(ys) - 1 * MM, max(xs) + 1 * MM, max(ys) + 1 * MM)
            zm = float(R["zoom_margin_mm"]) * MM
            g = zm + 2 * MM                                           # đủ rộng cho ảnh zoom
            cu = Copper(edb, B.ref_prims, (win[0] - g, win[1] - g, win[2] + g, win[3] + g))
            excl = [(v["x"], v["y"]) for v in vias + pins]
            oc = Copper(edb, B.other_prims(cu.window, t["nets"]), cu.window)
            fs = check_reference(B, cu, paths, excl, R, step, oc)
            fs += trace_stubs(paths, vias, pins, polys, pt)
            stacks = _stacks(vias, float(R["stack_merge_mm"]) * MM)
            vrows, vfs = via_rows(B, stacks, paths, polys, pins, pt, R)
            fs += vfs
            fs += _extra_findings(edb, B, rq, t, (paths, polys, vias, pins), ch, log, aedb)   # 028: check mới
            pg = set(edb.nets.power.keys()) | set(refs)
            chains = _chains(t["nets"], t["series"], t["start_nets"], pg)
            groups = naming.review_groups(t["start_nets"])                  # 034: tên 'X_P*' cũng ghép cặp
            chain_len, intra, inter, widths = lengths(chains, paths, vrows, groups)
            fs.sort(key=lambda f: (STATUS_ORDER[f["status"]], f["check"], f["net"], f["x"]))
            for i, f in enumerate(fs, 1):
                f["id"] = f"{len(chans) + 1}.{i}"
            pts_ = points(fs, len(chans) + 1)
            gnd_win = [g for g in B.gnd_ps if _bbox_hit(cu.window, g[0], g[1])]
            ch["overview_svg"] = svg_overview(win, paths, vrows, gnd_win, pts_)
            nimg = int(R["max_images"])
            ch.update(findings=fs, points=pts_, name=ch["name"])
            rws = [r for rs in RR.rows([ch]).values() for r in rs]
            rws.sort(key=lambda r: r["pi"])
            for r in rws[:nimg]:                                     # 026: ảnh theo dòng báo cáo, lớp liên quan
                sig, pl, note = RR.row_layers(r["items"], B.ref_layers, B.metal)
                bb = [f["bbox"] for f in r["items"]]
                b = (min(q[0] for q in bb), min(q[1] for q in bb), max(q[2] for q in bb), max(q[3] for q in bb))
                cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                ref_row = all(f["check"] in REF_CHECKS for f in r["items"]) and pl
                if ref_row:                                          # 032: đoạn + via clearance + lề, panel mỗi lớp
                    xs = [b[0], b[2]] + [v[0] for f in r["items"] for v in f.get("vias") or []]
                    ys = [b[1], b[3]] + [v[1] for f in r["items"] for v in f.get("vias") or []]
                    b = (min(xs), min(ys), max(xs), max(ys))
                    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                    hw = max(max(b[2] - b[0], b[3] - b[1]) / 2 + zm, 1.5 * MM)
                else:
                    hw = max(b[2] - b[0], b[3] - b[1]) / 2 + zm
                zw = (cx - hw, cy - hw, cx + hw, cy + hw)
                hook = (RR.report_specs().get(r["items"][0]["check"]) or {}).get("picture")
                if hook and all(f["check"] == r["items"][0]["check"] for f in r["items"]):
                    pic = (hook(r["items"][0], paths), [])              # 033: ảnh riêng của luật (serpentine)
                elif ref_row:
                    pic = svg_ref_panels(zw, cu, pl, paths, sig, vrows, gnd_win, r["items"], oc=oc)
                else:
                    pic = svg_zoom(zw, cu, pl, paths, sig, vrows, gnd_win, r["items"], oc=oc)
                ch.setdefault("images", {})[f"{r['point']}|{RR.section_of(r['items'][0]['check'])}"] = \
                    pic + (note, sig, pl)
            ch.update(findings=fs, points=pts_, widths=widths, vias=vrows, chain_len=chain_len, intra=intra,
                      inter=inter, window=win,
                      n_paths=len(paths), n_vias=len(vias))
            ch["routing"] = routing_data(edb, B, ch, rq, t, paths, pins, vrows, chains)    # 033: khung từng cặp
            log(f"[review] {ch['name']}: {len(fs)} phát hiện, {len(vrows)} via stack")
            chans.append(ch)
    return cell, B, chans


def routing_data(edb, B, ch, rq, t, paths, pins, vrows, chains):
    """033: dữ liệu mục 'Signal routing per pair' (review_routing) thu trong lượt đo: đường đi, via, chân linh kiện 2 đầu
    + nối tiếp (pad thật = khung pin), khung thân linh kiện, chuỗi net, H mỗi lớp. Lỗi đọc -> cảnh báo, không chặn."""
    from ..layout_snapshot import SnapshotMissing
    from ..review_checks import _serp
    keep = {rq["comp_a"], rq["comp_b"]} | set(t.get("series") or {})
    pins_ = [dict(q) for q in pins if q.get("comp") in keep]
    want = {q["id"] for q in pins_}
    boxes, comp_bb, miss = {}, {}, 0
    for n in sorted({q["net"] for q in pins_}):
        try:
            insts = edb.nets.nets[n].padstack_instances
        except Exception:
            continue
        for v in insts:
            try:
                if v.id in want:
                    boxes[v.id] = [float(x) for x in v.bounding_box]
            except (Exception, SnapshotMissing):                        # chỉ để vẽ pad: thiếu -> tròn theo padstack
                miss += 1
    for q in pins_:
        q["bbox"] = boxes.get(q["id"])
        if q["bbox"] is None:
            q["pad"] = B.padstack_dims(q.get("def"), q.get("range") or ())[0]
    comp_layer = {}
    for rd in keep:
        try:
            comp_bb[rd] = [float(x) for x in edb.components.instances[rd].bounding_box]
        except (Exception, SnapshotMissing):
            pass
        try:                                                            # 2.11.1 (R3): lớp đặt linh kiện
            comp_layer[rd] = str(edb.components.instances[rd].placement_layer or "")
        except (Exception, SnapshotMissing):
            pass
    if miss:
        ch["warnings"].append(f"routing view: {miss} pin pad box(es) not readable, drawn as circles")
    sv = rq.get("series_values") or {}                                  # 045: thân + giá trị linh kiện nối tiếp
    series_info = {rd: {"type": str(s.get("type") or ""), "part": str(s.get("part") or ""), "value": sv.get(rd, "")}
                   for rd, s in (t.get("series") or {}).items() if isinstance(s, dict)}
    return {"name": ch["name"], "comp_a": rq["comp_a"], "comp_b": rq["comp_b"], "metal": list(B.metal),
            "gnd_layers": list(B.planes), "paths": paths, "vias": vrows, "pins": pins_, "chains": chains,
            "comps": sorted(keep), "comp_bb": comp_bb, "comp_layer": comp_layer, "series_info": series_info,
            "H": {L: h for L in B.metal if (h := _serp.height(B, L))}}


BUILTIN_CHECKS = ("sov", "ref_other_net", "loss_of_reference", "via_clearance", "trace_stubs", "ref_plane_change", "via_stub",
                  "nearest_gnd_via", "routing")                       # đo trực tiếp ở trên (số liệu 011; 031: mỗi luật một file)


def _extra_findings(edb, B, rq, t, collected, ch, log, aedb=None):
    """028: check của registry ngoài 4 check gốc (thêm luật = thêm một file trong review_checks/) -> findings vào báo
    cáo HTML như check gốc. Check lỗi -> cảnh báo của channel, không chặn báo cáo."""
    from ..review_checks import checks
    extra = [m for n, m in checks().items() if n not in BUILTIN_CHECKS]
    if not extra:
        return []
    from ..review_checks._context import ChannelCtx, Ctx
    ctx = Ctx(edb, log, aedb)
    ctx._B = B
    cc = ChannelCtx(ctx, {"comp_a": rq["comp_a"], "comp_b": rq["comp_b"], "patterns": rq["patterns"]})
    cc._cache.update(trace=t, collected=collected)
    out = []
    for m in extra:
        try:
            out += list(m.run(cc).get("items") or [])
        except Exception as ex:                                          # check lỗi không chặn báo cáo
            ch["warnings"].append(f"check {m.NAME} failed: {ex}")
    return out


def _write_report(aedb, d, R, refs, cell, B, chans, out_html, gate, source):
    out_dir = os.path.join(os.path.dirname(aedb), d["run"]["output_subdir"])
    os.makedirs(out_dir, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_html = out_html or claim_file(os.path.join(out_dir, f"layout_review_{ts}.html"))   # 024: _2 khi trùng
    info = {"board": aedb, "cell": cell, "date": dt.datetime.now().strftime("%d/%m/%Y - %H:%M:%S"), "version": __version__,
            "planes": B.planes, "params": R, "refs": refs, "gate": gate, "source": source}
    with open(out_html, "w", encoding="utf-8") as fh:
        fh.write(render_html(info, chans))
    summary = []
    for ch in chans:
        cnt = {}
        for f in ch.get("findings", []):
            cnt[f["status"]] = cnt.get(f["status"], 0) + 1
        # id = số điểm trong HTML (#ch.n); một điểm có thể gồm nhiều check tại cùng via / net
        summary.append({"channel": ch["name"], "error": ch.get("error"), "finding_counts": cnt,
                        "not_ok_points": len(ch.get("points", [])),
                        "top": [{"id": p["id"], "status": NOK, "net": p["net"],
                                 "layer": p["main"]["layer"], "issues": issue_lines(p["items"]),
                                 "x_mm": round(p["x"] / MM, 3), "y_mm": round(p["y"] / MM, 3)}
                                for p in ch.get("points", [])[:5]]})
    return {"html": out_html, "plane_layers": B.planes, "channels": summary, "source": source}


# ----------------------------------------------------------------------------- HTML (English, theo yêu cầu người dùng)
CSS = """
:root{--b:#1f4e78}
body{font-family:Segoe UI,Arial,sans-serif;margin:16px auto;max-width:1400px;padding:0 16px;color:#222;background:#fff}
h1{font-size:22px;margin-bottom:4px}h2{font-size:18px;border-bottom:2px solid var(--b);padding-bottom:3px;margin-top:30px}
h3{font-size:15px;margin:18px 0 6px}
table{border-collapse:collapse;font-size:12.5px;margin:6px 0}
th,td{border:1px solid #c8c8c8;padding:4px 8px;text-align:left;vertical-align:top}
th{background:var(--b);color:#fff;position:sticky;top:0}
table.sort th{cursor:pointer}
table.sum{width:100%}table.sum td:first-child{font-weight:600;background:#f3f6fa;width:210px}
td.ok{color:#2e7d32}td.bad{background:#fde7e9;color:#9c0006}td.bad b{color:#9c0006}
.sev{padding:1px 6px;border-radius:3px;font-size:11px;font-weight:600}
.NOK{background:#fde7e9;color:#9c0006}.OK{background:#c8e6c9;color:#1b5e20}
.meta-tbl th{text-align:left;width:150px}
.lead{font-size:14px;margin:8px 0 4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(620px,1fr));gap:12px}
.card{border:1px solid #ccc;border-radius:6px;padding:8px;display:flex;gap:12px;scroll-margin-top:10px}
.card:target{outline:3px solid #ff7f0e}
.card .meta{font-size:12.5px;min-width:200px}.card ul{margin:4px 0;padding-left:18px}
.lay{border:1px solid #888;max-width:100%;height:auto;flex:none}
.legend span{display:inline-block;width:14px;height:10px;margin:0 4px 0 12px;vertical-align:middle}
.small{color:#666;font-size:12px}nav{margin:8px 0}nav a{margin-right:14px}
details{margin:8px 0}summary{cursor:pointer;font-weight:600;color:var(--b)}
"""
JS = """
document.querySelectorAll('table.sort').forEach(t=>{t.querySelectorAll('th').forEach((th,i)=>{th.title='Click to sort';
th.onclick=()=>{const b=t.tBodies[0],r=[...b.rows],asc=th.dataset.o!=='a';th.dataset.o=asc?'a':'d';
r.sort((x,y)=>{let p=x.cells[i].dataset.v??x.cells[i].innerText,q=y.cells[i].dataset.v??y.cells[i].innerText;
let a=parseFloat(p),c=parseFloat(q);if(!isNaN(a)&&!isNaN(c))return asc?a-c:c-a;return asc?p.localeCompare(q):q.localeCompare(p)});
r.forEach(e=>b.appendChild(e))}})});
"""
CHECKS = ["Loss of reference", "Ref to other net", "SOV", "Trace stub", "Ref plane change", "Via stub",
          "Nearest GND via"]


def _e(x):
    return html.escape(str(x))


def _mm(v):
    return f"{v / MM:.3f}"


def _sev(s):
    """036: ô trạng thái OK / NOT OK (tên hàm giữ cho bảng cũ)."""
    return f"<span class='sev {'NOK' if s == NOK else 'OK'}'>{s}</span>"


def _links(pids, n=8):
    pids = list(dict.fromkeys(pids))
    out = ", ".join(f"<a href='#p{p}'>#{p}</a>" for p in pids[:n])
    return out + (f" +{len(pids) - n} more" if len(pids) > n else "")


def _ok(txt="None"):
    return f"<td class='ok'>{txt}</td>"


def _bad(txt):
    return f"<td class='bad'>&#9888; {txt}</td>"


def _short(name, group):
    """Tên ngắn của nhóm: phần chung của các net, vd CPHY_LC2HSB_L0_A/B/C -> L0 (A/B/C)."""
    if len(group) < 2:
        return name
    pre = os.path.commonprefix(group)
    tails = [n[len(pre):] for n in group]
    base = pre.rstrip("_+-").split("_")[-1] if pre.rstrip("_+-") else pre
    return f"{base} ({'/'.join(tails)})"


def _via_groups(c):
    """Gộp via stack theo (loại, padstack, dải lớp, lớp nối) -> V1, V2..."""
    gs = {}
    for r in c.get("vias", []):
        span = f"{r['used'][0]} → {r['used'][-1]}" if r["used"] else "(not connected)"
        k = (r["kind"], ", ".join(r["defs"]), r["range"], span, r.get("size", ""))
        gs.setdefault(k, []).append(r)
    return [(f"V{i}", k, rs) for i, (k, rs) in enumerate(sorted(gs.items(), key=lambda a: -len(a[1])), 1)]


def _pid_of(c, f):
    return f.get("point")


def _summary_via(chans, P):
    lim = float(P["gnd_via_flag_mm"])
    rows = {k: [] for k in ("type", "layers", "bd", "stub", "gnd")}
    for c in chans:
        if c.get("error"):
            for k in rows:
                rows[k].append(f"<td class='bad'>review failed</td>" if k == "type" else "<td></td>")
            continue
        vg = _via_groups(c)
        if not vg:
            for k in rows:
                rows[k].append(_ok("No signal via") if k == "type" else "<td>-</td>")
            continue
        def lbl(size):
            mil, _, mm = size.partition(" (")
            return mil, (f"pad/hole {mm.rstrip(')')}; " if mm else "")
        rows["type"].append("<td>" + "<br>".join(f"<b>{v}</b>: <b>{_e(k[0])} {_e(lbl(k[4])[0])}</b> "
                                                 f"&times;{len(rs)} <span class='small'>"
                                                 f"({_e(lbl(k[4])[1])}{_e(k[1])}; {_e(k[2])})</span>"
                                                 for v, k, rs in vg) + "</td>")
        rows["layers"].append("<td>" + "<br>".join(f"<b>{v}</b>: {_e(k[3])}" for v, k, rs in vg) + "</td>")
        rows["bd"].append("<td>" + "<br>".join(f"<b>{v}</b>: " + ("yes" if all(r["has_bd"] for r in rs) else
                                                                 "partly" if any(r["has_bd"] for r in rs) else "no")
                                                for v, k, rs in vg) + "</td>")
        fs = c.get("findings", [])
        st = [f for f in fs if f["check"] == "Via stub"]
        if st:
            lines = []
            for v, k, rs in vg:
                ss = [r["stub_mm"] for r in rs if r["stub_mm"] > 1e-6]
                if ss:
                    lines.append(f"<b>{v}</b>: {len(ss)} via(s), stub up to {max(ss):.3f} mm")
            rows["stub"].append(_bad("<br>".join(lines) + "<br>" + _links(_pid_of(c, f) for f in st)))
        else:
            rows["stub"].append(_ok())
        far = [f for f in fs if f["check"] == "Nearest GND via"]
        rc = [f for f in fs if f["check"] == "Ref plane change" and f["status"] == NOK]
        dmax = max((r["gnd"]["d_mm"] for r in c["vias"] if r["gnd"]), default=None)
        if far or rc:
            n = len({(f["x"], f["y"]) for f in far + rc})
            txt = (f"<b>{n} via(s)</b> with no GND via within {lim:g} mm (max {dmax:.3f} mm)"
                   + (f"; {len(rc)} of them change reference plane" if rc else "") + "<br>"
                   + _links(_pid_of(c, f) for f in rc + far))
            rows["gnd"].append(_bad(txt))
        else:
            rows["gnd"].append(_ok(f"All within {lim:g} mm" + (f" (max {dmax:.3f} mm)" if dmax is not None else "")))
    names = [("type", "Via type, pad D hole (mil) &times; qty"), ("layers", "Signal layers (from → to)"), ("bd", "Backdrill"),
             ("stub", "Via stub"), ("gnd", f"GND via within {lim:g} mm")]
    return names, rows


def _summary_routing(chans):
    rows = {k: [] for k in ("len", "skew", "bylay", "width", "same", "sov", "other", "lor", "stub")}
    for c in chans:
        if c.get("error") or not c.get("chain_len"):
            for k in rows:
                rows[k].append("<td>-</td>")
            continue
        cl = c["chain_len"]
        tot = [L["total_mm"] for L in cl.values()]
        rows["len"].append(f"<td>{min(tot):.2f} – {max(tot):.2f} mm <span class='small'>({len(tot)} nets)</span></td>")
        sk = []
        if c["intra"]:
            g = max(c["intra"], key=lambda a: a["skew_mm"])
            sk.append(f"intra-group max {g['skew_mm']:.3f} mm ({_e(_short('', g['group']))})")
        if c["inter"]:
            sk.append(f"inter-group {c['inter']['skew_mm']:.3f} mm")
        rows["skew"].append(f"<td>{'<br>'.join(sk) or '-'}</td>")
        lays = {}
        for L in cl.values():
            for lay, v in L["by_layer"].items():
                lays.setdefault(lay, []).append(v)
        rows["bylay"].append("<td>" + "<br>".join(
            f"{_e(l)}: {min(v):.2f}" + (f" – {max(v):.2f}" if max(v) - min(v) > 0.005 else "") + " mm"
            + (f" <span class='small'>({len(v)}/{len(cl)} nets)</span>" if len(v) != len(cl) else "")
            for l, v in lays.items()) + "</td>")
        rows["width"].append("<td>" + "<br>".join(f"{_e(l)}: {', '.join(f'{w:.3f}' for w in ws)} mm"
                                                  for l, ws in c.get("widths", {}).items()) + "</td>")
        bad = [g for g in c["intra"] if not g.get("same_layers", True)]
        if bad:
            rows["same"].append(_bad("<br>".join(
                f"<b>{_e(_short('', g['group']))}</b>: " + "; ".join(f"{_e(n)} on {_e(', '.join(l))}"
                                                                    for n, l in g["layers"].items())
                for g in bad)))
        else:
            rows["same"].append(_ok("Yes, every pair / trio uses the same layers" if c["intra"] else "-"))
        fs = c.get("findings", [])
        for key, chk in (("sov", "SOV"), ("other", "Ref to other net"), ("lor", "Loss of reference"),
                         ("stub", "Trace stub")):
            ff = [f for f in fs if f["check"] == chk]
            if not ff:
                rows[key].append(_ok())
                continue
            if chk == "Ref to other net":
                nets = sorted({f"{f['ref']}" for f in ff})
                txt = f"<b>{len(ff)} segment(s)</b>, {sum(f['len_mm'] for f in ff):.2f} mm total, over " + \
                      _e("; ".join(nets))
            elif chk == "Trace stub":
                n_open = sum(1 for f in ff if f["value"].startswith("open"))
                txt = f"<b>{len(ff)}</b>: {n_open} open end(s), {len(ff) - n_open} T-branch(es)"
            else:
                txt = f"<b>{len(ff)} segment(s)</b>, {sum(f['len_mm'] for f in ff):.2f} mm total"
            rows[key].append(_bad(txt + "<br>" + _links(_pid_of(c, f) for f in ff)))
    names = [("len", "Total length (trace + via)"), ("skew", "Skew"), ("bylay", "Length per layer (per net)"),
             ("width", "Trace width per layer"), ("same", "Same layers within pair / trio"),
             ("sov", "Signal over void (SOV)"), ("other", "Reference change (GND → other net)"),
             ("lor", "Loss of reference"), ("stub", "Trace stub")]
    return names, rows


def _table(title, names, rows, chans):
    o = [f"<h3>{title}</h3><table class='sum'><tr><th>Item</th>" +
         "".join(f"<th>{_e(c['name'])}</th>" for c in chans) + "</tr>"]
    for k, label in names:
        o.append(f"<tr><td>{label}</td>{''.join(rows[k])}</tr>")
    o.append("</table>")
    return "".join(o)


def _issue(f):
    return f"<b>{_e(f['check'])}</b>: {_e(f['value'])}"


def render_html(info, chans):
    """026: báo cáo theo mẫu cố định (cut_board/review_report.render). Giữ tên / tham số (tests/review_check.py)."""
    return RR.render(info, chans)


def reference_html(info, chans):
    """Phần Reference data (thu gọn): bảng tóm tắt cũ, toàn cảnh channel, mọi phát hiện (OK + NOT OK), via, chiều dài,
    ngưỡng."""
    P = info["params"]
    o = []
    names, rows = _summary_via(chans, P)
    sv = _table("Signal via", names, rows, chans)
    names, rows = _summary_routing(chans)
    sr = _table("Signal routing", names, rows, chans)
    o.append(f"<details><summary>Summary tables (signal via, signal routing)</summary>{sv}{sr}</details>")
    for c in chans:
        if c.get("error"):
            o.append(f"<p><b>{_e(c.get('name'))}: ERROR</b> {_e(c['error'])}</p>")
            continue
        o.append(f"<details><summary>{_e(c['name'])} ({_e(c['comp_a'])} – {_e(c['comp_b'])}): overview and all "
                 f"checks incl. OK rows ({len(c['findings'])})</summary>")
        o.append(f"<p class='small'>{len(c['nets'])} nets · series parts: {_e(', '.join(c['series']) or 'none')} · "
                 f"end types: {_e(', '.join(f'{k}={v}' for k, v in c['end_types'].items()))} · "
                 f"{c['n_paths']} traces, {c['n_vias']} vias</p>")
        for w in c.get("warnings") or []:
            o.append(f"<p><b>Warning:</b> {_e(w)}</p>")
        o.append("<div class='legend small'>Overview:<span style='background:#d62728'></span>signal"
                 "<span style='background:#000'></span>signal via<span style='background:#1f5fd6'></span>GND via/pin"
                 "<span style='background:#d00000'></span>NOT OK "
                 "(hover for detail, click to open)</div>")
        o.append(c["overview_svg"])
        o.append("<table class='sort'><thead><tr><th>Status</th><th>Check</th><th>Net</th><th>Layer</th>"
                 "<th>Reference</th><th>x (mm)</th><th>y (mm)</th><th>Detail</th></tr></thead><tbody>")
        for f in c["findings"]:
            pid = f.get("point")
            o.append(f"<tr><td data-v='{STATUS_ORDER[f['status']]}'>{_sev(f['status'])}"
                     + (f" <a href='#p{pid}'>#{pid}</a>" if pid else "") +
                     f"</td><td>{_e(f['check'])}</td><td>{_e(f['net'])}</td><td>{_e(f['layer'])}</td>"
                     f"<td>{_e(f['ref'])}</td><td>{_mm(f['x'])}</td><td>{_mm(f['y'])}</td><td>{_e(f['value'])}</td></tr>")
        o.append("</tbody></table></details>")
    # 3. Reference data (thu gọn)
    o.append(f"<table class='meta-tbl'><tr><th>Board</th><td>{_e(info['board'])}</td></tr>"
             f"<tr><th>GND plane layers</th><td>{_e(', '.join(info['planes']))}</td></tr></table>")
    o.append("<details><summary>Signal via table</summary><p class='small'>Stacked vias are merged into one row.</p>"
             "<table class='sort'><thead><tr><th>Channel</th><th>Net</th><th>Type</th><th>Padstack</th><th>Pad D hole (mil)</th><th>x (mm)</th>"
             "<th>y (mm)</th><th>Layer range</th><th>Signal layers</th><th>Backdrill</th><th>Stub (mm)</th>"
             "<th>Used barrel (mm)</th><th>Nearest GND via (x, y)</th><th>Distance (mm)</th></tr></thead><tbody>")
    for c in chans:
        for r in c.get("vias", []):
            g = r["gnd"]
            o.append(f"<tr><td>{_e(c['name'])}</td><td>{_e(r['net'])}</td><td>{_e(r.get('kind', ''))}</td>"
                     f"<td>{_e(', '.join(r['defs']))}</td><td>{_e(r.get('size', ''))}</td><td>{_mm(r['x'])}</td><td>{_mm(r['y'])}</td>"
                     f"<td>{_e(r['range'])}</td><td>{_e(', '.join(r['used']))}</td><td>{_e(r['backdrill'])}</td>"
                     f"<td>{r['stub_mm']:.3f}</td><td>{r['barrel_mm']:.3f}</td>"
                     + (f"<td>({_mm(g['x'])}, {_mm(g['y'])}){' pin' if g['pin'] else ''}</td><td>{g['d_mm']:.3f}</td>"
                        if g else "<td>-</td><td data-v='1e9'>none</td>") + "</tr>")
    o.append("</tbody></table></details>")
    o.append("<details><summary>Length per net</summary><p class='small'>Length = trace (all layers) + via barrel "
             "between signal layers; nets through series parts are summed along the chain.</p>")
    for c in chans:
        if not c.get("chain_len"):
            continue
        lays = list(dict.fromkeys(l for L in c["chain_len"].values() for l in L["by_layer"]))
        o.append(f"<h3>{_e(c['name'])}</h3><table class='sort'><thead><tr><th>Group</th><th>Net</th>" +
                 "".join(f"<th>{_e(l)} (mm)</th>" for l in lays) +
                 "<th>Via (mm)</th><th>Total (mm)</th><th>Group skew (mm)</th></tr></thead><tbody>")
        grouped = {}
        for g in c["intra"]:
            for n in g["lengths"]:
                grouped[n] = g
        for n, L in c["chain_len"].items():
            g = grouped.get(n)
            o.append(f"<tr><td>{_e(_short('', g['group']) if g else '(single)')}</td><td>{_e(' + '.join(L['nets']))}</td>"
                     + "".join(f"<td>{L['by_layer'].get(l, 0):.3f}</td>" for l in lays) +
                     f"<td>{L['via_mm']:.3f}</td><td>{L['total_mm']:.3f}</td>"
                     f"<td>{g['skew_mm']:.3f}</td></tr>" if g else
                     f"<tr><td>(single)</td><td>{_e(' + '.join(L['nets']))}</td>"
                     + "".join(f"<td>{L['by_layer'].get(l, 0):.3f}</td>" for l in lays) +
                     f"<td>{L['via_mm']:.3f}</td><td>{L['total_mm']:.3f}</td><td>-</td></tr>")
        o.append("</tbody></table>")
        if c["inter"]:
            o.append("<p>Group means: " + ", ".join(f"{_e(_short('', k.split('/')))} {v:.3f}"
                                                    for k, v in c["inter"]["means"].items()) +
                     f" mm · inter-group skew <b>{c['inter']['skew_mm']:.3f} mm</b></p>")
    o.append("</details>")
    o.append("<details><summary>Thresholds and definitions</summary><table>")
    for k, v in P.items():
        o.append(f"<tr><td>review.{_e(k)}</td><td>{_e(v)}</td></tr>")
    o.append(f"<tr><td>reference nets</td><td>{_e(', '.join(info['refs']))}</td></tr></table>"
             "<p class='small'>Plane layer: largest GND polygon &ge; plane_area_ratio × largest GND polygon of the board. "
             "Reference layers of a trace: nearest plane layer above and below. Samples: trace center and both edges, "
             "every sample_step_mm; points within pad_exclusion_mm of a same-net pad/via, or inside its own antipad "
             "(void &le; 2 mm), are ignored. SOV: no copper at all on a reference layer under the trace. Reference change "
             "(GND → other net): the reference layer has copper of another net (power, signal) under the trace instead of "
             "GND. Loss of reference: no GND on any reference layer. Trace stub: trace end not connected to a pad, via, "
             "trace or polygon of the same net (open end), or ending on the middle of another trace (T-branch). Via stub: "
             "via barrel beyond the outermost signal layers; with backdrill, the remaining stub declared in EDB. "
             "Ref plane change at a via (e.g. Layer 2 → Layer 4/6) is NOT OK only when no GND via is within "
             "ref_change_gnd_via_mm.</p></details>")
    return "".join(o)
