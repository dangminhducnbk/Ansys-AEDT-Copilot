# Feature Specification: Review layout — code measures, agent interprets

**Feature Branch**: `011-review-measure` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "okay" — go for ROADMAP 011 "Review layout (measure + interpret)": code gives measurements
per channel as data; the agent interprets with the engineer; optional step of interface simulation after content
agreement; old `review_layout` HTML kept. Earlier discussion (2026-11-06): "Vì sao review layout và đề xuất channel lại
dùng code? LLM không xử lý được hả?" → "trong mục review, bạn nên tách ra nhiều function nhỏ hơn để sau này có thêm
function mới sẽ tiện hơn."

## Clarifications

### Session 2026-11-07

- Q: Who labels severity? → A: C — code gives a suggested severity per item (today's rules); the agent may change it
  only with a stated reason, recorded with the item.
- Q: Report format? → A: C — chat summary by default (table of suspect points with numbers); HTML with images only when
  the engineer asks.
- Q: Where are accept / dismiss decisions saved? → A: A — in the request's existing `user_settings` file (feature 004,
  one file per agreement); no new file.

## Problem

- `review_layout` is one large block (~1200 lines) that measures, judges severity and renders HTML in one pass, only
  inside the Excel cut flow (Gate 1). A new check means editing that block.
- The engineer cannot ask for one measurement alone ("via stub của net X", "SOV trên L3") or on a cut design.
- Severity is fixed in code (HIGH / MEDIUM / INFO); the agent only repeats it, it cannot weigh a finding against the
  interface (speed, length, what the engineer cares about).
- Interface simulation (003) has no layout review step at all.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Measure a channel, one check or all (Priority: P1)

The engineer asks for a review of an interface (or one check, e.g. "stub của via tín hiệu"). Code measures and returns
data per channel: signal vias (type, layers, backdrill, stub, nearest GND via), routing (length per layer, width,
pair / trio layer match), SOV, loss of reference, ref plane change, ref to other net, trace stubs — each item with net,
layer, coordinates and numbers.

**Why this priority**: measurements are the base; interpretation and reports read them.

**Independent Test**: on a board1 copy, measure CPHY_U14_U26 and CPHY_U21_J25 with all checks; numbers equal those of
today's `review_layout` (same counts, lengths, distances); then run one check alone and get the same subset.

**Acceptance Scenarios**:

1. **Given** a board and channels, **When** all checks run, **Then** every check returns its data per channel, and
   results equal today's review numbers on board1.
2. **Given** one check named, **When** it runs, **Then** only that check is measured, on the same data.
3. **Given** a new check added as its own module, **When** the tool runs, **Then** it is listed and run with no change
   to the other checks.
4. **Given** a cut design instead of the full board, **When** checks run, **Then** they work the same (no Excel / job
   needed).

---

### User Story 2 - Agent interprets with the engineer (Priority: P1)

The agent reads the measurements, applies the review rules from the guide and the interface context, and presents a
short summary of suspect points (table), with the evidence numbers. The engineer discusses, accepts or dismisses
points; the agreed outcome is recorded.

**Why this priority**: this is the "agent interprets" goal; code numbers stay objective, judgement is visible and
discussable.

**Independent Test**: board1 copy; agent summary for CPHY_U21_J25 lists the points the old HTML marks HIGH / MEDIUM, each
with its numbers; engineer dismisses one; the record shows it.

**Acceptance Scenarios**:

1. **Given** measurements, **When** the agent summarizes, **Then** each suspect point cites the measured numbers and
   the rule used; nothing is invented beyond the data.
2. **Given** the engineer dismisses or accepts a point, **When** the review is closed, **Then** the decision is saved
   with the review data.

---

### User Story 3 - Optional step in interface simulation (Priority: P2)

After content agreement (Gate A) the agent offers a layout review of the agreed interface before cutting; the engineer
may skip it.

**Why this priority**: brings review to the new process; optional, so it does not block 003.

**Independent Test**: interface simulation on a board1 copy: after Gate A the agent offers review; run it; then cut as
usual; skip on a second request.

**Acceptance Scenarios**:

1. **Given** content agreed, **When** the engineer accepts the review, **Then** it runs on the agreed nets and its
   result is linked to the request.
2. **Given** the engineer skips it, **When** the process continues, **Then** nothing changes from today.

---

### Edge Cases

- Old Excel flow: `review_layout` and its HTML, Gate 1 and `propose_channels` lock stay as today (Principle IX).
- Channel with no plane layer found: checks that need a reference report "no plane layer" instead of failing.
- Large BGA boards: one check alone must not pay for all others (lazy per check).
- A check fails on odd geometry: other checks still return; the failed one reports its error.
- Board open in AEDT (`.lock`): read-only measure still allowed (no write), as today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each review check MUST be its own module in a registry (Principle VIII), with its own inputs, outputs
  and contract; adding a check MUST NOT change other checks.
- **FR-002**: A new read-only utensil MUST measure one, several or all checks for given channels on any board or cut
  design, and return data (no severity verdict required), within the kitchen catalog (Principle X).
- **FR-003**: Measurements MUST equal today's `review_layout` numbers on board1 (same counts, lengths, distances).
- **FR-004**: Thresholds MUST stay in the template `review.*` rows (Principle III).
- **FR-005**: The guide MUST give the agent the interpretation rules (current severity rules as guidance) and the
  summary format; the agent MUST cite measured numbers and never compute geometry itself.
- **FR-006**: Code MUST give a suggested severity per item (HIGH / MEDIUM / INFO, today's rules and `review.*`
  thresholds); the agent MAY change it only with a stated reason, saved with the item (suggested, final, reason).
- **FR-007**: The default report MUST be the agent's chat summary (table of suspect points with numbers); an HTML
  report with images MUST be produced from the same data only when the engineer asks.
- **FR-008**: The engineer's accept / dismiss decisions (and any severity change with reason) MUST be saved in the
  request's existing `user_settings` file (feature 004); no new file. Outside a request (review of any board or design),
  decisions are shown in chat only.
- **FR-009**: Interface simulation MUST offer the review as an optional step after Gate A; skipping changes nothing.
- **FR-010**: The old `review_layout` tool, HTML and Excel-flow gates MUST keep working with identical output.

### Key Entities

- **Check**: one measurement module (name, inputs, outputs, thresholds used).
- **Measurement set**: per channel, per check: items with net, layer, coordinates, numbers.
- **Review decision**: point id, accepted / dismissed, note, time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On board1 copies, 100 % of numbers per check equal today's review (CPHY_U14_U26, CPHY_U21_J25).
- **SC-002**: One check alone on board1 runs in under half the time of all checks.
- **SC-003**: A new check is added with 0 lines changed in other checks.
- **SC-004**: Agent summary of CPHY_U21_J25 lists every point the old HTML shows as abnormal, each with numbers.
- **SC-005**: `tests/regression.py`, `tests/isim_check.py` PASS; old review HTML for board1 unchanged in content.

## Assumptions

- "Code measures" = all geometry and copper hit tests stay in code (the agent cannot read EDB geometry reliably).
- Excel flow review stays as is; this feature reuses its measuring code through the new checks (restructure, same
  results).
- AEDT is not opened graphically; measurement uses EDB on a copy or read-only.
- Version: minor → 0.12.0; restart Claude.
