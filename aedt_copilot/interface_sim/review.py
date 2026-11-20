"""Review layout của interface — bước BẮT BUỘC ngay sau isim_trace, trước GATE A (025; 035: kỹ sư duyệt report).

run(): đo (review_checks) với 2 đầu + net của đề xuất (hoặc nội dung đã chốt) -> <interface>/review.json + bản ghi
       cạnh board (reviews/) + LUÔN báo cáo HTML (035) để gửi kỹ sư đọc; dùng lại bản ghi còn hợp lệ (board không đổi,
       cùng 2 đầu / net / check / ngưỡng).
gate_status(): not_reviewed / out_of_date / no_report / ready (report có, chưa duyệt) / approved.
approve(): GATE A (isim_confirm_content) ghi lời đồng ý của kỹ sư (sau khi đọc report + vùng cut) vào user_settings
           'review.approval', gắn với measured_at của review. Cut cần 'approved'.
035 (user 2026-11-14): không còn quyết định từng điểm / override. 036: không còn mức nặng nhẹ — mỗi luật OK / NOT OK
theo ngưỡng; số liệu = số điểm NOT OK (+ theo check). Quyết định cut 100 % của kỹ sư. Chỉ đọc board.
"""
import os

from ..core.errors import CopilotInputError
from . import request as R

FILE = "review.json"
PARTIAL = "review_partial.json"


# ----------------------------------------------------------------------------- trợ giúp
def _basis(st, nets=None):
    """-> (basis, comp_a, comp_b, nets) để review: nội dung đã chốt nếu có và trùng đề xuất, không thì đề xuất."""
    c, p = st.get("content"), st.get("proposal")
    src, basis = (c, "content") if c else (p, "proposal")
    if c and p and (sorted([p["comp_a"], p["comp_b"]]) != sorted([c["comp_a"], c["comp_b"]])
                    or sorted(set(p["nets"])) != sorted(set(c["nets"]))):
        src, basis = p, "proposal"                                     # trace lại sau GATE A: review đề xuất mới
    if not src:
        raise CopilotInputError("interface", "traced interface (isim_trace first)", st.get("name"))
    if nets:
        nets = [n.strip() for n in (nets.split(",") if isinstance(nets, str) else nets) if n and str(n).strip()]
        if not nets:
            raise CopilotInputError("nets", "comma separated net names", nets)
        basis = "nets"
    return basis, src["comp_a"], src["comp_b"], sorted(set(nets or src["nets"]))


def _aedb(req):
    from ..cut_board import naming
    return naming.board_paths(req["board"])[0]


def _board_key(req):
    from ..layout_snapshot import key as K
    try:
        return K.board_key(_aedb(req), req.get("cell") or "")
    except (CopilotInputError, ValueError, OSError):
        return None


def _review_section(rid, name):
    from . import user_settings as U
    p = U.path(rid)
    if not os.path.isfile(p):
        return {}
    sec = (U._read(p).get("interfaces") or {}).get(name) or {}
    return sec.get("review") or {}


def _approval(sec, measured_at):
    """Lời đồng ý chỉ có hiệu lực cho đúng lần review (035). Quyết định / override của 2.12.0 không bao giờ tính."""
    a = (sec or {}).get("approval")
    return a if a and measured_at and a.get("measured_at") == measured_at else None


def _load(request_id, name):
    req = R.load(request_id)
    rid = req["request_id"]
    return req, rid, R.get_state(rid, name)


def series_values(req, st):
    """045: {refdes: giá trị} của linh kiện (netlist của request trước, không có -> board facts đã định dạng)."""
    from ..cut_board.review_routing import fmt_value
    out = {}
    for rd, c in ((st or {}).get("board_facts") or {}).get("components", {}).items():
        if isinstance(c, dict) and c.get("value") not in (None, ""):
            out[rd] = fmt_value(c["value"], c.get("type"))
    nl = R._rjson(os.path.join(R.work_dir(req), R.NETLIST_FILE)) or {}
    for rd, c in (nl.get("components") or {}).items():
        if isinstance(c, dict) and str(c.get("value") or "").strip():
            out[rd] = str(c["value"]).strip()
    return out


