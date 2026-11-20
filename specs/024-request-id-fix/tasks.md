# Tasks: Collision-proof run ids / output folders + about() 2.1–2.2 lines

**Input**: spec.md, plan.md, contracts/unique.md

## Phase 1: Foundational

- [X] T001 `claim_dir`, `claim_file`, `move_aside`, `file_lock` with input validation in aedt_copilot/core/unique.py (contracts/unique.md)
- [X] T002 Offline tests of the helper: same path twice → `_2`, `.aedb` suffix before extension, existing file counts as taken, move_aside never overwrites (file + folder), 8-thread race on claim_dir → 8 distinct, file_lock serializes + stale takeover + timeout in tests/unit/test_unique_024.py

## Phase 2: User Story 1 — requests in the same second (P1) 🎯

- [X] T003 [US1] `request.start`: claim_dir for the request folder, id = folder name; registry append under file_lock in aedt_copilot/interface_sim/request.py
- [X] T004 [US1] Tests: frozen clock → ids `S`, `S_2`; 8 threads → 8 ids, 8 registry entries, each request.json own data; `isim_previous`-style registry lookup finds both in tests/unit/test_unique_024.py

## Phase 3: User Story 2 — other time-stamped outputs (P1)

- [X] T005 [P] [US2] move_aside for `_old_` renames in aedt_copilot/interface_sim/request.py (advance), aedt_copilot/interface_sim/cut.py (copy_source, stage1), aedt_copilot/interface_sim/apply.py (final); claim_dir + copytree(dirs_exist_ok) for reapply backup
- [X] T006 [P] [US2] design_tools: copy_name / backup_name / cutout folder via claim_dir, copy_aedb dirs_exist_ok, merge default out_dir via claim_dir in aedt_copilot/design_tools/_common.py, cutout.py, merge.py
- [X] T007 [P] [US2] cut_board/merge.py `_backup/<ts>` claim_dir; cut_board/review.py HTML claim_file; edit_layout/run.py `_region/<stamp>` and `<name>_<stamp>` claim_dir
- [X] T008 [US2] Tests: frozen clock for request.advance reset twice, design_tools copy_name / backup_name twice, cut_board merge `_backup` twice (shutil patched), edit_layout region folder name helper in tests/unit/test_unique_024.py

## Phase 4: User Story 3 — about() (P2)

- [X] T009 [US3] about(): interface_sim line (isim_cut_form + isim_cut_preview, end GND rule) and review_measure line (layout_snapshot) in aedt_copilot/cli/docs.py; test in tests/unit/test_unique_024.py

## Phase 5: Polish

- [X] T010 Full unit suite PASS; `graphify update .`
- [X] T011 AEDT check on a fresh board1 copy: two request starts in the same second (two processes) → two folders; tests/regression.py PASS (tests/request_race_check.py)
- [X] T012 CHANGELOG.md "Unreleased" entry + CLAUDE.md status row (no VERSION bump)

## Phase 6: Convergence

- [X] T013 Add offline source guard test: in interface_sim / design_tools / cut_board merge+review / edit_layout no `os.replace(... _old_ ...)` and every time-stamped folder / review HTML goes through core.unique (claim_dir / claim_file / move_aside) in tests/unit/test_unique_024.py per FR-006 (partial)
- [X] T014 Justify removal of unused `design_tools._common._free` (replaced by claim_dir) in CHANGELOG.md per plan (unrequested)

## Phase 7: Fix — Windows lock file pending delete (2026-11-10)

Unit test `test_threaded_requests` failed now and then (`PermissionError` at `file_lock` `os.open`): on Windows a lock
file just deleted by another holder stays "delete pending" for a few ms and `O_EXCL` create returns access denied
instead of `FileExistsError` (reproduced: 4 errors in 40 rounds × 8 threads). Real processes can hit it too.

- [X] T015 `aedt_copilot/core/unique.py` `file_lock`: `PermissionError` = lock busy (retry 0.05 s); still failing after `perm_grace` 2 s → re-raise the `PermissionError` (real access problem stays visible); contract `contracts/unique.md`; unit tests (pending-delete retry, persistent denial re-raised); race script 0 errors

  Result: race script (40 rounds x 8 threads) 4 errors -> 0; full unit suite 475 PASS 5 runs in a row.
  50x test_threaded_requests: 50 OK; full unit suite 475 PASS. Released 2.5.1.
