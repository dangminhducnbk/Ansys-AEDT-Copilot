"""Hàm phụ cho chữ báo cáo của các check (feature 028; chuyển nguyên văn từ cut_board/review_report.py 2.6.0).
Module riêng (tên bắt đầu '_') -> registry không nạp như một check."""
import re

MM = 1e-3


def mm(v):
    return f"{v / MM:.3f}"


def num(text, pat):
    m = re.search(pat, str(text or ""))
    return float(m.group(1)) if m else None


def via_row(c, f):
    for v in (c or {}).get("vias") or []:
        if v["net"] == f["net"] and abs(v["x"] - f["x"]) < 1e-9 and abs(v["y"] - f["y"]) < 1e-9:
            return v
    return None


def planes(txt):
    return " / ".join(x.strip() for x in str(txt).split(",") if x.strip())


def xy(f):
    return f"({mm(f['x'])}, {mm(f['y'])}) mm"


def trace_seg(f):
    if f.get("start") and f.get("end"):
        return (f" from ({mm(f['start'][0])}, {mm(f['start'][1])}) to ({mm(f['end'][0])}, "
                f"{mm(f['end'][1])}) mm")
    return ""


def length_row(f):
    L = f.get("len_mm")
    return ("Length", f"{L:.3f} mm — limit: none ✗" if L is not None else "-")
