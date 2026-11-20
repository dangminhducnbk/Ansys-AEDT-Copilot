"""API của layout snapshot (feature 023, contract: specs/023-layout-snapshot/contracts/layout-snapshot.md).

build / status / list_ : tool MCP layout_snapshot + CLI `snapshot`.
for_review             : review_checks dùng (dò channel trên index -> cửa sổ cần -> dùng lại / build -> SnapEdb).
Board không bao giờ bị ghi; chỉ ghi dưới <thư mục board>/Ansys AEDT Copilot/snapshots/.
"""
import fnmatch
import os
import time

from ..core.errors import CopilotInputError
from . import SnapshotFallback, key as K, store as S

OPS = ("build", "status", "list")
SCOPES = ("window", "board")
MM = 1e-3


def _defaults():
    from ..core import config as C
    from ..cut_board import config
    d = config.defaults()
    sn = d.get("snapshot") or {}
    return {"refs": list(d["cutout"]["reference_nets"]), "margin_mm": float(sn.get("window_margin_mm", 5)),
            "arc_tol_um": float(sn.get("arc_tol_um", 1)), "zoom_mm": float(d["review"]["zoom_margin_mm"]),
            "use": bool(d["review"].get("use_snapshot", True)), "version": C.machine()["aedt_version"],
            "use_region": bool(sn.get("use_for_region", True))}


def _aedb(board):
    from ..core.edb import aedb_path
    if not isinstance(board, str) or not board.strip():
        raise CopilotInputError("board", ".aedb / .aedt path", board)
    try:
        return aedb_path(board)
    except CopilotInputError:
        raise
    except Exception:
        raise CopilotInputError("board", "existing .aedb / .aedt", board)


def _nets_arg(nets):
    if nets in (None, "", []):
        return []
    if isinstance(nets, str):
        nets = [n.strip() for n in nets.split(",") if n.strip()]
    if not isinstance(nets, (list, tuple)) or not all(isinstance(n, str) and n for n in nets):
        raise CopilotInputError("nets", "comma separated net names / patterns", nets)
    return list(nets)


class _Session:
    """Mở EDB chỉ đọc khi cần build (một lần cho cả index + window)."""

    def __init__(self, aedb, cell, version, log):
        self.aedb, self.cell, self.version, self.log = aedb, cell, version, log
        self.edb, self.live = None, None

    def open(self):
        if self.edb is None:
            from ..cut_board import inspect_board
            K.check_board_lock(self.aedb)
            t0 = time.perf_counter()
            self.edb = inspect_board.open_edb(self.aedb, cell=self.cell or None, readonly=True, version=self.version)
            self.open_s = round(time.perf_counter() - t0, 2)
        return self.edb

    def close(self):
        if self.edb is not None:
            try:
                self.edb.close()
            finally:
                self.edb = None


def _index(ses, key, refs, log):
    """-> (index, folder, 'reused' | 'built')."""
    folder = K.index_dir(ses.aedb, key)
    idx = S.read_index(folder, key)
    if idx:
        return idx, folder, "reused"
    with S.build_lock(folder, log=log):
        idx = S.read_index(folder, key)                          # người khác vừa build xong
        if idx:
            return idx, folder, "reused"
        from .build import build_index
        edb = ses.open()
        log("[snapshot] building board index...")
        idx, ses.live = build_index(edb, key, refs, log)
        idx["cell_name"] = edb.active_cell.GetName()
        idx["times"]["open_edb"] = ses.open_s
        S.write_index(folder, idx)
    return idx, folder, "built"


def _find_window(folder, key, need, tol_um):
    """Cửa sổ hợp lệ nhỏ nhất chứa need (need None = cả board)."""
    best = None
    for w in S.windows(folder):
        r = S.read_window(w, key)
        if not r or abs(r[0].get("arc_tol_um", -1) - tol_um) > 1e-9:
            continue
        win = tuple(r[0]["window"]) if r[0].get("window") else None
        if not K.contains(win, need):
            continue
        area = float("inf") if win is None else (win[2] - win[0]) * (win[3] - win[1])
        if best is None or area < best[0]:
            best = (area, w, r)
    return (best[1], best[2]) if best else (None, None)


