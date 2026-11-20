# Implementation Plan: Review approval by the user before cut (035)

**Branch**: `035-review-approval-gate` (work on `main`) | **Date**: 2026-11-14 | **Spec**: [spec.md](spec.md)

**Input**: `specs/035-review-approval-gate/spec.md` (Q1 A one approval, Q2 A tools removed, Q3 A preview always,
final cut region image; demo `mock/flow_demo.html` approved 2026-11-14).

## Summary

Interface simulation stops using review severity as a gate. After `isim_trace` the flow always produces three
things: the review HTML report, the cut preview drawn as the FINAL cut region, and one question. The engineer's one
"đồng ý" = GATE A (`isim_confirm_content`, `user_confirmed_content=true`), which now also records the review approval.
The cut refuses an interface without a current approval. STOP / CONTINUE, `isim_review_decide`,
`isim_review_override` and `design_review_decide` are removed (MAJOR 3.0.0). After the cut, the tool results name the
settings form (feature 005) as the next step; the guide makes the form mandatory.

## Technical Context

**Language/Version**: Python 3.12 (repo `.venv`)
**Primary Dependencies**: pyedb 0.85 / pyaedt 1.9 (unchanged), mcp<2, PIL, shapely
**Storage**: files: `<interface>/review.json`, `preview.json`, `user_settings.json` (key `review.approval`), review
records beside the board (`Ansys AEDT Copilot/reviews/`), review HTML in `<board dir>/autocut/` (Principle IX folder)
**Testing**: `python -m unittest discover -s tests/unit -t .`; AEDT checks on copies: `tests/regression.py`,
`tests/isim_check.py`, `tests/pcie_check.py`, `tests/review_check.py`, `tests/preview_check.py`,
`tests/review_gate_check.py` (rewritten as approval check)
**Target Platform**: Windows 11, AEDT 2026 R1
**Project Type**: Python package + CLI + MCP server (thin layers)
**Performance Goals**: review HTML on the snapshot ≤ ~20 s per channel (board1 2.12.0: 16 s); preview repeat seconds
**Constraints**: cut results identical to 2.12.0 (SC-005); board never written
**Scale/Scope**: interface_sim review / content / cut / cut_preview / ends / request status, review_checks verdict
text, end_gnd image, server + catalog + CLI, 3 guides, 2 workflows, tests

## Constitution Check

| Principle | Check |
|---|---|
| I Gates locked in code | PASS. GATE A stays the server-checked flag `user_confirmed_content`; the package refuses GATE A without a current review + report + error-free preview, and refuses the cut without a recorded approval bound to that review. Severity no longer gates (user decision); the gate is the user's go. |
| II User data safety | PASS. Board read only; report in `autocut/`, claim_file names; no deletion. |
| III Single source of defaults | PASS. No new defaults. Template rows unchanged. |
| IV Usage rules in guides | PASS. interface_sim, review_measure, catalog guides + workflows interface-sim / layout-review updated; server instructions text updated. |
| V Regression before release | PASS. regression / isim / pcie / preview / review checks on copies; references unchanged except the gate steps. |
| VI Windows & encoding | PASS. Edit/Write only, UTF-8. |
| VII Contracts | PASS. contracts/interface_sim-review.md, contracts/mcp-tools.md. |
| VIII Thin layers | PASS. Server keeps args + flag; logic in interface_sim/review.py. |
| IX Stable interface | JUSTIFIED: 3 tools removed, 1 flag removed, `isim_review(html)` ignored (always on for full review) → MAJOR 3.0.0 + CHANGELOG (user asked). Output folders unchanged. |
| X Catalog | PASS. Catalog entries removed with the tools; test_catalog keeps catalog = server set. |

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | changed: `isim_review` (always writes the HTML for a full review, returns `html`; no verdict / stop_md), `isim_confirm_content` (GATE A = approval: also records `review.approval`), `isim_cut` (refuses without approval), `isim_cut_preview` (`image` = final cut region), `isim_cut` / `isim_check_ends` (`next` = settings form), `isim_status` (Review column), `design_review` (no verdict text). Removed: `isim_review_decide`, `isim_review_override`, `design_review_decide`. |
| Safety level | unchanged (`isim_review` read, `isim_confirm_content` copy-free state write, `isim_cut` copy) |
| Approval flag | `user_confirmed_content` (unchanged); `user_approved_review_override` removed |
| Catalog entry + contract | tools.py entries updated / removed; contracts/mcp-tools.md, contracts/interface_sim-review.md |
| Registration | `@tool()` unchanged |
| Workflows affected | `workflows/interface-sim.md`, `workflows/layout-review.md` (decide / override steps removed) |
| New fixed-process tool | none |

## Design

### D1 Review always produces the report (FR-001, FR-013)
- `interface_sim/review.run`: full review (`checks` None) → always `review.review(...)` HTML (snapshot), `gate=None`;
  result `html` = absolute path; the path is stored in `review.json` (`html`) and in user_settings `review.html`.
  Reused review → the HTML is written again from the snapshot (seconds) so the file belongs to this request.
  Partial review (`checks=`) → no HTML unless `html=true` (unchanged).
- Report header: `_gate_html` line removed (no verdict); `gate=` argument kept, ignored (callers unchanged).
- `review_checks._verdict.verdict_md` → `summary line` without verdict word: `**<name>**: HIGH n, MEDIUM n, INFO n
  (incomplete: check x failed)`. `channel_verdict` stays (counts / incomplete for the approval record) but its
  `verdict` field is no longer printed anywhere. design_review results: `verdict_md` text without STOP / CONTINUE.

