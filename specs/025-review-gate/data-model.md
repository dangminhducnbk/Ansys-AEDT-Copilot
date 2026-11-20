# Data model: Layout review gate (025)

## Verdict (per channel, computed)

| Field | Type | Rule |
|---|---|---|
| `verdict` | `CONTINUE` / `STOP` | STOP if `counts.HIGH > 0` or `incomplete` |
| `reason` | `high` / `incomplete` / `high+incomplete` / `none` | |
| `counts` | `{HIGH, MEDIUM, INFO}` | points by FINAL severity; dismissed points not counted |
| `high_points` | `[{id, issues[], net, layer, x, y}]` | points with final HIGH |
| `failed_checks` | `[{check, error}]` (+ `{check: "trace", error}` when the channel failed) | |
| `incomplete` | bool | |
| `decided` | int | points with an engineer decision |

## Match key (per channel)

`{aedb, def_size, def_mtime_ns, cell, ends: [a, b] sorted, nets: sorted unique, checks: sorted, thresholds: {review.* minus use_snapshot}}`

## Review record — `<board dir>/Ansys AEDT Copilot/reviews/<stem>/review_<time>.json`

Measure output of 2.2.0 (`board, cell, plane_layers, checks_run, channels[], source, summary_md`) plus:

| Field | Content |
|---|---|
| `schema` | 1 |
| `record_source` | `standalone` / `isim:<request_id>/<interface>` |
| `cell_requested` | cell given ("" = active) |
| `board_key` | key before measuring |
| `measured_at` | time |
| `channels[i].key` | match key |
| `channels[i].verdict` | verdict from code (no decisions) |
| `channels[i].decisions` | `[{point, decision, severity_suggested, severity_final, reason, note, time}]` (via `design_review_decide`) |
| `channels[i].verdict_final` | verdict with decisions |

## Interface gate review — `<iface>/review.json`

One channel record: `request_id, interface, basis (proposal|content), comp_a, comp_b, nets (asked), key,
measured_at, verdict, record (path), reused_from (path|null), channels[1], summary_md, source`.
Partial checks → `<iface>/review_partial.json` (same shape, never used by the gate).

## user_settings.json — `interfaces[name].review`

`{measured_at, review_json, decisions[], override?: {measured_at, reason, time, verdict, high_points, failed_checks}}`
(existing key; `override` new). Decisions / override valid only when `measured_at` = review.json `measured_at`.

## Gate status (computed)

| status | ok | When |
|---|---|---|
| `not_reviewed` | no | no review.json |
| `out_of_date` | no | ends / nets ≠ content (or proposal), board key ≠ now, checks / thresholds ≠ now (`diffs` lists which) |
| `stop` | no | verdict with decisions STOP, no override |
| `continue` | yes | verdict CONTINUE (no decision needed) |
| `decided` | yes | code verdict STOP, verdict with decisions CONTINUE (all HIGH dismissed / lowered with reason, complete) |
| `override` | yes | STOP + valid override |

Status row (`isim_status`): `review` = `not reviewed` / `CONTINUE` / `STOP (n HIGH)` / `STOP (incomplete)` /
`decided` / `override` / `out of date`.
