# Feature Specification: Layout review gate (mandatory review + stop before cut)

**Feature Branch**: `claude/025-review-gate-ca985b` (worktree; merged into `main` by the owner)

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Bước layout review phải tách ra làm 1 "công thức nấu ăn" độc lập, nếu layout không ổn,
tôi có quyền không cut và chạy simulation." and "Trong quy trình cắt, bước review là bắt buộc sau khi người dùng cung
cấp channel, nếu lỗi nặng thì báo người dùng dừng lại, không cut. Bản thân quy trình review cũng có thể chạy độc lập".

## Clarifications

### Session 2026-11-10

User answer (via parent session): "Q1–Q5 đều A".

- Q1: After a STOP, may the engineer still cut? → A: yes, two ways, both only from the engineer's explicit words and
  recorded: (1) an interface override "vẫn cut" = explicit approval flag `user_approved_review_override` + reason,
  stored in `user_settings.json`; (2) per-point downgrade / dismiss of HIGH points with a reason through the existing
  decision step (`isim_review_decide`) — the verdict is recomputed from final severities.
- Q2: MEDIUM / INFO → A: report only, never stop.
- Q3: Incomplete review (a check error, channel not traced) → A: STOP like HIGH; the engineer decides per Q1.
- Q4: Standalone review report → A: chat summary + verdict file under `<board dir>/Ansys AEDT Copilot/reviews/`;
  HTML with images only on request.
- Q5: Reuse / re-cut → A: reuse only when board unchanged (snapshot key) + same ends / nets + all 4 checks + same
  thresholds, else measure again; a previous "vẫn cut" override is NOT reused — ask again.
- Assumptions kept (not objected): atomic design tools are not locked by the review; requests already past Gate A
  keep apply / re-apply / merge / run; only a new Gate A or cut needs the review.

## Problem

| Today (2.2.0) | Consequence |
|---|---|
| Interface simulation review (`isim_review`) is OPTIONAL and offered only AFTER Gate A | A channel with a severe layout defect (loss of reference, ref plane change without GND via) is cut and simulated: ~5 min cut + hours of solve on a result the engineer would reject |
| Nothing in code looks at review findings before a cut | The stop depends on Claude remembering a guide line |
| Standalone `layout-review` workflow (`design_review`) leaves decisions in chat only | Its result cannot be reused; interface simulation measures again |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mandatory review before the cut of every interface (Priority: P1)

The engineer gives the channels of an interface. Right after the tool proposes the content (trace), the layout of
that interface is reviewed automatically (same checks as today: reference / SOV, trace stubs, vias, routing). The
engineer sees the suspect points with numbers and a verdict per interface: CONTINUE or STOP.

**Why this priority**: it is the user's rule ("bước review là bắt buộc"); without it every other story is optional.

**Independent Test**: on a copy of board1, start a request with interface U14-U26; try to confirm the content (Gate A)
or cut before any review → refused with a message naming the review step; run the review → verdict CONTINUE (INFO
only) → Gate A and cut accepted.

**Acceptance Scenarios**:

1. **Given** an interface traced but not reviewed, **When** Gate A (confirm content) or the cut is requested,
   **Then** it is refused and the message says the review must run first.
2. **Given** a review stored for nets / ends that differ from the content sent to Gate A, **When** Gate A is
   requested, **Then** it is refused (review is out of date) until the review is run again for the agreed content.
3. **Given** a stored review whose board has changed since (board saved after the review), **When** Gate A or the
   cut is requested, **Then** it is refused as out of date.
4. **Given** a review with only MEDIUM / INFO findings, **When** Gate A and cut are requested, **Then** they proceed;
   the findings are shown, nothing stops.

---

### User Story 2 - Severe findings stop the interface (Priority: P1)

A review with HIGH findings (loss of reference; reference plane change without a GND via within the limit) gives
verdict STOP for that interface: the tool reports the points and refuses Gate A, cut, apply and run for it. Other
interfaces of the same request continue normally.

**Why this priority**: "nếu lỗi nặng thì báo người dùng dừng lại, không cut" — the stop must be enforced in code
(Principle I), not only by the guide.

**Independent Test**: on a copy of board1, request with U14-U26 and U21-J25; review both → U21_J25 STOP (2 HIGH),
U14_U26 CONTINUE; Gate A / cut refused for U21_J25, accepted for U14_U26; merge works with U14_U26 only.

**Acceptance Scenarios**:

1. **Given** a review with ≥ 1 HIGH point, **When** Gate A or cut is requested, **Then** refused; the reply lists the
   HIGH points (id, issue, net, layer, x/y) and the ways forward (fix board + review again, or the user's decision —
   see FR-007).
