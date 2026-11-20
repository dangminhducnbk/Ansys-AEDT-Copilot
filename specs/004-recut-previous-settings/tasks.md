---
description: "Tasks for feature 004 Re-cut from previous settings"
---

# Tasks: Re-cut from previous settings

**Input**: `specs/004-recut-previous-settings/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Tests**: REQUIRED (Principle VII): offline `unittest` in `tests/unit/`; AEDT checks on a board1 COPY only after the
user's OK (T030-T032).

**Rules for every task**: Python = `.venv\Scripts\python.exe`; write files UTF-8 with editor tools (never PowerShell
Set-Content); do not touch `test/`, `_backup_20261104_2026r1/`. Code comments Vietnamese, guides English.
Commit after each phase. No push.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Add row `setup.arc_step_deg,Arc step size,deg,num,channel,no,10,HFSS circle and arc approximation (Advanced Meshing)`
  after `setup.max_delta_zo` in `templates/autocut_template.csv`
- [X] T002 Change `tests/unit/_golden.py` `ADDED_PREFIXES` handling to per-key (`ADDED_KEYS = ("interface_sim.",
  "setup.arc_step_deg")`): strip added rows from `template_rows`, and added keys inside existing sections of
  `build_params_*["P"]` / `defaults` (drop a section only when all its keys are added); keep
  `tests/unit/test_interface_unchanged.py` and `test_core_config.py` PASS

**Checkpoint**: unit suite PASS.

---

## Phase 2: Foundational (blocking US1 + US2)

- [X] T003 Create `aedt_copilot/interface_sim/user_settings.py` per `contracts/isim-user-settings.md`: `FORMAT =
  "aedt_copilot.user_settings/1"`, `path`, `update` (allowed section keys only, header from `request.json`,
  `tool_version` from `aedt_copilot.__version__`, `board_fingerprint` = size + mtime of `<board>/edb.def`, atomic via
  `request.wjson`), `replace`, `load` (path = file or folder; validation per data-model; `dropped` keys not in the
  channel-scope template), `from_state` (0.6.0 folders)
- [X] T004 [P] Tests `tests/unit/test_isim_user_settings.py`: update A then B keeps other interfaces; round trip after
  copying the file to another temp folder = equal (SC-003); every load error names its field; `from_state` on a
  0.6.0-style folder; `replace` moves the section to `replaced[]`
- [X] T005 Wire the file: `content.confirm` → `user_settings.update(content, structural, content_agreed_at,
  recut_from)`; `settings.save` → `user_settings.update(values, handling, settings_agreed_at)` and NO
  `settings.json` / `settings.md`; `request.OUTPUTS` drop the two names; reset to `started` (`request.advance`)
  calls `user_settings.replace`; outputs of `isim_confirm_content` / `isim_apply` include `user_settings` path
  (files `aedt_copilot/interface_sim/{content,settings,request,apply}.py`)
- [X] T006 Update existing tests that expected `settings.json` / `settings.md` (`tests/unit/test_isim_*.py`) and add an
  assertion that an applied interface folder has no `settings.json` / `settings.md` (SC-004)

**Checkpoint**: unit suite PASS → commit.

---

## Phase 3: User Story 1 - Re-cut "like last time" (P1)

**Goal**: list → load → re-trace → only diffs → gates A-B-C pre-filled.
**Independent Test**: offline with fake registry / fake facts; board1 copy in T031.

- [X] T007 [US1] Registry entries get `workspace` (normcase abspath) in `request.start`; `recut.previous` also reads
  `request.json` for old entries without it (`aedt_copilot/interface_sim/request.py`)
- [X] T008 [US1] Create `aedt_copilot/interface_sim/recut.py` per `contracts/isim-recut.md`: `previous(name,
  workspace)`, `source(src, name)` (id / folder / file; `user_settings.load` else `user_settings.from_state`),
  `diff(...)` (pure, item list of data-model), `compare_handling(old_handling, ends)` (pure), `start(request_id,
  name, src)` (refuse same request; `content.trace` with old ends + nets; set state `recut_from`; return
  `recut_diffs`, `old_values`, `old_handling`, `dropped`)
- [X] T009 [US1] `content.validate_content`: every `recut_diffs[]` item needs a non-empty `resolution` (same message
  style as schematic diffs) (`aedt_copilot/interface_sim/content.py`); `content_md` shows a "Changes since previous
  run" table (or "No difference") first when `recut_diffs` is present
- [X] T010 [US1] `ends.check`: when state has `recut_from`, add `handling_compare` and pass `old_values` to
  `settings.proposal`; `settings.proposal` marks `source` = `previous run <id>` / `team default (new)` and returns
  `dropped` (`aedt_copilot/interface_sim/{ends,settings}.py`)
- [X] T011 [US1] CLI ops `previous`, `recut` in `aedt_copilot/interface_sim/api.py`; MCP tools `isim_previous`,
  `isim_recut` in `mcp_server/server.py` per `contracts/mcp-tools.md` (thin; `isim_recut` runs as task like
  `isim_trace`); `about()` / INSTRUCTIONS mention re-cut
- [X] T012 [P] [US1] Tests `tests/unit/test_isim_recut.py`: `previous` filters workspace + name, newest first, 0.6.0
  entries; `source` id / folder / file / ambiguous / missing; `diff` each item type + 0 items when equal (SC-002);
  `compare_handling` kept / not_needed / needs_choice; `start` refuses the source request; gate A refuses an
  unresolved `recut_diffs` item; settings source labels + dropped
- [X] T013 [US1] Extend `tests/unit/test_interface_unchanged.py` expectation: tool list = old list + `isim_previous`,
  `isim_recut` (nothing removed)

**Checkpoint**: unit suite PASS → commit.

---

## Phase 4: User Story 3 - Arc step 10 deg (P2)

- [X] T014 [US3] `aedt_copilot/cut_board/config.py` `build_params`: error when `setup.arc_step_deg` not in (0, 90]
  (message style of the sweep rule)
- [X] T015 [US3] `aedt_copilot/cut_board/cutter.py` `apply_setup`: `st.curve_approx_settings.arc_angle =
  f"{float(s['arc_step_deg']):g}deg"` (try / log like other items); `metrics` adds `arc_step_deg` read back
- [X] T016 [US3] `aedt_copilot/interface_sim/apply.py`: `read_setup` reads `arc_angle` → float deg;
  `expected_setup` adds `setup.arc_step_deg`
- [X] T017 [P] [US3] Tests `tests/unit/test_arc_step.py`: template default 10 via `build_params`; 0 / 91 / -1 refused;
  `read_setup` fake with `'10deg'` → no mismatch, `'30deg'` → mismatch; update `tests/unit/test_isim_self_check.py`
  fake setup with `curve_approx_settings`
- [X] T018 [US3] `tests/regression.py` + `tests/reference/CPHY_U14_U26.json`: expect `arc_step_deg` 10

**Checkpoint**: unit suite PASS → commit.

---

## Phase 5: Guide, docs, release

- [X] T019 `guides/interface_sim.md`: new section "Re-cut (như lần trước)" — trigger words / id / path ALWAYS use
  `isim_previous` → `isim_start` → `isim_recut`; never re-type old values; show only differences; gate A go even with
  0 diffs; handling compare; pre-filled settings; dropped / new rows; FILES section: `user_settings.json` replaces
  `settings.json` / `settings.md`; settings line in RULES; phases table
- [X] T020 [P] `prompts/interface-sim.md`: mention re-cut ("như lần trước")
- [X] T021 [P] `README.md` (Vietnamese): re-cut + `user_settings.json` + arc step; `CLAUDE.md` §3 interface_sim line,
  §8 status row 004
- [X] T022 `VERSION` → `0.7.0`; `CHANGELOG.md` 0.7.0 (re-cut, `user_settings.json` replaces settings.json/.md, arc step
  10 deg changes results, restart Claude for new tools, no setup.bat rerun)
- [X] T023 Run full unit suite + `graphify update .`; commit

---

## Phase 6: AEDT checks (ask the user first — machine use, board1 COPY)

- [X] T030 (2026-11-06: user OK relayed by the parent session, "Đồng ý") Ask the user for OK (Vietnamese, short) to run T031-T032 on the board1 copy (~15 min) and to open one
  design in the AEDT GUI (T032)
- [X] T031 (2026-11-06: recut 20261105_202026 -> 20261106_170050: 0 diffs, U26 smd_rebuild kept, metrics equal, self-check OK, arc 10, user_settings.json written, no settings.json; Excel flow job 20261106_170737 regression OK) `tests/isim_check.py` scenario `recut`: re-cut CPHY_U14_U26 from the 0.6.0 request in the scratch copy →
  0 diffs, handling all `kept`, apply with `old_values`, self-check OK incl. arc step 10, metrics equal to the first
  run; `tests/regression.py` PASS with `arc_step_deg` 10
- [X] T032 (2026-11-06: AEDT 2026.1 GUI opened a copy, setup CurveApproximation/ArcAngle = 10deg; tag left to the user) Open one cut design in AEDT 2026 R1 GUI (user not using AEDT): Setup → Advanced Meshing → arc step shows
  10 deg; report; tag `v0.7.0` locally (push by user); run `/speckit-converge`

## Dependencies

- T001-T002 → T003-T006 → US1 (T007-T013). US3 (T014-T018) needs only T001-T002 (parallel with Phase 2-3).
- T005 before T010 (settings.save changed). T008 before T011-T012. Phase 6 after Phase 5 and the user's OK.

## Parallel examples

- T004 ‖ T014-T017 (different files). T012 after T008. T020 ‖ T021.

## Implementation strategy

MVP = Phases 1-3 (one file + re-cut). Then arc step (US3), docs, release 0.7.0 after the AEDT checks.

## Phase 7: Convergence

- [X] T033 CRITICAL: validate `nets` in `aedt_copilot/interface_sim/recut.py` `start` (None or list of non-empty str -> else CopilotInputError) per Constitution VII (missing)
- [X] T034 When an old end refdes is no longer on the board, `recut.start` returns `recut_diffs` [end_missing] + `blocked` (nothing traced / cut) instead of a bare trace error; guide tells the agent to ask for the new end (normal `isim_trace`) per spec Edge Cases / FR-003 (partial)
- [X] T035 Show the failure reason of a failed previous run: `error` in `recut.previous` records + table, `previous_error` in `recut.start` output per spec Edge Cases (partial)
- [X] T036 MCP docstrings of `isim_check_ends`, `isim_confirm_content`, `isim_apply` mention the 004 outputs (`handling_compare` / `values` / `handling`, `user_settings` path) per contracts/mcp-tools.md (partial)

## Phase 8: Patch 0.7.1 (user 2026-11-06, guide-only)

- [X] T037 `guides/interface_sim.md` (+ one line in `prompts/interface-sim.md`): at GATE A (ends choice, board vs schematic / re-cut resolutions) and GATE B (sweep start / stop / step GHz, sweep type, basis order, max passes, delta S, arc step deg, one choice group per unusual end with its `options`) show an input form pre-filled with the proposal / defaults when the client can render interactive widgets, else the markdown table; the form answer is INPUT, not the gate go (show the resulting table from the tool, wait for an explicit "đồng ý"); mandatory sweep fields stay empty; server validation and the Excel flow unchanged; VERSION 0.7.1 + CHANGELOG

## Phase 9: Patch 0.7.2 (user 2026-11-06)

- [X] T038 `aedt_copilot/interface_sim/apply.py` `self_check` reads back ALL `airbox.*` values from the saved EDB (`read_airbox` / `expected_airbox` / `airbox_mismatches`, T050 pattern; operating freq compared in GHz); offline tests `tests/unit/test_isim_airbox_check.py`. The Excel flow has no self_check (not shared) - unchanged
- [X] T039 Guide `interface_sim` GATE B form: airbox group (extent types dropdowns, paddings numbers, z_from_stackup checkbox, open region radiation / pml, operating freq) pre-filled with defaults; prompt line; contract `003/contracts/isim-cut.md`
- [X] T040 (2026-11-06: recut 20261105_202026 -> 20261106_193617 PASS, self-check OK incl. airbox, metrics equal) AEDT check on a board1 COPY: re-cut CPHY_U14_U26 (`tests/isim_check.py --recut`) -> self-check OK incl. airbox; VERSION 0.7.2, CHANGELOG, tag v0.7.2 local
