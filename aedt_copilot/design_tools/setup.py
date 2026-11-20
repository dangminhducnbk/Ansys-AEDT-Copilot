"""Thao tác 'setup': tạo / thay HFSS setup (adaptive freq, passes, delta S, arc step ...) + sweep (feature 007)."""
from ..core.errors import CopilotInputError
from ..core.validate import require_text
from . import _common as C

NAME = "setup"
ORDER = 10
SECTIONS = ("setup", "sweep")


def validate(values, targets):
    P = C.params(values, SECTIONS)
    name = targets.get("setup_name") or P["setup"]["name"]
    P["setup"]["name"] = require_text("setup_name", name)
    targets["setup_name"] = P["setup"]["name"]
    return P, targets


def prepare(edb, P, targets):
    return targets


def run(edb, P, targets, log):
    from ..cut_board import cutter
    name = targets["setup_name"]
    st = dict(edb.setups).get(name)
    if st is not None:
        st.delete()                                                    # thay setup cùng tên
        log("  xoá setup cũ:", name)
    cutter.apply_setup(edb, P, log)
    return {}


def check(edb, P, targets):
    from ..interface_sim.apply import read_setup, setup_mismatches
    st = dict(edb.setups).get(targets["setup_name"])
    if st is None:
        return [{"item": "setup", "expected": targets["setup_name"], "got": sorted(dict(edb.setups))}]
    if P["sweep"]["name"] not in list(st.sweeps):
        return [{"item": "sweep", "expected": P["sweep"]["name"], "got": list(st.sweeps)}]
    return setup_mismatches(read_setup(st, P["sweep"]["name"]), P)


def require_setup(edb, name):
    names = sorted(dict(edb.setups))
    if name not in names:
        raise CopilotInputError("setup_name", "existing setup: " + ", ".join(names) if names else
                                "existing setup (design has none: use design_setup)", name)
    return dict(edb.setups)[name]
