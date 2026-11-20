"""Phần dùng chung của công cụ lẻ (feature 007): kiểm tra đầu vào, bản copy / backup, thông số, báo cáo."""
import datetime as dt
import difflib
import json
import os
import re
import shutil

from ..core.edb import aedb_path
from ..core.errors import CopilotInputError
from ..core.unique import claim_dir

REPORT_SUFFIX = ".design_tools.md"


def now_tag():
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def closest(name, pool, n=5):
    return difflib.get_close_matches(str(name), [str(x) for x in pool], n=n, cutoff=0.3) or sorted(pool)[:n]


def resolve_board(board):
    """-> đường dẫn .aedb có thật; design đang mở trong AEDT (.lock) -> lỗi (không bao giờ xoá lock)."""
    b = aedb_path(board)
    aedt = b[:-5] + ".aedt"
    locks = [aedt + ".lock"] if os.path.exists(aedt + ".lock") else []
    locks += [os.path.join(b, f) for f in os.listdir(b) if f.lower().endswith(".lock")]
    if locks:
        raise CopilotInputError("board", "design not open in AEDT (no .lock)", locks[0])
    return b



OPS_SUFFIX = re.compile(r"(_(?:read|setup|sweep|airbox|ports|solder_ball|cleanup|old)_\d{8}_\d{6}(?:_\d+)?)+$")


def base_stem(path):
    """Tên gốc: bỏ các đuôi _<thao tác>_<giờ> của lần gọi trước (gọi nối tiếp không làm tên dài thêm)."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return OPS_SUFFIX.sub("", stem) or stem


def copy_name(src, op):
    d, stem = os.path.dirname(src), base_stem(src)
    return claim_dir(os.path.join(d, f"{stem}_{op}_{now_tag()}.aedb"))       # 024: giữ chỗ nguyên tử


def backup_name(src):
    d, stem = os.path.dirname(src), base_stem(src)
    return claim_dir(os.path.join(d, f"{stem}_old_{now_tag()}.aedb"))


def copy_aedb(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("*.lock"), dirs_exist_ok=True)  # dst = chỗ đã giữ
    return dst


def params(values, sections):
    """values {key: v} (chỉ khoá của các section của thao tác) -> P (template + values), cùng luật build_params."""
    from ..cut_board import config
    if values in (None, ""):
        values = {}
    if not isinstance(values, dict):
        raise CopilotInputError("values", "JSON object {key: value}", values)
    values = dict(values)
    bad = [k for k in values if str(k).split(".", 1)[0] not in sections]
    if bad:
        raise CopilotInputError("values", "keys of " + ", ".join(f"{s}.*" for s in sections) if sections
                                else "no values for this operation", bad)
    merged = dict(values)
    if "sweep" not in sections:                                  # sweep bắt buộc chỉ khi thao tác dùng sweep
        merged.update({"sweep.start_ghz": 0, "sweep.stop_ghz": 1, "sweep.step_ghz": 0.1})
    P, errors = config.build_params(merged)
    errors = [e for e in errors if e.split(":", 1)[0].split(" ", 1)[0].split(".", 1)[0] in sections]
    if errors:
        raise CopilotInputError("values", "valid settings", errors)
    return P


def flatten(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "/"))
        else:
            out[key] = v
    return out


def changes(before, after):
    """Khác biệt 2 snapshot -> [{item, old, new}] (theo đường dẫn khoá)."""
    a, b = flatten(before), flatten(after)
    return [{"item": k, "old": a.get(k), "new": b.get(k)} for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def report_md(rep):
    def tbl(head, rows):
        if not rows:
            return "_none_"
        return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                         ["| " + " | ".join(str(x) for x in r) + " |" for r in rows])
    return "\n".join([
        f"## {rep['op']} - {rep['time']} - {'OK' if rep['ok'] else 'CHECK MISMATCH'}", "",
        f"- source: `{rep['source']}`", f"- result: `{rep['result']}`" + (" (in place)" if rep["in_place"] else ""),
        f"- backup: `{rep['backup']}`" if rep.get("backup") else "- backup: - (copy mode, original untouched)", "",
        "### Changes", tbl(["Item", "Old", "New"], [[c["item"], c["old"], c["new"]] for c in rep["changes"]]), "",
        "### Skipped", tbl(["Item", "Reason"], [[s["item"], s["reason"]] for s in rep["skipped"]]), "",
        "### Read-back", tbl(["Item", "Expected", "Got"], [[m["item"], m["expected"], m["got"]] for m in rep["mismatches"]])
        if rep["mismatches"] else "All values read back equal.", ""])


def write_report(rep):
    p = rep["result"] + REPORT_SUFFIX
    prev = rep["source"] + REPORT_SUFFIX
    if rep["result"] != rep["source"] and os.path.isfile(prev) and not os.path.exists(p):
        shutil.copyfile(prev, p)                                 # gọi nối tiếp: báo cáo cộng dồn
    with open(p, "a", encoding="utf-8") as f:
        f.write(report_md(rep) + "\n")
    with open(rep["result"] + ".design_tools.json", "a", encoding="utf-8") as f:
        f.write(json.dumps(rep, ensure_ascii=False, default=str) + "\n")
    return p
