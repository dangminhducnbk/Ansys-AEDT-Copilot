# Contracts: logic moved from server / CLI into feature packages (014)

Behaviour and messages are verbatim from the pre-014 server / CLI code.

## `cut_board.excel_io.review_reports(board) -> list[str]`

| Input | Type | Valid |
|---|---|---|
| board | str | `.aedt` / `.aedb` path (as `board_paths`) |

Output: sorted paths `<board dir>/<run.output_subdir>/layout_review_*.html` (empty list = none). Read only.

## `cut_board.excel_io.check_channels(excel) -> dict`

| Input | Type | Valid |
|---|---|---|
| excel | str | channel Excel written by `propose` |

Output: `{"board", "all_valid", "name_errors", "channels": [{enable, name, comp_a, comp_b, nets, diff_groups,
warnings, series, valid, sweep_ghz | errors}]}` (was the `read_channels` tool body). Read only.
Errors: file / sheet errors from `read_excel` propagate (unchanged).

## `cut_board.batch.mark_reported(job_id=None) -> str`

Writes `<job>/.reported` (local time `%Y-%m-%d %H:%M:%S`), returns its path. `job_id` None / "" = latest job.
Errors: `RuntimeError` from `find_job` when no job (unchanged).

## `cut_board.batch.merge_blocker(job_id=None) -> str | None`

Output: refusal reason (job not found → `find_job` message; state not done → `Job <id> chưa xong (state=...)`;
no `.reported` → verify message) or None when merge may run. Read only. The GATE 3 flag check stays in the server.

## `cut_board.inspect_board.inspect(board, cell=None) -> dict`

Opens the board read-only (version from machine config), returns `board_summary`, always closes EDB.
Errors: path errors from `excel_io.board_paths`, PyEDB errors propagate.

## `review_checks.measure_report(board, channels, checks_=None, cell="", html=False, log=None) -> dict`

`measure(board, channels, checks_, cell, log=log)`; `html=True` adds `html` = path from `cut_board.review.review`
(same as the pre-014 CLI). Errors: `CopilotInputError` from `measure` (raised before the HTML run).

## `interface_sim.settings.apply_route(request_id, name, values, handling) -> tuple`

| Input | Type | Valid |
|---|---|---|
| request_id | str | request id / "" (latest) |
| name | str | interface name |
| values / handling | dict | parsed JSON |

Output: `(op, kwargs, None)` with op `"reapply"` (step applied / merged, `validate_reapply` valid) or `"apply"` (step
`ends_checked`, `validate_for` valid); else `(None, None, refusal)` with refusal `{"refused": True, "reason", ...}`
(unknown request / interface, re-apply errors, wrong step, invalid values). GATE B flag check stays in the server.
Side effects: none (validation only).

Tests: `tests/unit/test_thin_layers_014.py`, `test_isim_reapply`, `test_isim_run_gates`, `test_kitchen_guards`.
