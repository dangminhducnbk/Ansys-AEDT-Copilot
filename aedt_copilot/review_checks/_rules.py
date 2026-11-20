"""Luật review = một file steering review_rules/<id>.md (+ tối đa một file code review_checks/<id>.py) (feature 031,
contract: specs/031-review-rule-files/contracts/review-rules.md).

Steering là NGUỒN DUY NHẤT của: tiêu đề luật, tên finding -> tiêu đề trong báo cáo, mục báo cáo, khoá ngưỡng (hover),
câu Why / Fix của báo cáo ({placeholder} do code điền; nhiều biến thể = gạch đầu dòng `- \\`<biến thể>\\`: câu`).
Luật của team ở repo; luật cá nhân ở AEDT_COPILOT_REVIEW_RULES hoặc ~/.aedt_copilot/review_rules (giống workflow cá
nhân): trùng id -> dùng của team, của cá nhân ghi 'shadowed'; code cá nhân chỉ chạy khi người dùng bật (enabled.json).
"""
import difflib
import importlib.util
import json
import os
import re

from ..core.errors import CopilotInputError

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIELDS = ("id", "findings", "section", "not ok when", "thresholds", "limit key", "code")
OLD_FIELDS = {"severity": "not ok when"}            # 036: steering cá nhân cũ vẫn đọc được
PARTS = ("What", "Why", "Fix", "Discuss")
ENABLED = "enabled.json"
_CACHE = {}


def team_dir():
    return os.path.join(ROOT, "review_rules")


def personal_dir():
    return os.environ.get("AEDT_COPILOT_REVIEW_RULES") or os.path.join(os.path.expanduser("~"), ".aedt_copilot",
                                                                       "review_rules")


def _pairs(v):
    """'A = x; B = y' -> {A: x, B: y}; giá trị đơn -> {None: v}."""
    v = (v or "").strip()
    if "=" not in v:
        return {None: v}
    out = {}
    for part in v.split(";"):
        if "=" in part:
            k, _, x = part.partition("=")
            out[k.strip()] = x.strip()
    return out


def _variants(body):
    """Thân mục Why / Fix -> {None: câu} hoặc {biến thể: câu} (gạch đầu dòng `- \\`k\\`: câu`)."""
    lines = [l.rstrip() for l in body.strip().splitlines()]
    out = {}
    for l in lines:
        m = re.match(r"- `([^`]+)`: (.*)$", l)
        if m:
            out[m.group(1)] = m.group(2).strip()
    plain = " ".join(l.strip() for l in lines if l.strip() and not re.match(r"- `([^`]+)`: ", l))
    if out:
        if plain:                                       # 033: câu khung (vd. '{problems}') + các biến thể
            out[None] = plain
        return out
    return {None: plain}


