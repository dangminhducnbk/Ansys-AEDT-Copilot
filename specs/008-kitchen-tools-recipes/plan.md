# Implementation Plan: Kitchen model — utensils + recipes

**Branch**: `main` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

## Summary

Three parts, all additions (Principle IX):

1. **Utensil catalog** — `aedt_copilot/kitchen/catalog.py`: one entry per MCP tool (name, group, one-line summary,
   inputs, outputs, safety level `read | copy | original | workspace | remote`, gate flag, `standalone` vs
   `process`). Served by MCP `kitchen_utensils()`. A unit test keeps catalog and server in sync (every tool listed,
   every listed tool exists, every `original / workspace / remote` utensil has its gate flag in the server signature).
2. **Missing utensils (FR-005)** — new registry entries in the 007 `design_tools` runner (copy by default, backup,
   read-back, report) and 4 new MCP tools:
   `design_trace` (read), `design_cutout` (new cut `.aedb` from a board), `design_cleanup` (GND cleanup on a design),
   `design_end_check` (read), `design_check` (read: self-check of ports / setup / sweep / airbox vs values),
   `design_merge` (designs into a workspace — gate `user_approved_merge`). Existing standalone tools are catalogued as
   utensils as they are: `inspect_board`, `review_layout`, `layout_region`, `layout_edit`, `pidc_*`, `design_*` (007).
