"""Hàm hình học thuần cho các luật review 030 (cặp / bộ 3, ghép net khác, mép plane, độ rộng). Mét như review.py.
Module riêng ('_') -> registry không nạp như một check."""
import math

import numpy as np
import shapely
from shapely.geometry import LineString

MM = 1e-3


def samples(pts, step):
    """Điểm mẫu dọc đường tâm, mỗi `step` (m), kèm hướng đơn vị: [(x, y, ux, uy)]."""
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L <= 0:
            continue
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        n = max(1, int(L / step))
        for k in range(n):
            t = (k + 0.5) * L / n
            out.append((x0 + ux * t, y0 + uy * t, ux, uy))
    return out


class Segs:
    """Các đoạn trace (STRtree) để hỏi khoảng cách gần nhất. items: [(pts, width, tag)]."""

    def __init__(self, items):
        geoms, self.w, self.tag = [], [], []
        for pts, w, tag in items:
            for a, b in zip(pts, pts[1:]):
                if a != b:
                    geoms.append(LineString([a, b]))
                    self.w.append(float(w))
                    self.tag.append(tag)
        self.geoms = geoms
        self.tree = shapely.STRtree(geoms) if geoms else None
        self.w = np.array(self.w)

    def nearest(self, xy):
        """xy (n, 2) -> (khoảng cách tâm-tâm (n,), chỉ số đoạn (n,)); không có đoạn -> inf / -1."""
        n = len(xy)
        d, idx = np.full(n, np.inf), np.full(n, -1)
        if self.tree is None or n == 0:
            return d, idx
        pts = shapely.points(np.asarray(xy, dtype=float))
        (i_in, i_tree), dist = self.tree.query_nearest(pts, return_distance=True, all_matches=False)
        d[i_in], idx[i_in] = dist, i_tree
        return d, idx


def near_any(xy, centers, r):
    """xy (n, 2) -> bool (n,): trong bán kính r của ít nhất một tâm."""
    if not len(centers) or not len(xy):
        return np.zeros(len(xy), dtype=bool)
    tree = shapely.STRtree(shapely.points(np.asarray(centers, dtype=float)))
    (i_in, _), dist = tree.query_nearest(shapely.points(np.asarray(xy, dtype=float)), return_distance=True,
                                         all_matches=False)
    out = np.zeros(len(xy), dtype=bool)
    out[i_in] = dist <= r
    return out


def runs(flags):
    """Các đoạn liên tiếp True -> [(i0, i1)]."""
    out, i0 = [], None
    for i, f in enumerate(flags):
        if f and i0 is None:
            i0 = i
        elif not f and i0 is not None:
            out.append((i0, i - 1))
            i0 = None
    if i0 is not None:
        out.append((i0, len(flags) - 1))
    return out


def finding(check, status, net, layer, smp, i0, i1, step, value, ref="", **extra):
    """036: status = 'NOT OK' / 'OK' (theo ngưỡng của luật)."""
    a, b = smp[i0], smp[i1]
    f = {"check": check, "status": status, "net": net, "layer": layer, "ref": ref,
         "x": (a[0] + b[0]) / 2, "y": (a[1] + b[1]) / 2, "start": (a[0], a[1]), "end": (b[0], b[1]),
         "len_mm": (i1 - i0 + 1) * step / MM, "value": value,
         "bbox": (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))}
    f.update(extra)
    return f


def merge(found, key):
    """Gộp các đoạn vi phạm theo key(f) -> một finding mỗi nhóm: vị trí = đoạn dài nhất; thêm runs, total_mm."""
    out, idx = [], {}
    for f in found:
        k = key(f)
        if k not in idx:
            idx[k] = len(out)
            out.append(dict(f, runs=1, total_mm=f["len_mm"]))
            continue
        g = out[idx[k]]
        runs, tot = g["runs"] + 1, g["total_mm"] + f["len_mm"]
        if f["len_mm"] > g["len_mm"]:
            g = dict(f)
        g.update(runs=runs, total_mm=tot)
        out[idx[k]] = g
    return out


def small_void(cu, layer, x, y, lim):
    """Điểm nằm trong void nhỏ (<= lim, vd antipad) của lớp plane."""
    try:
        for i, k in cu.voids_at(layer, x, y):
            b = cu.layers[layer][i][2][k][0]
            if max(b[2] - b[0], b[3] - b[1]) <= lim:
                return True
    except Exception:
        return False
    return False


def mask_points(collected):
    """Tâm pad / via của channel (vùng neck-down)."""
    _, _, vias, pins = collected
    return [(v["x"], v["y"]) for v in vias + pins]


def member_paths(paths, chains, group):
    """{tên nhóm: [path]} theo chuỗi net (qua linh kiện nối tiếp)."""
    return {s: [p for p in paths if p["net"] in set(chains.get(s, [s]))] for s in group}


def pair_gaps(cc):
    """Khe mép-mép giữa các thành viên của cặp / bộ 3, theo lớp (tính một lần cho luật 2 và 6).
    -> [{group, layer, members, nominal_median_m, res: {member: [(path, samples, gap (m) array, skip bool array)]}}]."""
    def f():
        R, step = cc.ctx.R, cc.ctx.step
        zone = float(R.get("neckdown_zone_mm", 1.0)) * MM
        paths, g = cc.collected[0], cc.groups
        centers = mask_points(cc.collected)
        out = []
        for grp in g["groups"]:
            if len(grp) != 2:                                    # chỉ cặp vi sai (bộ 3 CPHY: chỉ luật lệch chiều dài)
                continue
            mp = member_paths(paths, g["chains"], grp)
            for lay in sorted({p["layer"] for ps in mp.values() for p in ps}):
                per = {m: [p for p in mp[m] if p["layer"] == lay] for m in grp}
                members = [m for m in grp if per[m]]
                if len(members) < 2:
                    continue
                res, allg = {}, []
                for m in members:
                    others = Segs([(p["pts"], p["w"], o) for o in members if o != m for p in per[o]])
                    for p in per[m]:
                        smp = samples(p["pts"], step)
                        if not smp:
                            continue
                        xy = [(s[0], s[1]) for s in smp]
                        d, idx = others.nearest(xy)
                        ow = np.where(idx >= 0, others.w[np.maximum(idx, 0)] if len(others.w) else 0.0, 0.0)
                        gap = d - p["w"] / 2 - ow / 2
                        skip = near_any(xy, centers, zone)
                        res.setdefault(m, []).append((p, smp, gap, skip))
                        allg += [float(x) for x, s in zip(gap, skip) if not s and np.isfinite(x)]
                if allg:
                    out.append({"group": list(grp), "layer": lay, "members": members,
                                "nominal_median_m": float(np.median(allg)), "res": res})
        return out
    return cc._get("pair_gaps", f)


def paired_nets(cc):
    """Tập net thuộc cặp / bộ 3 (qua chuỗi net)."""
    g = cc.groups
    return {n for grp in g["groups"] if len(grp) > 1 for s in grp for n in g["chains"].get(s, [s])}


def height(B, layer, ref):
    """Chiều dày điện môi (m) giữa mặt đồng của lớp trace và lớp plane tham chiếu (theo cao độ stackup)."""
    lo, hi = B.elev[layer]
    rlo, rhi = B.elev[ref]
    return abs(rlo - hi) if rlo >= hi else abs(lo - rhi)
