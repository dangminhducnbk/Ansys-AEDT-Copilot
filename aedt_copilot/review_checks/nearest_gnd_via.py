"""Luật 'nearest_gnd_via' (031): via GND / pin GND gần nhất của via tín hiệu. Steering: review_rules/nearest_gnd_via.md."""
from . import _report
from . import _rules as X
from . import _text as T

NAME = "nearest_gnd_via"
ORDER = 32
TITLE, RULE = X.meta(NAME)


def run(cc):
    rows, fs = cc.via_rows                                           # via_rows tính một lần cho mọi luật via (cache)
    return {"items": [f for f in fs if f["check"] == "Nearest GND via"], "data": {}}


def _layers_via(f, ref_layers, metal):
    used = list(f.get("used") or [])
    if not used:
        return None
    pl = set()
    for u in used:
        pl |= set(ref_layers(u))
    return set(used), pl


def _describe(f, P, c=None):
    lim = float(P["gnd_via_flag_mm"])
    d = T.num(f.get("value"), r"nearest GND via ([0-9.]+) mm")
    at = str(f.get("value") or "").partition(" at ")[2]
    rows = [("Via at", T.xy(f)), ("Via layers", str(f.get("layer") or "")),
            ("Nearest GND via", (f"{d:.2f} mm" + (f" at {at} mm" if at else "") + f" — limit ≤ {lim:.2f} mm ✗")
             if d is not None else str(f.get("value")))]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix", lim=lim)


REPORT = X.report(NAME, _describe, _layers_via)
