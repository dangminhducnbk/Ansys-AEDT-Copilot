# Data Model: Kitchen model

## Utensil (catalog entry)

| Field | Type | Rule |
|---|---|---|
| name | str | MCP tool name (unique) |
| group | str | `board`, `cut`, `design`, `simulation`, `merge`, `review`, `pidc`, `layout`, `kitchen`, `help`, process names |
| kind | `utensil` \| `process` | process = step of an existing process, works only inside it |
| summary | str | one line |
| inputs | list[str] | short names (board .aedb, refdes, nets, values ...) |
| outputs | list[str] | short names (design .aedb, report, JSON) |
| safety | `read` \| `copy` \| `original` \| `workspace` \| `remote` | highest level the tool can reach |
| gate | str \| null | server flag for `original / workspace / remote` (and process gates) |
| condition | str \| null | when the higher level applies (e.g. `in_place=true`) |

## Recipe

| Field | Type | Rule |
|---|---|---|
| name | str | slug `[a-z0-9-]+`, unique per source |
| title | str | short |
| description | str | one line |
| inputs | list[str] | what to ask the engineer |
| guide | str \| "" | legacy guide to follow instead of steps |
| steps | list[{utensil, note?, checkpoint?}] | utensils from the catalog; may be empty when `guide` set |
| source | `team` \| `personal` | from the folder |
| path | str | file path |
| broken | list[str] | step utensils not in the catalog |
| body | str | free text |

## Recipe list entry (`kitchen_recipes`)

`{name, title, description, source, steps (count), checkpoints (count), guide, broken[], path}`.

## New utensil outputs

- `design_trace`: `{comp_a, comp_b, nets[], diff_groups[], series{rd: {nets, part, value}}, end_types{rd: type},
  pins{rd: {pin: net}}}`.
- `design_cutout`: 007 report + `stage1` path, `nets`, `ends`, `bga_ends`.
- `design_end_check`: `{ends{rd: {type, pins, gnd_pins, signal_pins[], solder_ball, via_in_pad, connector,
  unusual[{rule, detail, values, options}]}}}`.
- `design_check`: `{ok, mismatches[{item, expected, got}], ports, signal_pins}`.
- `design_merge`: `merge_designs` output (project, backup, designs, channels{name: state, design, warnings}).
