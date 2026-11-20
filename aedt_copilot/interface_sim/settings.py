"""Bảng settings: đề xuất (template), kiểm tra (luật như Excel), lưu (contract: isim-settings.md).

Giá trị chỉ lấy từ template hoặc người dùng; số đo chỉ ghi ở cột lý do. Giá trị đã chốt lưu trong
user_settings.json của request (004; thay settings.json / settings.md); bảng chỉ hiện trong chat.
"""
import os

from ..core.errors import CopilotInputError
from . import report, request as R
from .content import STRUCTURAL_KEYS, STRUCTURAL_PREFIX
from .ends import OPTIONS

ALL_OPTIONS = sorted({o for v in OPTIONS.values() for o in v})
# 006: nhóm thông số theo tiền tố khoá. cut = khoá sau apply (đổi = cắt lại); sim = sửa được (re-apply, GATE B)
CUT_PREFIXES = ("cutout", "series", "cleanup", "port", "solder_ball", "component")   # 038: component model = cut
SIM_PREFIXES = ("setup", "sweep", "airbox")
CUT_LOCKED_MSG = "đã cắt, đã khoá — cut lại để đổi"
REAPPLY_STEPS = ("applied", "merged")


def group_of(key):
    """'cut' | 'sim' theo tiền tố khoá template. Khoá khác -> lỗi (template thêm nhóm mới phải quyết định)."""
    pre = str(key).split(".", 1)[0]
    if pre in CUT_PREFIXES:
        return "cut"
    if pre in SIM_PREFIXES:
        return "sim"
    raise CopilotInputError("key", "key of group cut or sim", key)


def _rows():
    from ..cut_board import config
    return [r for r in config.template_rows() if r["scope"] == "channel"]


def recut_values(state, values):
    """Cut lại (009): values + khoá có lịch sử mặc định còn thiếu = giá trị lần trước (đã ghi) hoặc mặc định thời
    tool_version của lần trước. Không phải cut lại / values không phải dict -> trả nguyên."""
    from . import defaults_history as H
    rc = state.get("recut_old") if state.get("recut_from") else None
    if not rc or not isinstance(values, dict):
        return values
    old = rc.get("values") or {}
    out = dict(values)
    for k in H.HISTORY:
        if k in out:
            continue
        if k in old:
            out[k] = old[k]
        else:
            d = H.default_at(k, rc.get("tool_version"))
            if d is not None and d is not H.NOT_YET:
                out[k] = d
    return out


def _same_value(a, b):
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)


def _default(key):
    """Mặc định template của key, đã đổi kiểu (num -> số)."""
    from ..cut_board import config
    r = next((r for r in _rows() if r["key"] == key), None)
    if r is None or r["default"] in (None, ""):
        return None
    try:
        return config.coerce(r["default"], r["type"])
    except ValueError:
        return r["default"]


def _structural(k):
    return k.startswith(STRUCTURAL_PREFIX) or k in STRUCTURAL_KEYS


def _reason(r, ends):
    if r["key"] == "solder_ball.diameter_ratio" and ends:
        parts = []
        for rd, e in ends.items():
            ss = [min(p["pad"]["w_mm"], p["pad"]["h_mm"]) for p in e.get("signal_pins", []) if p.get("pad")]
            if ss and r["default"]:
                parts.append(f"{rd} pad {min(ss)} mm -> ball {round(float(r['default']) * min(ss), 3)} mm")
        return "; ".join(parts) or r["desc"]
    if r["mandatory"]:
        return "MANDATORY - engineer gives the value"
    return r["desc"]


