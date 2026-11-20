"""Check 'plane_edge' (feature 030, luật 4): trace nằm trên GND của lớp plane tham chiếu nhưng mép plane / mép void
cách tâm trace < D = max(review.plane_edge_factor x H, review.plane_edge_min_mm) (H = điện môi giữa lớp trace và
plane, theo cao độ stackup) trên đoạn >= review.plane_edge_min_len_mm -> NOT OK. Không có GND dưới tâm = SOV (check
reference), không tính ở đây; bỏ qua vùng neck-down quanh pad / via."""
from . import _si as S
from . import _rules as X
from . import _text as T

NAME = "plane_edge"
ORDER = 80
TITLE, RULE = X.meta(NAME)
MM = S.MM


def run(cc):
    R, step = cc.ctx.R, cc.ctx.step
    fac, dmin = float(R["plane_edge_factor"]), float(R["plane_edge_min_mm"]) * MM
    minlen, zone = float(R["plane_edge_min_len_mm"]) * MM, float(R["neckdown_zone_mm"]) * MM
    B = cc.ctx.B
    if not B.planes:
        return {"items": [], "data": {}}
    cu, _ = cc.copper
    centers = S.mask_points(cc.collected)
    found = []
    vlim = 2 * MM                                                       # void <= 2 mm = antipad (như SOV), không tính
    for p in cc.collected[0]:
        refs = B.ref_layers(p["layer"])
        smp = S.samples(p["pts"], step)
        if not refs or not smp:
            continue
        skip = S.near_any([(s[0], s[1]) for s in smp], centers, zone)
        per = {}                                                        # lớp plane -> (cờ từng mẫu, D, H)
        for r in refs:
            H = S.height(B, p["layer"], r)
            D = max(fac * H, dmin)
            flags = []
            for (x, y, ux, uy), s in zip(smp, skip):
                if s or not cu.covered(r, x, y):
                    flags.append(False)
                    continue
                nx, ny = -uy * D, ux * D
                edge = False
                for qx, qy in ((x + nx, y + ny), (x - nx, y - ny)):
                    if not cu.covered(r, qx, qy) and not S.small_void(cu, r, qx, qy, vlim):
                        edge = True
                flags.append(edge)
            per[r] = (flags, D, H)
        anyf = [any(per[r][0][i] for r in refs) for i in range(len(smp))]  # 032: MỘT phát hiện mỗi đoạn, mọi plane
        for i0, i1 in S.runs(anyf):
            if (i1 - i0 + 1) * step < minlen - 1e-12:
                continue
            pls = [r for r in refs if any(per[r][0][i0:i1 + 1])]
            info = [{"plane": r, "limit_mm": per[r][1] / MM, "h_mm": per[r][2] / MM} for r in pls]
            found.append(S.finding("Near plane edge", "NOT OK", p["net"], p["layer"], smp, i0, i1, step, "",
                                   ref=", ".join(pls), planes_info=info))
    items = []
    for f in S.merge(found, lambda f: (f["net"], f["layer"])):
        same = [x for x in found if (x["net"], x["layer"]) == (f["net"], f["layer"])]
        info = {}
        for x in same:
            for q in x["planes_info"]:
                info.setdefault(q["plane"], q)
        f["planes_info"] = [info[r] for r in info]
        f["ref"] = ", ".join(info)
        f["value"] = ("GND edge within " + "; ".join(f"{q['plane']} {q['limit_mm']:.3f} mm (H {q['h_mm']:.3f} mm)"
                                                     for q in f["planes_info"])
                      + f" of the trace centre on {f['runs']} stretch(es), {f['total_mm']:.3f} mm in total "
                        f"(longest {f['len_mm']:.3f} mm)")
        items.append(f)
    return {"items": items, "data": {}}


def _describe(f, P, c=None):
    fac = float(P["plane_edge_factor"])
    rows = [("Trace", f"{f.get('layer')}{T.trace_seg(f)}"), ("Reference", T.planes(f.get("ref") or ""))]
    for q in f.get("planes_info") or []:                                # 032: một dòng mỗi plane trong cùng phát hiện
        rows.append((f"Edge distance {q['plane']}", f"< {q['limit_mm']:.3f} mm — limit ≥ {q['limit_mm']:.3f} mm "
                                                   f"(max({fac:g} × H {q['h_mm']:.3f} mm, "
                                                   f"{float(P['plane_edge_min_mm']):g} mm)) ✗"))
    rows += [T.length_row(f), ("Stretches", f"{f.get('runs', 1)}, {f.get('total_mm', 0):.3f} mm in total")]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix", fac=fac, ref=T.planes(f.get("ref") or ""))


def _layers(f, ref_layers, metal):
    pls = {r.strip() for r in str(f.get("ref") or "").split(",") if r.strip()}
    return {f.get("layer")}, pls or set(ref_layers(f.get("layer")))


REPORT = X.report(NAME, _describe, _layers)
