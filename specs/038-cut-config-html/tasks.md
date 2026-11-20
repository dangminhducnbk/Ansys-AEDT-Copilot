# Tasks — 038 cut config HTML (one approval, folder per channel)

Legend: [P] = can run in parallel with the previous task (other files). Paths from the repo root.

## Phase 1 — Setup

- [x] T001 Template rows (Principle III) in `templates/autocut_template.csv`: `setup.solution_mode` (single),
  `setup.multi_freqs` (text JSON, empty), `setup.via_mesh_3d` (true), `setup.via_num_sides` (6),
  `sweep.distribution` (linear_step), `sweep.ranges` (text JSON, empty), `sweep.use_q3d_dc` (false),
  `airbox.dielectric_horizontal` (0), `airbox.z_sync` (true), `component.die_type` (flip_chip),
  `component.die_orientation` (chip_down), `component.die_height_mm` (0), `component.port_location` (end),
  `component.model` (text JSON, empty); `defaults_history` entry for 5.0.0 (old runs keep their behaviour).
- [x] T002 Package skeleton `aedt_copilot/interface_sim/config/__init__.py` + `assets/`.

## Phase 2 — Foundation (request layout, pure model)

- [x] T003 `interface_sim/request.py`: 5.0.0 layout (`_work/`, request id `<board>_<time>`), `work_dir`, registry both
  layouts, `iface_dir` with `channel_folders`, `set_channel_folder` (validate + move); all request-level files through
  `work_dir` (content.py board_nets, merge.py merge.json, run.py, schematic.py, user_settings.py, recut.py).
- [x] T004 [P] `tests/unit/test_request_layout_038.py`: new layout paths, old layout still read, folder rename,
  name validation.
- [x] T005 `interface_sim/config/model.py`: defaults / validate / to_settings / settings_hash (data-model.md rules).
- [x] T006 [P] `tests/unit/test_config_model.py`: every validation rule, mapping to structural / values / handling,
  nets include, sweep ranges → start / stop / step, multi freqs, component model.
- [x] T007 `interface_sim/config/answers.py`: M1 / Q1 / M2 / Q2 / M3 bilingual.
- [x] T008 [P] `tests/unit/test_config_answers.py`: each text has VI + EN line, only Q1 / Q2 are questions, at most one
  question per answer.

## Phase 3 — US3 page (HTML) + reader

- [x] T009 `interface_sim/config/assets/page.html|page.css|page.js` from the approved mock: per-channel state, all 4
  frames + Content frame + choices, folder field, Save (File System Access API + download fallback), readonly mode.
- [x] T010 `interface_sim/config/page.py`: build (inline assets, JSON blocks, meta) / parse.
- [x] T011 `interface_sim/config/read.py`: find_saved (request folder + Downloads).
- [x] T012 [P] `tests/unit/test_config_page.py` + `test_config_read.py`: build → parse round trip, saved state wins,
  other request ignored, newest saved_at.

## Phase 4 — US1 / US2 data + flow

- [x] T013 `interface_sim/config/data.py`: extents per type × factor (snapshot preview + cut_extent), layers (snapshot
  region + shapely), ends pads + choices (live read-only), with log + timings.
- [x] T014 `cut_board/cutter.py`: apply_setup (single / multi, via mesh / sides), apply_sweep (ranges, Q3D DC),
  apply_airbox (dielectric padding, z sync), component model per end in apply_stage (die, ball, port location);
  old P without the new keys = identical behaviour.
- [x] T015 [P] `tests/unit/test_cutter_038.py` (fake setup objects): calls made for single / multi / ranges / q3d /
  extents; old P → old calls.
- [x] T016 `interface_sim/config/flow.py`: config / check / go + publish channel folders; `merge.run_new_project` +
  `cut_board/merge.merge_designs(create_if_missing=True)`.
- [x] T017 [P] `tests/unit/test_config_flow.py` (fake steps): order of steps, refusal when config changed after Q2,
  a failed channel does not stop the others, publish layout.

## Phase 5 — Server, catalog, guide

- [x] T018 `interface_sim/api.py` ops `config`, `config_check`, `go`; `mcp_server/server.py` tools `isim_config`,
  `isim_config_check`, `isim_go` (gate `user_approved_cut` + `user_words`); `catalog/tools.py` entries (safety copy,
  gate), `PROCESS_GUIDES`; contract block.
- [x] T019 [P] catalog / server tests updated (tool count, gated refusal, golden of tool list if any).
- [x] T020 `guides/interface_sim.md` (fixed process, texts verbatim, old tools = manual / recovery),
  `prompts/interface-sim.md`, server instructions line; `about()`.

## Phase 6 — Verification on copies + release

- [x] T021 `tests/config_flow_check.py` on a board1 copy (quickstart) — PASS.
- [x] T022 `tests/regression.py`, `tests/isim_check.py` on board1 copies — PASS (old flow unchanged).
- [x] T023 Offline suite PASS; `graphify update .`; VERSION 5.0.0, CHANGELOG (setup.bat: no), CLAUDE.md status row;
  commit + tag v5.0.0 (no push).
