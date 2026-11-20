# Implementation Plan: Cut config up front (HTML), one approval, folder per channel

**Branch**: `main` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)
**Input**: specs/038-cut-config-html/spec.md (FR-001..037, approved mock `mock/config_demo_v5.html`)

## Summary

A new fixed process on top of the existing interface-simulation package:

`isim_start` → `isim_trace` (each channel) → **`isim_config`** (review + extents + layout data + `config.html`, M1)
→ user edits / saves / "xong" → **`isim_config_check`** (read + validate the saved file → M2, or previews + Q2)
→ "đồng ý" → **`isim_go`** (GATE: `user_approved_cut`; content confirm + cut + end check + apply + merge into a NEW
project in the request folder + channel folders; M3).

Existing tools and steps (`isim_confirm_content`, `isim_cut`, `isim_apply`, `isim_merge`, ...) stay (Principle IX)
and are reused inside `isim_go`; the guide makes the new process THE way to cut. New request layout (`_work/`,
channel folders named by the user) for requests created from 5.0.0; older requests are read as before.

## Technical Context

**Language/Version**: Python 3.12 (repo `.venv`), HTML + vanilla JS (no CDN: the page must open offline from disk)
**Primary Dependencies**: pyedb 0.85, pyaedt 1.9.0, shapely (layer pictures), PIL (existing images), mcp<2
**Storage**: files under `<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/`
**Testing**: `python -m unittest discover -s tests/unit -t .` (offline), AEDT checks on board copies
(`tests/regression.py`, new `tests/config_flow_check.py`)
**Target Platform**: Windows 11, AEDT 2026 R1; browser Chrome / Edge (File System Access API for Save; download
fallback for other browsers)
**Performance Goals**: config page data per channel ≤ 5 min first time (extents 3 types × 19 steps + layers + ends),
seconds when cached; page load < 1 s, slider / tab redraw < 0.1 s
**Constraints**: page fully offline (all JS / CSS inline), English only; chat texts bilingual (VI + EN)
**Scale/Scope**: 1–6 channels per request; HTML ≈ 5–15 MB per channel (layer copper)

## Constitution Check

| Principle | Status |
|---|---|
| I Gates in code | `isim_go` refuses without `user_approved_cut=true` + `user_words`; package `flow.go` re-checks: config validated, every channel reviewed (current review + report) and previewed with the config's settings (same key). The approval replaces GATE A + GATE B for this process; GATE C (merge) applies to the user's workspace only — `isim_go` merges into a NEW project of the request folder (no user file written) so no extra gate; GATE D unchanged. **Constitution text (Principle I lists gates A–D) must be amended by the repo owner** — recorded in the release notes, not changed by the agent. |
| II Data safety | Board opened read-only (snapshot / live session read-only); cut on copies; new merged project in the request folder; re-cut moves old files to `_work/history/<time>/` (never deleted). |
| III Defaults | Every default from `templates/autocut_template.csv`; NEW rows: `setup.solution_mode`, `setup.multi_freqs`, `setup.via_mesh_3d`, `setup.via_num_sides`, `sweep.distribution`, `sweep.ranges`, `sweep.use_q3d_dc`, `airbox.dielectric_horizontal`, `airbox.z_sync`, `component.die_type`, `component.die_orientation`, `component.die_height_mm`, `component.port_location`. The page gets defaults from the template (never hard-coded in JS). |
| IV Guides | `guides/interface_sim.md` rewritten for the fixed process (texts pasted verbatim); prompt `interface-sim` updated. |
| V Regression | `tests/regression.py` + `tests/isim_check.py` (old tools) must PASS unchanged; new `tests/config_flow_check.py` on a board1 copy. |
| VI Encoding | all files UTF-8, written by Python; no spaces in created paths (folder names validated). |
| VII Contracts | `contracts/config-flow.md` lists every new / changed public function; validation at entry with `CopilotInputError`; offline tests for pure logic (model, read, answers, layout paths). |
| VIII Layers | pure logic `interface_sim/config/model.py`, `answers.py`; EDB / snapshot code `config/data.py`; page rendering `config/page.py` + `config/assets/`; flow `config/flow.py`; server / CLI thin. |
| IX Stable interface | tool names kept; 3 tools ADDED; request folder layout changes for new requests only (old ones readable) → MAJOR 5.0.0 (workflow change). |
| X Catalog | see Tool catalog check. |

## Tool catalog check

| Tool | New / changed | Kind | Safety | Gate | Notes |
|---|---|---|---|---|---|
| `isim_config` | NEW | process | copy (writes only the request folder) | – | review (if not current) + snapshot data + config.html; returns M1 `answer_md`; long → task |
| `isim_config_check` | NEW | process | copy | – | reads saved config, validates; errors → M2; valid → previews of every channel with its config → Q2 `answer_md` |
| `isim_go` | NEW | process | copy (copies of the board + new project in the request folder) | `user_approved_cut` | confirm + cut + ends + apply + merge + channel folders; M3; long → task |
| `isim_start` | changed | process | copy | – | request id `<board>_<time>`, `_work/` layout |
| others `isim_*` | unchanged API | | | | work on both layouts through `request.work_dir` / `iface_dir` |

Workflows: team workflow `workflows/interface-sim.md` (if present) updated to the new steps; `PROCESS_GUIDES` maps the
3 new tools to guide `interface_sim`.

