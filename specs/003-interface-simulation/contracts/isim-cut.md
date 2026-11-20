# Contracts: `aedt_copilot.interface_sim.cut` and `.apply`

Run in a worker process (CLI `isim-cut` / `isim-apply`), inside `request.busy`. Tests: `tests/isim_check.py`.

## `cut.run(request_id, name, version=None) -> dict`

Precondition: step == `content_agreed`. Steps: copy `board` → `<iface>/_src/` (skip when a copy with the same
size + mtime exists), open the COPY writable, `cutter.cut_stage` to `<iface>/stage1/<name>.aedb`, save, write
`stage1.json`. Output: `stage1` summary + seconds; advances to `cut`.
Errors: any → step `failed`, partial `stage1/<name>.aedb` removed only if created by this run
(`cutter.remove_partial`); the engineer's board is never opened.

## `apply.run(request_id, name, values, handling, version=None) -> dict`

Precondition: step == `ends_checked`; `settings.validate(values)` valid. Steps: `P = build_params(values)`; copy
`stage1/<name>.aedb` → `final/<name>.aedb` (existing `final` renamed `_old_<time>`); open writable;
`cutter.apply_stage`; save; `self_check`. Output: `{aedb, metrics, warnings, self_check}`; advances to `applied`.

## `apply.self_check(aedb, P, ch, stage1, metrics, version) -> dict`

Read-only reopen. Checks (implemented): each end component present with ≥ its signal pins of `stage1`;
ports == signal pins found; setup `P.setup.name` and sweep `P.sweep.name` exist; `max_pin_shift_mm` ≤ 1;
setup / sweep VALUES read back equal P (T050: `read_setup` → `setup_mismatches`, every `setup.*` / `sweep.*`
channel key, GHz, rel. tol 1e-9; interpolation-only keys skipped for a discrete sweep; unreadable = mismatch).
Pure helpers `ghz`, `expected_setup`, `setup_mismatches` tested in `tests/unit/test_isim_self_check.py`. 0.7.2: every `airbox.*` value
read back from `hfss_extent_info` (`read_airbox` → `airbox_mismatches`, operating freq in GHz; test
`tests/unit/test_isim_airbox_check.py`). Output `{ok, mismatches[{item, expected, got}]}`.
