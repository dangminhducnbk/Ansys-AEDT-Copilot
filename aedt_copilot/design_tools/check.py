"""Thao tác 'check' (CHỈ ĐỌC, feature 008): tự kiểm tra một design - các đầu còn, port = pin tín hiệu của net trên
các đầu, setup / sweep và airbox đúng giá trị mong đợi (template + values). Cùng luật interface_sim.apply.self_check."""
from ..core.errors import CopilotInputError
from . import _common as C
from .end_check import comp_nets
from .trace import text_list

NAME = "check"
ORDER = 3
READ_ONLY = True
SECTIONS = ("setup", "sweep", "airbox", "cutout")
SWEEP_KEYS = ("sweep.start_ghz", "sweep.stop_ghz", "sweep.step_ghz")


def validate(values, targets):
    if values in (None, ""):
        values = {}
    if not isinstance(values, dict):
        raise CopilotInputError("values", "JSON object {key: value}", values)
    given = [k for k in SWEEP_KEYS if k in values]
    if given and len(given) != len(SWEEP_KEYS):
        raise CopilotInputError("values", "all of " + ", ".join(SWEEP_KEYS) + " or none", given)
    merged = dict(values)
    if not given:                                     # không có sweep -> không so start / stop / step
        merged.update({"sweep.start_ghz": 0, "sweep.stop_ghz": 1, "sweep.step_ghz": 0.1})
    P = C.params(merged, SECTIONS)
    targets["sweep_given"] = bool(given)
    targets["ends"] = text_list(targets.get("ends"), "ends")
    if not targets["ends"]:
        raise CopilotInputError("ends", "end component refdes (comma separated)", targets.get("ends"))
    targets["nets"] = text_list(targets.get("nets"), "nets")
    sn = targets.get("setup_name") or ""
    if not isinstance(sn, str):
        raise CopilotInputError("setup_name", "setup name (text)", sn)
    targets["setup_name"] = sn
    return P, targets


def prepare(edb, P, targets):
    return targets


def run(edb, P, targets, log):
    from ..cut_board import cutter
    from ..interface_sim.apply import airbox_mismatches, read_airbox, read_setup, setup_mismatches
    mm = []
    inst = dict(edb.components.instances)
    expected = set()
    for rd in targets["ends"]:
        if rd not in inst:
            mm.append({"item": f"component {rd}", "expected": "present", "got": None})
            continue
        nets = set(comp_nets(edb, P, rd, targets["nets"]))
        for pn, p in inst[rd].pins.items():
            if p.net_name in nets:
                expected.add(cutter.port_name(rd, pn, p))
    have = set(dict(edb.ports))
    if not expected:
        mm.append({"item": "signal pins", "expected": "at least one signal pin on the ends", "got": 0})
    for n in sorted(expected - have):
        mm.append({"item": f"port {n}", "expected": "present", "got": None})
    setups = dict(edb.setups)
    sname = targets["setup_name"] or (next(iter(setups)) if len(setups) == 1 else P["setup"]["name"])
    if sname not in setups:
        mm.append({"item": "setup", "expected": sname, "got": sorted(setups)})
    else:
        sw = list(setups[sname].sweeps)
        wname = P["sweep"]["name"] if P["sweep"]["name"] in sw else (sw[0] if len(sw) == 1 else P["sweep"]["name"])
        if wname not in sw:
            mm.append({"item": "sweep", "expected": wname, "got": sw})
        else:
            got = setup_mismatches(read_setup(setups[sname], wname), P)
            if not targets["sweep_given"]:            # adaptive freq 'auto' = sweep stop -> cũng không so
                auto = str(P["setup"]["adaptive_freq"]).strip().lower() in ("auto", "max", "")
                got = [m for m in got if m["item"] not in SWEEP_KEYS and
                       not (auto and m["item"] == "setup.adaptive_freq")]
            mm += got
    try:
        mm += airbox_mismatches(read_airbox(edb), P)
    except Exception as ex:
        mm.append({"item": "airbox", "expected": "readable", "got": f"unreadable: {ex}"})
    return {"ok": not mm, "mismatches": mm, "ports": len(have), "signal_pins": len(expected),
            "sweep_checked": targets["sweep_given"]}


def check(edb, P, targets):
    return []