def proposal(state, ends=None, values=None):
    """-> {rows[{key, name, unit, value, mandatory, source, reason, locked}], table_md}."""
    struct = (state.get("content") or {}).get("structural") or {}
    rc = state.get("recut_old") if state.get("recut_from") else None      # cut lại (004)
    old = (rc or {}).get("values") or {}
    if values is None and rc:
        values = {k: v for k, v in old.items() if not _structural(k)}  # điền sẵn giá trị lần trước
    values = dict(values or {})
    then = set()
    if rc:                                                                 # 009: khoá có lịch sử giữ giá trị lần trước
        filled = recut_values(state, values)
        then = {k for k in filled if k not in values and k not in old}
        values = filled
    rows = []
    for r in _rows():
        k = r["key"]
        if _structural(k):
            v, src, lock = struct.get(k, r["default"]), "content", True
        elif k in values:
            v, lock = values[k], False
            src = "engineer"
            if rc and k in old and str(old[k]) == str(values[k]):
                from .recut import setting_source
                src = setting_source(k, state["recut_from"].get("request_id"), rc.get("tool_version"))
        else:
            v, src, lock = r["default"], "default" if r["default"] is not None else "-", False
            if rc:
                from .recut import ADDED_IN, _ver
                if k in ADDED_IN and _ver(rc.get("tool_version")) < ADDED_IN[k]:
                    src = "team default (new)"
        rows.append({"key": k, "name": r["name"], "unit": r["unit"], "value": v, "mandatory": r["mandatory"],
                     "source": src, "locked": lock,
                     "reason": "locked (re-cut to change)" if lock else _reason(r, ends)})
    out = {"rows": rows, "table_md": table_md(rows)}
    if rc:
        from . import defaults_history as H
        for r in rows:
            if r["key"] in then:                                           # lần trước không ghi -> mặc định thời đó
                r["source"] = f"previous run {state['recut_from'].get('request_id')} (team default then)"
        changes = []
        for r in rows:
            if r["key"] in H.HISTORY and r["key"] in values and not _same_value(values[r["key"]], _default(r["key"])):
                changes.append({"key": r["key"], "previous": values[r["key"]], "team_default": _default(r["key"])})
                r["reason"] = f"team default now {_default(r['key'])}"
        out["table_md"] = table_md(rows)
        out["default_changes"] = changes
        if changes:
            out["table_md"] += "\n\nTeam default changed since the previous run (previous value kept): " + ", ".join(
                f"{c['key']} {c['previous']} -> team {c['team_default']}" for c in changes)
        out["values"] = values                                             # gửi lại ở isim_validate / isim_apply
        out["dropped"] = rc.get("dropped") or []
        if out["dropped"]:
            out["table_md"] += "\n\nDropped (not in the template any more): " + ", ".join(out["dropped"])
    return out


def table_md(rows, handling=None):
    md = report.table(["Key", "Parameter", "Value", "Unit", "Source", "Note"],
                      [[r["key"], r["name"], "**(fill)**" if r["mandatory"] and r["value"] in (None, "") else r["value"],
                        r["unit"], r["source"], r["reason"]] for r in rows])
    if handling:
        md += "\n\n" + report.table(["Refdes", "Handling"], sorted(handling.items()))
    return md


def effective_handling(ends, handling=None, kept=None):
    """012: handling dùng thật = mặc định team (đầu connector) < lựa chọn lần trước còn hợp lệ (cut lại) < kỹ sư.
    Thuần. ends {refdes: {default_handling?}}; kept / handling {refdes: option}."""
    out = {rd: e["default_handling"]["value"] for rd, e in (ends or {}).items()      # đầu có câu hỏi khác: kỹ sư chọn
           if isinstance(e, dict) and e.get("default_handling") and not e.get("unusual")}
    out.update(kept or {})
    out.update(handling or {})
    return out


def validate(values, handling=None, ends=None, structural=None):
    """-> {valid, errors[], P}. Thông báo lỗi = cut_board.config.build_params (như Excel) + handling + structural."""
    from ..cut_board import config
    if not isinstance(values, dict):
        raise CopilotInputError("values", "JSON object {key: value}", values)
    handling = dict(handling or {})
    errors = []
    channel_keys = {r["key"] for r in _rows()}
    struct = dict(structural or {})
    for k, v in values.items():
        if k in channel_keys and _structural(k) and k in struct and str(v) != str(struct[k]):
            errors.append(f"{k}: thay đổi thông số cắt -> cần cắt lại (đổi trong content rồi isim_cut)")
    merged = dict(struct)
    merged.update({k: v for k, v in values.items() if not _structural(k)})
    P, errs = config.build_params(merged)
    errors += errs
    for rd, e in (ends or {}).items():
        need = [u for u in e.get("unusual") or []]
        dh = e.get("default_handling")
        ng = [u for u in need if u["rule"] == "no_gnd_pin"]
        if ng:                                                          # 015: người dùng chọn, agent không tự chọn
            h = handling.get(rd)
            ok = [o for o in ng[0]["options"] if o != "other"]
            if h == "other":
                errors.append(f"{rd}: 'other' must be mapped to one of {ok} (or no tool exists: stop)")
            elif h not in ok:
                errors.append(f"{rd}: no GND pin - user's choice needed, one of {ok}")
        elif need:
            h = handling.get(rd)
            allowed = sorted({o for u in need for o in u["options"]})
            if h not in allowed:
                errors.append(f"{rd}: chọn cách xử lý cho {[u['rule'] for u in need]}: một trong {allowed}")
        elif dh and rd in handling and handling[rd] not in dh["options"]:
            errors.append(f"{rd}: {dh['rule']}: một trong {sorted(dh['options'])}")
    for rd, h in handling.items():
        if h not in ALL_OPTIONS:
            errors.append(f"{rd}: handling '{h}' không hợp lệ ({ALL_OPTIONS})")
        if ends is not None and rd not in ends:
            errors.append(f"{rd}: không phải linh kiện đầu của interface")
    return {"valid": not errors, "errors": errors, "P": P if not errors else None}


