# Implementation Plan: PI-DC + layout edit fixes

**Branch**: `main` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Six fixes from the boardb_19x19 PI-DC run (package, RDL layers) plus layout edit: VRM voltage by header name, narrow /
tiny copper never silent, empty power net list stops, 0 checked pairs never PASS, `delete` of vias, image width 10000,
via ΔT from the simulation. Patch 0.14.1. Results of BOARDB_B04 (`pidc_check`) and `layout_edit_b04` unchanged where
a fix does not apply.

### Finding during planning (item 1)

SIwave column "Series R Voltage(V)" is not always the I x R drop:

| Board | Column | I x R_source | Meaning |
|---|---|---|---|
| boardb_19x19 (76 VRM) | 1.2e-8 V … | equal | drop on the source R → output = Magnitude − column |
| BOARDB_B04 VCC_0P8V (remote sense, `..._SENSE` source 0.8 V) | 0.8114 V | 8.1e-6 V | the VRM output (user-approved 811.42 mV) |

Rule (FR-002 detail): column ≈ I x R (relative 1e-3 or absolute 1e-12) → `V = Magnitude − column`
(`V_source = "magnitude - series R drop"`); column empty → `V = Magnitude`; otherwise → `V = column`
(`V_source = "series R voltage column (remote sense)"`). B04 stays 811.42 mV; 19x19 DDR_VDDQ ≈ set voltage.

### 1. SIwave source tables by header (`pi_dc/report.py`)

| Function | What |
|---|---|
| `table_rows(tab, required)` | SIwave table (row 0 group titles, row 1 headers without "Name", data from row 2) → `[{"Name": .., <header>: ..}]`; header row missing a required name → positional fallback (today's indices) + `warning` |
| `vrm_sources(tabs)` | Voltage Sources with a current → `{name, net, terminal, V_set, R_ohm, I_A, series_V, V, V_source}` (rule above) |
| `load_sources(tabs)` | Current Sources → `{name, net, terminal, I_A, V}` (`Voltage(V)`) |

`voltage_distribution._sources` and `report.dcir` use them (no index access left). Report DCIR table: Name, V set,
R, Net, I, Series R V, **V out**, how.

### 2. Current density narrow / tiny copper (`skills/current_density.py`)

Order inside `analyse` (steps 1–2 = today, so B04 pairs measured today are identical):
1. 0.5 mm window, copper ≥ `cd_min_copper_frac` → as today.
2. none → 0.5 mm window, copper ≥ 0.2 → as today (`narrow_copper`).
3. none, or copper with current < 0.05 mm² (today NO_DATA) → **narrow path**:
   - label copper pieces (8-connected); pieces < `pidc.cd_tiny_area_mm2` (0.002) dropped from the evaluation;
   - nothing left → status `INFO`, reason "only tiny copper (< 0.002 mm2)", `peak_util` kept (never PASS / FAIL);
   - else window `pidc.cd_narrow_window_mm` (0.1 mm), mean J over copper pixels only, windows with copper fraction ≥
     half the best window's fraction; judged vs limit (PASS / WARN / FAIL), `narrow_window: true`,
     `window_mm: 0.1`, reason "narrow copper (0.1 mm window)". Pin-node masking applies as today.
- `run`: counts add `INFO`; verdict = FAIL > PENDING > WARN > PASS as today, but **`NO_DATA` when no pair is
  PASS / WARN / FAIL / PENDING** (0 checked pairs never PASS).
- Report: card shows INFO; INFO pairs with `peak_util > 1` listed in the "peak above limit" INFO table; table note for
  the narrow window.

### 3. Empty power net list (`pi_dc/common.py`)

`Ctx`: `.siw` without `B_PWR_GND_NETS_MOD_GEN` nets, or with only GND nets → `CopilotInputError`-style
`RuntimeError`: "<siw>: no power/ground net list (SIwave Net Manager → mark power / ground nets, save the .siw,
re-run the DC sim)". Raised before any export (also stops `pidc_report`). `voltage_distribution`: composite with no
finite pixel → `PENDING` (no crash).

### 4. layout_edit delete vias (`edit_layout/ops.py`, `run.py`)

