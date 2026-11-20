# Contracts — 016 PI-DC + layout edit fixes

## pi_dc.report

### `table_rows(tab: list[list[str]], required: list[str]) -> (rows: list[dict], warning: str | None)`
- In: SIwave table from `siwave_tables` (row 0 group titles, row 1 headers WITHOUT the Name column, data from row 2).
- Out: one dict per data row: `"Name"` + every header name. Header row lacking any `required` name → positional
  mapping with today's column order + `warning`.
- Never raises on short rows (skipped).

### `vrm_sources(tabs) -> list[dict]`
Rows of "Voltage Sources" with a current. Keys: `name, net, terminal, V_set, R_ohm, I_A, series_V, V, V_source`.
- `series_V` ≈ `I_A x R_ohm` (|d| ≤ 1e-3 x max(|a|, |b|) + 1e-12) → `V = V_set − series_V`, `V_source = "magnitude - series R drop"`.
- `series_V` empty → `V = V_set`, `V_source = "magnitude"`.
- else → `V = series_V`, `V_source = "series R voltage column (remote sense)"`.

### `load_sources(tabs) -> list[dict]`
Rows of "Current Sources": `name, net, terminal, I_A, V`.

## pi_dc.common

### `Ctx(folder, siw=None, sim="")`
- New error: no power / ground net list, or only GND nets → `RuntimeError` naming the `.siw` and the fix.

### `sim_temperature(ctx) -> float`
`GlobalTemperature` of `<run_dir>/<run>.cfg`. Missing file or key → `RuntimeError` naming the file.

## pi_dc.skills.current_density

- Pair status: `PASS | WARN | FAIL | PENDING | NO_DATA | INFO`. `INFO` = only copper pieces < `cd_tiny_area_mm2`
  (never in the verdict). Narrow path keys: `narrow_window: true`, `window_mm` = `cd_narrow_window_mm`.
- `run` verdict: `FAIL` > `PENDING` > `WARN` > `PASS`; `NO_DATA` when no pair is PASS / WARN / FAIL / PENDING.
  `counts` has `INFO`.

## pi_dc.skills.via_current

- `ipc_cap(r_mm, dT)` unchanged; `ipc_cap(2 * 0.0254, 60) = 0.9107` (4 decimals).
- `load_vias(base, metals, P, dT)`.
- `run`: `dT = sim_temperature − via_base_temp_C`; `dT ≤ 0` → `RuntimeError`; `dT < 10` or `> 100` → warning.
  Result adds `temperature: {T_sim_C, T_base_C, dT_C, source, warnings}`.

## pi_dc.export

- Result / manifest add `warnings` (list); `image_width > 10000` → "image_width N > 10000: SIwave caps the width at 10000".

## edit_layout.run.region(...)

- Output adds `vias`: `{columns: [id, net, padstack, x_mm, y_mm, from, to], rows, total[, note]}` — non-pin vias in the
  box (filtered by `nets` when given), sorted by net / x / y, at most 200 rows (`note` when cut).

## edit_layout.run.edit(plan)

- No `region` and no op with a position (e.g. only `delete`) → `CopilotInputError("region")` before the copy.

## edit_layout.ops.Editor.op_delete(o)

- `o["ids"]`: primitive ids or padstack instance ids (from `layout_region`).
- Via id → deleted; `ch["deleted_vias"]` {id, pd, net, x, y, from, to}; excluded from `all_vias()`.
- Component pin id → `RuntimeError("<id> is a pin of <refdes> ...")` (whole edit not saved).
- Returns `{"deleted": total, "vias": n_vias}`.

## Template `pidc_template.csv`

| Key | Change |
|---|---|
| `pidc.via_dT_C` | removed |
| `pidc.via_base_temp_C` | new, 25 °C |
| `pidc.cd_narrow_window_mm` | new, 0.1 mm |
| `pidc.cd_tiny_area_mm2` | new, 0.002 mm² |
| `pidc.image_width` | 12258 → 10000 |
