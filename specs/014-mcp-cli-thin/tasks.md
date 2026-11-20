# Tasks: MCP + CLI thin layers (014)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/](contracts/)

## Phase 1: Setup (golden from pre-014 code)

- [X] T001 `tests/unit/_make_golden_014.py` (`dump_server(srv)`, `dump_cli(main)`) → `tests/unit/golden/pre014.json` from pre-014 code (server tools / schemas / prompts / instructions / about / guides / defaults / refusals; CLI flags / help / bad-input outputs)

## Phase 2: User Story 2 + 3 - CLI package (P1 / P2)

- [X] T002 [US2] Tests in `tests/unit/test_thin_layers_014.py`: CLI dump equals golden; `__main__.py` has no `add_parser` / command names; parser commands = `cli.commands.COMMANDS` keys
- [X] T003 [US2] `aedt_copilot/cli/{__init__,main,parser,commands,io}.py`; `aedt_copilot/__main__.py` entry only
- [X] T004 [US2] `cut_board/inspect_board.inspect(board, cell)`, `review_checks.measure_report(...)` used by the handlers
- [X] T005 [US2] `tests/unit/_make_golden.py` `dump_interface` reads CLI commands from `aedt_copilot/cli/parser.py`

## Phase 3: User Story 1 - thin server (P1)

- [X] T006 [US1] Tests in `tests/unit/test_thin_layers_014.py`: server dump equals golden; `server.py` has no `open(`, `subprocess`, `glob`, `threading`; offline tests for `check_channels`, `mark_reported`, `merge_blocker`, `review_reports`
- [X] T007 [US1] `aedt_copilot/cli/tasks.py` (run / result / args_file) and `aedt_copilot/cli/docs.py` (guides / guide / prompt_files / prompt_text / about)
- [X] T008 [US1] `cut_board/excel_io.py` `review_reports`, `check_channels`; `cut_board/batch.py` `mark_reported`, `merge_blocker`; `interface_sim/settings.py` `apply_route`
- [X] T009 [US1] `mcp_server/server.py`: use the package functions; keep `_cli` / `_result` hooks, gates, docstrings, instructions, early imports

## Phase 4: Polish

- [X] T010 Unit tests all PASS (incl. kitchen / catalog / guard); `graphify update .`
- [X] T011 Identity: `tests/regression.py` on a board1 copy PASS; PI-DC 3 skills (`--skip-export`) through the new CLI on a sample copy vs 013 "before" copy = 0 differences (power tree not run)
- [X] T012 VERSION 0.13.2, CHANGELOG, CLAUDE.md status row + layout, ROADMAP 014 done; commit + local tag v0.13.2

## Dependencies

T001 before any code change. T002 → T003..T005; T006 → T007..T009; T007 before T009. T010..T012 last.
