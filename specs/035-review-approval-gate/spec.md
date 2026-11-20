# Feature Specification: Review approval by the user before cut (035)

**Feature Branch**: `035-review-approval-gate` (work on `main`, spec folder only)

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "tôi muốn quy trình thêm bước xuất review HTML trước, người dùng đọc, đồng ý thì mới cho cut. Bỏ đi các gating medium hay high trong quy trình, quyết định 100% bởi người dùng. Ngoài ra, tôi muốn quy trình phải chuẩn hóa, không hỏi hay in ra thông tin quá nhiều. Người dùng yêu cầu channel nào, bạn phân tích rồi in ra nội dung ngắn gọn."

## Context (today, 2.12.0)

| Item | Today | Problem |
|---|---|---|
| Layout review in interface simulation | Mandatory, measured right after the channel is traced | User never sees the HTML report unless asking for it |
| Gate | Code verdict: HIGH or incomplete review = STOP, cut refused; CONTINUE = Claude goes on | Severity decides, not the engineer; CONTINUE never waits for the engineer to read |
| Ways past a STOP | per-point decisions with reasons, or "cut anyway" override with reason | Extra questions and tools; the engineer has already read the report |
| Chat output | Content table, review summary, MEDIUM / INFO points, preview tables, questions spread over many messages | Too long; varies from run to run |

## Clarifications

### Session 2026-11-14

- Q1: Content confirmation (GATE A) and review approval: merged or separate? → A: ONE approval (content + cut area + review).
- Q2: Override / per-point decision tools? → A: removed.
- Q3: Cut preview? → A: always run before the approval question.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the review report, then decide (Priority: P1)

The engineer asks for a channel. The tool measures the layout review, writes the HTML report and gives its path. The
engineer opens it, reads it and answers "đồng ý" (cut) or not. Only after that answer can the channel be cut. The
severities in the report (NOT OK items, HIGH / MEDIUM inside) are information only: no severity blocks or allows the
cut by itself.

**Why this priority**: it is the core request: the decision is 100 % the engineer's, made after reading the report.

**Independent Test**: on a copy of a board with HIGH findings (PCIe test1, 7 HIGH) and one without (board1
CPHY_U14_U26): in both cases the cut is refused before the engineer's approval and accepted after it; no override and no
per-point decision is needed for the HIGH board.

**Acceptance Scenarios**:

1. **Given** a traced channel, **When** the review is done, **Then** the HTML report exists and its absolute path is
   sent to the engineer with the cut-area preview, whatever the findings.
2. **Given** the report was shown and the engineer has not approved, **When** a cut of that channel is requested,
   **Then** it is refused with the reason "review not approved by the user".
3. **Given** a channel with HIGH findings, **When** the engineer approves, **Then** the cut is allowed (no override,
   no reason required).
4. **Given** a channel with no findings, **When** the engineer has not approved, **Then** the cut is still refused.
5. **Given** an approval, **When** the board is saved again, or the channel ends / nets change, **Then** the approval no
   longer counts: a new review + report + approval is needed.
6. **Given** an approval, **When** the request is inspected later, **Then** the record shows who approved what: time,
   report file, finding counts at that time.

---

### User Story 2 - Channel request answered with cut area + review file + one question (Priority: P1)

User 2026-11-14: "Không cần mục tóm tắt channel, người dùng yêu cầu channel, in ra phần vùng cut dự tính và gửi file
review cho người dùng. Hỏi người dùng đọc review và xác nhận cut hay không."

The engineer names a channel. Claude traces it, runs the review and the cut preview, then answers with ONLY: the planned
cut area (preview image + one line per end: factor, GND kept), the review HTML file (sent as a file / absolute path) and
one question: "Đọc review rồi xác nhận cut <channel>?". No channel content table, no list of findings, no explanation.
Other questions only when the tool cannot decide (more than one end candidate, board vs schematic difference).

**Why this priority**: the user wants the process standard and quiet; it is used on every channel.

**Independent Test**: run the flow on board1 CPHY_U14_U26 and test1 PCIe: the answer to the channel request has the same
three parts (cut area, review file, question) both times and nothing else.

**Acceptance Scenarios**:

1. **Given** a channel request, **When** analysis is done, **Then** the chat shows the cut-area preview, the review file
   and one question, nothing else.
2. **Given** the engineer answers yes, **Then** that one answer confirms the channel content, the cut area and the review
   (one approval) and the cut starts.
3. **Given** an ambiguity (end candidates, schematic difference), **Then** it is asked before the preview / review, as a
   short numbered question.
4. **Given** several channels in one request, **Then** the same three parts per channel.
5. **Given** the engineer asks for details (nets, series parts, findings), **Then** Claude answers from the tool data;
   these details are never printed unasked.

---

### User Story 2b - Settings by input table (form), not by chat questions (Priority: P1)

User 2026-11-14 (screenshot of a test chat: after the cut, Claude asked the sweep range in a chat question with two
buttons): the settings input table (feature 005, one tab per interface, pre-filled, editable) already exists and MUST be
used. After the cut, the engineer gets the settings form; mandatory sweep values are typed there; the form submit is
validated and the table shown; the engineer's go applies.

**Independent Test**: on a copy, after the cut the next message is the settings form (or its table when the client
cannot draw forms), never a free-text / button question for sweep values.

**Acceptance Scenarios**:

1. **Given** a cut channel, **When** settings are needed, **Then** the settings form is shown pre-filled; no separate
   question per value.
