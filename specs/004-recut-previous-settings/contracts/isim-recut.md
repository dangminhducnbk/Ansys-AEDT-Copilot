# Contracts: `aedt_copilot.interface_sim.recut`

Tests: `tests/unit/test_isim_recut.py` (fake registry, fake board facts). Board part: `tests/isim_check.py` re-cut
scenario.

## `previous(name, workspace="") -> list[dict]`

| Input | Type | Valid |
|---|---|---|
| name | str | channel name rules |
| workspace | str | "" = workspace of the latest request; else existing `.aedt` |

Output: Previous-run records (data-model) of registry requests with the same workspace (normcase abspath) that
contain `name` (case-insensitive), newest first. Read-only. Empty list = none.

## `source(src, name="") -> dict`

`src` = request id, request folder, or `user_settings.json` path. Output `{doc, interface, section, origin}`; the
interface = `name` or the only one in the doc. Errors: unknown id / path; several interfaces and no `name`;
`name` not in doc → CopilotInputError listing the names.

## `diff(old_content, old_fp, facts, new_fp) -> list[dict]`

Pure. Items of data-model "Re-cut difference" with `resolution` "". Order: end, nets, series, groups, board file,
schematic.

## `compare_handling(old_handling, ends) -> list[dict]`

Pure. Per end in `ends` (and per old handled refdes): `kept` / `not_needed` / `needs_choice` (data-model).

## `start(request_id, name, source_ref, nets=None, version=None) -> dict`

Precondition: `request_id` is a NEW request (≠ source request) of the same workspace, interface not past `started`.
Does: `source` → `content.trace(request_id, name, refdes=[comp_a, comp_b], nets=nets or old trace_args.nets or old
nets, missing_ok=True)` (nets gone from the board are skipped and reported as `net_removed` "not found") → `diff` → state
`recut_from` + proposal content with `recut_diffs`. Output = `isim_trace` output + `recut_from`, `recut_diffs`,
`old_values`, `old_handling`, `dropped`, `previous_error` (failure reason of the old run or null). Old end refdes
not on the board → `{blocked: true, recut_diffs: [end_missing], content_md}` (nothing traced). `nets` not None and not
a list of non-empty str → CopilotInputError(`nets`). Errors: same request as source → CopilotInputError(`request_id`, `new
request`, id). EDB: read-only (as `trace`).
