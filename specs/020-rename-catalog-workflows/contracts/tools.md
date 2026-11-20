# Contracts: composable tools + tools documented in 010 (carried over, 2.0.0)

Carried from `specs/008-*/contracts/utensils-008.md` and `specs/010-*/contracts/legacy-tools.md` (feature 020: names
only; behaviour unchanged except the design tools output folder `Ansys AEDT Copilot/design_tools/`, was
`.../kitchen/`; old folders on disk are never touched). Safety / gate = catalog. Heavy work runs
`python -m aedt_copilot <cmd>` in a subprocess; > ~45 s → `{pending, task_id}` (`task_result`).

## Help

| Tool | Inputs | Output | Safety |
|---|---|---|---|
| `about()` | — | name, version, steps per process, prompts, guides, AEDT info | read |
| `show_defaults()` | — | version, template defaults, machine config, AEDT info | read |

## Board / layout

| Tool | Inputs | Validation | Output | Safety |
|---|---|---|---|---|
| `inspect_board(board, cell="")` | `.aedt` / `.aedb` | board path resolved by CLI (`naming.board_paths`) | designs, layers, nets, big components | read |
| `layout_region(board, box, layers="", nets="")` | box `x0,y0,x1,y1` mm | box parsed by CLI | per-layer polygons / traces / vias, PNG, region.json | read |
| `layout_edit(plan)` | plan JSON path or text | plan schema checked by `edit_layout` before the copy | copy `.aedb`, checks, images, changes.md | copy |
| `finish_in_aedt(aedb, port=0)` | cut result | result exists | saved result, highlight + colours | copy (writes the given RESULT) |

## PI-DC (solved SIwave folder, in place, never saves the project)

| Tool | Output | Safety |
|---|---|---|
| `pidc_export(folder, sim_name="")` | raw images, missing_jobs, image_size | read |
| `pidc_current_density(folder, sim_name="")` | CD table + images | read |
| `pidc_via_current(folder, sim_name="")` | via table + images | read |
| `pidc_voltage_distribution(folder, sim_name="")` | VLT image + table | read |
| `pidc_power_tree(folder, sim_name="", voltage=0, current=0)` | POWER_TREE image + Pass/Fail table | read |
| `pidc_report(folder, sim_name="")` | HTML / MD / JSON / CSV report | read |

## Composable design tools (design_tools registry, 007 runner)

Input validation before any file change, copy by default (`in_place` + backup + gate only where noted). Read-only
entries run through `design_tools.inspect` (no copy, no report file). Tests: `tests/unit/test_design_tools_008.py`;
board: `tests/catalog_check.py`.

| Tool | Contract |
|---|---|
| `design_trace(board, refdes, nets="", cell="")` | read; 2 refdes (or 1 + nets); unknown refdes / no match → CopilotInputError with closest names; `inspect_board.trace_channel` |
| `design_cutout(board, comp_a, comp_b, nets, series="", name="", values="", cell="")` | copy; board copied once to `<board dir>/Ansys AEDT Copilot/design_tools/_src/` (reused when size + mtime equal); `cutter.cut_stage(... "create_new")` → `design_tools/<name>_cutout_<time>/<name>.aedb` + `stage1.json`; given board never written; partial output removed only if created by this call |
| `design_cleanup(board, ends, nets="", values="", cell="", in_place=False, user_approved_in_place=False)` | copy / original (gate); nets / bga / extent from `stage1.json` next to the design, else computed; `cutter.cleanup_gnd`; check GND per layer after ≤ before, signal nets + end components present |
| `design_end_check(board, refdes, nets="", cell="")` | read; `interface_sim.ends` thresholds / measure / unusual rules; `ends` + `ends_md` |
| `design_check(board, ends, nets="", values="", setup_name="", cell="")` | read; ends present, ports = signal pins on the ends, setup / airbox mismatches; `{ok, mismatches, ports, signal_pins}` |
| `design_merge(workspace, designs, port=0, user_approved_merge=False)` | workspace (gate); workspace `.aedt` exists, no `.lock` unless `port`; designs `{name: .aedb}` or comma list; `merge_designs` into `<workspace dir>/Ansys AEDT Copilot/design_tools/merge_<time>` (backup first, `_v2` on clash, never overwrites) |
