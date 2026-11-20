"""Cấu hình máy (config.yaml) + đọc template CSV mặc định của nhóm (contract: core-config.md).

templates/*.csv là NGUỒN DUY NHẤT của giá trị mặc định. Đọc theo TÊN cột tiêu đề nên cả 3 template
(autocut 8 cột, pidc 8 cột, layout_edit 5 cột) dùng chung một hàm.
"""
import copy
import csv
import os
import sys

import yaml

from .errors import CopilotInputError
from .validate import require_choice

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
TEMPLATES_DIR = os.path.join(ROOT, "templates")
CONFIG_FILE = os.path.join(ROOT, "config.yaml")
TEMPLATES = {"autocut": "autocut_template.csv", "pidc": "pidc_template.csv",
             "layout_edit": "layout_edit_template.csv"}
TYPES = ("num", "bool", "text", "list")
# cột CSV -> (khoá trong dict, giá trị khi thiếu cột)
_COLS = (("Key", "key", ""), ("Parameter", "name", ""), ("Unit", "unit", ""), ("Type", "type", "text"),
         ("Scope", "scope", "channel"), ("Mandatory", "mandatory", ""), ("Default", "default", ""),
         ("Description", "desc", ""))
_cache = {}


def template_path(name):
    require_choice("name", name, list(TEMPLATES))
    return os.path.join(TEMPLATES_DIR, TEMPLATES[name])


def machine(config_file=CONFIG_FILE):
    cfg = {}
    if os.path.exists(config_file):
        with open(config_file, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    if not cfg.get("aedt_version"):
        cfg["aedt_version"] = "2026.1"                    # "auto" = bản mới nhất (aedt_env)
    py = cfg.get("python") or sys.executable
    if not os.path.isabs(py):
        py = os.path.join(ROOT, py)
    cfg["python"] = py if os.path.exists(py) else sys.executable
    return cfg


def template_rows(path):
    """[{key, name, unit, type, scope, mandatory, default, desc}] theo thứ tự trong file.
    Bỏ dòng trống và dòng bắt đầu bằng '#'; dòng còn lại đầu tiên = tiêu đề (cần cột Key và Default)."""
    p = os.path.abspath(os.fspath(path))
    if not os.path.isfile(p):
        raise CopilotInputError("template", "existing file", p)
    mt = os.path.getmtime(p)
    hit = _cache.get(p)
    if not hit or hit[0] != mt:
        with open(p, encoding="utf-8-sig", newline="") as f:
            lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith("#")]
        recs = list(csv.reader(lines))
        head = [h.strip() for h in recs[0]] if recs else []
        if "Key" not in head or "Default" not in head:
            raise CopilotInputError("template header", "columns Key and Default", head)
        idx = {h: i for i, h in enumerate(head)}
        rows = []
        for r in recs[1:]:
            if not r or not r[0].strip():
                continue
            cells = [x.strip() for x in r]
            row = {}
            for col, k, miss in _COLS:
                i = idx.get(col)
                v = cells[i] if i is not None and i < len(cells) else ""
                row[k] = v if v != "" else miss
            row["key"] = str(row["key"]).strip()
            row["mandatory"] = str(row["mandatory"]).lower() == "yes"
            row["default"] = row["default"] if row["default"] != "" else None
            rows.append(row)
        _cache[p] = (mt, rows)
    return copy.deepcopy(_cache[p][1])


def coerce(value, typ):
    """Giá trị ô Excel / default -> kiểu Python. Ô trống -> None. Sai kiểu -> ValueError (thông điệp như cũ)."""
    if typ not in TYPES:
        raise CopilotInputError("typ", "one of " + ", ".join(TYPES), typ)
    if value is None or str(value).strip() == "":
        return None
    t = str(value).strip()
    if typ == "bool":
        if t.lower() in ("true", "yes", "1", "on", "x"):
            return True
        if t.lower() in ("false", "no", "0", "off"):
            return False
        raise ValueError(f"'{t}' không phải true/false")
    if typ == "num":
        f = float(t)
        return int(f) if f.is_integer() and "." not in t and "e" not in t.lower() else f
    if typ == "list":
        out = []
        for x in t.replace(";", ",").split(","):
            x = x.strip()
            if x:
                try:
                    out.append(int(x))
                except ValueError:
                    out.append(x)
        return out
    return t
