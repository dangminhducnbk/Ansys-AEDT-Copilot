# Implementation Plan: No-GND end — keep the exposed GND pad

**Branch**: `main` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

The cut already has the source board open: it records, per non-BGA end whose GND pins all lie outside the cut extent,
the facts of those pads (pin, pad box, GND vias in the pad, other nets in the extension). The end check turns them
into option `gnd_keep_pad` (offered / omitted with reason) and draws them. Choosing it makes `isim_apply` cut again
from the source copy with extent = old ∪ (pad + 0.5 mm), then apply as for an end with its own GND pin.

### 1. `cut_board/gnd_decision.py`

| Item | What |
|---|---|
| `KEEP_PAD = "gnd_keep_pad"` | new option; in `EXECUTABLE`, `LABELS` ("Extend the cut extent to keep the GND pad(s) of the component (pad + margin); the pad becomes the GND pin, no plate") |
| `options_for(n_vias, n_copper_vias, keep_pad=None)` | `keep_pad` None → unchanged (Excel / old callers: identical output). dict `{offered, reason}` → `gnd_keep_pad` after `gnd_existing_copper` when offered, else in `omitted` with `reason` |
| `outside_pads(edb, P, rd, nets, extent_mm)` | source board, read only. Only for a component with ≥ 1 signal pin, 0 GND pins inside `extent_mm`, ≥ 1 GND pin outside: `{pads: [{pin, layer, pad_mm, size_mm, inside_frac, vias_mm}], rects_mm (pad ± margin), touches (rect ∩ extent ≠ ∅), other_nets: [names], margin_mm}`; else None |
| `extend_extent(extent_mm, rects_mm)` | pure (shapely): union; not one polygon → `CopilotInputError` ("pad not touching the cut extent") |
| `finding(ctx, keep_pad=None)` | adds `keep_pad` facts + options (via `options_for`) |
| `render` | view grows to include the pads; draws old extent edge (grey dashed), extended extent (green), outside pads (green outline) + their vias; header names other nets in the extension |
| `question_md` | line "Keep pad: pin 65 6.3 x 6.3 mm, 25 GND vias, extension adds nets: …" |

Margin: new template row `interface_sim.keep_pad_margin_mm` = 0.5 (job scope, autocut template).

### 2. `cut_board/cutter.cut_stage(..., keep_pads=None)`

- After the extent: `facts = {rd: GD.outside_pads(...)}` for non-BGA ends (None dropped) → stage1 `gnd_pads_outside`.
- `keep_pads` (set of refdes): each must have facts with `touches` → `pts = GD.extend_extent(pts, rects)`;
  stage1 `extent_base_pts_mm` (old), `kept_pads` {rd: [pins]}; facts recomputed on the new extent.
- `keep_pads` None → extent and cutout identical to today (only stage1 gains `gnd_pads_outside`).

### 3. Interface simulation

- `cut.py`: core of `run` moved to `cut_design(src, dst, ch, P, cell, version, log, keep_pads=None)` (same calls).
- `ends.py`: `OPTIONS["no_gnd_pin"]` + `gnd_keep_pad`; `check` passes `keep_pad` per end:
  stage1 without `gnd_pads_outside` (cut < 0.15.0) → omitted "cut again (isim_cut) to get this option";
  facts with `touches` → offered; facts without → omitted "pad not touching the cut extent";
  no facts → omitted "no GND pin of the component outside the cut extent".
- `apply.run`: handling `gnd_keep_pad` for any end → `cut_design(... keep_pads=...)` into `final/<name>.aedb`
  (from `_src`, re-copied if needed), `stage1_keep_pad.json`, then `apply_stage` on it (no copy of stage1).
  `gnd_decisions[rd]` adds `pads` (pin, size). Other handlings: unchanged path (copy stage1).
- `cutter.apply_stage`: handling `gnd_keep_pad` → rebuild sees own GND pins; `gnd_reference = {"kind":
  "kept_pad", pins}`; pin still missing → RuntimeError (no plate fallback).
- `recut.compare_handling`: already `needs_confirm` for `no_gnd_pin` (no change).

### 4. Design end check

Reads `stage1.json` next to the design when present: facts shown in the finding; option listed in `omitted` with
reason "applied by interface simulation (isim_apply) only" (no design utensil re-cuts with an extended extent; Q2 A).
No stage1.json → no keep-pad entry.

### 5. Excel flow

Unchanged (Q2 A): propose calls `finding(ctx)` without `keep_pad` → same options / image as 0.14.0.

## Kitchen check

| Item | Answer |
|---|---|
| Utensils / process tools added | none |
| Tool inputs | unchanged (`isim_apply` handling accepts the new option value) |
| Outputs | `isim_check_ends` / `design_end_check`: option `gnd_keep_pad` / keep_pad facts; apply metrics `gnd_reference.kind = kept_pad` |
| Safety / gate | unchanged (`user_approved_gnd`) |
| Catalog + contract | no catalog change; contract `contracts/keep-pad.md` |
| Recipes affected | none |

## Technical Context

| Item | Value |
|---|---|
| Changed | `cut_board/{gnd_decision,cutter}.py`, `interface_sim/{cut,ends,apply}.py`, `design_tools/end_check.py`, `templates/autocut_template.csv`, guides `interface_sim`, `design_tools` |
| Tests | `tests/unit/test_keep_pad_019.py`: options_for with / without keep_pad (015 outputs identical), extend_extent (union, not touching → error), outside_pads with fake EDB (pad outside / partly inside / no GND pin / other nets), finding + render with pads, ends keep_pad reasons, apply route (fake cut_design called with keep_pads), apply_stage gnd_reference kept_pad |
| AEDT (board1 copies) | isim CPHY_U14_U26: end check offers `gnd_keep_pad` for U26 (pin 65, 6.3 x 6.3, 25 vias) + image; apply with it → U26 pin 65 in design, no plate, ports, self-check OK; `tests/isim_check.py` (plate) + `tests/regression.py` PASS, plate identical |

## Constitution Check (1.2.0)

| Principle | Check | Status |
|---|---|---|
| I Gates | `user_approved_gnd` unchanged | PASS |
| II Data safety | re-cut from the `_src` copy; board copies only | PASS |
| III Defaults | margin = template row | PASS |
| IV Guides | rules in guides | PASS |
| V Regression | regression.py + isim_check.py | PASS |
| VII Contracts | contract file; errors at entry | PASS |
| VIII Package | facts / extent union in gnd_decision; cut in cutter | PASS |
| IX Stable interface | additive option; minor 0.15.0 | PASS |
| X Kitchen | see Kitchen check | PASS |
