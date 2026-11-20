"""Bước 2a: cắt interface (cutter.cut_stage) trên BẢN COPY của board (contract: isim-cut.md).

Chạy trong tiến trình riêng (CLI isim op=cut). Board của người dùng không bao giờ được mở.
"""
import datetime as dt
import os
import shutil

from ..core.errors import CopilotInputError
from ..core.unique import move_aside
from . import request as R


class FileLog:
    """Log ra file + giữ thời gian từng bước (giống cutter.Log)."""

    def __init__(self, path):
        from ..cut_board.cutter import Log
        self.f = open(path, "a", encoding="utf-8")
        self.log = Log(lambda s: (self.f.write(s + "\n"), self.f.flush()))

    def close(self):
        self.f.close()


def _same_copy(src, dst):
    a, b = os.path.join(src, "edb.def"), os.path.join(dst, "edb.def")
    if not (os.path.exists(a) and os.path.exists(b)):
        return False
    sa, sb = os.stat(a), os.stat(b)
    return sa.st_size == sb.st_size and abs(sa.st_mtime - sb.st_mtime) < 2


def copy_source(board, iface_dir):
    """board .aedb -> <iface>/_src/<tên>.aedb (bỏ qua nếu bản copy giống: cùng size + mtime edb.def)."""
    dst = os.path.join(iface_dir, "_src", os.path.basename(board))
    if _same_copy(board, dst):
        return dst, False
    if os.path.exists(dst):
        move_aside(dst, dst[:-5] + "_old_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".aedb")
    shutil.copytree(board, dst, ignore=shutil.ignore_patterns("*.lock"))
    return dst, True


def channel(name, content):
    return {"name": name, "comp_a": content["comp_a"], "comp_b": content["comp_b"], "nets": list(content["nets"]),
            "series": {rd: dict(v) for rd, v in (content.get("series") or {}).items()}}


def params_for(content, values=None):
    """P = template + structural (+ values). Lỗi sweep bỏ qua khi chưa có values (cut_stage không dùng sweep)."""
    from ..cut_board import config
    vals = dict(content.get("structural") or {})
    vals.update(values or {})
    P, errors = config.build_params(vals)
    if values is None:
        errors = [e for e in errors if not e.startswith("sweep")]
    return P, errors


def cut_design(src, dst, ch, P, cell, version, log, keep_pads=None, end_factors=None):
    """Mở bản copy board (src), cắt channel ch ra dst (create_new), lưu, đóng. -> stage1 JSON (+ aedb, cell, seconds).
    cell: cell của board ('' = cell đang mở). keep_pads (019): {refdes} giữ pad GND (mở rộng cutout)."""
    from ..core.edb import open_edb
    from ..cut_board import cutter
    nets, ends, keep, refs = cutter.channel_sets(ch, P)
    with log.step("open"):
        edb = open_edb(src, cell or None, False, version)
    try:
        cell = cell or edb.active_cell.GetName()
        stage1 = cutter.cut_stage(edb, ch, P, cell, dst, "create_new", log, nets, ends, keep, refs,
                                  keep_pads=keep_pads, end_factors=end_factors)
        with log.step("save"):
            edb.save()
    finally:
        try:
            edb.close()
        except Exception as ex:
            log("  edb.close lỗi:", ex)
    s1 = cutter.stage1_to_json(stage1)
    s1.update(aedb=dst, cell=ch["name"], seconds=log.times)
    return s1


def run(request_id, name, version=None):
    from ..core.config import machine
    from ..cut_board import cutter
    req = R.load(request_id)
    rid = req["request_id"]
    st = R.get_state(rid, name)
    R.require_step(st, "content_agreed")
    c = st["content"]
    from . import review as RVW
    RVW.require(rid, name, c, for_cut=True)                             # 035: kỹ sư đã đồng ý sau khi đọc review
    P, errors = params_for(c)
    if errors:
        raise CopilotInputError("structural", "valid cut settings", errors)
    version = version or machine()["aedt_version"]
    with R.busy(rid, name) as d:
        fl = FileLog(os.path.join(d, "cut.log"))
        log = fl.log
        dst = os.path.join(d, "stage1", name + ".aedb")
        created = False
        try:
            if os.path.exists(os.path.dirname(dst)):
                move_aside(os.path.dirname(dst), os.path.dirname(dst) + "_old_" +
                           dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(os.path.dirname(dst))
            with log.step("copy_source"):
                src, copied = copy_source(req["board"], d)
                log(f"  source copy {src} ({'copied' if copied else 'reused'})")
            ch = channel(name, c)
            created = True
            ef = c.get("end_factors") or {}                             # 022 US5: hệ số tay từng đầu
            s1 = cut_design(src, dst, ch, P, req.get("cell") or "", version, log, end_factors=ef)
            from . import cut_preview as CP                             # 022 SC-005: extent cut = extent preview
            s1["preview_check"] = CP.compare(rid, name, CP.settings_key(P, ef, s1["nets"]), s1["extent_pts_mm"])
            R.wjson(os.path.join(d, "stage1.json"), s1)
            R.set_state(rid, name, "cut done", stage1={"aedb": dst, "bga_ends": s1["bga_ends"], "nets": s1["nets"],
                                                        "times": log.times})
            R.advance(rid, name, "cut")
            return {"name": name, "step": "cut", "stage1_aedb": dst, "nets": s1["nets"], "bga_ends": s1["bga_ends"],
                    "preview_check": s1["preview_check"],
                    "end_gnd": {rd: {k: e.get(k) for k in ("result", "factor", "added_mm2")}
                                for rd, e in (s1.get("end_gnd") or {}).get("ends", {}).items()},
                    "times": log.times, "log": os.path.join(d, "cut.log"), "next": "isim_check_ends, then " + R.NEXT_SETTINGS}
        except BaseException as ex:
            if created:
                cutter.remove_partial(dst, log)
            R.fail(rid, name, f"cut: {type(ex).__name__}: {ex}")
            raise
        finally:
            fl.close()
