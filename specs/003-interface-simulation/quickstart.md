# Quickstart / validation: Interface Simulation

Repo root `D:\work\project\tool\ansys_aedt_copilot`, Python `.venv\Scripts\python.exe`. Needs feature 002 (`core/`).
AEDT steps (§3-§6) only with the engineer's OK (machine use). Always on COPIES of board1.

## 1. Offline

```bash
.venv/Scripts/python.exe -m unittest discover -s tests/unit -v
```

Expected PASS: request state machine + gates, BOM parse (xlsx / csv, ranges), markdown save / parse, content diff,
settings validate (same messages as Excel flow), unusual rules, run copy plan / path mapping / sequential loop with a
fake solver. See [contracts/](contracts/).

## 2. Old flow unchanged

```bash
.venv/Scripts/python.exe tests/regression.py
```

After a fresh `cut --excel ... --only CPHY_U14_U26 --wait` on the board1 copy: PASS, metrics equal to the 0.5.x
reference (cutter split must not change the one-pass path).

## 3. Two-stage cut identical (AEDT, ~8 min)

```bash
.venv/Scripts/python.exe tests/isim_check.py <board1 copy folder>
```

Does: `isim_start` → trace `U14,U26` → confirm → cut → check ends → apply defaults + sweep 0/10/0.1 GHz → compare
metrics with `tests/reference/CPHY_U14_U26.json`; repeat for `U21,J25`. Expected: PASS; ends table shows U14 BGA,
U26 QFN, J25 through-hole / connector flagged `connector_end`.

## 4. Gates refuse (offline, MCP)

Call `isim_cut` before confirm, `isim_apply` with `user_agreed_settings=false`, `isim_merge` with the flag false,
`isim_run` with the flag false → each returns `refused` naming the gate (unit test on server functions).

## 5. Merge into a workspace copy (AEDT, ~4 min)

Copy `board1/simulation.aedt` + `.aedb` → scratch; use it as workspace; `isim_merge` → 2 new designs, existing
designs unchanged, backup under `Ansys AEDT Copilot/interface_sim/<id>/_backup/`.

## 6. Remote run (manual, engineer's server)

Engineer starts AEDT on the server with gRPC (`ansysedt.exe -grpcsrv <port>`), gives sim dir (local + server path).
`isim_run(..., user_requested_run=true)` → copy in a new sub-folder; designs solved one by one;
`isim_run_status` table; S-parameters present.

## 7. End-to-end with the agent (Claude desktop, new chat)

Prompt `interface-sim` with board1 workspace copy, schematic PDF + BOM, "U14-U26; U21-J25" → schematic.md written
once, content tables, cut, ends + settings tables, apply, merge. Engineer only answers questions (SC-001).
