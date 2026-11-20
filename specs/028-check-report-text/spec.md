# Feature Specification: Report text lives in the review check file

**Feature Branch**: `028-check-report-text` (work stays on `main`, no branch workflow)

**Created**: 2026-11-10

**Status**: Draft

**Input**: User: "Why/Fix trong file luật". Adding a layout review check must be ONE file in
`aedt_copilot/review_checks/`. Today the report text of the 4 checks (title, labelled rows, Why / Fix, limit key,
involved layers for the picture, report section) is hard-coded in `cut_board/review_report.py` by check name; a new
check gets a raw line, "involved layers unknown", and is not even measured by the HTML report.

## Clarifications

### Session 2026-11-10

- Decisions given with the request (no open question): optional, documented interface in each check module;
  `review_report` reads it through the registry; generic fallback for a check without it; output byte-identical for
  the 4 existing checks (golden from 2.6.0); example skeleton not registered + "How to add a review check" note;
  AEDT check = `review_check.py` on a board1 copy; release 2.6.1.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A new rule = one file (Priority: P1)

A developer adds `review_checks/<rule>.py` with NAME / ORDER / TITLE / SEVERITY_RULE / run and its report text
(title, labelled rows, Why, Fix, limit key, involved layers, report section). The rule is measured by
`design_review` / `isim_review` AND appears in the HTML report with labelled rows, Why / Fix and a picture of the
involved layers, with no change elsewhere.

**Independent Test**: a fake check module registered in a unit test: its findings get their own section (or the one
it names), rows / Why / Fix from the module, picture layers from the module.

**Acceptance Scenarios**:

1. **Given** a new check module with the report interface, **When** the HTML is built, **Then** its findings use the
   module's text and layers.
2. **Given** a new check module without the interface, **When** the HTML is built, **Then** a generic block is shown
   (location, layer, measured value) and the picture shows the issue layer only with a note (as today).
3. **Given** the registry, **When** the contract test runs, **Then** every check module either implements the
   interface for every finding name it produces or is listed as data-only.

### User Story 2 - Nothing changes for the 4 existing checks (Priority: P1)

**Independent Test**: golden HTML / explain output from 2.6.0 equal byte for byte (unit); board1 `review_check.py`
HTML identical (AEDT, copy).

### Edge Cases

- One module produces several finding names (vias: Via stub, Nearest GND via, Ref plane change) → interface keyed by
  finding name; a finding may name a section owned by another module (Ref plane change → Reference).
- Two modules describe the same finding name → registry error (refused at load in the contract test).

## Requirements *(mandatory)*

- **FR-001**: Each check module MAY define `REPORT = {finding check name: {...}}` with `section`, `title`,
  `limit_key`, `describe(f, P, channel) -> (rows, why, fix)`, `layers(f, ref_layers, metal) -> (signals, planes)`.
- **FR-002**: `review_report` builds section / title / text / layers from the registry `REPORT`s; fixed section order
  Reference, Trace stub, Via, Routing, then new sections in registry order.
- **FR-003**: Generic fallback for findings without `REPORT` (today's behaviour for unknown checks).
- **FR-004**: The HTML report measures registry checks that are not part of the built-in four (findings added to the
  channel before ids / points), so a new check reaches the report.
- **FR-005**: The 4 existing checks' report output is byte-identical to 2.6.0 (golden).
- **FR-006**: Example skeleton `review_checks/_example.py` (underscore = not registered) + "How to add a review
  check" in `guides/review_measure.md` (developer part) and a CLAUDE.md developer note.
- **FR-007**: Contract unit test over the registry (interface complete or data-only; no duplicate finding name).

## Success Criteria *(mandatory)*

- **SC-001**: golden HTML + explain equal (unit); board1 HTML from `review_check.py` identical apart from date /
  timing.
- **SC-002**: a fake new check renders labelled rows / Why / Fix / layers in a unit test without touching any other
  file.

## Assumptions

- Patch release 2.6.1 (internal refactor + extension point; no tool / schema change).
