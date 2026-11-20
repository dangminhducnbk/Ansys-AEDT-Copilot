# Feature Specification: Review first, config only after the user's OK

**Feature Branch**: `main` (no branch; repo owner works on main)

**Created**: 2026-11-16

**Status**: Accepted (user 2026-11-16, multi-channel option A)

**Input**: User description: "tôi muốn đổi lại quy trình. Bước review layout sau khi người dùng chỉ định channel cần cut
phải thực hiện trước, nếu người dùng okay thì mới chuyển qua bước config và cut. Không thì dừng lại."

## Context

5.0.0 (feature 038) fixed process: (1) board + interface → (2) trace, snapshot, cut regions, review (automatic) →
(3) config HTML, **M1** → (4) user saves, **Q1** → (5) errors **M2** → (6) cut region + review file of every channel,
**Q2** "Đồng ý cut không?" → (7) cut, **M3** → (8) merge.

The review report is measured in step (2) but the user first SEES it in step (6), after spending time on the config
page. When the review shows layout problems the user does not want to cut at all, so the config work was wasted.

This feature moves the user's look at the review to right after the channels are named, with its own yes / no
question. "No" ends the process; "yes" continues to the config page and the 038 steps.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the layout review before any config (Priority: P1)

The user names the board and the channels to cut. The tool traces them, measures the layout review and answers with
the review report file of each channel and ONE question: is the review OK, go on to config? Nothing else (no config
page, no cut region) is produced before that answer.

**Why this priority**: it is the change the user asked for; it saves the config time on a board that will not be cut.

**Independent Test**: start a request with one channel on a board copy; the answer holds the review file path and the
review question only; no config page exists in the request folder.

**Acceptance Scenarios**:

1. **Given** a board and 2 channels, **When** the tool finishes trace + review, **Then** the answer lists each
   channel with its review file and the number of NOT OK points, then the review question (Vietnamese + English),
   and the request folder has no config page yet.
2. **Given** the review answer was shown, **When** Claude tries to write the config page before the user answered,
   **Then** the server refuses (the step is locked in code, not only in the guide).

---

### User Story 2 - "OK" continues to config and cut (Priority: P1)

The user reads the review and answers yes. The tool records the approval (with the user's words and the review it
refers to) and continues with the 038 steps: config page M1 → Q1 / M2 → Q2 cut region → cut M3 → merge.

**Why this priority**: without it the process cannot reach the cut.

**Independent Test**: answer yes on the board copy; the config page is written (M1); the rest of the 038 flow runs to
the merged project with the same numbers as 5.0.0 (board1 U14_U26: 24 ports, 126 GND vias, pin shift 0.21 mm).

**Acceptance Scenarios**:

1. **Given** the review question, **When** the user answers "đồng ý" / "ok" / "yes", **Then** the approval is stored
   in the request and the next answer is M1 with the config file path.
2. **Given** an approved review, **When** the user changes the interface content in the config page (other nets) and
   the review is measured again at the check step, **Then** Q2 shows the new review file next to the cut region
   (the user sees the changed review before the cut; no second review question).

---

### User Story 3 - "No" stops the process (Priority: P1)

The user answers no. The tool records the refusal and ends: no config page, no cut, no merge. A later call of any
config / cut step on that request is refused with a message that the review was not accepted.

**Why this priority**: explicit user requirement ("Không thì dừng lại").

**Independent Test**: answer no; the request state shows stopped by the user; isim config / check / go refuse.

**Acceptance Scenarios**:

1. **Given** the review question, **When** the user answers "không" / "no", **Then** the answer is a short closing
   message (Vietnamese + English) with the review file paths, and the request is marked stopped.
2. **Given** a stopped request, **When** config, config check or go is called, **Then** the server refuses and says
   the review was not accepted; the user can start a new request (for example after the board is fixed).

---

### Edge Cases

- Several channels: ONE answer covers all channels of the request (user 2026-11-16, option A). "Yes" → all continue;
  "no" → the whole request stops. To drop one channel the user refuses and starts a new request without it.
