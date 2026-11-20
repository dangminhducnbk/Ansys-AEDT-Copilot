# Implementation Plan: Review first, config only after the user's OK

**Branch**: `main` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)
**Input**: specs/039-review-before-config/spec.md (FR-001..009; Q0 one answer for all channels). Released together
with 041 as 5.2.0 (user: "implement 1 lần").

## Summary

Two new MCP tools put the review question in front of the config page:

- `isim_layout_review(request_id)` (read): review of every traced channel (existing `review.run`, reused when
  current) → `<request>/_work/review_step.json` + answer M0 (table Channel / Review file / NOT OK points) + Q0.
- `isim_review_answer(request_id, accepted, user_answered_review, user_words)` (gate `user_answered_review`):
  `accepted=false` → request marked stopped, M0x; `accepted=true` → acceptance stored (bound to each channel's
  review `measured_at` + html), then `flow.config` runs and the answer is M1.

`flow.config / check / go` call `require_review_ok(req)` for requests created with `review_first` (new requests
from 5.2.0): refused when there is no acceptance, when the request was stopped, or when a channel's current review
`measured_at` differs from the accepted one at config time (review re-measured → "call isim_layout_review again").
At `check`, a review re-measured because the content changed is allowed (FR-007) and Q2 adds "review updated".

## Technical Context

Python 3.12; no new dependency. Storage: `<request>/_work/review_step.json` {time, channels {name: {measured_at,
html, not_ok, error}}, decision {accepted, user_words, time, channels (snapshot of the table)}}. Request flag
`review_first: true` written by `request.start`. Tests: offline (`tests/unit/_isim_fixture`, fake review).

## Constitution Check

| Principle | Status |
|---|---|
| I Gates in code | New approval Q0 locked in the server (`user_answered_review` + words) and in the package (`require_review_ok`). Wording of Principle I: fixed process now has Q0 + `isim_go`; owner may amend (noted in CHANGELOG). |
| II Data safety | Review is read-only; "no" deletes nothing. |
| IV Guides | Guide `interface_sim` §0 + server instructions + prompt: new order, M0 / Q0 / M0x verbatim. |
| V Regression | Offline suite; `tests/config_flow_check.py` gets the Q0 step (board1 copy). |
| VII Contracts | `contracts/review-step.md`. |
| IX Stable interface | New tools only; `isim_config` / `check` / `go` unchanged for old requests (FR-009). |
| X Catalog | 2 catalog entries (+ contract path), registration via `@tool()`; tool count 58 → 60. |

## Design

- `answers.py`: TEXTS m0 / q0 / m0x; QUESTIONS += q0; `m0(rows)`, `m0x(rows)`; `q2` note "Review updated / Review
  cập nhật" when `review_updated`.
- `flow.py`: `review_step`, `review_answer`, `require_review_ok`; config / check / go call it.
- `api.py`: ops `layout_review`, `review_answer`. Server: 2 tools. Catalog: 2 entries.

## Project Structure

Code: `aedt_copilot/interface_sim/config/{flow,answers}.py`, `aedt_copilot/interface_sim/{api,request}.py`,
`mcp_server/server.py`, `aedt_copilot/catalog/tools.py`, `guides/interface_sim.md`, `prompts/interface-sim.md`.
Tests: `tests/unit/test_review_first_039.py`.
