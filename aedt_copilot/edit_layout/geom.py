"""Hình học 2D (shapely, đơn vị mm) trên dữ liệu vùng do extract.py đọc từ EDB.

Region(D): D = dict của extract.extract_region (signal_layers, prims, instances, pdefs, comps, box).
"""
import collections

import numpy as np
from shapely import contains_xy
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.validation import make_valid


def valid(g):
    return g if g.is_valid else make_valid(g)


def parts(g):
    """Các Polygon con của một geometry (bỏ line/point)."""
    if g is None or g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    out = []
    for q in getattr(g, "geoms", []):
        out += parts(q)
    return out


def polys_only(g):
    return unary_union(parts(g)) if parts(g) else Polygon()


def ring_list(poly):
    """Polygon -> {"ext": [[x, y]...], "holes": [[...]...]} (mm, vòng khép kín)."""
    return {"ext": [[round(x, 6), round(y, 6)] for x, y in poly.exterior.coords],
            "holes": [[[round(x, 6), round(y, 6)] for x, y in r.coords] for r in poly.interiors]}


def to_geom(obj):
    """Nhận [[x,y]...] | {"ext","holes"} | {"box":[x0,y0,x1,y1]} | {"circle":[x,y,r]} -> shapely."""
    if isinstance(obj, dict):
        if "box" in obj:
            return box(*obj["box"])
        if "circle" in obj:
            x, y, r = obj["circle"]
            return Point(x, y).buffer(r, 32)
        return valid(Polygon(obj["ext"], obj.get("holes") or []))
    if len(obj) == 4 and not isinstance(obj[0], (list, tuple)):          # [x0, y0, x1, y1]
        return box(*obj)
    return valid(Polygon(obj))                                             # [[x, y], ...]


class Region:
    def __init__(self, D):
        self.D = D
        self.SIG = D["signal_layers"]
        self.box = box(*D["box"])
        self.LAY = collections.defaultdict(list)       # layer -> [(net, type, geom, id)]
        self.BYID = {}
        for p in D["prims"]:
            if "err" in p or p.get("is_void"):
                continue
            g = self._geom(p)
            if g is not None and not g.is_empty:
                self.LAY[p["layer"]].append((p["net"], p["type"], g, p["id"]))
                self.BYID[p["id"]] = (p["layer"], p["net"], p["type"], g)
        self.PD = D["pdefs"]
        self.inst = [dict(id=v[0], pd=v[1], net=v[2], x=v[3], y=v[4], sl=v[5], el=v[6], comp=v[7], pin=v[8])
                     for v in D["instances"]]

    @staticmethod
    def _geom(p):
        if p["type"] == "path" and len(p.get("poly") or []) < 3:
            cl = p.get("center_line") or []
            if not cl:
                return None
            w = max(p.get("width", 0), 1e-4) / 2
            g = LineString(cl).buffer(w, cap_style=1) if len(cl) > 1 else Point(cl[0]).buffer(w)
            return valid(g)
        if len(p.get("poly") or []) < 3:
            return None
        g = valid(Polygon(p["poly"]))
        hs = [valid(Polygon(v)) for v in p.get("voids", []) if len(v) >= 3]
        if hs:                                          # EDB: copper = outline - UNION(voids)
            g = g.difference(unary_union(hs))
        return polys_only(g)

    # ------------------------------------------------------------------ truy vấn
    def netgeom(self, L, n, types=None):
        gs = [g for nn, t, g, i in self.LAY[L] if nn == n and (types is None or t in types)]
        return unary_union(gs) if gs else Polygon()

    def others(self, L, excl, types=None):
        gs = [g for nn, t, g, i in self.LAY[L] if nn not in excl and (types is None or t in types)]
        return unary_union(gs) if gs else Polygon()

    def polygons(self, L, net, near=None):
        """[(id, geom)] polygon (không phải trace) của net trên lớp L, giao với `near` nếu có."""
        return [(i, g) for nn, t, g, i in self.LAY[L]
                if nn == net and t != "path" and (near is None or g.intersects(near))]

    def idx(self, L):
        return self.SIG.index(L)

    def spans(self, v, L):
        if L not in self.SIG or v["sl"] not in self.SIG or v["el"] not in self.SIG:
            return False
        a, b = sorted([self.idx(v["sl"]), self.idx(v["el"])])
        return a <= self.idx(L) <= b

    def on_layer(self, v, L):
        """Via xuyên qua L, hoặc pin có pad trên L."""
        return (L in (v["sl"], v["el"])) if v["pin"] else self.spans(v, L)

    def padr(self, pd, L):
        p = self.PD.get(pd, {}).get("pads", {}).get(L)
        if not p or not p[1]:
            return 0.0
        return p[1][0] / 2 if len(p[1]) == 1 else max(p[1][:2]) / 2

    def padr_min(self, pd, L):
        """Nửa cạnh NGẮN của pad (mm): vùng chắc chắn là đồng quanh tâm pad (pad chữ nhật / oval)."""
        p = self.PD.get(pd, {}).get("pads", {}).get(L)
        if not p or not p[1]:
            return 0.0
        return p[1][0] / 2 if len(p[1]) == 1 else min(x for x in p[1][:2] if x > 0) / 2

    def vias_near(self, geom, L=None, net=None, excl_net=None, d=0.0):
        out = []
        for v in self.inst:
            if net is not None and v["net"] != net:
                continue
            if excl_net is not None and v["net"] == excl_net:
                continue
            if L is not None and not self.on_layer(v, L):
                continue
            if geom.distance(Point(v["x"], v["y"])) <= d:
                out.append(v)
        return out

    def via_void_union(self, L, net_keep, region, r_of):
        """Hợp các vòng tròn clearance của via/pin net khác (≠ net_keep) xuyên lớp L gần `region`."""
        cs = []
        for v in self.inst:
            if v["net"] == net_keep or not self.on_layer(v, L):
                continue
            r = r_of(v, L)
            if r <= 0:
                continue
            p = Point(v["x"], v["y"])
            if region.distance(p) < r:
                cs.append(p.buffer(r, 32))
        return unary_union(cs) if cs else Polygon()


