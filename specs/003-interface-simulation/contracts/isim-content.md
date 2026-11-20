# Contracts: `aedt_copilot.interface_sim.content`

Tests: `tests/unit/test_isim_content.py` (diff + resolve with fake board facts); board part by `tests/isim_check.py`.

## `trace(request_id, name, refdes=(), nets=()) -> dict`

| Input | Type | Valid |
|---|---|---|
| name | str | channel name rules |
| refdes | iterable[str] | each on the board |
| nets | iterable[str] | names or fnmatch patterns; each matches ≥ 1 board net |

Precondition: at least one of refdes / nets. Opens the board READ-ONLY (`core.edb.edb_session`).

Output: `{proposal: {comp_a, comp_b, nets, diff_groups, series}, candidates (when > 2 end components: list with
pin counts), end_types {rd: type} (pre-check), schematic_diffs [...] (if schematic.md exists), structural
{cutout.*, series.keep: template defaults}, warnings, content_md}`.
Rules: only refdes → `inspect_board.trace_channel` for each pair; only nets → components on the nets (excluding
GND), 2-pin R/C/L followed as series; grouping = `propose.group_diff`. Unknown refdes / net → CopilotInputError
with up to 5 closest names (difflib) in `expected`.

Side effects: writes `<iface>/state.json` (step `started`, proposal) and `content.md`. EDB saved: no.

## `diff(board_facts, schematic) -> list[dict]`

Pure. Items: `missing_in_schematic`, `missing_on_board`, `pin_mismatch`, `name_case_or_prefix` (probable match),
`series_value` (BOM vs board). Each `{item, board, schematic, kind, probable}`.

## `confirm(request_id, name, content) -> dict`

Validates `content` (refdes on board, nets on board, groups ⊆ nets, series 2-pin, name unique in request, every
`schematic_diffs[*].resolution` filled); advances to `content_agreed`; writes `content.md`. Gate flag checked by
the MCP tool. Errors: CopilotInputError per field.
