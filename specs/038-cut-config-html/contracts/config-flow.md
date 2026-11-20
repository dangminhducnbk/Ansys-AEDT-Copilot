# Contracts — 038 config flow

All functions raise `CopilotInputError` (core/errors) naming the bad input and the expected value.

## interface_sim/config/model.py (pure)

### `defaults(P, data_channel) -> state_channel`
- in: P = `config.defaults()` (dict), data_channel = page data of one channel (dict with `content`, `ends`).
- out: the page state of the channel filled with template defaults (folder "", every net included, diffs "board",
  choices = offered default, sweep one row Linear Step 0 → "" (mandatory, empty)).

### `validate(state, data) -> list[{channel, frame, field, message}]`
- in: state = saved page state (dict, `channels`), data = page data (dict). Channel set of state must equal data.
- out: [] when valid. Never raises for value errors (they are returned); raises for a wrong document shape.

### `to_settings(name, state_channel, data_channel, P) -> {content, structural, values, handling, folder}`
- pre: `validate` returned no error for this channel.
- out: inputs of the existing steps (content for `content.confirm`, structural for `cut_preview`, values / handling
  for `apply.run`); values only hold template keys + `sweep.ranges` / `setup.multi_freqs` / `component.model` (JSON).

### `settings_hash(settings) -> str` — sha1 of the canonical JSON (approval binding).

## interface_sim/config/answers.py (pure)

`m1(path) / q1() / m2(errors) / q2(rows) / m3(rows)` -> markdown; each text = Vietnamese line then English line;
`q1` / `q2` are the only questions; `m2` / `m3` tables have English headers. `QUESTIONS = {"q1", "q2"}`.

## interface_sim/config/page.py

### `build(data, state, readonly=False) -> str` — full HTML (assets inlined, data / state JSON embedded, request meta).
- in: data / state dicts as data-model.md; readonly hides Save / folder field.
### `parse(html_text) -> (request_id, state)` — raises when the state block or meta is missing / not JSON.

## interface_sim/config/read.py

### `find_saved(request_id, folder, downloads=None) -> {path, state, saved_at} | None`
- in: request id (text), request folder (existing dir), downloads dir (default `~/Downloads`).
- out: newest saved page (saved_at set) of this request; None when none is saved.

## interface_sim/config/data.py (EDB / snapshot, read-only)

### `channel_data(req, name, P, log=print) -> data_channel` — extents (3 types × 19 factors), layers, ends, choices.
- pre: channel traced (state has proposal / content); board readable.

## interface_sim/config/flow.py

### `config(request_id) -> {config_html, channels, answer_md}`
- pre: every interface of the request traced. Runs `review.run` when the review is not current. Writes
  `<request>/config.html` (keeps the user's saved state when the file already holds one of this request).
### `check(request_id) -> {valid, errors, answer_md, previews}`
- reads the saved page (`read.find_saved`), validates; errors → M2; valid → moves channel internal folders to
  `<request>/<folder>/_work/`, stores the settings in user_settings (section `config038`), runs
  `cut_preview.preview(structural, end_factors={})` per channel, writes `check.json` (settings hash per channel) → Q2.
### `go(request_id, user_words) -> {channels, merged, answer_md}`
- pre: `check.json` valid and its hash = hash of the saved page now; every channel's preview key = config key.
- per channel: `content.confirm` → `cut.run` → `ends.check` → `apply.run(values, handling)`; failures are recorded and
  the next channel goes on. Then `merge.run_new_project` + publish channel folders. → M3.

## interface_sim/request.py (changed)

- `start(...)`: request id `<board stem>_<yyyymmdd_hhmmss>` (safe characters, `_2` on clash); files in `_work/`.
- `work_dir(req) -> path` (`_work` for 5.0.0 requests, else the request folder).
- `iface_dir(request_id, name)`: `channel_folders[name]/_work` when set, `_work/<name>` for 5.0.0, `<name>` before.
- `set_channel_folder(request_id, name, folder)`: validates the folder name, moves the internal folder, records the map.

## interface_sim/merge.py (changed)

### `run_new_project(request_id, names, log=print) -> out`
- merges the applied channels into `<request>/<request_id>.aedt` (created when missing), design names = channel
  folders, then publishes each channel folder (aedb moved, aedt beside it, review.html, config.html).

## cut_board/cutter.py (changed)

- `apply_setup(edb, P, log)`: `setup.solution_mode` single | multi (`setup.multi_freqs` JSON rows), via mesh 3D + sides.
- `apply_sweep(st, P, log)`: `sweep.ranges` JSON rows (linear step / count / log) else the old start/stop/step;
  `sweep.use_q3d_dc`.
- `apply_airbox(edb, P)`: `airbox.dielectric_horizontal`; `airbox.z_sync` → negative = positive.
- `apply_stage(..., handling)`: `P["component"]["model"]` per end (die + ball + port location).

## mcp_server tools

| Tool | Args | Refuses when |
|---|---|---|
| `isim_config(request_id)` | request id | – (package errors) |
| `isim_config_check(request_id)` | request id | – |
| `isim_go(request_id, user_approved_cut, user_words)` | | `user_approved_cut` false; `user_words` empty |
