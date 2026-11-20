# Tasks: No-GND end decision (015)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/gnd-decision.md](contracts/gnd-decision.md)

## Phase 1: Foundational - shared module

- [X] T001 Tests in `tests/unit/test_gnd_decision_015.py`: `options_for` per case (vias + copper / vias only / none), `plate_rect` equals the pre-015 formula on fake data, `render` writes a PNG from a fake finding
- [X] T002 `aedt_copilot/cut_board/gnd_decision.py`: OPTIONS, options_for, plate_rect, context, finding, render
- [X] T003 `aedt_copilot/cut_board/cutter.py`: `rebuild_smd_component` uses `context` + `gnd_choice`; `apply_stage` handling options + `metrics["gnd_reference"]`

## Phase 2: User Story 1 + 2 - interface simulation (P1)

- [X] T004 [US1] Tests: `_measure` rule `no_gnd_pin` (fake EDB), validate rejects `other` / non-offered option, apply_route gate refusal, server `isim_apply` refusal without `user_approved_gnd`
- [X] T005 [US1] `interface_sim/ends.py` (`_measure` P / body / image_dir, ends_md section), `check` passes them
- [X] T006 [US1] `interface_sim/settings.py` (ALL_OPTIONS, validate, apply_route flag), `apply.py` (gnd_notes, gnd_decisions, gnd_reference in self-check), `mcp_server/server.py` isim_apply params, `kitchen/catalog.py` description
- [X] T007 [US2] Tests + `interface_sim/recut.py` `needs_confirm` for `no_gnd_pin`; user_settings stores `gnd_decisions`
- [X] T008 [US1] `design_tools/end_check.py`: P / body / image under `.tasks`

## Phase 3: User Story 3 - Excel flow (P2, minimal)

- [X] T009 [US3] Tests: `batch.gnd_missing`; server `start_cut_batch` refusals
- [X] T010 [US3] `cut_board/propose.py` (finding + image + warning + gnd_questions.json), `batch.py` (gnd_missing, start / worker gnd_handling), `cutter.cut_channel` handling, `cli/parser.py` + `commands.py` (`cut --gnd-handling`), server `start_cut_batch` params

## Phase 4: Guides + polish

- [X] T011 Guides `interface_sim`, `workflow`, `design_tools`, `kitchen`, `verify`: show image + multiple-choice options, never choose; flags
- [X] T012 Unit tests all PASS (update fixtures that relied on silent rebuild); `graphify update .`
- [X] T013 AEDT on board1 copy: isim CPHY_U14_U26 stops at U26 with image + options; option 1 → plate [120.13, 36.83, 125.82, 38.82] mm, metrics equal reference; `tests/regression.py` (Excel cut with gnd_handling) PASS
- [X] T014 Converge: spec vs code; VERSION 0.14.0, CHANGELOG, CLAUDE.md status row, ROADMAP (015 row, renumber later rows); commit + local tag v0.14.0

## Dependencies

T001 → T002 → T003 → Phase 2 / 3. T004 → T005..T006; T007 after T006. T009 → T010. T011..T014 last.
