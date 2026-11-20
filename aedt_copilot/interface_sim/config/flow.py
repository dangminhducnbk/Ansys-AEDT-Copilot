"""038 fixed process (contract: specs/038-cut-config-html/contracts/config-flow.md):

039 (specs/039-review-before-config/contracts/review-step.md): requests with review_first start with
review_step (M0 + Q0) -> review_answer (no: stopped, M0x | yes: config, M1); config / check / go need the OK.

config(request_id)   review (when not current) + board data + <request>/config.html -> M1
check(request_id)    read the saved page, validate -> M2 | channel folders, previews with the config -> Q2
go(request_id, w)    (after the user's go on Q2) content confirm + cut + end check + apply + merge into the NEW project of
                     the request folder + channel folders -> M3
Every step reuses the existing step functions; nothing of the user is written (board read-only, cut on copies).
"""
import datetime as dt
import json
import os
import shutil
import time

from ...core.errors import CopilotInputError
from .. import request as R
from . import answers as A
from . import model as M
from . import page, read
from . import review_data as RD

DATA_FILE = "config_data.json"          # <iface work>/: page data of the channel (+ key)
RESOLVED_FILE = "resolutions.json"     # <request work>/: 045 resolutions of the checked page (FR-013)
CHECK_FILE = "config_check.json"        # <request work>/: what Q2 showed (settings hash per channel)
PAGE = "config.html"


def _P_rows():
    from ...cut_board import config
    return config.defaults(), config.template_rows()


def _content_of(st):
    """Traced (or agreed) content of a channel + schematic differences of the trace."""
    c = dict(st.get("content") or st.get("proposal") or {})
    if not c.get("comp_a"):
        raise CopilotInputError("interface", "traced interface (isim_trace)", st.get("name"))
    c.setdefault("schematic_diffs", [{"item": d.get("item"), "kind": d.get("kind"), "board": d.get("board"),
                                      "schematic": d.get("schematic")} for d in st.get("schematic_diffs") or []
                                     if not d.get("resolution")])
    return {k: c.get(k) for k in ("comp_a", "comp_b", "nets", "diff_groups", "series", "schematic_diffs")}


def _board_key(req):
    p = os.path.join(req["board"], "edb.def")
    try:
        s = os.stat(p)
        return [s.st_size, s.st_mtime_ns]
    except OSError:
        return None


def _review(rid, name, c, log):
    """Current review + HTML report for the content c (runs isim_review when needed). -> html path."""
    from .. import review as RVW
    g = RVW.gate_status(rid, name, c)
    if g["status"] in ("ready", "approved"):
        return g["html"]
    log(f"[config] {name}: review ({g['status']})")
    RVW.run(rid, name, html=True, nets=list(c["nets"]))
    g = RVW.gate_status(rid, name, c)
    if not g["ok"]:
        raise CopilotInputError("review", "layout review with its HTML report", g["message"])
    return g["html"]


def _channel_data(req, name, P, log, version):
    """Page data of one channel; cached in <iface>/config_data.json while board / content / tool version are equal."""
    from ... import __version__
    from . import data as DATA
    rid = req["request_id"]
    st = R.get_state(rid, name)
    c = _content_of(st)
    html = _review(rid, name, c, log)
    key = {"board": _board_key(req), "content": c, "version": __version__}
    path = os.path.join(R.iface_dir(rid, name), DATA_FILE)
    old = R._rjson(path)
    if old and old.get("key") == key:
        d = old["data"]
        d["review_html"] = html
        return d
    t0 = time.perf_counter()
    d = DATA.channel_data(req, c, P, html, log, version)
    log(f"[config] {name}: board data {round(time.perf_counter() - t0, 1)} s ({d['times']})")
    R.wjson(path, {"key": key, "data": d})
    return d


def page_data(req, chans, P, rows):
    adv = [{"key": r["key"], "label": r["name"], "unit": r["unit"], "type": r["type"]} for r in M.adv_rows(rows)]
    return {"request_id": req["request_id"], "board_name": os.path.splitext(os.path.basename(req["board"]))[0],
            "request_folder": req["folder"], "template": {"adv": adv}, "channels": chans, "built_at": R._now(),
            "defaults": {n: M.defaults(P, rows, d) for n, d in chans.items()}}


