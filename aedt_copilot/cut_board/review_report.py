"""Mẫu báo cáo layout review (feature 026; hình thức mới 033, contract: specs/033-review-report-redesign/contracts/
review-report-033.md).

Báo cáo = một CÁCH XEM dữ liệu review (không đo lại): header 3 dòng (035: không còn kết luận gate) -> mỗi connection một tab:
Summary (mỗi mục một dòng OK / NOT OK + số issue) -> mục 2.x (danh sách check từ steering, dòng OK / NOT OK, bảng
Index / Verdict / Description / Picture chỉ các dòng NOT OK; 2.1 Routing có khung đi dây từng cặp). Issue = finding
status NOT OK (036: không còn mức nặng nhẹ). Thuần (không EDB); HTML tiếng Anh (luật người dùng 2026-10-22).
"""
import html
import os

from ..core.errors import CopilotInputError
from . import review_units as U

MM = 1e-3
NOK = "NOT OK"

# key, title, prefix, câu ngắn của Summary (033: thứ tự cố định Routing, Reference, Trace stub, Via, Stackup; 028:
# finding nào thuộc mục nào do steering của luật khai báo; mục khác (vd. Crosstalk) chỉ hiện khi có finding)
SECTIONS = (
    ("routing", "Routing", "RTE", "Pair gap, serpentine."),
    ("reference", "Reference", "REF", "Trace has a solid GND reference."),
    ("trace_stub", "Trace stub", "STB", "No open trace ends or T-branches."),
    ("via", "Via", "VIA", "Via stubs and nearby GND vias."),
    ("Stackup", "Stackup", "STK", "Trace width and gap match stackup."),
)
_SPECS = None


def report_specs():
    """028: {tên finding: spec} gộp từ REPORT của các module check (registry). Trùng tên finding -> RegistryError."""
    global _SPECS
    if _SPECS is None:
        from ..core.errors import RegistryError
        from ..review_checks import checks
        out, owner = {}, {}
        for name, m in checks().items():
            for chk, spec in (getattr(m, "REPORT", None) or {}).items():
                if chk in out:
                    raise RegistryError(f"finding '{chk}' described by {owner[chk]} and {name}")
                out[chk], owner[chk] = spec, name
        _SPECS = out
    return _SPECS


def _check_chans(chans):
    if not isinstance(chans, list) or not all(isinstance(c, dict) for c in chans):
        raise CopilotInputError("chans", "list of review channel dicts", type(chans).__name__)


def section_of(check):
    """Tên finding -> key mục (REPORT của module check); không khai báo -> mục riêng (key = tên check)."""
    return (report_specs().get(check) or {}).get("section") or check


def _prefix(name):
    ws = [w for w in str(name).replace("_", " ").split() if w]
    if len(ws) >= 3:
        return "".join(w[0] for w in ws).upper()[:4]
    return "".join(ch for ch in str(name) if ch.isalnum()).upper()[:3] or "CHK"


def sections(chans):
    """-> [{key, title, prefix, sentence}]: 5 mục cố định, rồi check lạ theo thứ tự gặp (check mới = mục mới)."""
    _check_chans(chans)
    out = [{"key": k, "title": t, "prefix": p, "sentence": c} for k, t, p, c in SECTIONS]
    seen = {s["key"] for s in out}
    for c in chans:
        for f in c.get("findings") or []:
            k = section_of(f["check"])
            if k not in seen:
                seen.add(k)
                out.append({"key": k, "title": k, "prefix": _prefix(k), "sentence": ""})
    return out


def rows(chans):
    """-> {key mục: [row]}: mỗi điểm bất thường (gộp net + vị trí như cũ) tách theo mục, chỉ finding NOT OK."""
    secs = sections(chans)
    out = {s["key"]: [] for s in secs}
    for ci, c in enumerate(chans, 1):
        for pi, p in enumerate(c.get("points") or []):
            by = {}
            for f in p["items"]:
                if f["status"] == NOK:
                    by.setdefault(section_of(f["check"]), []).append(f)
            for k, items in by.items():
                r = {"channel": c.get("name"), "ci": ci, "pi": pi, "point": p["id"], "net": p["net"],
                     "x": p["x"], "y": p["y"], "status": NOK, "items": items}
                img = (c.get("images") or {}).get(f"{p['id']}|{k}")      # review.review: (svg, legend, note, sig, pl)
                if img:
                    r.update(img=img[0], legend=img[1], note=img[2], signals=img[3], planes=img[4])
                out[k].append(r)
    for s in secs:
        rs = out[s["key"]]
        rs.sort(key=lambda r: (r["ci"], r["pi"]))
        w = 3 if len(rs) > 99 else 2
        for i, r in enumerate(rs, 1):
            r["index"] = f"{s['prefix']}-{i:0{w}d}"
            r["anchor"] = "r-" + r["index"]
    return out


