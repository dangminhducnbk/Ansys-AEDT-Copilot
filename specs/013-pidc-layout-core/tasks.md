# Tasks: PI-DC + layout edit on core (013)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/](contracts/)

## Phase 1: Setup (baseline from pre-013 code)

- [X] T001 Baseline runs with pre-013 code: PI-DC 3 skills (`pidc --skip-export --skills current_density,via_current,voltage_distribution`) on scratch copy `pidc013/before` of the BOARDB_B04 VCC_0P8V sample + `tests/pidc_check.py`; `tests/layout_edit_b04.py all` (log `le_before.log`)
- [X] T002 `tests/unit/_make_golden_013.py` → `tests/unit/golden/pre013.json` from pre-013 code: SKILLS keys / TITLE, DEFAULT, NEEDS_EXPORT, `common.params()`, `edit_layout.run.defaults()`, `run._aedb()` on path forms of a temp `.aedb`, `extract.MM`, `ops.MM`

## Phase 2: User Story 1 + 3 - PI-DC on core (P1 / P2)

- [X] T003 [US1] Tests in `tests/unit/test_pidc_layout_core_013.py`: SKILLS / DEFAULT / NEEDS_EXPORT / TITLE / params equal golden; skills loaded by `core.registry`; `run_skill` unknown name and missing folder → `CopilotInputError`; `run` bad skills → `CopilotInputError` before export
- [X] T004 [US3] `aedt_copilot/pi_dc/skills/*.py`: `ORDER` (10/20/30/40), `NEEDS_EXPORT` (power_tree False); `skills/__init__.py` docstring
- [X] T005 [US1] `aedt_copilot/pi_dc/workflow.py`: SKILLS / DEFAULT / NEEDS_EXPORT from `core.registry`; validation in `run_skill` / `run`
- [X] T006 [US1] `aedt_copilot/pi_dc/common.py` TEMPLATE via `config.template_path("pidc")`; `skills/via_current.py` `ro * MM`

## Phase 3: User Story 2 - Layout edit on core (P1)

- [X] T007 [US2] Tests in `tests/unit/test_pidc_layout_core_013.py`: `aedb_path` equals golden `_aedb` for all path forms; defaults / MM equal golden; region bad board / bbox → `CopilotInputError` before EDB; edit bad plan / ops / unknown op → `CopilotInputError` before copy (no out_dir created); no local `MM =`, `_aedb`, `_open`, `aedt_env` import left in `edit_layout/`
- [X] T008 [US2] `aedt_copilot/edit_layout/run.py`: `core.edb.aedb_path` + `edb_session`; validation of board / bbox / plan / ops / region at entry
- [X] T009 [US2] `aedt_copilot/edit_layout/extract.py`, `ops.py`: `from ..core.units import MM`

## Phase 4: Polish

- [X] T010 Unit tests all PASS; `graphify update .`
- [X] T011 Identity: PI-DC 3 skills on copy `pidc013/after` with 013 code → diff `results/*.json` vs before (ignore seconds / paths) = 0; `tests/pidc_check.py` PASS; `tests/layout_edit_b04.py all` → diff vs `le_before.log` (ops, checks, summary) = 0; `tests/regression.py` on a board1 copy PASS
- [X] T012 VERSION 0.13.1, CHANGELOG, CLAUDE.md status row, ROADMAP 013 done; commit + local tag v0.13.1

## Dependencies

T001, T002 before any code change. T003 → T004..T006; T007 → T008..T009; US1 and US2 independent. T010..T012 last.
