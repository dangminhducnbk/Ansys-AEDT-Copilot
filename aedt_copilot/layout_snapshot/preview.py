"""Cut preview trên layout snapshot (feature 027, contract: specs/027-snapshot-phase2/contracts/snapshot-phase2.md).

Extent = EDB expanded_extent (thuật toán của AEDT), lưu cache theo (net, thông số extent, hệ số) trong thư mục index của
snapshot (khoá board) -> preview luôn GIỐNG HỆT extent lúc cut (Q2 A). Pin GND / linh kiện / net khác / cảnh vẽ đọc từ
snapshot. Board chỉ mở khi thiếu cache (một lần cho cả lượt preview), không bao giờ ghi.
"""
import contextlib
import hashlib
import json
import os
import time

from ..core.errors import CopilotInputError
from . import SnapshotFallback, key as K, store as S

MM = 1e-3
EXTENTS, COMP_PINS = "extents", "comp_pins"
COMP_MARGIN_MM = 5.0            # quanh vị trí pin của linh kiện đầu (pad tới 10 mm + vùng đầu 1 mm)
EXTENT_MARGIN_MM = 1.5          # quanh extent (cảnh vẽ đọc trace / via trong extent + 1 mm)


def extent_key(P, nets, factor=None):
    if not isinstance(nets, (list, tuple, set)) or not nets or not all(isinstance(n, str) and n for n in nets):
        raise CopilotInputError("nets", "non-empty list of net names", nets)
    c = P["cutout"]
    f = float(c["expansion"] if factor is None else factor)
    return {"nets": sorted(nets), "extent_type": str(c["extent_type"]).lower(),
            "unitless": bool(c["expansion_unitless"]), "round_corner": bool(c["round_corner"]),
            "increments": int(c["increments"]), "factor": f}


def _hash(d):
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:16]


def _wjson(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)