def counts(chans):
    """-> {key mục: {channel: số finding NOT OK}}; channel lỗi không có số."""
    secs = sections(chans)
    out = {s["key"]: {} for s in secs}
    for c in chans:
        if c.get("error"):
            continue
        for s in secs:
            out[s["key"]][c.get("name")] = 0
        for f in c.get("findings") or []:
            if f["status"] == NOK:
                out[section_of(f["check"])][c.get("name")] += 1
    return out


def row_layers(items, ref_layers, metal):
    """FR-005: lớp liên quan của một dòng -> (lớp tín hiệu, lớp plane, ghi chú). Chỉ tên có trong metal, theo stackup."""
    sig, pl, note = set(), set(), ""
    specs = report_specs()
    for f in items:
        fn = (specs.get(f["check"]) or {}).get("layers")
        got = fn(f, ref_layers, metal) if fn else None
        if got is not None:
            sig |= set(got[0])
            pl |= set(got[1])
        else:
            if f.get("layer") in metal:
                sig.add(f.get("layer"))
            note = "involved layers unknown — issue layer only"
    order = {n: i for i, n in enumerate(metal)}
    pl = sorted((p for p in pl if p in order), key=order.get)
    sig = sorted((s for s in sig if s in order and s not in pl), key=order.get)
    return sig, pl, note




# ----------------------------------------------------------------------------- HTML
OK_HTML, NOK_HTML = "<b class='okk'>OK</b>", "<b class='nok'>NOT OK</b>"


def _e(x):
    return html.escape(str(x))


def _mm(v):
    return f"{v / MM:.3f}"


def explain(f, P, c=None):
    """026 / 028: một phát hiện -> (tiêu đề, [(nhãn, giá trị)], why, fix) cho dữ liệu / chat (HTML 033 không hiện).
    Chữ do REPORT của module check cung cấp; không có -> khối chung (vị trí, lớp, giá trị đo)."""
    spec = report_specs().get(f["check"])
    if spec and spec.get("describe"):
        rows_, why, fix = spec["describe"](f, P, c)
        return spec.get("title") or f["check"], rows_, why, fix
    xy = f"({_mm(f['x'])}, {_mm(f['y'])}) mm"
    return f["check"], [("At", xy), ("Layer", str(f.get("layer") or "")), ("Measured", str(f.get("value")))], "", ""


def _planes(ref):
    return " and ".join(r.split(":")[0].strip() for r in str(ref or "").split(",") if r.strip()) or "its reference plane"


def fields(f):
    """Placeholder chung cho câu Issue / Recommendation của steering."""
    net = str(f.get("net") or "").rstrip("*")
    return {"net": net, "layer": f.get("layer") or "", "planes": _planes(f.get("ref")),
            "group": " / ".join(f.get("group") or list(f.get("lengths_mm") or {})) or net,   # pair skew: lengths_mm
            "other_net": f.get("other_net") or "another net",
            "what": "a T-branch" if "T-junction" in str(f.get("value")) else "an open trace end",
            "value": f.get("value") or ""}


def issue_rec(f, P, c=None):
    """033: (Issue, Recommendation) một câu mỗi dòng, lấy từ steering của luật (## Issue / ## Recommendation; biến thể
    theo tên finding); luật không có câu -> câu chung từ tên + giá trị đo."""
    from ..review_checks import _rules as X
    spec = report_specs().get(f["check"]) or {}
    rid = spec.get("rule")
    fm = fields(f)
    if spec.get("fields"):
        fm.update(spec["fields"](f, P) or {})
    iss = rec = ""
    if rid:
        var = f["check"] if X.has_text(rid, "issue", f["check"]) else None
        iss = X.text(rid, "issue", var, **fm)
        var = f["check"] if X.has_text(rid, "recommendation", f["check"]) else None
        rec = X.text(rid, "recommendation", var, **fm)
    if not iss:
        iss = f"{fm['net']} ({fm['layer']}): {spec.get('title') or f['check']} — {fm['value']}."
    if not rec:
        rec = "Check the layout at this location and fix it."
    return iss, rec


def _desc(r, P, c=None):
    seen, o = set(), []
    for f in r["items"]:
        iss, rec = issue_rec(f, P, c)
        if (iss, rec) in seen:
            continue
        seen.add((iss, rec))
        lk = (report_specs().get(f["check"]) or {}).get("limit_key")
        hover = f"check {f['check']}; point #{r['point']}; finding {f.get('id')}" + (f"; limit {lk}" if lk else "")
        o.append(f"<div class='iss' title='{_e(hover)}'><div><b>Issue:</b> {U.wrap(_e(iss))}</div>"
                 f"<div><b>Recommendation:</b> {U.wrap(_e(rec))}</div></div>")
    return "".join(o)


