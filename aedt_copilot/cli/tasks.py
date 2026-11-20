"""Chạy CLI ở tiến trình con cho MCP server: quá `wait` giây thì trả task_id (gọi result sau).

Python có pyedb .NET lấy từ config.yaml; env + ANSYSEM_ROOT### / license từ env Windows (aedt_env.child_env).
Log stderr: <repo>/.tasks/<task_id>.log. Tham số dài: args_file -> <repo>/.tasks/<stem>_<hex8>.json.
"""
import json
import os
import subprocess
import threading
import uuid

from .. import aedt_env
from ..core import config

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS_DIR = os.path.join(ROOT, ".tasks")
TASKS = {}


def run(args, wait=45):
    """Chạy `python -m aedt_copilot <args>`; quá `wait` giây thì trả {pending, task_id}."""
    m = config.machine()
    tid = uuid.uuid4().hex[:8]
    log = os.path.join(TASKS_DIR, f"{tid}.log")
    os.makedirs(TASKS_DIR, exist_ok=True)
    proc = subprocess.Popen([m["python"], "-u", "-m", "aedt_copilot", *args], cwd=ROOT,
                            env=aedt_env.child_env(),        # + ANSYSEM_ROOT### / license từ env Windows
                            stdin=subprocess.DEVNULL,       # không kế thừa stdin JSON-RPC của server (Windows: treo tiến trình con)
                            stdout=subprocess.PIPE, stderr=open(log, "w", encoding="utf-8"),
                            creationflags=0x08000000 if os.name == "nt" else 0)
    box = {}

    def reader():
        out = proc.stdout.read().decode("utf-8", "replace")
        proc.wait()
        box["rc"], box["out"] = proc.returncode, out

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    TASKS[tid] = (th, box, log)
    th.join(wait)
    return result(tid)


def result(tid):
    if tid not in TASKS:
        return {"error": f"Không có task {tid}"}
    th, box, log = TASKS[tid]
    if th.is_alive():
        return {"pending": True, "task_id": tid, "hint": "Gọi task_result(task_id) sau 30-60 s"}
    out = box.get("out", "")
    try:
        data = json.loads(out[out.index("{"):]) if "{" in out else {"output": out}
    except ValueError:
        data = {"output": out[-4000:]}
    if box.get("rc"):
        with open(log, encoding="utf-8", errors="ignore") as f:
            data["error_log"] = f.read()[-4000:]
    return data


def args_file(stem, data):
    """Ghi tham số cho tiến trình con: str ghi nguyên văn, còn lại JSON. Trả đường dẫn file."""
    os.makedirs(TASKS_DIR, exist_ok=True)
    path = os.path.join(TASKS_DIR, f"{stem}_{uuid.uuid4().hex[:8]}.json")
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(data, str):
            f.write(data)
        else:
            json.dump(data, f, ensure_ascii=False)
    return path
