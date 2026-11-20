# Feature Specification: No severity, standard answer, netlist-based schematic check (036)

**Feature Branch**: `main` (no branch; repo works on main)

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "bạn triển khai plan trên đi" — the 6-point plan agreed in chat on 2026-11-14/15 after a
test of 3.0.0 in another session (board BOARDA, interface PCIE_HSA2HSB):

1. Remove the HIGH / MEDIUM / INFO severity classification completely. A rule only says OK / NOT OK against its
   threshold. Claude never classifies findings; the user is 100 % responsible.
2. The channel answer is produced by the tool as ready text (3 parts: cut area + review file + one question); Claude
   pastes it, adds nothing.
3. The request accepts a schematic NETLIST file (Altium Protel 2.0, Cadence Allegro / Telesis); connectivity and part
   values come from it, not from reading the PDF.
4. Board vs schematic comparison by pins, not by net names; unreadable pins are "board only", a swapped 1 / 2 pin of a
   2-pin part is not a difference.
5. Series parts (C / R / L) become 0 Ω by team default: never asked, never mentioned in the answer.
6. Tests and references updated to OK / NOT OK.

## Background (observed 2026-11-14, 3.0.0 test session)

- The answer to "cut PCIE_HSA2HSB" contained: steps done, a severity disclaimer, "7 HIGH, 11 MEDIUM, 45 INFO", a list
  of board vs schematic differences with Claude's own proposal, a note on the 220 nF capacitors, and a free-form
  question. The guide asked for 3 parts only, but it is prose; the tool returned loose data (counts by severity).
- The differences were false: J25 pins C19 / C20 / C16 / C17 sit behind Altium off-page connectors (the net has another
  name on the other sheet, sometimes renamed inside a block diagram), so the PDF reader left them out; the 4 AC caps
  were flagged for pin 1 / 2 orientation.
- The user's Altium netlist (Protel 2.0, 9 339 parts, 4 084 nets) gives `PCIE_HSA2HSB_L0_P*` = U14.AT54 + C951.1 and
  `PCIE_HSA2HSB_L0_P` = C951.2 + J25.C19, i.e. exactly the board connectivity, with part values (`220nF`) in the part
  type.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review says OK / NOT OK only (Priority: P1)

The engineer reads a review (HTML, tool results, chat answer, approval record) and sees, per check, OK or NOT OK with
the measured value and the limit. No severity word or severity count exists anywhere. Whether to cut is the engineer's
call.

**Why this priority**: user rule — Claude must not judge findings; severity words in the answer were the main
complaint.

**Independent Test**: run a review on a board copy (board1 U21_J25, BOARDA PCIe) and search every output (review
record, tool result, HTML, approval in user_settings, guides, rule files) for HIGH / MEDIUM / INFO / severity: none.

**Acceptance Scenarios**:

1. **Given** a channel with measured values beyond limits, **When** the review runs, **Then** each such item is NOT OK
   with value and limit, and the result gives only the number of NOT OK items per check.
2. **Given** a former "INFO" case (e.g. reference plane change with a GND via within the limit, other-net via
   clearance), **When** the review runs, **Then** the item is OK (not a finding in the NOT OK list).
3. **Given** the engineer approves a review with NOT OK items, **When** the approval is recorded, **Then** the record
   holds the NOT OK count per check, not severity counts.
4. **Given** a review record from 3.0.0 (with severities), **When** the gate is checked, **Then** it is out of date
   and must be measured again (no silent reuse of severity data).

---

### User Story 2 - The tool writes the channel answer (Priority: P1)

After trace + review + preview, the tool returns the complete answer text for the channel: the cut area picture with
its title and one line per end, the review file path, and the question "Đọc review rồi xác nhận cut <name>?". Claude
sends the picture and pastes the text unchanged.

**Why this priority**: same complaint; prose rules in the guide were not followed.

**Independent Test**: on a board copy, run the channel request; the tool result contains the answer text; the guide
says to paste it verbatim; the answer contains no step narration, no counts, no notes about series parts.

**Acceptance Scenarios**:

1. **Given** review and preview are done, **When** the answer is requested, **Then** the text has exactly the 3 parts
   in the agreed language (Vietnamese) with absolute paths.
