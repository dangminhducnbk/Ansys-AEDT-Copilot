# Tasks: No-GND end — keep the exposed GND pad (019)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/keep-pad.md](contracts/keep-pad.md)

## Phase 1: Setup

- [X] T001 Template row `interface_sim.keep_pad_margin_mm` 0.5 in templates/autocut_template.csv

## Phase 2: Foundational

- [X] T002 `KEEP_PAD`, `options_for(keep_pad=)`, `outside_pads`, `extend_extent`, `finding(keep_pad=)`, render + question_md in aedt_copilot/cut_board/gnd_decision.py
- [X] T003 `cut_stage(keep_pads=)` facts + extension; `apply_stage` gnd_reference kept_pad in aedt_copilot/cut_board/cutter.py

## Phase 3: User Story 1+2 — option + image (P1)

- [X] T004 [US1] `OPTIONS` + keep_pad reasons in `check` in aedt_copilot/interface_sim/ends.py
- [X] T005 [US1] design end check reads stage1.json facts (omitted: interface sim only) in aedt_copilot/design_tools/end_check.py

## Phase 4: User Story 3 — apply with extended extent (P1)

- [X] T006 [US3] `cut_design` in aedt_copilot/interface_sim/cut.py; keep-pad route + `gnd_decisions.pads` in aedt_copilot/interface_sim/apply.py

## Phase 5: Tests + polish

- [X] T007 [P] Unit tests tests/unit/test_keep_pad_019.py (options identical without keep_pad, extend_extent, outside_pads fake EDB, finding/render, ends reasons, apply route, gnd_reference)
- [X] T008 Guides guides/interface_sim.md, guides/design_tools.md; full unit suite; `graphify update .`
- [X] T009 AEDT on board1 copies: isim U14_U26 keep_pad (offered + image, apply → pin 65 kept, self-check OK); tests/isim_check.py + tests/regression.py PASS
- [X] T010 Release 0.15.0: VERSION, CHANGELOG.md, CLAUDE.md status, specs/ROADMAP.md 019 done; commit + local tag v0.15.0 (no push)

## Dependencies

T001 → T002 → T003 → T004..T006 → T007 → T008 → T009 → T010.

## Converge (2026-11-09)

- [X] T011 Image header listed all 38 other nets (cut off) → `nets_text` (image: 3 + count, question: 10 + count) in aedt_copilot/cut_board/gnd_decision.py
- FR-001..006 checked: facts at cut, option offered / omitted with reason, image, re-cut apply, gate + storage (015 path), plate + regression identical. SC-001 (U26 / U21 offered, pin 65 6.3 x 6.3, 25 vias), SC-002 (kept_pad, 24 ports, self-check OK), SC-003 (isim_check plate PASS, plates [120.13, 36.83, 125.82, 38.82] / [84.93, 33.18, 86.82, 38.82] 10 vias; Excel regression PASS), SC-004 (332 unit tests).
- Found, not 019: two `isim_start` in the same second on different workspaces get the same request id (registry lookup then mixes them) — follow-up.