def _window(ses, idx, folder, key, need, tol_um, log, build_need=None):
    """-> (folder, (win, geom), 'reused' | 'built'). build_need (029): cửa sổ build khi không có cửa sổ chứa need;
    "board" = cả board (layout_region, clarify Q2 B: tìm theo box, thiếu -> build hình học cả board một lần)."""
    wf, r = _find_window(folder, key, need, tol_um)
    if r:
        return wf, r, "reused"
    if build_need is not None:
        need = None if build_need == "board" else build_need
    wf = os.path.join(folder, K.window_name(need))
    with S.build_lock(wf, log=log):
        r = S.read_window(wf, key)
        if r:
            return wf, r, "reused"
        from .build import build_index, build_window
        edb = ses.open()
        if ses.live is None:                                   # index có sẵn, phiên mới: lấy lại object .NET
            ses.live = {p.GetId(): p for p in list(edb.active_layout.Primitives) if p}
        log("[snapshot] building window geometry...")
        win, geom = build_window(edb, idx, ses.live, need, tol_um * 1e-6, log)
        S.write_window(wf, win, geom)
        r = (win, geom)
    return wf, r, "built"


def _match(idx, nets):
    names = idx["nets"]
    out = [n for n in names if any(n == p or fnmatch.fnmatchcase(n, p) for p in nets)]
    if not out:
        raise CopilotInputError("nets", "net names / patterns matching at least one net of the board", nets)
    return out


def net_window(idx, nets, margin_m):
    """bbox (m) của mọi primitive + via/pin của các net + margin."""
    ns = set(nets)
    bbs = [r[5] for r in idx["prims"] if r[3] in ns and r[5] and not r[4]]
    bbs += [(r[3], r[4], r[3], r[4]) for r in idx["insts"] if r[1] in ns and r[3] is not None]
    return K.window_of(bbs, margin_m)


def _report(idx, ifolder, wf, r, how_i, how_w, margin_mm, warnings):
    win, _ = r
    rep = {"folder": wf, "index_folder": ifolder, "board": idx["key"]["aedb"], "cell": idx.get("cell_name"),
           "scope": win["scope"], "window_mm": [round(v / MM, 3) for v in win["window"]] if win.get("window") else None,
           "margin_mm": margin_mm, "arc_tol_um": win["arc_tol_um"], "index": how_i, "window": how_w,
           "index_built_at": idx["built_at"], "window_built_at": win["built_at"],
           "counts": dict(win["counts"], board_primitives=len(idx["prims"]), board_instances=len(idx["insts"]),
                          components=len(idx["comps"])),
           "times": {"index": idx["times"], "window": win["times"]},
           "unsupported": win["unsupported"], "warnings": warnings, "size_mb": S.folder_mb(wf)}
    return rep


# ----------------------------------------------------------------------------- public
def build(aedb, cell="", nets=None, scope="window", margin_mm=None, version=None, log=None):
    log = log or (lambda *a: None)
    aedb = _aedb(aedb)
    if scope not in SCOPES:
        raise CopilotInputError("scope", " / ".join(SCOPES), scope)
    nets = _nets_arg(nets)
    if scope == "window" and not nets:
        raise CopilotInputError("nets", "at least one net / pattern (or scope=board)", nets)
    D = _defaults()
    if margin_mm in (None, 0, ""):
        margin_mm = D["margin_mm"]
    if not isinstance(margin_mm, (int, float)) or margin_mm < 0:
        raise CopilotInputError("margin_mm", ">= 0", margin_mm)
    cell = cell or ""
    key = K.board_key(aedb, cell)
    ses = _Session(aedb, cell, version or D["version"], log)
    t0 = time.perf_counter()
    try:
        idx, ifolder, how_i = _index(ses, key, D["refs"], log)
        need = None if scope == "board" else net_window(idx, _match(idx, nets), margin_mm * MM)
        wf, r, how_w = _window(ses, idx, ifolder, key, need, D["arc_tol_um"], log)
    finally:
        ses.close()
    rep = _report(idx, ifolder, wf, r, how_i, how_w, margin_mm, [])
    rep["seconds"] = round(time.perf_counter() - t0, 2)
    if how_w == "built" or how_i == "built":
        S.write_report(wf, rep)
    return rep


def status(aedb, cell="", nets=None, scope="window", margin_mm=None):
    aedb = _aedb(aedb)
    if scope not in SCOPES:
        raise CopilotInputError("scope", " / ".join(SCOPES), scope)
    nets = _nets_arg(nets)
    D = _defaults()
    margin_mm = D["margin_mm"] if margin_mm in (None, 0, "") else margin_mm
    if not isinstance(margin_mm, (int, float)) or margin_mm < 0:
        raise CopilotInputError("margin_mm", ">= 0", margin_mm)
    key = K.board_key(aedb, cell or "")
    folder = K.index_dir(aedb, key)
    idx = S.read_index(folder, key)
    if not idx:
        others = [x for x in list_(aedb) if x["cell"] == (cell or "")]
        return {"state": "stale" if others else "missing", "index_folder": folder,
                "other_snapshots": [x["folder"] for x in others]}
    need = None if scope == "board" or not nets else net_window(idx, _match(idx, nets), margin_mm * MM)
    if scope == "window" and not nets:
        return {"state": "valid", "index_folder": folder, "windows": len(S.windows(folder))}
    wf, r = _find_window(folder, key, need, D["arc_tol_um"])
    if not r:
        return {"state": "too_small" if S.windows(folder) else "missing", "index_folder": folder}
    return {"state": "valid", "folder": wf, "report": S.read_report(wf)}


