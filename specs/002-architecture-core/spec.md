# Feature Specification: Architecture + core/

**Feature Branch**: `002-architecture-core` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Feature 002 'Architecture + core/' for Ansys AEDT Copilot. Define target package layout
for the whole restructure (roadmap features 002-014, recorded in specs/ROADMAP.md with type restructure/new rule and
order). Create aedt_copilot/core/: EDB session (wrap aedt_env.open_edb), config/template reading (templates/*.csv only
source of defaults), validation helpers + CopilotInputError, geometry (from cut_board/geometry.py), units. core/ must
not import any feature package. Define contract format for all later features (inputs/types/ranges, preconditions,
outputs, errors) and registry pattern (one file per check/handler, registered like pi_dc SKILLS). Old modules keep
working via thin re-exports so tests/regression.py and tests/pidc_check.py give identical results; no MCP tool name,
guide, prompt, Excel/CSV format or output folder change. Offline unit tests for pure logic in core/."

## Problem

- Shared helpers live inside one feature and are imported across features: `pi_dc` and `edit_layout` import
  `cut_board.config`; `aedt_env` imports `cut_board.config`; three different template-CSV readers exist
  (cut board, PI-DC, layout edit).
- No shared input error: bad inputs fail minutes into an AEDT run with unclear messages (Principle VII).
- Large files (`review.py` 1213 lines, `cutter.py` 756 lines) mix many agreed rules; adding a rule means editing old
  code. The restructure (features 002-014) needs one agreed target layout, one contract format and one registry
  pattern before any module is moved.

## User Scenarios & Testing *(mandatory)*

Actors: **team user** (runs the tool through Claude desktop / MCP), **maintainer** (repo owner, adds rules),
**feature session** (a later Claude session implementing features 003-014).

### User Story 1 - Nothing changes for the team user (Priority: P1)

A team user does `git pull` and keeps working: same MCP tools, guides, prompts, channel Excel, templates and output
folders; the same board gives the same cut and PI-DC results.

**Why this priority**: Principle IX. A restructure that changes results or the interface is a regression.

**Independent Test**: run `tests/regression.py` (board1 copy, CPHY_U14_U26) and `tests/pidc_check.py`
(BOARDB_B04 reference) after the change; compare with the run before the change.

**Acceptance Scenarios**:

1. **Given** the reference job inputs, **When** the cut regression runs after 002, **Then** it PASSes with the same
   ports, component pin / GND-pin counts, GND via count, plane areas and pin shift as before 002.
2. **Given** the BOARDB_B04 reference folder, **When** `pidc_check` runs after 002, **Then** it PASSes with the same
   values as before 002.
3. **Given** any existing import path (`aedt_copilot.cut_board.config`, `aedt_copilot.cut_board.geometry`,
   `aedt_copilot.aedt_env`), **When** old code or tests import it, **Then** every previously public name still
   exists and behaves the same.
4. **Given** the MCP server, **When** listing tools, guides and prompts, **Then** the names and count are unchanged.

---

### User Story 2 - One shared core for all features (Priority: P1)

The maintainer (and later feature sessions) find EDB opening, template/config reading, input validation, the
shared input error, 2D geometry and unit conversion in one place that does not depend on any feature.

**Why this priority**: every later feature (003-014) moves code onto these blocks; without them each move
re-creates helpers.

**Independent Test**: offline unit tests (no AEDT, no PyEDB) for template reading, value coercion, validation
helpers, error messages, geometry and units PASS; an import check proves `core/` imports no feature package.

**Acceptance Scenarios**:

1. **Given** any `templates/*.csv` (autocut, PI-DC, layout edit), **When** read through core, **Then** the same
   keys, types and default values are returned as by today's reader of that template.
2. **Given** a public core function called with a bad input (wrong type, out of range, missing file), **When** it
   runs, **Then** it raises the shared input error whose message names the input, the expected value and the
   value received, before any AEDT / PyEDB call.
3. **Given** a board path (`.aedt`, `.aedb` folder or `edb.def`), **When** core opens the EDB session, **Then** the
   right `.aedb` is opened with the resolved AEDT version, read-only by default, and the session is closed when the
   caller's block ends, also on error.
4. **Given** the `core/` package, **When** its imports are scanned, **Then** none points to `cut_board`, `pi_dc`,
   `edit_layout`, `cli` or `mcp_server`.

---

### User Story 3 - Add a rule as one new file (Priority: P2)

A feature session adds a new check or handler (e.g. connector end in 011) by creating one new file in the right
folder, without editing existing check / handler files, and documents its function with the shared contract
format.

**Why this priority**: user decision 2026-11-04 (1 file ≈ 1 agreed rule); it is the base of 003-013 but has no
user-visible effect in 002.

**Independent Test**: offline test with a throw-away package of two dummy entries: both are found, run in their
declared order, a duplicate name or a missing required attribute is rejected with a clear error.

**Acceptance Scenarios**:

1. **Given** a registry package with entry files, **When** the registry loads, **Then** every entry file is
   found without listing it anywhere else, and entries are returned in declared order (ties by name).
2. **Given** two entries with the same name, or an entry without a name / order / run callable, **When** the
   registry loads, **Then** loading fails with a message naming the file and the problem.
3. **Given** a public function in any feature, **When** its contract is written, **Then** it follows the one
   contract format (inputs with types and ranges, preconditions, outputs / postconditions, errors).

---

### User Story 4 - The restructure plan is written down (Priority: P2)

The maintainer sees in one document the target package layout and the ordered features 002-014, each marked
restructure (no result change) or new rule (minor bump + new reference data).

**Why this priority**: lets the user group Spec Kit cycles and AEDT regression runs (~6 min each) and review the
order before work starts.

**Independent Test**: open `specs/ROADMAP.md`; every feature 002-014 is listed with number, name, type, scope,
dependencies and the regression it must pass.

**Acceptance Scenarios**:

1. **Given** the roadmap, **When** read, **Then** it lists 002-014 in order, with type restructure for 002-010 and
   new rule for 011-013, 014 as test, and the postponed stackup-config feature (not numbered).
2. **Given** the target layout, **When** compared with the user's decisions of 2026-11-04, **Then** every named
   module (review checks, cut / cleanup / ports / sim_setup / flow, propose, excel, batch, merge) has a place.

### Edge Cases

- Template CSV with comment lines, blank lines, BOM, missing trailing columns or an empty default → same result as
  today's reader (empty default = no default).
- Template file missing → shared input error naming the file path.
- Value that does not match its type (e.g. `abc` for a number, `maybe` for a bool) → error naming key and value.
- Board path with surrounding quotes / spaces, or pointing to `.aedt` → normalised to the `.aedb` folder;
  non-existing folder → shared input error before PyEDB is loaded.
- EDB open fails inside PyEDB (license, version) → original error is kept and the session is not left open.
- Registry package with no entries → empty, ordered list (not an error); a non-entry helper file (name starting
  with `_`) is skipped.
- Old code catching `ValueError` for bad values keeps catching the shared input error.
- Geometry on degenerate input (zero-length segment, polygon with < 3 points) → same result as today's code.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A `core/` package MUST provide: EDB session, config / template reading, validation helpers, the shared
  input error `CopilotInputError`, 2D geometry, unit conversion, and the registry helper.
- **FR-002**: `core/` MUST NOT import any feature package (`cut_board`, `pi_dc`, `edit_layout`, `cli`) or
  `mcp_server`; the AEDT resolver (`aedt_env`) MUST depend only on core, not on `cut_board`.
- **FR-003**: `templates/*.csv` MUST stay the only source of default values; core MUST read any template by column
  header name (`Key`, `Type`, `Default`, ...), so the three existing templates are read without format change.
- **FR-004**: Value coercion (num / bool / text / list) MUST give exactly today's results for every value accepted
  today and the same rejections.
- **FR-005**: The machine config (`config.yaml`: `aedt_version`, `aedt_root`, `python`, ...) MUST be read in one
  place in core with today's defaults.
- **FR-006**: `CopilotInputError` MUST be a subclass of `ValueError` and its message MUST name the input, the
  expected value / range and the value received.
- **FR-007**: Validation helpers MUST cover: type, numeric range (inclusive / exclusive bounds), choice from a set,
  non-empty text, existing file / folder; each raises `CopilotInputError`.
- **FR-008**: The EDB session MUST normalise the board path, validate it before loading PyEDB, open with the resolved
  AEDT version and the .NET backend (as `aedt_env.open_edb` today), default to read-only, and always close.
- **FR-009**: Geometry MUST offer every function of `cut_board/geometry.py` with identical results; pure functions
  MUST be separated from the one that reads EDB primitives.
- **FR-010**: Units MUST convert m ↔ mm, m² ↔ mm² and format a length for EDB (e.g. `0.2mm`) without float noise.
- **FR-011**: The registry helper MUST discover entry files in a package automatically, require `NAME`, `ORDER` and
  a run callable per entry, reject duplicates / missing attributes, and return entries sorted by `ORDER` then
  `NAME`. Files starting with `_` are not entries.
- **FR-012**: Old import paths MUST keep working: `cut_board/config.py` and `cut_board/geometry.py` become thin
  re-exports of core (cut-board-only logic such as the sweep rule stays in `cut_board`); `aedt_env.open_edb` keeps
  its signature. `pi_dc` and `edit_layout` MUST read their templates through core instead of `cut_board.config`.
- **FR-013**: No change to MCP tool names, guides, prompts, Excel / CSV formats, output folders (`autocut/`,
  `Ansys AEDT Copilot/`) or CLI commands (Principle IX).
- **FR-014**: A contract format document MUST define, for every public function: signature, inputs (type, unit,
  valid range, default), preconditions, outputs / postconditions, side effects (files written, EDB saved or not),
  errors raised; every core public function MUST have a contract in that format.
- **FR-015**: `specs/ROADMAP.md` MUST record the target package layout and features 002-014 (number, name, type,
  scope, dependency, regression gate, version bump) plus the postponed stackup-config feature.
- **FR-016**: Pure core logic MUST have offline unit tests runnable with the repo `.venv` without AEDT, PyEDB .NET
  or a license.
- **FR-017**: `VERSION` bump: patch (0.5.0 → 0.5.1), CHANGELOG entry stating no `setup.bat` rerun needed.

### Key Entities

- **Template row**: one parameter of a team-defaults CSV: key, name, unit, type, scope, mandatory, default,
  description (columns present depend on the template).
- **Machine config**: per-PC settings from `config.yaml` (AEDT version / root, Python, gRPC port).
- **EDB session**: one open EDB on a normalised `.aedb` path, read-only or writable, closed at the end.
- **Contract**: the documented promise of one public function (inputs, preconditions, outputs, errors).
- **Registry entry**: one file = one agreed rule (check / handler / skill) with a name, an order and a run callable.
- **Roadmap item**: one feature 002-014 with type, scope, dependency and regression gate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cut regression and PI-DC check PASS after 002 with values identical to the run before 002
  (0 differences in compared metrics).
- **SC-002**: 0 changes in MCP tool / guide / prompt names, template files and Excel layout (diff of those lists = empty).
- **SC-003**: 0 imports from `core/` to any feature package (automated check).
- **SC-004**: 100 % of core public functions have a contract and input validation; 100 % of pure core functions
  have at least one offline test; the offline test suite runs in under 30 s without AEDT.
- **SC-005**: Only one template-CSV reader remains in the package (was 3).
- **SC-006**: Adding a dummy registry entry needs 1 new file and 0 edits to existing files (shown by test).
- **SC-007**: The roadmap lists 13 numbered features (002-014), each with type and regression gate.

> **Note 2026-11-05 (converge T037)**: `specs/ROADMAP.md` rev 2, agreed with the user, replaces the 002-014 list
> of US4 / SC-007 with features 002-008 (003 interface sim, 004 review layout, ...; stackup config still postponed).
> US4 and SC-007 are checked against rev 2.

## Assumptions

- `aedt_env.py` stays at `aedt_copilot/aedt_env.py` (public path used by the server and CLI) and is treated as part
  of the core layer; `core/edb.py` wraps it. Moving it is not needed.
- Registry entries declare an explicit `ORDER` (number) because order matters (e.g. `classify_ends` before
  cleanup); discovery is automatic so a new rule = one new file. `pi_dc` `SKILLS` is migrated to the registry in
  009, not in 002.
- `cut_board.config.build_params` (sweep rule, Excel validation) stays in `cut_board` until feature 004.
- Running the AEDT regression (~6 min) and the PI-DC check during implement needs the user's OK (machine use);
  planning does not run AEDT.
- Unit tests use the standard library test runner (no new dependency in `requirements.txt`).
- Work stays on branch `main` (single-owner repo); spec folder `specs/002-architecture-core`.
