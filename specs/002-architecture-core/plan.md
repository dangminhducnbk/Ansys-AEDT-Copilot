# Implementation Plan: Architecture + core/

**Branch**: `002-architecture-core` (work on `main`) | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: `specs/002-architecture-core/spec.md`, user decisions 2026-11-04 (see `specs/ROADMAP.md`)

## Summary

Create `aedt_copilot/core/` (errors, validate, config/template, edb session, geometry, units, registry) by MOVING
existing logic (no behaviour change), make old modules thin re-exports, point `aedt_env`, `pi_dc` and
`edit_layout` at core (removes the cross-feature imports of `cut_board.config`), define the contract format
(`specs/CONTRACTS.md`) and registry pattern used by 003-014, add offline unit tests with golden outputs captured
from the code BEFORE the move. Release 0.5.1 after cut regression + PI-DC check PASS identical.

## Technical Context

**Language/Version**: Python 3.12 (repo `.venv`)

**Primary Dependencies**: pyedb 0.85 (.NET), pyaedt 1.9.0, PyYAML, mcp<2 — unchanged; no new dependency

**Storage**: files — `templates/*.csv`, `config.yaml`, golden JSON in `tests/unit/golden/`

**Testing**: stdlib `unittest` (`python -m unittest discover -s tests/unit`), offline; AEDT: `tests/regression.py`,
`tests/pidc_check.py` (pytest not installed — not added)

**Target Platform**: Windows, AEDT 2026 R1 (2025 R2 fallback)

**Project Type**: Python package + CLI + MCP server (stdio)

**Performance Goals**: no slowdown of cut / review (geometry hot path unchanged); unit suite < 30 s

**Constraints**: Principle IX (identical results, no interface change); UTF-8 writes only (no PowerShell
Set-Content); `core/` imports no feature package; guard hook — code edits only after tasks.md

**Scale/Scope**: 7 new core modules (~400 lines moved/added), 6 modules re-pointed, ~8 unit test files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I Gates locked in code | server gates untouched | PASS |
| II User data safety | EDB session read-only by default; no file deleted; tests write only to temp dirs | PASS |
| III Single source of defaults | one template reader in core, reads `templates/*.csv` only | PASS |
| IV Usage rules in guides | no usage rule changes (internal) → no guide edit | PASS |
| V Regression before release | regression + pidc_check before 0.5.1; VERSION, CHANGELOG, tag | PASS |
| VI Windows & encoding | files written UTF-8 via editor tools; CSV read `utf-8-sig` as today | PASS |
| VII Contracts & validation | contracts/ for every core public function; `CopilotInputError`; unit tests | PASS with 1 justified deviation (geometry hot path, see Complexity Tracking) |
| VIII Package by function | `core/` created, no feature imports (automated test) | PASS |
| IX Stable interface | old paths re-export; tools/guides/prompts/templates/folders unchanged | PASS |

Post-design re-check (after Phase 1): unchanged, PASS.

## Design