def list_(aedb):
    aedb = _aedb(aedb)
    base = K.root(aedb)
    out = []
    try:
        names = sorted(os.listdir(base))
    except OSError:
        return out
    for n in names:
        f = os.path.join(base, n)
        d = S._rjson(os.path.join(f, S.INDEX)) or {}
        k = d.get("key") or {}
        try:
            valid = bool(k) and k == K.board_key(aedb, k.get("cell", ""))
        except CopilotInputError:
            valid = False
        for w in S.windows(f) or [None]:
            wd = S._rjson(os.path.join(w, S.WINDOW)) if w else {}
            wd = wd or {}
            out.append({"folder": w or f, "cell": k.get("cell", ""), "valid": valid,
                        "scope": wd.get("scope"), "built_at": wd.get("built_at") or d.get("built_at"),
                        "window_mm": [round(v / MM, 3) for v in wd["window"]] if wd.get("window") else None,
                        "size_mb": S.folder_mb(w or f)})
    return out


def run_op(op, args, log=None):
    """CLI `snapshot --op=` (args dict)."""
    if op not in OPS:
        raise CopilotInputError("op", " / ".join(OPS), op)
    a = dict(args or {})
    board = a.pop("board", None) or a.pop("aedb", None)
    if op == "list":
        return {"snapshots": list_(board)}
    kw = {k: a[k] for k in ("cell", "nets", "scope", "margin_mm") if k in a}
    if op == "status":
        return status(board, **kw)
    return build(board, log=log, **kw)


def for_review(aedb, cell, specs, version=None, log=None):
    """-> (SnapEdb, source). SnapshotFallback khi không dùng được (board khoá cần build, primitive không chuyển được)."""
    from ..cut_board import inspect_board
    from .facade import SnapEdb
    log = log or (lambda *a: None)
    D = _defaults()
    cell = cell or ""
    key = K.board_key(aedb, cell)
    margin_mm = max(D["margin_mm"], 1 + D["zoom_mm"] + 2 + 0.01)     # >= cửa sổ đồng của review (Copper)
    ses = _Session(aedb, cell, version or D["version"], log)
    t0 = time.perf_counter()
    try:
        try:
            idx, ifolder, how_i = _index(ses, key, D["refs"], log)
            lean = SnapEdb(idx, None, lenient=True)
            nets = set()
            for s in specs:
                try:
                    nets |= set(inspect_board.trace_channel(lean, s["comp_a"], s["comp_b"],
                                                            list(s.get("patterns") or []), idx["refs"])["nets"])
                except Exception:
                    pass                                            # measure báo lỗi channel như live
            if not nets:
                return SnapEdb(idx, None), {"kind": "snapshot", "folder": ifolder, "index": how_i, "window": None,
                                            "seconds": round(time.perf_counter() - t0, 2)}
            need = net_window(idx, sorted(nets), margin_mm * MM)
            wf, r, how_w = _window(ses, idx, ifolder, key, need, D["arc_tol_um"], log)
        except CopilotInputError as ex:
            if ex.name == "board" and ".lock" in ex.expected:
                raise SnapshotFallback(f"board open in AEDT, snapshot must be built: {ex.got}")
            raise
    finally:
        ses.close()
    bad = r[0]["unsupported"]                                   # Q3 = A: cả review chạy live, nêu id
    if bad:
        raise SnapshotFallback("primitives that could not be converted in the review window", [u["id"] for u in bad])
    src = {"kind": "snapshot", "folder": wf, "index": how_i, "window": how_w, "arc_tol_um": r[0]["arc_tol_um"],
           "window_mm": [round(v / MM, 3) for v in r[0]["window"]] if r[0].get("window") else None,
           "seconds": round(time.perf_counter() - t0, 2)}
    if how_w == "built" or how_i == "built":
        S.write_report(wf, _report(idx, ifolder, wf, r, how_i, how_w, margin_mm, []))
    return SnapEdb(idx, r), src
