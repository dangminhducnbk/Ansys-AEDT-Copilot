# Contract: `aedt_copilot.kitchen.registration` + catalog additions (010)

Tests: `tests/unit/test_kitchen_guards.py`.

## `class KitchenRegistrationError(RuntimeError)`

Message: `kitchen: tool '<name>': <problem>; <problem> ...` + hint `add it to aedt_copilot/kitchen/catalog.py (Principle X)`.

## `problems(name, params) -> list[str]`

| Check | Problem text |
|---|---|
| name not in `catalog.by_name()` | `no catalog entry` |
| safety not in SAFETY | `safety '<v>' not one of read, copy, original, workspace, remote` |
| kind not in KINDS | `kind '<v>' not utensil / process` |
| safety gated and no gate | `safety '<v>' needs a gate flag` |
| gate not in params | `gate '<g>' is not a parameter` |
| contract empty | `no contract reference` |

## `make_tool(mcp) -> tool`

`tool()` → decorator `deco(fn)`: `p = problems(fn.__name__, signature params)`; `p` → raise
`KitchenRegistrationError`; else `mcp.tool()(fn)`, append name to `tool.registered`, return the result of FastMCP
(same function). Never changes name, docstring or parameters.

## Catalog additions

- `CONTRACTS: dict[str, str]` tool → repo-relative contract path; every entry gets `contract` (None if missing).
- `PROCESS_GUIDES = {"excel-cut": "workflow", "interface-sim": "interface_sim"}`.

## `recipes.parse` addition

`misplaced`: sorted step utensils whose catalog `kind == "process"` and `PROCESS_GUIDES[group] != recipe guide`.
`list_md` status order: `error` > `broken` > `misplaced` > `ok`.
