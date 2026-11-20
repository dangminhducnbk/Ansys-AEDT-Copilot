"""Cut lại interface "như lần trước" (feature 004, contract: isim-recut.md).

previous(): tìm các lần chạy cũ của interface cho cùng workspace (registry). source(): đọc lần chạy cũ (request id,
thư mục request, hoặc file user_settings.json - kể cả copy từ máy khác; request 0.6.0 đọc từ state.json).
start(): trace lại trên board hiện tại với 2 đầu + net cũ, chỉ báo KHÁC BIỆT, đề xuất nội dung cũ -> gate A như 003.
"""
import os

from ..core.errors import CopilotInputError
from ..core.validate import require_path
from . import report, request as R
from . import user_settings as U

from .defaults_history import HISTORY, ver as _ver

# khoá template thêm sau 0.6.0: với lần chạy cũ hơn thì ghi nguồn "team default (new)" (009: từ lịch sử mặc định)
ADDED_IN = {k: h[0][0] for k, h in HISTORY.items()}


def _doc_of_folder(f):
    p = os.path.join(f, R.WORK, U.FILE)                                # 038
    if not os.path.isfile(p):
        p = os.path.join(f, U.FILE)
    return U.load(p) if os.path.isfile(p) else U.from_state(f)


def _sweep(sec):
    v = sec.get("values") or {}
    keys = ("sweep.start_ghz", "sweep.stop_ghz", "sweep.step_ghz")
    return {k.split(".")[1]: v.get(k) for k in keys} if any(k in v for k in keys) else None


# ----------------------------------------------------------------------------- tìm lần chạy cũ
def previous(name, workspace=""):
    """-> [{request_id, created, workspace, interface, last_step, failed, sweep, source, path}] mới nhất trước."""
    name = R.check_name(name)
    if workspace:
        ws = require_path("workspace", workspace, "file")
    else:
        ws = R.load("")["workspace"]
    ws = R.norm_path(ws)
    out = []
    for e in R.registry():
        f = e["folder"]
        req = R.read_folder(f) or {}                                    # 038: request.json trong _work/
        if R.norm_path(e.get("workspace") or req.get("workspace") or "") != ws:
            continue
        hit = next((n for n in req.get("interfaces") or [] if n.lower() == name.lower()), None)
        if not hit:
            continue
        st = R._rjson(os.path.join(R.iface_dir_of(req, hit), "state.json")) or {}
        usp = os.path.join(req.get("work") or f, U.FILE)
        has_us = os.path.isfile(usp)
        sec = {}
        if has_us:
            sec = (R._rjson(usp) or {}).get("interfaces", {}).get(hit) or {}
        else:
            sec = {"values": (st.get("settings") or {}).get("values")}
        out.append({"request_id": req.get("request_id") or e["request_id"], "created": req.get("created"),
                    "workspace": req.get("workspace"), "interface": hit, "last_step": st.get("step"),
                    "failed": bool(st.get("failed")), "error": st.get("error") if st.get("failed") else None,
                    "sweep": _sweep(sec),
                    "source": "user_settings" if has_us else "state", "path": f})
    out.sort(key=lambda r: (str(r["created"]), str(r["request_id"])), reverse=True)
    return out


def previous_md(runs):
    return report.table(["#", "Request", "Created", "Interface", "Last step", "Sweep start / stop / step (GHz)", "Error"],
                        [[i + 1, r["request_id"], r["created"], r["interface"],
                          r["last_step"] + (" (failed)" if r["failed"] else ""),
                          " / ".join(str((r["sweep"] or {}).get(k)) for k in ("start_ghz", "stop_ghz", "step_ghz"))
                          if r["sweep"] else "-", (r.get("error") or "")[:120]] for i, r in enumerate(runs)])


