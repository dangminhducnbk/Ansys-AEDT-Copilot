# Tasks: GND pin cleanup on SMD / connector ends (021)

**Input**: spec.md, plan.md, contracts/gnd-pin-cleanup.md. Commit after each step. AEDT on fresh copies, one after
another. Do not touch request / folder-id code (feature 024 in parallel).

## Phase 1: Setup

- [X] T001 Template row `cleanup.smd_gnd_pin_keep_dist_mm` 1.6 mm (scope channel) in `templates/autocut_template.csv`; `HISTORY` entry since (2, 3, 0) in `aedt_copilot/interface_sim/defaults_history.py`

## Phase 2: Foundational

- [X] T002 New `aedt_copilot/cut_board/gnd_pins.py`: `select`, `report`, `protected_names` per contract

## Phase 3: US1 — connector end keeps only the GND ring (P1)

- [X] T003 [US1] `aedt_copilot/cut_board/cutter.py`: `rebuild_smd_component(protect_names)` prunes own GND pins before the rebuild; `apply_stage` passes protect names from stage1, `metrics.gnd_pin_cleanup`
- [X] T004 [US1] `aedt_copilot/interface_sim/apply.py`: `gnd_pin_cleanup` in the apply result + self-check
- [X] T005 [US1] `tests/unit/test_gnd_pins_021.py`: selector, 022 / 015 / 019 references never pruned, nearest kept per signal pin, rebuild with fake EDB

## Phase 4: US2 — engineer sees / changes the rule (P2)

- [X] T006 [US2] Gate B row shown (template), re-cut source "team default (new)"; unit tests (settings proposal, defaults history)
- [X] T007 [US2] `aedt_copilot/design_tools/cleanup.py` + `cutter.cleanup_gnd(smd_ends, smd_protect)`; unit test

## Phase 5: Polish + verify

- [X] T008 Guides `guides/interface_sim.md` (verification 4 / 4c, N5), `guides/design_tools.md`; `tests/pcie_check.py` J25 check
- [X] T009 All unit tests (goldens: new row added after 014 / 002); `graphify update .`
- [X] T010 AEDT fresh copies: test1 `pcie_check.py`; board1 `regression.py` then `isim_check.py`
- [X] T011 Converge; CLAUDE.md status row (no release: user decides 2.3.0)

## Converge (2026-11-10)

- FR-001..009 / SC-001..004 checked against code: no gap. FR-001 / Q2 `rebuild_smd_component` prunes own GND pins of every rebuilt SMD / via-in-pad / connector end (not `keep_component`); FR-002 / Q1 row `cleanup.smd_gnd_pin_keep_dist_mm` 1.6 mm (Gate B, cut group); Q3 `defaults_history` since 2.3.0 (re-cut source "team default (new)"); FR-003 plate / copper never pruned, 022 end GND pin / pad + 019 kept pads protected (unit tests); FR-004 nearest per signal pin kept + warning; FR-005 rebuild pin-count check unchanged + self-check GND count; FR-006 `metrics` / `self_check.gnd_pin_cleanup`; FR-007 `design_cleanup`; FR-008 board1 references unchanged; FR-009 guides + pcie_check.
- AEDT 2026-11-10 on fresh copies, one after another: test1 `tests/pcie_check.py` PASS — J25 GND pins 64 → 32, 0 warnings, 16 ports = expected, self-check OK, review 19 / 46 / 24 unchanged, U14 / J25 `met`. Board1 `tests/regression.py` PASS (2.1.0 reference). Board1 `tests/isim_check.py` PASS (reference OK; CPHY_U21_J25: J25 84 → 30, 18 ports, self-check OK; U21 enlarged, J25 met). U26 / U21: 1 → 1 (pad 65 only) with 12 / 9 warnings "no GND pin within 1.6 mm" (centre-to-centre to the 6.3 mm exposed pad centre) — reported to the parent session as a possible follow-up (warn only when the nearest pin is not the protected end reference).
- 413 unit tests PASS; 54 tools. No release (user decides 2.3.0).

## Phase 6: Fix — distance to the GND pad edge (clarify 2026-11-10)

- [X] T012 `aedt_copilot/cut_board/gnd_pins.py` `select` accepts GND pad boxes (distance point → box, 0 inside); `cutter.prune_own_gnd_pins` passes pad bounding boxes; contract updated; unit test (6.3 mm pad, signal pins at its edge → kept, no warning)
- [X] T013 AEDT fresh copies: test1 `pcie_check.py` (J25 count), board1 `isim_check.py` (U26 / U21 warnings 0, J25 count)
- Result 2026-11-10 (fresh copies, one after another): test1 `pcie_check.py` PASS — J25 64 → 32 (unchanged), 0 warnings, 16 ports, review 19 / 46 / 24; board1 `isim_check.py` PASS (reference OK) — U26 1 → 1 and U21 1 → 1 with 0 warnings (were 12 / 9), J25 84 → 30 (unchanged), 18 ports. 415 unit tests PASS.

## Phase 7: Rule — single own GND pin = the chip's return path (clarify 2026-11-10)

- [X] T014 `aedt_copilot/cut_board/gnd_pins.py` `report`: exactly one own GND pin → no warning, `info` line "<rd>: GND duy nhất pin <n>, đã giữ"; several → warning unchanged; contract + guide N5; unit tests (single pin 5 mm away → kept, 0 warnings, info; two far pins → warning). Reporting only: `select` / pruning unchanged → no AEDT re-run
