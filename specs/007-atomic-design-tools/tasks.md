---
description: "Tasks for feature 007 Atomic design tools"
---

# Tasks: Atomic design tools

**Input**: `specs/007-atomic-design-tools/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Tests**: REQUIRED (Principle VII): offline `unittest` in `tests/unit/`; AEDT checks on a board1 COPY only after the
user's OK (T019-T020).

**Rules for every task**: Python = `.venv\Scripts\python.exe`; write files UTF-8 with editor tools; do not touch
`test/`, `_backup_20261104_2026r1/`. Code comments Vietnamese, guides English. Commit after each phase. No push.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Foundational (restructure, results identical)

- [X] T001 `aedt_copilot/cut_board/cutter.py`: extract `apply_sweep(st, P, log)` from `apply_setup` (same calls,
  `apply_setup` calls it) and `create_ports(edb, rd, nets, log, replace=False)` from `apply_stage` (same name rule,
  `apply_stage` calls it with its previous behaviour) per `contracts/design-tools.md`
- [X] T002 [P] Offline tests: `apply_setup` with the fake setup of `tests/unit/test_arc_step.py` still sets the same
  attributes; `create_ports` with fake pins: names `<rd>.<pin>.<net>`, existing port skipped, `replace` deletes first
- [X] T003 Create `aedt_copilot/design_tools/__init__.py` (registry load, `run`, `read`) and `_common.py`: board /
  lock check, copy name `<stem>_<op>_<time>.aedb` (+ `_2`), in-place backup `<stem>_old_<time>.aedb`, values →
  `build_params` (op sections only), closest-name helper, report dict + markdown writer (append per op)
- [X] T004 [P] Offline tests `tests/unit/test_design_tools.py`: lock refused; missing board; copy / backup naming and
  never overwrite; validation errors before any file is created; report markdown sections

**Checkpoint**: unit suite PASS → commit.

---

## Phase 2: User Story 1 - setup / sweep / airbox (P1)

- [X] T005 [US1] `design_tools/read.py` (snapshot: setups via `interface_sim.apply.read_setup`, airbox via
  `read_airbox`, ports, solder balls)
- [X] T006 [US1] `design_tools/setup.py` (delete setup of that name → `cutter.apply_setup`; check =
  `setup_mismatches`), `sweep.py` (setup must exist → `cutter.apply_sweep`; check = sweep keys of
  `setup_mismatches`), `airbox.py` (`apply_airbox`; check = `airbox_mismatches`)
- [X] T007 [P] [US1] Tests (fake EDB): changes old → new listed; sweep on unknown setup refused with names; sweep rule
  errors before copy; only the op's sections taken from values

---

## Phase 3: User Story 2 - ports (P1)

- [X] T008 [US2] `design_tools/ports.py`: targets `refdes` (required), `nets` (default = component nets that are not
  reference nets), `replace`; unknown refdes / net → CopilotInputError with closest names; run = `cutter.create_ports`;
  check = every expected port name exists
- [X] T009 [P] [US2] Tests (fake EDB): created / skipped lists; replace; closest-name errors

---

## Phase 4: User Story 3 - solder balls (P2)

- [X] T010 [US3] `design_tools/solder_ball.py`: targets `refdes` (required); run = `cutter.set_solder_ball` per refdes
  (signal-pad short side; component without outer-layer pads → skipped with reason); check = diameter / height mm
  strings read back
- [X] T011 [P] [US3] Tests (fake EDB): skipped component; values from template vs given

---

## Phase 5: CLI, MCP, guide, docs

- [X] T012 `aedt_copilot/__main__.py` sub-command `design --op= --args= | --args-file=` (input error → exit 2, JSON)
- [X] T013 `mcp_server/server.py`: 6 tools `design_read`, `design_setup`, `design_sweep`, `design_airbox`,
  `design_ports`, `design_solder_ball` per `contracts/mcp-tools.md`; in place without `user_approved_in_place` →
  refusal (no CLI call); INSTRUCTIONS / `about()` line
- [X] T014 [P] Tests: server refuses in place without flag; tool list includes the 6 tools; nothing removed
  (`test_interface_unchanged`)
- [X] T015 `guides/design_tools.md` (MISSION / RULES / EXECUTION): when to use vs `workflow` / `interface_sim` (one
  change on any design vs a whole cut), copy default + result path, in place only after explicit go + backup, values
  from template + user, always show the report (changes, skipped, read-back), interface_sim designs → prefer
  re-apply (records stay consistent); `prompts/design-tools.md`
- [X] T016 [P] `README.md`, `CLAUDE.md` §3 / §8
- [X] T017 `VERSION` 0.10.0; `CHANGELOG.md` 0.10.0 (restart Claude, no setup.bat)
- [X] T018 Full unit suite + `graphify update .`; commit

---

## Phase 6: AEDT checks (ask the user first — board1 COPY)

- [X] T019 (2026-11-06: Excel cut job 20261106_235001 regression OK, metrics identical to 0.7.0 run; recut PASS) Ask the user for OK; `tests/regression.py` (Excel flow) + `tests/isim_check.py --recut` identical after the
  cutter extraction (Principle IX)
- [X] T020 (run 1 FAIL -> T021; run 2 2026-11-07 PASS: 5 chained ops ok, other=[], original unchanged; converge -> T022-T023) `tests/design_check.py <cut .aedb copy>` per quickstart §3 (each op: report, read-back OK, other items
  unchanged, original unchanged, in place without flag refused); on PASS tag `v0.10.0` locally; `/speckit-converge`

## Dependencies

- T001 → T002; T003 → T004-T011; T005 before T006-T010 (snapshot used for old → new); T012 → T013.
- T019-T020 after Phase 5 and the user's OK.

## Implementation strategy

MVP = Phases 1-2 (setup / sweep / airbox on a copy). Then ports, solder balls, CLI / MCP / guide, release 0.10.0 after
the AEDT checks.

## Phase 7: Fix from T020 run 1

- [X] T021 Package function `read` shadowed by module `read.py` (CLI `design --op=read` failed: 'function' object has no attribute 'snapshot'); rename to `read_design`, import the module with `importlib`; tests: fresh-process CLI read path + no package function shadows a registry entry

## Phase 8: Convergence

- [X] T022 Copy name when the source is itself a design_tools result: strip earlier `_<op>_<YYYYmmdd_HHMMSS>[_N]` / `_old_<time>` suffixes from the stem so chained calls give `<original>_<op>_<time>.aedb` (T020 showed names growing past Windows path limits) per FR-003 / research R4 (partial)
- [X] T023 Report of a chained call carries the earlier sections: when the source has `<source>.design_tools.md`, the new result's report starts with it, then the new section (guide step 5 promised one cumulative report) per FR-007 / guides/design_tools.md (contradicts)
