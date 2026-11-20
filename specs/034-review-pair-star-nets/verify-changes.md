# Verify changes — 034 (2026-11-14)

All AEDT runs on COPIES in the session scratchpad (test1 `BOARDA_PN00000000-A_01_EDB_20260915`, board1 `simulation`),
layout snapshot. Before = 2.11.4 record (schema 1), after = 034 (schema 2).

## SERLINK (test1 copy, FAB stackup table)

| Channel | Pairs recognised | Findings before → after | Reason |
|---|---|---|---|
| SERLINK_U14_U15 | 2 → 4 | HIGH 0 / MEDIUM 16 / INFO 37 → 0 / 8 / 37: "Width vs stackup" 8 → 0 | DEVA2DEVB L0 / L1 start with `X_P*` / `X_N*`; now compared with the 85 Ω pair width (0.101 / 0.102 mm, within 0.01) |
| SERLINK_U14_J8 | 0 → 2 | 0 / 6 / 15 → unchanged | TX pairs now checked: skew 0.024 / 0.011 mm (OK), no pair gap / coupling / gap vs stackup finding |
| SERLINK_U14_U227 | 2 → 2 | 0 / 4 / 9 → unchanged | no `*` start nets |

## PCIe (test1 copy, `tests/pcie_check.py`) — reference changed on purpose

| Item | Before → after | Reason |
|---|---|---|
| Pairs recognised | 2 → 4 | PCIE_HSA2HSB L0 / L1 start with `X_P*` at U14 (same naming as SERLINK) |
| Review items | HIGH 5 / MEDIUM 14 / INFO 45 → 7 / 14 / 45 | +2 Pair skew HIGH: HSA2HSB_L0 0.917 mm, HSA2HSB_L1 1.244 mm (> 0.127); verdict was already STOP |
| Points | HIGH 5 / MEDIUM 11 → 7 / 11 | same 2 findings |
| Cut (ports, series shorts, J25 GND pins 64 → 32) | unchanged | cut does not use review pairs |

Spec SC-003 expected PCIe identical: wrong assumption (PCIe uses the same `*` naming); the two new HIGH rows are real
pair-skew results that 2.11.x skipped.

## board1 (copies)

| Script | Result |
|---|---|
| `tests/review_check.py` (b1) | PASS (findings / points / rows = golden) |
| `tests/regression.py` (b2) | PASS: 24 ports, 126 GND vias, planes 901–923 mm², pin shift 0.21 mm, arc 30; review CONTINUE (0 / 1 / 25) |

## Unit tests

574 PASS (new `tests/unit/test_pairs_034.py`: review_groups cases, plain names = group_diff, Gate A grouping
unchanged, serpentine P first, stackup width on a `*` pair, store schema 2).
