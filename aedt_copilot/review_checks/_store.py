"""Bản ghi review cạnh board (feature 025, contract: review-gate.md).

<thư mục board>/Ansys AEDT Copilot/reviews/<tên board>/review_<giờ>.json — không bao giờ ghi đè (core.unique).
Mỗi channel có `key` (board key 023 + cell + 2 đầu + net đã trace + check + ngưỡng) để interface simulation dùng lại
và `findings` (số điểm NOT OK, check lỗi). 035: không còn verdict / quyết định từng điểm (design_review_decide bỏ).
"""
import datetime as dt
import glob
import json
import os

from ..core import unique
from ..core.errors import CopilotInputError
from . import _verdict as V

OUTPUT = os.path.join("Ansys AEDT Copilot", "reviews")
SCHEMA = 5                          # 034: luật ghép cặp mới (2); 035: không còn verdict / decisions (3);
#                                     036: status OK / NOT OK thay mức nặng nhẹ (4) -> bản ghi 3.0.0 không dùng lại
#                                     037: pair skew chỉ dữ liệu, pair gap bỏ thân BGA (5)


def folder(aedb):
    if not isinstance(aedb, str) or not aedb.strip():
        raise CopilotInputError("board", ".aedb path", aedb)
    a = os.path.abspath(aedb)
    return os.path.join(os.path.dirname(a), OUTPUT, os.path.splitext(os.path.basename(a))[0])


def _write(p, doc):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)


def _read(p):
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) and d.get("schema") == SCHEMA and isinstance(d.get("channels"), list) else None
    except (OSError, ValueError):
        return None


def channel_key(ch, board_key, cell_requested, checks, thr):
    """None khi channel lỗi / không có net (không bao giờ dùng lại)."""
    if ch.get("error") or not ch.get("nets"):
        return None
    return V.match_key(board_key, cell_requested, ch["comp_a"], ch["comp_b"], ch["nets"], checks, thr)


def annotate(out, board_key, cell_requested, thr):
    """Thêm key / findings / findings_md vào từng channel của kết quả đo (tại chỗ)."""
    for ch in out.get("channels") or []:
        ch["key"] = channel_key(ch, board_key, cell_requested, out.get("checks_run") or [], thr)
        ch["findings"] = V.channel_findings(ch)
        ch["findings_md"] = V.findings_md(ch.get("name") or "", ch["findings"])
    out["findings_md"] = "\n\n".join(c["findings_md"] for c in out.get("channels") or [])
    return out


def save(out, cell_requested, record_source, board_key, thr):
    """Ghi bản ghi mới; -> đường dẫn. out được bổ sung key / verdict."""
    if not isinstance(out, dict) or not out.get("board") or not isinstance(out.get("channels"), list):
        raise CopilotInputError("out", "measure output with board and channels", type(out).__name__)
    annotate(out, board_key, cell_requested, thr)
    now = dt.datetime.now()
    doc = dict(out, schema=SCHEMA, record_source=record_source, cell_requested=cell_requested or "",
               board_key=board_key, thresholds=thr, measured_at=out.get("measured_at") or now.isoformat(timespec="seconds"))
    doc.pop("review_file", None)
    p = unique.claim_file(os.path.join(folder(out["board"]), f"review_{now:%Y%m%d_%H%M%S}.json"))
    _write(p, doc)
    return p


def records(aedb):
    """Bản ghi của board, mới nhất trước."""
    fs = glob.glob(os.path.join(folder(aedb), "review_*.json"))
    return sorted(fs, key=lambda p: (os.path.getmtime(p), p), reverse=True)


def find(aedb, key):
    """-> (đường dẫn, doc, channel) của bản ghi mới nhất có channel khớp key; None nếu không có."""
    if not key:
        return None
    for p in records(aedb):
        doc = _read(p)
        if not doc:
            continue
        for ch in doc["channels"]:
            if ch.get("key") and not V.diff(ch["key"], key):
                return p, doc, ch
    return None