def source(src, name=""):
    """src = request id | thư mục request | file user_settings.json. -> {doc, interface, section, origin}."""
    s = str(src or "").strip().strip('"')
    if not s:
        raise CopilotInputError("source", "request id, request folder or user_settings.json path", src)
    if os.path.isfile(s):
        doc = U.load(s)
    elif os.path.isdir(s):
        doc = _doc_of_folder(s)
    else:
        doc = _doc_of_folder(R.folder(s))                              # request id (lỗi rõ nếu không có)
    names = list(doc["interfaces"])
    if name:
        hit = next((n for n in names if n.lower() == name.lower()), None)
        if hit is None and len(names) == 1:
            hit = names[0]                                             # đổi tên interface khi cut lại
        if hit is None:
            raise CopilotInputError("name", "interface of the previous run: " + ", ".join(names), name)
    elif len(names) == 1:
        hit = names[0]
    else:
        raise CopilotInputError("name", "one of " + ", ".join(names), name)
    sec = doc["interfaces"][hit]
    origin = {"request_id": doc.get("request_id"), "interface": hit, "path": doc.get("path"),
              "tool_version": doc.get("tool_version")}
    return {"doc": doc, "interface": hit, "section": sec, "origin": origin,
            "dropped": (doc.get("dropped") or {}).get(hit, [])}


# ----------------------------------------------------------------------------- so sánh (thuần)
def diff(old, old_facts, old_fp, new, new_facts, new_fp, missing_nets=(), old_sch=(), new_sch=()):
    """old / new = content (comp_a, comp_b, nets, diff_groups, series). -> [{item, ref, old, new, resolution}]."""
    out = []

    def add(item, ref, o, n):
        out.append({"item": item, "ref": ref, "old": o, "new": n, "resolution": ""})
    oc = (old_facts or {}).get("components") or {}
    nc = (new_facts or {}).get("components") or {}
    for role in ("comp_a", "comp_b"):
        rd = old.get(role)
        if rd not in nc:
            add("end_missing", rd, "present", None)
        elif rd in oc and oc[rd].get("signal_pins") != nc[rd].get("signal_pins"):
            add("end_pins_changed", rd, oc[rd].get("signal_pins"), nc[rd].get("signal_pins"))
    on, nn = set(old.get("nets") or []), set(new.get("nets") or [])
    for n in sorted(on - nn):
        add("net_removed", n, "in interface", "not found" if n in set(missing_nets) else "not on this path")
    for n in sorted(nn - on):
        add("net_added", n, None, "on this path")
    os_, ns = set(old.get("series") or {}), set(new.get("series") or {})
    for rd in sorted(os_ - ns):
        add("series_removed", rd, "series part", None)
    for rd in sorted(ns - os_):
        add("series_added", rd, None, "series part")
    for rd in sorted(os_ & ns):
        ov, nv = (oc.get(rd) or {}).get("value"), (nc.get(rd) or {}).get("value")
        if rd in oc and ov != nv:
            add("series_value_changed", rd, ov, nv)
    keep = on & nn
    og = sorted(sorted(g) for g in old.get("diff_groups") or [] if set(g) <= keep)
    ng = sorted(sorted(g) for g in new.get("diff_groups") or [] if set(g) <= keep)
    if og != ng:
        add("diff_group_changed", "diff_groups", og, ng)
    if old_fp and new_fp and old_fp != new_fp:
        add("board_file_changed", "edb.def", old_fp, new_fp)
    now = {(d["item"], d.get("kind")) for d in new_sch or []}
    for d in old_sch or []:
        if d.get("resolution") and (d["item"], d.get("kind")) not in now:
            add("schematic_resolution_stale", d["item"], d.get("resolution"), "difference gone")
    return out


def compare_handling(old_handling, ends):
    """old_handling {refdes: option}, ends {refdes: {unusual: [{rule, options}]}} -> [{refdes, old, new_rules,
    result: kept | not_needed | needs_choice, options}]."""
    old_handling = old_handling or {}
    out = []
    for rd, e in sorted((ends or {}).items()):
        un = list(e.get("unusual") or [])
        if e.get("default_handling"):                                  # 012: đầu connector có mặc định team
            un.append(e["default_handling"])
        rules = [u["rule"] for u in un]
        opts = sorted({o for u in un for o in u.get("options") or []})
        old = old_handling.get(rd)
        if "no_gnd_pin" in rules:                                      # 015: không dùng lại âm thầm - hỏi lại
            ng = next(u for u in un if u["rule"] == "no_gnd_pin")
            label = "gnd_plate_vias (smd_rebuild)" if old == "smd_rebuild" else old
            out.append({"refdes": rd, "old": old, "new_rules": rules, "result": "needs_confirm",
                        "options": list(ng.get("options") or []), "previous": label,
                        "image": (ng.get("values") or {}).get("image")})
            continue
        if rules:
            res = "kept" if old in opts else "needs_choice"
        elif old:
            res = "not_needed"
        else:
            continue
        out.append({"refdes": rd, "old": old, "new_rules": rules, "result": res, "options": opts})
    for rd in sorted(set(old_handling) - set(ends or {})):
        out.append({"refdes": rd, "old": old_handling[rd], "new_rules": [], "result": "not_needed",
                    "options": [], "note": "not an end of this cut"})
    return out


