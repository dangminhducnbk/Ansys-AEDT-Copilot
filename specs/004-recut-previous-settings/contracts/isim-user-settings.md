# Contracts: `aedt_copilot.interface_sim.user_settings`

File `<request folder>/user_settings.json` (data-model.md). Tests: `tests/unit/test_isim_user_settings.py`.

## `path(request_id) -> str`

Output: `<request folder>/user_settings.json` (existence not checked). Errors: unknown request → CopilotInputError.

## `update(request_id, name, **section) -> dict`

| Input | Type | Valid |
|---|---|---|
| request_id | str | existing request |
| name | str | channel name rules |
| section keys | subset of `content, structural, content_agreed_at, values, handling, settings_agreed_at, recut_from, trace_args, board_facts` | else CopilotInputError(`section`, ...) |

Creates the file (header from `request.json`, `tool_version`, board fingerprint) when missing; changes only the
given keys of `interfaces[name]`; `updated` = now; atomic write. Output: the whole document.
Called by `content.confirm` (gate A: content, structural, content_agreed_at, recut_from, trace_args = the refdes / net
patterns of the trace, board_facts = pins / values used by the re-cut diff) and `settings.save`
(gate B: values, handling, settings_agreed_at).

## `replace(request_id, name) -> None`

Moves `interfaces[name]` to `replaced[]` with time (called when the interface is reset to `started`). No error when
absent.

## `load(path) -> dict`

| Input | Type | Valid |
|---|---|---|
| path | str | existing `.json` file, or a request folder containing `user_settings.json` |

Output: validated document + `dropped` (`{interface: [keys not in template]}`). Errors (CopilotInputError naming the
field): not JSON; `format` not `aedt_copilot.user_settings/1`; interface name rules; `content` without
`comp_a/comp_b/nets`; `handling` option not allowed; `values` / `structural` not a dict.

## `from_state(folder) -> dict`

0.6.0 fallback: builds the same document from `request.json` + `<iface>/state.json` of a folder without
`user_settings.json` (`values` = `state.settings.values`, `handling` = `state.settings.handling`). Errors: folder
without `request.json` → CopilotInputError(`source`, `request folder`, path).