## Project Structure

### Documentation (this feature)

```text
specs/038-cut-config-html/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/config-flow.md
├── mock/ (approved mocks)
└── tasks.md
```

### Source Code

```text
aedt_copilot/interface_sim/
├── request.py          + layout 038: work_dir(), channel folder map, request id <board>_<time>, registry both layouts
├── user_settings.py    path() through work_dir
├── merge.py            + run_new_project(): merge into <request>/<request_id>.aedt (created when missing)
├── answer.py           unchanged (old flow)
└── config/             NEW package (feature 038)
    ├── __init__.py
    ├── model.py        PURE: fields, defaults from P, validation, state -> (content, structural, values, handling,
    │                   component model, folder) ; sweep / setup / extents rules ; settings key
    ├── answers.py      PURE: M1 / Q1 / M2 / Q2 / M3 texts (VI + EN)
    ├── data.py         EDB / snapshot: extents per type x factor (final, with end GND rule), layer copper SVG
    │                   paths, end pads + unusual cases + options (read-only)
    ├── page.py         build the HTML (template + JSON data + JSON state), parse a saved page (state JSON)
    ├── read.py         find the saved page (request folder, Downloads), newest with the request id
    ├── flow.py         config(), check(), go() (orchestration over content / review / cut_preview / cut / ends /
    │                   apply / merge), publish channel folders
    └── assets/page.html, page.css, page.js   (from the approved mock)
aedt_copilot/cut_board/
├── cutter.py           apply_setup: solution mode single / multi, via 3D mesh + sides; apply_sweep: ranges
│                       (linear step / count / log), Q3D DC; apply_airbox: dielectric padding, z sync;
│                       per-end component model (die type / orientation / height, ball shape / ratio / height /
│                       material, port location centre / end)
└── merge.py            merge_designs(create_if_missing=True)
mcp_server/server.py    3 new tools (thin)
aedt_copilot/catalog/tools.py  3 entries
templates/autocut_template.csv  new rows (Principle III)
guides/interface_sim.md, prompts/interface-sim.md
tests/unit/test_config_*.py ; tests/config_flow_check.py
```

**Structure Decision**: new sub-package `interface_sim/config/` keeps the 038 process apart from the per-step modules
it orchestrates.

## Design decisions (details in research.md)

1. **One editable page per request**: `<request>/config.html` with one tab per channel (channel folders do not exist
   before the user names them). After `isim_go`, each channel folder gets a READ-ONLY `config.html` (same page, one
   channel, Save hidden, approval block). FR-036's request top level therefore also lists `config.html`.
2. **Save**: Chrome / Edge `showSaveFilePicker` (suggested `config.html`, the page shows the path to choose; the handle
   is kept so later Saves overwrite silently); other browsers → download. The saved page embeds its state as
   `<script type="application/json" id="cfg-state">` plus `<meta name="aedt-copilot-request">`. The reader takes the
   newest of `<request>/config.html` and `~/Downloads/config*.html` whose request id matches and whose `saved_at` is
   set.
3. **Picture data** from the layout snapshot (027 / 029): extents via `open_for_preview` + `cutter.cut_extent`
   (strict=False) per type × factor 0.02..0.20; copper via `open_for_region` + `extract_region` → shapely → SVG paths
   (simplify 0.01 mm). End pads + unusual classification on the live board read-only (one session).
4. **Mapping**: Auto Generate Extent → `structural` (cutout.* / cleanup.* / series.*) + content nets (Include);
   Component Model → `component.*` per end (stored as `handling`-like `component_model` {refdes: {...}}) + solder ball
   rows; Analysis Setup → setup.* / sweep.* (ranges JSON); HFSS Model Extents → airbox.*; unusual choices → `handling`;
   folder → channel folder map. `sweep.start/stop/step` = first / last range (old keys kept for old code paths).
5. **Approval binding**: Q2 shows previews computed with the saved config (`cut_preview.preview(structural=...)`).
   `isim_go` checks the config file hash and every channel's preview key = key of the config → else refuses (config
   changed after Q2).
6. **Folder layout 5.0.0**: `<request>/_work/` = request.json, user_settings.json, board_nets.json, netlist.json, ...;
   channel internal folder = `<request>/_work/<name>/` until the folder is named, then `<request>/<folder>/_work/`
   (moved at `isim_config_check`, map in request.json `channel_folders`). `isim_go` moves the final `.aedb` to
   `<request>/<folder>/<folder>.aedb`, the merge prepares `<folder>.aedt` beside it, copies `review.html`, writes
   `config.html`, and creates `<request>/<request_id>.aedt` (+ `.aedb`) with one design per channel named `<folder>`.
7. **Unusual cases** known before the cut (no GND pin on the board, connector handling, unusual pads of the source
   board) are choice fields; cases that only the cut reveals use the default handling and are listed in M3.

## Complexity Tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Principle I text lists gates A–D | the user asked for ONE approval (FR-005, FR-035) | keeping A + B as separate chat questions contradicts the agreed fixed flow; owner amends the constitution |
| `config.html` at request top level (FR-036 list) | channel folders are named inside this page | per-channel files cannot exist before the names |
| Process tools (`isim_config` / `_check` / `_go`) | the fixed flow must run identically every time | a workflow file alone cannot guarantee identical texts / order; tools stay thin wrappers over package steps |