END_GND_SINCE = (2, 1, 0)                                              # 022: luật GND ở 2 đầu khi cắt


def method_diffs(tool_version):
    """022: lần chạy cũ cắt trước 2.1.0 -> 1 khác biệt 'cut_method_changed' (kỹ sư ghi resolution ở Gate A). Thuần."""
    if _ver(tool_version) >= END_GND_SINCE:
        return []
    return [{"item": "cut_method_changed", "ref": "end GND rule 2.1.0", "resolution": "",
             "old": "one factor for the whole extent",
             "new": "an end that loses all its GND pins gets its region enlarged (shown after the cut)"}]


def previous_stage1(origin):
    """stage1.json của lần chạy cũ (origin = recut_from: path, interface) -> dict hoặc None."""
    op_ = (origin or {}).get("path") or ""
    base = op_ if os.path.isdir(op_) else os.path.dirname(op_)
    if not base or not (origin or {}).get("interface"):
        return None
    return R._rjson(os.path.join(base, origin["interface"], "stage1.json"))


def compare_end_gnd(old_s1, new_s1):
    """-> [{refdes, previous, now, result: same | enlarged | changed}] mỗi đầu của lần cắt mới. Thuần."""
    from ..cut_board import end_gnd as EG
    out = []
    for rd in (new_s1 or {}).get("ends") or []:
        o, n = EG.end_entry(old_s1, rd), EG.end_entry(new_s1, rd)
        of = o.get("factor") if o.get("result") != "cut_before_2.1.0" else None
        if n.get("result") == "enlarged" and (o.get("result") != "enlarged" or of != n.get("factor")):
            res = "enlarged"
        elif (o.get("result"), of) == (n.get("result"), n.get("factor")) or                 (o.get("result") == "cut_before_2.1.0" and n.get("result") == "met"):
            res = "same"
        else:
            res = "changed"
        out.append({"refdes": rd, "previous": EG.text(o),
                    "now": EG.text(n), "result": res})
    return out


def handling_md(rows):
    return report.table(["Refdes", "Old handling", "Unusual now", "Result", "Options"],
                        [[r["refdes"], r["old"] or "-", ", ".join(r["new_rules"]) or "-", r["result"],
                          ", ".join(r["options"])] for r in rows]) if rows else "No end handling to compare."


def setting_source(key, previous_id, tool_version):
    """Nhãn cột Source của bảng settings khi cut lại."""
    if key in ADDED_IN and _ver(tool_version) < ADDED_IN[key]:
        return "team default (new)"
    return f"previous run {previous_id}"


