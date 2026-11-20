"""038 fixed chat texts (PURE). Every text = Vietnamese line, then English line (FR-032). Claude pastes them verbatim.

039: M0 review table / Q0 review OK, go on to config? / M0x stopped. M1 config file written / Q1 finished? / M2 config
errors / Q2 agree to cut? / M3 cut result. Only Q0, Q1 and Q2 are questions; one answer holds at most one question.
"""
from .. import report

TEXTS = {
    "m0": ("Review layout (mỗi channel: file review, số điểm NOT OK):",
           "Layout review (per channel: review file, NOT OK points):"),
    "q0": ("Review layout ổn, chuyển sang bước config không?", "Is the layout review OK, go on to config?"),
    "m0x": ("Đã dừng theo yêu cầu. File review:", "Stopped as requested. Review files:"),
    "m1":("File config: `{path}`. Mở, kiểm tra từng khung, Save rồi trả lời *xong*.",
           "Config file: `{path}`. Open it, check every frame, Save, then reply *done*."),
    "m1_link": ("Link config: {url} — mở link, điền tên folder, bấm Save rồi trả lời *xong*. (File: `{path}`)",
                "Config link: {url} — open it, fill the folder names, press Save, then reply *done*. (File: `{path}`)"),
    "q1": ("Bạn đã config xong chưa?", "Have you finished the config?"),
    "m2": ("Config có lỗi, sửa rồi Save lại:", "The config has errors, fix them and Save again:"),
    "q2": ("Đồng ý cut không?", "Do you agree to cut?"),
    "m3": ("Kết quả cut:", "Cut result:"),
    "m0p": ("Trang review + config: {where} — mỗi channel: tab *Review layout* (điểm NOT OK trên hình, xem chi tiết, "
            "Resolve) rồi tab *Settings*. Resolve hết, Save rồi trả lời *xong*.",
            "Review + config page: {where} — per channel: tab *Review layout* (NOT OK points on the picture, details, "
            "Resolve), then tab *Settings*. Resolve all, Save, then reply *done*."),
    "res": ("{n} điểm NOT OK đã được người dùng resolve.", "{n} NOT OK points resolved by the user."),
}
QUESTIONS = ("q0", "q1", "q2")
ANSWERS = {"done": ("xong", "done"), "yes": ("đồng ý", "dong y", "yes", "ok"), "no": ("không", "khong", "no")}


def line(key, **kw):
    vi, en = TEXTS[key]
    return f"{vi.format(**kw)}\n{en.format(**kw)}"


def _review_table(rows):
    return report.table(["Channel", "Review file", "NOT OK points"],
                        [[r["name"], r.get("review_html") or ("error: " + str(r.get("error") or "-"))[:200],
                          "" if r.get("error") else r.get("not_ok", 0)] for r in rows])


def m0(rows):
    """039: rows [{name, review_html, not_ok, error}] -> M0 table + Q0 (Q0 only when every channel has a report)."""
    t = line("m0") + "\n\n" + _review_table(rows)
    return t if any(r.get("error") for r in rows) else t + "\n\n" + line("q0")


def m0x(rows):
    """039: closing text after 'no' + review files."""
    return line("m0x") + "\n\n" + "\n".join(f"- {r['name']}: {r.get('review_html') or '-'}" for r in rows)


def m0p(rows, path, url=None):
    """045: review table (file + NOT OK points per channel) + the one page (link / file). No question."""
    where = f"{url} (File: `{path}`)" if url else f"`{path}`"
    return line("m0") + "\n\n" + _review_table(rows) + "\n\n" + line("m0p", where=where)


def m0p_errors(rows):
    """045: a channel without a review report -> M0 table only (no page, no question)."""
    return line("m0") + "\n\n" + _review_table(rows)


def resolved_line(n):
    """045: Q2 line (FR-013)."""
    return line("res", n=n)


def m1(path, url=None):
    """040: with the local link (Save writes the file directly); without it the 038 text."""
    return line("m1_link", path=path, url=url) if url else line("m1", path=path)


def q1():
    return line("q1")


def m2(errors):
    rows = [[e["channel"], e["frame"], e["field"], e["message"]] for e in errors]
    return line("m2") + "\n\n" + report.table(["Channel", "Frame", "Field", "Problem"], rows)


def q2(channels, resolved=None):
    """channels: [{name, folder, image, size_mm, area_mm2, review_html, ends[str]}] -> picture + review of each channel,
    then the question (once)."""
    out = []
    for c in channels:
        w, h = (c.get("size_mm") or [0, 0])[:2]
        out.append(f"**{c['name']} → {c.get('folder') or c['name']}** — cut region {w:g} × {h:g} mm, "
                   f"{round(c.get('area_mm2') or 0):g} mm²")
        if c.get("image"):
            out.append(f"Cut region / Vùng cut: {c['image']}")
        for e in c.get("ends") or []:
            out.append(f"- {e}")
        out.append(f"Review: {c.get('review_html') or '-'}"
                   + (" (review cập nhật / review updated)" if c.get("review_updated") else ""))
        out.append("")
    if resolved is not None:                                           # 045 (FR-013)
        out += [resolved_line(resolved), ""]
    return "\n".join(out) + line("q2")


def m3(rows, merged=None, board_copy=None):
    """rows: [{name, folder, status, ports, gnd_vias, self_check, stackup, stackup_diffs, checks, warnings, error}];
    merged: project path; board_copy (042): {designs, mb, copied_now}."""
    t = report.table(["Channel", "Folder", "Status", "Ports", "GND vias", "Self-check", "Stackup = board", "Notes"],
                     [[r["name"], r.get("folder") or "", r.get("status"), r.get("ports", ""), r.get("gnd_vias", ""),
                       r.get("self_check", ""), _stackup_cell(r),
                       (r.get("error") or "; ".join(r.get("warnings") or []))[:160]]
                      for r in rows])
    tail = f"\n\nProject: {merged}" if merged else ""
    if board_copy:
        d = ", ".join(board_copy.get("designs") or []) or "-"
        tail += (f"\nBản copy board / Board copy: {d}" +
                 (f" ({board_copy.get('mb')} MB)" if board_copy.get("copied_now") else ""))
    diffs = [f"- {r['name']}: {x}" for r in rows for x in (r.get("stackup_diffs") or []) +
             [f"merged: {y}" for y in ((r.get("checks") or {}).get("stackup") or [])]]
    if diffs:
        tail += "\n\nStackup khác board / Stackup differs from the board:\n" + "\n".join(diffs[:40])
    return line("m3") + "\n\n" + t + tail


def _stackup_cell(r):
    """042: OK only when the cut design AND the merged design (when merged) equal the board stackup."""
    s = r.get("stackup") or "-"
    merged = (r.get("checks") or {}).get("stackup")
    if merged:
        return "NOT OK"
    return s


def count_questions(text):
    """Number of fixed questions in a text (test: at most one per answer)."""
    return sum(1 for k in QUESTIONS for part in TEXTS[k] if part in text) // 2


def is_answer(text, kind):
    """User reply matches one of the accepted words (both languages)."""
    t = str(text or "").strip().lower().strip(".!")
    return any(t == w or t.startswith(w + " ") for w in ANSWERS[kind])
