# Implementation Plan: Kitchen guards — lock Principle X in code

**Branch**: `main` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

## Summary

Locks only; no tool name, input, output or result changes (FR-007, Principle IX).

1. **Shared registration path** (FR-001/002) — `aedt_copilot/kitchen/registration.py`: `make_tool(mcp)` returns the
   decorator `tool()` used for EVERY server tool instead of `@mcp.tool()`. At registration it checks the catalog
   (`problems(name, params)`): entry exists, safety + kind valid, gated level (`original / workspace / remote`) has a
   gate that is a parameter of the function, contract reference set. Any problem → `KitchenRegistrationError`
   (server import fails = server refuses to start) naming the tool and what is missing. `tool.registered` keeps the
   names; FastMCP gets the same function (same name / schema).
2. **Catalog contract reference** (FR-005) — `catalog.CONTRACTS {tool: specs/<feature>/contracts/<file>.md}` attached as
   field `contract`. 19 tools without a contract today get one in `specs/010-kitchen-guards/contracts/legacy-tools.md`
   (inputs, validation, output, safety — documenting current behaviour only).
3. **Process tools only in their process** (US3-3) — `catalog.PROCESS_GUIDES {excel-cut: workflow, interface-sim:
   interface_sim}`; `recipes.parse` adds `misplaced` (process step in a recipe whose `guide` is not that process's guide);
   `list_md` status `misplaced: ...`; personal recipes only marked (not a test failure).
4. **Offline lock tests** (FR-003/004) — `tests/unit/test_kitchen_guards.py`:
   - registration: a dummy FastMCP + dummy tools: missing entry / gated without flag / unknown → refused with name;
     complete → registered;
   - server: every `@...tool` function goes through `tool()` (AST: no `@mcp.tool` left); `tool.registered` == catalog;
   - contracts: every entry's `contract` file exists and contains `` `name` ``;
   - gates: for EVERY catalog entry with a gated safety level, call the server function with the flag false, other
     inputs dummies from the signature, the entry `condition` applied (e.g. `in_place=true`); `_cli` patched to fail;
     refusal must name the gate; temp folder and `.tasks/` unchanged. New gated tools are covered with no test edit;
   - recipes: every team recipe: 0 broken, 0 misplaced.
5. **Gate first** — `merge_to_project` checks `user_approved_verify` before the job checks (today the job checks run
   first, so the refusal without flag named the job, not the gate). Same refusal set, order only; every other gated
   tool already checks its flag first.
6. **Spec Kit** (FR-006) — `.specify/templates/plan-template.md`: section "Kitchen check" (utensils added / changed,
   safety, gate, contract, recipes affected, "no new fixed-process tool" or justification). `speckit-converge` skill:
   step "run `python -m unittest tests.unit.test_kitchen tests.unit.test_kitchen_guards`; each failure → a task".
7. **Guide** (FR-008) — `guides/kitchen.md`: never call or propose an unregistered operation or ad-hoc script; a
   missing utensil is reported and added through Spec Kit.
8. **ROADMAP rev 8** — 009 setup defaults (done 0.11.1), 010 kitchen guards; review layout 011, coded rules 012, PI-DC
   on core 013, thin layers 014, multi-board 015. Version 0.11.2.

## Kitchen check

| Item | Answer |
|---|---|
| Utensils added / changed | none (registration + checks only); catalog entries gain `contract` |
| Safety levels / gates | unchanged; `merge_to_project` checks its gate first |
| Contracts | 19 existing tools documented in `contracts/legacy-tools.md`; new `contracts/registration.md` |
| Recipes affected | none change; `misplaced` check added (team recipes all pass) |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| Language / runtime | Python 3.12, mcp<2 FastMCP |
| New code | `aedt_copilot/kitchen/registration.py`; `tests/unit/test_kitchen_guards.py` |
| Changed code | `mcp_server/server.py` (decorator only + merge_to_project gate order), `kitchen/catalog.py` (CONTRACTS, PROCESS_GUIDES), `kitchen/recipes.py` (misplaced), `tests/unit/_make_golden.py` + `test_kitchen.py` (tool discovery by decorator `tool`), guide, plan template, converge skill |
| Tests | offline unit; AEDT: final `tests/regression.py` on a board1 copy (no reference change) |

## Constitution Check (1.2.0)

| Principle | Check | Status |
|---|---|---|
| I Gates in code | gates proven by tests for every gated utensil | PASS |
| II Data safety | gate test asserts no file written | PASS |
| III Defaults | untouched | PASS |
| IV Rules in guides | kitchen guide rule (FR-008) | PASS |
| V Regression | regression on board1 copy, no reference change | PASS |
| VI Encoding | UTF-8 edits | PASS |
| VII Contracts | every catalog entry has a contract (test) | PASS |
| VIII Package by function | registration in `kitchen/` | PASS |
| IX Stable interface | names / inputs / outputs unchanged; golden interface test | PASS |
| X Kitchen | this feature implements its code locks | PASS |
