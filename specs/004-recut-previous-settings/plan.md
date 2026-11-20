# Implementation Plan: Re-cut from previous settings

**Branch**: `main` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Summary

Add a re-cut path to the interface-simulation process (003): find an earlier run of an interface (registry, request
id or a `user_settings.json` path), re-trace it on the current board, show only differences, then go through gates
A-B-C with the old content / handling / values pre-filled. All agreed data of a request lives in ONE
`user_settings.json` in the request folder, which replaces `settings.json` and `settings.md` per interface. A new team
template row `setup.arc_step_deg` (default 10) sets the HFSS arc step in `cutter.apply_setup` (both flows) and is read
back by the self-check. Version 0.7.0 (minor: arc step changes results).

## Technical Context

| Item | Value |
|---|---|
| Language / runtime | Python 3.12 (repo `.venv`), pyedb 0.85 (.NET), pyaedt 1.9.0, mcp<2 |
| New code | `aedt_copilot/interface_sim/user_settings.py`, `aedt_copilot/interface_sim/recut.py` |
| Changed code | `interface_sim/settings.py` (save → user_settings), `content.py` (confirm → user_settings), `ends.py` (handling compare on re-cut), `request.py` (`OUTPUTS`, registry `workspace`), `apply.py` (self-check arc step), `api.py` (ops), `cut_board/cutter.py` (`apply_setup` arc step), `cut_board/config.py` (range rule), `mcp_server/server.py` (2 new tools), template row, guide |
| Storage | JSON / markdown files in the request folder; registry `~/.aedt_copilot/isim_requests.json` |
| Tests | `unittest` offline (`tests/unit/`); AEDT: `tests/regression.py`, `tests/isim_check.py` on a board1 copy (user OK first) |
| PyEDB arc step API | `setup.curve_approx_settings.arc_angle` — str `'30deg'` default; set `'10deg'`, saved and read back `'10deg'` (research R1, probed 2026-11-06 on a board1 cut copy) |
| Performance | re-trace = same as `isim_trace` (~1 min on board1); file work negligible |

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I Gates in code | re-cut uses the same gates A / B / C in the server; no gate skipped when there is no difference (go still required) | PASS |
| II Data safety | re-cut always in a NEW request; old request folder only read; `user_settings.json` written atomically; reset keeps the replaced section in `replaced[]` (nothing lost) | PASS |
| III Single source of defaults | arc step default only in `templates/autocut_template.csv`; old values come from the file, new rows from the template | PASS |
| IV Rules in guides | `guides/interface_sim.md` gets the re-cut section + "như lần trước" rule | PASS |
| V Regression | new reference value `arc_step_deg` in `tests/reference/CPHY_U14_U26.json`; `isim_check` re-cut scenario; minor bump 0.7.0 | PASS |
| VI Encoding | JSON UTF-8 via `request.wjson` | PASS |
| VII Contracts | `contracts/` for every new / changed public function and MCP tool; inputs validated with `CopilotInputError` | PASS |
| VIII Package by function | new modules inside `interface_sim/`; MCP tools thin | PASS |
| IX Stable interface | no tool / prompt / Excel / folder renamed or removed; new template row = addition; `settings.json` / `settings.md` were 0.6.0 outputs of a new process (not part of the Excel flow) — replacement agreed by the user 2026-11-06 | PASS (see Complexity Tracking) |

Post-design re-check: PASS.

## Design

### Process (re-cut) ↔ tools

| Step | Agent (guide) | Tool | Gate / state |
|---|---|---|---|
| 0 find | user says "như lần trước" / id / path | `isim_previous(name, workspace)` → list newest first | — |
| 0 start | new request for the workspace (as 003) | `isim_start` | `started` |
| 1 load + re-trace | — | `isim_recut(request_id, name, source)` → old content, re-trace with old ends / nets, `recut_diffs`, `content_md` | state `recut_from` set |
| 1 confirm | 0 diffs → ask for go; else resolve each diff | `isim_confirm_content(user_confirmed_content=true)` (unchanged) | GATE A → `content_agreed`; writes `user_settings.json` |
| 2 cut | as 003 | `isim_cut` | `cut` |
| 2 ends | show `handling_compare` | `isim_check_ends` (adds `handling_compare`, settings pre-filled from source) | `ends_checked` |
| 2 apply | go | `isim_apply(user_agreed_settings=true)` (unchanged API) | GATE B → `applied`; writes `user_settings.json` |
| 3 merge | as 003 | `isim_merge` | GATE C |

