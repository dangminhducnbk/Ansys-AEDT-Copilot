# Implementation Plan: Atomic design tools

**Branch**: `main` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

## Summary

New package `aedt_copilot/design_tools/` with one file per operation (registry pattern of 002: `NAME`, `ORDER`, `run`):
`setup`, `sweep`, `airbox`, `ports`, `solder_ball`, plus a read-only `read`. A shared runner resolves the `.aedb`,
checks the lock, makes the working copy (`<name>_<op>_<time>.aedb`) or the in-place backup (`<name>_old_<time>.aedb`),
reads the "before" values, runs the operation with the cut flow's own functions (`cutter.apply_setup`,
`apply_airbox`, `set_solder_ball`, coax port creation), saves, reads back, and writes a short report
(`<result>.design_tools.md` + JSON). Six MCP tools `design_*` (thin, CLI subprocess); gate only for in-place.
Guide `design_tools`. Version 0.10.0.

## Technical Context

| Item | Value |
|---|---|
| Language / runtime | Python 3.12, pyedb 0.85 (.NET), mcp<2 |
| New code | `aedt_copilot/design_tools/{__init__,_common,read,setup,sweep,airbox,ports,solder_ball}.py` |
| Changed code | `cut_board/cutter.py`: extract `apply_sweep(st, P, log)` from `apply_setup` and `create_ports(edb, rd, nets, log)` from `apply_stage` (same calls, results identical — regression proves it); `__main__.py` sub-command `design`; `mcp_server/server.py` 6 tools; guide + prompt |
| Read-back | `interface_sim.apply.read_setup` / `setup_mismatches` / `read_airbox` / `airbox_mismatches` (0.7.x) reused |
| Tests | offline `tests/unit/test_design_tools.py` (fake EDB, copy / backup / lock / validation / report); AEDT: `tests/design_check.py` on a board1 cut copy (user OK first) |
| Performance | open + one op + save + read-back ≈ 20–40 s on a cut design; copy of a cut `.aedb` < 1 s |

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I Gates in code | in-place refused without `user_approved_in_place=true` (server); copy mode needs no gate (original untouched) — user decision 2026-11-06 | PASS |
| II Data safety | copy by default; in-place only after backup copy; `.lock` → refuse; never delete | PASS |
| III Single source of defaults | values = template defaults (`autocut_template.csv`) overridden by the engineer | PASS |
| IV Rules in guides | new `guides/design_tools.md` (+ when to use vs cut / interface_sim) | PASS |
| V Regression | cutter extractions = restructure → `tests/regression.py` + `tests/isim_check.py` identical; new `tests/design_check.py` | PASS |
| VI Encoding | report markdown / JSON via Python UTF-8 | PASS |
| VII Contracts | `contracts/design-tools.md`, `contracts/mcp-tools.md`; CopilotInputError before any change | PASS |
| VIII Package by function | new `design_tools/` package, registry entries, MCP thin | PASS |
| IX Stable interface | additions only; cutter extraction keeps results identical | PASS |

Post-design re-check: PASS.

## Design

### Runner (`design_tools/_common.py`)

`run(op, board, cell="", values=None, targets=None, in_place=False, version=None)`:
1. Validate: `aedb_path(board)`; `.lock` next to the `.aedt` / inside `.aedb` → CopilotInputError (`board`, `design not
   open in AEDT`); op known (registry); op `validate(values, targets)` (pure, before any file work).
2. Work target: copy mode → `shutil.copytree` to `<dir>/<name>_<op>_<YYYYmmdd_HHMMSS>.aedb` (suffix `_2` if taken);
   in place → backup `<name>_old_<time>.aedb`, then the given path.
3. Open writable (`core.edb.open_edb`), `before = read.snapshot(edb, op scope)`, `op.run(edb, P, targets, log)`, save,
   close; reopen read-only → `after`; op `check(after, P, targets)` → mismatches.
4. Report: `{op, source, result, backup, in_place, changes[{item, old, new}], skipped[{item, reason}], mismatches,
   ok, seconds}` + markdown file `<result>.design_tools.md` (appended per op).

### Operations (registry entries, `ORDER` only for listing)

| NAME | Values (template keys) | Targets | Does |
|---|---|---|---|
| `read` | — | — | snapshot: setups (all `setup.*` / `sweep.*` read-back), airbox, ports (name, refdes, net), components with solder ball |
| `setup` | `setup.*` + mandatory `sweep.*` | `setup_name` (default template) | delete setup of that name, `cutter.apply_setup` (setup + sweep + arc step) |
| `sweep` | `sweep.*` | `setup_name` (must exist) | delete the sweeps of that setup, `cutter.apply_sweep` |
| `airbox` | `airbox.*` | — | `cutter.apply_airbox` |
| `ports` | — | `refdes` (list), `nets` (list, optional = all non-reference nets of the component), `replace` (bool) | per pin of those nets: skip if a port exists (unless replace → delete first), `create_ports` with `<refdes>.<pin>.<net>` |
| `solder_ball` | `solder_ball.*` | `refdes` (list) | `cutter.set_solder_ball` per component (short side of its signal pads), read back mm strings |

Values = `build_params(defaults ∪ values)` (same rules / messages as the settings table); only the op's sections are
taken. Unknown refdes / net / setup → CopilotInputError with closest names.

### MCP tools

`design_read(board, cell="")`, `design_setup(board, values, setup_name="", cell="", in_place=False,
user_approved_in_place=False)`, `design_sweep(...)`, `design_airbox(...)`, `design_ports(board, refdes, nets="",
replace=False, ...)`, `design_solder_ball(board, refdes, values="", ...)`. In place without the flag → refusal
(no CLI call). CLI: `python -m aedt_copilot design --op=<op> --args-file=<json>`.

## Project Structure

```
specs/007-atomic-design-tools/ plan.md research.md data-model.md quickstart.md contracts/{design-tools.md,mcp-tools.md} tasks.md
aedt_copilot/design_tools/      NEW (registry package)
aedt_copilot/cut_board/cutter.py   apply_sweep, create_ports extracted (identical results)
aedt_copilot/__main__.py        + design
mcp_server/server.py            + 6 tools
guides/design_tools.md          NEW;  prompts/design-tools.md NEW
tests/unit/test_design_tools.py NEW; tests/design_check.py NEW (AEDT, board1 copy)
VERSION 0.10.0, CHANGELOG.md, README.md, CLAUDE.md
```

## Complexity Tracking

| Deviation | Why | Simpler alternative rejected |
|---|---|---|
| Small extraction in `cutter.py` (`apply_sweep`, `create_ports`) | one implementation for the cut and the atomic tools | copying the code: two versions drift |
