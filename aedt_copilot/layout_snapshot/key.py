"""Khoá hợp lệ, thư mục, toán cửa sổ (pure + stat file, feature 023).

Khoá = đường dẫn .aedb + cell + kích thước / mtime của edb.def + schema. KHÔNG dùng edb.def.tmp (EDB chạm file 0 byte
này mỗi lần mở). Board đang mở trong AEDT (.lock) -> từ chối, không bao giờ xoá lock.
"""
import hashlib
import json
import os
import re

from ..core.errors import CopilotInputError
from . import SCHEMA_VERSION

OUTPUT = os.path.join("Ansys AEDT Copilot", "snapshots")


def board_key(aedb, cell):
    d = os.path.join(aedb, "edb.def")
    if not os.path.isfile(d):
        raise CopilotInputError("board", "EDB folder with edb.def", aedb)
    st = os.stat(d)
    return {"aedb": os.path.normcase(os.path.abspath(aedb)), "cell": cell or "", "def_size": st.st_size,
            "def_mtime_ns": st.st_mtime_ns, "schema": SCHEMA_VERSION}


def key_hash(key):
    return hashlib.sha1(json.dumps(key, sort_keys=True).encode("utf-8")).hexdigest()[:8]


def check_board_lock(aedb):
    aedt = aedb[:-5] + ".aedt" if aedb.lower().endswith(".aedb") else aedb + ".aedt"
    locks = [aedt + ".lock"] if os.path.exists(aedt + ".lock") else []
    try:
        locks += [os.path.join(aedb, f) for f in os.listdir(aedb) if f.lower().endswith(".lock")]
    except OSError:
        pass
    if locks:
        raise CopilotInputError("board", "board not open in AEDT (no .lock; the lock is never deleted)", locks[0])


def root(aedb):
    return os.path.join(os.path.dirname(os.path.abspath(aedb)), OUTPUT, os.path.splitext(os.path.basename(aedb))[0])


def _safe(s):
    return re.sub(r'[<>:"/\\|?*;\s]', "_", s or "") or "cell"


def index_dir(aedb, key):
    return os.path.join(root(aedb), f"{_safe(key['cell'])}_{key_hash(key)}")


def window_name(window):
    if window is None:
        return "w_board"
    return "w_" + "_".join(str(int(round(v * 1e6))) for v in window)


def window_dir(aedb, key, window):
    return os.path.join(index_dir(aedb, key), window_name(window))


# ----------------------------------------------------------------------------- window (m)
def window_of(bboxes, margin_m):
    bboxes = [b for b in bboxes if b]
    if not bboxes:
        raise CopilotInputError("nets", "at least one primitive / via of the nets", [])
    if not isinstance(margin_m, (int, float)) or margin_m < 0:
        raise CopilotInputError("margin_mm", ">= 0", margin_m)
    return (min(b[0] for b in bboxes) - margin_m, min(b[1] for b in bboxes) - margin_m,
            max(b[2] for b in bboxes) + margin_m, max(b[3] for b in bboxes) + margin_m)


def contains(outer, inner):
    """outer None = cả board (chứa mọi cửa sổ)."""
    if outer is None:
        return True
    if inner is None:
        return False
    return outer[0] <= inner[0] and outer[1] <= inner[1] and outer[2] >= inner[2] and outer[3] >= inner[3]


def overlap(a, b):
    if a is None or b is None:
        return True
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]