### Sources of a previous run (R2)

1. `user_settings.json` (0.7.0+) of a request folder or any path (copied from another PC).
2. 0.6.0 request folder without `user_settings.json`: built from `<iface>/state.json` (`content`, `settings.values`,
   `settings.handling`) — the engineer's real 003 runs keep working.
Search (`isim_previous`): registry entries whose `request.json.workspace` equals the given workspace (normalised, case-
insensitive) and that contain the interface name; output request id, created, last step, sweep start / stop / step.

### Re-trace and difference (R3)

`content.trace(request_id, name, refdes=[comp_a, comp_b], nets=old nets)` on the current board gives new facts.
`recut.diff(old, new_facts, old_board_fp, new_board_fp)` (pure) → items: `net_added`, `net_removed`, `end_missing`,
`end_pins_changed`, `series_added`, `series_removed`, `series_value_changed`, `diff_group_changed`,
`board_file_changed`, `schematic_resolution_stale`. Proposal content = old content restricted to what still exists;
every difference must have a resolution before gate A (same rule as 003 schematic diffs: `content.recut_diffs` with
`resolution`).

### Handling compare (R4)

`recut.compare_handling(old_handling, new_ends)` (pure) per end: `kept` (old option still in the new `options`),
`not_needed` (end no longer unusual), `needs_choice` (new unusual case, or old option not allowed). Pre-fill
`handling` with `kept` items only.

### Settings pre-fill

`settings.proposal(state, ends, values=old_values)` already shows given values; `source` = `previous run <id>` for
keys from the old run, `team default (new)` for template keys missing in the old run; old keys not in the template →
`dropped` list (not applied).

### `user_settings.json` (data-model)

One per request. Written by `user_settings.update(request_id, name, section)`: gate A writes `content` +
`structural`; gate B writes `values` + `handling`. Atomic write (`request.wjson`). `settings.save` no longer writes
`settings.json` / `settings.md`; its table is still returned (`settings_md`) and shown in chat. `request.OUTPUTS`
drops the two names. Reset of an interface (content change) moves its section to `replaced[]`.

### Arc step (R1)

Template row `setup.arc_step_deg,Arc step size,deg,num,channel,no,10,HFSS circle and arc approximation (Advanced
Meshing)`. `build_params` rule: 0 < value ≤ 90. `cutter.apply_setup`: `st.curve_approx_settings.arc_angle =
f"{v:g}deg"` (log on error, like other setup items). `apply.read_setup` reads `arc_angle` (`'10deg'` → 10.0);
`expected_setup` adds it. Old Excel flow gets the row in the Settings matrix automatically (channel scope).

## Project Structure

### Documentation (this feature)

```
specs/004-recut-previous-settings/
  spec.md  plan.md  research.md  data-model.md  quickstart.md  tasks.md
  contracts/ isim-user-settings.md  isim-recut.md  arc-step.md  mcp-tools.md
```

### Source Code (repository root)

```
aedt_copilot/interface_sim/user_settings.py   NEW  load / validate / update / from_state
aedt_copilot/interface_sim/recut.py           NEW  previous / source / diff / compare_handling / start
aedt_copilot/interface_sim/{settings,content,ends,request,apply,api}.py   changed
aedt_copilot/cut_board/{cutter,config}.py      arc step
mcp_server/server.py                           + isim_previous, isim_recut
templates/autocut_template.csv                 + setup.arc_step_deg
guides/interface_sim.md                        re-cut section, file list
tests/unit/test_isim_user_settings.py, test_isim_recut.py, test_arc_step.py   NEW
tests/unit/_golden.py                           ADDED keys (per key, not per section)
tests/reference/CPHY_U14_U26.json, tests/regression.py, tests/isim_check.py   arc step + re-cut scenario
VERSION 0.7.0, CHANGELOG.md, README.md, CLAUDE.md §3/§8
```

## Complexity Tracking

| Deviation | Why | Simpler alternative rejected |
|---|---|---|
| `settings.json` / `settings.md` no longer written (output change of 0.6.0) | user requirement "không nên tạo ra quá nhiều file", agreed 2026-11-06 | keep both + new file: more files, user said no |
| `_golden.ADDED_PREFIXES` becomes per-key | arc step adds a key inside the existing `setup` section; stripping the whole section would hide real changes | add a section `mesh.*`: breaks the agreed name `setup.arc_step_deg` |
