---
description: "Tasks for feature 035 - review approval by the user before cut"
---

# Tasks: Review approval by the user before cut (035)

**Input**: `specs/035-review-approval-gate/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)

## Phase 1: Foundational (blocks all stories)

- [X] T001 `aedt_copilot/review_checks/_verdict.py`: `verdict_md` without verdict word / HIGH table (counts + incomplete + failed checks); `aedt_copilot/review_checks/__init__.py`: remove `gate_of`, `measure_report` passes `gate=None`; `aedt_copilot/cut_board/review_report.py`: no gate line in the header
- [X] T002 `aedt_copilot/review_checks/_store.py`: remove `decide` / `validate_decisions` / `merge_decisions` (record `decisions` kept read-only)

## Phase 2: User Story 1 - Read the report, then decide (P1)

- [X] T003 [US1] `aedt_copilot/interface_sim/review.py`: `run` always writes the HTML for a full review (snapshot, reused review re-rendered), stores `html` in review.json + user_settings `review.html`, resets `approval`; no `verdict` / `stop_md`; remove `decide`, `override`, `WAYS`
- [X] T004 [US1] `aedt_copilot/interface_sim/review.py`: `gate_status` statuses not_reviewed / out_of_date / no_report / ready / approved; `require(for_cut)`; `approve(...)`; `status_label`; `aedt_copilot/interface_sim/request.py` Review column
- [X] T005 [US1] `aedt_copilot/interface_sim/content.py`: GATE A requires review ready + error-free preview of the same settings key, then `review.approve` (preview path, `user_words`); `aedt_copilot/interface_sim/cut.py`: `require(for_cut=True)`
- [X] T006 [US1] `mcp_server/server.py`: `_review_refusal` on new statuses + messages (contracts/mcp-tools.md); `isim_confirm_content` `user_words`; `isim_cut` refusal without approval; remove `isim_review_decide`, `isim_review_override`, `design_review_decide`; descriptions + server `instructions` without STOP
- [X] T007 [US1] `aedt_copilot/catalog/tools.py`, `aedt_copilot/cli/commands.py`, `aedt_copilot/cli/parser.py`, `aedt_copilot/interface_sim/api.py`, `aedt_copilot/cli/docs.py` (about lines): remove the 3 tools / ops; goldens: REMOVED_035 list in `tests/unit/test_interface_unchanged.py` / `tests/unit/test_thin_layers_014.py`
- [X] T008 [US1] Unit tests `tests/unit/test_approval_035.py`: statuses, GATE A refused without review / report / preview / with preview errors, approval recorded (fields), cut refused without approval and allowed with HIGH findings, approval out of date after board / nets change, 2.12.0 user_settings with override not counted, no verdict text in summaries / report header; update `tests/unit/test_review_gate_025.py`, `tests/unit/test_isim_review.py`, catalog tests

## Phase 3: User Story 2 - Cut area + review file + one question (P1)

- [X] T009 [US2] `aedt_copilot/cut_board/end_gnd.py`: `final_scene` (pure) + legend item `Cut region`; `aedt_copilot/interface_sim/cut_preview.py`: `image` = final region, `detail` = diagnostic image; unit test in test_approval_035
- [X] T010 [US2] `guides/interface_sim.md`: Phase 1 rewritten (trace → snapshot → review → preview with defaults → 3-part answer → one go = GATE A; questions only end candidates / schematic differences; content / findings / cut form only on request); Phase 1.5 STOP rules removed; `guides/review_measure.md` (severity = information, no verdict, no decide); `guides/catalog.md`; `workflows/interface-sim.md`, `workflows/layout-review.md`

## Phase 4: User Story 2b - Settings form (P1)

- [X] T011 [US2b] `aedt_copilot/interface_sim/cut.py` + `aedt_copilot/interface_sim/ends.py`: result `next` (settings form); `guides/interface_sim.md` GATE B: form MANDATORY (widget, else full table_md once; never per-value questions); unit test

## Phase 5: User Story 3 - Standalone review (P2)

- [X] T012 [US3] `design_review` summary / result without verdict text (uses T001); `mcp_server/server.py` description; unit test

## Phase 6: Polish & verification

- [X] T013 Full unit suite + `graphify update .`
- [X] T014 AEDT checks on copies (quickstart.md): `tests/regression.py`, `tests/isim_check.py`, `tests/pcie_check.py`, `tests/preview_check.py`, `tests/review_check.py` updated to the approval flow; `tests/review_gate_check.py` rewritten as approval check; numbers = 2.12.0; write `specs/035-review-approval-gate/verify-changes.md`
- [X] T015 Release 3.0.0 locally: VERSION, CHANGELOG.md (Vietnamese, MAJOR: 3 tools removed, new flow; restart Claude / new chat, no setup.bat), CLAUDE.md §8 row + §3 notes, tag v3.0.0 (no push)

## Dependencies

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008; T009 after T004; T010 after T006 + T009; T011 after T005;
T012 after T001; T013 → T014 → T015.