- Board changed (edb.def size / time) after the review was accepted and before config: the approval no longer matches
  the review → the review is measured again and the question is asked again.
- Review cannot be measured for a channel (error): the answer shows the error for that channel; no review question
  until every channel has a review report.
- User answers something that is neither yes nor no: treated as a discussion; the question stays open, nothing runs.
- Requests created before this feature (5.0.0) that already passed the config step keep working unchanged (no review
  question inserted into a running request).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** New fixed step order (replaces 038 FR-031 steps 2–3): (1) user gives board + channels; (2) tool traces,
  measures the layout review and writes the HTML report of each channel — automatic; (3) message **M0** + question
  **Q0**; (4a) "no" → message **M0x**, END; (4b) "yes" → (5) cut regions pre-computed + config HTML, **M1**; then the
  038 steps unchanged (Q1, M2, Q2, M3, merge).
- **FR-002** Fixed texts (Vietnamese line first, English line below, generated by the tool, pasted verbatim):
  | id | Vietnamese | English |
  |---|---|---|
  | M0 | Review layout (mỗi channel: file review, số điểm NOT OK): | Layout review (per channel: review file, NOT OK points): |
  | Q0 | Review layout ổn, chuyển sang bước config không? | Is the layout review OK, go on to config? |
  | M0x | Đã dừng theo yêu cầu. File review: | Stopped as requested. Review files: |
  Answers accepted in both languages: "đồng ý" / "ok" / "yes", "không" / "no". M0 is one table (Channel, Review file,
  NOT OK points) followed by Q0; at most one question per answer (038 test rule kept).
- **FR-003** The config step (config page), config check and go MUST be refused by the server unless the request
  holds an accepted review for every channel; the acceptance needs an explicit approval flag plus the user's words
  (Principle I: locked in code).
- **FR-004** The acceptance is bound to the reviews it refers to (measurement time / board key / content of each
  channel). If any of them changes before config, the acceptance is void and steps (2)–(3) run again.
- **FR-005** A refusal marks the request stopped (with the user's words and time); every later config / cut / merge
  step of that request is refused with "review not accepted". Nothing is deleted.
- **FR-006** The tool's review step produces only the review (no cut region pictures, no config page) so the user's
  first answer comes as early as possible; snapshot / cut region pre-computation starts after "yes".
- **FR-007** Q2 (038) still shows the review file of each channel; if the review was measured again at the check step
  (content changed in the config page), Q2 says so ("review updated / review cập nhật").
- **FR-008** Guide `interface_sim` section 0, prompt `interface-sim` and the server instructions describe the new order;
  Claude never skips Q0 and never answers it for the user.
- **FR-009** Requests created before this feature: a request whose config page already exists continues without Q0.

### Key Entities

- **Review acceptance** (per request): decision (accepted / refused), user's words, time, and per channel the review
  it refers to (measured time, report file, NOT OK count).
- **Request state**: gains "stopped by the user at review" as an end state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** The user's first answer after naming the channels is the review (M0 + Q0) — no config page exists before
  "yes" in 100 % of runs (checked by test).
- **SC-002** On board1 one channel, the time from request start to Q0 is shorter than 5.0.0's time to M1 (no cut
  region pre-computation before the answer).
- **SC-003** "No" leaves the request with zero cut designs and zero merged project; config / check / go refused 3 / 3.
- **SC-004** "Yes" path gives the same cut result as 5.0.0 on board1 U14_U26 (24 ports, 126 GND vias, pin shift
  0.21 mm, self-check OK).
- **SC-005** Every tool answer of the process holds at most one question (existing test extended to M0 / Q0 / M0x).

## Assumptions

- The review content (checks, thresholds, OK / NOT OK, HTML report) is unchanged; only its place in the process moves.
- The tool never judges the review for the user (no automatic stop on NOT OK points); the user decides at Q0.
- One request = one Q0 (re-asked only when the reviews change, FR-004).
- The old step-by-step tools (gates A–D) stay as they are (manual / recovery path).
- Constitution Principle I already covers "approvals locked in code"; the new approval is added to its fixed-process
  sentence by the repo owner if the wording needs it.
