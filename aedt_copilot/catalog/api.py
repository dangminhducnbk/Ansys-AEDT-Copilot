"""Bảng thao tác của danh mục (CLI `catalog --op=...`, MCP list_tools / list_workflows / get_workflow /
save_workflow). Không cần AEDT."""
from ..core.errors import CopilotInputError
from . import tools as catalog_tools, workflows


def tools(group="", kind="", safety=""):
    entries = catalog_tools.tools(group, kind, safety)
    return {"tools": entries, "count": len(entries), "table_md": catalog_tools.catalog_md(entries)}


def workflow_list():
    entries = workflows.list_workflows()
    return {"workflows": entries, "table_md": workflows.list_md(entries), "team_dir": workflows.team_dir(),
            "personal_dir": workflows.personal_dir(), "old_personal_dirs": workflows.legacy_dirs()}


def get(name, source=""):
    return workflows.get(name, source)


def save(name, markdown, overwrite=False):
    return workflows.save(name, markdown, overwrite)


OPS = {"tools": tools, "workflows": workflow_list, "get": get, "save": save}


def call(op, args):
    if op not in OPS:
        raise CopilotInputError("op", "one of " + ", ".join(OPS), op)
    if not isinstance(args, dict):
        raise CopilotInputError("args", "JSON object", args)
    try:
        return OPS[op](**args)
    except TypeError as ex:
        raise CopilotInputError("args", f"arguments of {op}", str(ex)) from ex
