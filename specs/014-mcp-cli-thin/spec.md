# Feature Specification: MCP + CLI thin layers

**Feature Branch**: `014-mcp-cli-thin` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-09

**Status**: Draft (no clarification needed — assumptions recorded below)

**Input**: Parent session, user go 2026-11-09 ("làm đi"): ROADMAP 014 "MCP + CLI thin layers" — restructure only
(Principle VIII + IX). Create `aedt_copilot/cli/` so `__main__.py` only dispatches; `mcp_server/server.py` keeps only
argument parsing + gate checks + calls into the package API (business logic found there moves into the package).
No change to MCP tool names, inputs, outputs, user-facing messages, CLI commands / flags, guides, prompts, output
folders. Kitchen registration keeps working. Version 0.13.2.

## Problem

Principle VIII says the MCP server and the CLI only parse arguments and call the package API. Today both hold logic:

| Place | Logic today | Target |
|---|---|---|
| `__main__.py` (206 lines) | argparse tree + `if/elif` per command; `inspect` opens / closes EDB itself; JSON `--args` / `--args-file` load + input-error output copied 3 times (isim / design / kitchen); review-measure + HTML composed inline | `aedt_copilot/cli/` (parser, one handler per command, shared args / error helpers); `__main__.py` = entry only |
| `server.py` subprocess runner | `_cli` / `_result` / task table / `.tasks` args files | package module (server keeps a thin `_cli` hook) |
| `server.py` guides / prompts / about | reads `guides/*.md`, `prompts/*.md` front matter, builds `about` text | package module |
| `server.py` `read_channels` | Excel check loop (valid, sweep, errors, name errors) | `cut_board` package function |
| `server.py` `get_report` | writes the `.reported` marker | `cut_board.batch` function |
| `server.py` `merge_to_project` | job state + marker checks | `cut_board.batch` function returning the refusal reason (gate flag check stays in server) |
| `server.py` `propose_channels` | finds `layout_review_*.html` of the board | `cut_board` package function |
| `server.py` `isim_apply` | re-apply vs apply routing + validation | `interface_sim` package function returning the route or refusal (gate flag stays in server) |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Same MCP tools, same answers (Priority: P1)

The engineer (through Claude) uses the same MCP tools with the same inputs and gets the same results and the same
refusal / gate messages.

**Why this priority**: other users only `git pull`; guides and prompts name tools, inputs and messages.

**Independent Test**: offline — load the server before and after; tool names, descriptions and input schemas, prompt
list, server instructions, `about` / `get_guide` / `show_defaults` output and every gate refusal message are equal to a
golden captured from pre-014 code. Existing gate tests (kitchen guards, isim gates, design tools) PASS unchanged.

**Acceptance Scenarios**:

1. **Given** the pre-014 golden, **When** the new server is imported, **Then** the tool set, each tool's description and
   input schema, prompts and instructions are identical.
2. **Given** any gated tool called with its flag false, **When** it runs, **Then** the refusal is identical and no CLI
   process / args file is created.
3. **Given** a tool whose logic moved (read_channels, get_report, merge_to_project, propose_channels, isim_apply),
   **When** it is called with the same input, **Then** the output is identical.

---

### User Story 2 - Same CLI (Priority: P1)

A user runs `python -m aedt_copilot <cmd>` with the same commands and flags and gets the same JSON output and exit code.

**Why this priority**: the MCP server itself runs the CLI in a subprocess; scripts and tests call it too.

**Independent Test**: offline — every command, its flags (name, required, default, type, action) and the help texts
equal the pre-014 golden; bad `--args` JSON and unknown op give exit 2 with the same JSON. AEDT: `tests/regression.py`
(Excel flow through the CLI) PASS on a board1 copy, reference unchanged.

**Acceptance Scenarios**:

1. **Given** the pre-014 golden, **When** the new parser is built, **Then** commands, flags and help are identical.
2. **Given** `isim` / `design` / `kitchen` with invalid JSON or bad input, **When** run, **Then** output
   `{"ok": false, "error", "input", "expected"}` and exit code 2 as before.
3. **Given** a board1 copy, **When** the regression cut runs through the new CLI, **Then** it PASSes with the
   reference unchanged.

---

### User Story 3 - A new command is one handler (Priority: P2)

A developer adds a CLI command by adding its parser lines and one handler function; `__main__.py` is not touched.

**Independent Test**: offline — `__main__.py` holds no command name and no business call; every parser command has a
handler in the command table and vice versa.

## Edge Cases

- `inspect` prints AFTER the EDB closes (pyedb writes log lines to stdout on close) — order must be kept.
- `aedt_env.ensure()` MUST still run before any pyedb / pyaedt import (pyedb reads env once at import).
- The server imports `batch` / `excel_io` early (openpyxl / numpy DLL load hangs inside a running stdio server on
  Windows) — the early import must stay.
- Tests patch the server's `_cli` name: every server path that starts a CLI process MUST go through that name.
- `get_report` writes `.reported` only after the report succeeds (as today).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `aedt_copilot/cli/` MUST hold the CLI parser and one handler per command; `__main__.py` MUST only set up
  stdout encoding and call the CLI entry.
- **FR-002**: CLI commands, flags, defaults, help texts, JSON output and exit codes MUST be unchanged.
- **FR-003**: `mcp_server/server.py` MUST only parse arguments, check gates and call the package API; logic listed in
  Problem moves to package functions.
- **FR-004**: MCP tool names, descriptions, input schemas, outputs, refusal messages, prompts and instructions MUST be
  unchanged.
- **FR-005**: Kitchen registration MUST keep working: all tools through `@tool()`, catalog = server tools, gate
  refusal tests PASS.
- **FR-006**: Offline tests MUST compare the new server and CLI with a golden captured from pre-014 code.
- **FR-007**: Contracts MUST describe every new / changed public function.

### Key Entities

- **CLI command**: name, flags, handler(args) → JSON dict / exit code.
- **Server tool**: name, signature (input schema), docstring (description), gate flag, call into the package.

## Success Criteria *(mandatory)*

- **SC-001**: Server golden (tools, descriptions, schemas, prompts, instructions, about / guides / defaults, gate
  refusals): 0 differences.
- **SC-002**: CLI golden (commands, flags, help): 0 differences.
- **SC-003**: All unit tests PASS (incl. kitchen / catalog / guard tests); `tests/regression.py` PASS on a board1
  copy, reference unchanged.
- **SC-004**: `__main__.py` ≤ 20 lines; `server.py` holds no file reading / writing except via package helpers.

## Assumptions

- PI-DC: the CLI `pidc*` handlers move but make the same calls. Identity check: PI-DC 3 skills through the new CLI on
  a COPY of the sample (as in 013), compared with the 013 "before" copy; power tree NOT run (opens SIwave).
- Server instructions text and `@tool()` docstrings stay in `server.py` (they are the MCP interface itself).
- Small argument helpers (`_json_arg`, `_design_values`, building CLI argument lists, writing the args JSON through the
  package helper) are argument parsing and stay in the server.
- Gate checks that read state (isim step, workspace `.lock`, merge plan readiness) stay in the server but call package
  functions for the data.
- Version 0.13.2 (patch: restructure). No push (user pushes).
