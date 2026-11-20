# Contracts: review verdict, store, gate (025)

## `review_checks._verdict`

| Function | Inputs | Output | Errors |
|---|---|---|---|
| `channel_verdict(ch, decisions=None)` | `ch`: measure channel dict (`points[]` with `id`, `severity_suggested`, `issues`, `net`, `layer`, `x`, `y`; optional `error`, `checks{name: {error?}}`); `decisions`: list of decision dicts or None | Verdict dict (data-model) | `ch` not a dict → `CopilotInputError("channel")`; decision without `point` → `CopilotInputError("decisions")` |
| `thresholds(review_defaults)` | dict of template `review.*` | sorted dict without `use_snapshot` | not a dict → `CopilotInputError` |
| `match_key(board_key, cell, comp_a, comp_b, nets, checks, thresholds)` | board_key dict from `layout_snapshot.key.board_key`; strings; lists | key dict | empty comp / nets → `CopilotInputError` |
| `diff(a, b)` | two keys | list of field names (`board_changed`, `cell`, `ends`, `nets`, `checks`, `thresholds`); `[]` = same | — |

Pure: no file, no EDB.

## `review_checks._store`

| Function | Inputs | Output | Errors |
|---|---|---|---|
| `folder(aedb)` | .aedb path | reviews folder path | — |
| `save(out, cell_requested, record_source, board_key, thresholds)` | measure output | record path; adds `key`, `verdict`, `verdict_final` to each channel of `out` | folder not writable → OSError |
| `find(aedb, key)` | key | `(path, doc, channel)` newest match or `None` | unreadable records skipped |
| `annotate(out, board_key, cell_requested, thresholds)` | measure output | adds `key`, `verdict`, `verdict_final`, `verdict_md` (no file) | — |
| `validate_decisions(points, decisions, now)` / `merge_decisions(old, new)` | as 011 | decision list | invalid → `CopilotInputError(decisions[i].*)` |
| `decide(path, channel, decisions)` | record path, channel name, list | channel summary | not a record / unknown channel / invalid decision → `CopilotInputError` |

`measure_report(...)` postcondition: `review_file` in output; board never written.

## `interface_sim.review`

| Function | Pre | Output / post | Errors |
|---|---|---|---|
| `run(request_id, name, checks=None, html=False, version=None, snapshot="auto", reuse=True, nets=None)` | interface state has `proposal` or `content`; `nets` = agreed nets when they differ from the proposal | writes review.json (all checks) or review_partial.json; record saved or reused | no proposal / content → `CopilotInputError("interface", "traced interface")` |
| `decide(request_id, name, decisions)` | review.json | as 011 + `verdict`, `gate`; decisions carry `measured_at` | as 011 |
| `override(request_id, name, reason)` | review.json, gate status `stop` | `user_settings` `review.override`; returns gate | reason empty → `CopilotInputError("reason")`; status ≠ stop → `CopilotInputError("review", "verdict STOP", status)` |
| `gate_status(request_id, name, content=None)` | interface exists | gate dict (data-model) | — (never raises for missing files: status `not_reviewed`) |
| `require(request_id, name, content=None)` | — | gate dict when ok | not ok → `CopilotInputError("review", message, status)` |
| `status_label(gate)` | gate dict | Review cell text | — |

Call sites: `content.confirm` (new Gate A), `cut.run`, server `isim_confirm_content`, `isim_cut`.
