# Quickstart — 042 validation

1. Unit: `python -m unittest discover -s tests/unit -t .` → all PASS (incl. `test_merge_board_copy_042`).
2. board1 copy: `python tests/config_flow_check.py <copy>\simulation.aedt` → PASS; merged project designs = the board
   designs (`main`, samples) + `CPHY_U14_U26`; self-check and M3 "Stackup = board: OK"; cut numbers 24 / 126 / 0.21.
3. BOARDA copy: `python tests/merge_board_copy_check.py <request copy>` → merged design keeps C951 / C958 / C959 /
   C1015 with 2 pins, stackup OK, Validation Check finishes (≤ 2 × channel alone).
4. SC-003: same check with `--change-thickness "Layer 3"` → self-check NOT OK line naming `Layer 3`.
