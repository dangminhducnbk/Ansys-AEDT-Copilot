"""Điều phối PI-DC (guides/pidc_workflow.md): export -> các skill -> report.

Thêm skill mới: module trong pi_dc/skills/ (NAME, ORDER, TITLE, run(ctx, log), NEEDS_EXPORT) + guide
guides/pidc_<NAME>.md; core.registry tự tìm (contract: specs/013-pidc-layout-core/contracts/pi_dc.md).
report.py hiển thị mọi results/<NAME>.json (mục chung nếu skill không có renderer riêng).
"""
from __future__ import annotations

import time

from ..core import registry
from ..core.errors import CopilotInputError
from ..core.validate import require_choice, require_path
from . import common, skills as _skills

_ENTRIES = registry.load(_skills, ("NAME", "ORDER", "TITLE", "run"))
SKILLS = registry.by_name(_ENTRIES)
DEFAULT = [m.NAME for m in _ENTRIES]
NEEDS_EXPORT = {m.NAME for m in _ENTRIES if getattr(m, "NEEDS_EXPORT", True)}   # power_tree tự chạy SIwave


def run_skill(folder, name, sim="", log=print, **kw) -> dict:
    """kw: tham số riêng của skill (power_tree: voltage=, current=)."""
    require_choice("name", name, list(SKILLS))
    folder = require_path("folder", folder, "dir")
    ctx = common.Ctx(folder, sim=sim)
    ctx.mkdirs()
    if name in NEEDS_EXPORT and not (ctx.raw / "manifest.json").exists():
        raise RuntimeError("Chưa export ảnh SIwave cho thư mục này: chạy pidc_export trước.")
    return SKILLS[name].run(ctx, log, **{k: v for k, v in kw.items() if v is not None})


def run(folder, sim="", skills=None, skip_export=False, log=print) -> dict:
    folder = require_path("folder", folder, "dir")
    if skills is not None:                               # None / [] = DEFAULT (như trước)
        if not isinstance(skills, (list, tuple)):
            raise CopilotInputError("skills", "list of " + ", ".join(SKILLS), skills)
        for s in skills:
            require_choice("skills", s, list(SKILLS))
    from . import export, report
    t0 = time.time()
    out = {}
    if not skip_export:
        out["export"] = export.export(folder, sim, log=log)
    for s in skills or DEFAULT:
        log(f"skill {s}")
        r = run_skill(folder, s, sim, log)
        out[s] = {"verdict": r["verdict"], "counts": r["counts"]}
    out["report"] = report.build(folder, sim)
    out["seconds"] = round(time.time() - t0)
    return out
