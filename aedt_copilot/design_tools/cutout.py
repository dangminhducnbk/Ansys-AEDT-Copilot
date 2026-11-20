"""Thao tác 'cutout' (feature 008): cắt một channel từ BẢN COPY của board thành design MỚI.

Board copy 1 lần vào <thư mục board>/Ansys AEDT Copilot/design_tools/_src/ (dùng lại khi cùng size + mtime), cắt
(cutter.cut_stage create_new) ra design_tools/<tên>_cutout_<giờ>/<tên>.aedb + stage1.json bên cạnh (design_cleanup đọc).
Board đã cho không bao giờ được mở ghi. Lỗi -> xoá thư mục kết quả chỉ khi lần gọi này tạo ra nó.
"""
import json
import os
import shutil
import time

from ..core.errors import CopilotInputError
from . import _common as C
from .trace import text_list

NAME = "cutout"
ORDER = 5
READ_ONLY = False
CUSTOM = True                     # không qua runner copy / in place: tự tạo design mới
SECTIONS = ("cutout", "series")
OUTPUT = os.path.join("Ansys AEDT Copilot", "design_tools")     # 2.0.0 (020); trước đó .../kitchen (không đụng)


def output_dir(board):
    return os.path.join(os.path.dirname(board), OUTPUT)


def validate(values, targets):
    from ..interface_sim.request import check_name
    P = C.params(values, SECTIONS)
    for k in ("comp_a", "comp_b"):
        v = targets.get(k)
        if not isinstance(v, str) or not v.strip():
            raise CopilotInputError(k, "component refdes", v)
        targets[k] = v.strip()
    if targets["comp_a"] == targets["comp_b"]:
        raise CopilotInputError("comp_b", "a component other than comp_a", targets["comp_b"])
    targets["nets"] = text_list(targets.get("nets"), "nets")
    if not targets["nets"]:
        raise CopilotInputError("nets", "net names or patterns (required)", targets.get("nets"))
    targets["series"] = text_list(targets.get("series"), "series")
    name = targets.get("name") or ""
    if name:
        check_name(name)
    targets["name"] = name
    return P, targets


def prepare(edb, P, targets):
    """Trên bản copy: linh kiện có thật, mở rộng mẫu net, R/C/L nối tiếp -> net của chúng, tên tự sinh."""
    from ..cut_board.naming import default_name
    from ..interface_sim.content import _expand_nets
    inst = dict(edb.components.instances)
    for k in ("comp_a", "comp_b"):
        if targets[k] not in inst:
            raise CopilotInputError(k, "component on the board, closest: " +
                                    ", ".join(C.closest(targets[k], list(inst))), targets[k])
    netlist = list(edb.nets.netlist)
    found, missing = _expand_nets(targets["nets"], netlist)
    if missing:
        raise CopilotInputError("nets", "nets on the board, closest to " + missing[0] + ": " +
                                ", ".join(C.closest(missing[0], netlist)), missing)
    refs = set(P["cutout"]["reference_nets"])
    series = {}
    for rd in targets["series"]:
        if rd not in inst:
            raise CopilotInputError("series", "component on the board, closest: " +
                                    ", ".join(C.closest(rd, list(inst))), rd)
        series[rd] = {"nets": sorted({p.net_name for p in inst[rd].pins.values() if p.net_name} - refs)}
    targets["net_list"] = sorted(found)
    targets["series_map"] = series
    targets["name"] = targets["name"] or default_name(targets["comp_a"], targets["comp_b"], targets["net_list"])
    return targets


def run(edb, P, targets, log):
    """Cắt trên edb (bản copy, mở ghi) ra targets['dst']. Trả stage1 (dict)."""
    from ..cut_board import cutter
    ch = {"name": targets["name"], "comp_a": targets["comp_a"], "comp_b": targets["comp_b"],
          "nets": targets["net_list"], "series": targets["series_map"]}
    nets, ends, keep, refs = cutter.channel_sets(ch, P)
    stage1 = cutter.cut_stage(edb, ch, P, targets["cell"], targets["dst"], "create_new", log, nets, ends, keep, refs)
    edb.save()
    return stage1


def check(edb, P, targets):
    """Design mới: 2 đầu + mọi net còn."""
    mm = []
    inst = dict(edb.components.instances)
    for rd in (targets["comp_a"], targets["comp_b"]):
        if rd not in inst:
            mm.append({"item": f"component {rd}", "expected": "present", "got": None})
    have = set(edb.nets.netlist)
    for n in targets["net_list"]:
        if n not in have:
            mm.append({"item": f"net {n}", "expected": "present", "got": None})
    return mm


def execute(board, cell="", values=None, targets=None, version=None, log=None):
    from ..core.config import machine
    from ..core.edb import edb_session, open_edb
    from ..cut_board import cutter
    from ..interface_sim.cut import copy_source
    src = C.resolve_board(board)
    P, targets = validate(values or {}, dict(targets or {}))           # lỗi đầu vào trước khi đụng file
    version = version or machine()["aedt_version"]
    lines = []
    clog = cutter.Log(log or (lambda s: lines.append(s)))
    t0 = time.time()
    kdir = output_dir(src)
    os.makedirs(kdir, exist_ok=True)
    with clog.step("copy_source"):
        copy, copied = copy_source(src, kdir)
        clog(f"  source copy {copy} ({'copied' if copied else 'reused'})")
    out_dir = None
    try:
        edb = open_edb(copy, cell or None, False, version)
        try:
            targets["cell"] = cell or edb.active_cell.GetName()
            targets = prepare(edb, P, targets)
            out_dir = C.claim_dir(os.path.join(kdir, f"{targets['name']}_cutout_{C.now_tag()}"))  # 024
            targets["dst"] = os.path.join(out_dir, targets["name"] + ".aedb")
            stage1 = run(edb, P, targets, clog)
        finally:
            try:
                edb.close()
            except Exception as ex:
                clog("  edb.close lỗi:", ex)
    except BaseException:
        if out_dir and os.path.isdir(out_dir):                          # chỉ xoá thư mục do lần gọi này tạo
            shutil.rmtree(out_dir, ignore_errors=True)
        raise
    dst = targets["dst"]
    s1 = cutter.stage1_to_json(stage1)
    s1.update(aedb=dst, cell=targets["name"], source=src, source_copy=copy, seconds=clog.times)
    s1_path = os.path.join(out_dir, "stage1.json")
    with open(s1_path, "w", encoding="utf-8") as f:
        json.dump(s1, f, ensure_ascii=False, indent=1, default=str)
    with edb_session(dst, targets["name"], True, version) as edb:
        mismatches = check(edb, P, targets)
    rep = {"op": NAME, "source": src, "result": dst, "backup": None, "in_place": False,
           "changes": [{"item": "design", "old": None, "new": targets["name"]}],
           "skipped": [], "created": {"design": targets["name"], "nets": s1["nets"], "ends": s1["ends"],
                                      "bga_ends": s1["bga_ends"],
                                      "end_gnd": {rd: {"result": e.get("result"), "factor": e.get("factor"),
                                                       "gnd_pins_on_board": e.get("gnd_pins_on_board")}
                                                  for rd, e in ((s1.get("end_gnd") or {}).get("ends") or {}).items()}},
           "mismatches": mismatches, "ok": not mismatches, "seconds": round(time.time() - t0, 1),
           "time": C.now_tag(), "log": lines, "stage1": s1_path, "nets": s1["nets"], "ends": s1["ends"],
           "bga_ends": s1["bga_ends"], "name": targets["name"]}
    rep["report"] = C.write_report(rep)
    return rep
