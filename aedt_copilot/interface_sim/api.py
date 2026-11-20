"""Bảng op cho CLI `python -m aedt_copilot isim --op=<op> --args=<json> | --args-file=<path>` (lớp mỏng).

Mỗi op = 1 hàm của package; tham số = khoá của JSON. MCP server gọi CLI này (tiến trình con, có pyedb).
"""
import json

from ..core.errors import CopilotInputError


def _ops():
    from . import apply, content, cut, cut_form, cut_preview, ends, form, merge, recut, request, review, run, \
        schematic, settings
    return {
        "start": _start,
        "status": request.status,
        "bom": schematic.save_bom,
        "schematic_status": schematic.status,
        "schematic_template": lambda: {"template": schematic.template()},
        "save_schematic": schematic.save,
        "trace": content.trace,
        "confirm": content.confirm,
        "cut": cut.run,
        "ends": ends.check,
        "validate": lambda request_id, name, values, handling=None: {
            k: v for k, v in settings.validate_any(request_id, name, values, handling).items() if k != "P"},
        "apply": apply.run,
        "merge_plan": _merge_plan,
        "merge": merge.run,
        "run": run.start,
        "solve_loop": run.solve_loop,
        "run_status": run.status,
        "previous": _previous,
        "recut": recut.start,
        "reapply": apply.reapply,
        "form": form.build,
        "cut_preview": cut_preview.preview,
        "cut_form": cut_form.build,
        "validate_form": form.validate,
        "review": review.run,                                           # 035: review_decide / review_override bỏ
        "config": lambda request_id="": _flow().config(request_id),     # 038
        "config_check": lambda request_id="": _flow().check(request_id),
        "go": lambda request_id="", user_words="": _flow().go(request_id, user_words),
        "layout_review": lambda request_id="": _flow().review_step(request_id),            # 039
        "review_answer": lambda request_id="", accepted=False, user_words="":
            _flow().review_answer(request_id, accepted, user_words),
    }


def _flow():
    from .config import flow
    return flow


OPS = ("start", "status", "bom", "schematic_status", "schematic_template", "save_schematic", "trace", "confirm",
       "cut", "ends", "validate", "apply", "merge_plan", "merge", "run", "solve_loop", "run_status", "previous", "recut",
       "form", "validate_form", "reapply", "review", "cut_preview", "cut_form", "config", "config_check", "go",
       "layout_review", "review_answer")


def _previous(name, workspace=""):
    from . import recut
    runs = recut.previous(name, workspace)
    return {"runs": runs, "table_md": recut.previous_md(runs) if runs else "No previous run of this interface."}


def _start(**kw):
    from . import request, schematic
    r = request.start(**kw)
    st = schematic.status(r["request_id"])
    r["schematic_status"] = st
    if not st["up_to_date"] and not st["reuse_from"]:
        r["schematic_template"] = schematic.template()
    return r


def _merge_plan(request_id="", names=()):
    from . import merge
    _, ready, missing = merge.plan(request_id, names)
    return {"ready": ready, "missing": missing}


def call(op, args=None):
    ops = _ops()
    if op not in ops:
        raise CopilotInputError("op", "one of " + ", ".join(OPS), op)
    args = args or {}
    if isinstance(args, str):
        args = json.loads(args)
    if not isinstance(args, dict):
        raise CopilotInputError("args", "JSON object", args)
    import inspect
    fn = ops[op]
    try:
        inspect.signature(fn).bind(**args)
    except TypeError as ex:
        raise CopilotInputError("args", f"arguments of {op}{inspect.signature(fn)}", str(ex)) from ex
    return fn(**args)
