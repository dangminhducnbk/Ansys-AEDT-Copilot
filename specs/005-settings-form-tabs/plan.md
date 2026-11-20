# Implementation Plan: Full settings form with tabs and "Set default"

**Branch**: `main` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Summary

The MCP server gives the agent a complete, template-driven description of the Gate B settings of every interface of a
request (`isim_settings_form`): one tab per interface, every channel-scope template row as a setting descriptor
(key, label, unit, type, choices, team default, proposed value, group, mandatory, locked + reason), the unusual-end
choices and the pre-filled handling. The agent renders it as a widget (tabs, groups, "Set default" per tab / all tabs,
"Copy to all tabs", submit) or, without widgets, as the full grouped table. The submitted form is validated per
interface in one call (`isim_validate_form`); Gate B approval stays per interface in `isim_apply` (unchanged).
Version 0.8.0.

## Technical Context

| Item | Value |
|---|---|
| Language / runtime | Python 3.12 (repo `.venv`), mcp<2 |
| New code | `aedt_copilot/interface_sim/form.py` (descriptors, tabs, grouped table, multi-validate) |
| Changed code | `interface_sim/api.py` (ops `form`, `validate_form`), `mcp_server/server.py` (2 tools), `templates/autocut_template.csv` (choices text of 2 airbox rows), guide / prompt |
| Rendering | client side (Claude desktop `show_widget`: HTML + `sendPrompt(text)`); server returns data only (research R1) |
| Storage | none new: agreed values still go to `user_settings.json` at `isim_apply` (feature 004) |
| Tests | `unittest` offline (`tests/unit/test_isim_form.py`); AEDT: SC-004 on a board1 copy (user OK first) |
| Performance | descriptors from the cached template + state / ends files: < 0.1 s per request, no EDB |

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I Gates in code | form = input only; `isim_apply(user_agreed_settings=true)` per interface unchanged; `isim_validate_form` never applies | PASS |
| II Data safety | read-only tools; nothing written except the existing apply path | PASS |
| III Single source of defaults | descriptors and "Set default" values come from `templates/autocut_template.csv`; choices from the template Description (`a \| b \| c`) | PASS |
| IV Rules in guides | `guides/interface_sim.md` INPUT FORMS section rewritten for the full form | PASS |
| V Regression | no cut / apply code change; references unchanged; SC-004 check on a board1 copy | PASS |
| VI Encoding | JSON via Python | PASS |
| VII Contracts | `contracts/isim-form.md`, `contracts/mcp-tools.md`; inputs validated with `CopilotInputError` | PASS |
| VIII Package by function | `interface_sim/form.py`; MCP tools thin | PASS |
| IX Stable interface | additions only; Description text of 2 template rows changed (keys / values unchanged) | PASS (Complexity Tracking) |

Post-design re-check: PASS.

## Design

### Setting descriptor (data-model)

Built per channel-scope template row by `form.descriptors(state, ends, values)` on top of `settings.proposal` (same
values / sources as the chat table): `group` = key prefix (`cutout`, `cleanup`, `series`, `port`, `solder_ball`,
`setup`, `sweep`, `airbox`), template order; `choices` = Description parsed when it starts with `a | b | c`
(single-word options), bool → true / false; `default` = coerced template default (None for mandatory sweep);
`value` = proposal value; `source`; `locked` + `locked_reason` for `cutout.*` / `series.keep`.

### Form (one call, all tabs)

`form.build(request_id)` → `{request_id, groups[], tabs[{name, step, enabled, reason, applied, recut_from,
descriptors[], unusual{rd: {rules, options}}, handling{}}], table_md}`. `enabled` = step `ends_checked` (Gate B, same rule
as `isim_apply`); applied / merged and earlier steps are disabled with the step name.

### Client actions (widget, guide rule)

- "Set default" (tab) = every editable descriptor → `default`; mandatory sweep keep the value typed in this widget
  session or stay empty (FR-005). "Set default for all tabs" = same on every enabled tab.
- "Copy to all tabs" = editable non-locked values of the current tab → other enabled tabs; handling stays per tab.
- Submit → `sendPrompt` with JSON `{interface: {values, handling}}` → the agent calls `isim_validate_form`.

### Multi-validate

`form.validate(request_id, entries)` → per interface `settings.validate_for(...)` (existing rules); one interface's
errors never block others; output `{results{name: {valid, errors, table_md}}, all_valid}`.

### Fallback table

`form.table_md(tab)` = full grouped table (group headings, key, label, value, default, unit, source, note); used when
the client has no widget.

## Project Structure

```
specs/005-settings-form-tabs/ plan.md research.md data-model.md quickstart.md contracts/{isim-form.md,mcp-tools.md} tasks.md
aedt_copilot/interface_sim/form.py        NEW
aedt_copilot/interface_sim/api.py         + ops form, validate_form
mcp_server/server.py                      + isim_settings_form, isim_validate_form
templates/autocut_template.csv            Description of airbox.extent_type / dielectric_extent_type = choices
guides/interface_sim.md, prompts/interface-sim.md
tests/unit/test_isim_form.py              NEW
VERSION 0.8.0, CHANGELOG.md, README.md, CLAUDE.md
```

## Complexity Tracking

| Deviation | Why | Simpler alternative rejected |
|---|---|---|
| Description text of 2 airbox rows changed to list choices | template = single source (Principle III); a dropdown needs the allowed values | choices hard-coded in code: a second source of truth |
