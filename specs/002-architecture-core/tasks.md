---
description: "Tasks for feature 002 Architecture + core/"
---

# Tasks: Architecture + core/

**Input**: `specs/002-architecture-core/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Tests**: REQUIRED (FR-016, Principle VII): offline `unittest` in `tests/unit/`, golden data captured from the
code BEFORE the move; AEDT regression + PI-DC check at the end (ask user first, machine use).

**Rules for every task**: Python = `.venv\Scripts\python.exe`; write files UTF-8 with editor tools (never PowerShell
Set-Content); do not touch `test/`, `_backup_20261104_2026r1/`, guides, prompts, templates, `mcp_server/server.py`.
Comments in code: Vietnamese (existing style). Commit after each phase.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup (baseline BEFORE any code move)

- [X] T001 Create `tests/unit/__init__.py` (empty) and `tests/unit/golden/` folder
- [X] T002 Write `tests/unit/_make_golden.py`: using the CURRENT code, dump to `tests/unit/golden/pre002.json`:
  `cut_board.config.template_rows()`; `pi_dc.common.params()`; `edit_layout.run.defaults()`;
  `cut_board.config.machine()` keys (not values of `python`); `cut_board.config.build_params({})` (P + errors) and
  `build_params` with sweep 0/10/0.1 filled; a coerce table (values `None`, `""`, `" 3 "`, `"3.0"`,
  `"1e3"`, `"-0.5"`, `"yes"`, `"X"`, `"off"`, `"a; b,1"`, `"txt"` × types num/bool/text/list; record the result or
  the exception type + message); geometry cases (point_seg_dist incl. zero-length segment, seg_seg_dist crossing /
  touching / parallel, point_in_poly inside / outside / on edge / 2-point poly, poly_area square / triangle /
  < 3 points, bbox_of, edges) with `repr()` of floats so comparison is exact
- [X] T003 Run `.venv\Scripts\python.exe tests/unit/_make_golden.py` on the unmodified code; commit `pre002.json`
- [X] T004 [P] Write `tests/unit/golden/interface_pre002.json`: MCP tool names (parse `@mcp.tool` function names in
  `mcp_server/server.py` by AST), prompt names (`prompts/*.md`), guide names (`guides/*.md`), template file names,
  CLI sub-command names (AST of `aedt_copilot/__main__.py` `add_parser` calls), public names of
  `cut_board.config` / `cut_board.geometry` / `aedt_env`
- [X] T005 (deferred to T026: baseline produced from commit 1120735 in a scratch worktree, so no AEDT run before the move) Ask the user (Vietnamese, short) for OK to run baseline AEDT checks now: cut CPHY_U14_U26 on the board1
  COPY (~6 min) + `pidc --skip-export` on the BOARDB_B04 folder; save job `result.json` metrics and PI-DC
  `results/*.json` to the session scratchpad as baseline. If the user declines, baseline = `tests/reference/*.json`
  and `tests/reference_pidc/*.json`

**Checkpoint**: golden data committed; code still unchanged.

---

## Phase 2: Foundational (core/ basics, blocking all stories)

- [X] T006 Create `aedt_copilot/core/__init__.py` (docstring: core layer, imports no feature package; list of modules)
- [X] T007 Implement `aedt_copilot/core/errors.py` per `contracts/core-errors.md`: `CopilotInputError(ValueError)`
  with `name`, `expected`, `got` (sentinel MISSING), message `"<name>: expected <expected>, got <got!r>"`, TypeError
  on empty name / expected; `RegistryError(RuntimeError)`
- [X] T008 Implement `aedt_copilot/core/validate.py` per `contracts/core-validate.md`: `require_type`,
  `require_number` (rejects bool, NaN, inf; inclusive / exclusive bounds), `require_int` (rejects bool and 3.0),
  `require_choice`, `require_text` (strip, regex full match, forbidden chars), `require_path` (strip spaces / double
  quotes, abspath, kind any|file|dir)
- [X] T009 [P] Tests `tests/unit/test_core_errors.py` (message format, ValueError subclass, attributes, TypeError)
- [X] T010 [P] Tests `tests/unit/test_core_validate.py` (every error branch + returned value; temp dir for paths)

**Checkpoint**: `python -m unittest discover -s tests/unit` PASS.

---

## Phase 3: User Story 2 - One shared core (P1)

**Goal**: config/template, edb session, geometry, units in `core/`, no feature import.
**Independent Test**: unit suite PASS; golden equal; import-rule test PASS.

- [X] T011 [US2] Implement `aedt_copilot/core/config.py` per `contracts/core-config.md`: `ROOT` (repo root =
  `parents[2]` of the file), `TEMPLATES_DIR`, `CONFIG_FILE`, `TEMPLATES`, `template_path(name)`, `machine()` (code
  moved verbatim from `cut_board/config.py`), `template_rows(path)` by HEADER name — mapping `Key→key,
  Parameter→name, Unit→unit, Type→type ("text" if missing), Scope→scope ("channel"), Mandatory→mandatory (== "yes",
  case-insensitive), Default→default (None if ""), Description→desc` — same comment / blank / `utf-8-sig` / skip
  empty-key rules, cache by (abs path, mtime), deep copy; `coerce(value, typ)` verbatim + CopilotInputError for
  unknown `typ`
- [X] T012 [P] [US2] Implement `aedt_copilot/core/geometry.py` (pure functions moved verbatim from
  `cut_board/geometry.py`: point_seg_dist, _cross, seg_seg_dist, point_in_poly, poly_area, bbox_of, edges) and
  `aedt_copilot/core/geometry_edb.py` (`prim_points` verbatim) per `contracts/core-geometry.md`
- [X] T013 [P] [US2] Implement `aedt_copilot/core/units.py` per `contracts/core-units.md` (`MM`, `MM2`, 4
  converters, `edb_length(m, digits=4)` = `f"{round(m / MM, digits):g}mm"`, validation via core.validate)
- [X] T014 [US2] Implement `aedt_copilot/core/edb.py` per `contracts/core-edb.md`: `aedb_path` (logic of
  `edit_layout/run._aedb`: strip, `.aedt`→`.aedb`, `edb.def`→dirname, abspath, must be dir), `open_edb` (validate,
  then `from ..aedt_env import open_edb` inside the function), `edb_session` (contextlib, close in finally, close
  error suppressed only if body raised, printed to stderr)
- [X] T015 [US2] Change `aedt_copilot/aedt_env.py` `_machine()` to `from .core import config` (no other change)
- [X] T016 [P] [US2] Tests `tests/unit/test_core_config.py`: `template_rows(autocut)` == golden
  `cut_board.config.template_rows()`; pidc / layout_edit rows give golden `params()` / `defaults()` when mapped as in
  T019/T020; coerce table == golden (value or exception type + message); unknown typ → CopilotInputError; temp CSV
  with BOM, comments, blank lines, missing columns, missing file, bad header; cache refresh on mtime change;
  `machine()` with temp config file (missing, empty, relative python)
- [X] T017 [P] [US2] Tests `tests/unit/test_core_geometry.py` (golden, exact `repr` equality; prim_points fallback
  order with fake objects) and `tests/unit/test_core_units.py` (values, `edb_length(0.0002) == "0.2mm"`, errors)
- [X] T018 [P] [US2] Tests `tests/unit/test_core_edb.py`: aedb_path cases (`.aedb` dir, `.aedt` file, `edb.def`,
  quotes, missing → CopilotInputError) in a temp dir; `edb_session` with a fake opener (close called on success /
  on exception; close error suppressed vs propagated); `open_edb` with bad input raises BEFORE importing pyedb
  (assert `"pyedb" not in sys.modules` in a subprocess)
- [X] T019 [US2] Re-point `aedt_copilot/pi_dc/common.py` `params()` to `core.config.template_rows(template_path("pidc"))`
  + `coerce(row["default"], row["type"])`, key without `pidc.` prefix; keep `TEMPLATE`; `pi_dc/export.py` and
  `pi_dc/skills/power_tree.py` take `machine()` from `..core.config` / `...core.config`
- [X] T020 [US2] Re-point `aedt_copilot/edit_layout/run.py`: `TEMPLATE = core.config.template_path("layout_edit")`,
  `defaults()` = `{r["key"]: float(r["default"]) for r in template_rows(TEMPLATE)}`, `_open` uses `core.config.machine()`;
  remove `from ..cut_board import config`
- [X] T021 [US2] Test `tests/unit/test_core_imports.py`: AST-scan every `aedt_copilot/core/*.py` and
  `aedt_copilot/aedt_env.py`; FAIL on import of `cut_board`, `pi_dc`, `edit_layout`, `cli`, `mcp_server` (absolute or
  relative); also FAIL if `pi_dc/` or `edit_layout/` import `cut_board`

**Checkpoint**: unit suite PASS, golden equal → commit.

---

## Phase 4: User Story 1 - Nothing changes for the team user (P1)

**Goal**: old paths are thin re-exports; interface lists unchanged; results identical.
**Independent Test**: interface test + golden PASS; cut regression + pidc_check PASS identical to baseline.

- [X] T022 [US1] Rewrite `aedt_copilot/cut_board/config.py` as thin layer: re-export `ROOT`, `CONFIG_FILE`, `machine`,
  `coerce` from `core.config`; `TEMPLATE_FILE = template_path("autocut")`; `template_rows()` (no arg) =
  `core.config.template_rows(TEMPLATE_FILE)`; keep `build_params` and `defaults` code unchanged (cut-only, moves in 004)
- [X] T023 [US1] Rewrite `aedt_copilot/cut_board/geometry.py` as re-export of `core.geometry` (incl. `_cross`) +
  `core.geometry_edb.prim_points`; docstring says "kept for compatibility, use core.geometry"
- [X] T024 [US1] Test `tests/unit/test_interface_unchanged.py`: recompute the lists of T004 and compare with
  `golden/interface_pre002.json` (equal); golden values of `cut_board.config.*` and `cut_board.geometry.*` via old
  paths still equal `pre002.json`; `build_params({})` errors list equal to golden (add to T002 dump)
- [X] T025 [US1] Run full offline suite `.venv\Scripts\python.exe -m unittest discover -s tests/unit -v` → all PASS;
  run `python -m aedt_copilot --help` and `about`-equivalent import of `mcp_server/server.py` (import only, no start)
  to prove no ImportError
- [X] T026 [US1] (2026-11-05: cut CPHY_U14_U26 old 1120735 vs new -> metrics/warnings/nets identical, regression OK; PI-DC VCC_0P8V 3 skills on copies -> identical except image paths/seconds, pidc_check PASS) Ask the user for OK, then run quickstart §3 (cut CPHY_U14_U26 on board1 COPY + `tests/regression.py`)
  and §4 (`pidc --skip-export` + `tests/pidc_check.py`); compare metrics with the T005 baseline (identical) — report
  table to the user; on any difference STOP and fix before continuing

**Checkpoint**: Principle IX proven → commit.

---

## Phase 5: User Story 3 - Add a rule as one new file (P2)

**Goal**: registry helper ready for 003+. **Independent Test**: registry tests PASS.

- [X] T027 [US3] Implement `aedt_copilot/core/registry.py` per `contracts/core-registry.md`: `load(package,
  required=("NAME","ORDER","run"))` (accept dotted name or module; `pkgutil.iter_modules(pkg.__path__)`; skip names
  starting with `_` and sub-packages; import errors → RegistryError chained; check NAME non-empty str, ORDER int not
  bool, run callable; duplicate NAME → RegistryError naming both modules; sort by (ORDER, NAME)); `by_name(entries)`
- [X] T028 [US3] Tests `tests/unit/test_core_registry.py`: build throw-away packages in a temp dir on `sys.path`
  (2 entries out of file order → sorted; `_helper.py` skipped; empty package → []; duplicate NAME; missing ORDER;
  ORDER bool; run not callable; module raising on import; non-package input → CopilotInputError); adding a 3rd
  entry file only (no other edit) → appears (SC-006)

---

## Phase 6: User Story 4 - Restructure plan written down (P2)

- [X] T029 [US4] (ROADMAP rev 2 of 2026-11-05 supersedes rev 1 list 002-014, agreed with user) Check `specs/ROADMAP.md` against spec US4 acceptance (002-014 listed, types, gates, stackup
  postponed, every module of the user decision has a place); fix gaps
- [X] T030 [US4] Update `CLAUDE.md` §3 REPO LAYOUT: add `core/` modules, link `specs/ROADMAP.md` and
  `specs/CONTRACTS.md`; §8 STATUS row "002 core/ done"

---

## Phase 7: Polish & release

- [X] T031 Remove nothing old; confirm no remaining `cut_board.config` import inside `pi_dc/`, `edit_layout/`,
  `aedt_env.py` (T021 passes)
- [X] T032 [P] `VERSION` → `0.5.1`; `CHANGELOG.md` entry "0.5.1 — internal: new `core/` package (errors, validate,
  config, edb, geometry, units, registry); no behaviour change; no setup.bat rerun"
- [X] T033 Run `graphify update .`
- [X] T034 Commit; tag `v0.5.1` locally (push by user); run `/speckit-converge`

## Dependencies

- Phase 1 → Phase 2 → US2 (Phase 3) → US1 (Phase 4) → Polish. US3 (Phase 5) needs only Phase 2; US4 (Phase 6)
  independent (docs).
- T002/T003 MUST run before ANY code change (golden from old code). T015, T019, T020 before T021. T022/T023 after T011/T012.
- T005 and T026 need the user's OK (AEDT / machine use).

## Parallel examples

- Phase 2: T009 ‖ T010 after T007/T008.
- US2: T012 ‖ T013 (different files); T016 ‖ T017 ‖ T018 after their modules.
- US3 (T027-T028) can run in parallel with US2 / US1; US4 (T029-T030) any time.

## Implementation strategy

MVP = Phase 1-4 (core + identical results). Then US3 (registry, needed by 003), US4 docs, release 0.5.1.

## Phase 8: Convergence

- [X] T035 Add a test for `core.registry.by_name` rejecting a duplicate NAME (RegistryError naming both modules) in `tests/unit/test_core_registry.py` per SC-004 / contracts/core-registry.md (partial)
- [X] T036 Move the `TestUnits` cases from `tests/unit/test_core_geometry.py` into `tests/unit/test_core_units.py` (file named by contracts/core-units.md and T017) per FR-016 (partial)
- [X] T037 Add a dated note to `specs/002-architecture-core/spec.md` (US4 / SC-007) that `specs/ROADMAP.md` rev 2 (2026-11-05, agreed with user) replaces the 002-014 list with 002-008 per US4/AC1 (contradicts)