def _write_request_md(req, extra=""):
    lines = [f"# Request {req['request_id']}", "", f"- Board: {req['board']}", f"- Workspace: {req['workspace']}",
             f"- Created: {req.get('created')}", f"- Config: {os.path.join(req['folder'], PAGE)}", "",
             "| Channel | Folder | Step |", "|---|---|---|"]
    for n in req["interfaces"]:
        try:
            stp = R.get_state(req["request_id"], n)["step"]
        except CopilotInputError:
            stp = "(not started)"
        lines.append(f"| {n} | {(req.get('channel_folders') or {}).get(n, '')} | {stp} |")
    with open(os.path.join(req["folder"], "request.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n\n" + extra if extra else "") + "\n")


# ----------------------------------------------------------------------------- 039 review step (M0 / Q0 / M0x)
STEP_FILE = "review_step.json"          # <request work>/: reviews shown at Q0 + the user's decision


def _step_path(req):
    return os.path.join(R.work_dir(req), STEP_FILE)


def _measured(rid, name):
    from .. import review as RVW
    return (R._rjson(os.path.join(R.iface_dir(rid, name), RVW.FILE)) or {}).get("measured_at")


def _current(rid, name, row):
    """Review of the channel still current (board / content / checks) and the same measurement as shown at Q0."""
    from .. import review as RVW
    try:
        c = _content_of(R.get_state(rid, name))
    except CopilotInputError:
        return False
    return bool(RVW.gate_status(rid, name, c)["ok"]) and _measured(rid, name) == row.get("measured_at")


def _review_row(rid, name, log):
    from .. import review as RVW
    row = {"name": name}
    try:
        c = _content_of(R.get_state(rid, name))
        row["review_html"] = _review(rid, name, c, log)
        d = R._rjson(os.path.join(R.iface_dir(rid, name), RVW.FILE)) or {}
        row.update(measured_at=d.get("measured_at"), not_ok=(d.get("counts") or {}).get("NOT OK", 0))
    except Exception as ex:                                             # shown in M0; no Q0 until every channel has one
        row["error"] = f"{type(ex).__name__}: {ex}"[:300]
        log(f"[review] {name}: {row['error']}")
    return row


def _review_first(req):
    if not req.get("review_first"):
        raise CopilotInputError("request_id", "request created by 5.2.0 or later (review step); older requests "
                                              "continue with isim_config", req["request_id"])
    if not req["interfaces"]:
        raise CopilotInputError("interfaces", "at least one traced interface (isim_trace)", [])


def _stopped(st):
    return (st.get("decision") or {}).get("accepted") is False


def _refuse_stopped(rid):
    raise CopilotInputError("review", "an accepted layout review: the user answered 'no' at Q0 and the request is "
                                      "stopped (start a new request)", rid)


def review_step(request_id="", version=None, log=print):
    """039 step 2-3: review of every channel -> M0 (+ Q0 when every channel has a report). Read only.
    045 (request review_page): reviews, then the ONE page (review + settings, config.html) -> M0p, no Q0."""
    req = R.load(request_id)
    rid = req["request_id"]
    _review_first(req)
    if _stopped(R._rjson(_step_path(req)) or {}):
        _refuse_stopped(rid)
    rows = [_review_row(rid, n, log) for n in req["interfaces"]]
    ready = not any(r.get("error") for r in rows)
    R.wjson(_step_path(req), {"time": R._now(), "ready": ready, "channels": {r["name"]: r for r in rows}})
    if req.get("review_page"):
        if not ready:
            return {"request_id": rid, "channels": rows, "ready": False, "answer_md": A.m0p_errors(rows)}
        out = config(rid, version, log)
        return dict(out, channels=rows, ready=True, answer_md=A.m0p(rows, out["config_html"], out.get("config_url")))
    return {"request_id": rid, "channels": rows, "ready": ready, "answer_md": A.m0(rows)}