def _pic(r, P):
    loc = f"<div class='loc'><b>Location:</b> X = {U.span(r['x'])}, Y = {U.span(r['y'])}</div>"
    if not r.get("img"):
        return (f"<div>No picture: only the first {_e(P.get('max_images'))} rows per connection are drawn.</div>"
                + loc)
    note = f"<div>{U.wrap(_e(r['note']))}</div>" if r.get("note") else ""
    cls = "" if r["img"].startswith("<div class='rpanels'") else " class='pw'"
    return f"<div{cls}>{r['img']}{loc}{note}</div>"


def _n_issues(n):
    return f"{n} issue{'s' if n != 1 else ''}"


def _rule_order():
    from ..review_checks import checks
    return list(checks())


def _intro(key, order):
    """'This section checks:' + danh sách đánh số từ mục '## Report' của steering các luật thuộc mục."""
    from ..review_checks import _rules as X
    lines = X.section_lines(key, order)
    if not lines:
        return ""
    return ("<div class='intro'><div>This section checks:</div>"
            + "".join(f"<div>{i}. <b>{_e(n)}:</b> {U.wrap(_e(t))}</div>" for i, (n, t) in enumerate(lines, 1))
            + "</div>")


def _tab(info, c, k, order):
    """Một tab = report đầy đủ của một connection (id tiền tố t<k>-)."""
    from . import review_routing as RT
    P = info["params"]
    pre = f"t{k}-"
    secs = sections([c])
    rs = rows([c])
    cn = counts([c])
    name = c.get("name") or "?"
    o = [f"<h2 id='{pre}summary'>1. Summary</h2>"]
    if c.get("error"):
        o.append(f"<p><b class='nok'>Review incomplete</b>: {_e(c['error'])}</p>")
    o.append("<table class='sum'><colgroup><col class='c-i'><col class='c-s'><col><col class='c-v'></colgroup>"
             f"<tr><th>Index</th><th>Section</th><th>{_e(name)}</th><th>Verdict</th></tr>")
    nis = {}
    for i, s in enumerate(secs, 1):
        n = (cn.get(s["key"]) or {}).get(name) or 0
        nis[s["key"]] = n
        if c.get("error"):
            cell, verdict = "<td>review incomplete</td>", NOK_HTML
        else:
            cell = f"<td>{NOK_HTML}<br>{_n_issues(n)}</td>" if n else f"<td>{OK_HTML}</td>"
            verdict = NOK_HTML if n else OK_HTML
        sent = s.get("sentence") or ""
        o.append(f"<tr><td>{i}</td><td><b>{_e(s['title'])}</b>" + (f"<br>{U.wrap(_e(sent))}" if sent else "")
                 + f"</td>{cell}<td>{verdict}</td></tr>")
    o.append("</table>")
    for si, s in enumerate(secs, 1):
        key = s["key"]
        o.append(f"<h2 id='{pre}sec-{_e(key)}'>2.{si} {_e(s['title'])}</h2>")
        o.append(_intro(key, order))
        if key == "routing":
            o.append(RT.section_html(c.get("routing")))
        if c.get("error"):
            o.append(f"<p class='lead'>{NOK_HTML} — review incomplete</p>")
            continue
        n = nis[key]
        if not rs[key]:
            o.append(f"<p class='lead'>{NOK_HTML} — {_n_issues(n)}</p>" if n else f"<p class='lead'>{OK_HTML}</p>")
            continue
        o.append(f"<p class='lead'>{NOK_HTML} — {_n_issues(n)}</p>")
        o.append("<table class='rep'><colgroup><col class='c-i'><col class='c-vd'><col><col class='c-p'></colgroup>"
                 "<thead><tr><th>Index</th><th>Verdict</th><th>Description</th><th>Picture</th></tr></thead><tbody>")
        for j, r in enumerate(rs[key], 1):
            o.append(f"<tr id='{pre}{_e(r['anchor'])}'><td>{j}</td><td>{NOK_HTML}</td>"
                     f"<td>{_desc(r, P, c)}</td><td class='pic'>{_pic(r, P)}</td></tr>")
        o.append("</tbody></table>")
    return "".join(o)


