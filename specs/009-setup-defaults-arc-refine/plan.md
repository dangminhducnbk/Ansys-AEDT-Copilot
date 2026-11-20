# Implementation Plan: HFSS setup defaults — arc step 30 deg, max refinement per pass 10 %

**Branch**: `main` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

## Summary

1. **Template** (`templates/autocut_template.csv`): `setup.arc_step_deg` default 10 → 30; `setup.max_refine_per_pass`
   stays 10 (description: "% , whole number 1..100").
2. **Validation** (`cut_board/config.build_params`): `setup.max_refine_per_pass` whole number, 1 ≤ v ≤ 100 →
   error `setup.max_refine_per_pass: phải là số nguyên 1..100` before any file is written (FR-004). Same function serves
   Excel, interface simulation, settings form, re-apply and design tools.
3. **Default history** (FR-005, FR-007, US3): today the agreed `values` of a run hold only the keys the engineer
   entered; template defaults are not stored. Changing a default would silently change a re-cut "như lần trước" and a
   re-apply (006) of an old design. New `interface_sim/defaults_history.py`:
   - `HISTORY = {"setup.arc_step_deg": [((0, 7, 0), 10), ((0, 11, 1), 30)]}`; `default_at(key, tool_version)` →
     value the team default had at that version, or `NOT_YET` when the key did not exist yet.
   - `recut.ADDED_IN` derived from `HISTORY` (first version) — same behaviour as 004 for 0.6.0 runs.
   - **Freeze on write**: `user_settings.update` — before stamping the new `tool_version`, every interface section
     whose `values` lack a history key gets the default valid for the OLD `tool_version` of the document (one-time
     migration of old requests, no data lost). New saves (apply / re-apply) add the effective value of every history
     key from P, so each run records its arc step explicitly from now on.
   - **Re-cut proposal** (`settings.proposal`): old value kept (source `previous run <id>`); when it differs from the
     current team default the row reason says `team default now <v>` and the output lists `default_changes
     [{key, previous, team_default}]` (+ one line under `table_md`). Old run without the key and older than the key:
     `team default (new)` (unchanged 004 rule).
   - **Re-apply** (`settings.agreed_values(state, tool_version)`): missing history keys filled with `default_at` of the
     request's `tool_version` → P_old / P_new keep the design's arc step unless the engineer changes it.
4. **Self-check**: already reads back `setup.max_refine_per_pass` and `setup.arc_step_deg` (`apply.read_setup`,
   `expected_setup`, `design_check`); unit tests extended for both with the new defaults.
5. **Docs / tests**: guides `setup_note` (arc step 30, max refine 1..100), `interface_sim` (default changes on re-cut),
   README; `tests/reference/CPHY_U14_U26.json` arc 30, `tests/isim_check.py` expects the template default, unit tests.
6. Version **0.11.1** (patch: default change + validation; no restart needed for the template, restart for guides).

## Technical Context

| Item | Value |
|---|---|
| Language / runtime | Python 3.12, pyedb 0.85, pyaedt 1.9.0 |
| New code | `aedt_copilot/interface_sim/defaults_history.py` |
| Changed code | template CSV, `cut_board/config.py`, `interface_sim/{recut,settings,user_settings,apply}.py`, guides, README, tests |
| Unchanged | cutter (`apply_setup` already writes `max_refine_per_pass` int and `arc_angle`), Excel flow logic, MCP tools |
| Tests | offline unit (`test_arc_step`, `test_isim_recut`, `test_isim_reapply`, `test_isim_user_settings`, new `test_defaults_history`); AEDT on board1 copies: `tests/isim_check.py` (new cut → arc 30, max refine 10 read back), `--recut` from the 0.7.0 request (keeps 10, one default change listed), `tests/design_check.py` |

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I Gates in code | no gate change | PASS |
| II Data safety | nothing retroactive: freeze-on-write only ADDS the value the old run used; history kept | PASS |
| III Single source of defaults | current defaults stay in the template; `HISTORY` records only past team defaults (test: last entry == template default) | PASS |
| IV Rules in guides | setup_note / interface_sim updated (FR-006) | PASS |
| V Regression | reference updated only for arc step; isim / regression / design checks on copies | PASS |
| VI Encoding | edits via Python / editor, UTF-8 | PASS |
| VII Contracts | `contracts/defaults-history.md`; CopilotInputError / build_params errors name the setting + range | PASS |
| VIII Package by function | history lives in interface_sim (only re-cut / re-apply need it) | PASS |
| IX Stable interface | no tool / file format change; `user_settings.json` gains values, same format | PASS |
