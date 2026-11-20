# Tasks — 042 merge into a copy of the board (release 5.4.0)

- [x] T001 `cut_board/stackup_check.py`: `read(edb)`, `compare(ref, got)`.
- [x] T002 `cutter.cut_stage`: `stage1.board_stackup`.
- [x] T003 `apply.self_check`: item "stackup = board", result key `stackup`.
- [x] T004 `merge.py`: `copy_board`, `merge_designs(backup=, board_stackup=)`, `merged_checks` (components / pins,
  stackup), board designs before / after.
- [x] T005 `config/flow.merge_new_project`: board copy target, old empty project moved to `_work/history`, request keys;
  `go` rows `stackup` / `checks`, result `board_copy`.
- [x] T006 `answers.m3`: board copy line, stackup lines.
- [x] T007 [P] `tests/unit/test_merge_board_copy_042.py`; existing tests green.
- [x] T008 Guide `interface_sim`, CHANGELOG, VERSION 5.4.0, CLAUDE.md row.
- [x] T009 `tests/merge_board_copy_check.py` (BOARDA copy: pins, stackup, validation, `--change-thickness`).
- [x] T010 Copies: board1 `config_flow_check`; BOARDA check (SC-002, SC-003).
