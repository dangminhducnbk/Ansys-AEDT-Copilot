# Tasks: Layout snapshot phase 2 (027)

**Input**: spec.md, plan.md, contracts/snapshot-phase2.md. Commit after each step. AEDT on fresh copies, one after
another; no AEDT GUI.

## Phase 1: Foundational

- [X] T001 `aedt_copilot/layout_snapshot/facade.py`: `polygon_data.points`, `pin.pin_number`, `SnapEdb(extra_pin_bbox)`; unit tests
- [X] T002 New `aedt_copilot/layout_snapshot/preview.py`: `extent_key`, `ExtentCache`, `comp_pins`, `open_for_preview` per contract; unit tests (fake opener / EDB)
- [X] T003 Template row `snapshot.use_for_preview` (bool, job, true) in `templates/autocut_template.csv`; goldens

## Phase 2: US1 — HTML report from the snapshot (P1)

- [X] T004 [US1] `aedt_copilot/cut_board/review.py` `review(snapshot="auto")` + `_review_edb`; fallback live + warning; source in header; `review_checks.measure_report` / `interface_sim/review.run` pass snapshot; unit test (fallback)

## Phase 3: US2 — cut preview from the snapshot (P1)

- [X] T005 [US2] `aedt_copilot/cut_board/cutter.py` `cut_extent(extent=None)`; unit test
- [X] T006 [US2] `aedt_copilot/interface_sim/cut_preview.py`: snapshot path via `open_for_preview`, fallback live, `source`; unit test (fake)

## Phase 4: Polish + verify

- [X] T007 Guides `interface_sim`, `review_measure`; `tests/preview_check.py` (025 review before GATE A; live vs snapshot preview identical; timings), `tests/review_check.py` (HTML live vs snapshot identical; timings)
- [X] T008 Unit suite; `graphify update .`
- [X] T009 AEDT fresh copies: board1 preview_check, review_check, regression, isim_check; test1 pcie_check; timings before / after

## Verify (2026-11-10, fresh copies, one after another, no AEDT GUI)

| Check | Result |
|---|---|
| board1 `preview_check.py` (first run) | FAIL: facade had no `padstacks.instances` (end_gnd.nets_in / scene) → fixed d63e086 + unit test running the end GND rule + scene on a fake snapshot |
| board1 `preview_check.py` (fresh copy, rerun) | PASS — snapshot preview = live (rows, errors, extent points, area, end_gnd) for U14_U26 and U21_J25; cut preview_check equal, area diff 0.0; U26 enlarged 0.16 (+59.19 mm²), U21 enlarged 0.14; board files unchanged |
| board1 `review_check.py` | PASS — HTML live vs snapshot: findings / points / report rows / counts identical |
| board1 `regression.py`, `isim_check.py` | PASS (references unchanged) |
| test1 `pcie_check.py` | PASS (19 / 46 / 24, 16 ports, J25 64 → 32) |

| Timing (board1) | Live | Snapshot |
|---|---|---|
| HTML report, 2 channels | 94.6 s | 2.7 s (snapshot existing) |
| Cut preview U14_U26 | 265.2 s | first 69.1 s (6 extents from AEDT, window + pin boxes built), again 1.7 s |
| Cut preview U21_J25 | 89.1 s | first 52.4 s (5 extents), again 1.4 s |

## Converge (2026-11-10)

- FR-001 HTML from the snapshot (`review.review(snapshot="auto")`, `for_review`), numbers equal live (review_check) ✓.
- FR-002 preview from the snapshot: end GND rule, other nets, scene; extent = AEDT `expanded_extent` cached per
  (nets, settings, factor) → preview extent = cut extent (area diff 0.0) ✓.
- FR-003 `layout_region` stays live (Q1 A) ✓. FR-004 stale → new board key → rebuilt; missing data / unconvertible
  primitive / board locked while a build is needed → live + `source.warning` ✓ (unit tests).
- FR-005 tool names / arguments unchanged. Decision: `isim_cut_preview` has no `snapshot` argument (adding one would
  change the MCP schema); switch = template `snapshot.use_for_preview` (job). HTML follows the review's `snapshot`.
- FR-006 cut / apply / merge unchanged (regression, isim_check, pcie_check PASS). FR-007 guides interface_sim /
  review_measure ✓.
- SC-001 HTML 2.7 s vs 94.6 s live (2.9 %) ✓. SC-002 repeated preview 1.4–1.7 s ✓ (a factor not seen before opens the
  board: first preview 52–69 s, still below live 89–265 s). SC-003 0 differences ✓. SC-004 ✓.
- No open task. Not released (user decides). CLAUDE.md status row at release.

