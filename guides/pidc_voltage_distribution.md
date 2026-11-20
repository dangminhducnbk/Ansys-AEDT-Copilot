<!-- PI-DC skill: voltage distribution - ONE image of all power rails (GND excluded) with all metal layers overlaid, common linear scale, Vmin pin of every load and the VRM output voltage labelled; per-rail table of load Vmin and drop. Information only, no spec. Called by pidc_workflow. -->
# PI-DC SKILL — VOLTAGE DISTRIBUTION

## 1. MISSION
Show the DC voltage over every power rail in one picture and list, per rail, the voltage at the VRM and the minimum voltage at each load. Information only (user 2026-10-28: no IR-drop spec, no PASS/FAIL).

## 2. INPUT
- `ALL_POWER` job of `pidc_export` with `<voltage>1</voltage>` in its filter → `VLT_<layer>.png` (all power nets, GND excluded), in `raw/reports/ALL_POWER` (or `raw/reports_vlt/ALL_POWER` when exported later with `export(..., voltage_only=True)`).
- `raw/reports/ALL_NETS/report.htm` tables: Current Sources (load pin voltage), Voltage Sources (VRM output voltage).
- `.siw`: `CSRC "<load>" x+ y+ ...` (load pin position, mm), `X ... <part> <refdes> <pin> <flag>` pin records and `B_PIN_GROUP` (VRM position).

## 3. RULES
| Item | Rule |
|---|---|
| Image | exactly ONE: `images/VLT_ALL_POWER.png`, all power rails, GND excluded |
| Layer overlay | SIwave exports one VLT image per layer with its own auto scale. Each layer: colour bar OCR → mV per pixel. Layers drawn bottom first, TOP last (top layer covers lower ones = view from the top, as the GUI with all layers visible). Layers whose max < 50 % of the highest max (GND-only layers, a few mV) are skipped |
| Scale | one linear scale for the whole image = min..max voltage of the overlay, 14 SIwave colours, labels in mV. All rails share it (rails at different nominal voltages compress each other — say so) |
| Load Vmin | per load refdes and rail: the current-source pin with the lowest voltage (report.htm). Circle at that pin; label `<refdes>.<pin> <rail>: <V> mV` |
| VRM | voltage source with current (VRM output, not the sense source): label `VRM <refdes> (<rail>): <V> mV` at its pin group |
| VRM voltage | read by column NAME from Voltage Sources. Column "Series R Voltage" = drop on the source R when it equals I × R → output = Magnitude − column; otherwise (remote-sense VRM, e.g. BOARDB_B04 VCC_0P8V 0.811 V) the column IS the output. `V_source` in the result says which. Header missing → positional + warning (report it) |
| Drop | VRM output voltage − load Vmin (mV and %). Rails fed through ferrites/resistors have no own VRM → drop is from the upstream VRM (stated in the table) |
| Verdict | none (INFO). Never FAIL/WARN without a spec from the user |

## 4. EXECUTION
`pidc_voltage_distribution(folder, sim_name)` → `results/voltage_distribution.json` (rails, loads, scale, layers used) and the image. Do not compute anything yourself.

## 5. REPORT TO USER
Image path. Table per rail: VRM refdes + voltage, each load refdes.pin + Vmin + drop mV/%. Lowest load voltage of the board first.
