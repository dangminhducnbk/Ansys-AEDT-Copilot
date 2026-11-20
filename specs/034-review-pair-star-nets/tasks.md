---
description: "Tasks for feature 034 - review recognises pairs whose nets end with '*'"
---

# Tasks: Review recognises pairs whose nets end with `*` (034)

**Input**: `specs/034-review-pair-star-nets/` (spec.md, plan.md)

## Phase 1: User Story 1 - Pair checks see every pair (P1)

- [X] T001 [US1] `aedt_copilot/cut_board/naming.py`: `review_groups(names)` = `group_diff` on names without a trailing `*`, mapped back to the original names (one per base name); `group_diff` unchanged
- [X] T002 [US1] Use `naming.review_groups` in `aedt_copilot/review_checks/_context.py` (groups), `aedt_copilot/review_checks/routing.py`, `aedt_copilot/cut_board/review.py` (`_review_edb`), `aedt_copilot/cut_board/review_routing.py` (`groups`), `aedt_copilot/review_checks/_serp.py` (`pairs`, P-first sort without `*`)
- [X] T003 [US1] `aedt_copilot/review_checks/_store.py`: `SCHEMA` 2 (2.11.x records measured with the old pairing are not reused)
- [X] T004 [US1] Unit tests `tests/unit/test_pairs_034.py`: review_groups cases (spec edge cases), plain names = group_diff, interface_sim content diff groups unchanged, `_context.groups` / `_serp.pairs` with `*` start nets, store schema 2 ignores schema-1 records

## Phase 2: User Story 2 - The engineer sees the change (P2)

- [X] T005 [US2] Full unit suite + `graphify update .`
- [X] T006 [US2] AEDT checks on copies: SERLINK 3 channels with the FAB stackup table (before = 2.11.4 run, after = 034), `tests/pcie_check.py`, `tests/review_check.py`, `tests/regression.py` (board1); write `specs/034-review-pair-star-nets/verify-changes.md` (before → after per channel and check, reason)
- [X] T007 Release 2.12.0 locally: VERSION, CHANGELOG.md (Vietnamese; review results change on boards with `*` names, no setup.bat rerun), CLAUDE.md §8 row, tag v2.12.0 (no push)

## Dependencies

T001 → T002 → T003 → T004 → T005 → T006 → T007.
