"""Luật 'loss_of_reference' (031): không GND trên mọi lớp tham chiếu. Steering: review_rules/loss_of_reference.md."""
from . import _refcheck as RC
from . import _rules as X
from . import _text as T

NAME = "loss_of_reference"
ORDER = 12
TITLE, RULE = X.meta(NAME)
NoPlaneLayer = RC.NoPlaneLayer


def run(cc):
    items = [f for f in RC.findings(cc) if f["check"] == "Loss of reference"]
    return {"items": items, "data": {}}


def _describe(f, P, c=None):
    lay, ref = str(f.get("layer") or ""), str(f.get("ref") or "")
    rows = [("Trace", f"{lay}{T.trace_seg(f)}"), ("Reference", f"{T.planes(ref)}: no GND on any of them"),
            T.length_row(f)]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix")


REPORT = X.report(NAME, _describe, RC.layers_trace)
