# Data model — 038

## Page data (`<script type="application/json" id="cfg-data">`, read-only)

```
{request_id, board, created, version,
 template: {key: {default, unit, type, label}},           # defaults of the rows the page shows
 channels: {name: {
    content: {comp_a, comp_b, nets[], diff_groups[[]], series{refdes:{nets[]}}, schematic_diffs[{item, kind, board,
              schematic}]},
    ref_nets[], extents: {conformal|convex_hull|bounding_box: {"0.02".."0.20": [[x,y] mm]}},
    layers: {box[x0,y0,x1,y1], order[], routed[], layers{layer: {sig, gnd, oth: svg path}}},
    comps[{refdes, box, end}],
    ends: {refdes: {part, type, layer, bga, pins_total, pins_cut, signal[pad], gnd[pad], other[pad], non_round}},
    choices: {refdes: {rule, label, options[], default}}  # unusual cases (FR-034)
    review_html, preview_png}}}
pad = {pin, net, x, y, box[x0,y0,x1,y1]}   (mm)
```

## Page state (`id="cfg-state"`, written by Save)

```
{request_id, saved_at (ISO) | null, channels: {name: {
   folder: "<channel folder>",
   cut: {"cutout.extent_type", "cutout.expansion", <advanced cutout.* / cleanup.* / series.* changed only>},
   nets: {net: include(bool)},
   content_note: "",
   diffs: {item: "board" | "schematic" | "drop"},
   cm: {refdes: {die_type, die_orientation, die_height_mm, ball_shape, ball_ratio, ball_height_mm, ball_material,
                 port_location}},
   setup: {mode: single|multi, freq_ghz, max_passes, max_delta_s, multi[{f, unit, ds}], multi_passes,
           refine_pct, basis, via_mesh_3d, via_sides, delta_zo},
   sweep: {type: interpolation|discrete, q3d_dc, rows[{dist, start, end, value}], max_solutions, error_pct,
           passivity, passivity_tol, causality},
   extents: {dielectric_type, dielectric_pad, airbox_type, airbox_pad, z_pos, z_sync, z_neg},
   choices: {refdes: option}}}}
```

## Mapping (model.to_settings) → existing structures

| Page | Goes to |
|---|---|
| cut.* | `content.structural` (cutout.* / cleanup.* / series.*) |
| nets (include false) | removed from `content.nets` (signal nets only; ≥ 1 net per diff group kept or the group dropped) |
| diffs | `content.schematic_diffs[].resolution` |
| setup / sweep / extents | `values` (template keys; ranges → `sweep.ranges` JSON + `sweep.start_ghz/stop_ghz/step_ghz` of the whole span) |
| cm | `values["component.model"]` JSON {refdes: {...}} |
| choices | `handling` {refdes: option} |
| folder | `request.channel_folders[name]` |

## Validation rules (model.validate)

- folder: non-empty, no `<>:"/\|?*;` or space, not `.`/`..`, unique (case-insensitive) in the request.
- expansion 0 < f ≤ 1 (slider 0.02–0.20; typed advanced values follow build_params rules).
- setup: passes integer 1..100, ΔS > 0, refine 1..100, sides 3..64, ΔZo > 0, single freq > 0 GHz; multi: ≥ 1 row,
  every f > 0, ΔS > 0.
- sweep rows: ≥ 1; start ≥ 0; end > start; Linear Step 0 < step ≤ end − start; Linear Count integer ≥ 2; Log Scale
  start > 0, samples integer ≥ 1; max solutions integer ≥ 1; error % > 0; passivity tol > 0.
- extents: paddings ≥ 0; types in Bounding Box / Conformal / Convex Hull.
- cm: ratio 0 < r ≤ 1 unless shape None; heights ≥ 0; port location centre | end (BGA → centre).
- choices: option among the offered ones.
Errors: list of {channel, frame, field, message} → M2 table.

## State transitions (per channel, 038 process)

`started` (traced) → config written → config checked (folder moved, previews) → `content_agreed` (go) → `cut` →
`ends_checked` → `applied` → `merged` (into the request project). Any failure: channel `failed`, other channels go on;
M3 lists it.
