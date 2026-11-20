"""Thao tác 'sweep': thay sweep của một setup có sẵn (start / stop / step, loại, interpolation) (feature 007)."""
from ..core.validate import require_text
from . import _common as C
from .setup import require_setup

NAME = "sweep"
ORDER = 20
SECTIONS = ("sweep",)


def validate(values, targets):
    P = C.params(values, SECTIONS)
    if targets.get("setup_name"):
        targets["setup_name"] = require_text("setup_name", targets["setup_name"])
    return P, targets


def prepare(edb, P, targets):
    names = sorted(dict(edb.setups))
    targets["setup_name"] = targets.get("setup_name") or (names[0] if len(names) == 1 else P["setup"]["name"])
    require_setup(edb, targets["setup_name"])
    return targets


def run(edb, P, targets, log):
    from ..cut_board import cutter
    cutter.apply_sweep(dict(edb.setups)[targets["setup_name"]], P, log)
    return {}


def check(edb, P, targets):
    from ..interface_sim.apply import read_setup, setup_mismatches
    st = dict(edb.setups)[targets["setup_name"]]
    if P["sweep"]["name"] not in list(st.sweeps):
        return [{"item": "sweep", "expected": P["sweep"]["name"], "got": list(st.sweeps)}]
    return [m for m in setup_mismatches(read_setup(st, P["sweep"]["name"]), P) if m["item"].startswith("sweep.")]
