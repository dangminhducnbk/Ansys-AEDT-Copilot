# Data Model: Re-apply simulation settings

## Settings group

| Group | Key prefixes | After apply |
|---|---|---|
| cut | `cutout`, `series`, `cleanup`, `port`, `solder_ball` (+ end handling) | locked (change = re-cut) |
| sim | `setup`, `sweep`, `airbox` | editable (re-apply, Gate B) |

## Interface state additions (`<iface>/state.json`)

| Field | Type | Rule |
|---|---|---|
| reapplied | list | `[{time, values, backup, self_check_ok}]`, one per re-apply |
| result_history | list | previous `result` summaries (aedb, warnings, self_check) |
| merged_before | list | earlier `merged` records when a merged interface was re-applied |

## `user_settings.json` addition

`interfaces[name].history[]` = `[{values, handling, settings_agreed_at}]` (oldest first), pushed when `values` are
replaced.

## Files

`<iface>/final/<name>.aedb` (current), `<iface>/final/<name>_old_<time>.aedb` (backup per re-apply), `result.json`
(current).
