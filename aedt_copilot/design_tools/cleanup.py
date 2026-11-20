"""Thao tác 'cleanup' (feature 008): dọn GND của một design đã cắt (cutter.cleanup_gnd, không có id được bảo vệ).

Mặc định làm trên BẢN COPY (runner 007); in_place cần cờ. nets / bga_ends / extent_area lấy từ stage1.json cạnh
design (do design_cutout ghi), không có thì tính (research R2): nets = net tín hiệu chung của các đầu, bga_ends =
đầu BGA / xuyên lỗ, extent_area = diện tích GND lớn nhất trên một lớp.
"""
import json
import os

from ..core.errors import CopilotInputError
from . import _common as C
from .trace import text_list

NAME = "cleanup"
ORDER = 6
READ_ONLY = False
SECTIONS = ("cutout", "cleanup")


def validate(values, targets):
    P = C.params(values, SECTIONS)
    targets["ends"] = text_list(targets.get("ends"), "ends")
    if not targets["ends"]:
        raise CopilotInputError("ends", "end component refdes (comma separated)", targets.get("ends"))
    targets["nets"] = text_list(targets.get("nets"), "nets")
    return P, targets


def stage1_for(source):
    """stage1.json cạnh design (cùng thư mục) -> dict, hoặc None."""
    p = os.path.join(os.path.dirname(source or ""), "stage1.json")
    if not source or not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def gnd_area_by_layer(edb, refs):
    area = {}
    for p in edb.modeler.primitives:
        if p.net_name in refs and type(p).__name__ not in ("EdbPath", "Path"):
            area[p.layer_name] = area.get(p.layer_name, 0) + p.area()
    return area


def prepare(edb, P, targets):
    from ..cut_board.cutter import is_bga_or_th
    inst = dict(edb.components.instances)
    for rd in targets["ends"]:
        if rd not in inst:
            raise CopilotInputError("ends", "component on the design, closest: " +
                                    ", ".join(C.closest(rd, list(inst))), rd)
    refs = set(P["cutout"]["reference_nets"])
    s1 = stage1_for(targets.get("_source"))
    if s1 and set(targets["ends"]) <= set(s1.get("ends") or []):
        nets = targets["nets"] or list(s1["nets"])
        targets.update(bga_ends=[rd for rd in s1["bga_ends"] if rd in targets["ends"]],
                       extent_area=float(s1["extent_area_m2"]), defaults_from="stage1.json",
                       enlarged_ends=[rd for rd, e in ((s1.get("end_gnd") or {}).get("ends") or {}).items()
                                      if e.get("result") in ("enlarged", "manual") and rd in targets["ends"]])
        from ..cut_board import gnd_pins as GP                         # 021: pin GND không bao giờ xoá
        targets["smd_protect"] = {rd: sorted(GP.protected_names(s1, rd)) for rd in targets["ends"]}
    else:
        if targets["nets"]:
            nets = targets["nets"]
        else:
            try:
                power = set(edb.nets.power.keys())
            except Exception:
                power = set()
            sets = [{p.net_name for p in inst[rd].pins.values() if p.net_name} for rd in targets["ends"]]
            nets = sorted(set.intersection(*sets) - refs - power)
        area = gnd_area_by_layer(edb, refs)
        targets.update(bga_ends=[rd for rd in targets["ends"] if is_bga_or_th(inst[rd], set(nets))],
                       extent_area=max(area.values(), default=0.0), defaults_from="computed (largest GND layer)")
    have = set(edb.nets.netlist)
    bad = [n for n in nets if n not in have]
    if bad or not nets:
        raise CopilotInputError("nets", "signal nets on the design, closest: " +
                                ", ".join(C.closest((bad or ["?"])[0], sorted(have))), bad or nets)
    if targets["extent_area"] <= 0:
        raise CopilotInputError("design", "design with GND copper", targets.get("_source"))
    targets["net_list"] = sorted(nets)
    targets["gnd_before"] = gnd_area_by_layer(edb, refs)
    return targets


def run(edb, P, targets, log):
    from ..cut_board import cutter
    refs = set(P["cutout"]["reference_nets"])
    n0 = {}
    for p in edb.modeler.primitives:
        if p.net_name in refs:
            n0[p.layer_name] = n0.get(p.layer_name, 0) + 1
    protect = set()
    for rd in targets.get("enlarged_ends") or []:                     # 022: via GND trong pad GND giữ nhờ vùng đầu
        protect |= cutter.vias_in_gnd_pads(edb, P, rd)
    smd = [rd for rd in targets["ends"] if rd not in targets["bga_ends"]]   # 021: đầu SMD / connector
    reports = []
    cutter.cleanup_gnd(edb, P, set(targets["net_list"]), targets["ends"], targets["bga_ends"],
                       targets["extent_area"], protect, set(), log, smd_ends=smd,
                       smd_protect=targets.get("smd_protect") or {}, smd_reports=reports)
    n1 = {}
    for p in edb.modeler.primitives:
        if p.net_name in refs:
            n1[p.layer_name] = n1.get(p.layer_name, 0) + 1
    removed = {lay: n0[lay] - n1.get(lay, 0) for lay in sorted(n0) if n0[lay] - n1.get(lay, 0)}
    log(f"  cleanup defaults from {targets['defaults_from']}; removed GND primitives per layer: {removed}")
    return {"created": {"removed_per_layer": removed, "defaults_from": targets["defaults_from"],
                        "protected_pad_vias": len(protect), "gnd_pin_cleanup": reports,
                        "bga_ends": targets["bga_ends"], "nets": targets["net_list"]}}


def check(edb, P, targets):
    """GND mỗi lớp sau <= trước; net tín hiệu + linh kiện đầu còn đủ."""
    refs = set(P["cutout"]["reference_nets"])
    mm = []
    after = gnd_area_by_layer(edb, refs)
    for lay, a in after.items():
        if a > targets["gnd_before"].get(lay, 0) * (1 + 1e-6) + 1e-15:
            mm.append({"item": f"GND area {lay}", "expected": f"<= {targets['gnd_before'].get(lay, 0)}", "got": a})
    have = set(edb.nets.netlist)
    for n in targets["net_list"]:
        if n not in have:
            mm.append({"item": f"net {n}", "expected": "present", "got": None})
    inst = dict(edb.components.instances)
    for rd in targets["ends"]:
        if rd not in inst:
            mm.append({"item": f"component {rd}", "expected": "present", "got": None})
    return mm
