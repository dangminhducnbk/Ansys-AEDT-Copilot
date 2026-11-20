"""Tên / đường dẫn / yêu cầu channel dùng chung (1.0.0, feature 017: chuyển nguyên văn từ excel_io.py và propose.py
khi bỏ luồng Excel). Dùng bởi review, review_checks, interface_sim, design_tools."""
import os
import re


def board_paths(board):
    """.aedt hoặc .aedb -> (aedb, aedt hoặc None)."""
    b = board.rstrip("\\/")
    if b.lower().endswith(".aedt"):
        return b[:-5] + ".aedb", b
    if b.lower().endswith(".aedb"):
        aedt = b[:-5] + ".aedt"
        return b, aedt if os.path.exists(aedt) else None
    raise ValueError("Board phải là file .aedt hoặc thư mục .aedb")


def default_name(comp_a, comp_b, nets):
    pref = os.path.commonprefix(nets) if nets else ""
    pref = re.split(r"[_\W]", pref)[0] if pref else "CH"
    return f"{pref or 'CH'}_{comp_a}_{comp_b}"


def unique_name(name, taken):
    """Tên chưa dùng (so không phân biệt hoa thường, vì Windows): name, name_2, name_3..."""
    taken = {t.lower() for t in taken}
    if name.lower() not in taken:
        return name
    i = 2
    while f"{name}_{i}".lower() in taken:
        i += 1
    return f"{name}_{i}"


def parse_request(text):
    """'U14-U26:CPHY_B02DEVA_*; U21-J25:CPHY_LC2HSB_*' hoặc từng dòng -> [{comp_a, comp_b, patterns}]"""
    out = []
    for part in str(text).replace("\n", ";").split(";"):
        part = part.strip()
        if not part:
            continue
        pair, _, pats = part.partition(":")
        a, _, b = pair.replace(">", "-").replace("→", "-").partition("-")
        out.append({"comp_a": a.strip(), "comp_b": b.strip(),
                    "patterns": [p.strip() for p in pats.replace(",", " ").split() if p.strip()]})
    return out


DIFF_SUFFIX = [("_P", "_N"), ("_DP", "_DN"), ("+", "-"), ("P", "N")]
TRIO_SUFFIX = ("_A", "_B", "_C")


def group_diff(nets):
    """Ghép cặp vi sai / bộ 3 CPHY theo tên net. Trả [[net,...], ...] (net lẻ không ghép thì bỏ qua)."""
    left, groups = set(nets), []
    for n in sorted(nets):
        if n not in left:
            continue
        for sfx in [TRIO_SUFFIX] + DIFF_SUFFIX:
            if n.upper().endswith(sfx[0]):
                base = n[: len(n) - len(sfx[0])]
                g = [base + s for s in sfx]
                found = [next((x for x in left if x.upper() == m.upper()), None) for m in g]
                if all(found):
                    groups.append(found)
                    left -= set(found)
                    break
    return groups


def review_groups(nets):
    """034: ghép cặp / bộ 3 cho layout review = group_diff trên tên bỏ dấu '*' cuối (net phía tụ AC, vd SERLINK
    'X_P*'), trả lại tên gốc; mỗi tên gốc sau khi bỏ '*' chỉ giữ 1 net. group_diff giữ nguyên (Gate A / cắt)."""
    orig = {}
    for n in sorted(nets):
        orig.setdefault(n.rstrip("*"), n)
    return [[orig[m] for m in g] for g in group_diff(list(orig))]
