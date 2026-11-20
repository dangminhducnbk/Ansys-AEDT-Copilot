"""python -m aedt_copilot <lệnh> ... (dùng được không cần Claude). Danh sách lệnh: aedt_copilot/cli/parser.py."""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from .cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
