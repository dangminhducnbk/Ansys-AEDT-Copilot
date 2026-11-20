"""Một file cho mọi thứ đã chốt của một request: <request folder>/user_settings.json (contract: isim-user-settings.md).

Gate A ghi content + structural, gate B ghi values + handling. Dùng để cut lại sau (feature 004), copy sang máy khác
được. Thay settings.json / settings.md của từng interface (user 2026-11-06: không tạo quá nhiều file).
"""
import json
import os

from ..core.errors import CopilotInputError
from . import request as R

FORMAT = "aedt_copilot.user_settings/1"
FILE = "user_settings.json"
SECTION_KEYS = ("content", "structural", "content_agreed_at", "values", "handling", "settings_agreed_at",
                "recut_from", "trace_args", "board_facts", "review",                  # 011: quyết định review
                "gnd_decisions")                                                     # 015: đầu không pin GND


def _version():
    from .. import __version__
    return __version__


def board_fingerprint(board):
    """size + mtime của <board>.aedb/edb.def (None nếu không có)."""
    p = os.path.join(board or "", "edb.def")
    if not board or not os.path.isfile(p):
        return None
    st = os.stat(p)
    return {"size": st.st_size, "mtime": round(st.st_mtime, 3)}


def path(request_id):
    return os.path.join(R.work_dir(R.load(request_id)), FILE)         # 038: <request>/_work/


def _new_doc(req):
    return {"format": FORMAT, "tool_version": _version(), "request_id": req["request_id"],
            "workspace": req["workspace"], "board": req["board"], "board_fingerprint": board_fingerprint(req["board"]),
            "updated": R._now(), "interfaces": {}, "replaced": []}


