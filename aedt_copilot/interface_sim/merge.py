"""Bước 3: gộp các interface đã apply vào workspace chính của người dùng (contract: isim-merge.md)."""
import os

from ..core.errors import CopilotInputError
from ..core.validate import require_int
from . import report, request as R


def plan(request_id, names=()):
    """-> (req, chọn được [tên], thiếu [{name, step}]). Không ghi gì."""
    req = R.load(request_id)
    if isinstance(names, str):
        names = [n for n in names.split(",") if n.strip()]
    names = [n.strip() for n in names] or list(req["interfaces"])
    ok, missing = [], []
    for n in names:
        if n not in req["interfaces"]:
            raise CopilotInputError("names", "interfaces of this request", n)
        try:
            st = R.get_state(req["request_id"], n)
        except CopilotInputError:
            missing.append({"name": n, "step": "(not started)"})
            continue
        if st["step"] == "applied" and not st.get("failed"):
            ok.append(n)
        else:
            missing.append({"name": n, "step": st["step"] + (" (failed)" if st.get("failed") else "")})
    return req, ok, missing


def run(request_id, names=(), port=None, log=print):
    from ..cut_board.merge import merge_designs
    if port in (None, 0, "", "0"):                                  # không gắn vào phiên AEDT đang mở
        port = None
    else:
        port = require_int("port", int(port) if str(port).isdigit() else port, 1, 65535)
    req, sel, missing = plan(request_id, names)
    if not sel:
        raise CopilotInputError("names", "at least one interface at step 'applied'", missing)
    rid = req["request_id"]
    sources = {n: R.get_state(rid, n)["result"]["aedb"] for n in sel}
    out = merge_designs(req["workspace"], sources, R.work_dir(req), port or None, log)
    for n, r in out["channels"].items():
        if r.get("state") in ("ok", "renamed"):
            R.set_state(rid, n, "merged", merged={"design": r["design"], "status": r["state"],
                                                  "warnings": r.get("warnings")})
            R.advance(rid, n, "merged")
        else:
            R.set_state(rid, n, "merge error", merged={"status": "error", "error": r.get("error")})
    out["not_merged"] = missing
    out["table_md"] = report.table(["Interface", "Design in workspace", "Status", "Error"],
                                   [[n, r.get("design"), r.get("state"), r.get("error")]
                                    for n, r in out["channels"].items()])
    R.wjson(os.path.join(R.work_dir(req), "merge.json"), out)
    return out