### D2 One approval = GATE A (FR-002, FR-003, FR-006, FR-007, FR-011)
- `review.gate_status` statuses: `not_reviewed` / `out_of_date` (same diffs as 025) / `no_report` (review.json has no
  html or the file is missing) / `ready` (current review + report, not approved) / `approved` (user_settings
  `review.approval.measured_at` == review `measured_at`).
- `review.require(rid, name, content, for_cut=False)`: GATE A (`for_cut=False`) needs `ready` or `approved`;
  the cut (`for_cut=True`) needs `approved`.
- `content.confirm` (GATE A): after `require`, also requires a preview for the same settings (FR-012:
  `cut_preview.load` key == settings key and no errors; else refuse "run isim_cut_preview first"); then
  `review.approve(rid, name)` writes `review.approval = {measured_at, time, report, review_json, counts, incomplete,
  failed_checks, preview_json}`. Optional server arg `user_words` (engineer's words) stored when given.
- Server `_review_refusal` uses the new statuses; message names the missing step.
- `request.status` Review column: `not reviewed` / `out of date` / `report ready` / `approved` / `approval out of date`.
- Old requests (2.12.0 user_settings with `decisions` / `override`): read, kept as history, never count as approval.
  Interfaces already past GATE A with unchanged content keep their step (the server already skips the gate when the
  content is unchanged); a NEW cut after content change needs approval.

### D3 Remove severity gate tools (FR-004, FR-005)
- Delete `review.decide`, `review.override`, `WAYS`, `_bound` users; `review_checks._store.decide` /
  `validate_decisions` / `merge_decisions` removed with `design_review_decide`; record keeps old `decisions` read-only.
- Server tools, CLI ops (`isim --op=review_decide|review_override`, `review-decide`), catalog entries, contract blocks,
  golden lists (test_interface_unchanged, thin_layers goldens via a RENAMED / REMOVED_035 list like 020).
- `review_checks.gate_of` removed; `measure_report` calls `review.review(..., gate=None)`.

### D4 Final cut region image (FR-012, user on demo)
- `end_gnd.final_scene(sc)` (pure): `base_pts` None, `other` [], `ends[*].added_mm` [] and `region_mm` None.
- `render_scene`: legend item `final` ("Cut region", solid green line) when `final_pts` exist and no base is drawn.
- `cut_preview.preview`: `image` = `cut_region.png` drawn from `final_scene(sc)`; the old diagnostic drawing kept as
  `detail` (`cut_detail.png` + `zooms`) for questions on end factors (not shown by default). `table_md` unchanged plus
  one line per end used by the guide.

### D5 Next step = settings form (FR-015, US2b)
- `isim_cut` result and `isim_check_ends` result get `next`: `"settings form: isim_settings_form(request_id) → widget
  (or table_md) → isim_validate_form → GATE B"`. Guide: form MANDATORY at GATE B; without widget the full `table_md`
  once; never a per-value question; mandatory sweep fields empty in the form.

### D6 Guide: standard short flow (FR-009, FR-010, US2)
interface_sim Phase 1 rewritten: request → trace (questions only for end candidates / schematic differences) →
snapshot build → `isim_review` → `isim_cut_preview` (defaults, no form unless asked) → answer = final cut image + one
line per end + review file (send / absolute path) + "Đọc review rồi xác nhận cut <name>?" → yes → GATE A → cut.
Content / findings / cut form only on request. Phase 1.5 STOP rules removed. review_measure: severity = information;
no verdict. catalog guide + server `instructions` + about() + cli/docs text: no STOP.

## Project Structure

### Documentation (this feature)

```text
specs/035-review-approval-gate/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md
├── contracts/ (interface_sim-review.md, mcp-tools.md)
├── checklists/requirements.md
└── mock/ (flow_demo.html, final_CPHY_U14_U26.png)
```

### Source Code (repository root)

```text
aedt_copilot/interface_sim/review.py        D1 D2 D3
aedt_copilot/interface_sim/content.py       D2 (confirm: preview required + approve)
aedt_copilot/interface_sim/cut.py           D2 (require for_cut) D5 (next)
aedt_copilot/interface_sim/ends.py | api.py D5 (next); api op table (D3)
aedt_copilot/interface_sim/cut_preview.py   D4
aedt_copilot/interface_sim/request.py       D2 (status label)
aedt_copilot/cut_board/end_gnd.py           D4
aedt_copilot/cut_board/review_report.py     D1 (header line)
aedt_copilot/review_checks/__init__.py, _verdict.py, _store.py   D1 D3
aedt_copilot/catalog/tools.py, cli/commands.py, cli/parser.py, cli/docs.py   D3
mcp_server/server.py                        D2 D3 (+ instructions text)
guides/interface_sim.md, review_measure.md, catalog.md; workflows/interface-sim.md, layout-review.md   D6
tests/unit/test_approval_035.py (new); test_review_gate_025.py, test_isim_review.py, test_interface_unchanged.py,
test_thin_layers_014.py, test_catalog*.py updated; tests/regression.py, isim_check.py, pcie_check.py,
review_gate_check.py, review_check.py, preview_check.py updated
```

**Structure Decision**: existing modules; no new package.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| Principle IX: 3 tools + 1 flag removed | user decision Q2 A (decision 100 % the engineer's, one go) | keeping no-op tools would leave a second, confusing way past the gate |
