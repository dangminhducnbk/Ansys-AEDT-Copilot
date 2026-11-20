"""Thao tác 'trace' (CHỈ ĐỌC, feature 008): dò channel trên board / design bất kỳ - net, nhóm vi sai, R/C/L nối tiếp,
loại đầu, pin tín hiệu 2 đầu. Dùng interface_sim.content._board_trace (cùng luật isim_trace)."""
from ..core.errors import CopilotInputError
from . import _common as C

NAME = "trace"
ORDER = 1
READ_ONLY = True
SECTIONS = ("cutout",)


def text_list(v, name):
    if v in (None, "", []):
        return []
    if isinstance(v, str):
        v = [x.strip() for x in v.split(",") if x.strip()]
    if not isinstance(v, (list, tuple)) or not all(isinstance(x, str) and x.strip() for x in v):
        raise CopilotInputError(name, "list of names (or comma separated text)", v)
    return [x.strip() for x in v]


def validate(values, targets):
    P = C.params(values, SECTIONS)
    targets["refdes"] = text_list(targets.get("refdes"), "refdes")
    targets["nets"] = text_list(targets.get("nets"), "nets")
    if not targets["refdes"] and not targets["nets"]:
        raise CopilotInputError("refdes", "2 refdes, or 1 refdes + nets, or nets", targets.get("refdes"))
    if len(targets["refdes"]) < 2 and not targets["nets"]:
        raise CopilotInputError("nets", "net names / patterns when fewer than 2 refdes are given", [])
    return P, targets


def prepare(edb, P, targets):
    return targets


def run(edb, P, targets, log):
    from ..interface_sim.content import _board_trace
    refs = list(P["cutout"]["reference_nets"])
    prop, candidates, end_types, warnings = _board_trace(edb, targets["refdes"], targets["nets"], refs)
    nets = set(prop["nets"])
    inst = edb.components.instances
    pins = {rd: {str(p.pin_number or pn): p.net_name for pn, p in inst[rd].pins.items() if p.net_name in nets}
            for rd in (prop["comp_a"], prop["comp_b"])}
    return {"comp_a": prop["comp_a"], "comp_b": prop["comp_b"], "nets": prop["nets"],
            "diff_groups": prop["diff_groups"], "series": prop["series"], "end_types": end_types, "pins": pins,
            "candidates": candidates, "warnings": warnings}


def check(edb, P, targets):
    return []
