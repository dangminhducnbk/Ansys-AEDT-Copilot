# Data model: 036

## Finding (cut_board/review.py, review_checks items)
| Field | Change |
|---|---|
| `status` | NEW: "NOT OK" / "OK" (from the rule's threshold) |
| `severity` / `severity_suggested` | REMOVED |
| other fields (check, net, layer, ref, x, y, value, …) | unchanged |

## Point (merged NOT OK findings at net + position)
`{id, net, x, y, main, items, status: "NOT OK"}` (no severity).

## Channel findings (review_checks/_verdict.channel_findings)
`{not_ok: int (points), by_check: {check: int (NOT OK findings)}, failed_checks: [...], incomplete: bool}`.
Stored in review.json / review record as `counts = {"NOT OK": n}` + `by_check`.

## Review record (`_store`)
SCHEMA 4. Records with schema < 4 are not reused.

## Approval (`user_settings` `review.approval`)
`counts = {"NOT OK": n}`, `by_check`, rest unchanged.

## Rule steering header
Fields: id, findings, section, **not ok when**, thresholds, limit key, code. (`severity` accepted as an alias for
personal rules.)

## Netlist (`<request>/netlist.json`)
```
{source, format: "protel2" | "telesis", design, parsed_at,
 components: {refdes: {part, value, pins: n}},
 nets: {name: [[refdes, pin], ...]},
 warnings: [...]}
```

## Schematic data (schematic.load_parsed)
`{components, nets {name: {pins, page}}, unreadable, bad_rows, source: "netlist" | "pdf"}`.

## Compare result (content.compare)
`{diffs: [{item, kind: pin_mismatch | missing_on_board | series_value, board, schematic, probable: false}],
  board_only: [{item, pins}], renamed: [{board, schematic}]}`.
State keeps `schematic_diffs` (= diffs) and `schematic_info` (board_only, renamed).

## Channel answer (interface_sim/answer.build)
`{answer_md, answer_image}` or `{answer_md: None, reason}`.