2. **Given** two interfaces, one STOP and one CONTINUE, **When** the user continues, **Then** the CONTINUE interface
   goes through cut / apply / merge; the STOP interface stays at its step and is shown as "stopped by review" in the
   status table.
3. **Given** the board is fixed and saved, **When** the review is run again and finds no HIGH, **Then** the verdict
   becomes CONTINUE and the interface proceeds.

---

### User Story 3 - Standalone layout review with a stored verdict (Priority: P2)

The engineer runs the layout review alone ("công thức nấu ăn" `layout-review`) on any board and channels, without
starting a cut. The result is a chat summary plus a verdict per channel stored in a file next to the board. Later,
when the engineer starts interface simulation on the same board and channel, the stored review is reused instead of
measuring again — when it is still valid.

**Why this priority**: "Bản thân quy trình review cũng có thể chạy độc lập"; reuse saves the measuring time and keeps
one verdict per channel.

**Independent Test**: standalone review of U21-J25 on a board1 copy → verdict file written, STOP; then interface
simulation of the same channel → review step reports "reused" with the same points and verdict, no new measurement;
touch / save the board → next interface simulation measures again.

**Acceptance Scenarios**:

1. **Given** a board and channels, **When** the standalone review runs, **Then** a verdict per channel
   (CONTINUE / STOP + HIGH / MEDIUM / INFO counts + points) is written to a file and its path returned; the board is
   only read.
2. **Given** a stored standalone review of the same board (unchanged), same two ends and same nets, same checks and
   thresholds, **When** the interface review step runs, **Then** it reuses the stored result (says `reused` and the
   file) instead of measuring.
3. **Given** any of: board changed, different nets / ends, fewer checks, different review thresholds, **When** the
   interface review step runs, **Then** it measures again (never reuses silently).

---

### User Story 4 - The engineer's decision on a STOP (Priority: P2)

"Tôi có quyền không cut" — the decision belongs to the engineer. On a STOP the default is no cut. The engineer may
decide otherwise for that interface, and that decision is recorded with their reason.

**Why this priority**: keeps the engineer in control without letting Claude skip the stop.

**Independent Test**: U21_J25 STOP on a board1 copy; record the engineer's decision per FR-007 → Gate A / cut
accepted; the decision (who / when / reason / points) is in the request's settings file and in the status table.

**Acceptance Scenarios**:

1. **Given** STOP, **When** the engineer has not decided, **Then** every attempt to pass is refused.
2. **Given** STOP, **When** the engineer's decision is recorded per FR-007, **Then** Gate A / cut proceed and the
   decision is kept for re-cut ("như lần trước").

---

### Edge Cases

- A check fails to measure (e.g. `no plane layer`), or the channel cannot be traced: the review is incomplete →
  verdict STOP (incomplete) per FR-006.
- Snapshot cannot be used → review runs live (warning) — the verdict is computed the same way.
- Interface content changes after the review (nets added / removed, other end) → old review out of date → Gate A
  refused until reviewed again (the snapshot makes it seconds).
- Interface sent back to Phase 1 (content changed after cut) → `review.json` is kept (not renamed: it is a pre-Gate-A
  artifact); the gate compares it with the new content, so a review of the new content is needed first (decisions /
  override of that review are kept across the reset).
- Re-cut "như lần trước" (Phase R): review again unless a valid review of the same board / content exists
  (FR-011); a previous engineer decision on a STOP is shown, not reused silently.
- Requests created before 025 that are already past Gate A (cut / ends_checked / applied / merged): not blocked
  retroactively for apply / re-apply / merge of what was already cut; a NEW cut (re-cut, Phase 1 again) needs the
  review.
- Interface at a step after Gate A with a review → re-running the review is allowed (read only), it does not move
  the step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The interface review step MUST be available right after the trace (interface proposed, content not yet
  agreed) for the proposed ends and nets, as well as at later steps (as today).
- **FR-002**: Gate A (confirm content) MUST be refused for an interface without a stored review that matches the
  content being confirmed (same two ends, same net set) and the current board (unchanged since the review).
- **FR-003**: The cut of an interface MUST be refused when its review is missing, out of date (FR-002 rule against the
  agreed content) or has verdict STOP without a recorded engineer decision (FR-007).
- **FR-004**: Every review (interface or standalone) MUST produce a verdict per channel: STOP when at least one point
  has final severity HIGH, else CONTINUE; with counts per severity and the list of HIGH points.
