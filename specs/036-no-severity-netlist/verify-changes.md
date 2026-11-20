# Verify changes: 036 (4.0.0)

Copies only (session scratchpad `c36/`: board1 → b1–b5, test1 = BOARDA → t1, t2 + the user's Altium netlist). 2026-11-15.

| Check | Copy | Result | Notes |
|---|---|---|---|
| Unit suite | — | 590 PASS | new test_netlist_036 (12), test_answer_036 (5); goldens: post033 HTML only point numbers in hover titles changed (deliberate) |
| Equivalence 3.0.0 vs 4.0.0 (same copy, `review-measure` from a v3.0.0 worktree and from main) | b5, t1 | PASS | NOT OK items = HIGH + MEDIUM, OK = INFO, points equal, same check / net / value per item. board1 U14_U26 NOT OK 1 (points 1), U21_J25 14 items / 12 points; PCIe 21 / 45, 18 points |
| tests/netlist_check.py | t2 | PASS | netlist 9 339 parts / 4 084 nets in 1.9 s (whole start); PCIE_HSA2HSB 8 nets, series C951 / C958 / C959 / C1015, 0 board vs schematic differences; `answer_md` 3 parts (title 49.46 × 75.44 mm, 1023 mm²; U14 / J25 one line each; review file; final question), no severity / NOT OK / series words |
| tests/review_gate_check.py --cut | b1 | PASS | U21_J25 standalone 12 NOT OK → reused (4.0 s) → gate ready, cut refused before GATE A, approved after; board touched → approval out of date → measured again → re-approved; cut preview_check equal |
| tests/regression.py | b2 | PASS | = 3.0.0: 24 ports, 126 GND vias, planes 901–923 mm², pin shift 0.21 mm, arc 30, U26 enlarged 0.16 (+59.2 mm², pin 65); review NOT OK 1 (Near plane edge); answer_md present |
| tests/isim_check.py | b3 | PASS | U14_U26 + U21_J25 applied + approved |
| tests/pcie_check.py | t1 | PASS | review NOT OK 21 / OK 45 items, 18 points (= 3.0.0); 16 ports, caps shorted, J25 GND pins 64 → 32 |
| tests/preview_check.py | b4 | PASS | first run FAILED only on its old expect values "CONTINUE" / "STOP" → NOT OK points 1 / 12; rerun on a fresh copy PASS (preview = cut extent, manual factor errors refused at GATE A) |
| tests/review_check.py | b5 | PASS | live = snapshot = golden pre023 (items / points compared as sets by status; a merged point's displayed layer / issue order no longer follows the most severe item — first run FAILED on that, test normalised, rerun PASS) |

Before → after:

| Item | 3.0.0 | 4.0.0 |
|---|---|---|
| Review item | `severity_suggested` HIGH / MEDIUM / INFO | `status` NOT OK / OK |
| Counts (result, record, approval) | HIGH / MEDIUM / INFO points | `{"NOT OK": points}` + `by_check` |
| Channel answer | written by Claude from loose data | `answer_md` written by the tool, pasted verbatim |
| Schematic source | PDF read by Claude → schematic.md | netlist parsed by code (PDF fallback) |
| Board vs schematic | by net name; unread pins / renames / 2-pin swaps = differences | by pins; only real differences asked |
| Review record schema | 3 | 4 (3.0.0 records measured again once) |
| Cut results | — | unchanged |
