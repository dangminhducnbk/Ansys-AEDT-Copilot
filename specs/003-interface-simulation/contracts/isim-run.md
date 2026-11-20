# Contracts: `aedt_copilot.interface_sim.run`

Background process (CLI `isim-run`). Tests: `tests/unit/test_isim_run_gates.py` (copy plan, path mapping, order, status
with a fake solver); real server run = manual quickstart §6.

## `plan_copy(workspace, sim_dir, request_id) -> dict`

Pure. Output `{src: [.aedt, .aedb], dst_folder: <sim_dir>/<request_id>_<time>/, bytes, excluded: [*.aedtresults,
*.lock, _backup]}`. Errors: `sim_dir` not existing / not writable → CopilotInputError; free space < bytes × 1.1 →
CopilotInputError(`sim_dir`, `free space >= <n> GB`, free).

## `server_path(local_path, sim_dir_local, sim_dir_server) -> str`

Pure. Replaces the `sim_dir_local` prefix with `sim_dir_server` (both given by the engineer, or the
`config.yaml sim_servers` entry); `sim_dir_server` "" → same path. Errors: path not under `sim_dir_local`.

## `start(request_id="", server="", port=17878, sim_dir="", sim_dir_server="", designs=(), mode="service", aedt_port=50000, client_port=18050, spawn=True) -> dict`

`spawn=False` = test hook (no background process). Mode `grpc` = the section below this one; `service` = last section.

Preconditions: ≥ 1 `merged` interface; `designs` ⊆ merged design names (default all merged, request order);
port 1..65535. Copies (never overwrites: new folder), writes `run_<time>.json` (all `queued`), starts the background
solver. Output `{run_id, folder}`.

## `solve_loop(run_json, solver=None)` (background)

For each design in order: state `running` → connect (`Desktop(machine=server, port=port, new_desktop=False)`) once,
open project by server path once, `analyze_setup(<setup>)`, `save_project`, state `done` / `failed` (message);
a failure does not stop the next. `solver` = test hook. Never closes the engineer's other projects on the server.

## `status(request_id, run_id="") -> dict`

Reads `run_<time>.json` → per design state, start / end, seconds, message, result path + `table_md`.

## Service-manager mode (FR-015a, R5b)

`start(..., mode="service", sim_dir="", sim_dir_server=<required>, port=17878, aedt_port=50000, client_port=18050)`:
`sim_dir` given → local copy to the shared folder as above; `sim_dir` empty → `transfer="upload"`: a filtered staging
copy is made under the request folder and uploaded by the background process into `<sim_dir_server>/<run_id>/`
(refuses when it exists). Errors: `aedt_port` not 1..65535, `client_port` not 1..65535, `mode` not `service|grpc`,
`sim_dir_server` empty in upload mode → CopilotInputError.

`_service_solver(data)`: one RPyC session + one launched non-graphical AEDT per run; `solve(design, setup)` as in grpc
mode; `close()` closes the project and the launched AEDT (`release_desktop(True, True)`), never other AEDT sessions.
