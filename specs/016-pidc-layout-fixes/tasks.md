# Tasks: PI-DC + layout edit fixes (016)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/pidc-layout-016.md](contracts/pidc-layout-016.md)

## Phase 1: Setup

- [X] T001 Template rows: remove `pidc.via_dT_C`, add `pidc.via_base_temp_C` 25, `pidc.cd_narrow_window_mm` 0.1, `pidc.cd_tiny_area_mm2` 0.002, `pidc.image_width` 10000 in templates/pidc_template.csv
- [X] T002 Golden normalisation for the 016 template change (pre002 `pidc_params`, pre013 `pidc.params`) in tests/unit/_golden.py, tests/unit/test_core_config.py, tests/unit/test_pidc_layout_core_013.py

## Phase 2: User Story 1 — VRM voltage by header (P1)

- [X] T003 [US1] `table_rows`, `vrm_sources`, `load_sources` in aedt_copilot/pi_dc/report.py; `dcir` uses them (V out + how columns)
- [X] T004 [US1] `voltage_distribution._sources` uses `vrm_sources` / `load_sources` in aedt_copilot/pi_dc/skills/voltage_distribution.py
- [X] T005 [P] [US1] Tests: 19x19 + B04 rows fixtures, header missing fallback + warning, remote-sense rule in tests/unit/test_pidc_layout_016.py

## Phase 3: User Story 2 — narrow / tiny copper (P1)

- [X] T006 [US2] Narrow path + INFO tiny + verdict NO_DATA + counts INFO in aedt_copilot/pi_dc/skills/current_density.py
- [X] T007 [US2] Report: INFO card count, INFO pairs with peak > limit listed, narrow-window note in aedt_copilot/pi_dc/report.py
- [X] T008 [P] [US2] Tests: synthetic J images (thin trace → narrow FAIL; tiny pieces → INFO; wide copper → unchanged path), run verdict NO_DATA in tests/unit/test_pidc_layout_016.py

## Phase 4: User Story 3 — empty power net list (P1)

- [X] T009 [US3] `Ctx` stop on no power / ground nets in aedt_copilot/pi_dc/common.py; voltage_distribution empty composite → PENDING in aedt_copilot/pi_dc/skills/voltage_distribution.py
- [X] T010 [P] [US3] Tests: .siw without list / only GND → error naming the file in tests/unit/test_pidc_layout_016.py

## Phase 5: User Story 6 — via ΔT from the simulation (P1)

- [X] T011 [US6] `common.sim_temperature` in aedt_copilot/pi_dc/common.py; `via_current.run` / `load_vias(..., dT)` + `temperature` + warnings in aedt_copilot/pi_dc/skills/via_current.py; report text in aedt_copilot/pi_dc/report.py
- [X] T012 [P] [US6] Tests: ipc_cap(2 mil, 60) = 0.9107, cfg parse, missing cfg / key error, dT ≤ 0 stop, warning outside 10..100 in tests/unit/test_pidc_layout_016.py

## Phase 6: User Story 4 — layout edit deletes vias (P2)

- [X] T013 [US4] `op_delete` via ids, `gone_vias`, `deleted_vias`, pin refusal in aedt_copilot/edit_layout/ops.py; touched / images in aedt_copilot/edit_layout/run.py
- [X] T014 [P] [US4] Tests with fake EDB (via deleted + excluded from all_vias, pin refused, primitive unchanged) in tests/unit/test_pidc_layout_016.py

## Phase 7: User Story 5 — image width (P3)

- [X] T015 [US5] `warnings` for image_width > 10000 in aedt_copilot/pi_dc/export.py (+ test in tests/unit/test_pidc_layout_016.py)

## Phase 8: Polish

- [X] T016 Guides guides/pidc_current_density.md, guides/pidc_via_current.md, guides/pidc_voltage_distribution.md, guides/pidc_workflow.md, guides/layout_edit.md; catalog text aedt_copilot/kitchen/catalog.py
- [X] T017 Full unit suite; `graphify update .`
- [X] T018 Offline checks on copies: pidc_check on BOARDB_B04 copy (`--skip-export`), rerun on a copy of boardb_19x19 (`--skip-export`), tests/layout_edit_b04.py identical + delete-via plan on an B04 copy; `_doc` note in tests/reference_pidc/pidc_BOARDB_B04_VCC_0P8V.json
- [X] T019 Release 0.14.1: VERSION, CHANGELOG.md, CLAUDE.md status row, specs/ROADMAP.md 016 done; commit + local tag v0.14.1 (no push)

## Dependencies

T001 → T002 and T011; T003 → T004; T006 → T007; US phases independent otherwise; T016–T019 last.

## Converge (2026-11-09)

- [X] T020 Report crashed on INFO pairs (image without J_avg_max) in aedt_copilot/pi_dc/report.py — found on the boardb_19x19 copy; fixed (`.get`), report rebuilt on both copies, pidc_check PASS
- FR-001..008 checked against code: all implemented; SC-001 (19x19 copy: 76 rails, 0 negative drops, DDR_VDDQ VRM 0.5 V = set − 2e-7), SC-002 (0 silent NO_DATA above limit; 505 → 76 NO_DATA, all "no current"), SC-003 (B04 copy identical, pidc_check PASS), SC-004 (319 unit tests (016 commits said 330: miscount), layout_edit_b04 identical, delete-via on a copy PASS)
