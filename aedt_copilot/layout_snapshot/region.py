"""layout_region trên layout snapshot (feature 029, contract: specs/029-layout-region-snapshot/contracts/region-snapshot.md).

edit_layout/extract.extract_region chạy KHÔNG đổi trên SnapEdb(region=True): điểm gốc EDB (cả cung) đổi cung như
PyEDB points() -> region.json giống live từng số (Q1 A). Cửa sổ: cửa sổ đã có chứa box (cả của review / preview) ->
dùng lại; không có -> build hình học CẢ BOARD một lần (Q2 B), mọi box sau dùng lại. Board có .lock: snapshot hợp lệ vẫn
dùng; cần build -> SnapshotFallback (Q3 A).
"""
import time

from ..core.errors import CopilotInputError
from . import SnapshotFallback, key as K, store as S

MM = 1e-3


def open_for_region(aedb, cell, bbox_mm, build=True, version=None, log=None):
    """bbox_mm [x0, y0, x1, y1] -> (SnapEdb, source). build=False: chỉ dùng cửa sổ đã có (layout_edit 'before').
    SnapshotFallback khi không dùng được (lý do trong .reason)."""
    from .api import _Session, _defaults, _find_window, _index, _report, _window
    from .facade import SnapEdb
    log = log or (lambda *a: None)
    D = _defaults()
    cell = cell or ""
    t0 = time.perf_counter()
    key = K.board_key(aedb, cell)
    box = tuple(float(v) * MM for v in bbox_mm)
    tol = D["arc_tol_um"]
    if not build:
        folder = K.index_dir(aedb, key)
        idx = S.read_index(folder, key)
        if not idx:
            raise SnapshotFallback("no valid snapshot of the board (not built, or the board changed)")
        wf, r = _find_window(folder, key, box, tol)
        if not r:
            raise SnapshotFallback("no snapshot window contains the region")
        how_i = how_w = "reused"
    else:
        ses = _Session(aedb, cell, version or D["version"], log)
        try:
            idx, folder, how_i = _index(ses, key, D["refs"], log)
            wf, r, how_w = _window(ses, idx, folder, key, box, tol, log, build_need="board")
        except CopilotInputError as ex:
            if ex.name == "board" and ".lock" in str(ex.expected):
                raise SnapshotFallback(f"board open in AEDT, snapshot must be built: {ex.got}")
            raise
        finally:
            ses.close()
        if how_w == "built" or how_i == "built":
            S.write_report(wf, _report(idx, folder, wf, r, how_i, how_w, D["margin_mm"], []))
    snap = SnapEdb(idx, r, region=True)
    src = {"kind": "snapshot", "folder": wf, "index": how_i, "window": how_w,
           "window_mm": [round(v / MM, 3) for v in r[0]["window"]] if r[0].get("window") else None,
           "seconds": round(time.perf_counter() - t0, 2)}
    return snap, src