2. **Given** a client that cannot draw forms, **Then** the full settings table is shown once and the engineer edits by
   text.
3. **Given** the stage before settings, **Then** the tool result itself says that the next step is the settings form
   (so the flow does not depend on Claude remembering the guide).

---

### User Story 3 - Same rule in standalone review (Priority: P2)

Standalone review (`design_review`, any board) no longer prints a STOP / CONTINUE verdict. It reports the findings and
the report path. Design-tool cuts (cutout) are not gated by review today and stay so.

**Why this priority**: consistency of wording; small.

**Independent Test**: standalone review on test1 PCIe: result has counts + report, no STOP word in the summary.

**Acceptance Scenarios**:

1. **Given** a standalone review, **When** it finishes, **Then** the summary gives counts per section and the report path,
   and no verdict.

### Edge Cases

- Review incomplete (a check failed, channel not traced): the report still lists the failed check at the top; the
  engineer decides (approve or not). Approval of an incomplete review is recorded as such.
- Report could not be written (disk / picture error): no approval possible; the error is shown.
- Engineer approves only some channels of a request: the others stay unapproved; cut refused only for those.
- Re-cut "như lần trước" (Phase R): a reused review (same board / ends / nets) still produces a report and needs a new
  approval in this request; the previous approval is shown as information.
- Old requests made with 2.12.0 (STOP / override / decisions in user_settings.json): read without error; their
  override / decisions are shown as history but do not count as approval for a new cut.
- Engineer answers "đồng ý" to something else (e.g. while discussing): only an explicit approval of the cut of that
  channel after the report was shown counts (constitution Principle I).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: After a channel is traced in interface simulation, the review MUST always produce the HTML report and
  return its absolute path (no longer only on request).
- **FR-002**: The cut of a channel (content confirmation and cut) MUST be refused until the engineer's approval of that
  channel's current review is recorded. The refusal is enforced by the tool, not only by the guide.
- **FR-003**: The approval MUST be given only after the engineer's explicit go in the conversation, after the report
  path was shown; it carries no required reason.
- **FR-004**: No severity (HIGH, MEDIUM, NOT OK) and no review verdict MAY block or allow a cut by itself. The STOP /
  CONTINUE verdict MUST NOT appear in chat summaries, reports or status any more.
- **FR-005**: The "cut anyway" override and the per-point decision steps MUST be removed from the interface-simulation
  flow (they are replaced by the approval); the decision / override tools are removed (user: decision 100 % the
  engineer's, one go).
- **FR-006**: An approval MUST be bound to the review it approves (board state, ends, nets, checks, thresholds). Any
  change makes it invalid; status shows "approval out of date".
- **FR-007**: The approval record MUST store time, report file, review record, finding counts per severity and the
  engineer's words, in the request's settings file.
- **FR-008**: The request status MUST show per channel: review measured / report / approved / out of date.
- **FR-009**: The answer to a channel request MUST contain only: the planned cut area (preview image(s) + one line per
  end), the review HTML file, one approval question. No channel summary / content table / finding list unasked.
- **FR-010**: Claude MUST ask only questions the tool cannot settle: end candidates, board vs schematic differences,
  and the approval. Everything with a team default is used, not asked.
- **FR-011**: ONE approval per channel confirms the content, the cut area and the review (today's GATE A + review
  decision in one go).
- **FR-012**: The cut preview MUST always run before the approval question (it is the "vùng cut dự tính"). The image
  shown is the FINAL cut region (added end areas merged, one outline; no base line, no separate added area, no other-net
  hatch) — user 2026-11-14 on the demo.
- **FR-015**: Settings after the cut MUST be entered with the settings form (feature 005) when the client can draw
  forms, else the full settings table once; never one chat question per value. The cut / end-check result MUST name the
  form as the next step.
- **FR-013**: Standalone review summaries MUST give counts + report path without a verdict (US3).
- **FR-014**: Guides (interface_sim, review_measure, catalog) and tool descriptions MUST state the new rule; existing
  checks (regression, isim, PCIe, review gate) MUST be updated to the approval flow.

### Key Entities

- **Review approval**: engineer's go for one channel's current review; time, report path, review record, counts,
  engineer's words, validity key.
- **Channel answer**: cut-area preview + review file + one approval question (US2).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100 % of test runs, no channel is cut without a recorded approval, and every channel with a recorded
  approval can be cut regardless of its findings (PCIe 7 HIGH included).
- **SC-002**: The engineer gets the report path in the first message after the channel analysis, every time.
- **SC-003**: Questions per channel without ambiguity: 1 (approval) — today ≥ 2 (content + STOP decision / override).
- **SC-004**: The answer to a channel request has exactly the 3 parts of US2 on board1 and test1; settings are entered through the form in 100 % of runs (0 per-value chat questions).
- **SC-005**: Cut results (ports, GND vias, planes, pin shift) on board1 / test1 copies identical to 2.12.0.

## Assumptions

- Review measurement, report content and finding severities are unchanged; only their use as a gate changes.
- HIGH / MEDIUM stay inside the review data (report OK / NOT OK, JSON) as information.
- Gates B (settings), C (merge), D (run) and `user_approved_gnd` are unchanged.
- Removing tools / flags changes the tool interface → MAJOR version (3.0.0).
- Report generation on the snapshot takes seconds (2.6+), so always producing it does not slow the flow noticeably.
