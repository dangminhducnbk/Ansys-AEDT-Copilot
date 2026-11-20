# Quickstart / validation: 036

Copies only (scratchpad). Board1 = `C:\work\cut_board\board1`, test1 = `test/test1` (BOARDA).

| Step | Command | Expect |
|---|---|---|
| Unit | `.venv\Scripts\python -m unittest discover -s tests/unit -t .` | all PASS |
| No severity words | grep `HIGH|MEDIUM|INFO|severity` in review outputs / guides / review_rules | none (pi_dc excluded) |
| Netlist | `tests/netlist_check.py <BOARDA copy .aedt> <netlist>` | parse < 10 s; trace PCIE_HSA2HSB → 0 diffs, C951 value 220 nF; answer_md 3 parts |
| Review gate | `tests/review_gate_check.py <board1 copy .aedt> --cut` | PASS with NOT OK counts |
| Regression | `tests/regression.py <board1 copy>` | = 3.0.0 cut numbers |
| isim | `tests/isim_check.py` | PASS |
| PCIe | `tests/pcie_check.py` (test1 copy) | NOT OK counts reference updated; cut numbers unchanged |
| Preview / review | `tests/preview_check.py`, `tests/review_check.py` | PASS |