2. **Given** the review or preview is missing or failed, **When** the answer is requested, **Then** no answer text is
   produced; the reason is returned instead.
3. **Given** the tool needs a question from the user (end candidates, a real pin difference, a no-GND end), **When**
   the answer is built, **Then** that question is part of the answer text, one line per item, before the final
   question.

---

### User Story 3 - Schematic connectivity from a netlist (Priority: P1)

The engineer gives a netlist file exported from the schematic tool together with (or instead of) the PDF. The tool
reads it itself: components with values and nets with pins. Claude does not read the PDF for connectivity.

**Why this priority**: PDF reading cannot follow off-page / block renames reliably; the netlist is exact.

**Independent Test**: start a request on the BOARDA copy with the user's Protel netlist; trace PCIE_HSA2HSB; zero
board vs schematic differences; C951 value 220 nF from the netlist.

**Acceptance Scenarios**:

1. **Given** a Protel 2.0 netlist, **When** the request starts, **Then** components (refdes, part, value) and nets
   (name, pins) are read and saved with the request; counts reported (e.g. 9 339 / 4 084).
2. **Given** an Allegro / Telesis netlist (`$PACKAGES` / `$NETS`), **When** the request starts, **Then** it is read
   the same way.
3. **Given** a netlist whose header names another design, **When** the request starts, **Then** the user is warned
   (design name shown) before it is used; if almost none of the board's components exist in it, it is refused.
4. **Given** both netlist and PDF, **When** content is compared, **Then** the netlist is the connectivity source; the
   PDF is only used when the user asks about a page.
5. **Given** an unknown file format, **When** the request starts, **Then** it is refused with the supported formats
   listed.

---

### User Story 4 - Compare by pins, no false differences (Priority: P2)

The board is compared with the schematic by pin connectivity (`refdes.pin` sets per path), not by net names. Only a
real connectivity difference is asked.

**Why this priority**: false differences produce questions the user should not have to answer.

**Independent Test**: unit cases + BOARDA PCIe with the PDF-only schematic.md of the test session: no difference for
J25 pins left unread, no difference for cap pin 1 / 2.

**Acceptance Scenarios**:

1. **Given** schematic net `X*` = {U14.AT54, C951.1} and `X` = {C951.2, J25.C19} and board nets with the same pins
   but other names, **When** compared, **Then** no difference is reported (names may differ).
2. **Given** a component whose pins the schematic does not list (PDF unreadable), **When** compared, **Then** its board
   pins are "board only" information, not a difference, and no question is asked.
3. **Given** a 2-pin part whose pins 1 / 2 are swapped between board and schematic, **When** compared, **Then** no
   difference.
4. **Given** a board pin that the schematic connects to a different net (real mismatch), **When** compared, **Then**
   one difference with both pin sets is reported and asked.

---

### User Story 5 - Series parts silent by default (Priority: P2)

Series 2-pin parts on the path (C / R / L) are modelled as 0 Ω by team default. The tool never asks about them and the
answer never mentions them. They appear in the self-check and in user_settings; the GATE B form is where the engineer
changes the handling.

**Independent Test**: PCIe channel (4 AC caps): no question, no answer line about them; self-check lists the 4 parts
shorted.

**Acceptance Scenarios**:

1. **Given** a channel with series caps, **When** the answer is produced, **Then** it contains no line about them.
2. **Given** the engineer opens the GATE B form, **When** looking at series handling, **Then** the parts and the
   default (0 Ω) are visible and editable as today.

### Edge Cases

- Netlist net names with `*`, `+`, `-`, spaces or lower case: kept exactly; pairs found by the existing pair rules.
- Protel component block with a value only in the part type text (e.g. `CAP,CER,220nF,20%…`): value taken from the
  part type; no value found → empty (not a difference).
- Netlist bigger than 400 000 lines (BOARDA 7.8 MB): read in a few seconds, once per request.
- Two netlist sections in one file (seen in an Allegro export): read once; duplicate net names merged, conflicting pins
  reported as a warning.
- Board refdes missing in the netlist (mechanical parts, test points): not a difference.
- Re-cut of a 3.0.0 request: its review approval is out of date (schema change), review runs again; settings reused.
- A rule whose threshold is missing: the check is reported incomplete (no OK / NOT OK), as today.

