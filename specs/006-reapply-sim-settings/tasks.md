---
description: "Tasks for feature 006 Re-apply simulation settings"
---

# Tasks: Re-apply simulation settings after apply

**Input**: `specs/006-reapply-sim-settings/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Tests**: REQUIRED (Principle VII): offline `unittest` in `tests/unit/`; AEDT check on a board1 COPY only after the
user's OK (T017).

**Rules for every task**: Python = `.venv\Scripts\python.exe`; write files UTF-8 with editor tools; do not touch
`test/`, `_backup_20261104_2026r1/`. Code comments Vietnamese, guides English. Commit after each phase. No push.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Foundational

- [X] T001 `aedt_copilot/interface_sim/settings.py`: `CUT_PREFIXES`, `SIM_PREFIXES`, `group_of(key)` per
  `contracts/isim-reapply.md`
- [X] T002 [P] Test in `tests/unit/test_isim_reapply.py`: every channel-scope template key belongs to exactly one
  group; unknown prefix → CopilotInputError
- [X] T003 `aedt_copilot/interface_sim/user_settings.py`: `update` pushes the old `values` / `handling` /
  `settings_agreed_at` to `history[]` before replacing; `validate_doc` accepts `history` (list); tests

**Checkpoint**: unit suite PASS → commit.

---

## Phase 2: User Story 2 - Cut settings stay locked (P1)

- [X] T004 [US2] `settings.validate_reapply(request_id, name, values, handling)` per contract (step applied / merged;
  agreed = state.settings.values + defaults + content structural; cut-group differences and handling change listed
  as `đã cắt, đã khoá — cut lại để đổi`; then `build_params` rules)
- [X] T005 [P] [US2] Tests: changed `cleanup.*` / `solder_ball.*` / `port.*` / `series.*` / `cutout.*` refused naming
  the key (SC-002); same values accepted; handling change refused; sweep rule error same message; wrong step →
  CopilotInputError

---

## Phase 3: User Story 1 - Re-apply simulation settings (P1)

- [X] T006 [US1] `aedt_copilot/cut_board/cutter.py` `reapply_sim(edb, P_old, P_new, log)`: delete setups named
  old / new `setup.name` (`edb.setups[n].delete()`, log on error), `apply_setup`, `apply_airbox`; no geometry calls
- [X] T007 [US1] `aedt_copilot/interface_sim/apply.py` `reapply(...)` per contract: busy lock, validate, backup copy
  `final/<name>_old_<time>.aedb`, open, `reapply_sim`, save, metrics (pin shift from previous result), `self_check`,
  geometry compare (ports, components, gnd_vias, gnd_by_layer), result.json, state (`reapplied`, `result_history`,
  `merged` → `applied` with `merged_before`), `settings.save`; failure → `fail`, backup kept
- [X] T008 [US1] CLI op `reapply` in `interface_sim/api.py`; `mcp_server/server.py` `isim_apply`: step
  `ends_checked` → apply (unchanged), `applied` / `merged` → `validate_reapply` (refuse with errors) → op `reapply`;
  `isim_validate_settings` uses `validate_reapply` for applied / merged; docstrings
- [X] T009 [P] [US1] Tests (fake EDB, mocked `open_edb` / `cutter.reapply_sim` / `collect_metrics`): backup created and
  never overwritten (SC-004); state back to applied from merged with `merged_before`; user_settings history; geometry
  diff reported; failure keeps backup and marks failed; MCP `isim_apply` re-apply path refuses a cut change without
  calling the CLI; flag false refused

**Checkpoint**: unit suite PASS → commit.

---

## Phase 4: User Story 3 - Form shows applied tabs (P2)

- [X] T010 [US3] `aedt_copilot/interface_sim/form.py`: `GATE_B_STEPS` += applied / merged; applied tab values =
  `state.settings.values`; cut-group descriptors locked with `already cut - locked (re-cut to change)`; `reapply`,
  `note` for merged; `form.validate` → `validate_reapply` for such tabs
- [X] T011 [P] [US3] Tests in `tests/unit/test_isim_form.py` (update the 005 test that expected applied tabs disabled):
  applied tab enabled, cut group locked, sim group editable with agreed values; merged note; validate uses re-apply rules

---

## Phase 5: Guide, docs, release

- [X] T012 `guides/interface_sim.md`: replace "re-apply with new values is allowed (no re-cut)" with the rule: cut
  group fixed after apply (change = re-cut, Phase R); simulation group (setup / sweep / airbox, incl. convergence and
  arc step) → re-apply = `isim_apply` again after a new explicit go; backup `_old_<time>`; merged → new merge (new
  design); form: applied tabs, Set default only on unlocked rows
- [X] T013 [P] `prompts/interface-sim.md` one line; `README.md`; `CLAUDE.md` §3 / §8
- [X] T014 `VERSION` 0.9.0; `CHANGELOG.md` 0.9.0 (restart Claude, no setup.bat)
- [X] T015 `tests/isim_check.py` scenario `--reapply <request id>` (cut-change refused; sim change applied; backup;
  self-check; geometry equal; user_settings history)
- [X] T016 Full unit suite + `graphify update .`; commit

---

## Phase 6: AEDT check (ask the user first — board1 COPY)

- [X] T017 (run 2 after T018: PASS - backup, self-check OK, geometry_same, history; converge clean) (2026-11-06 run 1: FAIL only on component bbox_mm, in-session vs reopened measure - backup reopened gives the same values; fix T018) Ask the user for OK, then quickstart §2 on the board1 copy; on PASS tag `v0.9.0` locally; run
  `/speckit-converge`

## Dependencies

- T001 → T004 → T007 → T008; T003 before T007; T006 before T007; T010 after T004. Docs any time after T008.
- T017 after Phase 5 and the user's OK.

## Implementation strategy

MVP = Phases 1-3 (re-apply through text). Then the form (US3), docs, release 0.9.0 after the AEDT check.

## Phase 7: Fix from T017

- [X] T018 `apply.geometry_diff` ignores component `bbox_mm` (EDB recomputes it on reopen); pins, GND pins, `pins_extent_mm`, ports, GND vias, GND planes still compared; unit test; contract note