3. **Recipe catalog + format** — Markdown files with YAML front matter; team recipes in `recipes/` (repo), personal
   recipes in `%USERPROFILE%\.aedt_copilot\recipes\` (env `AEDT_COPILOT_RECIPES`); MCP `kitchen_recipes()`,
   `get_recipe(name, source)`, `save_recipe(name, markdown, overwrite)` (personal folder only). Team recipes ship for
   every existing process (listed as they are, pointing to their guide) + one new example recipe built only from
   utensils. Guide `kitchen` + INSTRUCTIONS / `about()` lines.

Rebuilding the old processes on the utensils (FR-007) is NOT in this feature (FR-012). Version 0.11.0.

## Technical Context

| Item | Value |
|---|---|
| Language / runtime | Python 3.12, pyedb 0.85 (.NET), pyaedt 1.9.0, PyYAML (already a dependency), mcp<2 |
| New code | `aedt_copilot/kitchen/{__init__,catalog,recipes}.py`; `aedt_copilot/design_tools/{trace,cutout,cleanup,end_check,check}.py`; `aedt_copilot/design_tools/merge.py` (not a registry entry: different target = workspace) |
| Changed code | `mcp_server/server.py` (+4 design tools, +4 kitchen tools, INSTRUCTIONS / about), `__main__.py` (`kitchen` sub-command), guides / prompts, `recipes/` (new folder) |
| Reused | `cutter.channel_sets` / `cut_stage` / `cleanup_gnd` / `collect_metrics`; `interface_sim.ends._measure` / `classify_unusual` / `thresholds`; `interface_sim.apply.read_setup` / `setup_mismatches` / `read_airbox` / `airbox_mismatches`; `inspect_board.trace_channel` / `end_type`; `cut_board.merge.merge_designs`; `interface_sim.cut.copy_source` |
| Tests | offline `tests/unit/test_kitchen.py`, `tests/unit/test_design_tools_008.py`; AEDT: `tests/kitchen_check.py` on board1 copies (user OK first) |
| Performance | catalog / recipes: file reads only (< 0.1 s); cutout ≈ today's cut stage 1 (~5 min board1) |

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I Gates in code | gates locked on the utensil by safety level (catalog), enforced in the server for `original / workspace / remote`; test checks every such utensil has its flag | PASS |
| II Data safety | copy by default (007 runner), cutout works on a copy of the board, merge backs up the workspace (existing `merge_designs`); `save_recipe` never overwrites unless `overwrite=true`, personal folder only | PASS |
| III Single source of defaults | utensils use `templates/*.csv`; recipes may pass values, never hold defaults | PASS |
| IV Rules in guides | `guides/kitchen.md`; recipes are guide-like files; every new rule there | PASS |
| V Regression | no existing code path changed; `tests/regression.py`, `tests/isim_check.py`, `tests/pidc_check.py` unchanged; new `tests/kitchen_check.py` | PASS |
| VI Encoding | recipe files read / written UTF-8 by Python | PASS |
| VII Contracts | `contracts/` for catalog, recipes, each new utensil, MCP tools; CopilotInputError before any file change | PASS |
| VIII Package by function | `kitchen/` (catalogs), new utensils in `design_tools/` registry; MCP thin | PASS |
| IX Stable interface | additions only; existing tools / formats / folders unchanged | PASS |

Post-design re-check: PASS.

## Design

### Safety levels (catalog)

| Level | Meaning | Gate |
|---|---|---|
| `read` | reads only | none |
| `copy` | writes a NEW file / folder (copy, new cut, report) | none |
| `original` | writes the given design / board in place (after backup) | flag (`user_approved_in_place`, ...) |
| `workspace` | writes the engineer's workspace project (merge) | flag (`user_approved_merge`, ...) |
| `remote` | runs on a remote server | flag (`user_requested_run`) |

A utensil that can do both (e.g. `design_*` copy / in place) is listed with its highest level and the condition.
Process tools (`isim_*`, `propose_channels`, `start_cut_batch` ...) are listed with `kind: process` and their process
gate; they keep working unchanged.

### New utensils (design_tools registry, 007 runner)

| Tool | Level | Inputs | Output |
|---|---|---|---|
| `design_trace(board, refdes, nets="", cell="")` | read | 2 refdes (+ net patterns) | nets, diff groups, series parts, end types, pins (JSON) |
| `design_cutout(board, refdes, nets, series="", cell="", values="")` | copy | 2 end refdes, nets (patterns), series refdes, `cutout.*` | `<board dir>/Ansys AEDT Copilot/kitchen/<name>_cutout_<time>/<name>.aedb` + `stage1.json` (source board copied once, reused by size + mtime) |
| `design_cleanup(board, ends, nets="", values="", cell="", in_place, user_approved_in_place)` | copy / original | design `.aedb`, end refdes, signal nets (default from `stage1.json` next to it or all non-reference nets of the ends), `cleanup.*` | cleaned copy + report (GND pieces / vias / pins removed per layer) |
| `design_end_check(board, refdes, nets="", cell="")` | read | refdes list, nets | per end: type, pins, GND near, pads, solder ball, via-in-pad, unusual + options |
| `design_check(board, ends, nets="", values="", cell="")` | read | ends, nets, expected `setup.* / sweep.* / airbox.*` | mismatches: ports vs signal pins, setup / sweep / arc / airbox read-back |
| `design_merge(workspace, designs, port=0, user_approved_merge=False)` | workspace | `.aedt`, `{name: .aedb}` or comma list of `.aedb` | new designs in the workspace (`_v2` on clash), backup path, compare (existing `merge_designs`) |

### Recipe format (`recipes/<name>.md`)

```markdown
---
name: cut-sweep-merge            # slug, unique per source
title: Cut, set sweep, merge
description: one line shown in the recipe list
inputs: [board .aedb, end refdes, nets, sweep start/stop/step, workspace .aedt]
guide: ""                        # optional: legacy process guide followed instead of steps
steps:
  - utensil: design_trace
  - utensil: design_cutout
    checkpoint: true             # stop for the engineer's explicit go before this step
  - utensil: design_sweep
  - utensil: design_merge
    checkpoint: true
---
Free text for the agent: why, choices, what to report.
```

Validation (`recipes.parse`): front matter YAML; `name` slug `[a-z0-9-]+`; `steps` list of `{utensil, note?, checkpoint?}`
(or empty when `guide` is set); unknown utensil → recipe listed as `broken` with the names (never fails the list).

### Recipe sources

| Source | Folder | Who | Listed as |
|---|---|---|---|
| team | `<repo>/recipes/*.md` | repo owner (git) | `team` |
| personal | `%USERPROFILE%\.aedt_copilot\recipes\*.md` (env `AEDT_COPILOT_RECIPES`) | each engineer | `personal` |

Same name in both → two entries (`team`, `personal`), `get_recipe(name)` without source → refuse listing both
(CopilotInputError `source`); never a silent override. `save_recipe` writes the personal folder only, validates
first, refuses an existing name unless `overwrite=true`.

### Team recipes shipped

`excel-cut` (guide workflow), `interface-sim` (guide interface_sim), `re-cut` (interface_sim Phase R),
`re-apply` (interface_sim step 8), `pidc-report` (guide pidc_workflow), `layout-edit` (guide layout_edit),
`design-tools` (guide design_tools), and the new `cut-sweep-merge` (utensils only, no guide) for SC-003.

## Project Structure

```
specs/008-kitchen-tools-recipes/ plan.md research.md data-model.md quickstart.md
  contracts/{kitchen-catalog.md,recipes.md,utensils-008.md,mcp-tools.md} tasks.md
aedt_copilot/kitchen/{__init__,catalog,recipes}.py              NEW
aedt_copilot/design_tools/{trace,cutout,cleanup,end_check,check,merge}.py   NEW
aedt_copilot/__main__.py           + kitchen
mcp_server/server.py               + design_trace, design_cutout, design_cleanup, design_end_check, design_check,
                                     design_merge, kitchen_utensils, kitchen_recipes, get_recipe, save_recipe
recipes/*.md                       NEW (8 team recipes)
guides/kitchen.md, prompts/kitchen.md   NEW
tests/unit/test_kitchen.py, tests/unit/test_design_tools_008.py, tests/kitchen_check.py   NEW
VERSION 0.11.0, CHANGELOG.md, README.md, CLAUDE.md
```

## Complexity Tracking

| Deviation | Why | Simpler alternative rejected |
|---|---|---|
| Catalog written in Python next to the server, kept in sync by a test | one source per tool fact; the test fails when a tool is added without its catalog entry | catalog from docstrings (no safety / io fields) |
| `design_merge` outside the registry runner | target is a workspace project, not an `.aedb` copy | forcing the copy runner on a workspace would copy a multi-GB project |
