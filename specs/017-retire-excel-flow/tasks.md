# Tasks: Retire the Excel cut flow (017)

**Input**: [spec.md](spec.md) (approved inventory), [plan.md](plan.md)

## Phase 1: Foundational (no behaviour change)

- [X] T001 Create aedt_copilot/cut_board/naming.py (board_paths, default_name, unique_name, parse_request, group_diff moved verbatim); switch imports in aedt_copilot/cut_board/review.py, aedt_copilot/review_checks/__init__.py, aedt_copilot/review_checks/routing.py, aedt_copilot/interface_sim/content.py, aedt_copilot/design_tools/cutout.py; unit suite PASS

## Phase 2: User Story 2 — remove (approved table only)

- [X] T002 [US2] Server: remove 7 tools + Excel gate code in mcp_server/server.py; catalog entries in aedt_copilot/kitchen/catalog.py; instructions rewritten
- [X] T003 [US2] CLI: remove propose / cut / status / report / merge / run-job / worker / review in aedt_copilot/cli/parser.py, aedt_copilot/cli/commands.py; docs.about steps in aedt_copilot/cli/docs.py
- [X] T004 [US2] Modules: delete aedt_copilot/cut_board/excel_io.py, propose.py, batch.py; remove cutter.cut_channel / _cut, merge.merge (job) in aedt_copilot/cut_board/cutter.py, merge.py
- [X] T005 [US2] Prompts cut-*.md, guide workflow.md, recipe excel-cut.md deleted; template rows run.channel_timeout_min / run.max_parallel removed

## Phase 3: Moved content + docs

- [X] T006 Move setup_note / verify into guides/interface_sim.md, review_layout into guides/review_measure.md, then delete those 3 guides; finish_in_aedt usage in guides/interface_sim.md + guides/design_tools.md; fix guides/design_tools.md, guides/kitchen.md, prompts/copilot-help.md, README.md, specs/010-*/contracts/legacy-tools.md (removed note)

## Phase 4: User Story 3 — tests

- [X] T007 [US3] Rewrite tests/regression.py on the interface-sim flow (same reference); tests/isim_check.py keeps importing check
- [X] T008 [US3] Unit tests: drop Excel cases, REMOVED_017 in goldens, new tests/unit/test_retire_excel_017.py; full suite PASS; grep 0 references (SC-001); graphify update
- [X] T009 [US3] AEDT on board1 copies: tests/regression.py PASS, tests/isim_check.py PASS

## Phase 5: Release

- [X] T010 [US4] VERSION 1.0.0, CHANGELOG migration note (tool → replacement, old jobs → tag v0.15.0), CLAUDE.md status + layout, ROADMAP 017 done; commit + local tag v1.0.0 (no push)

## Dependencies

T001 → T002..T005 → T006 → T007 → T008 → T009 → T010.

## Converge (2026-11-09)

- [X] T011 `inspect_board.py` still imported `excel_io` (found by grep after removal) → `naming`
- FR-001..005 checked; SC-001 (`test_retire_excel_017`: no removed tool in guides / prompts / recipes / instructions, no kept module imports a removed one), SC-002 (2026-11-09 board1 copies: new tests/regression.py (isim flow) PASS - 24 ports, 101 GND vias, GND planes 845-865 mm2 1 piece each, pin shift 0.21 mm, arc 30 (same numbers as the Excel flow); tests/isim_check.py PASS (U21_J25 18 ports).), SC-003 (336 unit tests).
