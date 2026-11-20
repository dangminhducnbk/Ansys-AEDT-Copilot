# Implementation Plan: Merged project = copy of the original board + cut channels, stackup checked

**Branch**: `main` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)
| Release: 5.4.0 (minor: merge target changes, no tool / CLI change)

## Summary

| Area | Change |
|---|---|
| `cut_board/stackup_check.py` (new, pure + EDB reader) | `read(edb)` → `{layers: [{name, type, material, fill, thickness_um}], materials: {name: {permittivity, loss_tangent, conductivity}}}` (only materials used by the layers); `compare(ref, got)` → list of difference lines (order / missing / extra layer; per layer type / material / fill / thickness ± 0.01 µm; per material property relative 1e-6). |
| `cutter.cut_stage` | `stage1["board_stackup"] = stackup_check.read(edb)` before the cutout (source board). |
| `apply.self_check` | item "stackup = board": `compare(stage1.board_stackup, read(design))`, one mismatch line per difference; result key `stackup` {ok, diffs}. Old stage1 without `board_stackup`: `stackup: {ok: null, note: "no board stackup recorded (cut before 5.4.0)"}`, not a mismatch. |
| `cut_board/merge.py` | `copy_board(board, workspace, target_aedt, log)` (new): copies the board project per research R3 into the request folder, returns {aedt, aedb, bytes, board_designs}; board without `.aedt` → open the copied `.aedb` in AEDT once, save. `merge_designs(..., backup=True, board_stackup=None)`: `backup=False` for the tool's own copy; after AEDT is released, `merged_checks`: for every merged channel open the merged `.aedb` cell read-only and compare with the channel `.aedb`: components {refdes: numpins, part, sorted pin names} and stackup (vs `board_stackup` when given, else vs the channel); differences → channel `state = "error"`, `error` = lines, `checks` {pins, stackup}. Board designs listed before / after: any missing → error. |
| `interface_sim/config/flow.merge_new_project` | target = `<request>/<request_id>.aedt`: if missing or not a board copy (request key `merge_layout != "board_copy"`, i.e. 5.0–5.3 empty project) → old one moved to `_work/history/<time>/`, `copy_board(req.board, req.workspace)`; request `merge_layout = "board_copy"`, `merged_board_designs`, `merged_copy_bytes`; `merge_designs(..., backup=False, board_stackup=<stage1 of the first channel>)`. Re-run of `isim_go` on a board-copy target: channels added again (`_vN`, as before). |
| `answers.m3` | after the table: "Board copy: <designs> (<size> MB)" and "Stackup = board: OK" or the difference lines per channel (VI + EN like the other texts). Rows carry `stackup` and `checks`. |
| Step tools `isim_merge` / `design_merge` | unchanged target (user's project, backup kept); get `merged_checks` through `merge_designs` (stackup vs channel). |
| Guide `interface_sim` §0 / N7 merge | merged project = copy of the board + channels; stackup / pin checks; old 5.0–5.3 merged projects with series parts: re-run `isim_go` (CHANGELOG). |

## Constitution Check

| Principle | Status |
|---|---|
| I Gates | Unchanged (`isim_go` user_approved_cut). |
| II Data safety | Board only read (copy; `.lock`, `edb.def.tmp` skipped; copy works while the board is open). Old merged project moved to `_work/history`, never deleted. |
| III Defaults | No template change. |
| V Regression | board1 config_flow_check: cut numbers unchanged (24 / 126 / 0.21), merged project now holds `main` + channel. New BOARDA check (SC-002). |
| VII Contracts | [contracts/merge-board-copy.md](contracts/merge-board-copy.md): result keys added. |
| IX Stable interface | Tools / CLI unchanged; `isim_go` result adds keys; merged project path unchanged. |

## Tests

- Unit `tests/unit/test_merge_board_copy_042.py`: `stackup_check.compare` (equal, thickness 0.02 µm, material, fill,
  order, extra / missing layer, εr / tanδ change), `read` on a fake EDB, `copy_board` file selection (fake tree with
  `.lock`, `edb.def.tmp`, `edb.def+`, `stride/`; `.aedb` only board), component pin comparison, merge target decision
  (missing / old empty / board copy), M3 lines; self-check stackup item (with / without `board_stackup`).
- Existing: config flow / merge golden lists updated where result keys are added.
- AEDT on copies: board1 `tests/config_flow_check.py` (merged project designs = board designs + channel, stackup OK);
  BOARDA PCIE_U14_J25 (`tests/merge_board_copy_check.py`, new): request copy → merge → 4 C × 2 pins, stackup OK,
  Validation Check ≤ 2 × channel alone (SC-002); changed-thickness copy → self-check NOT OK naming the layer (SC-003).

## Project Structure

`aedt_copilot/cut_board/{stackup_check.py (new), cutter.py, merge.py}`, `aedt_copilot/interface_sim/{apply.py,
config/flow.py, config/answers.py}`, `guides/interface_sim.md`, `tests/unit/test_merge_board_copy_042.py`,
`tests/merge_board_copy_check.py`, CHANGELOG / VERSION 5.4.0 / CLAUDE.md row.
