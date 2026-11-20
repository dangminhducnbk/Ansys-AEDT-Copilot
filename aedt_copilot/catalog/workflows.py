"""Danh mục workflow (contract: specs/020-rename-catalog-workflows/contracts/catalog.md).

Workflow = file Markdown: front matter YAML (name, title, description, inputs, guide, steps[{tool, note,
checkpoint}]) + thân bài tự do. Nhóm: <repo>/workflows (chỉ chủ repo sửa). Cá nhân: env AEDT_COPILOT_WORKFLOWS hoặc
~/.aedt_copilot/workflows (tạo khi lưu lần đầu). Trùng tên giữa nhóm và cá nhân -> 2 mục, không ghi đè ngầm.
2.0.0 (020): thư mục cá nhân cũ (env AEDT_COPILOT_RECIPES, ~/.aedt_copilot/recipes) vẫn ĐỌC, không bao giờ ghi / xoá;
khoá bước cũ `utensil` đọc như `tool`. Tên trùng thư mục cá nhân mới -> mục cũ `shadowed`, get không trả về.
"""
import difflib
import glob
import os
import re

from ..core.errors import CopilotInputError

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOURCES = ("team", "personal")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONT = re.compile(r"^﻿?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)(.*)$", re.S)
OLD_STEP_KEY = "utensil"                              # khoá bước trước 2.0.0 (file cá nhân cũ)
OLD_ENV, OLD_DIR = "AEDT_COPILOT_RECIPES", "recipes"  # thư mục cá nhân trước 2.0.0 (chỉ đọc)


def team_dir():
    return os.path.join(ROOT, "workflows")


def personal_dir():
    return os.path.abspath(os.environ.get("AEDT_COPILOT_WORKFLOWS") or
                           os.path.join(os.path.expanduser("~"), ".aedt_copilot", "workflows"))


def legacy_dirs():
    """Thư mục cá nhân cũ (chỉ đọc), bỏ trùng với thư mục mới / thư mục nhóm."""
    cands = [os.environ.get(OLD_ENV), os.path.join(os.path.expanduser("~"), ".aedt_copilot", OLD_DIR)]
    seen = {os.path.normcase(os.path.realpath(personal_dir())), os.path.normcase(os.path.realpath(team_dir()))}
    out = []
    for d in cands:
        if not d:
            continue
        k = os.path.normcase(os.path.realpath(d))
        if k not in seen:
            seen.add(k)
            out.append(os.path.abspath(d))
    return out


def _text_list(v, field):
    if v in (None, ""):
        return []
    if isinstance(v, str):
        return [v]
    if not isinstance(v, list) or not all(isinstance(x, (str, int, float)) for x in v):
        raise CopilotInputError(field, "list of text", v)
    return [str(x) for x in v]


def parse(text, source, path=""):
    """Markdown -> workflow dict + broken (bước có tool không có trong danh mục) + misplaced."""
    import yaml
    from .tools import by_name, PROCESS_GUIDES
    if source not in SOURCES:
        raise CopilotInputError("source", "team or personal", source)
    if not isinstance(text, str):
        raise CopilotInputError("front matter", "Markdown text starting with --- YAML ---", type(text).__name__)
    m = FRONT.match(text)
    if not m:
        raise CopilotInputError("front matter", "--- YAML --- block at the top", text[:60])
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as ex:
        raise CopilotInputError("front matter", "valid YAML", str(ex).splitlines()[0]) from ex
    if not isinstance(fm, dict):
        raise CopilotInputError("front matter", "YAML mapping (key: value)", type(fm).__name__)
    name = fm.get("name")
    if not isinstance(name, str) or not SLUG.match(name):
        raise CopilotInputError("name", "slug [a-z0-9-]+ (e.g. cut-sweep-merge)", name)
    guide = fm.get("guide") or ""
    if not isinstance(guide, str):
        raise CopilotInputError("guide", "guide name (text)", guide)
    raw = fm.get("steps")
    if raw in (None, ""):
        raw = []
    if not isinstance(raw, list):
        raise CopilotInputError("steps", "list of {tool, note?, checkpoint?}", raw)
    steps = []
    for i, s in enumerate(raw):
        if isinstance(s, str):
            s = {"tool": s}
        if isinstance(s, dict) and "tool" not in s and OLD_STEP_KEY in s:
            s = dict(s, tool=s[OLD_STEP_KEY])                           # file cũ (trước 2.0.0)
        if not isinstance(s, dict) or not isinstance(s.get("tool"), str) or not s["tool"].strip():
            raise CopilotInputError("steps", "list of {tool, note?, checkpoint?}", s)
        cp = s.get("checkpoint", False)
        if not isinstance(cp, bool):
            raise CopilotInputError(f"steps[{i}].checkpoint", "true or false", cp)
        steps.append({"tool": s["tool"].strip(), "note": str(s.get("note") or ""), "checkpoint": cp})
    if not steps and not guide:
        raise CopilotInputError("steps", "at least one step, or a guide", raw)
    cat = by_name()
    misplaced = sorted({s["tool"] for s in steps if s["tool"] in cat and cat[s["tool"]]["kind"] == "process"
                        and PROCESS_GUIDES.get(cat[s["tool"]]["group"]) != guide})   # tool quy trình lạc chỗ
    return {"misplaced": misplaced, "name": name, "title": str(fm.get("title") or name),
            "description": str(fm.get("description") or ""), "inputs": _text_list(fm.get("inputs"), "inputs"),
            "guide": guide, "steps": steps, "source": source, "path": path,
            "broken": sorted({s["tool"] for s in steps if s["tool"] not in cat}), "body": m.group(2).strip()}


