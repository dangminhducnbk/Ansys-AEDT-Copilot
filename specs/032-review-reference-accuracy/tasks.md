# Tasks: Accurate reference findings and readable pictures (032)

- [X] T001 `cut_board/review.py`: `Board.insts_in`, `check_reference` classification + one finding per stretch (+ `trace_pts`, `vias`, `void_mm`)
- [X] T002 New rule `via_clearance` (`review_rules/via_clearance.md` + `review_checks/via_clearance.py`, shared `_refcheck`), alias `reference`, BUILTIN_CHECKS
- [X] T003 `review.svg_ref_panels` + picture loop (panels for reference findings, window = stretch + vias + margin), `_pic` without the 390 px cap for panels
- [X] T004 Steering `sov.md`, `loss_of_reference.md` (2026-11-08 rule replaced), guide list regenerated
- [X] T005 Unit tests `tests/unit/test_reference_032.py`; existing tests adapted; full suite; `graphify update .`
- [X] T006 AEDT copies: test1 SERLINK (before / after per point), pcie_check, board1 review_check / regression / isim_check; references updated deliberately with the list of changed points
- [X] T008 `review_checks/plane_edge.py`: one finding per stretch over all reference planes (`planes_info`: plane, limit, H), merged per net / layer; steering `plane_edge.md`; tests; re-run SERLINK / pcie_check / review_check; counts in verify-changes.md
- [X] T007 SERLINK HTML + 1366 px REF-01 screenshot to the parent session for user review (no release yet)

## Verify (2026-11-11, copies, one after another, no AEDT GUI)

| Check | Result |
|---|---|
| test1 SERLINK (scratch copy) | U14_J8: 12 LoR HIGH + 24 SOV -> 0 (own-net clearance of J8 pins / AC-cap vias), +3 INFO; U14_U15 +5 INFO; U14_U227 +1 INFO; 0 HIGH caused by via clearances (SC-001) |
| test1 `pcie_check.py` | PASS with reference updated on purpose: items 21 / 57 / 25 -> 5 / 19 / 45, points 21 / 13 -> 5 / 13 (LoR 19 -> 3: 16 other-net via clearances -> INFO, 3 at a no-net 2.32 mm hole stay HIGH; 38 SOV twins removed) |
| board1 `review_check.py` | PASS (no change on board1; legacy check shape maps via_clearance into reference) |
| board1 `regression.py`, `isim_check.py` | PASS |
| unit | full suite PASS; `test_reference_032` (own clearance silent, other-net INFO, real slot HIGH, slot with a via at one end keeps the far part as a gap, no-net hole HIGH, one finding per stretch, outer layer, panels) |

Every changed point: [verify-changes.md](verify-changes.md). Live path slower (board1 HTML live 288 s; snapshot 6.5 s)
because all padstack instances are read once for the clearance test.

Decided by agent: a no-net padstack (mechanical hole / NPTH) never owns a clearance (its void is a real hole);
"Near plane edge" is also drawn with per-plane panels (same section, same need).

## Plane edge merge + converge (2026-11-11)

- T008: `plane_edge` one finding per stretch over all reference planes (rows "Edge distance <plane>" per plane, one
  Why / Fix); counts in verify-changes.md (SERLINK 4 -> 2 / 2 -> 1, PCIe 6 -> 3, board1 2 -> 1 per channel).
- Re-run on copies: SERLINK HTML regenerated; test1 `pcie_check.py` PASS (5 / 16 / 45, points 5 / 13); board1
  `review_check.py` PASS (26 / 1, 31 / 12). Unit suite PASS.
- User review of the 032 reports: "Gộp rồi release".
- Converge: FR-001..007 met (SC-001 0 HIGH from via clearances on SERLINK; SC-002 no stretch reported twice, plane
  edge included; SC-003 real gaps HIGH (unit + PCIe no-net hole); SC-004 user reviewed). Nothing open except the live
  path time (snapshot is the default).

