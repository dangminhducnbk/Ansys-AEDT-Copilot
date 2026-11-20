"""Luật 'serpentine' (feature 033): serpentine bù chiều dài của cặp vi sai phải đạt G >= 3H, A <= 3W, không góc 90°,
cạnh vát 45° >= 1.5W (ngưỡng review.serp_*). Mỗi serpentine vi phạm = một finding NOT OK (mục routing). Đo trong
_serp (dùng chung với pair_gap). Steering: review_rules/serpentine.md."""
from . import _rules as X
from . import _serp as SP
from . import _text as T

NAME = "serpentine"
ORDER = 65
TITLE, RULE = X.meta(NAME)
MM = SP.MM


def item(sp):
    """Serpentine có vi phạm -> finding (vị trí = tâm vùng serpentine)."""
    x, y = (sp["x0"] + sp["x1"]) / 2, (sp["y0"] + sp["y1"]) / 2
    return {"check": "Serpentine", "status": "NOT OK", "net": sp["net"], "layer": sp["layer"], "ref": "",
            "x": x, "y": y, "bbox": (sp["x0"], sp["y0"], sp["x1"], sp["y1"]), "used": [sp["layer"]],
            "group": list(sp["group"]), "serp": sp,
            "value": "; ".join(v[1] for v in sp["violations"]) + f" ({sp['n_bumps']} bumps)"}


def run(cc):
    found = SP.found(cc)
    items = [item(sp) for sp in found if sp["violations"]]
    data = [{"net": sp["net"], "layer": sp["layer"], "group": sp["group"], "bumps": sp["n_bumps"],
             "A_mm": round(sp["A"] / MM, 4), "G_mm": None if sp["G"] is None else round(sp["G"] / MM, 4),
             "W_mm": round(sp["W"] / MM, 4), "H_mm": round(sp["H"] / MM, 4),
             "violations": [v[0] for v in sp["violations"]]} for sp in found]
    return {"items": items, "data": {"serpentines": data}}


def fields(f, P):
    """Placeholder cho câu Issue / Recommendation: {problems} / {actions} ghép từ các biến thể A / G / C / S."""
    sp = f.get("serp")
    if not sp:
        return {}
    lim = sp.get("limits") or {}
    W, Hh = sp["W"], sp["H"]
    amp, gap, cham = lim.get("amp", 3), lim.get("gap", 3), lim.get("chamfer", 1.5)
    v = SP.v_txt
    fmt = {"A": v(sp["A"]), "A_lim": v(amp * W), "G": v(sp["G"] or 0), "G_lim": v(gap * Hh), "n90": len(sp["c90"]),
           "c": v(min((t[2] for t in sp["short"]), default=0)), "c_lim": v(cham * W),
           "amp": f"{amp:g}", "gap": f"{gap:g}", "cham": f"{cham:g}"}
    codes = [c for c, _ in sp["violations"]]
    probs = [X.text(NAME, "issue", c, **fmt) for c in codes]
    acts = [X.text(NAME, "recommendation", c, **fmt) for c in codes]
    a = "; ".join(acts)
    return {"problems": "; ".join(probs), "actions": a[:1].upper() + a[1:]}


def _describe(f, P, c=None):
    sp = f.get("serp") or {}
    rows = [("Serpentine", f"{f.get('layer')} at {T.xy(f)}, {sp.get('n_bumps', '?')} bumps"),
            ("Measured", str(f.get("value")))]
    codes = [x for x, _ in sp.get("violations") or []] or [None]
    return rows, X.text(NAME, "why", codes[0]), X.text(NAME, "fix", codes[0])


def _layers(f, ref_layers, metal):
    return {f.get("layer")}, set(ref_layers(f.get("layer")))


def _picture(f, paths):
    return SP.svg(f["serp"], paths) if f.get("serp") else ""


REPORT = X.report(NAME, _describe, _layers, picture=_picture, fields=fields)
