# Implementation Plan: Re-apply simulation settings after apply

**Branch**: `main` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Summary

Settings are split by template key prefix into a CUT group (`cutout`, `series`, `cleanup`, `port`, `solder_ball` +
end handling) and a SIMULATION group (`setup`, `sweep`, `airbox`). After apply (or merge), `isim_apply` (same tool,
Gate B) accepts a re-apply when only simulation values change: the tool copies `final/<name>.aedb` to
`final/<name>_old_<time>.aedb`, opens the design, deletes the HFSS setup(s) it created and rebuilds setup / sweep /
arc step / airbox with the existing `cutter.apply_setup` / `apply_airbox`, saves, runs the self-check (values read back
+ geometry metrics equal to the previous apply), stores the new values in `user_settings.json` (old ones in the
interface's `history`). A merged interface goes back to `applied` so a new Gate C merge adds a new design. The form
(005) opens applied / merged tabs with the cut group locked. Version 0.9.0.

## Technical Context

| Item | Value |
|---|---|
| Language / runtime | Python 3.12, pyedb 0.85 (.NET), mcp<2 |
| New code | `interface_sim/apply.py` `reapply()`; `interface_sim/settings.py` `group_of()`, `validate_reapply()`; `cut_board/cutter.py` `reapply_sim()` |
| Changed code | `mcp_server/server.py` `isim_apply` (steps applied / merged → op `reapply`), `interface_sim/api.py` (op `reapply`), `interface_sim/form.py` (applied tabs), `interface_sim/user_settings.py` (history), guide / prompt |
| PyEDB | `edb.setups[name].delete()` (attribute seen on `HfssSimulationSetup` 2026-11-06); `create_hfss_setup` + `curve_approx_settings` + `hfss_extent_info` as in 0.7.x (research R1) |
| Tests | `unittest` offline (`tests/unit/test_isim_reapply.py`); AEDT: `tests/isim_check.py --reapply` on a board1 copy (user OK first) |
| Performance | re-apply = open + setup rewrite + save + self-check: ~1 min on board1 (no cutout, no cleanup) |

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I Gates in code | re-apply only through `isim_apply(user_agreed_settings=true)`; server refuses cut-group changes before any CLI call | PASS |
| II Data safety | backup copy `<name>_old_<time>.aedb` before writing; workspace never written by re-apply; nothing deleted | PASS |
| III Single source of defaults | groups derived from template key prefixes; values / defaults from the template | PASS |
| IV Rules in guides | guide line "re-apply any value" replaced by the cut / simulation rule | PASS |
| V Regression | first apply / cut code unchanged; `tests/isim_check.py --reapply` new scenario; minor bump 0.9.0 | PASS |
| VI Encoding | JSON via Python | PASS |
| VII Contracts | `contracts/isim-reapply.md`, `contracts/mcp-tools.md`, form / user_settings changes; CopilotInputError | PASS |
| VIII Package by function | geometry-free rewrite in `cutter.reapply_sim`, orchestration in `interface_sim.apply` | PASS |
| IX Stable interface | no tool renamed; `isim_apply` accepts more steps (addition); Excel flow unchanged | PASS |

Post-design re-check: PASS.

## Design

### Groups

`settings.CUT_PREFIXES = ("cutout", "series", "cleanup", "port", "solder_ball")`, `SIM_PREFIXES = ("setup", "sweep",
"airbox")`; `group_of(key)` → `cut` | `sim`; a channel-scope key in neither → CopilotInputError (test: every template
channel row belongs to exactly one group, so a new prefix forces a decision).

### Validation (`settings.validate_reapply(request_id, name, values, handling=None)`)

Precondition step `applied` or `merged`. Agreed = `state.settings.values` (+ template defaults for keys not given +
structural content values). Errors: cut-group key whose value differs from agreed (`<key>: đã cắt, đã khoá — cut lại
để đổi`), handling different from agreed; then `build_params(agreed cut ∪ new sim)` rules (same messages). Output as
`validate_for` (`valid, errors, table_md, rows, P`).

### Re-apply (`apply.reapply(request_id, name, values, version=None)`)

Inside `request.busy`: validate → copy `final/<name>.aedb` → `final/<name>_old_<time>.aedb` → open writable →
`cutter.reapply_sim(edb, P_old, P_new, log)` (delete setups named `P_old.setup.name` and `P_new.setup.name` if present,
`apply_setup`, `apply_airbox`) → save → metrics (`collect_metrics` + `arc_step_deg`; pin shift kept from the previous
result) → `self_check` → geometry compare with previous `result.json` (ports, components, GND vias, planes) →
`result.json` (previous moved into `result_history[]` of state) → `settings.save` (user_settings: old values pushed to
`history`) → state `applied` (from `merged`: `merged_before` appended, `merged` = None). Failure → `fail()`, backup kept.

### Form (005 change)

`GATE_B_STEPS` += `applied`, `merged`; applied / merged tabs: descriptors with `values = state.settings.values`;
cut-group descriptors `locked`, reason "already cut — locked (re-cut to change)"; tab `reapply: true`; merged note
"re-apply needs a new merge (new design)". "Set default" rule (guide): only unlocked descriptors.

### user_settings history

`update(..., values=...)` when the section already has `values`: push `{values, handling, settings_agreed_at}` to
`interfaces[name].history[]` first. `history` added to the document schema (validated as list).

## Project Structure

```
specs/006-reapply-sim-settings/ plan.md research.md data-model.md quickstart.md contracts/{isim-reapply.md,mcp-tools.md} tasks.md
aedt_copilot/cut_board/cutter.py              + reapply_sim
aedt_copilot/interface_sim/{settings,apply,form,user_settings,api}.py
mcp_server/server.py                          isim_apply accepts applied / merged
guides/interface_sim.md, prompts/interface-sim.md
tests/unit/test_isim_reapply.py               NEW;  tests/isim_check.py --reapply
VERSION 0.9.0, CHANGELOG.md, README.md, CLAUDE.md
```

## Complexity Tracking

None.
