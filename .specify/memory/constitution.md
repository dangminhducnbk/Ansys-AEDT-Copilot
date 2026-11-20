# Ansys AEDT Copilot Constitution

## Core Principles

### I. User Gates Are Locked in Code

- The interface-simulation approvals MUST be enforced by the MCP server, not only by guides: the fixed
  process has ONE approval (`isim_go`: `user_approved_cut` + the user's words, bound to the checked
  config); the manual / recovery tools keep gates A content, B settings + `user_approved_gnd`,
  C merge, D run. The in-place / merge gates of design tools likewise.
- `user_approved_*` MUST be passed only after the user's explicit go in the current conversation.
- When the user is listing items or discussing, Claude MUST only record and ask; work starts on an
  explicit go ("làm đi", "đồng ý").

Rationale: cuts and merges take minutes per channel and change the user's project; a skipped gate
wastes AEDT time or writes wrong designs.

### II. User Data Safety

- Claude MUST NOT delete or overwrite user files (boards, results, `.lock` files) without permission.
- Layout edits MUST run on a COPY of the EDB.
- Merge MUST back up the original `.aedt` + `.aedb` before writing, and MUST NOT overwrite a design
  (name conflict → `_v2`, `_v3`).
- PI-DC MUST work in place on the solved project and MUST NOT save it.

Rationale: boards are large, slow to regenerate and owned by the user.

### III. Single Source of Defaults

- `templates/*.csv` MUST be the only source of default parameter values.
- Python functions MUST take parameters as arguments (dict `P`); no module may read the template
  during a cut or edit.

Rationale: one place to change defaults, visible in git diffs; runs are reproducible from
`user_settings.json`.

### IV. Usage Rules Live in Guides

- Every agreed rule that changes what Claude does or checks when USING the tool MUST be written to
  `guides/*.md` (or `prompts/*.md`), not only to CLAUDE.md.
- Dev-only facts (PyEDB API quirks, environment, status) stay in CLAUDE.md.

Rationale: other users receive only the MCP server and guides, never this repo's CLAUDE.md.

### V. Regression Before Release

- `tests/regression.py` (interface-simulation flow, board1 copy) and `tests/pidc_check.py` MUST
  PASS against the reference data before a release.
- Each release MUST bump `VERSION` (patch = fix, minor = feature, major = breaking workflow / tool
  interface),
  add a `CHANGELOG.md` entry (stating whether `setup.bat` must be rerun) and be tagged `vX.Y.Z`.

Rationale: results feed SI/PI sign-off; silent geometry or port changes are costly.

### VI. Windows & Encoding Discipline

- Files MUST be written as UTF-8; repo files MUST NOT be rewritten with PowerShell
  `Get-Content` / `Set-Content` (5.1 reads UTF-8 as ANSI → mojibake).
- Paths used by AEDT / `.bat` MUST NOT contain spaces.
- CLI entry points MUST reconfigure stdout to UTF-8.

Rationale: the tool runs on Windows with Vietnamese text; encoding bugs corrupt guides and reports.

### VII. Function Contracts & Validation

- Every public function (called by another module, the CLI or the MCP server) MUST have a contract
  in `specs/<feature>/contracts/` stating: inputs with types and valid ranges, preconditions,
  outputs / postconditions, and the errors it raises.
- A public function MUST validate its inputs at entry and raise `CopilotInputError` (shared, defined
  in `core/`) with a message that names the bad input and the expected value.
- Pure logic (no PyEDB / AEDT / SIwave call) MUST have offline unit tests; code that calls AEDT MUST
  be covered by `tests/regression.py` or `tests/pidc_check.py`.

Rationale: bad inputs today fail minutes into an AEDT run with unclear errors; contracts make each
function checkable on its own and let other users trust the API.

### VIII. Package by Function, Thin Layers

- The package MUST be split by function: `core/` (EDB session, config / template, validation,
  errors, geometry, units), `cut_board/`, `pi_dc/`, `edit_layout/`, `cli/`.