- **FR-005**: MEDIUM and INFO findings MUST be reported only; they MUST NOT stop an interface.
- **FR-006**: An incomplete review (a check returned an error, or the channel could not be traced) MUST give verdict
  STOP (reason `incomplete`, the failing checks listed); the engineer decides per FR-007.
- **FR-007**: After a STOP, the interface MUST NOT pass Gate A / cut unless either (a) every HIGH point has a recorded
  engineer decision that makes its final severity non-HIGH or dismisses it (with reason) and the review is complete,
  or (b) the engineer gave an interface override "vẫn cut" — explicit approval flag `user_approved_review_override`
  plus a non-empty reason, checked in code, stored in `user_settings.json` (time, reason, verdict, HIGH points /
  failing checks at that time). Both MUST be passed only after the engineer's explicit words in the conversation.
  An override is bound to the review it was given for: a new review (re-measured or reused) needs a new override.
- **FR-008**: The stop MUST apply per interface; other interfaces of the same request MUST continue; the request status
  MUST show the verdict per interface (CONTINUE / STOP / decided by engineer / not reviewed).
- **FR-009**: The standalone layout review MUST run on any board and channels without a request, read the board only,
  and store the verdict per channel in a file next to the board (inside the tool's output folder of that board), and
  return its path with a chat summary; HTML with images only on request.
- **FR-010**: Engineer decisions in a standalone review (accept / dismiss points, severity change with reason) MUST be
  storable in that verdict file (today they stay in chat).
- **FR-011**: The interface review step MUST reuse a stored review (standalone or from an earlier request) only when:
  same board, board unchanged since that review, same two ends, same net set, all checks of the interface review were
  run, same review thresholds. Otherwise it MUST measure again. The result MUST say `reused` + source file, or
  `measured`.
- **FR-012**: A reused review MUST carry over the stored point decisions; an engineer decision on a STOP (FR-007) is
  NOT carried over silently from another request — it is shown and must be given again.
- **FR-013**: Interfaces already past Gate A when 025 is installed MUST keep working for apply / re-apply / merge /
  run; only a new Gate A or cut needs the review.
- **FR-014**: The guide of interface simulation MUST describe the review as mandatory step 1.5 (after trace, before cut
  preview and Gate A), the STOP message and the engineer's options; the review guide and the `layout-review` workflow
  MUST describe the standalone verdict file and reuse.
- **FR-015**: Review measuring, severity rules, points and numbers MUST stay identical to 2.2.0 (same checks, same
  thresholds); only the verdict, storage, reuse and gates are new.

### Key Entities

- **Review verdict (per channel)**: channel name, ends, nets, board identity (file + change key), checks run,
  thresholds, counts per severity, HIGH points, verdict CONTINUE / STOP, incomplete flag, measured / reused source,
  time.
- **Standalone review record**: file next to the board with the verdicts of one standalone run + engineer point
  decisions; looked up for reuse.
- **Engineer decision on a STOP**: interface, time, reason, points concerned (per FR-007), kept in the request's
  settings file.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 interfaces can be cut without a stored, up-to-date review (offline gate tests cover every path: no
  review, out-of-date nets, changed board, STOP without decision).
- **SC-002**: On board1 copies: U21_J25 → STOP (its 2 HIGH points), U14_U26 → CONTINUE (INFO only); on a test1 copy
  the PCIe interface (19 HIGH) → STOP; the CONTINUE interfaces cut / apply / merge with the 2.2.0 reference numbers
  unchanged (regression.py, isim_check.py).
- **SC-003**: Reusing a valid standalone review in interface simulation takes < 5 s (no measuring) and gives identical
  points and verdict.
- **SC-004**: Review numbers / points of every check identical to 2.2.0 golden (board1 24/0, 29/11; test1 PCIe
  19/46/24).

## Assumptions

- HIGH = the severity suggested by code (2.2.0 rules) unless the engineer changed it with a reason through the existing
  decision step (`isim_review_decide`); the final severity is used for the verdict.
- Atomic design tools (`design_cutout` etc.) are NOT gated by a review: they are single operations on any design; the
  review gate belongs to the interface simulation process. A team workflow that composes them may include the review
  step (guide), not a code lock.
- The review checks run are all four (reference, trace_stubs, vias, routing) for the gate; a review with fewer checks
  is not a valid gate review.
- Board "unchanged" = the layout snapshot key (board database size + modification time), as used by feature 023.
- Depends on feature 024 (request / folder id fix) and 021 (GND pin cleanup) being merged into `main` first; 025 is
  implemented on top of them.
- No new MCP tool is assumed; existing `isim_review`, `isim_review_decide`, `design_review` gain behaviour; any new
  tool follows Principle X (catalog + contract + test).