def review_answer(request_id="", accepted=False, user_words="", version=None, log=print):
    """039 step 4: the user's answer to Q0. no -> request stopped, M0x. yes -> decision bound to the reviews of Q0,
    then the config page (M1)."""
    req = R.load(request_id)
    rid = req["request_id"]
    _review_first(req)
    if req.get("review_page"):
        raise CopilotInputError("request_id", "a request with the Q0 question (5.2-5.5). This request (5.6.0+) has no "
                                              "Q0: the user resolves the NOT OK points on the page, Saves and says "
                                              "'xong' -> isim_config_check", rid)
    if not str(user_words or "").strip():
        raise CopilotInputError("user_words", "the user's words of the answer to Q0", user_words)
    st = R._rjson(_step_path(req)) or {}
    if not st.get("channels"):
        raise CopilotInputError("review", "isim_layout_review first (M0 + Q0 shown to the user)", None)
    if _stopped(st):
        _refuse_stopped(rid)
    if not st.get("ready"):
        raise CopilotInputError("review", "a review report for every channel (isim_layout_review again)",
                                [n for n, r in st["channels"].items() if r.get("error")])
    changed = sorted(set(req["interfaces"]) ^ set(st["channels"])) + \
        [n for n, r in st["channels"].items() if n in req["interfaces"] and not _current(rid, n, r)]
    if changed:
        raise CopilotInputError("review", "the reviews shown at Q0 (they changed: isim_layout_review again)", changed)
    st["decision"] = {"accepted": bool(accepted), "user_words": str(user_words), "time": R._now()}
    R.wjson(_step_path(req), st)
    rows = list(st["channels"].values())
    if not accepted:
        _write_request_md(req, "**Stopped by the user at the layout review (Q0).** Words: " + str(user_words))
        return {"request_id": rid, "stopped": True, "answer_md": A.m0x(rows)}
    return dict(config(rid, version, log), review_accepted=True)


def require_review_ok(req, stage):
    """039 guard of config / check / go (requests with review_first only). config: the reviews must still be the
    ones accepted at Q0; check / go: a review re-measured for changed content is allowed (Q2 says so)."""
    if not req.get("review_first"):
        return None
    rid = req["request_id"]
    st = R._rjson(_step_path(req)) or {}
    if _stopped(st):
        _refuse_stopped(rid)
    if req.get("review_page"):                                          # 045: no Q0; the page's resolutions instead
        if not st.get("channels"):
            raise CopilotInputError("review", "isim_layout_review first (reviews + the review / config page)", None)
        return st
    if not (st.get("decision") or {}).get("accepted"):
        raise CopilotInputError("review", "the user's OK on the layout review first (isim_layout_review -> Q0 -> "
                                          "isim_review_answer)", "not answered")
    if stage == "config":
        ch = st.get("channels") or {}
        changed = [n for n in req["interfaces"] if n not in ch or not _current(rid, n, ch[n])]
        if changed:
            raise CopilotInputError("review", "the reviews accepted at Q0 (they changed: isim_layout_review again)",
                                    changed)
    return st


# ----------------------------------------------------------------------------- isim_config
def config(request_id="", version=None, log=print):
    req = R.load(request_id)
    rid = req["request_id"]
    if req.get("layout") != "038":
        raise CopilotInputError("request_id", "request created by 5.0.0 or later (isim_start)", rid)
    if not req["interfaces"]:
        raise CopilotInputError("interfaces", "at least one traced interface (isim_trace)", [])
    require_review_ok(req, "config")
    P, rows = _P_rows()
    chans = {n: _channel_data(req, n, P, log, version) for n in req["interfaces"]}
    data = page_data(req, chans, P, rows)
    state = {"channels": {n: M.defaults(P, rows, d) for n, d in chans.items()}, "saved_at": None}
    saved = read.find_saved(rid, req["folder"])
    kept = bool(saved and set(saved["state"].get("channels") or {}) == set(chans))
    if kept:                                                            # keep what the user already set
        state = saved["state"]
    carried = 0
    if req.get("review_page"):                                          # 045: review data + resolutions on the page
        data["review"] = review_page_data(rid, chans)
        old = state.get("review") or {}
        state = dict(state, review=None)
        state["review"], carried = RD.carry_over(old, data["review"])
        if any((old.get(n) or {}).get("measured_at") != r["measured_at"] for n, r in data["review"].items()) \
                and state.get("saved_at"):
            state["saved_at"] = None                                    # review changed: the user must Save again
    path = os.path.join(req["folder"], PAGE)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(page.build(data, state))
    _write_request_md(req)
    from . import serve
    port = serve.ensure(log)                                            # 040: local link, Save writes the file
    url = serve.page_url(req, port) if port else None
    return {"request_id": rid, "config_html": path, "config_url": url,
            "channels": {n: d.get("times") for n, d in chans.items()},
            "kept_saved_state": kept, "carried_resolutions": carried, "answer_md": A.m1(path, url)}