def save(request_id, name, values, handling, rows, P=None, gnd_decisions=None):
    """Gate B: ghi values + handling vào user_settings.json. -> {values, handling, agreed_at, user_settings}.
    P (009): khoá có lịch sử mặc định được ghi tường minh (giá trị thật đã dùng)."""
    from . import defaults_history as H
    from . import user_settings as U
    if P is not None:
        values = H.effective(values, P)
    now = R._now()
    extra = {"gnd_decisions": gnd_decisions} if gnd_decisions else {}
    U.update(request_id, name, values=dict(values), handling=dict(handling or {}), settings_agreed_at=now, **extra)
    return {"values": values, "handling": handling or {}, "rows": rows, "agreed_at": now,
            "user_settings": U.path(request_id)}


def validate_for(request_id, name, values, handling=None):
    """Kiểm tra theo state hiện tại (bước ends_checked) -> {valid, errors, table_md}."""
    req = R.load(request_id)
    st = R.get_state(req["request_id"], name)
    R.require_step(st, "ends_checked")
    ends = (R._rjson(os.path.join(R.iface_dir(req["request_id"], name), "ends.json")) or {}).get("ends") or {}
    values = recut_values(st, values)                                    # 009: cut lại giữ arc step lần trước
    kept = None
    if st.get("recut_from"):                                             # 004/012: lựa chọn lần trước còn hợp lệ
        from . import recut
        kept = {r["refdes"]: r["old"] for r in
                recut.compare_handling((st.get("recut_old") or {}).get("handling"), ends) if r["result"] == "kept"}
    eff = effective_handling(ends, handling, kept)
    res = validate(values, eff, ends, (st.get("content") or {}).get("structural"))
    rows = proposal(st, ends, values)["rows"]
    return {"valid": res["valid"], "errors": res["errors"], "table_md": table_md(rows, eff), "rows": rows,
            "P": res["P"], "ends": ends, "values": values, "handling": eff}


def agreed_values(state, request_id=None, name=None):
    """Giá trị đã chốt lần apply gần nhất (state.settings.values) + structural của content.
    009: có request_id -> khoá có lịch sử mặc định (arc step) còn thiếu lấy từ user_settings.json của interface,
    không có thì mặc định thời tool_version của request (lần chạy cũ giữ giá trị của nó)."""
    from . import defaults_history as H
    v = dict((state.get("settings") or {}).get("values") or {})
    if request_id:
        from . import user_settings as U
        doc = R._rjson(U.path(request_id)) or {}
        sec = ((doc.get("interfaces") or {}).get(name) or {}).get("values") or {}
        for k in H.HISTORY:
            if k not in v and k in sec:
                v[k] = sec[k]
        v = H.fill(v, doc.get("tool_version") or "<0.7.0")
    v.update((state.get("content") or {}).get("structural") or {})
    return v


