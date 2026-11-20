# Contracts: `aedt_copilot.catalog` (tools, workflows, registration, api) + MCP / CLI

Rewritten from `specs/008-*/contracts/{kitchen-catalog,recipes,mcp-tools}.md` and `specs/010-*/contracts/registration.md`
(2.0.0, feature 020): same rules, new names. Tests: `tests/unit/test_catalog.py`, `tests/unit/test_catalog_guards.py`,
`tests/unit/test_rename_020.py`.

## `catalog.tools.TOOLS: list[dict]`

One entry per MCP tool of `mcp_server/server.py`. Invariants (tested):
- names unique; the set equals the set of `@tool()` functions in the server (AST);
- `safety` ∈ `read, copy, original, workspace, remote`; `kind` ∈ `tool, process`;
- `safety` ∈ `original, workspace, remote` → `gate` is a parameter of that tool in the server;
- `contract` = repo path of a file that names the tool in backticks;
- every tool named in a team workflow exists here.

## `catalog.tools.tools(group="", kind="", safety="") -> list[dict]`

Filters (each optional, validated against the allowed values → CopilotInputError naming the filter). Output keeps
catalog order. `by_name() -> dict`; `catalog_md(entries)` → `| Tool | Kind | Safety (gate) | What it does | Inputs → Outputs |`
grouped by `group`. `PROCESS_GUIDES = {"interface-sim": "interface_sim"}`.

## `catalog.workflows`

| Function | Contract |
|---|---|
| `team_dir()` | `<repo>/workflows` |
| `personal_dir()` | env `AEDT_COPILOT_WORKFLOWS` or `~/.aedt_copilot/workflows` (created on first save only) |
| `legacy_dirs()` | folders used before 2.0.0, READ ONLY: env `AEDT_COPILOT_RECIPES`, `~/.aedt_copilot/recipes` (minus the new personal / team folder) |
| `parse(text, source, path="")` | front matter YAML (`name` slug, `title`, `description`, `inputs`, `guide`, `steps[{tool, note, checkpoint}]`) + body. Step key `utensil` (pre-2.0.0 files) read as `tool`. Errors (CopilotInputError naming the field): `front matter`, `name`, `steps`, `steps[i].checkpoint`, `guide`, `inputs`. Output adds `broken` (unknown tools) and `misplaced` (process tools outside their process guide) |
| `list_workflows()` | team, then personal (new folder, then legacy folders), each sorted by name; a file that fails `parse` → entry with `error`; legacy entries get `legacy_folder: true`; a legacy entry whose name is already listed as personal gets `shadowed: <path of the copy in use>` |
| `get(name, source="")` | full workflow + body; never a `shadowed` entry; name in team and personal with `source` "" → CopilotInputError(`source`); unknown → CopilotInputError(`name`, closest names) |
| `save(name, markdown, overwrite=False)` | writes `<personal_dir>/<name>.md` only (never team, never legacy); `name` = front matter name; existing file without `overwrite` → CopilotInputError(`name`); personal folder = team folder → CopilotInputError(`personal folder`) |
| `list_md(entries)` | `| Workflow | Source | Steps | Checkpoints | Description | Status |`; status order `error` > `shadowed` > `broken` > `misplaced` > `ok` |

## `catalog.registration`

`class CatalogRegistrationError(RuntimeError)`; message `catalog: tool '<name>': <problem>; ...` + hint
`add it to aedt_copilot/catalog/tools.py (Principle X)`.
`problems(name, params)`: `no catalog entry`, `safety '<v>' not one of ...`, `kind '<v>' not tool / process`,
`safety '<v>' needs a gate flag`, `gate '<g>' is not a parameter`, `no contract reference`.
`make_tool(mcp)` → `tool()` decorator: problems → raise; else `mcp.tool()(fn)` (name / docstring / params unchanged),
name appended to `tool.registered`.

## `catalog.api.call(op, args)`

ops `tools(group, kind, safety)` → `{tools[], count, table_md}`; `workflows()` → `{workflows[], table_md, team_dir,
personal_dir, old_personal_dirs}`; `get(name, source)`; `save(name, markdown, overwrite)`. Unknown op / bad args →
CopilotInputError(`op` / `args`).

## MCP tools (thin: arguments → `catalog.api`)

| Tool | Inputs | Safety / gate | Output |
|---|---|---|---|
| `list_tools(group="", kind="", safety="")` | filters | read | `{tools[], count, table_md}` |
| `list_workflows()` | — | read | `{workflows[], table_md, team_dir, personal_dir, old_personal_dirs}` |
| `get_workflow(name, source="")` | workflow name | read | workflow + body |
| `save_workflow(name, markdown, overwrite=False)` | front matter + body | copy (personal folder only) | saved workflow + path |

Input errors come back as `{ok: false, ...}` (`input_error`).

## CLI

`python -m aedt_copilot catalog --op=<tools|workflows|get|save> --args=<json> | --args-file=<path>`; input error →
JSON `{ok: false}`, exit 2.