def review_page_data(rid, chans):
    """045: review data of every channel for the page (review.json + its report HTML + the config data stackup)."""
    from .. import review as RVW
    out = {}
    for n, d in chans.items():
        doc = R._rjson(os.path.join(R.iface_dir(rid, n), RVW.FILE))
        if not doc:
            raise CopilotInputError("review", f"layout review of {n} (isim_layout_review)", None)
        text = None
        if doc.get("html") and os.path.isfile(doc["html"]):
            with open(doc["html"], encoding="utf-8") as f:
                text = f.read()
        out[n] = RD.channel_review(doc, text, d.get("stackup") or [], (d.get("layers") or {}).get("order") or [])
    return out


def require_resolved(req, saved):
    """045 (FR-012): every NOT OK point of every channel resolved on the saved page, for the CURRENT review of each
    channel. -> {channel: {measured_at, points, resolved[]}} (the record of FR-013). Raises CopilotInputError."""
    from .. import review as RVW
    rid = req["request_id"]
    rv = (saved.get("data") or {}).get("review") or {}
    missing = [n for n in req["interfaces"] if n not in rv]
    if missing:
        raise CopilotInputError("review", "the review / config page of this request (isim_layout_review again: the "
                                          "saved page has no review of these channels)", missing)
    old = []
    for n in req["interfaces"]:
        cur = (R._rjson(os.path.join(R.iface_dir(rid, n), RVW.FILE)) or {}).get("measured_at")
        if rv[n].get("measured_at") != cur:
            old.append(n)
    if old:
        raise CopilotInputError("review", "a page built from the current reviews (the review was measured again: "
                                          "open the new page, resolve, Save)", old)
    errs = RD.validate_resolutions(saved["state"].get("review"), rv)
    if errs:
        raise CopilotInputError("review", "valid resolutions on the saved page", errs[:10])
    left = RD.unresolved(saved["state"], {"review": rv})
    if left:
        raise CopilotInputError("review", "every NOT OK point resolved on the page, then Save",
                                {n: f"{len(v)} of {len(rv[n]['points'])} NOT OK point(s) not resolved"
                                 for n, v in left.items()})
    rec = {}
    for n in req["interfaces"]:
        res = (saved["state"]["review"].get(n) or {}).get("resolved") or {}
        rec[n] = {"measured_at": rv[n]["measured_at"], "points": len(rv[n]["points"]),
                  "resolved": [dict(id=p["id"], **{k: res[p["id"]].get(k) for k in ("check", "net", "x", "y", "time",
                                                                                      "note")})
                               for p in rv[n]["points"]]}
    return rec


# ----------------------------------------------------------------------------- isim_config_check
def _settings(req, saved, P, rows):
    """Validated settings of every channel from the saved page (data = the tool's cached data, not the page's)."""
    rid = req["request_id"]
    chans = {n: (R._rjson(os.path.join(R.iface_dir(rid, n), DATA_FILE)) or {}).get("data") for n in req["interfaces"]}
    missing = [n for n, d in chans.items() if not d]
    if missing:
        raise CopilotInputError("config", "isim_config first (page data of every channel)", missing)
    data = {"channels": chans}
    errors = M.validate(saved["state"], data, P, rows)
    if errors:
        return None, errors
    return {n: M.to_settings(n, saved["state"]["channels"][n], chans[n], P, rows) for n in chans}, []


