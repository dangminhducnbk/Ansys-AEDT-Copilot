"""Schematic (PDF, agent đọc) + BOM (xlsx / csv, code đọc) -> schematic.md (contract: isim-schematic.md).

Agent điền template() rồi gửi lại qua save(); code kiểm tra các mục bắt buộc, lưu dấu vân tay file nguồn để dùng lại.
"""
import csv
import io
import os
import re

from ..core.errors import CopilotInputError
from ..core.validate import require_path, require_text
from . import report
from .request import NETLIST_FILE, _rjson, load, wjson, work_dir

COLS = {
    "refdes": ("refdes", "designator", "reference", "ref des", "ref. des.", "part reference", "references"),
    "part": ("part number", "partnumber", "mpn", "manufacturer part number", "mfr part number", "part"),
    "value": ("value", "comment"),
    "desc": ("description", "desc"),
}
SECTIONS = {
    "Sources": None,
    "Components": ["Refdes", "Part", "Value", "Description", "Page"],
    "Nets": ["Net", "Pins (refdes.pin, ...)", "Page"],
}
OPTIONAL = {"Unreadable": None, "BOM differences": ["Refdes", "In BOM", "In schematic", "Note"]}


# ----------------------------------------------------------------------------- BOM
def _expand(text):
    """'R1-R4, C5 C6' -> ['R1','R2','R3','R4','C5','C6']."""
    out = []
    for tok in re.split(r"[,;\s]+", str(text or "").strip()):
        if not tok:
            continue
        m = re.fullmatch(r"([A-Za-z_]+)(\d+)-(?:\1)?(\d+)", tok)
        if m and int(m.group(3)) >= int(m.group(2)) and int(m.group(3)) - int(m.group(2)) < 1000:
            out += [f"{m.group(1)}{i}" for i in range(int(m.group(2)), int(m.group(3)) + 1)]
        else:
            out.append(tok)
    return out


def _rows_xlsx(path):
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:                          # sheet đầu tiên có dòng tiêu đề chứa cột refdes
            rows = [[("" if c is None else str(c)).strip() for c in r] for r in ws.iter_rows(values_only=True)]
            for i, r in enumerate(rows[:50]):
                if any(c.lower() in COLS["refdes"] for c in r):
                    return rows[i], rows[i + 1:]
        return [], []
    finally:
        wb.close()


def _rows_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = [[c.strip() for c in r] for r in csv.reader(io.StringIO(text), dialect)]
    for i, r in enumerate(rows[:50]):
        if any(c.lower() in COLS["refdes"] for c in r):
            return rows[i], rows[i + 1:]
    return (rows[0] if rows else []), rows[1:]


def parse_bom(path):
    p = require_path("bom", path, "file")
    head, body = _rows_xlsx(p) if p.lower().endswith((".xlsx", ".xlsm")) else _rows_csv(p)
    low = [h.lower() for h in head]
    cmap = {}
    for k, names in COLS.items():
        for i, h in enumerate(low):
            if h in names:
                cmap[k] = i
                break
    if "refdes" not in cmap:
        raise CopilotInputError("bom", "a refdes column (Refdes / Designator / Reference)", head)
    rows, seen, warnings = [], set(), []
    for r in body:
        if not any(r):
            continue
        get = lambda k: r[cmap[k]] if k in cmap and cmap[k] < len(r) else ""
        for rd in _expand(get("refdes")):
            if rd.upper() in seen:
                warnings.append(f"duplicate refdes {rd} (first row kept)")
                continue
            seen.add(rd.upper())
            rows.append({"refdes": rd, "part": get("part"), "value": get("value"), "desc": get("desc")})
    used = set(cmap.values())
    return {"columns_map": {k: head[i] for k, i in cmap.items()}, "rows": rows,
            "unmapped_columns": [h for i, h in enumerate(head) if i not in used and h], "warnings": warnings}


def save_bom(request_id, path=""):
    req = load(request_id)
    path = path or req.get("bom")
    if not path:
        raise CopilotInputError("bom", "BOM path (in isim_start or here)", path)
    b = parse_bom(path)
    out = os.path.join(work_dir(req), "bom.json")
    wjson(out, b)
    return {**{k: b[k] for k in ("columns_map", "unmapped_columns", "warnings")}, "rows": len(b["rows"]),
            "bom_json": out}


# ----------------------------------------------------------------------------- fingerprints
def fingerprints(paths):
    out = []
    for p in paths:
        if p and os.path.exists(p):
            st = os.stat(p)
            out.append({"path": os.path.abspath(p), "size": st.st_size, "mtime": round(st.st_mtime, 3)})
    return out


def _sources(req):
    return list(req.get("schematic") or []) + ([req["bom"]] if req.get("bom") else [])


