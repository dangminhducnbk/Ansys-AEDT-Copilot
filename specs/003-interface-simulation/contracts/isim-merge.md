# Contracts: merge

Tests: existing merge test on a scratch copy (unchanged results) + `tests/isim_check.py`.

## `cut_board.merge.merge_designs(target_aedt, sources, out_dir, port=None, log=print) -> dict`

| Input | Type | Valid |
|---|---|---|
| target_aedt | str | existing `.aedt`; no `.lock` unless `port` |
| sources | dict[name → aedb] | each existing `.aedb`; names = channel name rules |
| out_dir | str | writable; backup goes to `<out_dir>/_backup/<time>/` |
| port | int \| None | AEDT gRPC port of the session holding the target open |

Output: `{name: {status: ok|renamed|error, design, compare, warnings}}` — logic moved verbatim from `merge()`
(prepare → CopyDesign / Paste → rename `_vN` → compare). Existing designs never changed. Errors: lock without port →
RuntimeError (message unchanged).

## `cut_board.merge.merge(job_id=None, only=None, port=None, log=print)` — UNCHANGED API/results

Builds `sources` from the job and calls `merge_designs`.

## `interface_sim.merge.run(request_id, names=(), port=None) -> dict`

Precondition: each name step == `applied`. Target = request workspace. Writes `merge.json`; advances merged ones to
`merged`; error ones stay `applied` with the message.
