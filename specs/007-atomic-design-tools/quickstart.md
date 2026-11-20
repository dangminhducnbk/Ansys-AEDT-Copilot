# Quickstart: Atomic design tools

1. Offline: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` → PASS.
2. Board1 (user OK first): `tests/regression.py` + `tests/isim_check.py --recut` identical after the cutter extraction.
3. `tests/design_check.py <cut .aedb copy>`: read → sweep 0/20/0.05 (copy) → setup max passes 25 → airbox pml →
   delete-and-recreate ports of U26 (`replace`) → solder ball U14 → each report: changes listed, read-back OK, other
   items unchanged (snapshot diff), original `.aedb` unchanged; in-place call without flag refused.
