"""Netlist schematic do code đọc (feature 036, contract: specs/036-no-severity-netlist/contracts/contracts.md).

Kết nối + giá trị linh kiện lấy thẳng từ netlist (không đọc PDF): tên net sau compile của công cụ schematic, nên
off-page / block diagram đổi tên không còn là vấn đề. Định dạng nhận theo NỘI DUNG (không theo đuôi file):
  - Protel netlist 2.0 (Altium): khối '[' DESIGNATOR / FOOTPRINT / PARTTYPE / cặp khoá-giá trị ']' và khối net
    '(' tên net / 'REFDES-PIN ...' ')'.
  - Allegro / Telesis: '$PACKAGES' (fp ! 'part' ! 'value' ; refdes ...) và '$NETS' (NET ; refdes.pin ...), dòng kết
    thúc bằng ',' nối tiếp dòng sau; các mục lặp lại được gộp.
Chỉ đọc file. -> {format, design, components {refdes: {part, value, pins}}, nets {name: [[refdes, pin]]}, warnings}.
"""
import os
import re

from ..core.errors import CopilotInputError
from ..core.validate import require_path

FORMATS = "Protel netlist 2.0 (Altium) or Allegro / Telesis netlist ($PACKAGES / $NETS)"
VALUE_KEYS = ("value", "capacitance", "resistance", "inductance")
_VAL = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?\s?(?:[pnuµmkKMG]?(?:F|H|Ohm|ohm|OHM|Ω|R)|[kKM](?![A-Za-z])|[pnuµ]))"
                  r"(?![A-Za-z0-9])")


def _read(path):
    for enc in ("utf-8-sig", "cp1252"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    with open(path, encoding="latin-1") as f:
        return f.read()


def detect(text):
    """-> 'protel2' / 'telesis'; khác -> CopilotInputError."""
    head = [ln.strip() for ln in text.splitlines()[:20] if ln.strip()]
    if head and (head[0].upper().startswith("PROTEL NETLIST") or head[0] == "["):
        return "protel2"
    if re.search(r"^\s*\$(PACKAGES|NETS)\b", text, re.M):
        return "telesis"
    raise CopilotInputError("netlist", FORMATS, head[0][:80] if head else "(empty file)")


def value_of(text):
    """Giá trị linh kiện trong chuỗi part type ('CAP,CER,220nF,20%,...' -> '220nF'); không có -> ''."""
    m = _VAL.search(str(text or ""))
    return m.group(1).replace(" ", "") if m else ""


def _split_pin(tok, comps, sep):
    """'C951-1' -> ('C951', '1'): chọn vị trí tách sao cho refdes là linh kiện đã biết; không biết -> tách lần đầu."""
    idx = [i for i, ch in enumerate(tok) if ch == sep]
    for i in idx:
        if tok[:i] in comps:
            return tok[:i], tok[i + 1:]
    if idx:
        return tok[:idx[0]], tok[idx[0] + 1:]
    return None


# ----------------------------------------------------------------------------- Protel 2.0
def _protel(text):
    comps, nets, warnings = {}, {}, []
    lines = text.splitlines()
    i, n = 0, len(lines)
    raw_nets = []
    while i < n:
        s = lines[i].strip()
        if s == "[":
            j = i + 1
            block = []
            while j < n and lines[j].strip() != "]":
                block.append(lines[j].rstrip("\r\n"))
                j += 1
            b = [x.strip() for x in block]
            if len(b) >= 2 and b[0].upper() == "DESIGNATOR" and b[1]:
                rd = b[1]
                part = b[b.index("PARTTYPE") + 1] if "PARTTYPE" in b[:8] and b.index("PARTTYPE") + 1 < len(b) else ""
                val = ""
                low = [x.lower() for x in b]
                for k in VALUE_KEYS:
                    if k in low[6:]:
                        p = low.index(k, 6) + 1
                        if p < len(b) and b[p] and b[p].lower() not in VALUE_KEYS:
                            val = b[p]
                            break
                comps[rd] = {"part": part, "value": val or value_of(part), "pins": 0}
            i = j + 1
            continue
        if s == "(":
            j = i + 1
            block = []
            while j < n and lines[j].strip() != ")":
                block.append(lines[j].strip())
                j += 1
            if block:
                raw_nets.append((block[0], [x.split()[0] for x in block[1:] if x.split()]))
            i = j + 1
            continue
        i += 1
    for name, toks in raw_nets:
        pins = nets.setdefault(name, [])
        for t in toks:
            rp = _split_pin(t, comps, "-")
            if rp is None:
                warnings.append(f"pin not understood in net {name}: {t}")
                continue
            if list(rp) not in pins:
                pins.append(list(rp))
    return comps, nets, warnings, ""


# ----------------------------------------------------------------------------- Allegro / Telesis
def _logical(lines):
    """Gộp dòng kết thúc bằng ',' với dòng sau."""
    cur = ""
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        cur = f"{cur} {s}" if cur else s
        if cur.endswith(","):
            cur = cur[:-1]
            continue
        yield cur
        cur = ""
    if cur:
        yield cur


def _unq(s):
    s = s.strip()
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] == "'" else s


