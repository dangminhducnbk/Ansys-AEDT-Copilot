"""Review layout: code đo, agent diễn giải (feature 011, contract: review-checks.md).

Mỗi phép kiểm tra = một module trong registry (NAME, ORDER, TITLE, RULE, run(cc) -> {items, data}):
reference, trace_stubs, vias, routing. Hàm đo là của cut_board/review.py (không đổi) nên số liệu giống hệt
review_layout; thứ tự, id và cách gộp điểm cũng như review.review(). Thêm check = thêm một file.
036: item có status OK / NOT OK theo ngưỡng của luật (RULE = câu 'not ok when' của steering); không có mức nặng nhẹ.
"""
import difflib

from ..core.errors import CopilotInputError
from . import _report

PACKAGE = __name__


# 031: tên check cũ (trước khi tách mỗi luật một file) -> các luật mới (design_review checks="reference" vẫn chạy)
ALIASES = {"reference": ("sov", "ref_other_net", "loss_of_reference", "via_clearance"),
           "vias": ("ref_plane_change", "via_stub", "nearest_gnd_via")}


def checks():
    """Luật có code: của team (module trong package) + luật cá nhân ĐÃ BẬT (031; trùng id -> của team)."""
    from ..core import registry
    from . import _rules
    reg = registry.by_name(registry.load(PACKAGE, ("NAME", "ORDER", "TITLE", "RULE", "run")))
    for m in _rules.personal_modules():
        if m.NAME not in reg and all(hasattr(m, a) for a in ("NAME", "ORDER", "TITLE", "run")) and \
                (hasattr(m, "RULE") or hasattr(m, "SEVERITY_RULE")):                 # luật cá nhân cũ (trước 036)
            if not hasattr(m, "RULE"):
                m.RULE = m.SEVERITY_RULE
            reg[m.NAME] = m
    return dict(sorted(reg.items(), key=lambda kv: (kv[1].ORDER, kv[0])))


def select(names=None):
    reg = checks()
    if names in (None, "", []):
        return list(reg)
    if isinstance(names, str):
        names = [x.strip() for x in names.split(",") if x.strip()]
    if not isinstance(names, (list, tuple)) or not names:
        raise CopilotInputError("checks", "check names (comma separated) or empty = all", names)
    names = [x for n in names for x in ALIASES.get(n, (n,))]
    bad = [n for n in names if n not in reg]
    if bad:
        raise CopilotInputError("checks", "one of " + ", ".join(reg) + "; closest: " +
                                ", ".join(difflib.get_close_matches(bad[0], list(reg), 3, 0.3) or list(reg)), bad)
    return [n for n in reg if n in names]                                # thứ tự registry


def specs_of(channels):
    from ..cut_board import naming
    specs = naming.parse_request(channels) if isinstance(channels, str) else channels
    if not specs:
        raise CopilotInputError("channels", "'A-B:pattern,...; C-D:...' (at least one)", channels)
    for s in specs:
        if not s.get("comp_a") or not s.get("comp_b"):
            raise CopilotInputError("channels", "each channel 'CompA-CompB:pattern'", s)
    return specs


def measure_edb(edb, specs, names, log=None, board=None):
    """Đo trên edb đã mở (chỉ đọc). -> (plane_layers, [channel])."""
    from ..cut_board import naming
    from ..cut_board import review as RV
    from ._context import ChannelCtx, Ctx
    reg = checks()
    ctx = Ctx(edb, log, board)
    chans, taken = [], set()
    for s in specs:
        ci = len(chans) + 1                                              # như review.review(): tính cả channel lỗi
        ch = {"comp_a": s["comp_a"], "comp_b": s["comp_b"], "patterns": list(s.get("patterns") or []),
              "checks": {}, "items": [], "points": [], "warnings": []}
        cc = ChannelCtx(ctx, ch)
        try:
            t = cc.trace
        except Exception as ex:
            ch.update(name=s.get("name") or f"{s['comp_a']}_{s['comp_b']}", error=str(ex))
            chans.append(ch)
            continue
        nm = s.get("name") or naming.default_name(s["comp_a"], s["comp_b"], t["nets"])
        ch["name"] = naming.unique_name(nm, taken)
        taken.add(ch["name"].lower())
        ch.update(nets=t["nets"], series=sorted(t["series"]), end_types=t["end_types"], warnings=t["warnings"])
        if not t["nets"]:
            ch["error"] = "No net connects the two components"
            chans.append(ch)
            continue
        fs = []
        for n in names:
            try:
                r = reg[n].run(cc)
                fs += r["items"]
                ch["checks"][n] = {"items": len(r["items"]), "data": r.get("data") or {}}
            except Exception as ex:                                      # check lỗi không chặn check khác
                ch["checks"][n] = {"error": str(ex) or type(ex).__name__}
        fs.sort(key=lambda f: (RV.STATUS_ORDER[f["status"]], f["check"], f["net"], f["x"]))
        for i, f in enumerate(fs, 1):
            f["id"] = f"{ci}.{i}"
        pts = RV.points(fs, ci)
        ch["items"] = [_report.item(f) for f in fs]
        ch["points"] = [_report.point(p) for p in pts]
        ch["built"] = cc.built()
        chans.append(ch)
    planes = ctx._B.planes if ctx._B is not None else None
    for ch in chans:
        ch["summary_md"] = _report.summary_md(ch)
    return planes, chans