## Requirements *(mandatory)*

### Functional Requirements

Severity removal (US1)

- **FR-001**: Every review check MUST give each measured item OK or NOT OK from its threshold. No severity level
  exists in the code, records, results, report, guides or rule files.
- **FR-002**: Items that were INFO before MUST be OK and not listed among findings; data tables in the report keep the
  values.
- **FR-003**: Results and the approval record MUST give the number of NOT OK items per check (and incomplete / failed
  checks); no severity counts.
- **FR-004**: The review record schema MUST change so 3.0.0 records are not reused; the gate status becomes out of
  date for them.
- **FR-005**: The review HTML MUST stay OK / NOT OK (as since 2.11.0) with no severity anywhere, including hover text.

Standard answer (US2)

- **FR-006**: After a successful review and preview of a channel, the tool MUST return the full answer text (3 parts,
  Vietnamese, absolute paths, question "Đọc review rồi xác nhận cut <name>?").
- **FR-007**: Questions the tool cannot decide (end candidates, real pin differences, no-GND end) MUST be included in
  the answer text, one line each, before the final question; nothing else is added.
- **FR-008**: The guide MUST instruct Claude to send the picture and paste the answer text verbatim, with no extra
  sentences; details only when the user asks.

Netlist (US3)

- **FR-009**: The request MUST accept an optional netlist file; supported: Protel netlist 2.0 (Altium) and Allegro /
  Telesis (`$PACKAGES` / `$NETS`).
- **FR-010**: The tool MUST parse components (refdes, part, value) and nets (name, pins) and store them with the
  request; the schematic summary reports counts and the source (netlist / PDF).
- **FR-011**: With a netlist, connectivity and values MUST come from it; Claude does not read the PDF for connectivity.
- **FR-012**: A netlist for another design MUST be detected (header name, share of board components found) and the
  user warned or the file refused.

Comparison (US4)

- **FR-013**: Board vs schematic comparison MUST use pin connectivity per net; net names alone never make a
  difference.
- **FR-014**: Pins of components the schematic does not describe MUST be "board only", not a difference.
- **FR-015**: A swapped pin 1 / 2 of a 2-pin part MUST NOT be a difference.
- **FR-016**: Only real connectivity differences (and missing nets between the two ends) MUST be asked.

Series parts (US5)

- **FR-017**: Series 2-pin parts MUST be shorted (0 Ω) by default without a question and without a line in the
  answer; listed in self-check and user_settings; changeable in the GATE B form.

Tests (all)

- **FR-018**: Unit tests, goldens and AEDT checks MUST be updated to OK / NOT OK counts; cut results (ports, GND vias,
  planes, pin shift) MUST stay identical to 3.0.0.

### Key Entities

- **Check result**: check name, items with value / limit / OK or NOT OK, incomplete flag.
- **Netlist**: source file, format, design name, components (refdes, part, value, pin count), nets (name, pins).
- **Schematic difference**: path / net, board pins, schematic pins, kind (real mismatch, missing net); "board only"
  items kept as information.
- **Channel answer**: picture path, title, end lines, review path, questions, final question.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 occurrences of severity words (HIGH / MEDIUM / INFO / severity) in any review output, approval record,
  guide or rule file.
- **SC-002**: The channel answer for BOARDA PCIE_HSA2HSB is exactly the tool's answer text: 3 parts, no other sentence.
- **SC-003**: BOARDA PCIE_HSA2HSB with the user's netlist: 0 board vs schematic differences, 0 questions besides the
  final one.
- **SC-004**: The BOARDA netlist (7.8 MB) is read in under 10 s.
- **SC-005**: Cut results on board1 and BOARDA copies identical to 3.0.0 (ports, GND vias, planes, pin shift).

## Assumptions

- The user exports the netlist; the tool never runs Altium / Allegro.
- Netlist and board come from the same design revision; a mismatch is a real difference to ask.
- The PDF path stays for users without a netlist (with the pin-based comparison and "board only" rule).
- NOT OK is decided by the existing thresholds (`review.*` template rows); no threshold changes in this feature.
- MAJOR version 4.0.0 (tool results change: severity fields removed, new answer field, new start argument).
- Answer language is Vietnamese (the team's language); other languages out of scope.
