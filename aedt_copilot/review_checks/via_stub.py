"""Luật 'via_stub' (031): stub thân via / backdrill; giữ bảng via của review. Steering: review_rules/via_stub.md."""
from . import _report
from . import _rules as X
from . import _text as T

NAME = "via_stub"
ORDER = 31
TITLE, RULE = X.meta(NAME)


def run(cc):
    rows, fs = cc.via_rows                                           # via_rows tính một lần cho mọi luật via (cache)
    return {"items": [f for f in fs if f["check"] == "Via stub"], "data": {"rows": [_report.via_row(r) for r in rows]}}


def _layers_via(f, ref_layers, metal):
    used = list(f.get("used") or [])
    if not used:
        return None
    pl = set()
    for u in used:
        pl |= set(ref_layers(u))
    return set(used), pl


def _describe(f, P, c=None):
    v = T.via_row(c, f)
    st = T.num(f.get("value"), r"stub ([0-9.]+) mm")
    top, bot = T.num(f.get("value"), r"top ([0-9.]+)"), T.num(f.get("value"), r"bottom ([0-9.]+)")
    used = list(f.get("used") or [])
    rows = [("Via at", T.xy(f)), ("Via span", str(f.get("layer") or "")),
            ("Signal layers", f"{used[0]} → {used[-1]}" if len(used) > 1 else (used[0] if used else "-")),
            ("Stub", (f"{st:.3f} mm (top {top:.3f}, bottom {bot:.3f}) — limit: none ✗")
             if None not in (st, top, bot) else str(f.get("value"))),
            ("Backdrill", (v or {}).get("backdrill") or "no")]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix")


REPORT = X.report(NAME, _describe, _layers_via)