# ----------------------------------------------------------------------------- bắt đầu cut lại
def start(request_id, name, source_ref, nets=None, version=None):
    from . import content as C
    if nets is not None and (not isinstance(nets, (list, tuple)) or
                             not all(isinstance(n, str) and n.strip() for n in nets)):
        raise CopilotInputError("nets", "list of net names / patterns (or empty = as last time)", nets)
    req = R.load(request_id)
    rid = req["request_id"]
    src = source(source_ref, name)
    if src["origin"]["request_id"] == rid:
        raise CopilotInputError("request_id", "a NEW request (isim_start) - never re-cut into the previous one", rid)
    name = R.check_name(name or src["interface"])
    st_path = os.path.join(R.iface_dir_of(req, name), "state.json")
    if os.path.isfile(st_path) and (R._rjson(st_path) or {}).get("step") not in (None, "started"):
        raise CopilotInputError("name", "interface not started yet in this request", name)
    sec = src["section"]
    old = sec.get("content")
    if not old:
        raise CopilotInputError("source", "previous run with agreed content (gate A passed)", src["origin"])
    old = dict(old, structural=sec.get("structural") or {})
    targs = sec.get("trace_args") or {}
    pats = list(nets) if nets else (targs.get("nets") or list(old["nets"]))
    prev_err = None
    op_ = src["origin"].get("path") or ""
    base = op_ if os.path.isdir(op_) else os.path.dirname(op_)        # file user_settings.json -> thư mục request
    if base:
        ost = R._rjson(os.path.join(base, src["interface"], "state.json")) or {}
        prev_err = ost.get("error") if ost.get("failed") else None
    try:
        r = C.trace(rid, name, [old["comp_a"], old["comp_b"]], pats, version, missing_ok=True)
    except CopilotInputError as ex:
        if ex.name != "refdes":
            raise
        # đầu cũ không còn trên board: báo khác biệt, không trace / cắt; người dùng chọn đầu mới (isim_trace)
        d = [{"item": "end_missing", "ref": ex.got, "old": "present", "new": None, "resolution": "",
              "detail": str(ex)}]
        return {"request_id": rid, "name": name, "blocked": True, "recut_from": src["origin"], "recut_diffs": d,
                "previous_error": prev_err, "old_values": sec.get("values") or {},
                "old_handling": sec.get("handling") or {},
                "content_md": "\n".join([
                    f"# Interface {name} - re-cut from {src['origin']['request_id']}", "",
                    "## Changes since previous run",
                    report.table(["Item", "Ref", "Old", "New", "Detail"],
                                 [["end_missing", ex.got, "present", "-", str(ex)]]), "",
                    "Blocked: choose the new end with the user, then isim_trace."])}
    st = R.get_state(rid, name)
    new = r["proposal"]
    facts = st.get("board_facts") or {}
    diffs = diff(old, sec.get("board_facts"), src["doc"].get("board_fingerprint"), new, facts,
                 U.board_fingerprint(req["board"]), r.get("missing_nets") or [], old.get("schematic_diffs"),
                 r["schematic_diffs"]) + method_diffs(src["origin"].get("tool_version"))
    keep = set(old["nets"]) & set(new["nets"])
    ores = {(d["item"], d.get("kind")): d.get("resolution") for d in old.get("schematic_diffs") or []}
    prop = {"comp_a": old["comp_a"], "comp_b": old["comp_b"], "nets": sorted(keep),
            "diff_groups": [g for g in old.get("diff_groups") or [] if set(g) <= keep],
            "series": {rd: v for rd, v in (old.get("series") or {}).items() if rd in (new.get("series") or {})},
            "schematic_diffs": [dict(d, resolution=ores.get((d["item"], d.get("kind"))) or "")
                                for d in r["schematic_diffs"]],
            "structural": old["structural"], "recut_diffs": diffs,
            **({"end_factors": {rd: f for rd, f in old["end_factors"].items() if rd in (old["comp_a"], old["comp_b"])}}
               if old.get("end_factors") else {})}
    recut_old = {"values": sec.get("values") or {}, "handling": sec.get("handling") or {},
                 "dropped": src["dropped"], "tool_version": src["origin"].get("tool_version")}
    R.set_state(rid, name, "re-cut from " + str(src["origin"]["request_id"]), recut_from=src["origin"],
                recut_diffs=diffs, recut_old=recut_old, proposal=prop)
    md = C.content_md(name, prop, facts, prop["schematic_diffs"], r["end_types"],
                      title=f"Re-cut proposal from {src['origin']['request_id']} (not agreed)")
    return dict(r, proposal=prop, content_md=md, recut_from=src["origin"], recut_diffs=diffs, previous_error=prev_err,
                old_values=recut_old["values"], old_handling=recut_old["handling"], dropped=src["dropped"],
                previous_review=previous_review(sec))


def previous_review(sec):
    """Review của lần trước (chỉ để HIỂN THỊ): lời đồng ý (035) hoặc override / quyết định cũ (2.12.0). KHÔNG dùng lại:
    re-cut chạy isim_review, gửi report và hỏi kỹ sư đồng ý lại (GATE A)."""
    rv = (sec or {}).get("review") or {}
    if not rv:
        return None
    ov = rv.get("override") or None
    ap = rv.get("approval") or None
    return {"measured_at": rv.get("measured_at"),
            "approval": {"time": ap.get("time"), "report": ap.get("report"), "counts": ap.get("counts")} if ap else None,
            "override_2_12": {"reason": ov.get("reason"), "time": ov.get("time")} if ov else None,
            "note": "shown only; never reused - send the new report and ask the engineer again"}
