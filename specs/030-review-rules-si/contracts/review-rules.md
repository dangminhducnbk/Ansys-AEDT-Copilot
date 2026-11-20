# Contract: review rules 030 + stackup table

## Check modules (028 interface)

`pair_skew`, `pair_gap`, `coupling`, `plane_edge`, `via_count`, `stackup_width` in `aedt_copilot/review_checks/`:
NAME, ORDER (50..100), TITLE, SEVERITY_RULE, `run(cc) -> {items, data}`, `REPORT` for every finding name.
Findings use the cut_board/review.py dict (metres): check, severity, net, layer, ref, x, y, value, bbox
(+ start / end / len_mm for runs, used for via findings).

## Template rows (job scope, `review.*`)

| Key | Default | Rule |
|---|---|---|
| `review.pair_skew_mm` | 0.127 | 1 |
| `review.pair_gap_ratio` | 1.5 | 2 |
| `review.pair_gap_min_len_mm` | 0.5 | 2 |
| `review.coupling_gap_factor` | 3 | 3 |
| `review.coupling_min_len_mm` | 2.5 | 3 |
| `review.plane_edge_factor` | 3 | 4 |
| `review.plane_edge_min_mm` | 0.2 | 4 |
| `review.plane_edge_min_len_mm` | 0.5 | 4 |
| `review.via_count_max` | 2 | 5 |
| `review.stackup_tol_mm` | 0.01 | 6 |
| `review.neckdown_zone_mm` | 1.0 | 2, 3, 4, 6 |

## review_checks._stackup

- `path(aedb)` → `<board dir>/Ansys AEDT Copilot/stackup/<stem>.json`.
- `load(aedb)` → table or None. `table_hash(aedb)` → sha1[:16] or None.
- `validate(table, layers)` → normalized table; `CopilotInputError` on unknown layer / non-positive or missing values.
- `save(aedb, table, source_file, layers)` → path (old file moved aside).
- `template(layers)` → empty table.

## MCP tool `review_stackup_table(board, op="get", table="", source_file="", cell="", user_confirmed_table=False)`

- `get` → `{path, table | None}`; `template` → `{layers, table}` (board signal layers from the snapshot index or EDB);
  `save` → refused unless `user_confirmed_table=true`; → `{path, table}`.
- CLI `stackup-table --op=get|template|save --args-file=<json {board, cell, table, source_file}>`.
