# Research: 035

## R1 Where the approval lives
- Decision: GATE A (`isim_confirm_content`, flag `user_confirmed_content`) records the approval in user_settings
  `review.approval`; the cut checks it.
- Rationale: Q1 A = one go for content + cut area + review; GATE A is already the server-checked go of that moment.
- Alternatives: new tool `isim_review_approve` + flag (rejected: a second question, the user asked for one).

## R2 Approval validity
- Decision: bound to the review's `measured_at`; the review itself is invalid on board / ends / nets / checks /
  thresholds change (025 diffs reused). New review → new approval.
- Rationale: same binding as 025 decisions; proven, offline-testable.

## R3 Report always
- Decision: full `isim_review` always writes the HTML via `review.review(snapshot)`; reused review re-renders HTML.
- Rationale: FR-001; on the snapshot it costs seconds (board1 16 s, SERLINK 6 s). Output folder `autocut/` kept
  (Principle IX).
- Alternative: copy the HTML of the reused record (rejected: records do not keep HTML paths; files may be gone).

## R4 Verdict
- Decision: keep `channel_verdict` internally (counts, incomplete, failed checks) for the approval record; remove
  every printed verdict word and the HTML header line.
- Rationale: FR-004; no data loss in records; review records keep schema 2 (reuse stays valid).

## R5 Final cut region image
- Decision: pure scene transform `final_scene` + legend item; diagnostic image kept as `cut_detail.png`.
- Rationale: user on the demo; end-factor questions still need the detail picture (on request).

## R6 Preview before GATE A
- Decision: GATE A requires a preview with the same settings key and no errors (022 `_preview_gate` turns from
  "if present" into "required").
- Rationale: FR-012 (Q3 A); the engineer approves the area he saw.

## R7 Settings form
- Decision: `next` field in cut / ends results + guide rule (mandatory form).
- Rationale: test chat skipped the form; a tool-side pointer does not depend on Claude recalling the guide.
