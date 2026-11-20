"""Check 'stackup_width' (feature 030, luật 6): độ rộng trace (theo lớp) và khe giữa các dây của cặp (theo lớp) so với
bảng stackup của nhà máy (review_checks/_stackup.py, tool review_stackup_table). Lệch > review.stackup_tol_mm ->
NOT OK. Không có bảng / lớp không có trong bảng -> OK (dữ liệu, không đo được). Không tính trở kháng (2026-11-11)."""
import numpy as np

from . import _si as S
from . import _stackup
from . import _rules as X
from . import _text as T

NAME = "stackup_width"
ORDER = 100
TITLE, RULE = X.meta(NAME)
MM = S.MM


def _info(check, p, value):
    x, y = p["pts"][0]
    return {"check": check, "status": "OK", "net": p["net"], "layer": p["layer"], "ref": "", "x": x, "y": y,
            "bbox": (x, y, x, y), "value": value}


def run(cc):
    R, step = cc.ctx.R, cc.ctx.step
    tol, zone = float(R["stackup_tol_mm"]) * MM, float(R["neckdown_zone_mm"]) * MM
    paths = cc.collected[0]
    if not paths:
        return {"items": [], "data": {}}
    table = _stackup.load(cc.ctx.board)
    if not table:
        return {"items": [_info("No stackup table", paths[0], "no stackup width / gap table for this board "
                                "(review_stackup_table)")], "data": {"table": None}}
    paired = S.paired_nets(cc)
    centers = S.mask_points(cc.collected)
    items, seen = [], set()
    for p in paths:
        smp = S.samples(p["pts"], step)
        if not smp:
            continue
        skip = S.near_any([(s[0], s[1]) for s in smp], centers, zone)
        if skip.mean() > 0.5:                                           # đoạn break-out quanh pad / via
            continue
        isp = p["net"] in paired
        exp = _stackup.expected(table, p["layer"], isp)
        kind = "pair" if isp else "single-ended"
        if exp is None or not exp[0]:
            k = ("missing", p["layer"], kind)
            if k not in seen:
                seen.add(k)
                items.append(_info("No stackup value", p, f"no {kind} width for {p['layer']} in the stackup table"))
            continue
        d = min(abs(p["w"] - w * MM) for w in exp[0])
        k = ("w", p["net"], p["layer"], round(p["w"] / MM, 4))
        if d > tol + 1e-12 and k not in seen:
            seen.add(k)
            f = _info("Width vs stackup", p, f"width {p['w'] / MM:.3f} mm vs stackup "
                                             f"{' / '.join(f'{w:.3f}' for w in exp[0])} mm ({kind})")
            f.update(status="NOT OK", width_mm=p["w"] / MM, table_mm=list(exp[0]), kind=kind)
            items.append(f)
    for e in S.pair_gaps(cc):
        exp = _stackup.expected(table, e["layer"], True)
        if not exp or not exp[1]:
            continue
        some = next(iter(e["res"].values()))[0]
        p0 = some[0]
        gaps = [float(g) for v in e["res"].values() for _, _, gap, skip in v for g, s in zip(gap, skip)
                if not s and np.isfinite(g)]
        if not gaps:
            continue
        med = float(np.median(gaps))
        best = min(exp[1], key=lambda q: abs(q["width_mm"] * MM - p0["w"]))
        if abs(med - best["gap_mm"] * MM) > tol + 1e-12:
            f = _info("Gap vs stackup", p0, f"pair gap {med / MM:.3f} mm vs stackup {best['gap_mm']:.3f} mm "
                                            f"({best['name']})")
            f.update(status="NOT OK", gap_mm=med / MM, table_gap_mm=best["gap_mm"], group=e["group"],
                     pair_name=best["name"])
            items.append(f)
    return {"items": items, "data": {"table": _stackup.path(cc.ctx.board) if cc.ctx.board else None}}


def _describe(f, P, c=None):
    tol = float(P["stackup_tol_mm"])
    chk = f["check"]
    if chk == "Width vs stackup":
        rows = [("Trace", f"{f.get('layer')} at {T.xy(f)} ({f.get('kind')})"),
                ("Width", f"{f.get('width_mm', 0):.3f} mm — stackup "
                          f"{' / '.join(f'{w:.3f}' for w in f.get('table_mm') or [])} mm ± {tol:g} ✗")]
    elif chk == "Gap vs stackup":
        rows = [("Pair / trio", " / ".join(f.get("group") or [])), ("Layer", str(f.get("layer"))),
                ("Gap", f"{f.get('gap_mm', 0):.3f} mm (median) — stackup {f.get('table_gap_mm', 0):.3f} mm "
                        f"({f.get('pair_name')}) ± {tol:g} ✗")]
    else:
        rows = [("At", T.xy(f)), ("Layer", str(f.get("layer"))), ("Note", str(f.get("value")))]
    return rows, X.text(NAME, "why", chk), X.text(NAME, "fix", chk)


def _layers(f, ref_layers, metal):
    return {f.get("layer")}, set(ref_layers(f.get("layer")))


REPORT = X.report(NAME, _describe, _layers)
