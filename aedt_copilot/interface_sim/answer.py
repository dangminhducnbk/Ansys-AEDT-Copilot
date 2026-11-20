"""Câu trả lời chuẩn cho một yêu cầu channel (feature 036, contract: specs/036-no-severity-netlist/contracts/).

Code viết sẵn câu trả lời 3 phần (vùng cut dự tính + file review + MỘT câu hỏi) để agent dán NGUYÊN VĂN, không kể bước,
không nhận xét lỗi, không nhắc linh kiện nối tiếp (luật người dùng 2026-11-14 / 15). Chỉ có khi review hiện hành có
report HTML VÀ preview cùng thông số không lỗi; thiếu -> answer_md None + lý do. Chỉ đọc file (state, review.json,
preview.json).
"""
from . import request as R

QUESTION = "Đọc review rồi xác nhận cut {name}?"


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{f:g}"


def end_line(r):
    """Một dòng mỗi đầu (tiếng Việt): hệ số, phần thêm, chân GND giữ được."""
    f = r.get("factor_used")
    fac = "-" if f is None else f"hệ số {_num(f)} ({'nhập tay' if r.get('manual') else 'tự động'})"
    if r.get("added_mm2"):
        fac += f", thêm {_num(round(r['added_mm2'], 1))} mm²"
    g = ", ".join(r.get("gnd_gained") or [])
    s = f"- {r['refdes']}: {fac}, giữ chân GND {g}" if g else f"- {r['refdes']}: {fac}, không có chân GND trong vùng cut"
    return s + (f" — LỖI: {r['error']}" if r.get("error") else "")


def _diff_line(d):
    kind = {"pin_mismatch": "chân nối khác", "missing_on_board": "net có trong schematic, không có trên board",
            "series_value": "giá trị khác"}.get(d.get("kind"), d.get("kind"))
    b = d.get("board")
    s = d.get("schematic")
    return f"- Board khác schematic: {d['item']} ({kind}; board {b}, schematic {s}): theo board / theo schematic / bỏ net?"


def questions(st):
    """Câu hỏi tool không tự quyết được: khác biệt THẬT board / schematic chưa có cách xử lý, > 2 đầu ứng viên."""
    out = [_diff_line(d) for d in st.get("schematic_diffs") or [] if not d.get("resolution")]
    ends = [c["refdes"] for c in st.get("candidates") or [] if c.get("refdes")]
    if len(ends) > 2:
        out.append(f"- Có {len(ends)} linh kiện đầu có thể chọn ({', '.join(ends[:8])}): chọn 2 đầu nào?")
    return out


def build(request_id, name):
    """-> {answer_md, answer_image, answer_files} hoặc {answer_md: None, answer_reason}."""
    from . import cut_preview as CP, review as RVW
    req = R.load(request_id)
    rid = req["request_id"]
    st = R.get_state(rid, name)
    c = CP._content(st)
    if not c:
        return {"answer_md": None, "answer_reason": "interface not traced"}
    g = RVW.gate_status(rid, name, c)
    if g["status"] not in ("ready", "approved"):
        return {"answer_md": None, "answer_reason": f"review {g['status']}: {g['message']}"}
    try:
        P, _, nets, _, ef, errs, _ = CP.inputs(c, name)
    except ValueError as ex:
        return {"answer_md": None, "answer_reason": f"cut settings: {ex}"}
    p = CP.last(rid, name)
    if errs or not p or p.get("key") != CP.settings_key(P, ef, nets):
        return {"answer_md": None, "answer_reason": "no preview for the current cut settings (isim_cut_preview)"}
    if p.get("errors"):
        return {"answer_md": None, "answer_reason": "preview errors: " + "; ".join(map(str, p["errors"]))}
    w, h = (p.get("extent_size_mm") or [0, 0])[:2]
    lines = [f"**{name}: vùng cut dự tính ({_num(w)} × {_num(h)} mm, {_num(round(p.get('extent_area_mm2') or 0))} mm²)**",
             f"Ảnh: {p.get('image')}"]
    lines += [end_line(r) for r in p.get("rows") or []]
    lines += ["", f"**Review:** {g['html']}"]
    q = questions(st)
    if q:
        lines += [""] + q
    lines += ["", QUESTION.format(name=name)]
    return {"answer_md": "\n".join(lines), "answer_image": p.get("image"),
            "answer_files": [x for x in (p.get("image"), g.get("html")) if x]}


def attach(out, request_id, name):
    """Thêm answer_md / answer_image / answer_files vào kết quả tool (không bao giờ ném lỗi)."""
    try:
        a = build(request_id, name)
    except Exception as ex:                                            # câu trả lời là phần phụ: không làm hỏng bước chính
        a = {"answer_md": None, "answer_reason": f"{type(ex).__name__}: {ex}"}
    out.update(a)
    return out
