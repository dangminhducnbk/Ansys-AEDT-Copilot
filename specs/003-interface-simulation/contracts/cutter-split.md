# Contracts: `aedt_copilot.cut_board.cutter` split

Tests: `tests/regression.py` (one-pass, unchanged reference) + `tests/isim_check.py` (two-pass vs reference).

## `cut_channel(ch, P, src, cell, out_dir, mode, version=None, log=None) -> dict` — UNCHANGED

Same signature, return keys (`name, aedb, nets, metrics, warnings, times`) and results as 0.5.x. Now implemented as
`cut_stage` + `apply_stage` on the same open EDB (no save / reopen between).

## `channel_sets(ch, P) -> (nets, ends, keep, refs)`

Pure. Nets incl. both sides of kept series parts, end refdes, kept components, reference nets (as `cut_channel`).

## `cut_stage(edb, ch, P, cell, dst, mode, log, nets, ends, keep, refs) -> dict`

| Input | Type | Valid |
|---|---|---|
| edb | open writable Edb of the source (or of its copy) | — |
| ch | dict | `name`, `comp_a`, `comp_b`, `nets` (≥ 1, on board), `series` |
| P | dict | `build_params` output (uses `cutout.*`, `series.keep`) |
| dst | str | `.aedb` path that does not exist (mode `create_new`) |
| nets, ends, keep, refs | from `channel_sets(ch, P)` | — |

Output: `stage1` dict (JSON-safe): `nets, ends, keep, refs, bga_ends, bodies, sig_pos0, extent_pts_mm,
extent_area_m2`; edb is now the cutout (other cells deleted, cell renamed, non-kept components deleted).
Errors: RuntimeError messages unchanged (`Net không có trong board`, `Không có linh kiện`).

## `apply_stage(edb, stage1, ch, P, log, protect_polys=None, handling=None) -> dict`

Input: open writable Edb of the stage-1 design (same session or reopened), `stage1` from `cut_stage`.
Does: series 0 Ω, SMD rebuild, cleanup, BGA rebuild, coax ports, pin shift, solder balls, setup / sweep, airbox,
save, metrics, check. `handling` `{refdes: keep_component | no_solder_ball | smd_rebuild}` (None = old flow);
`protect_polys` = set of polygon ids kept by cleanup (None = empty). Output: `{metrics (incl. max_pin_shift_mm), warnings}`. EDB saved: yes.

## `stage1_to_json(stage1) -> dict` / `stage1_from_json(d) -> dict`

Pure. JSON-safe copy (`sig_pos0` key `(rd, net)` → `"rd|net"`, tuples → lists) and back. The caller saves the EDB
(`edb.save()`) and writes `stage1.json`.