- `core/` MUST NOT import any feature package.
- `mcp_server` and `cli` MUST only parse arguments and call the package API; they MUST NOT hold
  business logic.
- Pure logic MUST be separated from code that calls PyEDB / AEDT so it can be tested offline.

Rationale: one place per concern, no duplicated helpers across features, and testable logic without
a 5-minute AEDT run.

### IX. Stable Public Interface

- MCP tool names, guides, prompts, the CSV template format and output folders
  (`Ansys AEDT Copilot/`, `autocut/` for review HTML) MUST NOT change.
- Restructuring MUST NOT change results: `tests/regression.py` and `tests/pidc_check.py` MUST give
  identical results before and after, and MUST be run after each restructuring feature.
- An interface change is allowed only in a MAJOR release, recorded in `CHANGELOG.md`.

Rationale: other users only `git pull`; they must not have to relearn the tool or redo their settings.

### X. Tool Catalog and Workflows

- Every MCP tool MUST be one operation, usable alone on any valid input, registered in the tool
  catalog with inputs, outputs, preconditions, what it writes and its safety level
  (read-only / writes a copy / writes the original / remote).
- A tool MUST be registered through the shared registration helper; the server MUST refuse to start
  if a tool lacks a catalog entry or safety level.
- Tools that write an original file / workspace or run remotely MUST require an explicit approval
  flag checked server-side, whatever workflow calls them.
- A new way of working MUST be a workflow (file in `workflows/` or the personal workflow folder), not a
  new fixed-process tool. A process tool is allowed only as a thin wrapper over catalog tools.
- Offline tests MUST fail when: a tool is missing from the catalog, a catalog entry has no contract,
  a risky tool has no approval flag, or a workflow names a tool that does not exist.
- When a needed tool does not exist, Claude MUST say so and add it through Spec Kit; it MUST NOT
  write an ad-hoc script instead.

Rationale: tools reused by many workflows stay safe and consistent; new workflows need no new code.

## Technical Constraints

- Target: Ansys AEDT 2026 R1 (`ANSYSEM_ROOT261`), fallback 2025 R2 (`ANSYSEM_ROOT252`); HFSS 3D Layout / EDB,
  SIwave for PI-DC. The AEDT root MUST be resolved by `aedt_copilot/aedt_env.py` (config `aedt_root` → env →
  registry → scan), never hard-coded.
- Files saved by AEDT 2026 R1 do not open in 2025 R2.
- Python 3.12 repo `.venv`, pinned in `requirements.txt`: pyedb 0.85, `pyaedt==1.9.0`, `mcp<2`.
- Layers: guides = what Claude does; MCP server = bridge + gate locks; Python package
  `aedt_copilot` = execution. No Claude plugin (MCP server registered by `setup.bat`).

## Development Workflow

- Feature and behavior changes go through Spec Kit: specify → clarify (if unclear) → plan → tasks →
  implement → converge; specs live in `specs/`; commit after each step.
- `/speckit-plan` MUST produce `contracts/` for every new or changed public function (Principle VII).
- `/speckit-converge` MUST check that each contract has matching input validation and a test.
- `/speckit-plan` MUST include a "Tool catalog check": which tools are added or changed, their safety
  level, and which workflows are affected (Principle X).
- `/speckit-converge` MUST run the catalog tests and check that every new tool has a catalog entry,
  a contract and a test.
- Before reading source for a codebase question, query the graph (`graphify query`); after code
  changes run `graphify update .`.
- AEDT GUI MUST NOT be operated while the user is using the machine; ask first.
- Communication with the user is in Vietnamese, short, tables over prose.

## Governance

- This constitution supersedes other practices in this repo. Amendments are made by the repo owner
  only, via `/speckit-constitution`, with a version bump (MAJOR: principle removed/redefined,
  MINOR: principle/section added, PATCH: wording).
- Every spec, plan and review MUST check compliance with the principles above; deviations MUST be
  justified in the plan.
- Runtime development guidance: `CLAUDE.md`.

**Version**: 2.1.0 | **Ratified**: 2026-11-04 | **Last Amended**: 2026-11-16
