"""Thao tác 'end_check' (CHỈ ĐỌC, feature 008): đo các đầu của một design (loại, pad, GND gần pin tín hiệu,
solder ball, via-in-pad, trường hợp lạ). Cùng luật interface_sim.ends (isim_check_ends)."""
import os

from ..core.errors import CopilotInputError
from . import _common as C
from .trace import text_list

NAME = "end_check"
ORDER = 2
READ_ONLY = True
SECTIONS = ("cutout", "cleanup", "interface_sim")


def validate(values, targets):
    P = C.params(values, SECTIONS)
    targets["refdes"] = text_list(targets.get("refdes"), "refdes")
    if not targets["refdes"]:
        raise CopilotInputError("refdes", "at least one component refdes", targets.get("refdes"))
    targets["nets"] = text_list(targets.get("nets"), "nets")
    return P, targets


def comp_nets(edb, P, rd, nets):
    """Net tín hiệu của linh kiện: nets đã cho (tên hoặc mẫu *, có trên pin) hoặc mọi net không phải reference / nguồn."""
    import fnmatch
    pin_nets = {p.net_name for p in edb.components.instances[rd].pins.values() if p.net_name}
    if nets:
        return sorted(n for n in pin_nets if any(n == x or fnmatch.fnmatchcase(n, x) for x in nets))
    try:
        power = set(edb.nets.power.keys())
    except Exception:
        power = set()
    return sorted(pin_nets - set(P["cutout"]["reference_nets"]) - power)


def prepare(edb, P, targets):
    inst = dict(edb.components.instances)
    per = {}
    for rd in targets["refdes"]:
        if rd not in inst:
            raise CopilotInputError("refdes", "component on the design, closest: " +
                                    ", ".join(C.closest(rd, list(inst))), rd)
        per[rd] = comp_nets(edb, P, rd, targets["nets"])
        if not per[rd]:
            raise CopilotInputError("nets", f"signal nets on {rd} pins", targets["nets"] or "(none found)")
    targets["per_refdes"] = per
    return targets


def run(edb, P, targets, log):
    from ..cut_board.cutter import is_bga_or_th
    from ..interface_sim import ends as E
    from ..core.config import ROOT
    th = E.thresholds(P)
    refs = set(P["cutout"]["reference_nets"])
    out = {}
    name = os.path.splitext(os.path.basename(targets.get("_source") or "design"))[0]
    img = os.path.join(ROOT, ".tasks", f"end_check_{name}")                 # 015: ảnh ở thư mục tool (chỉ đọc design)
    s1 = _stage1_beside(targets.get("_source"))
    for rd, nets in targets["per_refdes"].items():
        bga = is_bga_or_th(edb.components.instances[rd], set(nets))
        out[rd] = E._measure(edb, rd, set(nets), refs, bga, th, P=P, image_dir=img, keep_pad=_keep_pad(s1, rd))
    if s1 and img:                                                               # 022: luật GND ở 2 đầu (stage1.json)
        from ..cut_board import end_gnd as EG
        imgs = EG.images(s1, img)
        for rd in out:
            if rd in (s1.get("ends") or []):
                out[rd]["end_gnd"] = dict(EG.end_entry(s1, rd), image=imgs.get(rd))
    res = {"ends": out, "thresholds": th, "ends_md": E.ends_md(name, out),
           "unusual": {rd: [u["rule"] for u in e["unusual"]] for rd, e in out.items() if e["unusual"]},
           "default_handling": E.defaults_of(out)}                               # 012: đầu connector
    if any(e.get("end_gnd") for e in out.values()):
        res["end_gnd"] = {rd: e["end_gnd"] for rd, e in out.items() if e.get("end_gnd")}
    if E.gnd_questions(out):
        res["gnd_questions"] = E.gnd_questions(out)
    return res


DESIGN_KEEP_PAD = "applied by interface simulation only (isim_apply); no design tool re-cuts with an extended extent"


def _stage1_beside(source):
    """019: stage1.json cạnh design (design_cutout / isim stage1) -> dict hoặc None."""
    import json
    if not source:
        return None
    p = os.path.join(os.path.dirname(os.path.abspath(source)), "stage1.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _keep_pad(s1, rd):
    """019: có số liệu pad (stage1.json) -> báo cho người dùng nhưng KHÔNG đưa thành lựa chọn ở design tool."""
    if not s1 or "gnd_pads_outside" not in s1:
        return None
    from ..cut_board import gnd_decision as GD
    e = GD.keep_pad_entry((s1["gnd_pads_outside"] or {}).get(rd), s1.get("extent_pts_mm"))
    if e.get("offered"):
        e.update(offered=False, reason=DESIGN_KEEP_PAD)
    return e


def check(edb, P, targets):
    return []
