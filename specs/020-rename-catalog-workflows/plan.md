# Implementation Plan: Remove the "kitchen" metaphor from all names

**Branch**: `main` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Pure rename per the approved table (spec.md), no behaviour change: package `kitchen` → `catalog`, kind `utensil` →
`tool`, recipe → workflow, 4 MCP tools, CLI `kitchen` → `catalog`, guide / prompt `kitchen` → `catalog`, repo
`recipes/` → `workflows/`, personal folder + env var (old ones still read). Contracts for renamed tools move to this
feature's `contracts/`. Goldens record old → new. MAJOR 2.0.0.

### 1. Rename map (code)

| Old | New |
|---|---|
| `aedt_copilot/kitchen/` (`__init__`, `api`, `catalog`, `recipes`, `registration`) | `aedt_copilot/catalog/` (`__init__`, `api`, `tools` (was catalog.py), `workflows`, `registration`) |
| `catalog.UTENSILS`, `utensils()`, `KINDS = ("utensil", "process")`, group `kitchen` | `tools.TOOLS`, `tools()`, `KINDS = ("tool", "process")`, group `catalog` |
| `catalog_md` header `Utensil` | `Tool` |
| `recipes.list_recipes`, `get`, `save`, `list_md` header `Recipe`, step key `utensil` | `workflows.list_workflows`, `get`, `save`, header `Workflow`, step key `tool` (old key `utensil` read) |
| `recipes.team_dir()` = `recipes/`; `personal_dir()` env `AEDT_COPILOT_RECIPES` / `~/.aedt_copilot/recipes` | `workflows/`; env `AEDT_COPILOT_WORKFLOWS` / `~/.aedt_copilot/workflows`; `legacy_dirs()` = env `AEDT_COPILOT_RECIPES` / `~/.aedt_copilot/recipes` (read only) |
| `registration.KitchenRegistrationError`, message `kitchen: tool ...` | `CatalogRegistrationError`, `catalog: tool ... add it to aedt_copilot/catalog/tools.py (Principle X)` |
| `api` ops `utensils`, `recipes`, `get`, `save`; keys `utensils`, `recipes` | ops `tools`, `workflows`, `get`, `save`; keys `tools`, `workflows` |
| MCP `kitchen_utensils`, `kitchen_recipes`, `get_recipe`, `save_recipe`; helper `_kitchen` | `list_tools`, `list_workflows`, `get_workflow`, `save_workflow`; `_catalog` |
| CLI `kitchen --op=<utensils\|recipes\|get\|save>` | `catalog --op=<tools\|workflows\|get\|save>` |
| `design_tools/cutout.py` `KITCHEN`, `kitchen_dir()` → `Ansys AEDT Copilot/kitchen/` | `OUTPUT`, `output_dir()` → `Ansys AEDT Copilot/design_tools/` (A1) |
| `design_tools/merge.py` out_dir `.../kitchen/merge_<time>` | `.../design_tools/merge_<time>` |
| guides `kitchen.md`; prompts `kitchen.md`; repo `recipes/*.md` | `catalog.md`; `catalog.md`; `workflows/*.md` (`utensil:` → `tool:`) |
| tests `test_kitchen.py`, `test_kitchen_guards.py`, `tests/kitchen_check.py` | `test_catalog.py`, `test_catalog_guards.py`, `tests/catalog_check.py` |

Personal folders (FR-002): `list_workflows` reads new personal folder, then each legacy folder; a legacy entry whose
name exists in the new folder gets `shadowed: true` (status `shadowed (newer copy in <new folder>)`) and `get` never
returns it; `save` writes only the new folder.

### 2. Text

Server INSTRUCTIONS ("TOOL CATALOG: every tool has a safety level + gate; every process is a workflow (team or
personal)... list_workflows + list_tools first; get_guide('catalog')"), tool docstrings (`DỤNG CỤ` → `TOOL`,
`NHÀ BẾP` → `DANH MỤC`), `about()` (cli/docs.py), CLI help (parser.py), guides `catalog`, `design_tools`,
`layout_edit`, `interface_sim` (if any), prompts `catalog`, `copilot-help`, README, CLAUDE.md, CHANGELOG 2.0.0,
`.specify/templates/plan-template.md` ("Tool catalog check"), `.claude/skills/speckit-converge/SKILL.md` (test names).
`interface_sim/settings.py` / `design_tools/end_check.py` wording "utensil" → "tool".

### 3. Contracts (`contracts/`)

- `catalog.md`: modules `catalog.tools`, `catalog.workflows`, `catalog.registration`, `catalog.api`; MCP
  `list_tools`, `list_workflows`, `get_workflow`, `save_workflow`; CLI `catalog`. (Rewritten from 008
  kitchen-catalog / recipes / mcp-tools and 010 registration; same rules.)
