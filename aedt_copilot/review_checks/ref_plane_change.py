"""Luật 'ref_plane_change' (031): via tín hiệu đổi lớp plane tham chiếu. Steering: review_rules/ref_plane_change.md."""
from . import _report
from . import _rules as X
from . import _text as T

NAME = "ref_plane_change"
ORDER = 30
TITLE, RULE = X.meta(NAME)


def run(cc):
    rows, fs = cc.via_rows                                           # via_rows tính một lần cho mọi luật via (cache)
    return {"items": [f for f in fs if f["check"] == "Ref plane change"], "data": {}}


def _layers_via(f, ref_layers, metal):
    used = list(f.get("used") or [])
    if not used:
        return None
    pl = set()
    for u in used:
        pl |= set(ref_layers(u))
    return set(used), pl


def _describe(f, P, c=None):
    lim = float(P["ref_change_gnd_via_mm"])
    d = T.num(f.get("value"), r"nearest GND via ([0-9.]+) mm")
    a, _, b = str(f.get("ref") or "").partition("→")
    rows = [("Via at", T.xy(f)), ("Signal", str(f.get("layer") or "")),
            ("Reference", f"{T.planes(a)} → {T.planes(b)}"),
            ("Nearest GND via", (f"{d:.2f} mm — limit ≤ {lim:.2f} mm " + ("✗" if d > lim else "✓"))
             if d is not None else f"none — limit ≤ {lim:.2f} mm ✗")]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix", lim=lim)


def _layers_change(f, ref_layers, metal):
    used = list(f.get("used") or [])
    if not used:
        return None                                       # không biết lớp -> mặc định (lớp issue + ghi chú)
    return {used[0], used[-1]}, set(ref_layers(used[0])) | set(ref_layers(used[-1]))


REPORT = X.report(NAME, _describe, _layers_change)