def _html(req, a, b, nets, snapshot, log=None, values=None):
    """Báo cáo HTML của review (review.review trên snapshot; thư mục autocut/ cạnh board). -> (path, lỗi)."""
    from ..cut_board import review as RV
    try:
        r = RV.review(req["board"], f"{a}-{b}:{','.join(nets)}", req.get("cell") or None,
                      log=log or (lambda *x: None), snapshot=snapshot, series_values=values or {})
        return os.path.abspath(r["html"]), None
    except Exception as ex:                                            # report lỗi: không duyệt được (no_report)
        return None, f"{type(ex).__name__}: {ex}"


# ----------------------------------------------------------------------------- đo / dùng lại
def run(request_id, name, checks=None, html=False, version=None, snapshot="auto", reuse=True, nets=None):
    from .. import review_checks as RC
    from ..review_checks import _store as store
    from ..review_checks import _verdict as V
    from . import user_settings as U
    req, rid, st = _load(request_id, name)
    if not isinstance(html, bool):
        raise CopilotInputError("html", "true or false", html)
    if not isinstance(reuse, bool):
        raise CopilotInputError("reuse", "true or false", reuse)
    basis, a, b, asked = _basis(st, nets)
    names = RC.select(checks)
    full = names == RC.select(None)
    cell = req.get("cell") or ""
    aedb = _aedb(req)
    bkey = RC.record_key(req["board"], cell)
    thr = RC.current_thresholds(req["board"])
    want = V.match_key(bkey, cell, a, b, asked, names, thr)
    hit = store.find(aedb, want) if full and reuse else None
    if hit:
        path, doc, ch = hit
        out = {k: doc.get(k) for k in ("board", "cell", "plane_layers", "checks_run", "checks_available", "source")}
        out.update(channels=[ch], summary_md=ch.get("summary_md", ""), measured_at=doc.get("measured_at"),
                   review_file=path, reused_from=path)
    else:
        spec = {"comp_a": a, "comp_b": b, "patterns": asked, "name": name}
        out = RC.measure_channels(req["board"], [spec], names, cell, version, snapshot=snapshot)
        out["measured_at"] = R._now()
        if full:
            RC.save_record(out, cell, f"isim:{rid}/{name}", bkey, req["board"])
        else:
            store.annotate(out, bkey, cell, thr)
        out["reused_from"] = None
    ch = out["channels"][0]
    f = V.channel_findings(ch)
    out.update(request_id=rid, interface=name, basis=basis, comp_a=a, comp_b=b, nets_asked=asked, key=want,
               counts=f["counts"], by_check=f["by_check"], incomplete=f["incomplete"],
               failed_checks=f["failed_checks"],
               findings_md=V.findings_md(name, f))
    if full or html:                                                   # 035: review đầy đủ LUÔN có report HTML
        vals = series_values(req, st)                                  # 045: topology labels '220nF - 0402'
        out["html"], err = _html(req, a, b, asked, snapshot, **({"values": vals} if vals else {}))
        if err:
            out["html_error"] = err
    p = os.path.join(R.iface_dir(rid, name), FILE if full else PARTIAL)
    R.wjson(p, out)
    out["review_json"] = p
    if full:
        U.update(rid, name, review={"measured_at": out["measured_at"], "review_json": p, "html": out.get("html"),
                                    "approval": None})
        out["gate"] = gate_status(rid, name, {"comp_a": a, "comp_b": b, "nets": asked})
        from . import answer
        answer.attach(out, rid, name)                                  # 036: có preview cùng thông số -> câu trả lời
    else:
        out["gate"] = {"ok": False, "status": "partial",
                       "message": "Review một phần (checks=...) không thay review bắt buộc (cần đủ các check)."}
    return out


# ----------------------------------------------------------------------------- gate
def _g(ok, status, message, **kw):
    return {"ok": ok, "status": status, "message": message, "diffs": kw.get("diffs") or [],
            "counts": kw.get("counts"), "html": kw.get("html"), "approval": kw.get("approval")}


