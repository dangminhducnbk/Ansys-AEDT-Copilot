# Feature Specification: Remove the "kitchen" metaphor from all names

**Feature Branch**: `020-rename-catalog-workflows` (work stays on `main`)

**Created**: 2026-11-09

**Status**: Done 2.0.0 (no clarify: the user approved the rename table; A1-A6 relayed to the user).

**Input**: Parent session, user go 2026-11-09: "kitchen" was only an analogy to explain how the tool works; it must
not appear in names. Approved rename table below. Breaking (MCP tool names change) → MAJOR 2.0.0.

## Approved rename table (user)

| Old | New |
|---|---|
| kitchen (package `aedt_copilot/kitchen/`, guide `kitchen`, prompt `kitchen`, CLI `kitchen`) | `catalog` |
| utensil (catalog kind, wording everywhere) | tool |
| recipe | workflow |
| MCP `kitchen_utensils` / `kitchen_recipes` | `list_tools` / `list_workflows` |
| MCP `get_recipe` / `save_recipe` | `get_workflow` / `save_workflow` |
| repo `recipes/`, personal `~/.aedt_copilot/recipes` (env `AEDT_COPILOT_RECIPES`) | `workflows/`, `~/.aedt_copilot/workflows` (env `AEDT_COPILOT_WORKFLOWS`); the old personal folder and old env var are still READ, never deleted |
| plan template section "Kitchen check" | "Tool catalog check" |

Also: server instructions ("KITCHEN" text), README, CHANGELOG (migration table old → new), CLAUDE.md, contracts,
tests, golden files. Old spec folders (`specs/008-*`, `specs/010-*`) stay as history. Constitution Principle X
becomes "Tool catalog and workflows" (same rules, new words) — the user runs `/speckit-constitution`; the plan holds
the proposed wording.

## User Scenarios & Testing

### User Story 1 — Engineer sees plain names (P1)

An engineer asks "what can you do?". Claude lists tools with `list_tools` and workflows with `list_workflows`, reads
one with `get_workflow`, reads guide `catalog`. No answer, guide, prompt or tool description uses kitchen / utensil /
recipe.

**Acceptance**:
1. Server has `list_tools`, `list_workflows`, `get_workflow`, `save_workflow`; none of the 4 old names exists.
2. Guide `catalog` and prompt `catalog` exist; guide / prompt `kitchen` do not.
3. Server instructions, `about()`, every guide / prompt / workflow file and every tool description contain none of
   the words kitchen / utensil / recipe (case-insensitive) — except the CHANGELOG migration note.

### User Story 2 — Existing personal recipes keep working (P1)

An engineer saved personal recipes before 2.0.0 in `~/.aedt_copilot/recipes` (or `AEDT_COPILOT_RECIPES`).

**Acceptance**:
1. `list_workflows` lists them as personal workflows; `get_workflow` reads them; their steps written with the old
   key `utensil:` are read as `tool:`.
2. `save_workflow` writes only to the new personal folder (`~/.aedt_copilot/workflows` or `AEDT_COPILOT_WORKFLOWS`);
   nothing in the old folder is changed or deleted.
3. Same name in the old and the new personal folder → the new one is used; the old one is listed as `shadowed`.

### User Story 3 — Results unchanged (P1)

Cut, design tools, interface simulation, PI-DC and layout edit give the same results as 1.0.0.

**Acceptance**: unit tests PASS; server imports with 51 tools; `tests/regression.py` PASS on a board1 copy with the
unchanged reference.

### Edge Cases

- A team workflow names a tool that does not exist → status `broken` (same rule as before).
- A workflow file mixes `utensil:` and `tool:` steps → both read.
- `AEDT_COPILOT_WORKFLOWS` points at the team `workflows/` folder → save refused (same rule as before).
- An old CLI call `kitchen --op=...` → argparse "invalid choice" (exit 2), like any removed command.

## Requirements

- **FR-001**: Rename per the approved table: package, CLI command, MCP tools, guide, prompt, repo folder, personal
  folder + env var, catalog kind `utensil` → `tool`, catalog group `kitchen` → `catalog`, plan template section.
- **FR-002**: Old personal folder / env var are read (never written, never deleted); old step key `utensil` is read.
- **FR-003**: No old name in: server source (names, docstrings, instructions), catalog entries (names, groups, kinds,
  summaries, contract paths), workflow files, guides, prompts, `about()`, CLI help. A unit test proves 0 leftovers.
- **FR-004**: Behaviour unchanged: same tools (51), same gates, same safety levels, same registration guard (server
  refuses an unregistered tool), same workflow checks (`broken`, `misplaced`, `error`).
- **FR-005**: CHANGELOG 2.0.0 has a migration table (old tool / CLI / folder / env name → new).
- **FR-006**: Contracts for the renamed tools and modules live in `specs/020-rename-catalog-workflows/contracts/`;
  catalog entries point there (old spec folders untouched).
- **FR-007**: Goldens record the rename (old name → new name) so interface tests still compare everything else.

## Success Criteria

- **SC-001**: Leftover-name test: 0 hits of kitchen / utensil / recipe in server, catalog, workflows, guides, prompts.
- **SC-002**: 51 tools at server import; catalog = server tools.
- **SC-003**: `tests/regression.py` PASS on a board1 copy (24 ports, 101 GND vias, planes 845–865 mm², shift 0.21 mm).
- **SC-004**: All unit tests PASS.

## Assumptions (decided, reported to the parent session)

- **A1 Output folder**: design tools wrote to `<board dir>/Ansys AEDT Copilot/kitchen/` (cutout, merge, board copy
  `_src`). New results go to `<board dir>/Ansys AEDT Copilot/design_tools/`. Old folders on disk are not touched; the
  first `design_cutout` after the update copies the board once more into `design_tools/_src`.
- **A2 Code names**: `KitchenRegistrationError` → `CatalogRegistrationError`; `UTENSILS` → `TOOLS`; API ops
  `utensils` / `recipes` → `tools` / `workflows`; result keys `utensils` / `recipes` → `tools` / `workflows`; workflow
  step key `utensil` → `tool`.
- **A3 Tests / scripts**: `tests/unit/test_kitchen*.py` → `test_catalog*.py`; `tests/kitchen_check.py` →
  `tests/catalog_check.py`.
- **A4** Vietnamese wording in code comments ("nhà bếp", "dụng cụ", "công thức") → "danh mục", "tool", "workflow".
- **A5** No aliases for old MCP / CLI names (MAJOR release + migration table), same as 1.0.0.
- **A6** `.claude/skills/speckit-converge/SKILL.md` catalog step names the renamed test modules.
