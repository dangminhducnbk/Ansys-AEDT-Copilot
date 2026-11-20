# Feature Specification: One file per layout review rule

**Feature Branch**: `031-review-rule-files` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "đối với review layout, mỗi một rule là một file steering hoặc code (nếu có) riêng biệt để
khi sửa sẽ dễ hơn."

Number note: 029 (layout_region on snapshot, worktree branch) and 030 (6 new review rules, main checkout, in
progress) are taken. `.specify/feature.json` is NOT switched to 031 while 030 is active in this checkout.

## Problem

Today (2.6.1) a review rule is spread over several places:

| What | Where today | Problem |
|---|---|---|
| Measuring code | `review_checks/<check>.py` (028: one file per CHECK, with its report text) | One check file holds several rules: `reference` = SOV + reference to other net + loss of reference + reference plane change; `vias` = via stub / backdrill + nearest GND via |
| Rule definition for Claude (what it means, how to read it, severity, how to discuss with the engineer) | One big guide `guides/review_measure.md` (H4 4.1–4.6, H5 severity) | Editing one rule means finding it in a long shared file; easy to break another rule's text |
| Thresholds | `templates/autocut_template.csv` rows `review.*` | Fine, but not linked from the rule |

The engineer wants to open ONE place per rule and change it there.

## Clarifications

### Session 2026-11-11

- Q: Granularity? → A: one file per RULE (split `reference` into 4 rules, `vias` into 2); shared helpers stay shared.
- Q: Steering-only rules (no code)? → A: allowed, judged by Claude and reported, but cannot stop a cut on their own.
- Q: Where do rules live? → B: repo (team) + a personal rule folder per user, like personal workflows; team wins on an
  id clash (personal shown as shadowed); personal code rules run only after the user enables them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Each rule lives in its own file(s) (Priority: P1)

The engineer (or Claude on their behalf) wants to change how "Nearest GND via" works. They open the rule's own
steering file (meaning, thresholds used, severity, why it matters, how to fix, how to discuss) and, if the rule has
code, its own code file. Nothing else has to be edited.

**Why this priority**: this is the request.

**Independent Test**: list the rules: every rule shown in the review report maps to exactly one steering file and at
most one code file; changing the steering text of one rule changes only that rule's guidance.

**Acceptance Scenarios**:

1. **Given** the rule set, **When** listed, **Then** each rule (SOV, Reference to other net, Loss of reference,
   Reference plane change, Trace stub, Via stub / backdrill, Nearest GND via, Length match, and the 030 rules) has
   its own steering file and, when it measures something, its own code file.
2. **Given** a steering file, **When** read, **Then** it states: what the rule checks, the template thresholds it
   uses (keys + defaults), severity rule, why it matters, how to fix, how Claude discusses it with the engineer.
3. **Given** the engineer edits one rule's steering or code file, **When** a review runs, **Then** only that rule's
   behaviour / text changes; other rules' results are identical.

---

### User Story 2 - Claude reads only the rule it needs (Priority: P2)

When Claude interprets review results, it loads the steering of the rules that have findings (not one long guide).

**Why this priority**: shorter, focused guidance; less chance Claude mixes rules.

**Independent Test**: a review with only "Nearest GND via" findings → Claude is pointed to that rule's steering only;
the general review guide keeps only the process (how to run, gate, record) and links to rule files.

**Acceptance Scenarios**:

1. **Given** review results, **When** returned to Claude, **Then** each finding carries its rule id and where its
   steering is.
2. **Given** the general review guide, **When** read, **Then** it no longer contains per-rule definitions, only the
   process and the list of rules with links.

---

### User Story 3 - Adding a rule = adding its files (Priority: P2)

A new rule is added by adding its steering file (+ code file if it measures). Report section, summary, gate,
listing pick it up without other edits (extends 028).

**Independent Test**: add an example rule from the template files → it appears in the rule list, the report and the
gate, with its own Why / Fix text from its files.

---

### Edge Cases

- Steering-only rule (no code): allowed; Claude judges it from the review data / pictures and reports it, labelled
  "judged by Claude"; it can NOT stop a cut on its own (only measured rules feed the 025 gate) (Q2 A).
- A rule's code without a steering file (or the reverse): listed as incomplete; unit test fails for repo rules.
- Two rules sharing measurement work (e.g. one copper index for SOV and loss of reference): shared helper stays
  shared; each rule file keeps only its own decision and text; results and speed unchanged.
- Old review records (025) and report golden files: rule ids keep the same finding names so old records still read.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every layout review rule MUST have its own steering file (plain text for Claude and the engineer) and,
  when it measures, its own code file; the granularity is one file per RULE (Q1 A): `reference` splits into SOV, Reference to other net, Loss of
  reference, Reference plane change; `vias` into Via stub / backdrill and Nearest GND via. Shared measuring helpers
  stay shared; results and speed unchanged.
- **FR-002**: A steering file MUST contain: rule id, title, what is checked, thresholds used (template keys +
  defaults), severity rule, why it matters, how to fix, how Claude discusses it; the report's Why / Fix text MUST come
  from it (single source).
- **FR-003**: Rule results, finding names, severities, counts, report HTML and review records MUST be identical to
  2.6.1 for the existing rules after the move (board1 + test1 golden).
- **FR-004**: The general guide `review_measure` MUST keep only the process (run, snapshot, gate, record, report)
  and a generated list of rules with links; per-rule definitions move to the rule files.
- **FR-005**: Claude MUST be able to read one rule's steering on its own (e.g. through the guide tool by rule id).
- **FR-006**: A rule listing (rule id, title, has code, thresholds, file paths) MUST be available to Claude and the
  engineer.
- **FR-007**: Rules live in the repo (team rules, owner edits) AND in a personal rule folder per user, like personal
  workflows (Q3 B). A personal rule with the same id as a team rule is reported as a clash (team rule used, personal
  one shown as shadowed); personal rules are labelled "personal" in results / report. A personal rule with code runs
  only after the user explicitly enables it (code from a personal folder is not run silently).
- **FR-008**: Unit tests MUST fail when a repo rule lacks its steering file, a steering file lacks a mandatory part,
  or a code file has no steering file.
- **FR-009**: The 030 rules (in progress) MUST follow this layout (coordinate: 030 delivers them as separate files).

### Key Entities

- **Review rule**: id, title, steering file, optional code file, thresholds (template keys), severity rule, report
  section, source (team / personal).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Changing one rule touches at most 2 files (its steering + its code), verified on 3 example edits.
- **SC-002**: 100 % of rules in the report map to exactly one steering file.
- **SC-003**: Existing rules' review results and HTML identical to 2.6.1 on board1 and test1.
- **SC-004**: The general review guide shrinks to process only (no per-rule definitions left).

## Assumptions

- "Steering" = the written guidance Claude follows for that rule (same role as today's guide sections), English like
  the other guides; code comments stay Vietnamese.
- Thresholds stay in `templates/autocut_template.csv` (Principle III, single source of defaults); the steering file
  names the keys, it does not hold the values.
- Users who only have the MCP server + guides (no repo knowledge) get the rule steering through the guide tool.
- Order with 030: spec / clarify now; implementation after 030 is merged (both touch `review_checks/`), or 030 adopts
  the layout directly if 031 is clarified before 030 implements.
- Version: minor (guide structure changes, Claude restart).
