# Contracts: `aedt_copilot.layout_snapshot` (023)

## `arcs.to_coords(raw, tol_m) -> list[tuple[float, float]]`

Purpose: EDB point list (arc markers `Y > 1e300`, `X` = height) → closed-ring chord points.

| Input | Type | Unit | Valid | Default |
|---|---|---|---|---|
| raw | list of (x, y) | m | ≥ 1 point | — |
| tol_m | float | m | > 0 | — |

Output: points without markers; each arc replaced by points with chord error ≤ tol_m. Side effects: none.
Errors: CopilotInputError `tol_m` ≤ 0. Tests: test_layout_snapshot_023 (quarter circle, sign, full circle).

## `key.board_key(aedb, cell) -> dict` / `key.check_board_lock(aedb) -> None`

Purpose: validity key `{aedb, cell, def_size, def_mtime_ns, schema}` (`edb.def` only, never `edb.def.tmp`); refuse a
board open in AEDT.
Errors: CopilotInputError `board` (no `edb.def`; `.lock` present — names the lock, never deletes it).
Tests: key change on size / mtime / schema; `.tmp` ignored; lock refused.

## `key.window_of(bboxes, margin_m) -> tuple` / `key.contains(outer, inner) -> bool`

Pure window maths. Errors: CopilotInputError empty bboxes, margin < 0. Tests: unit.

## `store.write_index / read_index / write_window / read_window / list_snapshots / build_lock`

Purpose: files of data-model.md. `read_*` return None when missing, unreadable, other schema or other key (= stale).
`build_lock(folder, wait_s)` context manager: O_EXCL `.build.lock` (pid, time); waits while another live pid holds
it; removes only its own lock. Side effects: files under the snapshot folder only. Tests: round trip incl. WKB,
schema mismatch → None, lock wait / stale pid.

## `build.build_index(edb, aedb, cell, refs, log) -> dict` / `build.build_window(edb, index, window, tol_m, log) -> (dict, bytes)`

Purpose: read EDB (open read-only by the caller) into index / window data. EDB saved: no. Errors: RuntimeError from
EDB kept; per-primitive conversion errors → `unsupported` (never dropped). Tests: AEDT (`tests/review_check.py`,
`tests/snapshot_check.py`).

## `facade.SnapEdb(index, window=None)`

Purpose: read-only PyEDB-like object (data-model.md §Facade). Any value not in the snapshot →
`SnapshotMissing` (BaseException subclass, so `except Exception` in measuring code cannot swallow it).
Tests: fake snapshot drives `review_checks.measure_edb` (every check) offline.

## `api.build(aedb, cell="", nets=None, scope="window", margin_mm=None, version=None, log=None) -> dict`

| Input | Type | Unit | Valid | Default |
|---|---|---|---|---|
| aedb | str | — | existing `.aedb` / `.aedt` | — |
| nets | list[str] / comma str | — | ≥ 1 when scope window; names or fnmatch patterns matching ≥ 1 net | None |
| scope | str | — | `window`, `board` | `window` |
| margin_mm | float | mm | ≥ 0 | template `snapshot.window_margin_mm` |

Output: report (`snapshot.json`). Reuses a valid index and a valid containing window (`reused` flags).
Errors: CopilotInputError (inputs, lock, no net matches). Tests: unit (validation, reuse with fake store) + AEDT.

## `api.status(...) -> dict` / `api.list_(aedb) -> list`

Same inputs as build; no EDB open. State `valid` / `stale` / `missing` / `too_small`.

## `api.for_review(aedb, cell, specs, version=None, log=None) -> (SnapEdb, source)`

Purpose: facade for a review of `specs` (ensures index + window). Raises `SnapshotFallback(reason, ids)` when the window
has unsupported primitives; caller runs live and warns.

## `review_checks.measure_channels(board, specs, checks_=None, cell="", version=None, log=None, snapshot="auto")`

Change: `snapshot` (`auto` / `off`) + template `review.use_snapshot`; output + `source`. Errors: CopilotInputError
`snapshot`. Results identical to the live path (golden pre023).
