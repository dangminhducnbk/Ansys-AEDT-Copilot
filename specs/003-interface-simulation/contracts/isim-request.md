# Contracts: `aedt_copilot.interface_sim.request`

Pure except file I/O in the request folder. Tests: `tests/unit/test_isim_request.py` (temp dirs).

## `start(workspace, board="", cell="", stackup="", schematic=(), bom="", interfaces=()) -> dict`

| Input | Type | Valid | Default |
|---|---|---|---|
| workspace | str | existing `.aedt` file | — |
| board | str | existing `.aedb` / `.aedt` (via `core.edb.aedb_path`) | `<workspace>.aedb` |
| stackup | str | existing file if given | "" |
| schematic | iterable[str] | each existing `.pdf` | () |
| bom | str | existing `.xlsx` / `.csv` if given | "" |
| interfaces | iterable[str] | channel name rules, unique | () |

Output: `{request_id, folder}`; writes `request.json`. Errors: CopilotInputError per bad input.

## `load(request_id="") -> dict` / `folder(request_id="") -> str`

"" = newest request under any workspace registered in `~/.aedt_copilot/isim_requests.json`. Errors:
CopilotInputError(`request_id`, `existing request`, value).

## `get_state(request_id, name) -> dict` / `set_state(request_id, name, **changes) -> dict`

`set_state` writes atomically (temp file + `os.replace`), appends `history`. Errors: unknown interface →
CopilotInputError.

## `require_step(state, expected) -> None`

Raises CopilotInputError(`step`, `<expected>`, state.step) — used by every gate.

## `advance(request_id, name, to_step, note="") -> dict`

Only allowed transitions (data-model); otherwise CopilotInputError. `to_step="started"` from any step renames old
outputs to `*_old_<time>` (never deletes).

## `busy(request_id, name)` — context manager

Creates `<iface>/.busy` with `O_CREAT|O_EXCL` (PID + time); raises CopilotInputError(`interface`, `not busy`,
holder) if held by a live PID; stale lock (dead PID) is replaced; removed on exit.
