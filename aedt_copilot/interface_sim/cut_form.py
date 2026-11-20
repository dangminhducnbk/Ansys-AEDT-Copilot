"""Form cut settings ở GATE A (feature 022, contract: specs/022-cut-keeps-end-gnd/contracts/cut-preview.md). CHỈ ĐỌC.

Mỗi interface = một tab: các dòng template cutout.* (+ series.keep) và một ô "end factor" cho mỗi đầu (trống = tự động).
Client vẽ form như form GATE B (005): "Set default" (= default), "Copy to all tabs" (chỉ ô copy=true, KHÔNG copy hệ số
từng đầu). Submit = dữ liệu nhập: agent gọi isim_cut_preview từng tab (kiểm tra + tính lại preview); GATE A vẫn cần
người dùng đồng ý rõ ràng rồi isim_confirm_content (content.structural + content.end_factors).
"""
import os

from . import report, request as R
from .form import choices

CUT_LOCKED_REASON = "already cut - locked (re-cut to change)"
END_FACTOR_DESC = ("Factor of this end region only (same unit as cutout.expansion). Empty = automatic (raised until a "
                   "GND pin / pad is fully inside). A value is used as given and must keep a GND pin / pad inside.")


def _rows():
    from ..cut_board import config
    from .content import STRUCTURAL_KEYS, STRUCTURAL_PREFIX
    return [r for r in config.template_rows() if r["scope"] == "channel" and
            (r["key"].startswith(STRUCTURAL_PREFIX) or r["key"] in STRUCTURAL_KEYS)], config.coerce


def descriptors(c, locked, source):
    """content / proposal -> [descriptor]: thông số cut theo thứ tự template + 1 ô hệ số cho mỗi đầu. Thuần (template)."""
    from .content import structural_defaults
    rows, coerce = _rows()
    s = dict(c.get("structural") or structural_defaults())
    out = []
    unit = ""
    for t in rows:
        try:
            default = coerce(t["default"], t["type"])
        except ValueError:
            default = t["default"]
        try:
            value = coerce(s.get(t["key"], t["default"]), t["type"])
        except ValueError:
            value = s.get(t["key"])
        if t["key"] == "cutout.expansion":
            unit = t["unit"]
        out.append({"key": t["key"], "label": t["name"], "unit": t["unit"], "type": t["type"],
                    "choices": choices(t["desc"], t["type"]), "default": default, "value": value,
                    "source": source if t["key"] in (c.get("structural") or {}) else "team default",
                    "group": t["key"].split(".", 1)[0], "mandatory": False, "copy": True, "per_end": False,
                    "locked": locked, "locked_reason": CUT_LOCKED_REASON if locked else None, "desc": t["desc"]})
    ef = c.get("end_factors") or {}
    for rd in (c.get("comp_a"), c.get("comp_b")):
        out.append({"key": f"cutout.end_factor.{rd}", "label": f"End factor {rd}", "unit": unit or "-/mm",
                    "type": "num", "choices": None, "default": None, "value": ef.get(rd),
                    "source": source if rd in ef else "automatic", "group": "end factor", "mandatory": False,
                    "copy": False, "per_end": True, "refdes": rd, "locked": locked,
                    "locked_reason": CUT_LOCKED_REASON if locked else None, "desc": END_FACTOR_DESC})
    return out


def _tab(rid, name):
    from . import cut_preview as CP
    st = R._rjson(os.path.join(R.iface_dir(rid, name), "state.json"))
    c = (st or {}).get("content") or (st or {}).get("proposal")
    if not c:
        return {"name": name, "step": (st or {}).get("step") or "(not started)", "enabled": False,
                "reason": "interface not traced yet (isim_trace)", "descriptors": [], "preview": None}
    step = st["step"]
    locked = step not in CP.BEFORE_CUT
    tab = {"name": name, "step": step + (" (failed)" if st.get("failed") else ""), "enabled": True,
           "locked": locked, "reason": CUT_LOCKED_REASON if locked else None,
           "content_agreed": bool(st.get("content")),
           "descriptors": descriptors(c, locked, "agreed" if st.get("content") else "proposal"), "preview": None}
    p = CP.last(rid, name)
    if p:
        cur = None
        try:
            P, ch, nets, ends, ef, errs, _ = CP.inputs(c, name)
            cur = (not errs) and p.get("key") == CP.settings_key(P, ef, nets)
        except Exception:
            pass
        tab["preview"] = {"time": p.get("time"), "current": bool(cur), "image": p.get("image"),
                          "zooms": p.get("zooms") or {}, "extent_area_mm2": p.get("extent_area_mm2"),
                          "rows": p.get("rows") or [], "errors": p.get("errors") or []}
    return tab


def table_md(tab):
    """Bảng dự phòng khi client không vẽ được form."""
    if not tab["enabled"]:
        return f"## {tab['name']}\n\n{tab['step']}: {tab['reason']}"
    lines = [f"## {tab['name']} - cut settings" + (" (locked: already cut)" if tab["locked"] else "")]
    lines += ["", report.table(["Key", "Parameter", "Value", "Default", "Unit", "Source"],
                               [[d["key"], d["label"], "" if d["value"] is None else d["value"],
                                 "(automatic)" if d["per_end"] else d["default"], d["unit"], d["source"]]
                                for d in tab["descriptors"]])]
    p = tab.get("preview")
    if p:
        lines += ["", f"Last preview {p['time']} ({'current settings' if p['current'] else 'OLD settings: run isim_cut_preview again'}): "
                      f"{p['extent_area_mm2']} mm2, image {p['image']}"]
        lines += [f"Zoom {rd}: {z}" for rd, z in p["zooms"].items()]
        if p["errors"]:
            lines += ["Errors: " + "; ".join(p["errors"])]
    else:
        lines += ["", "No preview yet: run isim_cut_preview."]
    return "\n".join(lines)


def build(request_id=""):
    """-> {request_id, tabs[], table_md}: một tab / interface của request."""
    req = R.load(request_id)
    rid = req["request_id"]
    tabs = [_tab(rid, n) for n in req.get("interfaces") or []]
    return {"request_id": rid, "tabs": tabs,
            "table_md": "\n\n".join(table_md(t) for t in tabs) or "No interface in this request."}