def check(request_id="", version=None, log=print):
    from .. import cut_preview as CP
    req = R.load(request_id)
    rid = req["request_id"]
    step = require_review_ok(req, "check")
    accepted_at = {n: r.get("measured_at") for n, r in ((step or {}).get("channels") or {}).items()}
    saved = read.find_saved(rid, req["folder"])
    path = os.path.join(req["folder"], PAGE)
    if not saved:
        return {"request_id": rid, "saved": False, "valid": False,
                "answer_md": A.m1(path) + "\n\n" + A.q1()}
    resolved = require_resolved(req, saved) if req.get("review_page") else None   # 045 (FR-012)
    P, rows = _P_rows()
    sets, errors = _settings(req, saved, P, rows)
    if errors:
        return {"request_id": rid, "saved": True, "valid": False, "errors": errors, "saved_page": saved["path"],
                "answer_md": A.m2(errors)}
    out_rows, record = [], {}
    for n, s in sets.items():
        R.set_channel_folder(rid, n, s["folder"])
        st = R.get_state(rid, n)
        if st["step"] != "started":                                     # new config of a channel already cut
            R.advance(rid, n, "started", "038: new config")
        prop = dict(st.get("proposal") or st.get("content") or {})
        R.set_state(rid, n, "038 config", proposal=dict(prop, **{k: s["content"][k] for k in
                                                                ("nets", "diff_groups", "series")}),
                    proposal_traced=st.get("proposal_traced") or prop, content=None)
        html = _review(rid, n, s["content"], log)
        pv = CP.preview(rid, n, structural=s["structural"], end_factors=None, version=version)
        if not pv.get("ok", True) and pv.get("validation"):
            errs = [{"channel": n, "frame": "Auto Generate Extent", "field": "cut", "message": e}
                    for e in pv.get("errors") or []]
            return {"request_id": rid, "saved": True, "valid": False, "errors": errs, "answer_md": A.m2(errs)}
        out_rows.append({"name": n, "folder": s["folder"], "image": pv.get("image"), "size_mm": pv.get("extent_size_mm"),
                         "area_mm2": pv.get("extent_area_mm2"), "review_html": html,
                         "review_updated": bool(step) and _measured(rid, n) != accepted_at.get(n),   # 039 FR-007
                         "ends": [l.lstrip("- ") for l in pv.get("ends_lines") or []], "errors": pv.get("errors")})
        record[n] = {"hash": M.settings_hash(s), "folder": s["folder"]}
    R.wjson(os.path.join(R.work_dir(R.load(rid)), CHECK_FILE),
            {"time": R._now(), "saved_page": saved["path"], "saved_at": saved["saved_at"], "channels": record})
    n_res = None
    if resolved is not None:                                            # 045 (FR-013): record of the resolutions
        n_res = sum(len(c["resolved"]) for c in resolved.values())
        R.wjson(os.path.join(R.work_dir(R.load(rid)), RESOLVED_FILE),
                {"time": R._now(), "saved_page": saved["path"], "saved_at": saved["saved_at"], "channels": resolved})
    _write_request_md(R.load(rid))
    return {"request_id": rid, "saved": True, "valid": True, "saved_page": saved["path"], "previews": out_rows,
            "resolved_points": n_res, "answer_md": A.q2(out_rows, n_res)}


# ----------------------------------------------------------------------------- isim_go
def handling_for(ends, chosen):
    """Handling used by apply: the user's choice when allowed for the end, else the proposal (no_gnd_pin ->
    gnd_plate_vias, connector -> team default, other rule -> first option). -> (handling, auto{refdes: option})."""
    out, auto = {}, {}
    for rd, e in (ends or {}).items():
        need = e.get("unusual") or []
        dh = e.get("default_handling")
        allowed = [o for u in need for o in u.get("options") or [] if o != "other"] or (dh or {}).get("options") or []
        if not allowed:
            continue
        h = (chosen or {}).get(rd)
        if h in allowed:
            out[rd] = h
            continue
        if any(u["rule"] == "no_gnd_pin" for u in need):
            pick = "gnd_plate_vias" if "gnd_plate_vias" in allowed else allowed[0]
        elif dh and not need:
            pick = dh["value"]
        else:
            pick = allowed[0]
        out[rd], auto[rd] = pick, pick
    return out, auto


def _metrics(res):
    m = res.get("metrics") or {}
    sc = res.get("self_check") or {}
    st = sc.get("stackup") or {}
    return {"ports": m.get("ports"), "gnd_vias": m.get("gnd_vias"),
            "self_check": "OK" if sc.get("ok") else "mismatch: " + "; ".join(map(str, sc.get("mismatches") or []))[:120],
            "stackup": "OK" if st.get("ok") else ("NOT OK" if st.get("ok") is False else "-"),     # 042
            "stackup_diffs": st.get("diffs") or []}


