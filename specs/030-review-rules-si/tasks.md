# Tasks: More layout review rules (030)

## Phase 1: Foundational
- [X] T001 Template rows `review.*` (contract table) in `templates/autocut_template.csv`; goldens
- [X] T002 `aedt_copilot/review_checks/_si.py` pure helpers (samples, nearest edge gap, runs, neck-down mask, perpendicular offsets); `ChannelCtx.groups`; `Ctx(board=)` plumbing (`measure_edb`, `review._review_edb`)
- [X] T003 `aedt_copilot/review_checks/_stackup.py` (path / load / hash / validate / save / template); `current_thresholds(board)` adds the table hash

## Phase 2: US1 pair / trio
- [X] T004 [US1] `pair_skew.py`, `pair_gap.py`, `via_count.py`

## Phase 3: US2 return path / crosstalk
- [X] T005 [US2] `plane_edge.py`, `coupling.py`

## Phase 4: US3 stackup
- [X] T006 [US3] `stackup_width.py`; MCP tool `review_stackup_table` + CLI `stackup-table` + catalog entry + contract; goldens

## Phase 5: Polish + verify
- [X] T007 Guide `review_measure` (new rules, how the user changes a threshold, stackup table: where stored, import from fab PDF / Excel, re-import / edit); report routing note
- [X] T008 `tests/unit/test_review_rules_030.py`; full suite; `graphify update .`
- [X] T009 AEDT copies: board1 review_check (4-check golden), regression, isim_check; test1 pcie_check; numbers per rule

## Verify (2026-11-11, fresh copies, one after another, no AEDT GUI)

| Check | Result |
|---|---|
| board1 `review_check.py` | PASS — 4-check golden pre023 identical (live / snapshot build / reuse); HTML live vs snapshot identical |
| board1 `regression.py`, `isim_check.py` | PASS (verdicts unchanged: U14_U26 CONTINUE, U21_J25 STOP → override) |
| test1 `pcie_check.py` | PASS with the review reference updated on purpose: items 21 / 57 / 25, points 21 HIGH / 13 MEDIUM |
| HTML board1 / test1 | new section "Stackup" (INFO no table); "Crosstalk" appears only when a coupling finding exists (none here) |

| New rule | board1 CPHY_U14_U26 | board1 CPHY_U21_J25 | test1 PCIE_U14_J25 |
|---|---|---|---|
| 1 pair_skew | 0 (trio skew 0.013–0.041 mm) | 0 | 2 HIGH (RX L0 2.561 mm, L1 2.895 mm) |
| 2 pair_gap | — (trios) | — (trios) | 1 MEDIUM (gap up to 0.688 vs nominal 0.219 mm, 1.5 mm) |
| 3 coupling | 0 | 0 | 0 |
| 4 plane_edge | 2 MEDIUM (L1_A, Layer 3, 2.05 / 2.3 mm) | 2 MEDIUM (L2_C, Layer 5, 6.6 mm) | 6 MEDIUM |
| 5 via_count | 0 (2 vias per net) | 0 | 4 MEDIUM (TX through AC caps: 4 vias per net) |
| 6 stackup_width | 1 INFO (no table) | 1 INFO | 1 INFO |

Timing: review on the snapshot ~4–5 s per board (all 10 checks). Live path (fallback / snapshot="off") board1
85 s → 232 s (rule 4 calls the .NET point-in-polygon 3× per sample) — open point.

## Converge

- FR-001..007 / SC-001 met; SC-002 (rule 6 fake table) unit test. Decisions recorded in the spec. Nothing open
  except the live-path time of rule 4 (snapshot is the default path).

