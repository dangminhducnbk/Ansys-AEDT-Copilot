# Data Model: Atomic design tools

## Operation request

| Field | Type | Rule |
|---|---|---|
| op | str | registry NAME: `read`, `setup`, `sweep`, `airbox`, `ports`, `solder_ball` |
| board | str | existing `.aedb` (or `.aedt` → `.aedb`), no lock |
| cell | str | "" = first cell |
| values | dict | template keys of the op's sections (`setup.*` + `sweep.*` / `sweep.*` / `airbox.*` / `solder_ball.*`) |
| targets | dict | `setup_name`; `refdes` list; `nets` list; `replace` bool |
| in_place | bool | false = copy |

## Operation report (`<result>.design_tools.md` + returned JSON)

`{op, source, result, backup, in_place, changes[{item, old, new}], skipped[{item, reason}], mismatches[{item,
expected, got}], ok, seconds, time}`. Markdown: title, paths, changes table, skipped table, read-back result.
Several operations on the same result append sections to the same markdown file.

## Snapshot (`read`)

`{setups: {name: {setup.* / sweep.* values}}, airbox: {airbox.*}, ports: [{name, refdes, net}], solder_balls:
{refdes: {diameter, height, shape}}}`.
