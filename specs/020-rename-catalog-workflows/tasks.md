# Tasks: Remove the "kitchen" metaphor from all names (020)

**Input**: spec.md, plan.md. Pure rename, behaviour unchanged. Commit after implement / converge / release.

## Phase 1: Setup

- [X] T001 `git mv` package `aedt_copilot/kitchen/` → `aedt_copilot/catalog/` (catalog.py → tools.py, recipes.py → workflows.py), `guides/kitchen.md` → `guides/catalog.md`, `prompts/kitchen.md` → `prompts/catalog.md`, `recipes/` → `workflows/`, `tests/unit/test_kitchen.py` → `test_catalog.py`, `test_kitchen_guards.py` → `test_catalog_guards.py`, `tests/kitchen_check.py` → `tests/catalog_check.py`

## Phase 2: Foundational (US1 + US2 code)

- [X] T002 [US1] `aedt_copilot/catalog/tools.py`: `TOOLS`, `tools()`, `KINDS = ("tool", "process")`, group `catalog`, 4 renamed entries, `catalog_md` header `Tool`, `CONTRACTS` → 020 contracts for tools that pointed at 008 / 010
- [X] T003 [US2] `aedt_copilot/catalog/workflows.py`: `team_dir()` = `workflows/`, `personal_dir()` env `AEDT_COPILOT_WORKFLOWS` / `~/.aedt_copilot/workflows`, `legacy_dirs()` (env `AEDT_COPILOT_RECIPES`, `~/.aedt_copilot/recipes`, read only), step key `tool` (+ old `utensil`), `list_workflows` with `shadowed`, `get` skips shadowed, `save` new folder only, `list_md` header `Workflow`
- [X] T004 [US1] `aedt_copilot/catalog/registration.py` (`CatalogRegistrationError`, message), `api.py` (ops `tools`, `workflows`, `get`, `save`), `__init__.py`
- [X] T005 [US1] `mcp_server/server.py`: import `aedt_copilot.catalog.registration`, `_catalog`, tools `list_tools`, `list_workflows`, `get_workflow`, `save_workflow`, INSTRUCTIONS "TOOL CATALOG", docstrings without DỤNG CỤ / NHÀ BẾP
- [X] T006 [US1] CLI `aedt_copilot/cli/parser.py`, `commands.py` (`catalog`), `docs.py` (about text)
- [X] T007 [US3] `aedt_copilot/design_tools/cutout.py` (`OUTPUT`, `output_dir`), `merge.py` out_dir `design_tools`; wording in `design_tools/end_check.py`, `interface_sim/settings.py`

## Phase 3: Text

- [X] T008 [US1] guides `catalog.md`, `design_tools.md`, `layout_edit.md`; prompts `catalog.md`, `copilot-help.md`; `workflows/*.md` (`tool:` keys, wording)
- [X] T009 [P] contracts `specs/020-rename-catalog-workflows/contracts/catalog.md`, `contracts/tools.md`
- [X] T010 [P] `.specify/templates/plan-template.md` "Tool catalog check"; `.claude/skills/speckit-converge/SKILL.md` test names

## Phase 4: Tests

- [X] T011 `tests/unit/test_catalog.py`, `test_catalog_guards.py`: names updated + legacy folder read / shadowed / never written, `utensil:` key read
- [X] T012 `tests/unit/_golden.py` `RENAMED_020`; `test_interface_unchanged.py`, `test_thin_layers_014.py`, `_make_golden_014.py`, `test_design_tools_008.py`, `test_retire_excel_017.py` updated
- [X] T013 `tests/unit/test_rename_020.py`: old names absent / new present, 51 tools, leftover scan = 0
- [X] T014 `tests/catalog_check.py` text / folder; run all unit tests; server import 51 tools; `graphify update .`

## Phase 5: Verify + release

- [X] T015 `tests/regression.py` on a board1 COPY → PASS (unchanged reference)
- [X] T016 README, CLAUDE.md, CHANGELOG 2.0.0 (migration table), VERSION 2.0.0, ROADMAP done, tag v2.0.0 (no push)

## Converge (2026-11-09)

- FR-001..007 checked: no gap found. SC-001 test_rename_020 (0 old words), SC-002 51 tools = catalog, SC-003 2026-11-09 board1 copy: tests/regression.py (isim flow) PASS - 24 ports, 101 GND vias, GND planes 845-865 mm2, pin shift 0.21 mm, arc 30 (unchanged). SC-004 349 unit tests PASS.
- Catalog step (test_catalog, test_catalog_guards) PASS. Constitution 2.0.1 (dec9077) carries the plan wording.
