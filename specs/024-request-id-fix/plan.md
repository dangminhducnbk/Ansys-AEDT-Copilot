# Implementation Plan: Collision-proof run ids / output folders + about() 2.1–2.2 lines

**Branch**: `claude/024-request-id-fix-bd5e0b` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

## Summary

One pure helper module `aedt_copilot/core/unique.py` (no PyEDB) with three functions:
`claim_dir(path)` (atomic `os.mkdir` without exist_ok, suffix `_2`, `_3` … on clash, returns the created path),
`move_aside(src, dst)` (rename `src` to `dst` or the next free suffix, never overwrite; `os.rename` fails on an
existing target on Windows, also pre-checked so POSIX file renames cannot overwrite) and `file_lock(path)`
(context manager: exclusive lock file `O_CREAT|O_EXCL`, retry with timeout, stale lock > 60 s taken over).
Every time-stamped creation site calls them. Names without clash are unchanged (same `strftime` stamp).
about(): 2 lines added in `aedt_copilot/cli/docs.py`.

## Technical Context

Python 3.12, stdlib only (`os`, `time`, `contextlib`). Tests: `unittest` offline, clock mocked by patching the
module's `dt` / `datetime` / `time`, threaded race with `threading.Barrier`.

## Design — call sites

| # | File:place | Today | After |
|---|---|---|---|
| 1 | `interface_sim/request.py` `start` | exists-loop then `wjson` (makedirs exist_ok) → race shares folder | `folder = claim_dir(root/stamp)`, `rid = basename(folder)`; registry append inside `file_lock(registry + ".lock")` |
| 2 | `interface_sim/request.py` `advance('started')` outputs `_old_<tag>` | `os.replace` (file overwrite) | `move_aside` |
| 3 | `interface_sim/apply.py` apply `final_old_<tag>` | `os.replace` | `move_aside` |
| 4 | `interface_sim/apply.py` reapply backup `<name>_old_<tag>.aedb` | exists-loop + copytree | `claim_dir` + `copytree(dirs_exist_ok=True)` |
| 5 | `interface_sim/cut.py` `copy_source` `_old_` and `stage1_old_` | `os.replace` | `move_aside` |
| 6 | `design_tools/_common.py` `copy_name` / `backup_name` | `_free` (check only) | `claim_dir` (empty folder reserved) and `copy_aedb` with `dirs_exist_ok=True` |
| 7 | `design_tools/cutout.py` work folder | `_free` + `makedirs` | `claim_dir` |
| 8 | `design_tools/merge.py` `merge_<time>` default out_dir | makedirs exist_ok | `claim_dir` (given out_dir unchanged) |
| 9 | `cut_board/merge.py` `_backup/<ts>` | makedirs exist_ok | `claim_dir` |
| 10 | `cut_board/review.py` `layout_review_<ts>.html` | `open("w")` | claim file name with `O_EXCL` via `claim_file` (4th helper) |
| 11 | `edit_layout/run.py` `_region/<stamp>`, `<name>_<stamp>` | makedirs exist_ok / raise if dst exists | `claim_dir` (given out_dir unchanged) |

Out of scope (spec Assumptions): `interface_sim/run.py` server folder (`os.makedirs` strict already),
PI-DC report HTML, layout snapshot (key-based, not time), preview (fixed name under the interface folder).

`base_stem` regex already accepts `_<op>_<time>_<k>` → chained names unchanged.

Check #6: callers of `copy_name` / `backup_name` copy into the returned path — verify every caller uses
`copy_aedb` (or switch to it) so the reserved empty folder is filled, not refused.

## Contracts

`contracts/unique.md`.

## Tool catalog check

No tool added / changed / removed; no safety level or gate change; no workflow affected. about() text only.

## Constitution Check (2.0.1)

| Principle | Status |
|---|---|
| I gates | unchanged |
| II data safety | improved: backups never overwritten, runs never share folders |
| III defaults | n/a |
| IV guides | no usage rule change (names same) — nothing to add |
| V regression | `tests/regression.py` on board1 copy before merge |
| VI encoding | Edit tool only |
| VII contracts | contracts/unique.md, validation (`CopilotInputError` on empty path), offline tests |
| VIII layers | helper in `core/` (imports no feature package) |
| IX interface | names identical without clash; tool names unchanged |
| X catalog | no change |

## Project Structure

```
aedt_copilot/core/unique.py          new
tests/unit/test_unique_024.py        new (helper, same-second, threads, call sites, about lines)
specs/024-request-id-fix/            spec, plan, contracts, tasks
```

## Complexity Tracking

None.
