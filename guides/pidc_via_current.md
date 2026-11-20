<!-- PI-DC skill: current of every power via from the DC solver files (.vcd/.vias), worst segment vs IPC via capacity (finished hole), FAIL/WARN, and 3 SIwave via-current images with circled vias. Called by pidc_workflow. -->
# PI-DC SKILL — VIA CURRENT

## 1. MISSION
Rate every power via by its current (A) against the IPC capacity of its finished hole. Show where the highest-current vias are.

## 2. INPUT
- `<run>.vias`: `!VIA_n r_inner_mm r_drill_mm from to` (r_drill = finished hole radius).
- `<run>.vcd`: `!VIA_n "net" x_m y_m "layer_from" "layer_to" J_A/m²` (one line per via segment).
- Images from `pidc_export`: `ALL_POWER/VIACUR_<TOP|BOTTOM>.png` (power vias only, filter tag `<via-current>1</via-current>`), `ALL_NETS/VIACUR_TOP.png` (GND + power).
- Cross-check: `raw/element_data/Vias.txt` (`ScrExportElementData(sim, file, 'Vias')`).

## 3. RULES
| Item | Rule |
|---|---|
| Segment current | `I = |J| × π (r_drill² − r_inner²)` (r_inner = 0 → filled via) |
| Physical via | same net + same x, y (mm, 3 decimals) |
| Via current | WORST segment. Never sum segments |
| Capacity | `I_cap = 0.024 × dT^0.44 × (3.14 × r_mil²)^0.725`, r = finished hole radius in mil. Same for every layer span |
| dT | `dT = T_sim − pidc.via_base_temp_C` (25 °C). T_sim = `GlobalTemperature` of the DC run (`<run>/<run>.cfg`, = SIwave DC board temperature). T_sim missing or dT ≤ 0 → the tool STOPS (never guess a dT). dT outside 10..100 °C → warning in the result: report it. Always state T_sim, T_base, dT |
| Verdict | util = I / I_cap: FAIL > 1, WARN > `pidc.via_warn_util` = 0.8, else PASS |
| Units | amperes (A), never A/mm² |
| Nets | power nets rated; GND vias shown for information only |
| Type | through (first–last metal), blind (touches one outer layer), buried (none) — information |

## 4. IMAGES (2800×1400, colour bar in A on the left, layout cropped to the via area)
| File | Background | Circled (red) |
|---|---|---|
| `VIA_POWER_<top>.png` | SIwave via current of power vias at the top layer | power vias FAIL/WARN + top `pidc.via_top_n` (5) by current at that layer |
| `VIA_POWER_<bottom>.png` | same at the bottom layer (shows blind vias to bottom) | same |
| `VIA_ALL_<top>.png` | all vias (GND + power) at the top layer | power selection above + top 5 GND vias |
Label = current at that layer + net (+ FAIL/WARN). Circle positions: via x, y (mm) mapped with the board calibration, snapped to the nearest SIwave marker. Labels of close vias are stacked in a column with leader lines.

## 5. EXECUTION
`pidc_via_current(folder, sim_name)` → `results/via_current.json` (vias, gnd_top, images, crosscheck, verdict). Do not compute anything yourself.

## 6. REPORT TO USER
Verdict; every FAIL/WARN via (net, x/y mm, drill, worst segment, I, I_cap, util); worst 5 power vias; highest GND via (info); cross-check ratio (expect ≈ 1).
