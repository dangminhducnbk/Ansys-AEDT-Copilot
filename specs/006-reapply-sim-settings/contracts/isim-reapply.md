# Contracts: re-apply (feature 006)

Tests: `tests/unit/test_isim_reapply.py` (offline, fake EDB / fake cutter); board: `tests/isim_check.py --reapply`.

## `interface_sim.settings.group_of(key) -> "cut" | "sim"`

Pure. Prefix before the first `.` in `CUT_PREFIXES` / `SIM_PREFIXES`. Other → CopilotInputError(`key`, `key of
group cut or sim`, key).

## `interface_sim.settings.validate_reapply(request_id, name, values, handling=None) -> dict`

| Input | Type | Valid |
|---|---|---|
| values | dict | channel-scope keys; cut-group keys only with the agreed value |
| handling | dict \| None | None or equal to the agreed handling |

Precondition: step `applied` or `merged` (else CopilotInputError(`step`)). Output `{valid, errors[], table_md, rows,
P}` like `validate_for`. Errors listed (not raised): `<key>: đã cắt, đã khoá — cut lại để đổi`; `handling: đã cắt,
đã khoá — cut lại để đổi`; `build_params` messages. Writes nothing.

## `cut_board.cutter.reapply_sim(edb, P_old, P_new, log) -> None`

Precondition: writable Edb of a design built by `apply_stage`. Deletes the HFSS setups named `P_old.setup.name` and
`P_new.setup.name` (if present), then `apply_setup(edb, P_new, log)` and `apply_airbox(edb, P_new)`. Touches no
geometry, component, port or solder ball. Caller saves.

## `interface_sim.apply.reapply(request_id, name, values, version=None) -> dict`

Precondition: `validate_reapply` valid; interface not busy. Steps: backup copy `final/<name>_old_<time>.aedb` (never
overwrite / delete) → open → `reapply_sim` → save → metrics → `self_check` → geometry compare with previous result (ports, components pins / GND pins / `pins_extent_mm` / part with `_cut_N`
normalised, GND vias, GND by layer; component `bbox_mm` NOT compared: EDB recomputes it on reopen) →
write `result.json`, state (`reapplied[]`, `result_history[]`, step `applied`; from `merged`: `merged_before[]`,
`merged` = None) → `settings.save` (user_settings with history). Output `{name, step: "applied", aedb, backup,
metrics, warnings, self_check, geometry_same, geometry_diff, user_settings}`. Error → `request.fail`, backup kept,
re-raised.

## `interface_sim.form` (005) change

`GATE_B_STEPS = ("ends_checked", "applied", "merged")`. Applied / merged tab: `reapply: true`, descriptors pre-filled
with `state.settings.values`; every cut-group descriptor `locked` with reason `already cut - locked (re-cut to
change)`; merged tab `note` = re-apply needs a new merge. `form.validate` uses `validate_reapply` for such tabs.

## `interface_sim.user_settings.update` change

When `values` is given and the section already has `values`: append `{values, handling, settings_agreed_at}` of the
section to `history[]` before replacing. `validate_doc`: `history` must be a list when present.
