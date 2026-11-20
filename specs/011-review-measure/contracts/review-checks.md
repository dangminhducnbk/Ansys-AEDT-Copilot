# Contract: `aedt_copilot.review_checks`

Tests: `tests/unit/test_review_checks.py`; board: `tests/review_check.py`.

## Registry entry (one module per check)

`NAME` (str), `ORDER` (int), `TITLE` (str), `run(cc) -> {"items": [finding], "data": dict}`. `cc` = channel context
(lazy). Files starting with `_` are helpers. Adding a check = adding a file.

## `checks() -> dict[str, module]` (ORDER)

## `measure(board, channels, checks=None, cell="", version=None, log=None) -> dict`

| Input | Rule |
|---|---|
| board | `.aedt` / `.aedb` existing (read only, `.lock` allowed) |
| channels | `'A-B:pattern,...; C-D:...'` (same as `review_layout`) — at least one |
| checks | None / "" = all; list or comma text of registry names; unknown → CopilotInputError naming closest |

## `measure_channels(board, specs, checks=None, cell="", version=None, log=None)` — specs `[{comp_a, comp_b, patterns, name?}]`

## Output

`{board, cell, plane_layers, checks_run[], channels: [{name, comp_a, comp_b, nets, error?, warnings,
checks: {name: {items_count | error, data?}}, items: [item], points: [point], summary_md}], summary_md}`

- item: `{id, check, severity_suggested, net, layer, ref, value, x_mm, y_mm, len_mm?, other_net?, point?}`;
  order / ids = `review.review()` (sort `(severity, check, net, x)`, id `<channel no>.<n>`).
- point (HIGH / MEDIUM grouped by net + position, `review.points`): `{id, severity_suggested, net, x_mm, y_mm,
  issues: ["<check>: <value>"]}`.
- data: `vias.rows` (net, x_mm, y_mm, kind, size, range, used, backdrill, stub_mm, barrel_mm, gnd_d_mm), `routing`
  (chains, intra, inter, widths).
- check error → `{error}`; channel trace error → channel `error`; reference without plane layer → `{error: "no plane layer"}`.

## `interface_sim.review`

| Function | Rule |
|---|---|
| `run(request_id, name, checks=None, html=False)` | step ≥ `content_agreed`; specs from agreed content (patterns = agreed nets); writes `<iface>/review.json`; html → `cut_board.review.review()` HTML path |
| `decide(request_id, name, decisions)` | needs `review.json`; each `{point, decision: accepted|dismissed, severity_final?, reason?, note?}`; unknown point → CopilotInputError; severity_final ∉ HIGH/MEDIUM/INFO → error; severity_final ≠ suggested without reason → error; saves `user_settings` key `review` = `{measured_at, review_json, decisions[...+ severity_suggested, time]}` |
