# Tasks: Cut keeps the GND pins of IC / connector ends (022)

**Input**: spec.md, plan.md, contracts/end-gnd.md. Commit after implement / converge / release. AEDT on copies only.

## Phase 1: Setup

- [X] T001 Template rows `cutout.end_expansion_step` 0.02, `cutout.end_region_margin_mm` 1.0 (scope channel) in `templates/autocut_template.csv`; checks step > 0, margin ≥ 0 in `aedt_copilot/cut_board/config.py` `build_params` (max row dropped by T014)

## Phase 2: Foundational

- [X] T002 New `aedt_copilot/cut_board/end_gnd.py`: `params`, `factors`, `region`, `fully_inside`, `grow`, `gnd_pads`, `apply_rule`, `render`, `md_rows` per contract
- [X] T003 `aedt_copilot/cut_board/cutter.py`: `compute_extent_mm(..., factor=None)`; `cut_stage` calls `end_gnd.apply_rule` after the base extent (before 019 outside_pads / keep_pads), stage1 `end_gnd`; `apply_stage` protects GND vias in GND pads of `enlarged` ends, `gnd_reference[rd].end_gnd`

## Phase 3: US1 — only the end region is enlarged (P1)

- [X] T004 [US1] `tests/unit/test_end_gnd_022.py`: factors / region / fully_inside / grow (outside region unchanged, two regions joined, not one polygon → None), apply_rule with fake EDB (met unchanged, enlarged at k-th factor, max_reached → base, no GND pin, cache), template + build_params errors, apply_stage protection

## Phase 4: US2 — engineer sees each enlargement before Gate B (P1)

- [X] T005 [US2] `aedt_copilot/interface_sim/ends.py`: `end_gnd` per end from stage1 + image `end_gnd_<rd>.png`; ends.md section "End GND rule (cut extent)"; old stage1 → `cut_before_2.1.0`
- [X] T006 [US2] `aedt_copilot/design_tools/end_check.py` (end_gnd + image from stage1.json beside), `design_tools/cutout.py` (`created.end_gnd`), `design_tools/cleanup.py` (protect pad vias of enlarged ends)
- [X] T007 [US2] unit tests for ends / design tools wiring in `tests/unit/test_end_gnd_022.py`

## Phase 5: US3 — settings and re-cut (P2)

- [X] T008 [US3] `aedt_copilot/interface_sim/recut.py`: diff `cut_method_changed` (previous tool_version < 2.1.0); `ends.check` re-cut mode → `end_gnd_compare`; unit tests

## Phase 6: Polish + verify

- [X] T009 Guides `guides/interface_sim.md`, `guides/design_tools.md`: the rule
- [X] T010 Run all unit tests (update goldens / template-count tests only where the 3 new rows appear); server import 51 tools; `graphify update .`
- [X] T011 `tests/regression.py` + reference `tests/reference/CPHY_U14_U26.json` updated on purpose (U26 own pad, no GND question, end_gnd enlarged); `tests/isim_check.py` expectations; run on board1 COPY → PASS
- [X] T012 `tests/pcie_check.py`: both ends `met`; run on test1 COPY → PASS unchanged (16 ports)
- [X] T014 Correction (spec 814383c): detect GND pins on the source board first (`gnd_pins_on_board`, `gnd_pins_detected`, table column); no maximum (row `cutout.end_expansion_max` dropped, `max_reached` removed); region covered without GND → geometry error; tests (no maximum, geometry errors, detection), guides, plan, contract
- [X] T013 CHANGELOG 2.1.0 (reference change), VERSION, README, CLAUDE.md status, ROADMAP; tag v2.1.0 (no push)

## Phase 7: Extension (spec d320421) — US4 Gate A form + preview, US5 manual end factor

- [X] T015 [US5] `aedt_copilot/cut_board/end_gnd.py`: `apply_rule(manual=, strict=)` (manual factor exact: (current − region) ∪ (extent(f) ∩ region), result `manual`; errors: no GND inside, no GND pin on board; strict=False records `error` + `info.errors`); `validate_end_factors`
- [X] T016 [US4] `aedt_copilot/cut_board/cutter.py`: `cut_extent(edb, P, nets, ends, log, end_factors, strict)` shared by `cut_stage(end_factors=)` and the preview
- [X] T017 [US4] `aedt_copilot/cut_board/end_gnd.py`: `scene(edb, ...)` (EDB read) + `render_scene(scene, path, view)` (pure PIL) per plan E2
- [X] T018 [US4] `aedt_copilot/interface_sim/cut_preview.py`: `preview(...)` (step check, validation, read-only board, preview.json + images under the interface folder, table_md); api op `cut_preview`
- [X] T019 [US4] `aedt_copilot/interface_sim/cut_form.py`: `build(request_id)` tabs (cutout.* + series.keep descriptors, per-end factor fields copy false, locked after cut, last preview); api op `cut_form`
- [X] T020 [US5] `aedt_copilot/interface_sim/content.py` (`end_factors` in validate_content; confirm refused on preview error), `cut.py` (end_factors to cut_design / cut_stage, stage1 `preview_check`), `recut.py` (keep end_factors)
- [X] T021 [US4] `mcp_server/server.py` tools `isim_cut_preview`, `isim_cut_form` (`@tool()`); `aedt_copilot/catalog/tools.py` entries (read) + CONTRACTS; contract `specs/022-cut-keeps-end-gnd/contracts/cut-preview.md`; goldens (tools added in 022)
- [X] T022 [US4] `guides/interface_sim.md` Gate A form + preview flow; `prompts/interface-sim.md` if it lists Gate A steps
- [X] T023 `tests/unit/test_cut_preview_022.py` per plan; all unit tests; server import 53 tools; `graphify update .`
- [X] T024 AEDT board1 COPY: preview checks (auto = cut extent, 0.10 recomputed, U26 manual 0.20 used, 0.06 refused, board unchanged) — script `tests/preview_check.py`