def min_width(geom, window, zone_a, zone_b, h=0.05):
    """Độ rộng đồng nhỏ nhất (mm) giữa 2 vùng đầu cuối của `geom` trong `window` (max-flow trên lưới h mm,
    8 hướng, dung lượng đỉnh). Trả (width_mm, [điểm nghẽn])."""
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import breadth_first_order, maximum_flow
    x0, y0, x1, y1 = window.bounds
    xs = np.arange(x0 + h / 2, x1, h)
    ys = np.arange(y0 + h / 2, y1, h)
    X, Y = np.meshgrid(xs, ys)
    cu = contains_xy(geom, X, Y) & contains_xy(window, X, Y)
    A = contains_xy(zone_a, X, Y) & cu
    B = contains_xy(zone_b, X, Y) & cu
    n = int(cu.sum())
    if n == 0 or not A.any() or not B.any():
        return 0.0, []
    ny, nx = cu.shape
    idx = -np.ones(cu.shape, dtype=np.int64)
    idx[cu] = np.arange(n)
    S, T, BIG = 2 * n, 2 * n + 1, 10 ** 6
    ii = np.arange(n)
    rows, cols, caps = [2 * ii], [2 * ii + 1], [np.ones(n, dtype=np.int64)]
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        if dx >= 0:
            a = cu[: ny - dy, : nx - dx] & cu[dy:, dx:]
            ia, ib = idx[: ny - dy, : nx - dx][a], idx[dy:, dx:][a]
        else:
            a = cu[: ny - dy, 1:] & cu[dy:, : nx - 1]
            ia, ib = idx[: ny - dy, 1:][a], idx[dy:, : nx - 1][a]
        rows += [2 * ia + 1, 2 * ib + 1]
        cols += [2 * ib, 2 * ia]
        caps += [np.full(len(ia), BIG), np.full(len(ia), BIG)]
    il, ir = idx[A], idx[B]
    rows += [np.full(len(il), S), 2 * ir + 1]
    cols += [2 * il, np.full(len(ir), T)]
    caps += [np.full(len(il), BIG), np.full(len(ir), BIG)]
    N = 2 * n + 2
    M = csr_matrix((np.concatenate(caps).astype(np.int32), (np.concatenate(rows), np.concatenate(cols))), shape=(N, N))
    res = maximum_flow(M, S, T)
    Mc = M.tocoo()
    fl = np.asarray(res.flow.tocsr()[Mc.row, Mc.col]).ravel()
    fw, bw = (Mc.data - fl) > 0, fl > 0
    rr = np.concatenate([Mc.row[fw], Mc.col[bw]])
    cc = np.concatenate([Mc.col[fw], Mc.row[bw]])
    Rg = csr_matrix((np.ones(len(rr)), (rr, cc)), shape=(N, N))
    reach = np.zeros(N, bool)
    reach[breadth_first_order(Rg, S, directed=True, return_predecessors=False)] = True
    cut = ii[reach[2 * ii] & ~reach[2 * ii + 1]]
    pos = np.argwhere(cu)
    pts = [(round(float(xs[pos[k][1]]), 3), round(float(ys[pos[k][0]]), 3)) for k in cut]
    return round(res.flow_value * h, 3), pts
