# Quickstart / validation (025)

Python: `D:\work\project\tool\ansys_aedt_copilot\.venv\Scripts\python.exe`, cwd = worktree. Boards: COPIES only
(scratchpad), never `test\` or `C:\work\cut_board\board1\` originals.

| # | Check | Command | Expected |
|---|---|---|---|
| 1 | Offline | `python -m unittest discover -s tests/unit -t .` | all PASS (incl. `test_review_gate_025`), server 56 tools |
| 2 | Gate on board1 copy | `python tests/review_gate_check.py --board <copy>` | U14_U26: Gate A / cut refused before review; review CONTINUE (24 INFO, 0 points); Gate A OK. U21_J25: STOP (2 HIGH); Gate A refused; override with reason → Gate A OK; cut start accepted (not waited unless `--cut`) |
| 3 | Standalone reuse | same script, step standalone | `design_review` U21-J25 → record + STOP; isim review → `reused_from` = record, same points, < 5 s; touch edb.def mtime on the copy → measured again |
| 4 | test1 PCIe | `python tests/pcie_check.py` (adapted) | review STOP (19 HIGH); continues only with override (script records reason "pcie_check") ; numbers unchanged |
| 5 | Regression | `python tests/regression.py`, `python tests/isim_check.py` | PASS with 2.1.0 / 2.2.0 references; U21_J25 path uses override |
