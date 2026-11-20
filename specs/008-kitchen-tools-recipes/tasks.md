---
description: "Tasks for feature 008 Kitchen model - utensils + recipes"
---

# Tasks: Kitchen model — utensils + recipes

**Input**: `specs/008-kitchen-tools-recipes/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Tests**: REQUIRED (Principle VII): offline `unittest` in `tests/unit/`; AEDT check on board1 COPIES only after the
user's OK (T024).

**Rules for every task**: Python = `.venv\Scripts\python.exe`; write files UTF-8 with editor tools; do not touch
`test/`, `_backup_20261104_2026r1/`. Code comments Vietnamese, guides / recipes English. Commit after each phase.
No push. No existing tool, format or folder changes (Principle IX).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Foundational — catalogs

- [X] T001 Create `aedt_copilot/kitchen/__init__.py` (docstring: kitchen = utensil catalog + recipe catalog) and
  `aedt_copilot/kitchen/catalog.py` per `contracts/kitchen-catalog.md`: `UTENSILS` for EVERY current MCP tool (45 +
  the 6 new of Phase 3), `utensils(group, kind, safety)`, `by_name()`, `catalog_md()`; process tools `kind: process`
  with their process gate
- [X] T002 Create `aedt_copilot/kitchen/recipes.py` per `contracts/recipes.md`: `team_dir`, `personal_dir`, `parse`,
  `list_recipes`, `get`, `save`, `list_md`
- [X] T003 [P] Tests `tests/unit/test_kitchen.py`: catalog names == server `@mcp.tool` names (AST); safety values;
  every `original / workspace / remote` entry's gate is a parameter of its server function; recipe parse errors name
  the field; list both sources with a name clash (2 entries, `get` without source refused); broken utensil marked;
  `save` personal only, no overwrite without flag, never the team folder; file with bad front matter listed with
  `error`

**Checkpoint**: unit suite PASS → commit.

---

## Phase 2: User Story 2 — recipes for today's processes (P1)

- [X] T004 [US2] Team recipes in `recipes/`: `excel-cut` (guide workflow), `interface-sim` (guide interface_sim),
  `re-cut`, `re-apply`, `pidc-report` (guide pidc_workflow), `layout-edit` (guide layout_edit), `design-tools` (guide
  design_tools): front matter with `guide`, `inputs`, main `steps` (existing tool names) and checkpoints = the
  process gates; body = when to use + "follow get_guide(<guide>)"
- [X] T005 [US2] Test: every team recipe parses, 0 broken, every step utensil in the catalog

---

## Phase 3: User Story 1 — missing utensils (P1)

- [X] T006 [US1] `aedt_copilot/design_tools/__init__.py`: `inspect(op, board, cell, values, targets)` for read-only
  entries (open read-only, no copy, no report file); registry entries get `READ_ONLY = True|False`
- [X] T007 [P] [US1] `design_tools/trace.py` (read) per `contracts/utensils-008.md`
- [X] T008 [P] [US1] `design_tools/end_check.py` (read): `ends.thresholds` / `_measure` / `classify_unusual`; `ends_md`
- [X] T009 [P] [US1] `design_tools/check.py` (read): ends present, ports vs signal pins, `setup_mismatches`,
  `airbox_mismatches`
- [X] T010 [US1] `design_tools/cutout.py` (copy, new design): board copy once to `kitchen/_src` (reuse by size +
  mtime), `channel_sets` + `cut_stage` create_new to `kitchen/<name>_cutout_<time>/<name>.aedb`, `stage1.json`;
  partial output removed only if created by this call; never writes the given board
- [X] T011 [US1] `design_tools/cleanup.py` (copy / original): defaults from `stage1.json` next to the design else
  research R2; `cutter.cleanup_gnd`; report removed counts per layer; check GND ≤ before, nets + ends still present
- [X] T012 [US1] `design_tools/merge.py`: `run(workspace, designs, port, out_dir)` per contract (validation, lock
  rule, names) → `cut_board.merge.merge_designs`
- [X] T013 [US1] CLI `design --op=trace|end_check|check|cutout|cleanup|merge` routing (`design_tools.call`) and
  `kitchen --op=utensils|recipes|get|save` in `aedt_copilot/__main__.py`
- [X] T014 [US1] `mcp_server/server.py`: `design_trace`, `design_cutout`, `design_cleanup`, `design_end_check`,
  `design_check`, `design_merge` (gate `user_approved_merge`, refused without it, no CLI call); `kitchen_utensils`,
  `kitchen_recipes`, `get_recipe`, `save_recipe`; catalog entries for the 10 new tools
- [X] T015 [P] [US1] Tests `tests/unit/test_design_tools_008.py` (fake EDB): trace output shape + closest-name errors;
  end_check unusual; check mismatches (missing port, wrong sweep); cleanup defaults from `stage1.json` vs computed;
  cutout writes only under `kitchen/` (mocked `cut_stage`), never the board, partial removed; merge validation (lock,
  names, port) + `merge_designs` called with backup dir; server: merge refused without flag, cleanup in place refused
  without flag
- [X] T016 [US1] `tests/unit/test_interface_unchanged.py`: new tools present, nothing removed

**Checkpoint**: unit suite PASS → commit.

---

## Phase 4: User Story 3 — new recipes without code (P2)

- [X] T017 [US3] Team recipe `recipes/cut-sweep-merge.md` built only from utensils (design_trace → design_cutout
  [checkpoint] → design_end_check → design_ports → design_setup → design_check → design_merge [checkpoint]) (SC-003)
- [X] T018 [US3] Test: `cut-sweep-merge` parses, ≥ 4 utensils, 0 broken; `save_recipe` of a copy into a temp personal
  folder → listed as `personal` in a fresh `list_recipes()`

---

## Phase 5: Guide, docs, release

- [X] T019 `guides/kitchen.md` (MISSION / RULES / EXECUTION): read `kitchen_recipes` + `kitchen_utensils` first for
  any request; pick a recipe (team or personal; ask on a name clash) or build a sequence from utensils and agree it;
  checkpoints stop for an explicit go; gates of `original / workspace / remote` utensils are locked in the server;
  never write ad-hoc scripts — a missing utensil is reported; save a sequence as a personal recipe only on request
  (`save_recipe`); "bạn làm được gì" → recipes + utensils in one answer
- [X] T020 [P] `prompts/kitchen.md`; INSTRUCTIONS + `about()` in `mcp_server/server.py` mention the kitchen;
  `prompts/copilot-help.md` lists recipes / utensils
- [X] T021 [P] `README.md` (Vietnamese: nhà bếp, dụng cụ, công thức, thư mục công thức cá nhân), `CLAUDE.md` §3 / §8
- [X] T022 `VERSION` 0.11.0; `CHANGELOG.md` 0.11.0 (restart Claude, no setup.bat)
- [X] T023 Full unit suite + `graphify update .`; commit

---

## Phase 6: AEDT check (ask the user first — board1 COPIES)

- [X] T024 Ask the user for OK, then quickstart §2 (`tests/kitchen_check.py`); `tests/regression.py` +
  `tests/isim_check.py --recut` unchanged; on PASS tag `v0.11.0` locally; `/speckit-converge`

## Phase 7: Converge (from the T024 AEDT run, 2026-11-07)

- [X] T025 `design_tools/end_check.comp_nets`: `nets` accept patterns (`CPHY_*`) like the other utensils; before, a
  pattern matched nothing and `design_check` reported `signal_pins=0` with ok=true
- [X] T026 `design_tools/check.py`: no signal pin on the ends → mismatch `signal pins` (never ok on an empty check);
  unit test `test_net_pattern_and_no_signal_pins`
- [X] T027 Recipe `cut-sweep-merge` + `tests/kitchen_check.py`: add `design_airbox` before `design_check` (a new cut
  has the PyEDB default airbox; first run FAIL was this missing step, `design_check` reported it correctly)

## Dependencies

- T001-T002 → T003; T001 → T004-T005; T006 → T007-T011; T010 before T011 (stage1.json); T012-T014 after the entries;
  T017-T018 after T014; docs after T014; T024 after Phase 5 and the user's OK.

## Implementation strategy

MVP = Phases 1-3 (catalogs + missing utensils). Then the example recipe, guide, docs, release 0.11.0 after the AEDT
check. Rebuilding the old processes on utensils = later features (FR-012).