def go(request_id="", user_words="", version=None, log=print):
    from .. import apply as AP, content as CT, cut as CU, ends as EN
    req = R.load(request_id)
    rid = req["request_id"]
    if not str(user_words or "").strip():
        raise CopilotInputError("user_words", "the user's words of the go (Q2)", user_words)
    require_review_ok(req, "go")
    chk =R._rjson(os.path.join(R.work_dir(req), CHECK_FILE))
    if not chk:
        raise CopilotInputError("config", "isim_config_check first (the user saw the cut regions + reviews)", None)
    saved = read.find_saved(rid, req["folder"])
    if saved and req.get("review_page"):
        require_resolved(req, saved)                                    # 045 (FR-012)
    P, rows = _P_rows()
    sets, errors = _settings(req, saved, P, rows) if saved else (None, ["no saved config"])
    if errors:
        raise CopilotInputError("config", "the configuration checked at Q2", errors)
    changed = [n for n, s in sets.items() if M.settings_hash(s) != (chk["channels"].get(n) or {}).get("hash")]
    if changed:
        raise CopilotInputError("config", "the configuration shown at Q2 (it changed: isim_config_check again)",
                                changed)
    rows_out, ok = [], []
    for n, s in sets.items():
        row = {"name": n, "folder": s["folder"], "status": "error"}
        try:
            t0 = time.perf_counter()
            CT.confirm(rid, n, dict(s["content"], end_factors={}), user_words=user_words)
            CU.run(rid, n, version)
            e = EN.check(rid, n, version)
            h, auto = handling_for(e["ends"], s["handling"])
            res = AP.run(rid, n, s["values"], h, version)
            if res.get("stopped"):
                row.update(status="stopped", error=f"stopped at {res['stopped']} (user choice)")
            else:
                row.update(status="applied", **_metrics(res), warnings=list(res.get("warnings") or []) +
                           [f"{rd}: {o} (proposal, case found after the cut)" for rd, o in auto.items()],
                           seconds=round(time.perf_counter() - t0))
                ok.append(n)
        except Exception as ex:                                          # one channel failing never stops the others
            row["error"] = f"{type(ex).__name__}: {ex}"[:300]
            log(f"[go] {n}: {row['error']}")
        rows_out.append(row)
    merged, board_copy = None, None
    if ok:
        mo = merge_new_project(rid, ok, log=log)
        merged, board_copy = mo["project"], mo.get("board_copy")
        for r in rows_out:
            c = (mo["channels"].get(r["name"]) or {})
            if r["name"] in ok:
                r["status"] = "merged" if c.get("state") in ("ok", "renamed") else "merge error"
                r["checks"] = c.get("checks")                            # 042: merged design read back
                if c.get("error"):
                    r["error"] = c["error"]
    _write_request_md(R.load(rid))
    out = {"request_id": rid, "channels": rows_out, "merged_project": merged, "board_copy": board_copy,
           "answer_md": A.m3(rows_out, merged, board_copy)}
    R.wjson(os.path.join(R.work_dir(R.load(rid)), "go.json"), dict(out, time=R._now(), user_words=user_words))
    return out