def _read(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _freeze_history(doc):
    """009: trước khi ghi tool_version mới, values đã chốt của mọi interface nhận các khoá có lịch sử mặc định còn
    thiếu = mặc định thời tool_version CŨ của tài liệu (chỉ thêm, không đổi khoá đã có)."""
    from . import defaults_history as H
    old = doc.get("tool_version") or "<0.7.0"
    for sec in (doc.get("interfaces") or {}).values():
        if isinstance(sec, dict) and isinstance(sec.get("values"), dict):
            sec["values"] = H.fill(sec["values"], old)


def update(request_id, name, **section):
    """Đổi đúng các khoá đã cho của interfaces[name]; tạo file nếu chưa có. -> cả tài liệu."""
    bad = sorted(set(section) - set(SECTION_KEYS))
    if bad:
        raise CopilotInputError("section", "keys among " + ", ".join(SECTION_KEYS), bad)
    req = R.load(request_id)
    name = R.check_name(name)
    p = os.path.join(R.work_dir(req), FILE)
    doc = _read(p) if os.path.isfile(p) else _new_doc(req)
    _freeze_history(doc)
    sec = doc["interfaces"].setdefault(name, {k: None for k in SECTION_KEYS})
    if "values" in section and sec.get("values") is not None:          # re-apply (006): giữ giá trị cũ
        sec.setdefault("history", []).append({k: sec.get(k) for k in ("values", "handling", "settings_agreed_at")})
    sec.update(section)
    doc["updated"] = R._now()
    doc["tool_version"] = _version()
    R.wjson(p, doc)
    return doc


def replace(request_id, name):
    """Interface quay lại 'started': chuyển mục cũ vào replaced[] (không mất dữ liệu)."""
    p = path(request_id)
    if not os.path.isfile(p):
        return
    doc = _read(p)
    sec = doc["interfaces"].pop(name, None)
    if sec is None:
        return
    doc.setdefault("replaced", []).append({"interface": name, "time": R._now(), "section": sec})
    doc["updated"] = R._now()
    R.wjson(p, doc)


# ----------------------------------------------------------------------------- đọc + kiểm tra
def _channel_keys():
    from ..cut_board import config
    return {r["key"] for r in config.template_rows() if r["scope"] == "channel"}


def _options():
    from .ends import OPTIONS
    return sorted({o for v in OPTIONS.values() for o in v})


def validate_doc(doc, where="user_settings"):
    """Kiểm tra cấu trúc; trả doc + dropped {interface: [khoá values không còn trong template]}."""
    if not isinstance(doc, dict):
        raise CopilotInputError(where, "JSON object", type(doc).__name__)
    if doc.get("format") != FORMAT:
        raise CopilotInputError("format", FORMAT, doc.get("format"))
    ifs = doc.get("interfaces")
    if not isinstance(ifs, dict):
        raise CopilotInputError("interfaces", "object {name: section}", ifs)
    keys, opts, dropped = _channel_keys(), _options(), {}
    for name, sec in ifs.items():
        R.check_name(name)
        if not isinstance(sec, dict):
            raise CopilotInputError(f"interfaces.{name}", "object", sec)
        c = sec.get("content")
        if c is not None:
            if not isinstance(c, dict) or not c.get("comp_a") or not c.get("comp_b") or \
                    not isinstance(c.get("nets"), list) or not c["nets"]:
                raise CopilotInputError(f"interfaces.{name}.content", "{comp_a, comp_b, nets[...]}", c)
        for k in ("structural", "values", "handling"):
            v = sec.get(k)
            if v is not None and not isinstance(v, dict):
                raise CopilotInputError(f"interfaces.{name}.{k}", "object", v)
        if sec.get("history") is not None and not isinstance(sec["history"], list):
            raise CopilotInputError(f"interfaces.{name}.history", "list", sec["history"])
        for rd, h in (sec.get("handling") or {}).items():
            if h not in opts:
                raise CopilotInputError(f"interfaces.{name}.handling.{rd}", "one of " + ", ".join(opts), h)
        gone = sorted(k for k in (sec.get("values") or {}) if k not in keys)
        if gone:
            dropped[name] = gone
    return dict(doc, dropped=dropped)


def load(src):
    """src = file user_settings.json hoặc thư mục request chứa nó."""
    p = os.path.abspath(str(src).strip().strip('"'))
    if os.path.isdir(p):
        w = os.path.join(p, R.WORK, FILE)                               # 038: <request>/_work/user_settings.json
        p = w if os.path.isfile(w) else os.path.join(p, FILE)
    if not os.path.isfile(p):
        raise CopilotInputError("source", "existing user_settings.json (or request folder with it)", p)
    try:
        doc = _read(p)
    except ValueError as ex:
        raise CopilotInputError("source", "valid JSON", f"{p}: {ex}") from ex
    return dict(validate_doc(doc), path=p)


def from_state(folder):
    """Request 0.6.0 (chưa có user_settings.json): dựng cùng tài liệu từ request.json + <iface>/state.json."""
    f = os.path.abspath(str(folder).strip().strip('"'))
    req = R.read_folder(f)                                              # 038: request.json trong _work/
    if req is None:
        raise CopilotInputError("source", "request folder (with request.json)", f)
    doc = _new_doc(req)
    doc["board_fingerprint"] = None                     # không biết board lúc đó
    doc["tool_version"] = "<0.7.0"
    for name in req.get("interfaces") or []:
        st = R._rjson(os.path.join(R.iface_dir_of(req, name), "state.json"))
        if not st:
            continue
        c = dict(st.get("content") or {}) or None
        stt = (st.get("settings") or {})
        doc["interfaces"][name] = {
            "content": {k: v for k, v in c.items() if k != "structural"} if c else None,
            "structural": (c or {}).get("structural"), "content_agreed_at": st.get("content_agreed_at"),
            "values": stt.get("values"), "handling": stt.get("handling") or {},
            "settings_agreed_at": None, "recut_from": st.get("recut_from"), "trace_args": st.get("trace_args"),
            "board_facts": st.get("board_facts")}
    return dict(validate_doc(doc), path=f,
                step={n: (R._rjson(os.path.join(R.iface_dir_of(req, n), "state.json")) or {}).get("step")
                      for n in doc["interfaces"]})
