"""Đổi đơn vị m <-> mm (contract: core-units.md). EDB dùng mét; template / báo cáo dùng mm."""
from .validate import require_int, require_number

MM = 1e-3        # mét / mm (như cutter.MM)
MM2 = 1e-6       # m2 / mm2


def mm_to_m(v):
    return require_number("v", v) * MM


def m_to_mm(v):
    return require_number("v", v) / MM


def mm2_to_m2(v):
    return require_number("v", v) * MM2


def m2_to_mm2(v):
    return require_number("v", v) / MM2


def edb_length(m, digits=4):
    """Độ dài (m) -> chuỗi cho EDB, vd 0.0002 -> '0.2mm' (giống chuỗi solder ball trong cutter.py)."""
    require_number("m", m)
    require_int("digits", digits, 0, 9)
    return f"{round(m / MM, digits):g}mm"