SNAPSHOT_MODES = ("auto", "off")


def _live(aedb, specs, names, cell, version, log):
    from ..cut_board import config, inspect_board
    edb = inspect_board.open_edb(aedb, cell=cell or None, readonly=True,
                                 version=version or config.machine()["aedt_version"])
    try:
        cell = edb.active_cell.GetName()
        planes, chans = measure_edb(edb, specs, names, log, aedb)
    finally:
        edb.close()
    return cell, planes, chans


def measure_channels(board, specs, checks_=None, cell="", version=None, log=None, snapshot="auto"):
    """023: snapshot 'auto' + template review.use_snapshot -> đo trên layout snapshot (dựng / dùng lại), kết quả như
    live; 'off' hoặc use_snapshot=false -> đọc EDB live như trước. Snapshot không dùng được -> live + cảnh báo."""
    import time

    from ..cut_board import config, naming
    if snapshot not in SNAPSHOT_MODES:
        raise CopilotInputError("snapshot", " / ".join(SNAPSHOT_MODES), snapshot)
    names = select(checks_)
    specs = specs_of(specs)
    aedb, _ = naming.board_paths(board)
    use = snapshot == "auto" and bool(config.defaults()["review"].get("use_snapshot", True))
    source = {"kind": "live"}
    planes = chans = None
    if use:
        from .. import layout_snapshot as LS
        from ..layout_snapshot import api as LSA
        t0 = time.perf_counter()
        try:
            edb, source = LSA.for_review(aedb, cell, specs, version, log)
            cell = edb.active_cell.GetName()
            planes, chans = measure_edb(edb, specs, names, log, aedb)
            source["measure_s"] = round(time.perf_counter() - t0 - source["seconds"], 2)
        except (LS.SnapshotFallback, LS.SnapshotMissing) as ex:
            ids = getattr(ex, "ids", [])
            source = {"kind": "live", "warning": f"layout snapshot not used ({ex}); measured live" +
                      (f"; primitive ids {ids[:20]}" if ids else "")}
            planes = chans = None
    if chans is None:
        t0 = time.perf_counter()
        cell, planes, chans = _live(aedb, specs, names, cell, version, log)
        source["seconds"] = round(time.perf_counter() - t0, 2)
    return {"board": aedb, "cell": cell, "plane_layers": planes, "checks_run": names,
            "checks_available": {n: {"title": m.TITLE, "not_ok_when": m.RULE} for n, m in checks().items()},
            "channels": chans, "summary_md": "\n\n".join(c["summary_md"] for c in chans), "source": source}


def measure(board, channels, checks_=None, cell="", version=None, log=None, snapshot="auto"):
    return measure_channels(board, channels, checks_, cell, version, log, snapshot)


def record_key(board, cell=""):
    """025: khoá board (023) lấy TRƯỚC khi đo."""
    from ..cut_board import naming
    from ..layout_snapshot import key as K
    aedb, _ = naming.board_paths(board)
    return K.board_key(aedb, cell or "")


def current_thresholds(board=None):
    """Ngưỡng review.* (+ 030: mã bảng stackup của board) = phần khoá của bản ghi review (025): đổi -> đo lại."""
    from ..cut_board import config
    from . import _stackup, _verdict as verdict
    thr = verdict.thresholds(config.defaults()["review"])
    if board:
        from ..cut_board import naming
        try:
            h = _stackup.table_hash(naming.board_paths(board)[0])
        except Exception:
            h = None
        if h:
            thr["stackup_table"] = h
    return thr


def save_record(out, cell, source, board_key, board=None):
    """Ghi bản ghi review (store.save); không ghi được -> kết quả đo vẫn trả về + cảnh báo."""
    from . import _store as store
    try:
        out["review_file"] = store.save(out, cell or "", source, board_key, current_thresholds(board))
    except OSError as ex:
        store.annotate(out, board_key, cell or "", current_thresholds(board))
        out["review_file"] = None
        out.setdefault("warnings", []).append(f"review record not written: {ex}")
    return out


def measure_report(board, channels, checks_=None, cell="", html=False, log=None, snapshot="auto"):
    """measure + (html=True) báo cáo HTML layout review (review.review LIVE ở phase 1; lệnh CLI review-measure).
    025: ghi bản ghi review cạnh board (số điểm từng channel, dùng lại được cho interface simulation; 035: không
    kết luận)."""
    select(checks_)                                                      # đầu vào sai báo trước khoá board (như 2.2)
    specs_of(channels)
    key0 = record_key(board, cell)
    out = measure(board, channels, checks_, cell, log=log, snapshot=snapshot)
    save_record(out, cell, "standalone", key0, board)
    if html:
        from ..cut_board import review
        out["html"] = review.review(board, channels, cell or None, log=log, snapshot=snapshot)["html"]
    return out
