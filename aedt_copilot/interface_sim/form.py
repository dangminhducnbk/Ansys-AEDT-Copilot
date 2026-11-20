"""Form settings đầy đủ cho GATE B (feature 005, contract: isim-form.md). CHỈ ĐỌC, không mở EDB.

Mỗi interface của request = một tab; mỗi dòng template scope channel = một descriptor (khoá, nhãn, đơn vị, kiểu,
lựa chọn, mặc định nhóm, giá trị đề xuất, nhóm, bắt buộc, khoá + lý do). Client (Claude desktop widget) vẽ form,
nút "Set default" (= descriptor.default), "Copy to all tabs"; server chỉ cấp dữ liệu và kiểm tra.
Kết quả form chỉ là dữ liệu nhập: GATE B vẫn từng interface ở isim_apply.
"""
import json
import os
import re

from ..core.errors import CopilotInputError
from . import report, request as R
from . import settings as S

LOCKED_REASON = "set in content (Gate A); change = back to content + re-cut"
GATE_B_STEPS = ("ends_checked", "applied", "merged")   # 006: đã apply / merge -> re-apply nhóm sim
CUT_LOCKED_REASON = "already cut - locked (re-cut to change)"
_CHOICES = re.compile(r"^\s*(\w+(?:\s*\|\s*\w+)+)")


def choices(desc, typ):
    """Lựa chọn cho dropdown: bool -> [True, False]; mô tả bắt đầu bằng 'a | b | c' -> các từ; còn lại None."""
    if typ == "bool":
        return [True, False]
    m = _CHOICES.match(str(desc or ""))
    return [w.strip() for w in m.group(1).split("|")] if m else None


def _template():
    from ..cut_board import config
    return {r["key"]: r for r in config.template_rows() if r["scope"] == "channel"}, config.coerce


def descriptors(state, ends=None, values=None):
    """-> [descriptor] theo thứ tự template (dựa trên settings.proposal: cùng giá trị / nguồn như bảng chat)."""
    rows, coerce = _template()
    prop = S.proposal(state, ends, values)
    out = []
    for r in prop["rows"]:
        t = rows[r["key"]]
        try:
            default = coerce(t["default"], t["type"])
        except ValueError:
            default = t["default"]
        out.append({"key": r["key"], "label": r["name"], "unit": r["unit"], "type": t["type"],
                    "choices": choices(t["desc"], t["type"]), "default": default, "value": r["value"],
                    "source": r["source"], "group": r["key"].split(".", 1)[0], "mandatory": bool(r["mandatory"]),
                    "locked": bool(r["locked"]), "locked_reason": LOCKED_REASON if r["locked"] else None,
                    "desc": t["desc"], "note": r["reason"]})
    return out


def groups(descs):
    seen = []
    for d in descs:
        if d["group"] not in seen:
            seen.append(d["group"])
    return seen


def _tab(rid, name):
    st_path = os.path.join(R.iface_dir(rid, name), "state.json")
    st = R._rjson(st_path)
    if not st:
        return {"name": name, "step": "(not started)", "enabled": False, "reason": "interface not traced yet",
                "applied": False, "recut_from": None, "descriptors": [], "unusual": {}, "handling": {}}
    step = st.get("step")
    enabled = step in GATE_B_STEPS
    tab = {"name": name, "step": step + (" (failed)" if st.get("failed") else ""), "enabled": enabled,
           "reason": None if enabled else f"step {step}: settings come after isim_check_ends",
           "applied": step in ("applied", "merged"), "recut_from": st.get("recut_from"), "descriptors": [], "unusual": {},
           "handling": {}}
    if not enabled:
        return tab
    ends = (R._rjson(os.path.join(R.iface_dir(rid, name), "ends.json")) or {}).get("ends") or {}
    sett = st.get("settings") or {}
    if step in S.REAPPLY_STEPS:                                       # 006: nhóm cut khoá, nhóm sim sửa được
        agreed = {k: v for k, v in S.agreed_values(st, rid, name).items() if not S._structural(k)}
        descs = descriptors(st, ends, agreed)
        for d in descs:
            if S.group_of(d["key"]) == "cut":
                d["locked"], d["locked_reason"] = True, CUT_LOCKED_REASON
        tab.update(descriptors=descs, reapply=True,
                   note="re-apply needs a new merge (adds a new design)" if step == "merged" else
                   "re-apply: only setup / sweep / airbox")
    else:
        tab["descriptors"] = descriptors(st, ends)
    tab["unusual"] = {rd: {"rules": [u["rule"] for u in e["unusual"]],
                           "options": sorted({o for u in e["unusual"] for o in u["options"]})}
                      for rd, e in ends.items() if e.get("unusual")}
    for rd, e in ends.items():                                        # 012: đầu connector, mặc định team (đổi được)
        dh = e.get("default_handling")
        if dh and rd not in tab["unusual"]:
            tab["unusual"][rd] = {"rules": [dh["rule"]], "options": sorted(dh["options"]), "default": dh["value"]}
    if sett.get("handling"):
        tab["handling"] = dict(sett["handling"])
    elif st.get("recut_from"):                                        # cut lại (004): giữ lựa chọn cũ còn hợp lệ
        from . import recut
        tab["handling"] = {r["refdes"]: r["old"] for r in
                           recut.compare_handling((st.get("recut_old") or {}).get("handling"), ends)
                           if r["result"] == "kept"}
    for rd, u in tab["unusual"].items():
        if u.get("default") and rd not in tab["handling"]:
            tab["handling"][rd] = u["default"]
    return tab


