# Data Model: Re-cut from previous settings

## `user_settings.json` (one per request folder)

```json
{
  "format": "aedt_copilot.user_settings/1",
  "tool_version": "0.7.0",
  "request_id": "20261106_101500",
  "workspace": "D:/.../simulation.aedt",
  "board": "D:/.../simulation.aedb",
  "board_fingerprint": {"size": 123, "mtime": 1730000000.0},
  "updated": "2026-11-06T10:30:00",
  "interfaces": {
    "CPHY_U14_U26": {
      "recut_from": {"request_id": "20261105_202026", "interface": "CPHY_U14_U26", "path": "..."} ,
      "content": {"comp_a": "U14", "comp_b": "U26", "nets": [], "diff_groups": [], "series": {},
                  "schematic_diffs": [], "recut_diffs": []},
      "structural": {"cutout.expansion_factor": 0.06},
      "content_agreed_at": "ISO",
      "values": {"sweep.start_ghz": 0, "sweep.stop_ghz": 10, "sweep.step_ghz": 0.1},
      "handling": {"U26": "smd_rebuild"},
      "settings_agreed_at": "ISO",
      "trace_args": {"refdes": ["U14", "U26"], "nets": ["CPHY_B02DEVA_*"]},
      "board_facts": {"components": {}, "nets": {}}
    }
  },
  "replaced": [{"interface": "X", "time": "ISO", "section": {}}]
}
```

| Field | Rule |
|---|---|
| format | exactly `aedt_copilot.user_settings/1` |
| interfaces keys | channel name rules (`request.check_name`) |
| content | same schema as 003 `state.content` (+ optional `recut_diffs`) |
| structural | keys `cutout.*` / `series.keep` of the template |
| values | keys of channel-scope template rows; unknown keys → dropped on load (listed) |
| handling | `{refdes: smd_rebuild | keep_component | no_solder_ball | stop_interface}` |
| recut_from | null or source of the re-cut |
| *_agreed_at | ISO time or null (null = gate not passed) |

## Previous run (output of `isim_previous`)

`{request_id, created, workspace, interface, last_step, failed, error, sweep: {start_ghz, stop_ghz, step_ghz} | null,
source: "user_settings" | "state", path}`

## Re-cut difference (`content.recut_diffs[]`)

`{item, ref, old, new, resolution}`; `item` ∈ `net_added, net_removed, end_missing, end_pins_changed, series_added,
series_removed, series_value_changed, diff_group_changed, board_file_changed, schematic_resolution_stale`;
`resolution` "" until the engineer decides (`keep_old`, `use_new`, `exclude`, free text).

## Handling compare (`isim_check_ends.handling_compare[]`)

`{refdes, old, new_rules[], result: kept | not_needed | needs_choice, options[]}`

## Interface state additions (`<iface>/state.json`)

`recut_from` (same as above, null for a normal run), `recut_diffs`, `recut_old` `{values, handling, dropped,
tool_version}`, `trace_args` `{refdes, nets}`.

## Template row

`setup.arc_step_deg,Arc step size,deg,num,channel,no,10,HFSS circle and arc approximation (Advanced Meshing)`;
rule 0 < v ≤ 90.
