# Implementation Plan: Cut keeps the GND pins of IC / connector ends

**Branch**: `main` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/end-gnd.md](contracts/end-gnd.md)

## Correction (user, spec commit 814383c, 2026-11-10) — supersedes the text below where they differ

| Item | Now |
|---|---|
| Step 1 | DETECT each end's GND pins / exposed pad on the source board (pins on `cutout.reference_nets`): `gnd_pins_on_board`, `gnd_pins_detected` in `end_gnd` and the end check table |
| No maximum | `cutout.end_expansion_max` and the 0.30 cap are DROPPED; `factor(base, step, k)` for k = 1, 2, … until a GND pin is fully inside |
| Loop end | end region contains all pins → ends; region fully covered (or 500 tries, safety only) without GND inside → `RuntimeError` naming the end and pins (geometry error), the cut fails |
| `max_reached` | removed. `no_gnd_pin_on_board` (detection) is the ONLY path to the 015 question; an end with GND pins never reaches it |
| Template | 2 rows: `cutout.end_expansion_step` 0.02, `cutout.end_region_margin_mm` 1.0 |

## Summary

`cutter.cut_stage` keeps the base extent (engineer's `cutout.expansion`). New module `cut_board/end_gnd.py` checks,
on the source board (read only), each end component for a GND pin whose pad box lies fully inside the extent. An end
that fails gets its region (pin box of the component + `cutout.end_region_margin_mm`) enlarged with extents of
factor base + k × step (k = 1, 2 … up to `cutout.end_expansion_max`): new extent = current ∪ (extent(f) ∩ region),
until a GND pin is fully inside. Maximum reached → that end's addition is dropped (extent = base there) and the 015
question appears unchanged. Facts go to `stage1['end_gnd']`; the end check shows them (table + image); apply protects
the GND vias inside the gained pads (as 019); re-cut lists the change. Same code path for `design_cutout`.

### 1. `cut_board/end_gnd.py` (new; pure helpers + one EDB reader)

| Function | What |
|---|---|
| `params(P)` | `{base, step, max, margin_mm, unitless}` from `P["cutout"]` |
| `factors(base, step, max)` | pure: `[base+step, base+2·step, …] ≤ max` (rounded 6 dp); empty when max ≤ base |
| `region(body_mm, margin_mm)` | pure: box (body ± margin) |
| `fully_inside(extent_mm, box_mm)` | pure (shapely): pad box inside extent (tolerance 1e-6 mm) |
| `grow(extent_mm, ext_f_mm, region_box)` | pure: `extent ∪ (ext_f ∩ region)` → (pts, added polygons, added mm²); not one polygon → None |
| `gnd_pads(comp, refs, extent_mm)` | EDB: GND pins `[{pin, pad_mm}]`; pins whose centre is inside the extent first; stops reading pad boxes at the first fully inside one (BGA: 1666 GND balls) |
| `apply_rule(edb, P, nets, ends, pts, extent_fn, log)` | per end: `met` (base ok) / `enlarged` / `max_reached`; extents cached per factor (shared by both ends); `other_nets` = nets other than channel + reference with vias / primitives in the added area (not kept by the cut) → `(pts, info)` |
| `render(info_end, base_pts, final_pts, path)` | PIL image (no AEDT): base extent (grey dashed), added area (green), body box, region box (dotted), gained GND pad (green outline) |
| `md(info)` | table rows for ends.md |

`info` (stage1 `end_gnd`): `{base_factor, step, max, margin_mm, base_pts_mm, ends: {rd: {result, factor, tries,
region_mm, added_mm2, added_mm (polygons), gnd_pins_gained [{pin, pad_mm}], other_nets}}}`.

- `met` → `factor = base`, `added_mm2 = 0`, nothing drawn; extent unchanged → cut identical (FR-005, test1).
- `max_reached` → no addition kept for this end (015 question identical, FR-006).
- `expansion_unitless = false` → step / max are mm like `cutout.expansion` (same rule, mm).

### 2. `cut_board/cutter.py`

- `compute_extent_mm(edb, P, nets, log, factor=None)`: optional factor override (default = template → same call).
- `cut_stage`: after the base extent, `pts, end_gnd = EG.apply_rule(...)` for all ends (BGA too: test1 U14 → `met`),
  before the 019 `outside_pads` / `keep_pads` step (that step now sees the enlarged extent). stage1 `end_gnd`.
- `apply_stage`: for ends with `end_gnd.result == enlarged` → `protect_ids |= vias_in_gnd_pads(...)`;
  `gnd_reference[rd]` gains `end_gnd: {factor, pins}` (kind stays `own_pins` / as rebuild reports).

### 3. Template (Principle III) — `templates/autocut_template.csv`, scope channel (→ Gate A structural, cut group, locked)

| Key | Default | Unit |
|---|---|---|
| `cutout.end_expansion_step` | 0.02 | -/mm (as `cutout.expansion`) |
| `cutout.end_region_margin_mm` | 1.0 | mm |

`config.build_params`: step > 0, margin ≥ 0 (errors `cutout.…`, checked even before sweep values exist).
`defaults_history`: not needed (new keys; older runs re-cut with the current method by decision).

### 4. Interface simulation

- `ends.check`: per end `end["end_gnd"]` from stage1 + image `end_gnd_<rd>.png` (enlarged / max_reached);
  `ends.md` section "## End GND rule (cut extent)": Refdes | Result | Base factor | Factor used | Added mm² |
  GND pin / pad gained | Other nets in added area (not kept) | Image. Output key `end_gnd`.
  stage1 without `end_gnd` (cut < 2.1.0) → row "cut before 2.1.0: cut again (isim_cut)".
- Re-cut (FR-008): `recut.start` adds diff `cut_method_changed` (ref `end GND rule 2.1.0`) when the previous run's
  tool_version < 2.1.0 (needs a resolution at Gate A like every re-cut diff); `ends.check` in re-cut mode returns
  `end_gnd_compare` = per end previous (stage1 of the previous run: factor / none) vs now, result
  `same` / `enlarged` / `changed`, also in `handling_md`'s neighbour section.
- `apply.run`: unchanged (stage1 copy); 019 `gnd_keep_pad` path unchanged.

### 5. Design tools

- `design_cutout`: same `cut_stage` → stage1.json gains `end_gnd`; report `created.end_gnd` (result / factor per end).
- `design_cleanup`: stage1.json beside the design with enlarged ends → protect GND vias in their GND pads.
- `design_end_check`: stage1.json beside → `end_gnd` row + image, as interface sim.

### 6. Guides / docs

`guides/interface_sim.md`, `guides/design_tools.md`: rule (base factor everywhere; end region enlarged only to keep a
GND pin; show the table + image before Gate B; max reached → 015 question). CHANGELOG 2.1.0 (board1 reference changed
on purpose), README, CLAUDE.md status, ROADMAP.

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | none added; outputs of `isim_cut` / `isim_check_ends` / `design_cutout` / `design_end_check` gain `end_gnd` (additive) |
| Safety level | unchanged |
| Approval flag | unchanged |
| Catalog entry + contract | no catalog change; contract `specs/022-cut-keeps-end-gnd/contracts/end-gnd.md` |
| Registration | n/a |
| Workflows affected | none |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| Changed | `cut_board/{end_gnd (new), cutter, config}.py`, `interface_sim/{ends, recut}.py`, `design_tools/{cutout, cleanup, end_check}.py`, template, guides, tests |
| Tests | `tests/unit/test_end_gnd_022.py`: factors / region / fully_inside / grow (outside region unchanged = SC-002, two regions joined, not one polygon → None), apply_rule with fake EDB (met → same pts object values; enlarged at k-th factor; max_reached → base pts; extents cached), template rows + build_params errors, ends row / md / image, apply protects pad vias, recut diff + compare, design cutout / cleanup / end check wiring |
| AEDT (copies only) | board1: `tests/regression.py` with reference updated (U26 own pad, no GND question, `end_gnd` U26 enlarged), `tests/isim_check.py` (U21 enlarged too, J25 met); test1: `tests/pcie_check.py` unchanged (16 ports) + both ends `met` |

## Constitution Check (2.0.1)

| Principle | Check | Status |
|---|---|---|
| I Gates | no gate change; end_gnd shown before Gate B; 015 gate `user_approved_gnd` only for an end with no GND pin on the board | PASS |
| II Data safety | source copies only; source board read only | PASS |
| III Defaults | 2 template rows | PASS |
| IV Guides | rule in interface_sim + design_tools guides | PASS |
| V Regression | board1 reference changed on purpose (CHANGELOG); test1 PCIe unchanged | PASS |
| VI Encoding | ASCII-safe log; UTF-8 files | PASS |
| VII Contracts | contract end-gnd.md; values validated in build_params | PASS |
| VIII Package | rule in `cut_board/end_gnd.py`; isim / design tools only read stage1 | PASS |
| IX Stable interface | additive outputs; cut result changes for ends that lost GND → minor 2.1.0 | PASS |
| X Tool catalog | see Tool catalog check | PASS |

## Decisions (no user input needed)

| # | Decision |
|---|---|
| D1 | Body = box of all pin pads of the component (same as 015 `bodies`). |
| D2 | (superseded by the correction) no maximum; geometry error stops the cut. |
| D3 | Rule checked for every end (BGA / through-hole too); `met` costs one pad-box read. |
| D4 | Re-cut of a run before 2.1.0 → one `cut_method_changed` diff at Gate A + `end_gnd_compare` after the cut. |

## Extension (spec commit d320421): Gate A cut form, cut preview, manual end factor (US4, US5, FR-011..014)

### E1. Same computation for preview and cut — `cutter.cut_extent`

`cutter.cut_extent(edb, P, nets, ends, log, end_factors=None, strict=True) -> (pts, end_gnd)` = base
`compute_extent_mm` + `end_gnd.apply_rule`. `cut_stage(..., end_factors=None)` calls it; the preview calls it on the
source board opened read-only. Same inputs → same extent (SC-005).

`end_gnd.apply_rule(..., manual=None, strict=True)`:
- `manual {refdes: factor}` → that end uses the factor exactly (no stepping): new extent =
  `(current − region) ∪ (extent(f) ∩ region)` (narrows or widens only the end region), result `manual`.
  No GND pin fully inside → error "end factor <rd> = f leaves no GND pin / pad fully inside". End with no GND pin on
  the board + manual factor → error "has no GND pin on the board: leave its end factor empty".
- `strict=False` (preview): an error is recorded on the end (`result: error`, `error`) instead of raised; the extent
  for that end stays unchanged; `info.errors` lists them.

### E2. Preview — `interface_sim/cut_preview.py` (new), MCP `isim_cut_preview` (safety read, no gate)

`preview(request_id, name, structural=None, end_factors=None, version=None)`:
- Needs a proposal (step `started` after trace) or agreed content, before the cut (`content_agreed`); after the cut
  (`cut` or later) → error "already cut: change = back to Gate A + re-cut".
- Content = agreed content if present, else the proposal. `structural` / `end_factors` given → validated first
  (errors name the field: `cutout.expansion`, `cutout.end_factor.U26`), else the stored ones.
- Opens `req["board"]` read-only (as `isim_trace`), computes `cut_extent(..., strict=False)`, builds the scene,
  writes ONLY under the interface folder: `preview/cut_region.png`, `preview/end_<rd>.png` (enlarged / manual ends),
  `preview.json` {structural, end_factors, nets, extent_pts_mm, extent_area_mm2, end_gnd, errors, images}.
- Returns `{name, ok, errors, rows, table_md, image, zooms, extent_area_mm2, extent_size_mm}`.
  Rows (FR-007 + US4): Refdes | GND pins on board | GND inside at base | Factor used (auto / manual) | Added mm² |
  GND pin / pad gained | Other nets in added area | Error.

`end_gnd.scene(edb, ...)` (EDB read) + `end_gnd.render_scene(scene, path, view=None)` (pure PIL):
signal primitives + vias red; base extent grey outline; added end area light green + label
"<refdes>: <factor>, +N mm²"; end region dashed; end + series components frame + refdes; GND pins / pad kept blue,
still outside blue with red outline (BGA: circle at pin position, no bounding box); other-net primitives in the added
area light grey + names (first 12); 1 mm scale bar + "W x H mm". Zoom = same scene, view = end region + 1 mm.

Cut check (SC-005): `cut.run` compares stage1 extent with `preview.json` when its structural / end_factors / nets
equal the agreed ones → stage1 `preview_check {compared, equal, area_diff_mm2}`; the isim_cut result returns it.

### E3. Gate A cut form — `interface_sim/cut_form.py` (new), MCP `isim_cut_form` (safety read)

`build(request_id)` → `{request_id, tabs[], table_md}`; one tab per interface:
- descriptors for the template `cutout.*` rows (+ `series.keep`, the other structural key): key, label, unit, type,
  choices, default ("Set default"), value (agreed → proposal → template), `copy: true`;
- one descriptor per end: key `cutout.end_factor.<refdes>`, type num, optional, default empty (= automatic),
  `per_end: true`, `copy: false` ("Copy to all tabs" never copies it);
- enabled when the interface has a proposal and is not cut yet; after the cut every field `locked`
  ("already cut - locked (re-cut to change)");
- `preview`: last `preview.json` summary + image paths when present.
Submit → for each tab `isim_cut_preview(request_id, name, values, end_factors)` (validates + recomputes); input only:
GATE A still needs the explicit go → `isim_confirm_content` with `content.structural` + `content.end_factors`.

### E4. Manual end factor storage + Gate A check

- `content.validate_content`: `end_factors {refdes: number > 0}`, refdes ∈ {comp_a, comp_b}, empty / None dropped;
  key kept only when non-empty (old contents unchanged). Stored in content → `user_settings.json` content.
- `content.confirm`: a `preview.json` with the same structural / end_factors / nets and `errors` → refused
  ("cut preview error: …; fix or clear the end factor").
- `cut.run` passes `content.end_factors` to `cut_design` → `cut_stage`; error → no cut (RuntimeError before cutout).
- `recut.start`: proposal keeps old `end_factors` of ends still in the content.
- `cut_board.config` validation of the number: `validate_end_factors(values)` pure (> 0).

### E5. Catalog / contracts / guide

| Tool | Group / kind | Safety | Gate | Contract |
|---|---|---|---|---|
| `isim_cut_preview` | interface-sim / process | read | none | `specs/022-cut-keeps-end-gnd/contracts/cut-preview.md` |
| `isim_cut_form` | interface-sim / process | read | none | same file |

Server tools 51 → 53 (`@tool()`); goldens list them as added in 022. Guide `interface_sim` Phase 1.5 (GATE A): form
(widget: tabs, Set default, Copy to all tabs, end factor per end) or markdown tables, preview table + image paths,
recompute on change, explicit go.

### Tool catalog check (extension)

| Item | Answer |
|---|---|
| Tools added | `isim_cut_preview` (request + interface + optional values → preview table + images, board read only), `isim_cut_form` (request → tabs) |
| Safety | `read` both (writes only under the request folder) |
| Approval flag | n/a (read) |
| Catalog entry + contract | `catalog/tools.py` entries; `contracts/cut-preview.md` |
| Registration | `@tool()` |
| Workflows affected | none (the interface-sim process guide covers them) |
| New fixed-process tool | none — both are steps of the existing interface-sim process (Gate A), like `isim_settings_form` |

### Tests (extension)

`tests/unit/test_cut_preview_022.py`: apply_rule manual (exact factor, narrows, error without GND, error for no-GND end,
strict=False records), cut_extent equality preview vs cut (fake EDB), render_scene (pure, image size, labels),
preview step / validation errors / preview.json / no write outside the interface folder (fake edb_session), cut form
tabs (descriptors, per-end fields copy false, locked after cut), validate_content end_factors, confirm refused on
preview error, cut.run passes end_factors + preview_check, recut keeps end_factors, server refusals / catalog.
AEDT (board1 copy): preview U14_U26 at 0.06 (U26 auto factor = cut factor, extent area equal after cut), factor 0.10
recomputed, U26 manual 0.20 used, U26 manual 0.06 refused; board files unchanged (mtime / size of the .aedb).
