# Implementation Plan: MCP + CLI thin layers

**Branch**: `main` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Restructure only. Move logic out of `__main__.py` and `mcp_server/server.py` into the package; outputs identical.

1. **Golden first** (FR-006): `tests/unit/_make_golden_014.py` captures from pre-014 code →
   `tests/unit/golden/pre014.json`:
   - server: tool list via FastMCP `list_tools()` (name, description, inputSchema), `list_prompts()`, instructions,
     rendered prompt text (sha1), `about()` / `get_guide("")` / `get_guide("nope")` / `get_guide(each)` (sha1) /
     `show_defaults()` (minus live `aedt`), refusals of every gated tool with its flag false and of bad JSON args;
   - CLI: parser captured by patching `ArgumentParser.parse_args` → per command: flags (option strings, dest,
     required, default, type, action, nargs) and `format_help()` (COLUMNS=100); exit code + JSON for bad input
     (`design --op=nope`, `isim` bad JSON, `kitchen` bad safety).
2. **CLI package** `aedt_copilot/cli/` (FR-001/002, US2/US3):
   - `parser.py` `build_parser()` — the argparse tree moved verbatim (+ usage docstring of `__main__`).
   - `commands.py` one handler per command `(args) -> int | None`, table `COMMANDS {cmd: handler}`.
   - `io.py` `print_json(obj)`, `json_args(args)` (`--args` / `--args-file` → dict, bad JSON → `CopilotInputError("args")`),
     `input_error(ex)` → `{"ok": False, "error", "input", "expected"}`.
   - `main.py` `main(argv=None) -> int`: parse, `aedt_env.ensure()` + info line on stderr (before any pyedb import),
     dispatch. `cli/__init__.py` re-exports `main`.
   - `__main__.py`: stdout utf-8 + `from .cli import main` + `sys.exit(main())` (keeps `aedt_copilot.__main__.main`).
   - Logic moved to the package: `inspect_board.inspect(board, cell)` (open → summary → close),
     `review_checks.measure_report(board, channels, checks, cell, html, log)` (measure + optional review HTML).
3. **Server support in the package** (FR-003):
   - `cli/tasks.py`: `run(args, wait)` (subprocess `python -m aedt_copilot`, task table, `.tasks/<tid>.log`),
     `result(tid)`, `args_file(stem, data)` (`.tasks/<stem>_<hex8>.json`, str raw / obj JSON). Server keeps
     `_cli(args, wait=WAIT_S)` and `_result(tid)` as one-line hooks (tests patch `srv._cli`).
   - `cli/docs.py`: `guides()`, `guide(topic)`, `prompt_files()`, `prompt_text(path, arguments)`, `about()`.
   - `cut_board/excel_io.py`: `review_reports(board)` (was `_review_html`), `check_channels(excel)` (was
     `read_channels` body).
   - `cut_board/batch.py`: `mark_reported(job_id)` (`.reported` marker), `merge_blocker(job_id)` → refusal reason or
     None (job found, state done, marker present).
   - `interface_sim/settings.py`: `apply_route(request_id, name, values, handling)` → `(op, kwargs, None)` or
     `(None, None, refusal)` (state load, re-apply vs apply, step check, validation; messages verbatim).
   - Server keeps: `INSTRUCTIONS`, `@tool()` functions with docstrings, gate flag checks, `_refuse`, `_json_arg`,
     `_design_values`, CLI-argument building (`_isim`, `_design`, `_pidc`), early `batch, excel_io` import, prompt
     registration with `mcp.prompt`.
4. **Tests**: `tests/unit/test_thin_layers_014.py` — server + CLI equal golden; `__main__.py` has no command logic;
   parser commands = `COMMANDS` keys; server source has no `open(` / `subprocess` / `glob`; moved functions offline
   (check_channels on a temp Excel from `write_excel`, mark_reported / merge_blocker on a temp job, apply_route via
   existing isim fixtures already covered by `test_isim_reapply` / `test_isim_run_gates`). `_make_golden.dump_interface`
   reads CLI commands from `cli/parser.py`.
5. **Identity runs**: `tests/regression.py` on a board1 copy; PI-DC 3 skills through the new CLI on a copy of the
   sample (`--skip-export`) vs the 013 "before" copy (power tree not run).

## Kitchen check

| Item | Answer |
|---|---|
| Utensils added | none |
| Process tools added | none |
| Tool names / inputs / outputs | unchanged (golden: names, descriptions, input schemas, refusals) |
| Safety / gate | unchanged; gate flag checks stay in `server.py` |
| Catalog + contract | no catalog change; new package functions in `contracts/cli.md`, `contracts/package-moved.md` |
| Registration | all tools stay `@tool()`; `test_kitchen` / `test_kitchen_guards` unchanged and PASS |
| Recipes affected | none |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| New code | `aedt_copilot/cli/{__init__,main,parser,commands,io,tasks,docs}.py` |
| Changed code | `__main__.py`, `mcp_server/server.py`, `cut_board/{excel_io,batch,inspect_board}.py`, `interface_sim/settings.py`, `review_checks/__init__.py` |
| Unchanged | guides, prompts, templates, catalog, recipes, output folders |
| Tests | golden pre014 + structure tests; regression.py; PI-DC 3 skills on a copy |

## Constitution Check (1.2.0)

| Principle | Check | Status |
|---|---|---|
| I Gates | flag checks stay in server; refusals equal golden | PASS |
| II Data safety | regression / PI-DC on copies | PASS |
| III Defaults | untouched | PASS |
| IV Guides | no usage rule change | PASS |
| V Regression | regression.py + PI-DC identity before release | PASS |
| VII Contracts | contracts for new / moved public functions | PASS |
| VIII Thin layers | this feature | PASS |
| IX Stable interface | golden server + CLI | PASS |
| X Kitchen | see Kitchen check | PASS |

## Project Structure

```
specs/014-mcp-cli-thin/{spec,plan,tasks}.md, contracts/{cli,package-moved}.md
aedt_copilot/__main__.py, cli/*.py
aedt_copilot/cut_board/{excel_io,batch,inspect_board}.py, interface_sim/settings.py, review_checks/__init__.py
mcp_server/server.py
tests/unit/_make_golden_014.py, golden/pre014.json, test_thin_layers_014.py, _make_golden.py (CLI commands path)
```
