# Contract: end GND rule of the cut (feature 022)

Module `aedt_copilot/cut_board/end_gnd.py`. Units: mm unless named `_m`. (Corrected 2026-11-10, spec 814383c: no
maximum, detection first.)

## params(P) -> dict

`{base, step, margin_mm, unitless}` from `P["cutout"]` (`expansion`, `end_expansion_step`, `end_region_margin_mm`,
`expansion_unitless`). Validated by `config.build_params`: step > 0, margin ≥ 0, else errors
`cutout.end_expansion_step: …` / `cutout.end_region_margin_mm: …`.

## factor(base, step, k) -> float

Pure. `base + k·step` (k = 1, 2, …), rounded to 6 dp. No maximum.

## region(body_mm, margin_mm) -> [x0, y0, x1, y1]

Pure. Body box (all pin pads of the component) ± margin.

## fully_inside(extent_mm, box_mm) / covers(extent_mm, region_box) -> bool

Pure (shapely). Box inside the extent polygon (buffer 1e-6 mm tolerance).

## grow(extent_mm, ext_f_mm, region_box) -> (pts, added_polys, added_mm2) | None

Pure. `U = extent ∪ (ext_f ∩ region)`. Outside `region_box` U equals `extent` (SC-002). U not one polygon → None.

## apply_rule(edb, P, nets, ends, pts, extent_fn, log, body_fn=None) -> (pts, info)

- `edb`: source board copy (read only). `extent_fn(factor) -> pts` (cutter.compute_extent_mm with a factor).
- Per end, in order:
  1. Detect GND pins (pins on reference nets) → `gnd_pins_on_board`, `gnd_pins_detected` (first 30, sorted).
     None → `no_gnd_pin_on_board` (no growth; 015 question as 2.0.0).
  2. A GND pin pad fully inside the current extent → `met` (extent unchanged).
  3. Else k = 1, 2, …: `grow(current, extent_fn(factor(k)), region)`; first k with a GND pin fully inside →
     `enlarged`. Region fully covered without one, or `MAX_TRIES` (500, safety) → `RuntimeError("end GND rule: <rd>
     has GND pin(s) <pins> but none lies fully inside …")`.
- Extents cached per factor (both ends share them).

```
info = {"base_factor", "step", "margin_mm", "unitless", "base_pts_mm",
        "ends": {rd: {"result": "met" | "enlarged" | "no_gnd_pin_on_board",
                      "gnd_pins_on_board", "gnd_pins_detected", "factor", "tries", "region_mm", "added_mm2",
                      "added_mm": [[[x, y], ...]], "gnd_pins_gained": [{"pin", "pad_mm"}], "gnd_pads_mm",
                      "gnd_pin_inside": pin | None, "other_nets": [names]}}}
```

`other_nets`: nets ≠ channel nets ∪ reference nets with a via or primitive in the added area (cut does not keep them).

## stage1 / outputs

- `cut_stage` → `stage1["end_gnd"] = info`; `extent_pts_mm` = final extent.
- `apply_stage`: ends with result `enlarged` → GND vias inside their GND pads protected from cleanup;
  `metrics.gnd_reference[rd].end_gnd = {factor, pins, pad_vias}`.
- `isim_check_ends` / `design_end_check` → `ends[rd].end_gnd` (+ `image` for enlarged), output `end_gnd`, `ends_md`
  section "End GND rule (cut extent)" with column "GND pins on board". stage1 without `end_gnd` →
  `{"result": "cut_before_2.1.0"}`.
- Re-cut: `recut_diffs` item `cut_method_changed` (previous tool_version < 2.1.0);
  `isim_check_ends` → `end_gnd_compare [{refdes, previous, now, result: same | enlarged | changed}]`.
- `design_cutout` report `created.end_gnd = {rd: {result, factor, gnd_pins_on_board}}`; `design_cleanup` protects
  pad vias of enlarged ends.
