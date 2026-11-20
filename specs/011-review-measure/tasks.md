---
description: "Tasks for feature 011 review layout - code measures, agent interprets"
---

# Tasks: Review measure + interpret

**Input**: `specs/011-review-measure/` (plan.md, spec.md, contracts/, quickstart.md)

**Rules**: `cut_board/review.py`, `review_layout`, HTML and Excel gates stay byte-identical (stop and ask if a tool
name / input would change or a number differs from today's review). Offline first; AEDT only on board1 COPIES.
Commit after each phase. No push.

## Phase 1: Foundational — checks registry

- [X] T001 `aedt_copilot/review_checks/_context.py`: Ctx (edb, Board, R, refs, pt, step) + ChannelCtx lazy: trace,
  collect, window, cu / oc (reference only), stacks, via rows (shared)
- [X] T002 [P] Check modules `reference.py`, `trace_stubs.py`, `vias.py`, `routing.py` (reuse review.py functions)
- [X] T003 `review_checks/__init__.py`: `checks()`, `measure`, `measure_channels` (order / ids / points as
  `review.review()`), per-check error isolation, "no plane layer"; `_report.py` (mm items, points, summary_md)
- [X] T004 [P] Tests `tests/unit/test_review_checks.py`: registry order + names; unknown check → closest; fake context:
  only requested checks run (reference not built for trace_stubs); error isolation; sort / ids / points equal
  `review.points` on sample findings; JSON-safe output; summary_md table

## Phase 2: User Story 1 — utensil (P1)

- [X] T005 [US1] CLI `review-measure`; MCP `design_review` (`@tool()`), catalog entry + contract; html → `review.review()`

## Phase 3: User Story 2 + 3 — interpret, decisions, interface simulation (P1 / P2)

- [X] T006 [US3] `interface_sim/review.py` `run` (agreed content → measure_channels, `review.json`) + `decide`
  (validation, `user_settings` key `review`); `user_settings.SECTION_KEYS` + `review`; `api` ops `review`,
  `review_decide`; MCP `isim_review`, `isim_review_decide`; catalog entries
- [X] T007 [P] [US2] [US3] Tests: decide validation (unknown point, bad decision, severity change without reason),
  saved in user_settings, step check (before content_agreed refused); server tools present; kitchen tests PASS
- [X] T008 [US2] Guide `guides/review_measure.md` (interpretation rules, summary format, decisions); `interface_sim`
  Phase 1.6 optional review; recipes `layout-review` (new), `interface-sim` optional `isim_review` step; INSTRUCTIONS /
  about lines

## Phase 4: Docs, release

- [X] T009 README, CLAUDE.md, CHANGELOG 0.12.0, VERSION, ROADMAP 011 done; unit suite + `graphify update .`; commit

## Phase 5: AEDT check (board1 COPIES)

- [X] T010 `tests/review_check.py` per quickstart §2 (identical numbers vs old review, one-check timing, isim review +
  decide); `tests/regression.py` PASS; tag `v0.12.0`; converge (catalog tests)
