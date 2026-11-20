"""Thông số cut board: templates/autocut_template.csv (mặc định của nhóm) + config.yaml (riêng từng máy).

File mẫu CSV là NGUỒN DUY NHẤT của giá trị mặc định. Script nhận thông số qua tham số hàm (dict P lồng nhau
P[nhóm][khoá]); không module nào tự đọc file mặc định trong lúc cắt.

Từ 0.5.1: đọc template / config.yaml / coerce nằm ở aedt_copilot.core.config; file này giữ đường dẫn cũ
(re-export) + phần riêng của cut board (build_params với quy tắc sweep, defaults).
"""
import copy  # noqa: F401  (giữ tên public cũ)
import os  # noqa: F401
import sys  # noqa: F401

import yaml  # noqa: F401

from ..core import config as _core
from ..core.config import CONFIG_FILE, ROOT, coerce, machine  # noqa: F401

TEMPLATE_FILE = _core.template_path("autocut")


def template_rows():
    """[{key, name, unit, type, scope, mandatory, default, desc}] của autocut_template.csv (xem core.config)."""
    return _core.template_rows(TEMPLATE_FILE)


def build_params(values=None):
    """values {key: giá trị ô} -> (P lồng nhau, danh sách lỗi). Thiếu ô bắt buộc -> lỗi."""
    P, errors = {}, []
    values = values or {}
    known = set()
    for r in template_rows():
        known.add(r["key"])
        sec, k = r["key"].split(".", 1)
        raw = values.get(r["key"], r["default"])
        try:
            v = coerce(raw, r["type"])
        except ValueError as ex:
            errors.append(f"{r['key']}: {ex}")
            v = None
        if v is None and r["mandatory"]:
            errors.append(f"{r['key']} ({r['name']}): ô vàng chưa điền")
        P.setdefault(sec, {})[k] = v
    for k in values:
        if k not in known:
            errors.append(f"{k}: không có trong template")
    errors += _end_gnd_errors(P.get("cutout") or {})                  # 022: kiểm cả khi chưa có sweep
    if not errors:
        sw = P["sweep"]
        if not (sw["stop_ghz"] > sw["start_ghz"] >= 0):
            errors.append("sweep: cần 0 <= start < stop")
        if not (0 < sw["step_ghz"] <= sw["stop_ghz"] - sw["start_ghz"]):
            errors.append("sweep.step_ghz: phải > 0 và <= stop - start")
        arc = (P.get("setup") or {}).get("arc_step_deg")
        if arc is not None and not (0 < arc <= 90):
            errors.append("setup.arc_step_deg: phải > 0 và <= 90")
        mr = (P.get("setup") or {}).get("max_refine_per_pass")
        if mr is not None and not (isinstance(mr, (int, float)) and not isinstance(mr, bool)
                                   and float(mr).is_integer() and 1 <= mr <= 100):
            errors.append("setup.max_refine_per_pass: phải là số nguyên 1..100")
    P.setdefault("cutout", {})["mode"] = "create_new"
    return P, errors


def _end_gnd_errors(c):
    """022: luật GND ở 2 đầu: bước > 0, lề >= 0 (None = lỗi kiểu đã báo)."""
    out = []
    for k, ok, msg in (("end_expansion_step", lambda v: v > 0, "phải > 0"),
                       ("end_region_margin_mm", lambda v: v >= 0, "phải >= 0")):
        v = c.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and not ok(v):
            out.append(f"cutout.{k}: {msg}")
    return out


def defaults():
    """Mặc định của nhóm (ô bắt buộc = None). Dùng cho thông số cấp job (run, display)."""
    return build_params()[0]