def gate_status(request_id, name, content=None):
    """Trạng thái review của interface (không bao giờ đo, không ném lỗi khi thiếu file).
    ok = review hiện hành + có report (ready / approved): GATE A được phép (GATE A chính là lời đồng ý)."""
    from .. import review_checks as RC
    req, rid, st = _load(request_id, name)
    c = content or st.get("content") or st.get("proposal")
    data = R._rjson(os.path.join(R.iface_dir(rid, name), FILE))
    if not data:
        return _g(False, "not_reviewed", f"{name}: chưa review layout. Chạy isim_review (bắt buộc, sau isim_trace) "
                                         "trước GATE A / cut.")
    diffs = []
    if c:
        if sorted([str(c["comp_a"]), str(c["comp_b"])]) != sorted([str(data.get("comp_a")), str(data.get("comp_b"))]):
            diffs.append("ends")
        if sorted(set(c.get("nets") or [])) != sorted(set(data.get("nets_asked") or [])):
            diffs.append("nets")
    key = data.get("key") or {}
    now = _board_key(req)
    if now is None or any(now.get(k) != key.get(k) for k in ("aedb", "def_size", "def_mtime_ns")):
        diffs.append("board_changed")
    if key.get("checks") != sorted(RC.select(None)):
        diffs.append("checks")
    if key.get("thresholds") != RC.current_thresholds(req["board"]):
        diffs.append("thresholds")
    if diffs:
        old = _approval(_review_section(rid, name), data.get("measured_at"))
        return _g(False, "out_of_date", f"{name}: review đã cũ ({', '.join(diffs)}): chạy isim_review lại cho nội "
                                        "dung / board hiện tại (snapshot: vài giây)."
                  + (" Lời đồng ý cũ không còn hiệu lực." if old else ""), diffs=diffs, approval=old)
    kw = {"counts": data.get("counts"), "html": data.get("html")}
    if not data.get("html") or not os.path.isfile(data["html"]):
        return _g(False, "no_report", f"{name}: chưa có file review HTML ({data.get('html_error') or 'file thiếu'}): "
                                      "chạy isim_review lại.", **kw)
    ap = _approval(_review_section(rid, name), data.get("measured_at"))
    if ap:
        return _g(True, "approved", f"{name}: người dùng đã đồng ý cut sau khi đọc review ({ap['time']}).",
                  approval=ap, **kw)
    return _g(True, "ready", f"{name}: report review sẵn sàng ({data['html']}); chờ người dùng đọc và đồng ý cut.",
              **kw)


def require(request_id, name, content=None, for_cut=False):
    """GATE A: review hiện hành + report (ready / approved). Cut (for_cut): phải 'approved'."""
    g = gate_status(request_id, name, content)
    if not g["ok"]:
        raise CopilotInputError("review", "current layout review with its HTML report. " + g["message"], g["status"])
    if for_cut and g["status"] != "approved":
        raise CopilotInputError("review", "the user's approval after reading the review report (GATE A: "
                                          "isim_confirm_content)", g["status"])
    return g


def approve(request_id, name, preview_json=None, user_words="", content=None):
    """Ghi lời đồng ý của kỹ sư cho review hiện hành (gọi bởi GATE A). -> approval."""
    from . import user_settings as U
    req, rid, st = _load(request_id, name)
    g = require(rid, name, content)
    data = R._rjson(os.path.join(R.iface_dir(rid, name), FILE)) or {}
    sec = _review_section(rid, name)
    ap = {"measured_at": data.get("measured_at"), "time": R._now(), "report": data.get("html"),
          "review_json": os.path.join(R.iface_dir(rid, name), FILE), "counts": data.get("counts") or g.get("counts"),
          "by_check": data.get("by_check") or {},
          "incomplete": bool(data.get("incomplete")), "failed_checks": data.get("failed_checks") or [],
          "preview_json": preview_json, "user_words": str(user_words or "")}
    U.update(rid, name, review=dict(sec, measured_at=data.get("measured_at"), html=data.get("html"), approval=ap))
    return ap


def status_label(g):
    """Ô 'Review' của isim_status."""
    s = g["status"]
    if s == "out_of_date" and g.get("approval"):
        return "approval out of date"
    return {"not_reviewed": "not reviewed", "out_of_date": "out of date", "no_report": "no report",
            "ready": "report ready", "approved": "approved"}.get(s, s)