def _rjson(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


class ExtentCache:
    """get(factor) -> điểm extent mm (như cutter.compute_extent_mm). opener() -> EDB đã mở (chỉ gọi khi thiếu)."""

    def __init__(self, folder, P, nets, opener, log=None):
        self.folder, self.P, self.nets, self.opener = folder, P, list(nets), opener
        self.log = log or (lambda *a: None)
        self.hits = self.misses = 0
        extent_key(P, nets)                                     # kiểm tra đầu vào

    def get(self, factor=None):
        k = extent_key(self.P, self.nets, factor)
        path = os.path.join(self.folder, EXTENTS, _hash(k) + ".json")
        d = _rjson(path)
        if d and d.get("key") == k:
            self.hits += 1
            return [tuple(q) for q in d["pts_mm"]]
        from ..cut_board import cutter
        self.misses += 1
        pts = cutter.compute_extent_mm(self.opener(), self.P, self.nets, self.log, factor=factor)
        _wjson(path, {"key": k, "pts_mm": [list(q) for q in pts], "built_at": time.strftime("%Y-%m-%d %H:%M:%S")})
        return [tuple(q) for q in pts]


def comp_pins(opener, idx, folder, refdes):
    """{iid: [[x0, y0], [x1, y1]]} mọi pin của linh kiện (gồm GND / nguồn; cửa sổ snapshot bỏ pin nguồn)."""
    comp = idx["comps"].get(refdes)
    if comp is None:
        raise CopilotInputError("refdes", "component of the board", refdes)
    path = os.path.join(folder, COMP_PINS, f"{K._safe(refdes)}.json")
    d = _rjson(path)
    ids = [str(i) for i in comp["pins"]]
    if d and sorted(d.get("pins", {})) == sorted(ids):
        return d["pins"]
    edb = opener()
    want = set(int(i) for i in ids)
    by_id = {v.GetId(): v for v in list(edb.active_layout.PadstackInstances) if v.GetId() in want}
    li = edb.active_layout.GetLayoutInstance()
    out = {}
    for iid in ids:
        bb = li.GetLayoutObjInstance(by_id[int(iid)], None).GetBBox()
        out[iid] = [[bb.Item1.X.ToDouble(), bb.Item1.Y.ToDouble()], [bb.Item2.X.ToDouble(), bb.Item2.Y.ToDouble()]]
    _wjson(path, {"refdes": refdes, "pins": out})
    return out


def need_window(idx, nets, comps, base_pts_mm, margin_m):
    """Cửa sổ cần (m): cửa sổ net ∪ vị trí pin linh kiện + 5 mm ∪ extent nền + 1.5 mm."""
    from .api import net_window
    w = [net_window(idx, sorted(nets), margin_m)]
    pos = {r[0]: (r[3], r[4]) for r in idx["insts"] if r[3] is not None}
    for rd in comps:
        pts = [pos[i] for i in (idx["comps"].get(rd) or {}).get("pins", []) if i in pos]
        if pts:
            w.append(K.window_of([(x, y, x, y) for x, y in pts], COMP_MARGIN_MM * MM))
    if base_pts_mm:
        xs, ys = [p[0] * MM for p in base_pts_mm], [p[1] * MM for p in base_pts_mm]
        w.append(K.window_of([(min(xs), min(ys), max(xs), max(ys))], EXTENT_MARGIN_MM * MM))
    return (min(b[0] for b in w), min(b[1] for b in w), max(b[2] for b in w), max(b[3] for b in w))


@contextlib.contextmanager
def open_for_preview(aedb, cell, P, nets, comps, version=None, log=None):
    """-> (SnapEdb, extent(factor), source). Board chỉ mở khi thiếu index / cửa sổ / extent / khung pin."""
    from .api import _Session, _defaults, _index, _window
    from .facade import SnapEdb
    log = log or (lambda *a: None)
    D = _defaults()
    cell = cell or ""
    t0 = time.perf_counter()
    key = K.board_key(aedb, cell)
    ses = _Session(aedb, cell, version or D["version"], log)

    def opener():
        try:
            return ses.open()
        except CopilotInputError as ex:
            if ex.name == "board" and ".lock" in str(ex.expected):
                raise SnapshotFallback(f"board open in AEDT, snapshot data must be read: {ex.got}")
            raise
    try:
        try:
            idx, ifolder, how_i = _index(ses, key, D["refs"], log)
        except CopilotInputError as ex:
            if ex.name == "board" and ".lock" in str(ex.expected):
                raise SnapshotFallback(f"board open in AEDT, snapshot must be built: {ex.got}")
            raise
        missing = [rd for rd in comps if rd not in idx["comps"]]
        if missing:
            raise SnapshotFallback(f"components not in the snapshot: {missing}")
        cache = ExtentCache(ifolder, P, nets, opener, log)
        base = cache.get(None)
        need = need_window(idx, nets, comps, base, D["margin_mm"] * MM)
        try:
            wf, r, how_w = _window(ses, idx, ifolder, key, need, D["arc_tol_um"], log)
        except CopilotInputError as ex:
            if ex.name == "board" and ".lock" in str(ex.expected):
                raise SnapshotFallback(f"board open in AEDT, snapshot window must be built: {ex.got}")
            raise
        bad = r[0]["unsupported"]
        if bad:
            raise SnapshotFallback("primitives that could not be converted in the preview window",
                                   [u["id"] for u in bad])
        pins = {}
        for rd in comps:
            pins.update(comp_pins(opener, idx, ifolder, rd))
        edb = SnapEdb(idx, r, extra_pin_bbox=pins)
        src = {"kind": "snapshot", "folder": wf, "index": how_i, "window": how_w, "extent_cache": cache,
               "window_mm": [round(v / MM, 3) for v in r[0]["window"]] if r[0].get("window") else None}
        yield edb, cache.get, src
        src["extent_cache"] = {"hits": cache.hits, "misses": cache.misses}
        src["board_opened"] = ses.edb is not None or getattr(ses, "open_s", None) is not None
        src["seconds"] = round(time.perf_counter() - t0, 2)
    finally:
        ses.close()
