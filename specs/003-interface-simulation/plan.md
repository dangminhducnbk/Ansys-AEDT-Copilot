# Implementation Plan: Interface Simulation

**Branch**: `003-interface-simulation` (work on `main`) | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

**Input**: `specs/003-interface-simulation/spec.md` (clarified 2026-11-05)

## Summary

New user process "interface simulation" beside the existing cut-board workflow: schematic/BOM → markdown (once) →
per interface: agree content → cut (stage 1, on a copy) → end check + proposed settings → agree → apply (stage 2) +
self-check → merge all into the engineer's main workspace → (on request) copy to the remote simulation folder and
solve files one by one. Split agreed 2026-11-04/05: **tools measure and execute, the agent decides with the engineer
via the guide `interface_sim`**; unknown cases come back as `unusual` with numbers, never a silent default.
Key technical move: split today's one-pass `cutter._cut` into `cut_stage` (cutout, heavy, ~90 % of time) and
`apply_stage` (components, cleanup, ports, solder ball, setup, sweep, airbox) so settings can be agreed AFTER the cut
and re-applied without re-cutting; `cut_channel` = `cut_stage` + `apply_stage` with identical results.

## Technical Context

**Language/Version**: Python 3.12 (repo `.venv`)

**Primary Dependencies**: pyedb 0.85 (.NET), pyaedt 1.9.0 (gRPC to remote AEDT), openpyxl (BOM .xlsx), mcp<2 —
no new dependency

**Storage**: JSON state + markdown files under `<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/`

**Testing**: offline `unittest` (`tests/unit/`), AEDT `tests/regression.py` (cut identical), new
`tests/isim_check.py` (board1 two interfaces end-to-end, on copies)

**Target Platform**: Windows PC (cut, merge), remote Windows server with AEDT 2026 R1 (solve)

**Project Type**: Python package + CLI + MCP server (stdio)

**Performance Goals**: re-apply settings ≤ 2 min per interface on board1 (no re-cut); agent time per interface < 10 min

**Constraints**: Principles I-IX; old tools / Excel / prompts unchanged; engineer's files never written except the
merge into the main workspace (after backup) ; one EDB open per process; requires feature 002 (`core/`) first

**Scale/Scope**: ~10 new MCP tools, new package `aedt_copilot/interface_sim/` (~10 modules), cutter split, 1 guide,
1 prompt

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I Gates in code | 4 gates checked by the server against `state.json` step + flag: content → cut, settings → apply, merge, run | PASS |
| II Data safety | source board copied per interface; workspace backup before merge; sim dir: new sub-folder per run; never delete locks | PASS |
| III Single source of defaults | settings table = `templates/autocut_template.csv` (+ new `interface_sim.*` rows in the same template, job scope) | PASS |
| IV Rules in guides | `guides/interface_sim.md` (+ `prompts/interface-sim.md`) holds every agreed rule | PASS |
| V Regression | `tests/regression.py` identical after cutter split; new `tests/isim_check.py`; minor bump 0.6.0 | PASS |
| VI Encoding | markdown / JSON written UTF-8 by Python; agent writes markdown through a tool, not PowerShell | PASS |
| VII Contracts | `contracts/` for every new public function and MCP tool; `CopilotInputError` from `core` | PASS |
| VIII Package by function | new `interface_sim/` package; MCP tools thin (args + gate → CLI subprocess) | PASS |
| IX Stable interface | no existing tool / guide / prompt / Excel / folder changed; `cut_channel` signature + results unchanged | PASS |

Post-design re-check: PASS (no new violation; Complexity Tracking below).

## Design

### Process ↔ tools

