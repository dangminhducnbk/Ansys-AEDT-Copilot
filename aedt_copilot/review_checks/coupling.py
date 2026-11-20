"""Check 'coupling' (feature 030, luật 3): trace tín hiệu chạy song song với trace của net khác (không phải net tham
chiếu) gần hơn review.coupling_gap_factor x độ rộng (mép-mép, luật 3W) trên đoạn >= review.coupling_min_len_mm ->
NOT OK. Chỉ so trace cùng lớp trong cửa sổ channel; bỏ qua vùng neck-down quanh pad / via."""
from collections import Counter

from . import _si as S
from . import _rules as X
from . import _text as T

NAME = "coupling"
ORDER = 70
TITLE, RULE = X.meta(NAME)
MM = S.MM


def _other_paths(cc, nets, layer):
    from ..cut_board import review as RV
    win, refs = cc.window, set(cc.ctx.refs)
    by = cc.ctx.edb.modeler.primitives_by_layer
    out = []
    for p in by.get(layer, []) if hasattr(by, "get") else []:
        try:
            if type(p).__name__ not in ("EdbPath", "Path"):
                continue
            n = p.net_name
            if not n or n in nets or n in refs:
                continue
            b = p.bbox
            if b[2] < win[0] or b[0] > win[2] or b[3] < win[1] or b[1] > win[3]:
                continue
            pts = RV._pts(p)
            if len(pts) >= 2:
                out.append((pts, float(p.width), n))
        except Exception:
            continue
    return out


def run(cc):
    R, step = cc.ctx.R, cc.ctx.step
    fac, minlen = float(R["coupling_gap_factor"]), float(R["coupling_min_len_mm"]) * MM
    zone = float(R["neckdown_zone_mm"]) * MM
    paths = cc.collected[0]
    nets = set(cc.trace["nets"])
    centers = S.mask_points(cc.collected)
    found, segs = [], {}
    for p in paths:
        lay = p["layer"]
        if lay not in segs:
            segs[lay] = S.Segs(_other_paths(cc, nets, lay))
        o = segs[lay]
        if o.tree is None:
            continue
        smp = S.samples(p["pts"], step)
        if not smp:
            continue
        xy = [(s[0], s[1]) for s in smp]
        d, idx = o.nearest(xy)
        gap = d - p["w"] / 2 - o.w[idx.clip(0)] / 2
        skip = S.near_any(xy, centers, zone)
        lim = fac * p["w"]
        flags = [(not s) and i >= 0 and g < lim for g, i, s in zip(gap, idx, skip)]
        for i0, i1 in S.runs(flags):
            if (i1 - i0 + 1) * step < minlen - 1e-12:
                continue
            other = Counter(o.tag[i] for i in idx[i0:i1 + 1]).most_common(1)[0][0]
            gmin = float(min(gap[i0:i1 + 1]))
            found.append(S.finding("Coupling to other net", "NOT OK", p["net"], lay, smp, i0, i1, step,
                                   f"{other} at {gmin / MM:.3f} mm edge to edge (limit {lim / MM:.3f} mm = "
                                   f"{fac:g} × width) over {(i1 - i0 + 1) * step / MM:.3f} mm",
                                   ref=other, other_net=other, gap_min_mm=gmin / MM, limit_mm=lim / MM))
    items = []
    for f in S.merge(found, lambda f: (f["net"], f["layer"], f["other_net"])):
        same = [x for x in found if (x["net"], x["layer"], x["other_net"]) == (f["net"], f["layer"], f["other_net"])]
        f["gap_min_mm"] = min(x["gap_min_mm"] for x in same)
        f["value"] = (f"{f['other_net']} at {f['gap_min_mm']:.3f} mm edge to edge (limit {f['limit_mm']:.3f} mm = "
                      f"{fac:g} × width) on {f['runs']} stretch(es), {f['total_mm']:.3f} mm in total")
        items.append(f)
    return {"items": items, "data": {}}


def _describe(f, P, c=None):
    fac = float(P["coupling_gap_factor"])
    rows = [("Trace", f"{f.get('layer')}{T.trace_seg(f)}"), ("Other net", str(f.get("other_net") or f.get("ref"))),
            ("Edge gap", f"{f.get('gap_min_mm', 0):.3f} mm — limit ≥ {f.get('limit_mm', 0):.3f} mm "
                         f"({fac:g} × width) ✗"), T.length_row(f),
            ("Stretches", f"{f.get('runs', 1)}, {f.get('total_mm', 0):.3f} mm in total")]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix", fac=fac)


def _layers(f, ref_layers, metal):
    return {f.get("layer")}, set(ref_layers(f.get("layer")))


REPORT = X.report(NAME, _describe, _layers)
