"""Luật 'via_clearance' (032): trace đi qua void clearance (antipad) của via NET KHÁC trên lớp plane tham chiếu -> OK (dữ liệu, 036).
Clearance của via cùng net (trace vào chính via của nó) không báo. Steering: review_rules/via_clearance.md."""
from . import _refcheck as RC
from . import _rules as X
from . import _text as T

NAME = "via_clearance"
ORDER = 13
TITLE, RULE = X.meta(NAME)
NoPlaneLayer = RC.NoPlaneLayer


def run(cc):
    return {"items": [f for f in RC.findings(cc) if f["check"] == "Trace over via clearance"], "data": {}}


def _describe(f, P, c=None):
    vs = f.get("vias") or []
    sz = f.get("void_mm") or [0, 0]
    rows = [("Trace", f"{f.get('layer')}{T.trace_seg(f)}"), ("Planes", T.planes(f.get("ref") or "")),
            ("Vias", ", ".join(f"{v[2]} at ({T.mm(v[0])}, {T.mm(v[1])}) mm" for v in vs[:4])
             + (f" +{len(vs) - 4} more" if len(vs) > 4 else "")),
            ("Void", f"up to {sz[0]:.2f} x {sz[1]:.2f} mm"), T.length_row(f)]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix")


REPORT = X.report(NAME, _describe, RC.layers_trace)
