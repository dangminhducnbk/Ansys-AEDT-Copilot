---
description: "Tasks for feature 037 - review fixes after the 4.0.0 test"
---

# Tasks: 037

**Input**: `specs/037-review-fixes/` (spec.md, plan.md)

## Phase 1: US1 - cross-section walk (P1)

- [X] T001 [US1] `aedt_copilot/cut_board/review_routing.py` `walk()`: nearest unused path end (≤ TOL_PIN), nearest end pin
- [X] T002 [US1] Unit test with the dense-chain geometry of `PCIE_HSB2HSA_L0_P` (snapshot window of the test1 copy) → walk reaches J25

## Phase 2: US2 - pair gap in BGA body (P1)

- [X] T003 [US2] `aedt_copilot/review_checks/pair_gap.py`: skip stretches inside BGA end body (+ margin), `skipped_in_bga`
- [X] T004 [US2] `templates/autocut_template.csv` row `review.bga_breakout_margin_mm`; `review_rules/pair_gap.md` What
- [X] T005 [US2] Unit test: split inside BGA box skipped / outside reported / non-BGA end unchanged

## Phase 3: US3 - pair skew lengths only (P1)

- [X] T006 [US3] `pair_skew.py` data only (no items, lengths per group); `review_rules/pair_skew.md` + `routing.md`; template row `review.pair_skew_mm` removed; `review_report.py` routing section text
- [X] T007 [US3] `review_routing.len_table`: Total = trace + via, Vias column
- [X] T008 [US3] `_store.SCHEMA` 5; guide `review_measure` rule table regenerated; unit tests updated (030, 033, 026, 014 defaults, golden keys)

## Phase 4: Verification + release

- [X] T009 Full unit suite + `graphify update .`
- [X] T010 AEDT checks on copies (plan Verification); references updated; `verify-changes.md`
- [X] T011 Release 4.1.0 locally: VERSION, CHANGELOG.md, CLAUDE.md §8, tag v4.1.0 (no push)
