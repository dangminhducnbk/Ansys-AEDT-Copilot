# Feature Specification: PI-DC + layout edit on core

**Feature Branch**: `013-pidc-layout-core` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-08

**Status**: Draft (no clarification needed — assumptions recorded below)

**Input**: Parent session, user go 2026-11-08 ("bạn tự chọn rồi làm tiếp đi"): ROADMAP 013 "PI-DC + layout edit on
core" — restructure only (Principle IX): `pi_dc/` and `edit_layout/` use `core/` (registry, geometry, units,
config / template, validate, errors, EDB session) instead of their own helpers. No result change. Version 0.13.1.

## Problem

Feature 002 built `core/` and moved the cut-board flow onto it. PI-DC and layout edit still carry their own copies:

| Module | Own helper today | Core replacement |
|---|---|---|
| `pi_dc/workflow.py` | hand-written skill table `SKILLS` + `DEFAULT` list (a new skill = edit 3 places) | `core.registry` (a new skill = one file) |
| `pi_dc/common.py` | template path built by hand | `core.config.template_path("pidc")` |
| `pi_dc/skills/via_current.py` | literal `1e-3` mm → m | `core.units.MM` |
| `edit_layout/run.py` | `_aedb()` (.aedb path rules), `_open()` (EDB open) | `core.edb.aedb_path`, `core.edb.open_edb` / `edb_session` |
| `edit_layout/extract.py`, `ops.py` | own `MM = 1e-3` | `core.units.MM` |
| public entries (`run_skill`, `region`, `edit`) | bad input fails late with `RuntimeError` / `KeyError` | `core.validate` → `CopilotInputError` at entry |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Same PI-DC report after the restructure (Priority: P1)

The engineer runs PI-DC on a solved SIwave folder exactly as before and gets the same numbers, verdicts and images.

**Why this priority**: PI-DC reports go to customers; a restructure must not move a single value.

**Independent Test**: run the three image skills (current density, via current, voltage distribution) with the
pre-013 code and with the new code on two copies of the BOARDB_B04 VCC_0P8V sample; the result files are identical
except run time and folder paths; `tests/pidc_check.py` PASSes on both.

**Acceptance Scenarios**:

1. **Given** the sample folder, **When** PI-DC runs with the new code, **Then** every value in the results equals the
   pre-013 values (verdicts, counts, J, util, regions, images list).
2. **Given** the skill list, **When** a caller asks for the skills, **Then** the names and their order are the same as
   before (current_density, via_current, voltage_distribution, power_tree).
3. **Given** an unknown skill name, **When** a skill is run, **Then** it stops at once with a message naming the input
   and the valid names.

---

### User Story 2 - Same layout edit after the restructure (Priority: P1)

The engineer runs layout region / layout edit as before and gets the same edits, checks and images.

**Why this priority**: layout edit changes copper; a restructure must not change one polygon or via.

**Independent Test**: run the existing check script `tests/layout_edit_b04.py` (two real B04 cases, always on a
copy) with the pre-013 and new code; ops results, checks, summaries and changes are identical except run time and
output paths. Offline unit tests compare the helpers that moved to core with golden values from pre-013 code.

**Acceptance Scenarios**:

1. **Given** a plan, **When** layout edit runs with the new code, **Then** op results, checks and change lists equal
   the pre-013 run.
2. **Given** a board path written as `.aedt`, `.aedb`, `.aedb/edb.def` or with quotes, **When** region / edit runs,
   **Then** it resolves to the same `.aedb` folder as before.
3. **Given** a missing board or a malformed box, **When** region / edit runs, **Then** it stops before opening EDB with a
   message naming the bad input.

---

### User Story 3 - A new PI-DC skill is one file (Priority: P2)

A developer adds a PI-DC skill by adding one module in the skills package (plus its guide); no table to edit.

**Why this priority**: same rule as review checks and design tools (feature 002 / 007 / 011).

**Independent Test**: offline test — the skills package is loaded by the shared registry; every skill has a name,
order, title and run; order gives today's default list.

## Edge Cases

- Power tree skill launches SIwave itself: it is not re-run for the identity check (it would open SIwave on the user's
  desktop); its registry entry and order are covered by the offline test.
- A board path that is valid today MUST still be accepted (no new rejection of valid input).
- Rounding: unit constants MUST be replaced only where the value is bit-identical (`x * 1e-3` → `x * MM`); `x * 1e3`
  stays as written (`x / MM` is not always bit-identical).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: PI-DC skills MUST be discovered by the shared registry; each skill declares its order; the skill table
  and default list MUST equal today's (names, order, export need).
- **FR-002**: PI-DC defaults MUST be read through the shared template path / reader (values unchanged).
- **FR-003**: Layout edit MUST resolve and open boards through the shared EDB helpers (same path rules, same AEDT
  version from machine config, same read-only / write mode, EDB always closed).
- **FR-004**: Unit constants in PI-DC and layout edit MUST come from the shared units module where the value is
  bit-identical.
- **FR-005**: Public entries `run_skill`, `run` (PI-DC), `region`, `edit` (layout edit) MUST validate their inputs at
  entry and raise the shared input error naming the input (Principle VII); valid inputs accepted today MUST stay
  accepted.
- **FR-006**: No MCP tool name, input or output (success path) changes; template files unchanged; output folders
  unchanged.
- **FR-007**: Offline unit tests MUST compare the moved helpers with golden values captured from pre-013 code
  (skill table / order, PI-DC params, layout edit defaults, board path resolution, unit constants).
- **FR-008**: Contracts MUST describe every changed public function.

### Key Entities

- **PI-DC skill**: module with name, order, title, run; result saved as `results/<name>.json`.
- **Layout edit entry**: `region(board, box, ...)`, `edit(plan)`.

## Success Criteria *(mandatory)*

- **SC-001**: PI-DC results of 3 skills on the sample copy: 0 value differences pre-013 vs 013 (only run time /
  paths differ); `tests/pidc_check.py` PASS.
- **SC-002**: `tests/layout_edit_b04.py` both cases: 0 differences in op results, checks, summary and change counts.
- **SC-003**: `tests/regression.py` PASS on a board1 copy, reference unchanged; all unit tests PASS.
- **SC-004**: No duplicate EDB-open / .aedb-path / mm-constant helper left in `pi_dc/` or `edit_layout/`.

## Assumptions

- PI-DC identity check runs on COPIES of the sample folder (as feature 002 did), not in place: no SIwave launch, the
  user's own output folder is not overwritten. Power tree is not re-run (needs SIwave via explorer.exe).
- Error path only: messages for invalid input change from `RuntimeError` text to `CopilotInputError`
  (`<input>: expected ..., got ...`); the CLI / MCP still report a failure for the same inputs.
- Layout edit keeps its shapely geometry (`edit_layout/geom.py`): it has no duplicate in `core.geometry` (pure-Python
  point / segment helpers). The op table of the `Editor` class stays (ops share one edit session; not a registry case).
- CLI wrappers stay as they are (feature 014 thins the CLI).
- Version 0.13.1 (patch: restructure). No push (user pushes).
