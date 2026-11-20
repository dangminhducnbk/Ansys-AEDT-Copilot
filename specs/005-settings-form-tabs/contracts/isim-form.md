# Contracts: `aedt_copilot.interface_sim.form`

Read-only (no EDB). Tests: `tests/unit/test_isim_form.py`.

## `choices(desc, typ) -> list | None`

Pure. `typ == "bool"` → `[True, False]`; Description starting with `word | word [| word ...]` → the words; else None.

## `descriptors(state, ends=None, values=None) -> list[dict]`

Pure on top of `settings.proposal(state, ends, values)`; one descriptor per channel-scope template row, template order
(data-model). Count == number of channel-scope rows (SC-001).

## `build(request_id="") -> dict`

| Input | Type | Valid |
|---|---|---|
| request_id | str | existing request ("" = latest) |

Output `{request_id, groups[], tabs[...], table_md}`; one tab per `request.json.interfaces`, request order. Tab data
from `<iface>/state.json` + `ends.json`; interfaces without state → disabled, step `(not started)`.
Errors: unknown request → CopilotInputError(`request_id`). Writes nothing.

## `table_md(tab) -> str`

Full grouped table: `### <group>` then `| Key | Parameter | Value | Default | Unit | Source | Note |`; locked rows
note = locked reason; mandatory empty → `**(fill)**`; disabled tab → one line with the step.

## `validate(request_id, entries) -> dict`

| Input | Type | Valid |
|---|---|---|
| entries | dict \| JSON str | `{interface: {values: dict, handling: dict}}`; interface ∈ request interfaces |

Per interface `settings.validate_for(request_id, name, values, handling)` (step `ends_checked`, as `isim_apply`). Output
`{results: {name: {valid, errors[], table_md}}, all_valid}`; a step / input error of one interface is reported in its
result (`valid: false`), never raised for the others. Errors: entries not an object, unknown interface →
CopilotInputError(`entries`). Writes nothing.
