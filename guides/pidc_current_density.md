<!-- PI-DC skill: current density per power net x metal layer from 6x SIwave DC report images - colour-bar OCR, area-averaged J (0.5 mm window), J_avg_max verdict vs A/mm2 limits, outstanding regions boxed on report-style images. Called by pidc_workflow. -->
# PI-DC SKILL — CURRENT DENSITY

## 1. MISSION
Rate each power net on each metal layer by its maximum AREA-AVERAGED current density (J_avg_max) against the layer limit. Box only outstanding regions on the images.

## 2. INPUT
`pidc_export` output: `raw/reports/<job>/report_files/CUR_<layer>.png` for `ALL_POWER` and one job per power net (filter = that net). `ALL_NETS` (unfiltered) is used for calibration only.

## 3. RULES
| Item | Rule (template `pidc.*`) |
|---|---|
| Limit | outer layers (first / last metal) `cd_outer_A_mm2` = 150 A/mm²; inner `cd_inner_A_mm2` = 100 A/mm² |
| Colour bar | 14 linear bands, read by glyph-template OCR on the bar scaled to 1000 px height. Self-check: all 15 labels parse and are linear within 0.5 %. Fail → PENDING (never PASS) |
| Pixel value | nearest band colour (RGB distance < 60) → band mid value `vmax − (k+0.5)(vmax−vmin)/14`; other pixels = no copper |
| Scale | px/mm from the board outline (`<run>.outline`) vs the coloured extent of the widest ALL_NETS layer image |
| Window average | square window `cd_window_mm` = 0.5 mm, mean J over copper pixels only; windows with < `cd_min_copper_frac` = 50 % copper are ignored (if no window qualifies, 20 % is used and the pair is flagged `narrow_copper`) |
| **Narrow copper** | still no window (thin traces, e.g. 20–40 µm RDL) or < 0.05 mm² copper with current → copper pieces < `cd_tiny_area_mm2` (0.002 mm²) are dropped; window `cd_narrow_window_mm` = 0.1 mm, mean J over copper pixels only, windows with ≥ half the copper of the best-covered window. Judged like any pair (FAIL / WARN / PASS), flagged `narrow_window`, reason "narrow copper (0.1 mm window)". Say so when reporting |
| **Tiny copper** | only pieces < 0.002 mm² (via pads) → status INFO, never PASS / FAIL; list it when its colour-bar peak is above the limit |
| J_avg_max | maximum window average of the image; location reported in mm |
| Background | median of all window averages of that image |
| Verdict | FAIL if J_avg_max > limit; WARN if > `cd_warn_frac` (50 %) × limit; else PASS. No copper / no current → NO_DATA. Missing image → PENDING |
| Board verdict with 0 rated pairs | `NO_DATA` (never PASS): say that nothing was rated and why (reasons of the pairs) |
| Outstanding region | connected area of windows ≥ min(50 % limit, `cd_bg_factor` (2) × background); kept if its J_avg_max ≥ 50 % limit OR ≥ 2 × background; at most `cd_max_regions` = 3 per image, highest first |
| **Pin-node artefact** | SIwave cannot spread a component's current over its pad: it injects/collects it at a pin NODE, so J around that node is not physical. Windows centred on a component pad (outer-layer pads from `<run>.ppb`) + `cd_pin_keepout_mm` (0.25 mm = half window) are EXCLUDED from J_avg_max, regions and verdict. Their maximum is reported as INFO "pin node" (grey dashed box). NEVER call it FAIL/WARN (user rule 2026-10-28: VCC_0P8V TOP 194.8 A/mm² on the VRM pad was a pin node, not a violation). If `.ppb` is missing: say so and treat any FAIL/WARN region on a pad as "possible pin node — needs review", not FAIL |
| Peak | colour-bar maximum = single-point value at pad/via edges → INFO only, never a verdict |
| Nets | power nets of `B_PWR_GND_NETS_MOD_GEN` minus GND/return (`(^|_)(A|D|P|S)?GND|VSS|(^|_)GROUND`). Empty list / only GND → the tools STOP with an error: tell the user to mark power / ground nets in SIwave, save, re-run the DC sim. Never invent a net list |
Board verdict = worst per-net pair (ALL_POWER images are for display).

## 4. IMAGES
- One image per ALL_POWER layer (`CD_ALL_POWER_<layer>.png`) and per net × layer with current (`CD_<net>_<layer>.png`).
- 2800×1400, colour bar on the left (native, rescaled), layout cropped to the bulk of the structure (0.5–99.5 % of coloured pixels, +4 % margin, boxes always inside), centred.
- Red 4 px box per outstanding region, label `<layer short>-R<k>: <J_avg_max> A/mm²` (TOP → T, BOTTOM → B, L8_PWR1 → L8).
- No region → title says "no outstanding region (J_avg_max …)".
- Pin node above 50 % limit → grey dashed box, label `pin node (info): <J> A/mm²`.

## 5. EXECUTION
`pidc_current_density(folder, sim_name)` → `results/current_density.json` (pairs, all_power, counts, verdict). Do not compute anything yourself.

## 6. REPORT TO USER
Per FAIL/WARN/PENDING pair: net, layer, J_avg_max, limit, util, location (mm), image name. Per ALL_POWER layer: region labels. Pin nodes: list as INFO ("pin-node artefact, not a violation"), never in the FAIL/WARN list. Caveat: quantisation 1/14 of the colour bar range.
