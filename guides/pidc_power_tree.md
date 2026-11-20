<!-- PI-DC skill: SIwave DC power tree (VRM -> series R/ferrite -> loads) exported by script with threshold specifications (default: Include Yes, 100 A, Percentage 3 %, aggregate pins ON, power-loss list OFF), Pass/Fail per load. User may change voltage/current. Called by pidc_workflow. -->
# PI-DC SKILL — POWER TREE

## 1. MISSION
Export SIwave's DC power tree of the solved run with the user's threshold specifications and list Pass/Fail per load.

## 2. DEFAULT SETTINGS (user 2026-10-28, same as the SIwave "Export DC Power Tree" dialog)
| Setting | Default | Template key |
|---|---|---|
| Include | Yes | `pidc.pt_include` |
| Current threshold | 100 A | `pidc.pt_current_A` |
| Voltage threshold type | Percentage | `pidc.pt_voltage_type` (Percentage / Value) |
| Voltage | 3 (%) | `pidc.pt_voltage` |
| Aggregate pins on a net within a component as one block | ON | `pidc.pt_aggregate_pins` |
| Output power loss of every net (list under the image) | OFF | `pidc.pt_output_power_loss` |
The user may ask to change **voltage** and **current**: pass them to `pidc_power_tree(folder, voltage=..., current=...)` for that run (do not edit the template unless the user asks for a new team default). Never change them on your own.

## 3. HOW IT WORKS (no GUI)
1. `ScrActivateDcPowerTreePinAggregation`, `ScrShowDcPowerTreePowerLossOfNets` set the two check boxes.
2. A first `ScrExportDcPowerTree(sim, specs_probe.csv, probe_tree.png)` with a header-only spec file lists every node (env `GENERATE_POWERTREE_TEXT_FILE=1` → `<png>.txt`).
3. The spec CSV is written for every node AND every current/voltage source name of the `.siw` (aggregated load nodes take their spec from the source rows). Format = SIwave "Export Specifications":
   `Include,Component Name,Current Threshold (A),Voltage Threshold,Voltage Percentage (%),Voltage Value (V)`.
4. The final `ScrExportDcPowerTree` → `images/POWER_TREE.png` (SIwave rendering) + `<png>.txt` (tree) + `<png>.pwrLoss.txt` (env `GENERATE_POWERLOSS_TEXT_FILE=1`).
Runs SIwave directly on the user's folder (~1 min), never saves. Does not need `pidc_export`.

## 4. PASS / FAIL (per load = leaf node, as SIwave)
- Voltage: Percentage → actual V within VRM Vout × (1 ± %); Value → actual V ≥ value. Else `Fail_V`.
- Current: actual I > current threshold → `Fail_I`.
- Drop = VRM Vout − load V (mV, %). The tree image also shows SIwave's own ΔVp/ΔVg/ΔW per load; if a borderline result differs from the image, the image (SIwave) wins — say so.
- Skill verdict: FAIL if any load fails, else PASS. Each failing load appears in the report Summary.

## 5. EXECUTION
`pidc_power_tree(folder, sim_name[, voltage, current])` → `results/power_tree.json` (settings, VRM, loads with V/I/drop/spec/result, power loss per net, tree edges) and `images/POWER_TREE.png`.

## 6. REPORT TO USER
Settings used; VRM name and Vout; table of loads (result, load, rail, fed-from component, V, I, drop mV/%, spec) worst drop first; count FAIL/total. Remind that voltage/current can be changed on request.
