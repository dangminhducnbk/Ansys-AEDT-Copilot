# Quickstart — validate 038

## Offline

```bash
.venv/Scripts/python.exe -m unittest discover -s tests/unit -t .
```
Expected: all PASS, incl. `test_config_model`, `test_config_answers`, `test_config_page`, `test_config_read`,
`test_request_layout_038`, catalog tests (3 new tools registered, gated `isim_go`).

## On a board1 copy (AEDT 2026 R1, non-graphical)

```bash
.venv/Scripts/python.exe tests/config_flow_check.py --board <copy of board1>/simulation.aedt
```
Steps: `isim_start` → `isim_trace` CPHY U14-U26 → `isim_config` (config.html written, M1) → the script fills the
saved state (folder `CPHY_U14_U26`, sweep 0–20 GHz step 0.05, expansion 0.06) as a browser Save would →
`isim_config_check` (Q2, preview = 0.06 region) → `isim_go`.
Expected:
- `<request>/` top level: `<request_id>.aedt`, `<request_id>.aedb/`, `config.html`, `request.md`, `CPHY_U14_U26/`,
  `_work/`.
- `<request>/CPHY_U14_U26/`: `CPHY_U14_U26.aedb/`, `CPHY_U14_U26.aedt`, `review.html`, `config.html`, `_work/`.
- merged project: one design `CPHY_U14_U26`, 24 ports, setup / sweep read back = config.
- regression numbers unchanged vs `tests/reference/CPHY_U14_U26.json` (ports, GND vias, planes).

## Regression (Principle V)

```bash
.venv/Scripts/python.exe tests/regression.py
```
```bash
.venv/Scripts/python.exe tests/isim_check.py
```
Expected: PASS with the 2.1.0 references (old tools unchanged).
