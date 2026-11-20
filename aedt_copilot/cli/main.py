"""Điểm vào CLI: parse -> tìm AEDT -> gọi hàm xử lý của lệnh."""
import json
import sys

from .commands import COMMANDS
from .parser import build_parser


def main(argv=None):
    a = build_parser().parse_args(argv)
    # Tìm AEDT + đặt ANSYSEM_ROOT### TRƯỚC mọi import pyedb/pyaedt (pyedb đọc env 1 lần lúc import).
    # Lỗi (không thấy AEDT) để dành: lệnh không cần AEDT (status, report...) vẫn chạy; open_edb sẽ báo lại.
    from .. import aedt_env
    try:
        aedt_env.ensure()
    except Exception as ex:
        print(f"[aedt_env] {ex}", file=sys.stderr, flush=True)
    print("[aedt_env] " + json.dumps(aedt_env.info(), ensure_ascii=False), file=sys.stderr, flush=True)
    return COMMANDS[a.cmd](a) or 0