def parse(text, path=""):
    """Nội dung steering -> dict {id, title, desc, fields, findings, section, not_ok_when, thresholds, limit_keys, code,
    parts {What, Why, Fix, Discuss}, why / fix (biến thể)}."""
    m = re.search(r"^# (.+)$", text, re.M)
    d = re.match(r"\s*<!--\s*(.*?)\s*-->", text)
    fields = {}
    for row in re.findall(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", text, re.M):
        k = row[0].strip().lower()
        k = OLD_FIELDS.get(k, k)
        if k in FIELDS and k not in fields:
            fields[k] = row[1].strip()
    parts, cur = {}, None
    for l in text.splitlines():
        h = re.match(r"^## (\w+)\s*$", l)
        if h:
            cur = h.group(1)
            parts[cur] = []
            continue
        if cur:
            parts[cur].append(l)
    parts = {k: "\n".join(v).strip() for k, v in parts.items()}
    fnd = {} if fields.get("findings", "").lower() in ("", "none") else _pairs(fields.get("findings"))
    lim = _pairs(fields.get("limit key"))
    return {"id": fields.get("id", "").split(" ")[0], "title": m.group(1).strip() if m else "", "desc": d.group(1) if d
            else "", "fields": fields, "findings": {k: v for k, v in fnd.items() if k}, "section": fields.get("section", ""),
            "not_ok_when": fields.get("not ok when", ""), "thresholds": [t.strip() for t in fields.get("thresholds", "").split(",")
                                                                    if t.strip() and t.strip() != "none"],
            "limit_keys": {k: (None if (v or "none") == "none" else v) for k, v in lim.items()},
            "code": fields.get("code", "").lower().startswith("yes"), "parts": parts,
            "why": _variants(parts.get("Why", "")), "fix": _variants(parts.get("Fix", "")),
            "issue": _variants(parts.get("Issue", "")), "recommendation": _variants(parts.get("Recommendation", "")),
            "report_lines": _report_lines(parts.get("Report", "")), "steering": path}


def _report_lines(body):
    """033: mục '## Report' -> [(tên check, câu ngắn)] từ các dòng '- Tên: câu' (danh sách 'This section checks:')."""
    out = []
    for l in (body or "").splitlines():
        m = re.match(r"\s*- \*{0,2}([^:*]+?)\*{0,2}:\s*(.+)$", l)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


class _Keep(dict):
    """format_map: placeholder thiếu giữ nguyên '{x}' (không ném lỗi trong báo cáo)."""

    def __missing__(self, k):
        return "{" + k + "}"


def missing(rule):
    """Phần bắt buộc còn thiếu."""
    out = [f for f in ("id", "section", "not ok when", "thresholds", "limit key", "code") if not rule["fields"].get(f)]
    if not rule["fields"].get("findings"):
        out.append("findings")
    out += [p for p in PARTS if not rule["parts"].get(p)]
    return out


def _read(folder):
    out = {}
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return out
    for n in names:
        if not n.endswith(".md") or n.startswith("_"):
            continue
        p = os.path.join(folder, n)
        try:
            with open(p, encoding="utf-8") as f:
                r = parse(f.read(), p)
        except OSError:
            continue
        r["id"] = r["id"] or n[:-3]
        out[r["id"]] = r
    return out


def team():
    """Luật của team (cache theo thời điểm sửa thư mục)."""
    d = team_dir()
    try:
        stamp = tuple(sorted((n, os.path.getmtime(os.path.join(d, n))) for n in os.listdir(d)))
    except OSError:
        stamp = ()
    if _CACHE.get("team_stamp") != stamp:
        _CACHE["team"], _CACHE["team_stamp"] = _read(d), stamp
    return _CACHE["team"]


def enabled_ids():
    try:
        with open(os.path.join(personal_dir(), ENABLED), encoding="utf-8") as f:
            v = json.load(f)
        return sorted(set(v)) if isinstance(v, list) else []
    except (OSError, ValueError):
        return []


def rules():
    """[{id, title, source, shadowed, has_code, enabled, steering, code, findings, section, not_ok_when, thresholds}]."""
    t, p = team(), _read(personal_dir())
    on = set(enabled_ids())
    out = []
    for src, rs in (("team", t), ("personal", p)):
        for rid, r in rs.items():
            folder = os.path.join(ROOT, "aedt_copilot", "review_checks") if src == "team" else personal_dir()
            code = os.path.join(folder, f"{rid}.py")
            out.append({"id": rid, "title": r["title"], "description": r["desc"], "source": src,
                        "shadowed": src == "personal" and rid in t, "has_code": r["code"],
                        "code_file": code if os.path.isfile(code) else None,
                        "enabled": src == "team" or rid in on, "steering": r["steering"],
                        "findings": r["findings"], "section": r["section"], "not_ok_when": r["not_ok_when"],
                        "thresholds": r["thresholds"], "incomplete": missing(r)})
    return out


def get(rule_id):
    """-> {rule, text} (team trước)."""
    if not isinstance(rule_id, str) or not rule_id.strip():
        raise CopilotInputError("rule_id", "id of a review rule (review_rules op=list)", rule_id)
    for r in rules():
        if r["id"] == rule_id and not r["shadowed"]:
            with open(r["steering"], encoding="utf-8") as f:
                return {"rule": r, "text": f.read()}
    ids = [r["id"] for r in rules()]
    raise CopilotInputError("rule_id", "one of " + ", ".join(ids) + "; closest: " +
                            ", ".join(difflib.get_close_matches(rule_id, ids, 3, 0.3) or ids[:5]), rule_id)


def _rule(rule_id):
    r = team().get(rule_id) or _read(personal_dir()).get(rule_id)
    if r is None:
        raise CopilotInputError("rule_id", "a rule with a steering file", rule_id)
    return r


def meta(rule_id):
    """-> (TITLE, RULE = câu 'not ok when') của module code: lấy từ steering (một nguồn)."""
    r = _rule(rule_id)
    return r["title"], r["not_ok_when"]


TEXT_PARTS = ("why", "fix", "issue", "recommendation")


def text(rule_id, part, variant=None, **fmt):
    """Câu Why / Fix / Issue / Recommendation (033) của báo cáo từ steering (placeholder {..} điền bằng fmt; thiếu
    -> giữ nguyên). Biến thể không có -> câu chung (hoặc biến thể đầu)."""
    if part not in TEXT_PARTS:
        raise CopilotInputError("part", " / ".join(TEXT_PARTS), part)
    v = _rule(rule_id)[part]
    s = v.get(variant) if variant in v else v.get(None, next(iter(v.values()), ""))
    return s.format_map(_Keep(fmt)) if fmt else s


def has_text(rule_id, part, variant):
    """033: steering có biến thể này của mục part không."""
    try:
        return variant in _rule(rule_id)[part]
    except CopilotInputError:
        return False


def section_lines(section, order):
    """033: [(tên check, câu ngắn)] của mọi luật thuộc mục section, theo thứ tự order (id luật, thứ tự registry) -
    danh sách 'This section checks:' của báo cáo; luật mới tự xuất hiện."""
    out = []
    for rid in order:
        try:
            r = _rule(rid)
        except CopilotInputError:
            continue
        if (r["section"] or "").strip().lower() == str(section).strip().lower():
            out += [x for x in r["report_lines"] if x not in out]
    return out


def report_lines(rule_id):
    """033: [(tên check, câu ngắn)] của mục '## Report' (rỗng = luật chỉ dữ liệu)."""
    try:
        return list(_rule(rule_id)["report_lines"])
    except CopilotInputError:
        return []


def report(rule_id, describe, layers, picture=None, fields=None):
    """-> REPORT {finding: {section, title, limit_key, describe, layers, rule, picture, fields}} lấy tiêu đề / mục / khoá
    ngưỡng từ steering. describe(f, P, c) của code trả (rows, why, fix) - why / fix lấy bằng text().
    033: picture(f, paths) -> html ảnh riêng của luật (None = ảnh zoom chung); fields(f, P) -> {placeholder: chữ} thêm
    cho câu Issue / Recommendation."""
    r = _rule(rule_id)
    lk = r["limit_keys"]
    return {f: {"section": r["section"], "title": t, "limit_key": lk.get(f, lk.get(None)), "describe": describe,
                "layers": layers, "rule": rule_id, "picture": picture, "fields": fields}
            for f, t in r["findings"].items()}


# ----------------------------------------------------------------------------- luật cá nhân có code
def set_enabled(rule_id, on):
    rs = {r["id"]: r for r in rules() if r["source"] == "personal"}
    if rule_id not in rs:
        raise CopilotInputError("rule_id", "a personal rule (review_rules op=list, source personal)", rule_id)
    if on and not rs[rule_id]["code_file"]:
        raise CopilotInputError("rule_id", "a personal rule WITH a code file <id>.py", rule_id)
    if on and rs[rule_id]["shadowed"]:
        raise CopilotInputError("rule_id", "a personal rule whose id is not a team rule (team rule wins)", rule_id)
    ids = set(enabled_ids())
    ids = ids | {rule_id} if on else ids - {rule_id}
    os.makedirs(personal_dir(), exist_ok=True)
    p = os.path.join(personal_dir(), ENABLED)
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f)
    os.replace(p + ".tmp", p)
    return dict(rs[rule_id], enabled=on)


