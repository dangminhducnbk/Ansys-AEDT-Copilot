"""Thao tác 'merge' (feature 008, mức workspace): gộp design bất kỳ (.aedb) vào workspace .aedt của người dùng.

cut_board.merge.merge_designs: backup workspace trước, mỗi design 1 design mới, trùng tên -> _v2, không ghi đè.
MCP cần cờ user_approved_merge. Không qua runner copy: gọi run(workspace, designs, port, out_dir).
"""
import os

from ..core.errors import CopilotInputError
from ..core.validate import require_int
from . import _common as C

NAME = "merge"
ORDER = 90
READ_ONLY = False
CUSTOM = True
SECTIONS = ()


def designs_map(designs):
    """{tên: .aedb} hoặc 'a.aedb, b.aedb' (tên = stem) -> {tên: .aedb đã kiểm tra}."""
    from ..interface_sim.request import check_name
    if isinstance(designs, str):
        items = [x.strip() for x in designs.split(",") if x.strip()]
        designs = {os.path.splitext(os.path.basename(p.rstrip("\\/")))[0]: p for p in items}
    if not isinstance(designs, dict) or not designs:
        raise CopilotInputError("designs", "{name: .aedb} or comma separated .aedb paths", designs)
    out, taken = {}, []
    for name, path in designs.items():
        n = check_name(name, taken)
        taken.append(n)
        if not isinstance(path, str) or not path.strip():
            raise CopilotInputError("designs", ".aedb path", path)
        out[n] = C.resolve_board(path)                              # có thật, không .lock
    return out


def validate(values, targets):
    return C.params(values, SECTIONS), targets


def prepare(edb, P, targets):
    return targets


def check(edb, P, targets):
    return []


def run(workspace, designs, port=None, out_dir="", log=print):
    from ..cut_board.merge import merge_designs
    if not isinstance(workspace, str) or not workspace.lower().endswith(".aedt") or not os.path.isfile(workspace):
        raise CopilotInputError("workspace", "existing .aedt file", workspace)
    workspace = os.path.abspath(workspace)
    if port in (None, 0, "", "0"):
        port = None
    else:
        port = require_int("port", int(port) if str(port).isdigit() else port, 1, 65535)
    if os.path.exists(workspace + ".lock") and not port:
        raise CopilotInputError("workspace", "closed in AEDT (no .lock) or the port of the AEDT session holding it",
                                workspace + ".lock")
    src = designs_map(designs)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    else:                                                       # 024: thư mục mới nguyên tử, _2 khi trùng giây
        out_dir = C.claim_dir(os.path.join(os.path.dirname(workspace), "Ansys AEDT Copilot", "design_tools",
                                           f"merge_{C.now_tag()}"))
    res = merge_designs(workspace, src, out_dir, port, log)
    res["out_dir"] = out_dir
    return res