def status(request_id=""):
    req = load(request_id)
    w = work_dir(req)                                                   # 038: file request trong _work/
    md = os.path.join(w, "schematic.md")
    stored = _rjson(os.path.join(w, "schematic.sources.json"))
    now = fingerprints(_sources(req))
    # dùng lại schematic.md của request trước cùng workspace khi nguồn không đổi
    reuse = None
    if not os.path.exists(md):
        root = os.path.dirname(req["folder"])
        for d in sorted(os.listdir(root), reverse=True) if os.path.isdir(root) else []:
            f = os.path.join(root, d)
            for fw in (os.path.join(f, "_work"), f):
                if f != req["folder"] and os.path.exists(os.path.join(fw, "schematic.md")) and \
                        _rjson(os.path.join(fw, "schematic.sources.json")) == now and now:
                    reuse = os.path.join(fw, "schematic.md")
                    break
            if reuse:
                break
    out = {"exists": os.path.exists(md), "up_to_date": os.path.exists(md) and stored == now and bool(now),
           "path": md, "sources": now, "reuse_from": reuse}
    nl = _rjson(os.path.join(w, NETLIST_FILE))
    if nl:                                    # 036: có netlist -> kết nối lấy từ netlist, không cần đọc PDF
        from . import netlist as NL
        out.update(netlist=NL.summary(nl), up_to_date=True, source="netlist")
    else:
        out["source"] = "pdf" if (out["exists"] or reuse) else None
    return out


def is_up_to_date(request_id=""):
    return status(request_id)["up_to_date"]


# ----------------------------------------------------------------------------- markdown
def template():
    return "\n".join([
        "# Schematic + BOM", "",
        "## Sources", "- <file name> (pages read: ...)", "",
        "## Components", report.table(SECTIONS["Components"], [["U1", "", "", "", "1"]]), "",
        "## Nets", report.table(SECTIONS["Nets"], [["NET_NAME", "U1.A1, R1.1", "1"]]), "",
        "## Unreadable", "- (page / area the agent could not read clearly)", "",
        "## BOM differences", report.table(OPTIONAL["BOM differences"], [["", "", "", ""]]), ""])


def _sections(md):
    out, cur = {}, None
    for ln in md.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m:
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(ln)
    return out


def _table(lines):
    rows = [ln.strip() for ln in lines if ln.strip().startswith("|")]
    if len(rows) < 2:
        return None, []
    split = lambda ln: [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", ln.strip().strip("|"))]
    head = split(rows[0])
    body = [split(r) for r in rows[2:] if not re.fullmatch(r"\|?[\s:\-|]+\|?", r)]
    return head, body


def parse(md):
    secs = _sections(md)
    comps, nets, bad = {}, {}, []
    _, body = _table(secs.get("Components", []))
    for r in body:
        if len(r) < 5 or not r[0]:
            bad.append(r)
            continue
        comps[r[0]] = {"part": r[1], "value": r[2], "desc": r[3], "page": r[4]}
    _, body = _table(secs.get("Nets", []))
    for r in body:
        if len(r) < 3 or not r[0]:
            bad.append(r)
            continue
        toks = [t for t in re.split(r"[,;\s]+", r[1]) if t]
        if not toks or any("." not in t for t in toks):
            bad.append(r)
            continue
        nets[r[0]] = {"pins": [tuple(t.split(".", 1)) for t in toks], "page": r[2]}
    return {"components": comps, "nets": nets, "bad_rows": bad,
            "unreadable": [ln.strip("- ").strip() for ln in secs.get("Unreadable", []) if ln.strip().startswith("-")]}


def save(request_id, markdown):
    md = require_text("markdown", markdown)
    secs = _sections(md)
    for name, head in SECTIONS.items():
        if name not in secs:
            raise CopilotInputError("markdown", f"section '## {name}'", sorted(secs))
        if head:
            h, _ = _table(secs[name])
            if h != head:
                raise CopilotInputError(f"## {name} table header", "| " + " | ".join(head) + " |", h)
    data = parse(md)
    req = load(request_id)
    warnings = [f"row not understood: {r}" for r in data["bad_rows"]]
    bom = _rjson(os.path.join(work_dir(req), "bom.json"))
    if bom:
        b = {r["refdes"].upper() for r in bom["rows"]}
        s = {k.upper() for k in data["components"]}
        if b - s:
            warnings.append(f"in BOM, not in schematic table: {sorted(b - s)[:30]}")
        if s - b:
            warnings.append(f"in schematic table, not in BOM: {sorted(s - b)[:30]}")
    path = os.path.join(work_dir(req), "schematic.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md if md.endswith("\n") else md + "\n")
    wjson(os.path.join(work_dir(req), "schematic.sources.json"), fingerprints(_sources(req)))
    return {"path": path, "components": len(data["components"]), "nets": len(data["nets"]),
            "unreadable": data["unreadable"], "warnings": warnings}


def load_parsed(request_id=""):
    """netlist.json (036, ưu tiên) hoặc schematic.md đã lưu (hoặc bản dùng lại) -> parse(); None nếu chưa có."""
    req = load(request_id)
    nl = _rjson(os.path.join(work_dir(req), NETLIST_FILE))
    if nl:
        from . import netlist as NL
        return NL.as_schematic(nl)
    st = status(request_id)
    p = st["path"] if st["exists"] else st["reuse_from"]
    if not p:
        return None
    with open(p, encoding="utf-8") as f:
        return dict(parse(f.read()), source="pdf")