CSS = """
body{font-family:'Segoe UI',Arial,sans-serif;font-size:12px;color:#000;background:#fff;margin:16px 20px}
h1{font-size:18px;margin:0 0 6px}h2{font-size:14px;margin:24px 0 6px;border-bottom:2px solid #1f4e78;padding-bottom:3px}h3{font-size:14px;margin:14px 0 4px}
.hdr div{margin:2px 0}.gv{margin-right:14px}
table{border-collapse:collapse;margin:4px 0 10px}th,td{border:1px solid #9aa5b1;padding:4px 6px;vertical-align:top;
background:#fff}th{background:#dce6f2;text-align:center;font-weight:bold}
b.okk{color:#0050c8}b.nok{color:#d00000}
table.sum{table-layout:fixed;width:100%;max-width:1100px}table.sum td{text-align:center;vertical-align:middle}
table.sum td:nth-child(2){text-align:left}col.c-i{width:56px}col.c-s{width:270px}col.c-v{width:130px}
table.rep{table-layout:fixed;width:100%}col.c-vd{width:80px}col.c-p{width:600px}
table.rep td:nth-child(-n+2){text-align:center;vertical-align:middle}
.iss{margin:2px 0 8px;line-height:1.45}.iss+.iss{border-top:1px dashed #ccc;padding-top:6px}
.pw{max-width:390px}.loc{margin-top:3px}.meas{margin-top:4px}.intro{margin:4px 0 8px}.lead{margin:6px 0}
.tabs{display:flex;flex-wrap:wrap;gap:4px;border-bottom:2px solid #1f3b63;margin:14px 0 10px}
.tabb{padding:6px 16px;border:1px solid #1f3b63;border-bottom:none;border-radius:4px 4px 0 0;background:#fff;
cursor:pointer;font-weight:bold;font-size:12px;color:#000}.tabb.on{background:#dce6f2}
.pbox{border:1px solid #888;border-radius:4px;padding:6px 12px;margin:8px 0}.pbox summary{cursor:pointer}
.leg2{display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center;margin:4px 0}
.lg i{display:inline-block;width:18px;height:4px;vertical-align:middle;margin-right:5px}.lg i.v{width:6px;height:14px}
.ovx{overflow-x:auto;max-width:100%}.xsh{margin:6px 0 2px}
table.topo td,table.topo th{text-align:center;padding:2px 8px}table.topo td.l{text-align:left}
.zb{display:block;margin:4px 0;padding:2px 10px;font-size:12px;cursor:pointer;border:1px solid #888;border-radius:3px;
background:#fff}.zb.on{background:#dce6f2}
"""

TABS_JS = """
(function(){const bs=[...document.querySelectorAll('.tabb')],ps=[...document.querySelectorAll('.tabp')];
function show(t){ps.forEach(p=>p.style.display=p.dataset.t==t?'block':'none');
 bs.forEach(b=>b.classList.toggle('on',b.dataset.t==t));}
bs.forEach(b=>b.onclick=()=>show(b.dataset.t));if(bs.length)show(bs[0].dataset.t);})();
"""


def render(info, chans):
    """HTML tự chứa (033): header 3 dòng -> tab mỗi connection (Summary + mục 2.x) từ MỘT lượt đo."""
    _check_chans(chans)
    from . import review_routing as RT
    order = _rule_order()
    board = os.path.basename(info["board"].replace("\\", "/").rstrip("/"))
    stem = board[:-5] if board.lower().endswith(".aedb") else board
    o = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>"
         "<meta name='viewport' content='width=device-width,initial-scale=1'><title>Layout review</title>"]
    src = info.get("source") or {}
    if src:                                           # 027: nguồn dữ liệu (không hiện; header chỉ 3 dòng)
        o.append(f"<meta name='board-data' content='{_e(src.get('kind', 'live'))}"
                 + (f" ({_e(src['seconds'])} s)" if src.get("seconds") is not None else "") + "'>")
    o.append(f"<meta name='generator' content='Ansys AEDT Copilot v{_e(info.get('version', ''))}'>"
             f"<style>{CSS}{U.CSS}</style></head><body>")
    o.append("<h1>Layout Review — Pre-cut</h1><div class='hdr'>"
             f"<div><b>Layout version:</b> {_e(stem)}</div>"
             f"<div><b>Review date:</b> {_e(info['date'])}</div>{U.SWITCH_HTML}")
    if src.get("warning"):                            # 027: lùi về đọc live
        o.append(f"<div><b>Board data warning:</b> {_e(src['warning'])}</div>")
    o.append("</div><div class='tabs'>")
    o += [f"<button type='button' class='tabb' data-t='{k}'>{_e(c.get('name') or '?')}</button>"
          for k, c in enumerate(chans, 1)]
    o.append("</div>")
    for k, c in enumerate(chans, 1):
        hide = "" if k == 1 else " style='display:none'"
        o.append(f"<div class='tabp' data-t='{k}'{hide}>{_tab(info, c, k, order)}</div>")
    o.append(f"<script>{TABS_JS}{RT.ZOOM_JS}{U.JS}</script></body></html>")
    return "".join(o)
