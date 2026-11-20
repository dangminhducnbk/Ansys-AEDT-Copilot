"""Luật 'sov' (031): trace qua void của lớp plane tham chiếu. Steering: review_rules/sov.md."""
from . import _refcheck as RC
from . import _rules as X
from . import _text as T

NAME = "sov"
ORDER = 10
TITLE, RULE = X.meta(NAME)
NoPlaneLayer = RC.NoPlaneLayer


def run(cc):
    items = [f for f in RC.findings(cc) if f["check"] == "SOV"]
    return {"items": items, "data": {"plane_layers": cc.ctx.B.planes}}


def _describe(f, P, c=None):
    lay, ref = str(f.get("layer") or ""), str(f.get("ref") or "")
    rows = [("Trace", f"{lay}{T.trace_seg(f)}"), ("Reference", f"{T.planes(ref)}: no copper under the trace"),
            T.length_row(f)]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix", planes=T.planes(ref))


REPORT = X.report(NAME, _describe, RC.layers_trace)
