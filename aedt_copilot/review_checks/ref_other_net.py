"""Luật 'ref_other_net' (031): lớp tham chiếu có đồng net khác thay GND. Steering: review_rules/ref_other_net.md."""
from . import _refcheck as RC
from . import _rules as X
from . import _text as T

NAME = "ref_other_net"
ORDER = 11
TITLE, RULE = X.meta(NAME)
NoPlaneLayer = RC.NoPlaneLayer


def run(cc):
    items = [f for f in RC.findings(cc) if f["check"] == "Ref to other net"]
    return {"items": items, "data": {}}


def _describe(f, P, c=None):
    lay, ref = str(f.get("layer") or ""), str(f.get("ref") or "")
    pl, _, other = ref.partition(":")
    rows = [("Trace", f"{lay}{T.trace_seg(f)}"), ("Reference", f"{pl.strip()}: copper of {other.strip()} instead of GND"),
            T.length_row(f)]
    return rows, X.text(NAME, "why", other=other.strip()), X.text(NAME, "fix")


REPORT = X.report(NAME, _describe, RC.layers_trace)