| Item | Decision |
|---|---|
| Location | `aedt_copilot/core/{__init__,errors,validate,config,edb,geometry,geometry_edb,units,registry}.py` |
| aedt_env | stays at `aedt_copilot/aedt_env.py` (public path); `_machine()` imports `core.config` (not `cut_board.config`). Core layer. |
| config | `core.config`: `ROOT`, `TEMPLATES_DIR`, `CONFIG_FILE`, `template_path(name)`, `machine()`, `template_rows(path)` (header-name based, mtime cache per path), `coerce(value, typ)` — copied verbatim from `cut_board/config.py` |
| cut_board.config | keeps `TEMPLATE_FILE`, `build_params`, `defaults` (cut-only: sweep rule); `template_rows()` = `core.config.template_rows(TEMPLATE_FILE)`; re-exports `ROOT`, `CONFIG_FILE`, `machine`, `coerce` |
| pi_dc.common.params | uses `core.config.template_rows` + `coerce` (same key strip `pidc.`) |
| edit_layout.run.defaults | uses `core.config.template_rows` → `float(row["default"])`; `TEMPLATE` from `core.config.template_path("layout_edit")` |
| pi_dc export / power_tree | `machine()` from `core.config` |
| errors | `CopilotInputError(ValueError)(name, expected, got)`; `RegistryError(RuntimeError)` |
| validate | `require_type`, `require_number`, `require_int`, `require_choice`, `require_text`, `require_path` → return the cleaned value |
| edb | `aedb_path(board)` (pure, logic of `edit_layout.run._aedb`), `open_edb(board, cell, readonly=True, version=None)`, `edb_session(...)` context manager → `aedt_env.open_edb`; existing callers NOT migrated in 002 (005-009 do it) |
| geometry | pure functions moved verbatim; `prim_points` → `core/geometry_edb.py` (touches EDB objects); `cut_board/geometry.py` re-exports all |
| units | `MM = 1e-3`, `MM2 = 1e-6`, `m_to_mm`, `mm_to_m`, `m2_to_mm2`, `mm2_to_m2`, `edb_length(m, digits=4)` = `f"{round(m / MM, digits):g}mm"` (cutter.py solder-ball format). Callers migrate in later features. |
| registry | `load(package, required=("NAME","ORDER","run"))` → list of modules sorted by `(ORDER, NAME)`; `by_name(entries)`; auto-discovers `pkgutil.iter_modules`, skips `_*`; first user is 003 |
| Contract format | `specs/CONTRACTS.md` (cross-feature); this feature's contracts in `contracts/core-*.md` |
| Golden tests | Task order: capture golden JSON from CURRENT code first (template rows ×3, pidc params, layout-edit defaults, coerce table, geometry cases), then move code, then tests compare |
| Version | 0.5.1 (patch), CHANGELOG: "internal restructure, no setup.bat rerun" |

## Project Structure

### Documentation (this feature)

```text
specs/002-architecture-core/
├── spec.md  plan.md  research.md  data-model.md  quickstart.md  tasks.md
├── checklists/requirements.md
└── contracts/  core-errors.md core-validate.md core-config.md core-edb.md core-geometry.md core-units.md core-registry.md
specs/ROADMAP.md      features 002-014 + target layout
specs/CONTRACTS.md    contract format for all features
```

### Source Code (repository root)

```text
aedt_copilot/
├── aedt_env.py                 changed: _machine() → core.config
├── core/                       NEW
│   ├── __init__.py  errors.py  validate.py  config.py  edb.py
│   ├── geometry.py  geometry_edb.py  units.py  registry.py
├── cut_board/config.py         changed: re-export core + cut-only build_params/defaults
├── cut_board/geometry.py       changed: re-export core.geometry + core.geometry_edb.prim_points
├── pi_dc/common.py             changed: params() via core.config
├── pi_dc/export.py, pi_dc/skills/power_tree.py   changed: machine() via core.config
└── edit_layout/run.py          changed: defaults()/TEMPLATE/machine via core.config
tests/unit/                     NEW: test_core_*.py, golden/*.json, _make_golden.py
VERSION, CHANGELOG.md, CLAUDE.md §3 (layout)
```

**Structure Decision**: single Python package; `core/` is the bottom layer; feature packages above it; CLI / MCP
on top (thin in 010).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| VII: pure geometry functions (`point_seg_dist`, `seg_seg_dist`, `point_in_poly`, `poly_area`, `bbox_of`, `edges`) do not validate inputs per call | Called ~10⁶ times per review / cut (inner loops); inputs always produced by core / EDB readers | Per-call checks slow review by an estimated 2-3×; contract states the precondition and unit tests cover degenerate cases |
| VII: `core.config.coerce` raises plain `ValueError` with today's message (not `CopilotInputError`) for bad cell values | Messages are shown to users by `read_channels` / build_params; Principle IX forbids changing them in a restructure | `CopilotInputError` is a `ValueError` subclass, so a later MAJOR / 004 can switch; only a bad `typ` argument raises `CopilotInputError` now |