## Converge (2026-11-10)

- FR-001..014 checked against code: no gap. FR-001 detection (`end_gnd.apply_rule`, `gnd_pins_on_board`); FR-002 region-only growth, no maximum, geometry error (unit tests); FR-003 2 template rows (Gate A structural, cut group locked); FR-004 pad vias protected (`apply_stage`, `design_cleanup`); FR-005 / SC-003 test1 PCIe met / met, 16 ports; FR-006 015 question only for `no_gnd_pin_on_board`; FR-007 end check table + image; FR-008 `cut_method_changed` + `end_gnd_compare`; FR-009 `design_cutout` via `cut_stage`; FR-010 guides, board1 reference changed on purpose; FR-011 `isim_cut_preview` = `cutter.cut_extent`; FR-012 `isim_cut_form`; FR-013 `content.end_factors`; FR-014 catalog read entries + contract `cut-preview.md` + guide.
- AEDT 2026-11-10 on fresh copies (run one after another: two runs started in the same second share a request id, the known collision, proposal task_e2273234): board1 `tests/regression.py` PASS (U26 enlarged 0.16, +59.19 mm2, pin 65 kept, planes 901-923 mm2, 126 GND vias, 24 ports, shift 0.21 mm); `tests/isim_check.py` PASS (U21 enlarged, J25 met, 18 ports, no GND question); `tests/preview_check.py` PASS for every preview step (preview extent = cut extent, area diff 0.0; 0.10 recomputed; manual 0.20 used; manual 0.06 refused at Gate A; U21 auto 0.14); `edb.def` unchanged (only the 0-byte `edb.def.tmp` EDB touches on every open, as `isim_trace` does; the script now ignores it); `--preview-only` image run PASS; test1 `tests/pcie_check.py` PASS. 382 unit tests PASS; 53 tools.

## Phase 8: Patch 2.1.1 — preview image with less text (spec clarification 2.1.1)

- [X] T025 [US4] `aedt_copilot/cut_board/end_gnd.py` `render_scene`: one-line title, footer colour legend (present items only) next to the scale bar, label "<refdes> <factor>", other nets grey fill only (no numbers / name list); `scene` and extent code untouched
- [X] T026 [US4] `guides/interface_sim.md` 4b image description; unit test `tests/unit/test_cut_preview_022.py` (legend items, no other-net text)
- [X] T027 Fresh board1 copy: `tests/preview_check.py --preview-only` (CPHY_U14_U26, CPHY_U21_J25) → 4 image paths for the user's review
- [X] T028 Converge; CHANGELOG 2.1.1, VERSION, CLAUDE.md status; tag v2.1.1 (v2.1.0 untouched, no push)

## Converge 2.1.1 (2026-11-10)

- Clarification 2.1.1 checked: one-line title, footer colour legend of present items, label `<refdes> <factor>`, other nets grey only (names / mm² only in table_md and preview.json), scale bar + canvas fit + GND vias + refdes kept; user review fixes: frames clipped to the drawing area (canvas still fitted to the cut + end regions), other nets mid grey over the added area, same swatch colour. Extent code untouched (no AEDT re-cut). `tests/preview_check.py --preview-only` PASS on a fresh board1 copy (request 20261110_115733: U26 0.16, U21 0.14). 382 unit tests PASS.

## Phase 9: Patch 2.1.2 — other nets hatched (spec clarification 2.1.2)

- [X] T029 [US4] `aedt_copilot/cut_board/end_gnd.py` `render_scene` / `_swatch`: other nets = dark grey outline + diagonal grey hatch, no fill; unit test (pixel inside an other-net piece over the added area stays green)
- [X] T030 Fresh board1 copy `tests/preview_check.py --preview-only` → 4 image paths (green reads as green on end_U26 / U21)
- [X] T031 Converge; CHANGELOG 2.1.2, VERSION, CLAUDE.md; tag v2.1.2 (v2.1.0 / v2.1.1 untouched, no push)

## Converge 2.1.2 (2026-11-10)

- Clarification 2.1.2 checked: other nets = dark grey outline + diagonal grey hatch, no fill; legend swatch same hatch; added area green underneath (unit test + visual check of end_U26 / U21). Extent code untouched. `tests/preview_check.py --preview-only` PASS on a fresh board1 copy (request 20261110_120924: U26 0.16, U21 0.14). 383 unit tests PASS.
