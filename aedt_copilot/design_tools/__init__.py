"""Công cụ lẻ trên design bất kỳ (feature 007, contract: design-tools.md).

Mỗi thao tác = một file (registry 002: NAME, ORDER, run + SECTIONS, validate, prepare, check): read, setup, sweep,
airbox, ports, solder_ball; 008 thêm trace / end_check / check (READ_ONLY, chạy qua inspect), cutout (design mới từ
bản copy của board, CUSTOM), cleanup (runner copy / in place), merge (mức workspace, CUSTOM). Mặc định làm trên BẢN COPY <tên>_<thao tác>_<giờ>.aedb (file gốc không đổi);
in_place=True -> backup <tên>_old_<giờ>.aedb rồi sửa file đã cho (MCP cần cờ user_approved_in_place).
"""
import os
import shutil
import time

from ..core.errors import CopilotInputError
from . import _common as C

PACKAGE = __name__


def _read_mod():
    """Module read.py (không dùng 'from . import read': tên dễ trùng hàm của package)."""
    import importlib
    return importlib.import_module(PACKAGE + ".read")


def ops():
    from ..core import registry
    return registry.by_name(registry.load(PACKAGE, ("NAME", "ORDER", "run", "SECTIONS", "validate", "prepare",
                                                    "check")))


def read_design(board, cell="", version=None):
    """Chỉ đọc: snapshot setup / sweep / airbox / port / solder ball."""
    from ..core.config import machine
    from ..core.edb import edb_session
    R = _read_mod()
    b = C.resolve_board(board)
    with edb_session(b, cell or None, True, version or machine()["aedt_version"]) as edb:
        return {"board": b, "snapshot": R.snapshot(edb)}


def _special(mod):
    return getattr(mod, "READ_ONLY", False) or getattr(mod, "CUSTOM", False) or mod.NAME == "read"


def inspect(op, board, cell="", values=None, targets=None, version=None):
    """Thao tác CHỈ ĐỌC (READ_ONLY): mở chỉ đọc, không copy, không file báo cáo."""
    from ..core.config import machine
    from ..core.edb import edb_session
    reg = ops()
    names = [n for n, m in reg.items() if getattr(m, "READ_ONLY", False)]
    if op not in names:
        raise CopilotInputError("op", "one of " + ", ".join(names), op)
    mod = reg[op]
    src = C.resolve_board(board)
    P, targets = mod.validate(values or {}, dict(targets or {}))
    targets["_source"] = src
    lines = []
    with edb_session(src, cell or None, True, version or machine()["aedt_version"]) as edb:
        targets = mod.prepare(edb, P, targets)
        out = mod.run(edb, P, targets, lambda *a: lines.append(" ".join(str(x) for x in a))) or {}
    return {"op": op, "board": src, **out, "log": lines}


def run(op, board, cell="", values=None, targets=None, in_place=False, version=None, log=None):
    from ..core.config import machine
    from ..core.edb import edb_session, open_edb
    R = _read_mod()
    reg = ops()
    if op not in reg or _special(reg[op]):
        raise CopilotInputError("op", "one of " + ", ".join(n for n, m in reg.items() if not _special(m)), op)
    mod = reg[op]
    if not isinstance(in_place, bool):
        raise CopilotInputError("in_place", "true or false", in_place)
    src = C.resolve_board(board)
    P, targets = mod.validate(values or {}, dict(targets or {}))      # mọi lỗi đầu vào trước khi đụng file
    targets["_source"] = src                                         # cleanup: stage1.json cạnh design gốc
    version = version or machine()["aedt_version"]
    lines = []
    log = log or (lambda *a: lines.append(" ".join(str(x) for x in a)))
    t0 = time.time()
    backup = None
    if in_place:
        backup = C.copy_aedb(src, C.backup_name(src))
        work, created = src, False
    else:
        work, created = C.copy_aedb(src, C.copy_name(src, op)), True
    try:
        edb = open_edb(work, cell or None, False, version)
        try:
            targets = mod.prepare(edb, P, targets)                       # refdes / net / setup có trên design
            before = R.snapshot(edb)
            out = mod.run(edb, P, targets, log) or {}
            edb.save()
        finally:
            edb.close()
    except CopilotInputError:
        if created:                                                      # chỉ xoá bản copy do lần gọi này tạo
            shutil.rmtree(work, ignore_errors=True)
        raise
    with edb_session(work, cell or None, True, version) as edb:
        after = R.snapshot(edb)
        mismatches = mod.check(edb, P, targets)
    rep = {"op": op, "source": src, "result": work, "backup": backup, "in_place": in_place,
           "changes": C.changes(before, after), "skipped": out.get("skipped") or [], "created": out.get("created"),
           "mismatches": mismatches, "ok": not mismatches, "seconds": round(time.time() - t0, 1),
           "time": C.now_tag(), "log": lines}
    rep["report"] = C.write_report(rep)
    return rep


def call(op, args):
    """CLI: 'read' -> read_design; READ_ONLY -> inspect; 'cutout' / 'merge' -> module riêng; còn lại -> run()."""
    import importlib
    args = dict(args or {})
    if op == "read":
        return read_design(args.get("board", ""), args.get("cell", ""))
    reg = ops()
    if op in reg and getattr(reg[op], "READ_ONLY", False):
        return inspect(op, args.get("board", ""), args.get("cell", ""), args.get("values"), args.get("targets"))
    if op == "cutout":
        return importlib.import_module(PACKAGE + ".cutout").execute(
            args.get("board", ""), args.get("cell", ""), args.get("values"), args.get("targets"))
    if op == "merge":
        lines = []
        out = importlib.import_module(PACKAGE + ".merge").run(
            args.get("workspace", ""), args.get("designs"), args.get("port"), args.get("out_dir", ""),
            lambda *a: lines.append(" ".join(str(x) for x in a)))
        return {**out, "log": lines}
    return run(op, args.get("board", ""), args.get("cell", ""), args.get("values"), args.get("targets"),
               bool(args.get("in_place", False)))
