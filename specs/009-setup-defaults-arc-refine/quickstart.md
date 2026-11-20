# Quickstart: setup defaults

1. Offline: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` → PASS.
2. Board1 copies (non-graphical):
   - `tests/isim_check.py <ws copy>` → new cut: metrics `arc_step_deg` 30, self-check OK (reads back max refine 10,
     arc 30), reference metrics otherwise equal.
   - `tests/isim_check.py <ws copy> --recut <0.7.0 request>` → proposal keeps arc 10 (previous run), `default_changes`
     = [arc 10 → team 30]; result arc 10.
   - `tests/design_check.py <cut .aedb copy>` → design tools setup reads back arc 30 / max refine 10.
3. Invalid max refine (0, 101, 10.5) → refused with the setting name and range.