def personal_modules():
    """Module code của luật cá nhân ĐÃ BẬT (không trùng id luật team)."""
    out = []
    t = team()
    for rid in enabled_ids():
        p = os.path.join(personal_dir(), f"{rid}.py")
        if rid in t or not os.path.isfile(p):
            continue
        spec = importlib.util.spec_from_file_location(f"aedt_copilot_personal_rule_{rid}", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.SOURCE = "personal"
        out.append(mod)
    return out


# ----------------------------------------------------------------------------- danh sách cho guide
BEGIN, END = "<!-- rules:begin (generated: python -m aedt_copilot review-rules --op=guide-list) -->", "<!-- rules:end -->"


def guide_list():
    rows = ["| Rule id | Title | Findings | NOT OK when | Thresholds |", "|---|---|---|---|---|"]
    for r in rules():
        if r["source"] != "team":
            continue
        rows.append(f"| `{r['id']}` | {r['title']} | {', '.join(r['findings']) or '(data)'} | {r['not_ok_when']} | "
                    f"{', '.join('`' + t + '`' for t in r['thresholds']) or '-'} |")
    return "\n".join(rows)


def run_op(op, args):
    a = dict(args or {})
    if op == "list":
        return {"rules": rules(), "personal_dir": personal_dir(), "team_dir": team_dir()}
    if op == "get":
        return get(a.get("rule_id"))
    if op in ("enable", "disable"):
        return {"rule": set_enabled(a.get("rule_id"), op == "enable")}
    if op == "guide-list":
        return {"markdown": guide_list(), "begin": BEGIN, "end": END}
    raise CopilotInputError("op", "list / get / enable / disable / guide-list", op)
