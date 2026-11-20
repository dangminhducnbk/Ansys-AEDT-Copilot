# Contracts: new utensils (feature 008)

All except `merge` are `design_tools` registry entries run by the 007 runner (`design_tools.run`): input validation
before any file change, copy by default (`in_place` + backup + gate only where noted), snapshot before / after, report.
Read-only entries (`trace`, `end_check`, `check`) run through `design_tools.inspect(op, board, ...)`: open read-only,
no copy, no report file. Tests: `tests/unit/test_design_tools_008.py` (fake EDB); board: `tests/kitchen_check.py`.

## `trace` (read)

targets `refdes` (exactly 2 for a channel, or 1 + `nets`), `nets` (patterns, optional). Unknown refdes / no match →
CopilotInputError with closest names. Calls `inspect_board.trace_channel`; output data-model `design_trace`.

## `cutout` (copy — new design)

values `cutout.*`, `series.*`; targets `comp_a`, `comp_b`, `nets` (names or patterns, required), `series` (refdes list,
optional), `name` (default `<prefix>_<a>_<b>` like the Excel auto name). Steps: copy the board once to
`<board dir>/Ansys AEDT Copilot/kitchen/_src/` (reuse when size + mtime equal, as `interface_sim.cut.copy_source`),
open the copy writable, `cutter.channel_sets` + `cutter.cut_stage(... "create_new" ...)` to
`<board dir>/Ansys AEDT Copilot/kitchen/<name>_cutout_<time>/<name>.aedb`, save, write `stage1.json` next to it.
Never writes the given board. Failure → partial output removed only if created by this call.

## `cleanup` (copy / original)

values `cleanup.*`, `cutout.reference_nets`; targets `ends` (refdes list, required), `nets` (default: `stage1.json`
next to the design, else the non-reference nets shared by the ends). `bga_ends` / `extent_area` from `stage1.json`,
else research R2. Runs `cutter.cleanup_gnd` with no protected ids. check = GND per layer after ≤ before, signal nets
still present, end components still present. Report: removed counts per layer.

## `end_check` (read)

targets `refdes` (list, required), `nets` (default: non-reference nets of each component). Uses
`interface_sim.ends.thresholds(P)`, `_measure`, `classify_unusual`. Output data-model `design_end_check` + `ends_md`.

## `check` (read)

values `setup.* / sweep.* / airbox.*` (expected; template defaults + given), targets `ends`, `nets`, `setup_name`.
Mismatches: each end present; ports == signal pins of `nets` on the ends; `setup_mismatches(read_setup)`;
`airbox_mismatches(read_airbox)`. Output `{ok, mismatches, ports, signal_pins}`.

## `design_tools.merge.run(workspace, designs, port=None, out_dir="") -> dict` (workspace)

| Input | Type | Valid |
|---|---|---|
| workspace | str | existing `.aedt`; no `.lock` unless `port` |
| designs | dict \| str | `{name: .aedb}` or comma list of `.aedb` (name = stem); names follow channel name rules; each `.aedb` exists, no lock |
| port | int \| None | 1..65535 |

Calls `cut_board.merge.merge_designs(workspace, designs, out_dir or <workspace dir>/Ansys AEDT Copilot/kitchen/merge_<time>, port, log)`
(backup of the workspace first, `_v2` on name clash, never overwrites). Output = its result + `out_dir`.