def table_md(tab):
    """Bảng đầy đủ theo nhóm (dự phòng khi client không vẽ được form)."""
    if not tab["enabled"]:
        return f"## {tab['name']}\n\n{tab['step']}: {tab['reason']}"
    lines = [f"## {tab['name']}" + (" (applied)" if tab["applied"] else "")]
    if tab.get("note"):
        lines += ["", tab["note"]]
    descs = tab["descriptors"]
    for g in groups(descs):
        rows = []
        for d in descs:
            if d["group"] != g:
                continue
            v = "**(fill)**" if d["mandatory"] and d["value"] in (None, "") else d["value"]
            note = d["locked_reason"] if d["locked"] else (d["note"] or "")
            if d["choices"] and d["type"] != "bool":
                note = (note + " " if note and note != d["desc"] else "") + "(" + " | ".join(map(str, d["choices"])) + ")"
            rows.append([d["key"], d["label"], v, d["default"], d["unit"], d["source"], note])
        lines += ["", f"### {g}", report.table(["Key", "Parameter", "Value", "Default", "Unit", "Source", "Note"], rows)]
    if tab["unusual"]:
        lines += ["", "### unusual ends", report.table(
            ["Refdes", "Rules", "Options", "Handling"],
            [[rd, ", ".join(u["rules"]), ", ".join(u["options"]),
              (tab["handling"].get(rd) or "**(choose)**") + (" (team default)" if u.get("default") and
                                                            tab["handling"].get(rd) == u["default"] else "")]
             for rd, u in sorted(tab["unusual"].items())])]
    return "\n".join(lines)


def build(request_id=""):
    """-> {request_id, groups[], tabs[...], table_md}: một tab / interface của request (thứ tự request)."""
    req = R.load(request_id)
    rid = req["request_id"]
    tabs = [_tab(rid, n) for n in req.get("interfaces") or []]
    descs = next((t["descriptors"] for t in tabs if t["descriptors"]), [])
    return {"request_id": rid, "groups": groups(descs), "tabs": tabs,
            "table_md": "\n\n".join(table_md(t) for t in tabs) or "No interface in this request."}


def validate(request_id, entries):
    """entries {interface: {values, handling}} -> {results{name: {valid, errors, table_md}}, all_valid}. Không ghi."""
    if isinstance(entries, str):
        try:
            entries = json.loads(entries)
        except ValueError as ex:
            raise CopilotInputError("entries", "JSON object {interface: {values, handling}}", entries[:80]) from ex
    if not isinstance(entries, dict) or not entries:
        raise CopilotInputError("entries", "JSON object {interface: {values, handling}}", entries)
    req = R.load(request_id)
    rid = req["request_id"]
    known = {n.lower(): n for n in req.get("interfaces") or []}
    bad = [n for n in entries if str(n).lower() not in known]
    if bad:
        raise CopilotInputError("entries", "interfaces of this request: " + ", ".join(known.values()), bad)
    results = {}
    for n, e in entries.items():
        name = known[str(n).lower()]
        e = e if isinstance(e, dict) else {}
        try:
            r = S.validate_any(rid, name, e.get("values") or {}, e.get("handling") or None)
            results[name] = {"valid": r["valid"], "errors": r["errors"], "table_md": r["table_md"]}
        except CopilotInputError as ex:                                # lỗi của tab này không chặn tab khác
            results[name] = {"valid": False, "errors": [str(ex)], "table_md": ""}
    return {"results": results, "all_valid": all(r["valid"] for r in results.values())}