`op_delete(ids)`: id of a region primitive / new polygon → as today; id of a padstack instance in the region
(`R.inst`, as listed by `layout_region` vias) → `.Delete()` on the .NET instance, `gone_vias` updated so
`all_vias()` (antipads, via rules, checks) no longer sees it, `ch["deleted_vias"]` {id, pd, net, x, y, from, to};
a **component pin** id → error (nothing saved). Unknown id → error as today. Result `{"deleted": n, "vias": k}`.
`touched` includes deleted vias (images of their start / stop layers). `changes.md` row shows it. Guide row updated.
Found in implement: `layout_region` listed only via counts → output adds `vias` (id, net, padstack, x, y, from, to;
max 200). Check "Via đã xoá" confirms the via is gone in the saved file; deleted vias are not counted as lost contacts.
A plan with only `delete` needs `region` (error before the copy).

### 5. Image width (`templates/pidc_template.csv`, `pi_dc/export.py`)

Default 10000; `export` adds `warnings` ("image_width > 10000: SIwave caps it") to the result / manifest and logs it.

### 6. Via ΔT from the simulation (`pi_dc/common.py`, `skills/via_current.py`)

- `common.sim_temperature(ctx)` → `GlobalTemperature` of `<run>/<run>.cfg` (float °C); missing file / key →
  `RuntimeError` naming the file.
- Template: remove `pidc.via_dT_C`; add `pidc.via_base_temp_C` = 25.
- `via_current.run`: `dT = T_sim − via_base_temp_C`; `dT ≤ 0` → stop (formula gives no capacity; message names both
  temperatures); outside 10..100 °C → warning. `load_vias(base, metals, P, dT)`. Result `temperature` {T_sim_C,
  T_base_C, dT_C, source, warnings}. Report text shows the three values.
- B04: GlobalTemperature 60 → ΔT 35 = old default → via results identical; `pidc_check` reference gets a `_doc`
  note (ΔT now from the run). boardb_19x19: 90 → ΔT 65.

## Kitchen check

| Item | Answer |
|---|---|
| Utensils added | none |
| Process tools added | none |
| Tool inputs | unchanged |
| Outputs | `pidc_current_density`: status INFO, verdict NO_DATA possible, `narrow_window`; `pidc_via_current`: `temperature`; `layout_edit`: `deleted_vias` |
| Safety / gate | unchanged |
| Catalog + contract | `layout_edit` description: delete takes primitive or via ids; contract `contracts/pidc-layout-016.md` |
| Recipes affected | none |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| Changed | `pi_dc/{common,report,export}.py`, `pi_dc/skills/{current_density,via_current,voltage_distribution}.py`, `edit_layout/{ops,run}.py`, `templates/pidc_template.csv`, guides `pidc_*`, `layout_edit`, `kitchen/catalog.py` (text) |
| Tests | `tests/unit/test_pidc_layout_016.py`: header parsing (19x19 + B04 rows as fixtures, header missing → fallback), VRM rule, narrow / tiny copper on synthetic J images, verdict NO_DATA, empty net list error, T_sim parse + missing error, ipc_cap(2 mil, 60) = 0.9107, dT ≤ 0 stop, delete via with fake EDB (via / pin / primitive), image width warning; golden tests (pre002 / pre013 pidc params) normalised for the 016 template change |
| Offline checks | `pidc_check` on BOARDB_B04 copy with `--skip-export` (no SIwave); rerun on a COPY of boardb_19x19 `--skip-export`; `tests/layout_edit_b04.py` identical + a delete-via plan on an B04 copy |
| Not run | power_tree (opens SIwave), export (opens SIwave) |

## Constitution Check (1.2.0)

| Principle | Check | Status |
|---|---|---|
| I Gates | none touched | PASS |
| II Data safety | user folders read only; reruns on copies; layout edit on copies | PASS |
| III Defaults | new values only as template rows (`cd_narrow_window_mm`, `cd_tiny_area_mm2`, `via_base_temp_C`) | PASS |
| IV Guides | rules in `pidc_*` / `layout_edit` guides | PASS |
| V Regression | pidc_check + layout_edit_b04 | PASS |
| VII Contracts | contract file; errors at entry | PASS |
| VIII Package | header parsing shared in `report.py`; T_sim in `common` | PASS |
| IX Stable interface | tool names / params unchanged; removed template row documented in CHANGELOG (patch) | PASS |
| X Kitchen | see Kitchen check | PASS |
