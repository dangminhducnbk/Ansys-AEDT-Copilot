# Quickstart / validation: 023 layout snapshot

Python: `D:\work\project\tool\ansys_aedt_copilot\.venv\Scripts\python.exe`, cwd = repo (worktree). Boards: COPIES only.

1. Offline: `python -m unittest discover -s tests/unit -t .` → 0 failures.
2. board1 copy (`simulation.aedb` + `.aedt`): `python tests/review_check.py <copy .aedb> <copy .aedt>` →
   live vs snapshot (build) vs snapshot (reuse) identical; equals `tests/unit/golden/pre023_review_board1.json`;
   timing table; PASS.
3. test1 copy: `python tests/snapshot_check.py <copy .aedb>` → PCIe review identical to
   `pre023_review_test1.json`, timing build / re-run, `edb.def` checksum unchanged, stale after touch → rebuilt.
4. `python tests/regression.py <board1 copy>` and `python tests/isim_check.py ...` → PASS, references unchanged.
5. MCP: `layout_snapshot(op="build", board=..., nets="CPHY_*")` → task → report; `op="status"` → valid;
   `design_review(..., snapshot="off")` = live.