- `tools.md`: contracts carried from `specs/008-*/contracts/utensils-008.md` and `specs/010-*/contracts/legacy-tools.md`
  for the tools whose catalog contract pointed there (design_trace / cutout / cleanup / end_check / check / merge,
  about, show_defaults, inspect_board, finish_in_aedt, layout_*, pidc_*), output folder `design_tools/`.
- `tools.CONTRACTS` points those tools here; no catalog contract path contains an old word.

### 4. Tests

- Renamed test modules keep every case (names updated); new cases: legacy personal folder read / shadowed / never
  written; `utensil:` step key read.
- New `tests/unit/test_rename_020.py`: old MCP / CLI / guide / prompt names absent; new present; 51 tools; scan for
  `kitchen|utensil|recipe` (case-insensitive) in server source, `about()`, catalog entries (all fields incl. contract),
  `workflows/*.md`, `guides/*.md`, `prompts/*.md`, CLI help → 0 hits.
- `_golden.py`: `RENAMED_020 = {"kitchen_utensils": "list_tools", ...}` (+ CLI, guide, prompt) and `renamed_020(dump)`;
  `test_interface_unchanged`, `test_thin_layers_014` map old golden names → new before comparing (schemas equal;
  descriptions of the 4 tools + tools whose docstring said DỤNG CỤ / NHÀ BẾP compared by schema only).
- `test_retire_excel_017`: scans `workflows/`; `test_design_tools_008`: output folder `design_tools`.

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | renamed: `kitchen_utensils` → `list_tools`, `kitchen_recipes` → `list_workflows`, `get_recipe` → `get_workflow`, `save_recipe` → `save_workflow`; same inputs / outputs (keys renamed) |
| Catalog entry + contract | 4 entries renamed, group `catalog`; contracts in `specs/020-rename-catalog-workflows/contracts/` |
| Safety / gate | unchanged (read, read, read, copy) |
| Workflows affected | all 8 team files moved `recipes/` → `workflows/`, step key `tool` |
| New fixed-process tool | none |

## Constitution — proposed wording for Principle X (user runs `/speckit-constitution`; Claude does not edit it)

```
### X. Tool Catalog and Workflows

- Every MCP tool MUST be one operation, usable alone on any valid input, registered in the tool
  catalog with inputs, outputs, preconditions, what it writes and its safety level
  (read-only / writes a copy / writes the original / remote).
- A tool MUST be registered through the shared registration helper; the server MUST refuse to start
  if a tool lacks a catalog entry or safety level.
- Tools that write an original file / workspace or run remotely MUST require an explicit approval
  flag checked server-side, whatever workflow calls them.
- A new way of working MUST be a workflow (file in `workflows/` or the personal workflow folder), not a
  new fixed-process tool. A process tool is allowed only as a thin wrapper over catalog tools.
- Offline tests MUST fail when: a tool is missing from the catalog, a catalog entry has no contract,
  a risky tool has no approval flag, or a workflow names a tool that does not exist.
- When a needed tool does not exist, Claude MUST say so and add it through Spec Kit; it MUST NOT
  write an ad-hoc script instead.
```

Development Workflow line (now "`/speckit-plan` MUST include a "Kitchen check": which utensils are added or changed,
their safety level, and which recipes are affected (Principle X).") → "`/speckit-plan` MUST include a "Tool catalog
check": which tools are added or changed, their safety level, and which workflows are affected (Principle X)." Version: wording-only rename of a principle title →
the user decides MINOR (2.1.0) or PATCH.

## Technical Context

| Item | Value |
|---|---|
| Language | Python 3.12 (.venv), no new dependency |
| Moves | `git mv` for package, guides, prompts, `recipes/` → `workflows/`, tests (history kept) |
| AEDT (board1 copy) | `tests/regression.py` PASS (cut path does not use the catalog; run to prove unchanged) |
| Not touched | `specs/008-*`, `specs/010-*` (history), user folders on disk (old `Ansys AEDT Copilot/kitchen/`, `~/.aedt_copilot/recipes`) |

## Constitution Check (2.0.1, Principle X amended by the user with the wording below, dec9077)

| Principle | Check | Status |
|---|---|---|
| I | gates unchanged (same flags, same tools) | PASS |
| II | board copies only; old output folders untouched | PASS |
| IV | user files never deleted (old personal folder read only) | PASS |
| VII | contracts for renamed tools / modules in `contracts/` | PASS |
| IX | names change → MAJOR 2.0.0 + CHANGELOG migration table | PASS |
| X | same rules; wording amended (2.0.1) | PASS |
