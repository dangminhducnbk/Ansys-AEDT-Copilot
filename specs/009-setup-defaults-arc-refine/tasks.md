---
description: "Tasks for feature 009 setup defaults - arc step 30 deg, max refinement per pass 10 %"
---

# Tasks: HFSS setup defaults

**Input**: `specs/009-setup-defaults-arc-refine/` (plan.md, spec.md, research.md, contracts/, quickstart.md)

**Tests**: REQUIRED (Principle VII): offline `unittest` first; AEDT check on board1 COPIES (non-graphical, T013).

**Rules**: Python = `.venv\Scripts\python.exe`; UTF-8 edits; never touch `test/`, `_backup_20261104_2026r1/` or
original boards. Commit after each phase. No push.

## Phase 1: Foundational — template, validation, history

- [X] T001 `templates/autocut_template.csv`: `setup.arc_step_deg` default 30; `setup.max_refine_per_pass` description
  "Whole number 1..100 (AEDT Maximum Refinement Per Pass)"
- [X] T002 `aedt_copilot/cut_board/config.py` `build_params`: `setup.max_refine_per_pass` whole number 1..100 →
  `setup.max_refine_per_pass: phải là số nguyên 1..100`
- [X] T003 `aedt_copilot/interface_sim/defaults_history.py` per `contracts/defaults-history.md` (`HISTORY`, `NOT_YET`,
  `default_at`, `fill`, `effective`); `recut.ADDED_IN` derived from it
- [X] T004 [P] Tests `tests/unit/test_defaults_history.py`: last history value == template default; versions
  increase; `default_at` for 0.6.0 / 0.7.0 / 0.11.0 / 0.11.1 / unparsable; `fill` never changes present keys;
  validation of max refine (0, 101, 10.5 refused; 1, 10, 100 ok)

## Phase 2: User Story 1 + 2 — new defaults everywhere (P1)

- [X] T005 [US1] Update unit tests stating 10 deg as the default (`test_arc_step`, `test_isim_form`); golden test
  still PASS
- [X] T006 [US2] Self-check unit test: read-back `setup.max_refine_per_pass` differing (5 vs 10) → mismatch;
  design_check reports it too

## Phase 3: User Story 3 — earlier runs keep their values (P2)

- [X] T007 [US3] `user_settings.update`: before stamping the current `tool_version`, `fill` every interface `values`
  with the OLD document version (one-time, adds only)
- [X] T008 [US3] `settings.save(..., P)`: store `effective(values, P)`; callers in `apply.run` / `apply.reapply`
  pass P
- [X] T009 [US3] `settings.agreed_values(state, tool_version)` fills history keys; `validate_reapply` / `reapply`
  pass the request's `tool_version`
- [X] T010 [US3] `settings.proposal` (re-cut): kept old value, `default_changes` + `table_md` line + row reason
  `team default now <v>`; 0.6.0 runs unchanged (`team default (new)`)
- [X] T011 [P] [US3] Tests: re-cut of a 0.7.0 doc keeps arc 10 and lists one default change; 0.6.0 doc → 30
  `team default (new)`; re-apply of a 0.9.0 request keeps arc 10; old doc written by 0.11.1 gets arc 10 filled,
  present keys unchanged

## Phase 4: Docs, release

- [X] T012 Guides `setup_note` (arc 30, max refine 1..100), `interface_sim` (default changes on re-cut), README
  (arc 30), `tests/reference/CPHY_U14_U26.json` arc 30, `tests/isim_check.py` expects the template default; VERSION
  0.11.1, CHANGELOG, CLAUDE.md §8; full unit suite + `graphify update .`; commit

## Phase 5: AEDT check (board1 COPIES)

- [X] T013 quickstart §2: isim new cut (arc 30, max refine 10 read back), `--recut` from the 0.7.0 request (keeps 10),
  `tests/design_check.py`; on PASS tag `v0.11.1` locally; converge

## Dependencies

T001-T003 → T004-T011; T007-T010 sequential (same files); T012 after T011; T013 after T012.
