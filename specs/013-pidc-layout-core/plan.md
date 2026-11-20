# Implementation Plan: PI-DC + layout edit on core

**Branch**: `main` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

## Summary

Restructure only. `pi_dc/` and `edit_layout/` drop their own helpers and use `core/`:

1. **PI-DC skill registry** (FR-001, US1/US3):
   - Each module in `pi_dc/skills/` gets `ORDER` (current_density 10, via_current 20, voltage_distribution 30,
     power_tree 40) and optional `NEEDS_EXPORT` (True for the 3 image skills, False for power_tree).
   - `workflow.SKILLS = registry.by_name(registry.load(skills, ("NAME", "ORDER", "TITLE", "run")))`,
     `DEFAULT = [m.NAME for m in entries]`, `NEEDS_EXPORT = {m.NAME for m in entries if m.NEEDS_EXPORT}`.
     Same dict keys, order and set as today (golden).
   - `skills/__init__.py` docstring: "new skill = one module + guide" (no table edit).
2. **PI-DC template** (FR-002): `common.TEMPLATE = Path(config.template_path("pidc"))` (same file).
3. **Units** (FR-004): `via_current.load_vias` `ro * 1e-3` → `ro * MM` (`core.units.MM`, bit-identical);
   `edit_layout/extract.py`, `ops.py`: `MM = 1e-3` → `from ..core.units import MM`. `* 1e3` and `/ 1000` (µm) stay.
4. **EDB session** (FR-003): `edit_layout/run.py` `_aedb` → `core.edb.aedb_path`; `_open` → `core.edb.open_edb`
   / `edb_session(path, cell or None, readonly, config.machine()["aedt_version"])`. Same path rules, same version,
   same modes; `region` and the two opens in `edit` use `edb_session` (close guaranteed as today's try/finally).
5. **Validation at entry** (FR-005, Principle VII), error path only:
   - `workflow.run_skill`: `name` must be a skill name (`require_choice`), `folder` existing dir (`require_path`).
   - `workflow.run`: `folder` existing dir; `skills` names valid (before export starts).
   - `run.region`: `board` via `aedb_path`; `bbox` 4 finite numbers (str "x0,y0,x1,y1" or list), x0 < x1, y0 < y1.
   - `run.edit`: plan dict / JSON / file; `board` via `aedb_path`; `ops` non-empty list; every op name in `OPS`
     (checked BEFORE the copy — today it is checked after copying); `region` when given = 4 numbers.
6. **Tests** (FR-007): `tests/unit/_make_golden_013.py` captures from pre-013 code → `tests/unit/golden/pre013.json`:
   SKILLS keys / order / TITLE, DEFAULT, NEEDS_EXPORT, `common.params()`, `run.defaults()`, `_aedb()` results for
   path forms (`.aedb`, `.aedt`, `edb.def`, quoted, trailing spaces) on a temp folder, `extract.MM`, `ops.MM`.
   `tests/unit/test_pidc_layout_core_013.py` compares new code with the golden + validation tests + import rule
   (no local `MM =`, no `_aedb`, no `aedt_env.open_edb` import in `edit_layout/`).
7. **Identity runs** (SC-001/002): PI-DC 3 skills on two copies of the sample (pre-013 vs 013) → diff
   `results/*.json` ignoring `seconds` / paths; `tests/pidc_check.py` both. `tests/layout_edit_b04.py all` pre vs
   post → diff op results / checks / summary / changes. `tests/regression.py` on a board1 copy.

## Kitchen check

| Item | Answer |
|---|---|
| Utensils added | none |
| Process tools added | none |
| Tool names / inputs / outputs | unchanged (`pidc_*`, `layout_region`, `layout_edit`); error text for invalid input becomes `CopilotInputError` |
| Safety / gate | unchanged (layout edit writes a copy; PI-DC in place, never saves) |
| Catalog + contract | no catalog change; changed functions in `contracts/pi_dc.md`, `contracts/edit_layout.md` |
| Registration | n/a (server untouched) |
| Recipes affected | none |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| Changed code | `pi_dc/{workflow,common}.py`, `pi_dc/skills/*.py` (ORDER / NEEDS_EXPORT, MM), `edit_layout/{run,extract,ops}.py` |
| Unchanged | `core/` (no new function needed), `mcp_server/server.py`, `__main__.py`, templates, guides, prompts |
| Tests | offline golden (pre013.json) + validation; AEDT/files: PI-DC identity on copies, `layout_edit_b04.py`, `regression.py` |
| Not re-run | `power_tree` skill (launches SIwave on the desktop) — covered offline by registry test |

## Constitution Check (1.2.0)

| Principle | Check | Status |
|---|---|---|
| I Gates | untouched | PASS |
| II Data safety | PI-DC identity on copies; layout edit always on a copy | PASS |
| III Defaults | templates unchanged, read via core | PASS |
| IV Guides | no usage rule change → guides unchanged | PASS |
| V Regression | regression + pidc_check + layout_edit_b04 before release | PASS |
| VII Contracts | contracts for changed public functions + validation at entry | PASS |
| VIII Package by function | duplicates removed; core imports no feature (test kept) | PASS |
| IX Stable interface | results identical; tool names / IO unchanged | PASS |
| X Kitchen | see Kitchen check | PASS |

## Project Structure

```
specs/013-pidc-layout-core/{spec,plan,tasks}.md, contracts/{pi_dc,edit_layout}.md
aedt_copilot/pi_dc/workflow.py, common.py, skills/{current_density,via_current,voltage_distribution,power_tree}.py
aedt_copilot/edit_layout/run.py, extract.py, ops.py
tests/unit/_make_golden_013.py, golden/pre013.json, test_pidc_layout_core_013.py
```
