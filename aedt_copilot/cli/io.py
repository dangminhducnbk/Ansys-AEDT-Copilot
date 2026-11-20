"""In JSON, đọc --args / --args-file, lỗi đầu vào -> JSON (dùng chung cho các lệnh CLI và server)."""
import json
import sys

from ..core.errors import CopilotInputError


def print_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=1, default=str))


def log(*s):
    """Log tiến độ ra stderr (stdout chỉ dành cho JSON kết quả)."""
    print(*s, file=sys.stderr, flush=True)


def json_args(a):
    """--args (chuỗi JSON) hoặc --args-file (ưu tiên) -> dict. JSON sai -> CopilotInputError('args')."""
    args = a.args
    if a.args_file:
        with open(a.args_file, encoding="utf-8") as f:
            args = f.read()
    try:
        return json.loads(args) if args else {}
    except ValueError as ex:
        raise CopilotInputError("args", "valid JSON", f"{ex}") from ex


def input_error(ex):
    return {"ok": False, "error": str(ex), "input": ex.name, "expected": ex.expected}