# ----------------------------------------------------------------------------- merge + channel folders
def publish_aedb(rid, name):
    """Move the applied design to <request>/<folder>/<folder>.aedb (the merge writes <folder>.aedt beside it)."""
    req = R.load(rid)
    folder = (req.get("channel_folders") or {}).get(name)
    if not folder:
        raise CopilotInputError("folder", f"channel folder of {name} (isim_config_check)", None)
    st = R.get_state(rid, name)
    src = (st.get("result") or {}).get("aedb")
    dst = os.path.join(req["folder"], folder, folder + ".aedb")
    if not src or not os.path.isdir(src):
        raise CopilotInputError("result", f"applied design of {name}", src)
    if os.path.normcase(os.path.abspath(src)) != os.path.normcase(os.path.abspath(dst)):
        if os.path.exists(dst) or os.path.exists(dst[:-5] + ".aedt"):  # earlier run: keep it in _work/history
            hist = os.path.join(req["folder"], folder, R.WORK, "history", dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(hist, exist_ok=True)
            for p in (dst, dst[:-5] + ".aedt", dst[:-5] + ".aedtresults"):
                if os.path.exists(p):
                    os.replace(p, os.path.join(hist, os.path.basename(p)))
        os.replace(src, dst)
        R.set_state(rid, name, "038 published", result=dict(st["result"], aedb=dst))
    return dst


def channel_page(rid, name, approval):
    """Read-only config.html of one channel (FR-007)."""
    req = R.load(rid)
    saved = read.find_saved(rid, req["folder"])
    d = (R._rjson(os.path.join(R.iface_dir(rid, name), DATA_FILE)) or {}).get("data")
    if not (saved and d):
        return None
    P, rows = _P_rows()
    data = page_data(req, {name: d}, P, rows)
    data["ro_note"] = (f"Read-only record. Approved {approval.get('time', '')} — "
                       f"\"{approval.get('user_words', '')}\". Config saved {saved['saved_at']}.")
    st = {"channels": {name: saved["state"]["channels"][name]}, "saved_at": saved["saved_at"], "current": name}
    path = os.path.join(R.channel_dir(rid, name), PAGE)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(page.build(data, st, readonly=True))
    return path


def prepare_board_copy(req, project, log=print):
    """042: the merge target must be a copy of the board. Missing, or a 5.0-5.3 empty project (request key
    merge_layout != board_copy) -> old files moved to _work/history/<time>/ (never deleted), board copied.
    Existing board copy (re-run of isim_go) -> None (channels are added again, _vN)."""
    from ...cut_board.merge import copy_board
    aedb = project[:-5] + ".aedb"
    have = os.path.exists(project) or os.path.isdir(aedb)
    if have and req.get("merge_layout") == "board_copy":
        return None
    if have:
        hist = os.path.join(R.work_dir(req), "history", dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(hist, exist_ok=True)
        for p in (project, aedb, project[:-5] + ".aedtresults"):
            if os.path.exists(p):
                os.replace(p, os.path.join(hist, os.path.basename(p)))
        log(f"[board copy] old merged project (empty-project layout) moved to {hist}")
    return copy_board(req["board"], req.get("workspace"), project, log)


def merge_new_project(request_id, names, log=print):
    """Merge the applied channels into <request>/<request_id>.aedt (created when missing); design = channel folder;
    channel folders get <folder>.aedb / .aedt, review.html, config.html."""
    from ...cut_board.merge import merge_designs
    req = R.load(request_id)
    rid = req["request_id"]
    sources = {}
    for n in names:
        folder = req["channel_folders"][n]
        sources[folder] = publish_aedb(rid, n)
    project = os.path.join(req["folder"], rid + ".aedt")
    copied = prepare_board_copy(req, project, log)                       # 042: target = copy of the user's board
    stk = None
    for n in names:                                                      # board stackup read at the cut
        stk = (R._rjson(os.path.join(R.iface_dir(rid, n), "stage1.json")) or {}).get("board_stackup")
        if stk:
            break
    out = merge_designs(project, sources, R.work_dir(req), None, log, backup=False, board_stackup=stk)
    out["board_copy"] = {"designs": out.get("board_designs_before") or [],
                         "mb": round((copied or {}).get("bytes", req.get("merged_copy_bytes") or 0) / 1e6, 1),
                         "copied_now": bool(copied)}
    req = R.load(rid)
    req["merged_project"] = project
    req["merge_layout"] = "board_copy"
    req["merged_board_designs"] = out["board_copy"]["designs"]
    if copied:
        req["merged_copy_bytes"] = copied["bytes"]
    R.save_request(req)
    by_name = {}
    for n in names:
        folder = req["channel_folders"][n]
        r = out["channels"].get(folder) or {}
        by_name[n] = r
        if r.get("state") in ("ok", "renamed"):
            R.set_state(rid, n, "merged (038)", merged={"design": r["design"], "status": r["state"], "project": project,
                                                         "warnings": r.get("warnings")})
            R.advance(rid, n, "merged")
        cd = R.channel_dir(rid, n)
        from .. import review as RVW
        g = RVW.gate_status(rid, n)
        if g.get("html") and os.path.isfile(g["html"]):
            shutil.copy2(g["html"], os.path.join(cd, "review.html"))
        from .. import user_settings as U
        ap = ((((R._rjson(U.path(rid)) or {}).get("interfaces") or {}).get(n) or {}).get("review") or {}).get(
            "approval") or {}
        channel_page(rid, n, ap)
    out["channels"] = by_name
    R.wjson(os.path.join(R.work_dir(req), "merge.json"), out)
    return out
