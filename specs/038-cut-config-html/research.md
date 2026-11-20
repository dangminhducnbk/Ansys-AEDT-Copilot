# Research — 038 cut config HTML

## R1 Save of an HTML page opened from disk

- Decision: Chrome / Edge File System Access API (`showSaveFilePicker`, suggested name `config.html`, picker id per
  request so it reopens in the last folder; the handle is kept for later Saves). Fallback (no API): download
  `config.html`. The saved file is the whole page with the current state serialised in
  `<script type="application/json" id="cfg-state">` and `saved_at` set.
- Reader: candidates = `<request>/config.html` + `~/Downloads/config*.html`; keep files whose
  `<meta name="aedt-copilot-request" content="<request_id>">` matches; take the newest `saved_at`. None saved →
  "not saved yet" (Q1 / M1 again).
- Rejected: local HTTP server in the MCP process (lifetime / firewall / extra moving part); JSON side file (the user
  asked for HTML).

## R2 Picture data

- Extents: `layout_snapshot.preview.open_for_preview` yields a snapshot EDB + `ext(factor)` cached per nets / type /
  factor (027). For each type (`conformal`, `convex_hull`, `bounding_box`) and factor 0.02..0.20 step 0.01:
  `cutter.cut_extent(sedb, P, nets, ends, log, strict=False, extent=ext)` = FINAL region (end GND rule 022). Measured
  in the mock: board1 78 + 20 + 21 s after a 49 s open; cached after the first time.
- Copper: `layout_snapshot.region.open_for_region(aedb, cell, bbox)` + `edit_layout.extract.extract_region` (029,
  identical to live) → shapely union per layer × class (signal / GND / other) → SVG path strings, simplify 0.01 mm,
  2 decimals. View box = bounding box of the largest extent (bounding_box 0.20) + 1 mm.
- End pads / unusual cases: one read-only live session on the board: pins of both ends (signal, GND kept by the
  cleanup rules, others), pad boxes, `ends.classify_unusual` on the source board measurements, connector pattern.

## R3 PyEDB setup / sweep / extents API (pyedb 0.85)

| Need | API |
|---|---|
| Single | `setup.set_solution_single_frequency(f, max_num_passes, max_delta_s)` (today) |
| Multi-frequencies (per row ΔS) | `adaptive_settings.adapt_type = "kMultiFrequencies"`, `clean_adaptive_frequency_data_list()`, `add_adaptive_frequency_data(f, passes, ds)` per row |
| 3D via mesh / sides | `setup.via_settings.via_style` (`k25DViaMesh` = on, `k25DViaWirebond` = off — default read from a new setup at test time), `via_num_sides` |
| Sweep ranges | `setup.add_sweep(name, frequency_set=[["linear scale", a, b, step] | ["linear count", a, b, n] | ["log scale", a, b, n]], discrete=)` |
| Q3D DC | `sweep.use_q3d_for_dc = bool` |
| Dielectric padding | `hfss_extent_info.set_dielectric_extent(size, is_multiple=True)` |
| Vertical sync | same value for `air_box_positive_vertical_extent` / `negative` |

## R4 Component model per end

- Die type / orientation / height and solder ball shape / ratio / height / material per end: written through
  `ComponentProperty` (`GetDieProperty` / `SetDieProperty`, `GetSolderBallProperty`, as `cutter.set_solder_ball`
  already does for the ball) inside `apply_stage`, with P["component_model"] = {refdes: {...}} (validated, defaults
  from the template rows `component.*` / `solder_ball.*`).
- Port location: `centre` → the SMD rebuild keeps the pin at the pad centre (no move); `end` → today's behaviour
  (`plan_smd_pin`: pad end opposite the trace = body side; via-in-pad → centre, reported). BGA → centre always.

## R5 Folder layout

- 5.0.0 requests: `<root>/<board>_<yyyymmdd_hhmmss>[_n]/` with `_work/request.json`. `request.work_dir(req)` =
  `_work` for new requests, the request folder for old ones; registry accepts both.
- Channel internal folder `iface_dir` = `<request>/_work/<name>/` until the folder is named, then
  `<request>/<folder>/_work/` (moved by `isim_config_check`; map `channel_folders` in request.json).
- Publish (end of `isim_go`): final `.aedb` → `<request>/<folder>/<folder>.aedb`; the merge preparation writes
  `<folder>.aedt` beside it; `review.html` copied; `config.html` written read-only; merged project
  `<request>/<request_id>.aedt` created by `merge_designs(create_if_missing=True)` (`oDesktop.NewProject()` +
  `SaveAs`), designs named `<folder>`.