def _files(folder):
    return sorted(glob.glob(os.path.join(folder, "*.md")))


def _load(path, source):
    with open(path, encoding="utf-8") as f:
        return parse(f.read(), source, path)


def _entry(r):
    return {"name": r["name"], "title": r["title"], "description": r["description"], "source": r["source"],
            "steps": len(r["steps"]), "checkpoints": sum(1 for s in r["steps"] if s["checkpoint"]),
            "guide": r["guide"], "broken": r["broken"], "misplaced": r["misplaced"], "path": r["path"]}


def _folder_items(folder, source):
    items = []
    for p in _files(folder):
        try:
            items.append(_entry(_load(p, source)))
        except CopilotInputError as ex:
            items.append({"name": os.path.splitext(os.path.basename(p))[0], "title": "", "description": "",
                          "source": source, "steps": 0, "checkpoints": 0, "guide": "", "broken": [],
                          "misplaced": [], "path": p, "error": str(ex)})
    return sorted(items, key=lambda e: e["name"])


def list_workflows():
    """Mọi *.md: nhóm, rồi cá nhân (thư mục mới, rồi thư mục cũ), mỗi thư mục theo tên. File lỗi -> mục có `error`.
    Mục ở thư mục cũ trùng tên một mục cá nhân đã có -> `shadowed` = đường dẫn bản đang dùng."""
    out = _folder_items(team_dir(), "team")
    personal = _folder_items(personal_dir(), "personal")
    seen = {e["name"]: e["path"] for e in personal}
    for d in legacy_dirs():
        for e in _folder_items(d, "personal"):
            e["legacy_folder"] = True
            if e["name"] in seen:
                e["shadowed"] = seen[e["name"]]
            else:
                seen[e["name"]] = e["path"]
            personal.append(e)
    return out + personal


def get(name, source=""):
    if source not in ("",) + SOURCES:
        raise CopilotInputError("source", "team or personal (or empty)", source)
    all_ = list_workflows()
    entries = [e for e in all_ if e["name"] == name and not e.get("shadowed") and (not source or e["source"] == source)]
    if not entries:
        pool = sorted({e["name"] for e in all_})
        raise CopilotInputError("name", "workflow name, closest: " +
                                ", ".join(difflib.get_close_matches(str(name), pool, 5, 0.3) or pool[:5]), name)
    if len(entries) > 1:
        raise CopilotInputError("source", "team or personal (workflow exists in both)", name)
    e = entries[0]
    if e.get("error"):
        raise CopilotInputError("name", "workflow that parses: " + e["error"], name)
    return _load(e["path"], e["source"])


def save(name, markdown, overwrite=False):
    """Ghi <personal_dir>/<name>.md (không bao giờ ghi thư mục nhóm hay thư mục cá nhân cũ)."""
    if not isinstance(name, str) or not SLUG.match(name):
        raise CopilotInputError("name", "slug [a-z0-9-]+", name)
    if not isinstance(overwrite, bool):
        raise CopilotInputError("overwrite", "true or false", overwrite)
    d = personal_dir()
    if os.path.normcase(os.path.realpath(d)) == os.path.normcase(os.path.realpath(team_dir())):
        raise CopilotInputError("personal folder", "a folder other than the team workflows folder", d)
    r = parse(markdown, "personal")
    if r["name"] != name:
        raise CopilotInputError("name", f"same as front matter name '{r['name']}'", name)
    path = os.path.join(d, name + ".md")
    if os.path.exists(path) and not overwrite:
        raise CopilotInputError("name", "new name or overwrite=true", name)
    os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(markdown if markdown.endswith("\n") else markdown + "\n")
    r["path"] = path
    return r


def list_md(entries):
    rows = ["| Workflow | Source | Steps | Checkpoints | Description | Status |", "|---|---|---|---|---|---|"]
    for e in entries:
        if e.get("error"):
            status = "error: " + e["error"]
        elif e.get("shadowed"):
            status = "shadowed (newer copy: " + e["shadowed"] + ")"
        elif e["broken"]:
            status = "broken: " + ", ".join(e["broken"])
        elif e.get("misplaced"):
            status = "misplaced (process tool outside its process): " + ", ".join(e["misplaced"])
        else:
            status = "ok"
        steps = str(e["steps"]) + (f" (guide {e['guide']})" if e.get("guide") else "")
        src = e["source"] + (" (old folder)" if e.get("legacy_folder") else "")
        rows.append(f"| `{e['name']}` | {src} | {steps} | {e['checkpoints']} | {e['description']} | {status} |")
    return "\n".join(rows) + "\n"
