"""Thao tác 'solder_ball': đặt solder ball cho linh kiện đã chọn (luật nhóm: đường kính = tỉ lệ x cạnh ngắn pad tín
hiệu, chiều cao, hình dạng) - đơn vị mm ghi đúng (feature 007)."""
from ..core.errors import CopilotInputError
from . import _common as C
from .ports import _list

NAME = "solder_ball"
ORDER = 50
SECTIONS = ("solder_ball",)


def validate(values, targets):
    P = C.params(values, SECTIONS)
    targets["refdes"] = _list(targets.get("refdes"), "refdes")
    if not targets["refdes"]:
        raise CopilotInputError("refdes", "at least one component refdes", targets.get("refdes"))
    return P, targets


def prepare(edb, P, targets):
    inst = dict(edb.components.instances)
    for rd in targets["refdes"]:
        if rd not in inst:
            raise CopilotInputError("refdes", "component on the design, closest: " +
                                    ", ".join(C.closest(rd, list(inst))), rd)
    return targets


def run(edb, P, targets, log):
    from ..cut_board import cutter
    refs = set(P["cutout"]["reference_nets"])
    inst = dict(edb.components.instances)
    created, skipped = [], []
    for rd in targets["refdes"]:
        nets = {p.net_name for p in inst[rd].pins.values() if p.net_name and p.net_name not in refs}
        if not nets:
            skipped.append({"item": rd, "reason": "no signal pins (only reference nets)"})
            continue
        try:
            d = cutter.set_solder_ball(edb, P, rd, nets, None, log)
        except Exception as ex:
            d = None
            log(f"  {rd}: {ex}")
        if d is None:
            skipped.append({"item": rd, "reason": "solder ball could not be set (see log)"})
        else:
            created.append(rd)
    targets["done"] = created
    return {"created": created, "skipped": skipped}


def check(edb, P, targets):
    from .read import solder_balls
    exp_h = f"{round(float(P['solder_ball']['height_mm']), 4):g}mm"
    got = solder_balls(edb, targets.get("done") or [])
    mm = []
    for rd in targets.get("done") or []:
        g = got.get(rd)
        if not g or g.get("height") != exp_h:
            mm.append({"item": f"{rd} solder ball height", "expected": exp_h, "got": (g or {}).get("height")})
    return mm
