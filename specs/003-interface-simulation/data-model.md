# Data Model: Interface Simulation

All files UTF-8 JSON / markdown under `<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/`.
`request_id` = `YYYYmmdd_HHMMSS`. Interface name rules = channel name rules (unique case-insensitive, no
`<>:"/\|?*;` or space).

## Request (`request.json`)

| Field | Type | Rule |
|---|---|---|
| workspace | abs path `.aedt` | exists; engineer's main project |
| board | abs path `.aedb` | exists; default `<workspace>.aedb` |
| cell | str | default first cell / `main` |
| stackup | abs path \| "" | exists if given |
| schematic | list[abs path .pdf] | exist if given |
| bom | abs path .xlsx/.csv \| "" | exists if given |
| interfaces | list[str] | names, order of request |
| created | ISO time | — |

## Schematic markdown (`schematic.md` + `schematic.sources.json`)

Sections (fixed headers, parsed by code): `## Sources`, `## Components` table
`| Refdes | Part | Value | Description | Page |`, `## Nets` table `| Net | Pins (refdes.pin, ...) | Page |`,
`## Unreadable` list, `## BOM differences` table `| Refdes | In BOM | In schematic | Note |`.
Sources JSON: `[{path, size, mtime}]`; reuse when equal.

## BOM (`bom.json`)

`{columns_map: {refdes: "<col>", part: "<col>", value: "<col>", desc: "<col>"}, rows: [{refdes, part, value, desc}]}`;
one row per refdes (ranges like `R1-R4` and lists `R1, R2` expanded).

## Interface state (`<iface>/state.json`)

| Field | Type | Rule |
|---|---|---|
| name | str | channel name rules |
| step | enum | `started` → `content_agreed` → `cut` → `ends_checked` → `applied` → `merged`; `failed` (with `error`) |
| content | obj | `{comp_a, comp_b, nets[], diff_groups[[...]], series{refdes: {nets[]}}, schematic_diffs[{item, board, schematic, resolution}], structural{cutout.*, series.keep}}` |
| content_agreed_at | ISO \| null | set by GATE A |
| stage1 | obj \| null | `{aedb, ends, bga_ends, bodies{rd: [x0,y0,x1,y1]}, sig_pos0{"rd|net": [[x,y]...]}, nets, extent_area_m2, seconds}` |
| ends | obj \| null | see End check |
| settings | obj \| null | `{values{key: value}, rows[{key, value, unit, source: default|measured|engineer, reason}], handling{rd: option}, agreed_at}` |
| result | obj \| null | `{aedb, metrics, warnings, self_check{ok, mismatches[]}}` |
| merged | obj \| null | `{design, status: ok|renamed|error, compare}` |
| history | list | `[{time, step, note}]` |

Implementation note: a failure sets `failed: true` + `error` and KEEPS `step` = last good step (retry from there).
Transitions: only forward by one step via the matching tool; `content` change → `started` (old outputs renamed
`*_old_<time>`); any tool error → `failed` keeps the last good step in `history`; retry allowed from the last good
step.

## End check (`ends.json`)

Per end refdes: `{type: bga|through_hole|smd|smd_via_in_pad|connector|unknown, part, pins, signal_pins[{pin, net,
x, y, pad{shape, w, h}, gnd_near[{pin, dist_mm}], via_in_pad}], solder_ball, unusual[{rule, detail, values}],
options[...]}`.

Unusual rules (ids): `no_gnd_near_signal`, `non_round_pad_bga`, `connector_end`, `unknown_type`,
`pad_size_mismatch`. Options: `smd_rebuild`, `keep_component`, `no_solder_ball`, `stop_interface`.

## Simulation run (`run_<time>.json`)

`{sim_dir_local, sim_dir_server, server, port, folder, designs[{name, setup, state: queued|running|done|failed,
start, end, seconds, message, results}]}`.
