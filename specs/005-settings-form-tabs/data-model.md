# Data Model: Full settings form

## Setting descriptor

| Field | Type | Rule |
|---|---|---|
| key | str | channel-scope template key |
| label | str | template `Parameter` |
| unit | str | template `Unit` |
| type | `num` / `bool` / `text` / `list` | template `Type` |
| choices | list \| null | from Description `a \| b \| c`; bool → `[true, false]` |
| default | value \| null | coerced template default; null for mandatory rows without default |
| value | value \| null | proposal value (team default / previous run / engineer) |
| source | str | as `settings.proposal` (`default`, `engineer`, `previous run <id>`, `team default (new)`, `content`) |
| group | str | key prefix; order of first appearance in the template |
| mandatory | bool | template `Mandatory` |
| locked | bool | `cutout.*` or `series.keep` |
| locked_reason | str \| null | "set in content (Gate A); change = back to content + re-cut" |
| desc | str | template Description |

## Tab

`{name, step, enabled, reason, applied, recut_from, descriptors[], unusual{refdes: {rules[], options[]}},
handling{refdes: option}}`; `enabled` = step `ends_checked` (same rule as `isim_apply`); applied / merged tabs are
disabled with reason "already applied".

## Form submit (agent → `isim_validate_form`)

`{"<interface>": {"values": {key: value}, "handling": {refdes: option}}}`; keys ⊆ editable descriptors.
