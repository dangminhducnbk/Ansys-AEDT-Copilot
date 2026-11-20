# Feature Specification: Atomic design tools

**Feature Branch**: `007-atomic-design-tools` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User question 2026-11-06 (relayed by the parent session, agreed in principle): "Các feature có trong copilot
là các hàm set cứng, không thể gọi riêng rẻ từng cái như tạo port, set frequency hả?" Today the MCP tools are whole
processes (`isim_cut`, `isim_apply`, `start_cut_batch` ...). Proposed: one tool per operation on ANY existing design
(not only interface-simulation output): ports, setup, sweep, airbox, solder ball; template defaults; input
validation; copy by default; backup; read-back check after each operation; short report; a usage guide.

## Clarifications

### Session 2026-11-06

- Q: Design input? → A: `.aedb` only (EDB, optional cell name). PyEDB, no AEDT session needed (same as the cut).
- Q: Copy or in place? → A: on a COPY by default (`<name>_<op>_<time>.aedb` next to the original, path reported, like
  layout edit); `in_place=true` edits the given `.aedb` after a backup `<name>_old_<time>.aedb`.
- Q: Approval? → A: copy mode runs without a gate (original stays safe; result reported); in-place mode needs the
  engineer's explicit go (server gate flag `user_approved_in_place`).
- Q: Tools in v1? → A: all five: setup, sweep, airbox, ports, solder balls.

## Problem

- An engineer with a design made by hand (or by another tool, or an older cut) cannot ask the copilot for one step
  only, e.g. "tạo port cho net X", "đổi sweep lên 20 GHz", "thêm solder ball cho U5". The only way is a whole
  process that expects its own request / state files.
- The code for each step already exists inside the cut flow, but it is reachable only through those processes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Set simulation setup / sweep / airbox on any design (Priority: P1)

The engineer points to a design and asks to set the adaptive frequency, passes, delta S, arc step, a sweep or the
airbox. The agent shows the values (team defaults + the engineer's changes), the engineer approves, the tool applies
them, reads them back and reports what changed and where the result is.

**Why this priority**: the most frequent single change ("set frequency"), and the code is the most proven.

**Independent Test**: on a copy of a board1 cut design: set sweep 0–20 GHz step 0.05 and max passes 25; the report
lists the old and new values; a read-back shows exactly those values; nothing else in the design changed.

**Acceptance Scenarios**:

1. **Given** a design and new setup values, **When** applied, **Then** the setup is created or replaced with those
   values (others = team defaults) and read back equal.
2. **Given** a sweep request, **When** applied, **Then** the sweep of the chosen setup has the new start / stop / step
   / type, read back equal; invalid values (step > span, stop ≤ start) are refused with the rule, nothing changed.
3. **Given** airbox values, **When** applied, **Then** every airbox value is read back equal.
4. **Given** any operation, **When** it finishes, **Then** a short report lists each changed item (old → new), the
   result design path and the backup path.

---

### User Story 2 - Create or change ports (Priority: P1)

The engineer asks for coax ports on chosen nets of chosen components (or chosen pins). The tool creates them with the
team naming rule (`<refdes>.<pin>.<net>`), reports the count and the ports that could not be created (with reason).

**Why this priority**: the second request named by the user ("tạo port").

**Independent Test**: on a copy of a cut design without ports on one end: create ports for its signal nets; count =
signal pins of those nets; names follow the rule; existing ports are kept unless the engineer asked to replace them.

**Acceptance Scenarios**:

1. **Given** a component and nets, **When** ports are created, **Then** one coax port per pin of those nets is added
   and listed; pins already with a port are skipped and listed.
2. **Given** "replace", **When** applied, **Then** the old ports of those pins are removed first and listed.
3. **Given** a net or refdes not on the design, **When** called, **Then** the input error names it with the closest
   names; nothing changed.

---

### User Story 3 - Solder balls on chosen components (Priority: P2)

The engineer asks for solder balls on chosen components with the team rule (diameter = ratio × short side of the
signal pad, height, shape, material) or given values; the tool sets them and reads them back.

**Why this priority**: less frequent; follows the same pattern.

**Independent Test**: on a copy: set solder balls on U14 with defaults; read-back diameter / height in mm equal the
rule; other components unchanged.

**Acceptance Scenarios**:

1. **Given** components and solder-ball values, **When** applied, **Then** each component's solder ball has those
   values (mm strings, not plain doubles) read back equal.
2. **Given** a component without pads on an outer layer, **When** called, **Then** it is reported as skipped with the
   reason.

### Edge Cases

- Design open in AEDT by the engineer (`.lock`) → refuse; never delete the lock.
- Design made by the interface-simulation process → allowed; the tool says that the process's own records
  (`user_settings`, state) are not updated by an atomic tool, and suggests the re-apply path for those designs.
- Setup name not found for a sweep → refused, existing setup names listed.
- Values outside the template rules → refused with the same messages as the settings table.
- Several operations in a row on the same design → each one is recorded in the report; each backup kept.
- Old flows (Excel cut, interface simulation) are unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST offer separate operations: setup, sweep, airbox, ports, solder balls; each callable alone
  on an existing design.
- **FR-002**: The design input MUST be an existing `.aedb` folder (an `.aedt` path is mapped to its `.aedb`, as
  elsewhere), with an optional cell name (default: the only / first cell).
- **FR-003**: Each operation MUST work on a copy `<name>_<op>_<time>.aedb` by default (original untouched); with
  `in_place=true` it MUST back up to `<name>_old_<time>.aedb` first and then edit the given design.
- **FR-004**: Default values MUST come from the team template (Principle III); the engineer's values override them.
- **FR-005**: Every input MUST be validated before any design change (types, ranges, sweep rule, existing nets /
  refdes / setup); errors name the input and the expected value (Principle VII).
- **FR-006**: After each operation the tool MUST read the changed values back and report mismatches.
- **FR-007**: Each operation MUST produce a short report: changed items (old → new), skipped items with reason,
  result path, backup path.
- **FR-008**: Copy mode needs no gate; in-place mode MUST be refused unless `user_approved_in_place=true` is set
  after the engineer's explicit go in the conversation (Principle I).
- **FR-009**: A guide `design_tools` MUST describe when to use these tools vs the cut / interface-simulation
  processes, and every rule above (Principle IV).
- **FR-010**: No existing tool, guide, prompt, template key or output folder changes (Principle IX). Version minor
  (0.10.0).

### Key Entities

- **Design target**: path (and design name if needed), resolved EDB, lock state.
- **Operation request**: operation name, values (template keys or operation fields), targets (nets / refdes / pins /
  setup name).
- **Operation report**: changed items (old → new), skipped, read-back result, result path, backup path, time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the 5 operations can be called alone on a board1 cut design copy and reports read-back OK.
- **SC-002**: 100 % of invalid inputs are refused before any file change (offline tests).
- **SC-003**: 0 changes to the engineer's original files unless the agreed in-place rule allows it, and then only
  after a backup.
- **SC-004**: An operation on a design changes only the items it names (other setup / ports / components identical
  before / after on a board1 copy).
- **SC-005**: Existing references (`tests/regression.py`, `tests/isim_check.py`, unit tests) still PASS.

## Assumptions

- The operations reuse the cut flow's own code for setup, sweep, airbox, ports and solder balls (same results as in a
  cut).
- One design per call; batch over many designs is out of scope for v1.
- Merge into a workspace and simulation runs are out of scope (existing tools do them).
