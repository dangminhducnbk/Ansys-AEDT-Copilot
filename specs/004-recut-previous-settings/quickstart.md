# Quickstart: Re-cut from previous settings

1. Offline: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` → all PASS.
2. Board1 copy (ask the user first): `tests/isim_check.py` scenario `recut` — first run CPHY_U14_U26 (or reuse the
   0.6.0 request in the scratch copy), then `isim_previous` → `isim_recut` from it → 0 `recut_diffs` → confirm →
   cut → ends (`handling_compare` all `kept`) → apply with `old_values` → self-check OK, `arc_step_deg` 10, metrics
   equal to the first run.
3. Excel flow: `tests/regression.py` CPHY_U14_U26 → PASS with `arc_step_deg` 10.
4. Open one cut design in AEDT GUI (user not using AEDT): Setup → Advanced Meshing → arc step 10 deg.
