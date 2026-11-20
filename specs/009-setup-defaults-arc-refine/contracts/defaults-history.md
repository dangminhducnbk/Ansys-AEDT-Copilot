# Contract: `aedt_copilot.interface_sim.defaults_history`

Tests: `tests/unit/test_defaults_history.py`.

## `HISTORY: dict[str, list[tuple[tuple[int, int, int], value]]]`

Team default of a template key from a tool version on, oldest first. Invariant (tested): the last value of every key
equals the template default; versions strictly increase.

## `NOT_YET`

Sentinel: the key did not exist in that version.

## `default_at(key, tool_version) -> value | NOT_YET | None`

| Input | Rule |
|---|---|
| key not in HISTORY | `None` (no history: current template default applies) |
| tool_version older than the first entry (incl. `"<0.7.0"`, unparsable) | `NOT_YET` |
| otherwise | value of the last entry with version ≤ tool_version |

## `fill(values, tool_version) -> dict`

Copy of `values` + every HISTORY key that is missing and whose `default_at` is a value. Keys present are never changed.

## `effective(values, P) -> dict`

Copy of `values` + every HISTORY key that is missing, taken from P (`P[section][name]`). Used when saving agreed values.

## Callers

| Caller | Use |
|---|---|
| `user_settings.update` | before stamping the current `tool_version`: `fill` every interface `values` with the OLD doc version; the section being saved: `effective` is applied by the caller |
| `settings.save(..., P)` | `effective(values, P)` |
| `settings.agreed_values(state, tool_version)` | `fill` |
| `settings.proposal` (re-cut) | old value kept; `default_changes` lists keys whose kept value ≠ template default |
| `recut.ADDED_IN` | `{k: HISTORY[k][0][0]}` |
