# Contract — 039 review step (fixed process, request created by 5.2.0+)

## `isim_layout_review(request_id="")`  (safety: read, no gate)

- Input: request id (empty = latest). Every interface of the request must be traced.
- Does: review (with HTML report) of every channel, reused when current. Writes `<request>/_work/review_step.json`.
- Output: `{request_id, channels: [{name, review_html, not_ok, error}], ready: bool, answer_md}`.
  `answer_md` = M0 table + Q0 when every channel has a report; with an error row: M0 table only (no question).
- Refuses: request without `review_first` flag (created before 5.2.0) → `CopilotInputError` ("isim_config directly").

## `isim_review_answer(request_id="", accepted=False, user_answered_review=False, user_words="")`  (safety: copy, gate `user_answered_review`)

- Server refuses without `user_answered_review=true` or empty `user_words`.
- `accepted=false`: decision stored, request stopped. Output `{stopped: true, answer_md: M0x}`.
- `accepted=true`: needs a current `review_step.json` (every channel's review `measured_at` equal to the current
  review); stores the decision, runs `flow.config` → output of `isim_config` (answer_md = M1).
- Refuses: no review step, review changed since M0 ("isim_layout_review again"), request already stopped.

## Package guard `flow.require_review_ok(req, stage)`

- Applies only to requests with `review_first`. Stopped → refused ("review not accepted"). No accepted decision →
  refused. `stage == "config"`: any channel review `measured_at` ≠ accepted → refused. `check` / `go`: allowed
  (review may be re-measured for changed content; Q2 shows "review updated").
- Used by `flow.config`, `flow.check`, `flow.go`.
