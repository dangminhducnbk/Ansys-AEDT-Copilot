"""Check 'trace_stubs': đầu trace hở / nhánh chữ T (review.trace_stubs, không đổi)."""
from ..cut_board import review as RV
from . import _rules as X
from . import _text as T

NAME = "trace_stubs"
ORDER = 20
TITLE, RULE = X.meta(NAME)


def run(cc):
    paths, polys, vias, pins = cc.collected
    return {"items": RV.trace_stubs(paths, vias, pins, polys, cc.ctx.pt), "data": {}}


# ----------------------------------------------------------------------------- báo cáo (028: chữ của luật ở đây)
def _describe(f, P, c=None):
    t = "T-branch" if "T-junction" in str(f.get("value")) else "open trace end"
    seg = T.num(f.get("value"), r"segment length ([0-9.]+) mm")
    rows = [("At", T.xy(f)), ("Trace", str(f.get("layer") or "")), ("Kind", t),
            ("Segment length", f"{seg:.3f} mm" if seg is not None else "-")]
    return rows, X.text(NAME, "why", t), X.text(NAME, "fix", t)


def _layers(f, ref_layers, metal):
    return {f.get("layer")}, set(ref_layers(f.get("layer")))


REPORT = X.report(NAME, _describe, _layers)
