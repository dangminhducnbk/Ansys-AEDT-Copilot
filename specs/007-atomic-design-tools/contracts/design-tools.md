# Contracts: `aedt_copilot.design_tools`

Tests: `tests/unit/test_design_tools.py` (offline: fake EDB, temp folders); board: `tests/design_check.py`.

## Registry entries (one file each)

Module attributes: `NAME` (str), `ORDER` (int), `SECTIONS` (tuple of template sections used), `validate(values,
targets) -> (P, targets)` (pure, CopilotInputError), `run(edb, P, targets, log) -> {changes, skipped}`,
`check(edb, P, targets) -> mismatches[]`. `read` has `run` only (no write).

## `design_tools.run(op, board, cell="", values=None, targets=None, in_place=False, version=None) -> dict`

| Input | Type | Valid |
|---|---|---|
| op | str | registry NAME |
| board | str | existing `.aedb` (`.aedt` mapped), no `.lock` |
| values | dict \| None | keys of the op's `SECTIONS`; merged on template defaults; `build_params` rules |
| targets | dict \| None | per op (plan table) |
| in_place | bool | — |

Order: validate everything (op, board, lock, values, targets that need no EDB) → copy or backup → open writable →
targets that need the EDB (refdes / nets / setup exist; else CopilotInputError with closest names, copy removed only
if created by this call) → snapshot before → `op.run` → save → close → reopen read-only → `op.check` → report file.
Output: data-model report. Side effects: copy `<stem>_<op>_<time>.aedb` (or backup + in-place edit), report markdown.
Never deletes the source; never touches a lock.

## `design_tools.read_design(board, cell="") -> dict`

Read-only snapshot (data-model). No copy, no save.

## `cut_board.cutter.apply_sweep(st, P, log) -> None` (extracted)

Deletes the sweeps of setup `st`, adds the sweep from `P["sweep"]` (linear scale start / stop / step, type,
interpolation settings) — the exact calls of `apply_setup` before 0.10.0.

## `cut_board.cutter.create_ports(edb, rd, nets, log, replace=False) -> {created[], skipped[]}` (extracted)

Coax port per pin of `rd` on `nets`, name `<rd>.<pin>.<net>`; existing port of the same name → skipped (or deleted
first when `replace`). `apply_stage` calls it with its previous arguments (results identical).
