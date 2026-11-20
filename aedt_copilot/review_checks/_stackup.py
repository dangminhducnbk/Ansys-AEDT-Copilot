"""Bảng width / gap theo lớp từ stackup của nhà máy (feature 030, luật 6; contract: specs/030-review-rules-si/contracts/
review-rules.md). Claude đọc file stackup (PDF / Excel) MỘT lần, người dùng xác nhận, tool lưu:
<thư mục board>/Ansys AEDT Copilot/stackup/<tên board>.json. Không bao giờ ghi vào board.

Bảng: {board, source_file, confirmed_at, note, layers: {<lớp tín hiệu>: {se_width_mm, pairs: [{name, width_mm,
gap_mm}]}}}; se_width_mm = null khi lớp không có dây đơn; pairs = [] khi không có cặp.
"""
import datetime as dt
import hashlib
import json
import os

from ..core.errors import CopilotInputError

FOLDER = os.path.join("Ansys AEDT Copilot", "stackup")


def path(aedb):
    if not isinstance(aedb, str) or not aedb.strip():
        raise CopilotInputError("board", ".aedb path", aedb)
    a = os.path.abspath(aedb.rstrip("\\/"))
    stem = os.path.splitext(os.path.basename(a))[0]
    return os.path.join(os.path.dirname(a), FOLDER, f"{stem}.json")


def load(aedb):
    """-> bảng hoặc None (chưa có / không đọc được)."""
    if not aedb:
        return None
    try:
        with open(path(aedb), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) and isinstance(d.get("layers"), dict) else None
    except (OSError, ValueError, CopilotInputError):
        return None


def table_hash(aedb):
    t = load(aedb)
    if not t:
        return None
    return hashlib.sha1(json.dumps(t.get("layers"), sort_keys=True).encode()).hexdigest()[:16]


def _pos(v, where):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise CopilotInputError(where, "positive number (mm)", v)
    if not x > 0:
        raise CopilotInputError(where, "positive number (mm)", v)
    return round(x, 6)


def validate(table, layers):
    """-> bảng chuẩn hoá. layers = lớp tín hiệu của board (tên phải khớp)."""
    if isinstance(table, str):
        try:
            table = json.loads(table)
        except ValueError:
            raise CopilotInputError("table", "JSON object {layers: {...}}", table[:80])
    if not isinstance(table, dict) or not isinstance(table.get("layers"), dict) or not table["layers"]:
        raise CopilotInputError("table", "{layers: {<signal layer>: {se_width_mm, pairs: [...]}}}", type(table).__name__)
    known = list(layers or [])
    out = {}
    for lay, v in table["layers"].items():
        if known and lay not in known:
            raise CopilotInputError(f"table.layers.{lay}", "a signal layer of the board: " + ", ".join(known), lay)
        if not isinstance(v, dict):
            raise CopilotInputError(f"table.layers.{lay}", "{se_width_mm, pairs}", v)
        se = v.get("se_width_mm")
        pairs = []
        for i, p in enumerate(v.get("pairs") or []):
            if not isinstance(p, dict):
                raise CopilotInputError(f"table.layers.{lay}.pairs[{i}]", "{name, width_mm, gap_mm}", p)
            pairs.append({"name": str(p.get("name") or f"pair {i + 1}"),
                          "width_mm": _pos(p.get("width_mm"), f"table.layers.{lay}.pairs[{i}].width_mm"),
                          "gap_mm": _pos(p.get("gap_mm"), f"table.layers.{lay}.pairs[{i}].gap_mm")})
        if se in (None, "") and not pairs:
            raise CopilotInputError(f"table.layers.{lay}", "se_width_mm and / or pairs", v)
        out[lay] = {"se_width_mm": None if se in (None, "") else _pos(se, f"table.layers.{lay}.se_width_mm"),
                    "pairs": pairs}
    return {"layers": out, "note": str(table.get("note") or "")}


def template(layers):
    return {"layers": {l: {"se_width_mm": None, "pairs": [{"name": "", "width_mm": None, "gap_mm": None}]}
                       for l in layers},
            "note": "fill from the fab stackup (mm); delete layers without signal routing"}


def save(aedb, table, source_file, layers):
    """Ghi bảng (bảng cũ chuyển sang tên _old_<giờ>, không ghi đè). -> đường dẫn."""
    from ..core.unique import move_aside
    t = validate(table, layers)
    p = path(aedb)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p):
        move_aside(p, p[:-5] + "_old_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
    doc = {"board": os.path.abspath(aedb), "source_file": source_file or "",
           "confirmed_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **t}
    tmp = p + f".{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    os.replace(tmp, p)
    return p


def expected(table, layer, paired):
    """-> (độ rộng hợp lệ [mm], cặp [{width_mm, gap_mm, name}]) của lớp; None khi lớp không có trong bảng."""
    e = ((table or {}).get("layers") or {}).get(layer)
    if not e:
        return None
    if paired:
        return [p["width_mm"] for p in e.get("pairs") or []], e.get("pairs") or []
    return ([e["se_width_mm"]] if e.get("se_width_mm") else []), []


# ----------------------------------------------------------------------------- CLI `stackup-table` / tool review_stackup_table
OPS = ("get", "template", "save")


def board_layers(aedb, cell=""):
    """Lớp tín hiệu của board: từ index layout snapshot còn hợp lệ, không có thì mở EDB chỉ đọc."""
    from ..layout_snapshot import key as K, store as S
    try:
        key = K.board_key(aedb, cell or "")
        idx = S.read_index(K.index_dir(aedb, key), key)
        if idx:
            return [l[0] for l in idx["layers"]]
    except Exception:
        pass
    from ..cut_board import config, inspect_board
    edb = inspect_board.open_edb(aedb, cell=cell or None, readonly=True, version=config.machine()["aedt_version"])
    try:
        return list(edb.stackup.signal_layers)
    finally:
        edb.close()


def run_op(op, args):
    from ..cut_board import naming
    if op not in OPS:
        raise CopilotInputError("op", " / ".join(OPS), op)
    a = dict(args or {})
    board = a.get("board")
    if not isinstance(board, str) or not board.strip():
        raise CopilotInputError("board", ".aedb / .aedt path", board)
    aedb, _ = naming.board_paths(board)
    if op == "get":
        return {"path": path(aedb), "table": load(aedb)}
    layers = board_layers(aedb, a.get("cell") or "")
    if op == "template":
        return {"path": path(aedb), "layers": layers, "table": template(layers)}
    p = save(aedb, a.get("table"), a.get("source_file") or "", layers)
    return {"path": p, "table": load(aedb)}