def _telesis(text):
    comps, nets, warnings = {}, {}, []
    design = ""
    m = re.search(r"\(FOR DRAWING:\s*(.+?)\)\s*$", text, re.M)
    if m:
        design = os.path.splitext(os.path.basename(m.group(1).strip().replace("\\", "/")))[0]
    blocks, sect, buf = [], None, []                   # đoạn liên tiếp của một mục '$...' (mục lặp lại -> nhiều đoạn)
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("$"):
            if buf:
                blocks.append((sect, buf))
            sect, buf = s.split()[0].upper(), []
            continue
        buf.append(ln)
    if buf:
        blocks.append((sect, buf))
    for sect, buf in blocks:
        if sect == "$PACKAGES":
            for lg in _logical(buf):
                head, _, refs = lg.partition(";")
                parts = [_unq(x) for x in head.split("!")]
                part = parts[1] if len(parts) > 1 else ""
                val = parts[2] if len(parts) > 2 else value_of(part)
                for rd in refs.split():
                    rd = _unq(rd)
                    if rd and rd not in comps:
                        comps[rd] = {"part": part, "value": val, "pins": 0}
        elif sect == "$NETS":
            for lg in _logical(buf):
                name, _, toks = lg.partition(";")
                name = _unq(name)
                if not name:
                    continue
                pins = nets.setdefault(name, [])
                for t in toks.split():
                    rp = _split_pin(_unq(t), comps, ".")
                    if rp is None:
                        warnings.append(f"pin not understood in net {name}: {t}")
                        continue
                    if list(rp) not in pins:
                        pins.append(list(rp))
    return comps, nets, warnings, design


# ----------------------------------------------------------------------------- API
def parse(path):
    p = require_path("netlist", path, "file")
    text = _read(p)
    fmt = detect(text)
    comps, nets, warnings, design = (_protel if fmt == "protel2" else _telesis)(text)
    if not nets:
        raise CopilotInputError("netlist", FORMATS + " with at least one net", os.path.basename(p))
    for pins in nets.values():
        for rd, _ in pins:
            if rd in comps:
                comps[rd]["pins"] += 1
            else:
                comps[rd] = {"part": "", "value": "", "pins": 1}
    return {"source": os.path.abspath(p), "format": fmt, "design": design, "components": comps,
            "nets": {k: v for k, v in nets.items() if v}, "warnings": warnings[:50],
            "warnings_total": len(warnings)}


def summary(nl, path=""):
    return {"path": path or nl.get("source"), "format": nl["format"], "design": nl.get("design") or "",
            "components": len(nl["components"]), "nets": len(nl["nets"]), "warnings": nl.get("warnings") or []}


def as_schematic(nl):
    """netlist -> dạng schematic.parse() (components / nets {pins, page}) để so với board."""
    return {"components": {rd: {"part": c.get("part", ""), "value": c.get("value", ""), "desc": "", "page": ""}
                           for rd, c in nl["components"].items()},
            "nets": {n: {"pins": [tuple(p) for p in pins], "page": ""} for n, pins in nl["nets"].items()},
            "bad_rows": [], "unreadable": [], "source": "netlist", "design": nl.get("design") or ""}
