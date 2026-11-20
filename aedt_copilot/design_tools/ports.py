"""Thao tác 'ports': tạo / thay coax port cho pin của net đã chọn, tên <refdes>.<pin>.<net> (feature 007)."""
from ..core.errors import CopilotInputError
from . import _common as C

NAME = "ports"
ORDER = 40
SECTIONS = ()


def _list(v, name):
    if v in (None, "", []):
        return []
    if isinstance(v, str):
        v = [x.strip() for x in v.split(",")]
    if not isinstance(v, (list, tuple)) or not all(isinstance(x, str) and x.strip() for x in v):
        raise CopilotInputError(name, "list of names (or comma separated text)", v)
    return [x.strip() for x in v]


def validate(values, targets):
    P = C.params(values, SECTIONS)
    targets["refdes"] = _list(targets.get("refdes"), "refdes")
    if not targets["refdes"]:
        raise CopilotInputError("refdes", "at least one component refdes", targets.get("refdes"))
    targets["nets"] = _list(targets.get("nets"), "nets")
    if not isinstance(targets.get("replace", False), bool):
        raise CopilotInputError("replace", "true or false", targets.get("replace"))
    targets["replace"] = bool(targets.get("replace", False))
    return P, targets


def prepare(edb, P, targets):
    inst = dict(edb.components.instances)
    refs = set(P["cutout"]["reference_nets"])
    per = {}
    for rd in targets["refdes"]:
        if rd not in inst:
            raise CopilotInputError("refdes", "component on the design, closest: " +
                                    ", ".join(C.closest(rd, list(inst))), rd)
        pin_nets = {p.net_name for p in inst[rd].pins.values() if p.net_name}
        if targets["nets"]:
            bad = [n for n in targets["nets"] if n not in pin_nets]
            if len(bad) == len(targets["nets"]):
                raise CopilotInputError("nets", f"nets on {rd} pins, closest: " +
                                        ", ".join(C.closest(bad[0], sorted(pin_nets))), bad)
            per[rd] = [n for n in targets["nets"] if n in pin_nets]
        else:
            per[rd] = sorted(n for n in pin_nets if n not in refs)
    targets["per_refdes"] = per
    return targets


def run(edb, P, targets, log):
    from ..cut_board import cutter
    created, skipped = [], []
    for rd, nets in targets["per_refdes"].items():
        r = cutter.create_ports(edb, rd, nets, log, replace=targets["replace"])
        created += r["created"]
        skipped += r["skipped"]
    return {"created": created, "skipped": skipped}


def check(edb, P, targets):
    from ..cut_board import cutter
    have = set(dict(edb.ports))
    inst = dict(edb.components.instances)
    mm = []
    for rd, nets in targets["per_refdes"].items():
        for pn, p in inst[rd].pins.items():
            if p.net_name in nets:
                n = cutter.port_name(rd, pn, p)
                if n not in have:
                    mm.append({"item": f"port {n}", "expected": "present", "got": None})
    return mm
