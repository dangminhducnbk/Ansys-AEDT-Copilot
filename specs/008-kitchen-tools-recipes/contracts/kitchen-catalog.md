# Contracts: `aedt_copilot.kitchen.catalog`

Pure data + helpers. Tests: `tests/unit/test_kitchen.py`.

## `UTENSILS: list[dict]`

One entry per MCP tool of `mcp_server/server.py` (data-model "Utensil"). Invariants (tested):
- names unique; the set equals the set of `@mcp.tool` functions in the server (AST);
- `safety` ∈ `read, copy, original, workspace, remote`; `kind` ∈ `utensil, process`;
- `safety` ∈ `original, workspace, remote` → `gate` is a parameter of that tool in the server;
- every utensil named in a team recipe exists here.

## `utensils(group="", kind="", safety="") -> list[dict]`

Filters (each optional, validated against the allowed values → CopilotInputError naming the filter). Output keeps
catalog order.

## `catalog_md(entries) -> str`

Markdown table grouped by `group`: `| Utensil | Kind | Safety (gate) | What it does | Inputs → Outputs |`.

## `by_name() -> dict[str, dict]`
