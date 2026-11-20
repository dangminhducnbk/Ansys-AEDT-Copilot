# Contracts: MCP tools without a contract before 010

> 1.0.0 (feature 017): `review_layout`, `propose_channels`, `read_channels`, `start_cut_batch`, `job_status`,
> `get_report`, `merge_to_project` were REMOVED (Excel flow retired); their sections below are history only.

Documents CURRENT behaviour (Principle VII, FR-005); nothing changes. Safety / gate = catalog. All heavy work runs
`python -m aedt_copilot <cmd>` in a subprocess; > ~45 s → `{pending, task_id}` (`task_result`). Errors of the CLI come
back as `error_log`.

## Help

| Tool | Inputs | Validation | Output | Safety |
|---|---|---|---|---|
| `about()` | — | — | name, version, steps per process, prompts, guides, AEDT info | read |
| `show_defaults()` | — | — | version, template defaults, machine config, AEDT info | read |

## Board / review / layout

| Tool | Inputs | Validation | Output | Safety |
|---|---|---|---|---|
| `inspect_board(board, cell="")` | `.aedt` / `.aedb` | board path resolved by CLI (`excel_io.board_paths`); missing → CLI error | designs, layers, nets, big components | read |
| `review_layout(board, channels, cell="")` | channels `A-B:pattern; ...` | request parsed by CLI; unknown refdes / nets → CLI error | HTML report path + findings per level | read (report file beside the board) |
| `layout_region(board, box, layers="", nets="")` | box `x0,y0,x1,y1` mm | box parsed by CLI (4 numbers) | per-layer polygons / traces / vias, PNG, region.json | read |
| `layout_edit(plan)` | plan JSON path or JSON text | JSON text saved to `.tasks/plan_*.json`; plan schema checked by `edit_layout` (op error → nothing saved, copy removed) | copy `.aedb`, checks, images, changes.md | copy |
| `finish_in_aedt(aedb, port=0)` | cut result | CLI: result exists | saved result, highlight + colours (colour may warn on 2026 R1) | copy (writes the given RESULT) |

## PI-DC (solved SIwave folder, in place, never saves the project)

| Tool | Inputs | Validation | Output | Safety |
|---|---|---|---|---|
| `pidc_export(folder, sim_name="")` | folder with `.siw` + results | CLI: folder / DC sim exists (one DC sim when empty) | raw images, missing_jobs, image_size | read |
| `pidc_current_density(folder, sim_name="")` | same | needs pidc_export output | CD table + images | read |
| `pidc_via_current(folder, sim_name="")` | same | needs pidc_export output | via table + images | read |
| `pidc_voltage_distribution(folder, sim_name="")` | same | needs pidc_export output | VLT image + table | read |
| `pidc_power_tree(folder, sim_name="", voltage=0, current=0)` | same; voltage / current only on request (0 = template) | numbers | POWER_TREE image + Pass/Fail table | read |
| `pidc_report(folder, sim_name="")` | same | skill results present | HTML / MD / JSON / CSV report | read |

## Process: Excel cut (guide workflow)

| Tool | Inputs | Validation / gate | Output | Safety |
|---|---|---|---|---|
| `propose_channels(board, channels, user_approved_review=False)` | board, channels request | refused without a `layout_review_*.html` for the board, then without the flag (GATE 1) | `channels.xlsx` path + rows | copy |
| `read_channels(excel)` | Excel path | yellow cells, types, sweep rule, channel names | per channel valid / errors, `all_valid`, `name_errors` | read |
| `start_cut_batch(excel, only="", user_approved_excel=False)` | Excel, names | flag first (GATE 2), then `read_channels` all valid | job id (background) | copy |
| `job_status(job_id="")` | job id (empty = latest) | job exists | per channel state | read |
| `get_report(job_id="")` | job id | job exists | report + Excel; writes `.reported` marker | read |
| `merge_to_project(job_id="", only="", port=0, user_approved_verify=False)` | job, names, port | flag first (GATE 3, from 010), then job done + `.reported` | merge result (backup first, `_v2` on clash) | workspace |

## Help (already elsewhere)

`get_guide`, `task_result`: `specs/003-interface-simulation/contracts/mcp-tools.md`.
