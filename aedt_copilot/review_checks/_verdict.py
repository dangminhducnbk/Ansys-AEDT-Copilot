"""Tóm tắt review từng channel + khoá so khớp để dùng lại (025; contract 035: interface_sim-review.md). Thuần.

035 (user 2026-11-14): không còn kết luận STOP / CONTINUE; quyết định cut 100 % của kỹ sư sau khi đọc report HTML.
036 (user 2026-11-15): không còn mức HIGH / MEDIUM / INFO. Mỗi luật chỉ OK / NOT OK theo ngưỡng; số liệu = số NOT OK.
"""
from ..core.errors import CopilotInputError

NOK = "NOT OK"
NOT_THRESHOLD = ("use_snapshot",)                     # đổi đường đo, không đổi số liệu (023)


def channel_findings(ch):
    """-> {counts {"NOT OK": điểm}, by_check {check: finding NOT OK}, failed_checks, incomplete} (không kết luận)."""
    if not isinstance(ch, dict):
        raise CopilotInputError("channel", "measure channel object", ch)
    by = {}
    for i in ch.get("items") or []:
        if i.get("status") == NOK:
            by[i["check"]] = by.get(i["check"], 0) + 1
    failed = []
    if ch.get("error"):
        failed.append({"check": "trace", "error": str(ch["error"])})
    for name, c in (ch.get("checks") or {}).items():
        if isinstance(c, dict) and c.get("error"):
            failed.append({"check": name, "error": str(c["error"])})
    return {"counts": {NOK: len(ch.get("points") or [])}, "by_check": dict(sorted(by.items())),
            "failed_checks": failed, "incomplete": bool(failed)}


def thresholds(review_defaults):
    if not isinstance(review_defaults, dict):
        raise CopilotInputError("review_defaults", "dict of template review.* values", review_defaults)
    return {k: review_defaults[k] for k in sorted(review_defaults) if k not in NOT_THRESHOLD}


def match_key(board_key, cell, comp_a, comp_b, nets, checks, thresholds_):
    if not isinstance(board_key, dict) or not board_key.get("aedb"):
        raise CopilotInputError("board_key", "layout_snapshot.key.board_key() dict", board_key)
    if not comp_a or not comp_b:
        raise CopilotInputError("comp_a / comp_b", "two end refdes", (comp_a, comp_b))
    nets = sorted({str(n) for n in nets or [] if str(n).strip()})
    if not nets:
        raise CopilotInputError("nets", "at least one net", nets)
    return {"aedb": board_key["aedb"], "def_size": board_key.get("def_size"),
            "def_mtime_ns": board_key.get("def_mtime_ns"), "cell": cell or "",
            "ends": sorted([str(comp_a), str(comp_b)]), "nets": nets, "checks": sorted(checks or []),
            "thresholds": dict(thresholds_ or {})}


def diff(a, b):
    """-> các trường khác nhau giữa 2 khoá ([] = giống)."""
    a, b = a or {}, b or {}
    out = []
    if any(a.get(k) != b.get(k) for k in ("aedb", "def_size", "def_mtime_ns")):
        out.append("board_changed")
    for k in ("cell", "ends", "nets", "checks", "thresholds"):
        if a.get(k) != b.get(k):
            out.append(k)
    return out


def findings_md(name, f):
    """Một dòng số NOT OK (tổng điểm + theo check) + check lỗi (tiếng Anh như summary_md). Không kết luận (035/036)."""
    n = (f.get("counts") or {}).get(NOK, 0)
    by = ", ".join(f"{k} {v}" for k, v in (f.get("by_check") or {}).items())
    lines = [f"**{name}**: NOT OK {n}" + (f" ({by})" if by else "")
             + (" (incomplete review)" if f["incomplete"] else "")]
    for x in f["failed_checks"]:
        lines.append(f"- check {x['check']} failed: {x['error']}")
    return "\n".join(lines)
