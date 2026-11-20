---
description: "Tasks for feature 010 kitchen guards - lock Principle X in code"
---

# Tasks: Kitchen guards

**Input**: `specs/010-kitchen-guards/` (plan.md, spec.md, contracts/, quickstart.md)

**Tests**: REQUIRED: offline first; only AEDT run = final `tests/regression.py` on a board1 COPY (T012).

**Rules**: no tool name / input / output change (stop and ask if one would be needed). UTF-8 edits. Commit after
each phase. No push.

## Phase 1: Foundational — catalog + registration

- [X] T001 `aedt_copilot/kitchen/catalog.py`: `CONTRACTS` (every tool → contract file), field `contract` on every
  entry, `PROCESS_GUIDES`
- [X] T002 `aedt_copilot/kitchen/registration.py` per `contracts/registration.md` (`KitchenRegistrationError`,
  `problems`, `make_tool`)
- [X] T003 `mcp_server/server.py`: `tool = make_tool(mcp)`; every `@mcp.tool()` → `@tool()`; nothing else changes
  except T004

## Phase 2: User Story 1 + 2 — hard locks (P1)

- [X] T004 [US2] `merge_to_project`: check `user_approved_verify` before the job checks
- [X] T005 [US1] Tool discovery in `tests/unit/_make_golden.py` and `tests/unit/test_kitchen.py`: decorator `tool()`
  (and legacy `mcp.tool`) → same tool list; golden interface test PASS
- [X] T006 [P] [US1] [US2] `tests/unit/test_kitchen_guards.py`: registration refusals (missing entry, gated without
  flag, flag not a parameter, no contract) on a dummy FastMCP; server source has no `@mcp.tool`; `tool.registered` ==
  catalog; every gated entry refuses with flag false naming the gate, `_cli` never called, no file written in temp /
  `.tasks/`

## Phase 3: User Story 3 — contracts + recipes (P2)

- [X] T007 [US3] `recipes.parse` `misplaced` + `list_md` status
- [X] T008 [P] [US3] Tests: every `contract` file exists and names the tool in backticks; team recipes 0 broken /
  0 misplaced; a test recipe using `isim_cut` with guide `workflow` → misplaced; personal recipe only marked

## Phase 4: User Story 4 — Spec Kit + guide (P2)

- [X] T009 [US4] `.specify/templates/plan-template.md`: "Kitchen check" section; `.claude/skills/speckit-converge/
  SKILL.md`: catalog test step (failures → tasks)
- [X] T010 `guides/kitchen.md` FR-008 rule; README / CLAUDE.md §3 + §8 (new tool = `@tool()` + catalog entry +
  contract)
- [X] T011 VERSION 0.11.2, CHANGELOG; full unit suite + `graphify update .`; commit

## Phase 5: Final regression (board1 COPY)

- [X] T012 Server import check (quickstart §2); `tests/regression.py` on a fresh board1 copy (Excel flow), reference
  unchanged; tag `v0.11.2` locally; converge

## Dependencies

T001 → T002 → T003 → T004-T006; T007 → T008; T009-T011 after T008; T012 last.
