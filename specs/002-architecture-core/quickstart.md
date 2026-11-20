# Quickstart / validation: Architecture + core/

All commands from repo root `D:\work\project\tool\ansys_aedt_copilot`, Python = `.venv\Scripts\python.exe`.

## 1. Offline (no AEDT) — every task

```bash
.venv/Scripts/python.exe -m unittest discover -s tests/unit -v
```

Expected: all PASS in < 30 s. Covers contracts in [contracts/](contracts/): errors, validate, config (golden),
edb (`aedb_path`, fake session), geometry (golden), units, registry, import rule (`core/` → no feature package).

## 2. Interface unchanged (offline)

```bash
.venv/Scripts/python.exe -c "import aedt_copilot.cut_board.config as c, aedt_copilot.cut_board.geometry as g; print(len(c.template_rows()), g.poly_area([(0,0),(1,0),(1,1)]))"
```

Expected: same template row count as before; `0.5`. MCP: tool / prompt / guide name lists from
`mcp_server/server.py`, `prompts/`, `guides/` equal the lists saved before the change (test
`test_interface_unchanged.py`).

## 3. Cut regression (AEDT, ~6 min, ASK USER FIRST — machine use)

On a COPY of board1 with the reference Excel (channel `CPHY_U14_U26`):

```bash
.venv/Scripts/python.exe -m aedt_copilot cut --excel <board1 copy>/autocut/channels.xlsx --only CPHY_U14_U26 --wait
```

```bash
.venv/Scripts/python.exe tests/regression.py
```

Expected: PASS; metrics (ports 24, U14/U26 pins + GND pins, GND vias 101, planes 845-865 mm², pin shift) equal to
the last run before 002.

## 4. PI-DC check (no SIwave run needed)

```bash
.venv/Scripts/python.exe -m aedt_copilot pidc --dir <BOARDB_B04 folder> --skip-export
```

```bash
.venv/Scripts/python.exe tests/pidc_check.py <BOARDB_B04 folder>
```

Expected: PASS, same values as before 002 (L8 31.74 / 26.64 / 24.77, VCC_0P8V TOP 49.2, via max util 0.40).

## 5. Release

`VERSION` 0.5.1, `CHANGELOG.md` entry ("internal: core/ package; no setup.bat rerun"), `graphify update .`,
commit, tag `v0.5.1` (push by user).
