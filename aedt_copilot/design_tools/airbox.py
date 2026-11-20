"""Thao tác 'airbox': đặt extent / padding / open region / operating freq (feature 007)."""
from . import _common as C

NAME = "airbox"
ORDER = 30
SECTIONS = ("airbox",)


def validate(values, targets):
    return C.params(values, SECTIONS), targets


def prepare(edb, P, targets):
    return targets


def run(edb, P, targets, log):
    from ..cut_board import cutter
    cutter.apply_airbox(edb, P)
    return {}


def check(edb, P, targets):
    from ..interface_sim.apply import airbox_mismatches, read_airbox
    return airbox_mismatches(read_airbox(edb), P)
