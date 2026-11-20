"""Phiên EDB dùng chung (contract: core-edb.md). Bọc aedt_env.open_edb (version tường minh, grpc=False).

Module import được khi không có AEDT: pyedb chỉ được nạp bên trong open_edb, SAU khi kiểm tra đầu vào.
"""
import contextlib
import os
import sys

from .errors import CopilotInputError
from .validate import require_text, require_type


def aedb_path(board):
    """.aedb / .aedt / .aedb/edb.def (bỏ nháy, khoảng trắng) -> đường dẫn tuyệt đối của thư mục .aedb có thật."""
    if isinstance(board, os.PathLike):
        board = os.fspath(board)
    if not isinstance(board, str) or not board.strip().strip('"').strip():
        raise CopilotInputError("board", "non-empty path", board)
    b = os.path.abspath(board.strip().strip('"').strip())
    if b.lower().endswith(".aedt"):
        b = b[:-5] + ".aedb"
    if b.lower().endswith("edb.def"):
        b = os.path.dirname(b)
    if not os.path.isdir(b):
        raise CopilotInputError("board", "existing .aedb folder", b)
    return b


def open_edb(board, cell=None, readonly=True, version=None):
    """-> pyedb.Edb đang mở. Người gọi phải close (nên dùng edb_session)."""
    path = aedb_path(board)
    if cell is not None:
        cell = require_text("cell", cell)
    require_type("readonly", readonly, bool)
    if version is not None:
        version = require_text("version", version)
    from ..aedt_env import open_edb as _open             # nạp pyedb SAU khi đặt env
    return _open(path, cell, readonly, version)


@contextlib.contextmanager
def edb_session(board, cell=None, readonly=True, version=None, opener=None):
    """with edb_session(board) as edb: ...  -> luôn edb.close() khi ra khỏi khối (kể cả khi lỗi)."""
    edb = (opener or open_edb)(board, cell, readonly, version)
    try:
        yield edb
    except BaseException:
        try:
            edb.close()
        except Exception as ex:                          # giữ lỗi gốc của thân khối
            print(f"edb_session: close lỗi (bỏ qua): {ex}", file=sys.stderr)
        raise
    else:
        edb.close()