def validate_reapply(request_id, name, values, handling=None):
    """006: interface đã apply / merge -> chỉ cho đổi nhóm sim (setup / sweep / airbox). -> như validate_for."""
    from ..cut_board import config
    if not isinstance(values, dict):
        raise CopilotInputError("values", "JSON object {key: value}", values)
    req = R.load(request_id)
    st = R.get_state(req["request_id"], name)
    R.require_step(st, REAPPLY_STEPS)
    rows = {r["key"]: r for r in _rows()}
    agreed = agreed_values(st, req["request_id"], name)
    old_h = dict((st.get("settings") or {}).get("handling") or {})
    errors = []
    for k, v in values.items():
        if k not in rows:
            continue                                                    # build_params báo "không có trong template"
        if group_of(k) == "cut":
            ref = agreed.get(k, rows[k]["default"])
            same = str(v) == str(ref)
            if not same:
                try:
                    same = config.coerce(v, rows[k]["type"]) == config.coerce(ref, rows[k]["type"])
                except ValueError:
                    same = False
            if not same:
                errors.append(f"{k}: {CUT_LOCKED_MSG}")
    if handling is not None and dict(handling) != old_h and handling != {}:
        errors.append(f"handling: {CUT_LOCKED_MSG}")
    merged = {k: v for k, v in agreed.items()}
    merged.update({k: v for k, v in values.items() if k not in rows or group_of(k) == "sim"})
    P, errs = config.build_params({k: v for k, v in merged.items()})
    errors += errs
    prop_vals = {k: v for k, v in merged.items() if not _structural(k)}
    trows = proposal(st, None, prop_vals)["rows"]
    for r in trows:
        if group_of(r["key"]) == "cut":
            r["locked"], r["reason"] = True, "already cut - locked (re-cut to change)"
    return {"valid": not errors, "errors": errors, "table_md": table_md(trows, old_h), "rows": trows,
            "P": P if not errors else None, "handling": old_h, "values": prop_vals}


def no_gnd_ends(request_id, name):
    """015: {refdes: unusual no_gnd_pin} của interface (từ ends.json). Chỉ đọc."""
    ends = (R._rjson(os.path.join(R.iface_dir(request_id, name), "ends.json")) or {}).get("ends") or {}
    return {rd: u for rd, e in ends.items() for u in e.get("unusual") or [] if u.get("rule") == "no_gnd_pin"}


GND_GATE_MSG = ("GND: show the image + options of {ends} as a multiple-choice question (never choose), wait for the "
                "user's answer, then call again with user_approved_gnd=true.")


def apply_route(request_id, name, values, handling, user_approved_gnd=False):
    """Tool isim_apply (sau cờ GATE B): apply hay re-apply (006) + kiểm tra.
    -> (op, kwargs, None) hoặc (None, None, {refused, reason, ...}). Lỗi kiểm tra khác (CopilotInputError) đi thẳng ra."""
    def refuse(msg, **extra):
        return None, None, {"refused": True, "reason": msg, **extra}
    try:
        req = R.load(request_id)
        st = R.get_state(req["request_id"], name)
    except ValueError as ex:
        return refuse(str(ex))
    rid = req["request_id"]
    if st["step"] in REAPPLY_STEPS:                                    # 006: chỉ setup / sweep / airbox
        chk = validate_reapply(rid, name, values, handling or None)
        if not chk["valid"]:
            return refuse("Re-apply: chỉ đổi được setup / sweep / airbox - báo người dùng các lỗi.",
                          errors=chk["errors"])
        return "reapply", {"request_id": rid, "name": name, "values": values}, None
    if st["step"] != "ends_checked":
        return refuse(f"Cần chạy isim_check_ends trước; bước hiện tại: {st['step']}.")
    ng = no_gnd_ends(rid, name)
    if ng and not user_approved_gnd:                                   # 015: tấm GND chỉ sau lựa chọn người dùng
        return refuse(GND_GATE_MSG.format(ends=", ".join(sorted(ng))), ends=sorted(ng),
                      images={rd: (u.get("values") or {}).get("image") for rd, u in ng.items()})
    chk = validate_for(rid, name, values, handling)
    if not chk["valid"]:
        return refuse("Thông số chưa hợp lệ - báo người dùng các lỗi.", errors=chk["errors"])
    return "apply", {"request_id": rid, "name": name, "values": values, "handling": handling}, None


def validate_any(request_id, name, values, handling=None):
    """Theo bước: ends_checked -> validate_for; applied / merged -> validate_reapply."""
    req = R.load(request_id)
    st = R.get_state(req["request_id"], name)
    if st.get("step") in REAPPLY_STEPS:
        return validate_reapply(request_id, name, values, handling)
    return validate_for(request_id, name, values, handling)
