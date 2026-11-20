---
description: "Tasks for feature 036 - no severity, standard answer, netlist-based schematic check"
---

# Tasks: 036

**Input**: `specs/036-no-severity-netlist/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)

## Phase 1: US1 - OK / NOT OK only (P1)

- [X] T001 [US1] `aedt_copilot/cut_board/review.py`: findings `status` NOT OK / OK (no `severity`), `STATUS_ORDER`, points from NOT OK, overview one colour, summary counts by status, reference table status column, docstrings
- [X] T002 [US1] `aedt_copilot/cut_board/review_report.py`: rows / counts on `status`, remove `SEV_ORDER` / `DANGER` / `danger`
- [X] T003 [US1] `aedt_copilot/review_checks/`: `_report.py` item `status`, `_verdict.py` (not_ok / by_check, findings_md), `_store.py` SCHEMA 4, `__init__.py` (RULE attr, checks_available, sort), `_rules.py` field `not ok when` (+ alias `severity`), every rule module (`TITLE, RULE`), `_example.py`, `_si.py`, `stackup_width.py`, `pair_skew.py` and others setting severity
- [X] T004 [US1] `review_rules/*.md`: header field `not ok when`, texts without HIGH / MEDIUM / INFO; `_template.md`
- [X] T005 [US1] `aedt_copilot/interface_sim/review.py` + `content.py` / `recut.py`: counts `{"NOT OK"}` + `by_check`, no SEVERITIES; `mcp_server/server.py`, `aedt_copilot/catalog/tools.py`, `aedt_copilot/cli/docs.py` texts
- [X] T006 [US1] Unit tests updated (review_report_026, approval_035, check_report_028, review_checks, reference_032, report_033, coded_rules_012, review_rules_030/031, snapshot_023, isim_review, goldens via status mapping) + new test: no severity key / word in outputs

## Phase 2: US3 + US4 - netlist and pin comparison (P1 / P2)

- [X] T007 [US3] `aedt_copilot/interface_sim/netlist.py`: parse Protel 2.0 + Allegro / Telesis, values, design name, warnings
- [X] T008 [US3] `request.start(netlist=)` → netlist.json; `schematic.load_parsed` / `status` netlist first; design check at trace; server `isim_start` + `isim_schematic_status`, api / CLI args
- [X] T009 [US4] `content.compare` pin-based (2-pin wildcard, board only, renamed, pattern-limited missing_on_board, numeric series value); trace stores `schematic_info`
- [X] T010 [US3/US4] Unit tests: netlist parse (Protel + Telesis samples), compare cases (off-page rename, unread pins, 2-pin swap, real mismatch, wrong design)

## Phase 3: US2 + US5 - channel answer (P1)

- [X] T011 [US2] `aedt_copilot/interface_sim/answer.py` + `answer_md` / `answer_image` in `isim_cut_preview` and `isim_review` results; unit test
- [X] T012 [US2/US5] `guides/interface_sim.md` (Phase 0 netlist, Phase 1 step 5 paste `answer_md`, series parts never mentioned), `guides/review_measure.md` (OK / NOT OK, generated rule table), `prompts/interface-sim.md`, `workflows/interface-sim.md`, `workflows/layout-review.md`

## Phase 4: Verification + release

- [X] T013 Full unit suite + `graphify update .`
- [X] T014 AEDT checks on copies (quickstart.md); new `tests/netlist_check.py`; references updated (NOT OK counts); `verify-changes.md`
- [X] T015 Release 4.0.0 locally: VERSION, CHANGELOG.md (Vietnamese, MAJOR), CLAUDE.md §8 row, tag v4.0.0 (no push)

## Dependencies

T001 → T002 → T003 → T004 → T005 → T006; T007 → T008 → T009 → T010; T011 after T005 + T009; T012 after T011;
T013 → T014 → T015.