| Step | Agent does (guide) | Tool (new, MCP) | Gate / state |
|---|---|---|---|
| 0 start | collect workspace `.aedt`, board `.aedb` (default = workspace's), stackup, schematic PDF, BOM | `isim_start` | creates request, `state=started` |
| 0 schematic | BOM parsed by code; agent reads PDF itself (Claude reads PDFs), fills the fixed markdown template, sends it | `isim_bom`, `isim_save_schematic`, `isim_schematic_status` | reuse when source fingerprints equal |
| 1 content | turns engineer's words into refdes / nets; shows board facts + diffs; corrects with engineer | `isim_trace` (board facts + schematic diff + structural settings `cutout.*`) | — |
| 1 confirm | after explicit go | `isim_confirm_content(user_confirmed_content=true)` | GATE A → `content_agreed` |
| 2 cut | one sub-agent per interface (when the client supports it) | `isim_cut` (background, copy + `cut_stage`) | needs `content_agreed` → `cut` |
| 2 check | explains ends, unusual cases, options | `isim_check_ends` → end table + proposed settings table | → `ends_checked` |
| 2 agree | edits values with engineer; tool validates | `isim_validate_settings` | — |
| 2 apply | after explicit go | `isim_apply(user_agreed_settings=true)` (background, copy of stage-1 + `apply_stage` + self-check) | GATE B → `applied` |
| 3 status | table of all interfaces | `isim_status` | — |
| 3 merge | after explicit go | `isim_merge(user_approved_merge=true)` | GATE C → `merged` |
| 4 run | only on request; asks sim dir + server | `isim_run(user_requested_run=true)`, `isim_run_status` | GATE D → `run_*` |

Sub-agents: the guide tells the main agent to start one sub-agent per interface for steps 2 cut → check (Claude Code /
Cowork); a sub-agent never asks the engineer, it returns questions + tables to the main agent. Clients without
sub-agents run interfaces one by one. Isolation is guaranteed by the tools, not by the client: each interface has its
own folder, own copy of the source and its own lock file (`<iface>/.busy`), so two sub-agents cannot write the same
files.

### Folder layout (per request)

```
<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/
  request.json            workspace, board, stackup, schematic, bom, created
  schematic.md            agent-written, fixed template (tables parsed by code)  + schematic.sources.json
  bom.json                parsed BOM
  <iface>/
    state.json            step, content, settings, unusual handling, results, history (time + step)
    content.md            agreed content (engineer-readable)
    _src/<board>.aedb     copy of the source board (deleted only by the engineer)
    stage1/<iface>.aedb   cut_stage output (+ stage1.json: ends, bga_ends, bodies, sig_pos0, nets)
    ends.json / ends.md   end check
    settings.json / settings.md   agreed settings (P dict + source + reason per key)
    final/<iface>.aedb    apply_stage output (copy of stage1, then applied)
    apply.log  cut.log  result.json
  merge.json   run_<time>.json
```

### Cutter split (Principle IX)

| Today `_cut` step | New function | Uses settings |
|---|---|---|
| open, checks, `bga_ends`, `bodies`, `sig_pos0`, extent, cutout, delete other cells, delete non-kept components | `cut_stage(ch, P_cut, src, cell, dst, version, log)` → saves `dst` + returns `stage1` dict (JSON-safe: bodies bbox, sig_pos0, bga_ends, nets, ends, extent area) | `cutout.*`, `series.keep` |
| series 0 Ω, SMD rebuild, cleanup, BGA rebuild, ports, pin shift, solder ball, setup, airbox, save, metrics, check | `apply_stage(stage1, P, aedb, log)` (opens the copy writable) | `series.*`, `port.*`, `cleanup.*`, `solder_ball.*`, `setup.*`, `sweep.*`, `airbox.*` |
| `cut_channel(...)` | unchanged signature: `cut_stage` then `apply_stage` **in the same open EDB** (no save/reopen between) → identical to today | all |

Interface sim calls the two stages separately (save + reopen between). Proven identical by `tests/isim_check.py`
comparing metrics of the two-stage path with the reference of the one-pass path; if they differ beyond tolerance,
fallback documented in research R2.

### End check (code measures, agent decides)

Per end component on the stage-1 design: type (`bga`, `through_hole`, `smd`, `smd_via_in_pad`, `connector`?,
`unknown` from `end_type` + part name / pin count heuristics), pins, signal pins, GND pins within
`cleanup.bga_gnd_pin_keep_dist_mm` / `port.smd_gnd_search_margin_mm` of each signal pin, pad shape (circle / rect /
oval / polygon) + size, solder ball present, via-in-pad. `unusual` list: rule ids `no_gnd_near_signal`,
`non_round_pad_bga`, `connector_end`, `unknown_type`, `pad_size_mismatch` with measured values. Handling options
offered = only operations that exist today (`smd_rebuild`, `keep_component`, `no_solder_ball`, `stop_interface`);
new handling rules are later features (old roadmap 011-013).

### Settings table

Rows = template rows of scope `channel` (same keys as the channel Excel) + proposed value (template default, or
measured: e.g. solder-ball diameter from pad short side shown for information) + unit + source + reason; mandatory
sweep rows empty until the engineer fills them. Validation = `cut_board.config.build_params` (same rules and messages
as the Excel flow). Structural rows (`cutout.*`, `series.keep`) are agreed at step 1 because stage 1 uses them;
changing them later re-runs `isim_cut`.

### Merge

Reuse `cut_board.merge` internals with a target project = engineer's workspace `.aedt` and sources =
`<iface>/final/<iface>.aedb`; same backup, `_vN` naming, compare, lock check. Refactor `merge.merge()` into
`merge_designs(target_aedt, sources{name: aedb}, out_dir, port, log)` + thin `merge(job_id, ...)` (unchanged API).

### Remote run

Copy `<workspace>.aedt` + `<workspace>.aedb` (+ results folders excluded) into `<sim_dir>/<request_id>_<time>/`
(UNC or mapped path given by the engineer; never overwrite). Solve: pyaedt `Desktop(machine=<server>, port=<port>,
new_desktop=False)` to an AEDT gRPC session the engineer started on the server (`ansysedt -grpcsrv <port>`); open the
project by the SERVER-side path (`sim_dir_server` given by the engineer or mapping in `config.yaml`
`sim_servers`), then `analyze_setup` design by design in the given order, `save_project` after each; status JSON per
design. Background process, `isim_run_status` reads it.

## Project Structure

### Documentation (this feature)

```text
specs/003-interface-simulation/
├── spec.md  plan.md  research.md  data-model.md  quickstart.md  (tasks.md next)
├── checklists/requirements.md
└── contracts/ isim-request.md isim-schematic.md isim-content.md isim-cut.md isim-ends.md
               isim-settings.md isim-merge.md isim-run.md mcp-tools.md cutter-split.md
```

### Source Code (repository root)

```text
aedt_copilot/interface_sim/        NEW
├── __init__.py
├── request.py        start, paths, state.json read/write (atomic), step machine, busy lock
├── schematic.py      BOM parse (xlsx/csv, column mapping), markdown template, save + parse tables, fingerprints
├── content.py        trace (inspect_board.trace_channel + propose.group_diff), schematic diff, confirm
├── cut.py            copy source, run cut_stage in worker process
├── ends.py           end check (measure + unusual rules)
├── settings.py       proposed table, validate (build_params), save
├── apply.py          copy stage1 → final, apply_stage, self-check readback
├── merge.py          → cut_board.merge.merge_designs
├── run.py            copy to sim dir, remote solve loop, status
└── report.py         markdown tables (content.md, ends.md, settings.md, status)
aedt_copilot/cut_board/cutter.py   split: cut_stage / apply_stage; cut_channel unchanged
aedt_copilot/cut_board/merge.py    merge_designs + merge (unchanged API)
aedt_copilot/__main__.py           new sub-commands `isim-*` (thin)
mcp_server/server.py               new tools isim_* (args + gates → CLI)
guides/interface_sim.md  prompts/interface-sim.md   NEW
templates/autocut_template.csv     + rows interface_sim.* (job scope): end check distances, run options
tests/unit/test_isim_*.py  tests/isim_check.py
```

**Structure Decision**: new feature package on top of `core/` (002) and `cut_board`; MCP / CLI thin.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| `cutter._cut` split inside a feature that is not a pure restructure | settings must be agreed after the cut (spec US2) without re-running a 5-min cutout | full re-cut per settings change: 5-6 min each time; cut after settings: contradicts the agreed order (cut → check → settings) |
| ~10 new MCP tools | one tool per gate / step keeps gates checkable in code (Principle I) | one generic `isim(step, ...)` tool hides gates from the server and the client UI |
| Stage-1 copy of a 240 MB board per interface | sub-agents must not open the same EDB writable; today's cut opens the source writable (`readonly=False`) and the cutout with `output_aedb_path` was only proven that way | read-only cutout of a shared source is unproven on PyEDB 0.85 (research R3); a copy costs ~10 s and disk only |
