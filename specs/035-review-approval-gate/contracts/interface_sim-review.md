# Contracts: review approval (035)

## `interface_sim.review`

| Function | Pre | Output / post | Errors |
|---|---|---|---|
| `run(request_id, name, checks=None, html=False, version=None, snapshot="auto", reuse=True, nets=None)` | interface traced (`proposal` or `content`) | full review: review.json + record (or reused) + HTML ALWAYS (`html` = absolute path, also in review.json / user_settings `review.html`); `approval` reset to null for a new `measured_at`; no `verdict` / `stop_md` keys; `summary_md` + `counts`; partial (`checks`) → review_partial.json, HTML only if `html=True` | no proposal / content → `CopilotInputError("interface")`; html not bool → `CopilotInputError("html")`; report error → result `html_error` and status `no_report` |
| `gate_status(request_id, name, content=None)` | — | `{ok, status, message, diffs, counts, html, approval}`; status ∈ `not_reviewed`, `out_of_date`, `no_report`, `ready`, `approved`; `ok` = status in (`ready`, `approved`) | never raises for missing files |
| `require(request_id, name, content=None, for_cut=False)` | — | gate dict; `for_cut=True` needs `approved` | not ok → `CopilotInputError("review", message, status)` |
| `approve(request_id, name, preview_json=None, user_words="")` | status `ready` or `approved` for the current review | writes `review.approval` (data-model); returns approval | other status → `CopilotInputError("review", ...)` |
| `status_label(gate)` | gate dict | `not reviewed` / `out of date` / `no report` / `report ready` / `approved` | — |

Removed: `decide`, `override`, `WAYS`.

## `interface_sim.content.confirm(request_id, name, content, user_words="")`
Pre (added): review `require(for_cut=False)`; preview for the same settings key exists and has no errors
(else `CopilotInputError("preview", "isim_cut_preview with these cut settings first", ...)`).
Post (added): `review.approve(...)` with the preview path. Unchanged content on an interface past GATE A → unchanged
(no new approval needed).

## `interface_sim.cut.run`
Pre: `review.require(..., for_cut=True)`. Output adds `next` (settings form pointer).

## `interface_sim.ends.check` (isim_check_ends) — output adds `next`.

## `cut_board.end_gnd`
| Function | Inputs | Output |
|---|---|---|
| `final_scene(sc)` | scene dict | new dict: `base_pts` None, `other` [], ends `added_mm` [] / `region_mm` None (pure, input not changed) |
| `legend_items(sc)` | scene | adds (`final`, `Cut region`) when `final_pts` and no `base_pts` |

## `interface_sim.cut_preview.preview` — `image` = final region `cut_region.png`; new `detail` = `cut_detail.png`.

## `review_checks`
- `_verdict.verdict_md(name, v)` → `**<name>**: HIGH n, MEDIUM n, INFO n` (+ `, incomplete`) and failed checks; no
  verdict word, no HIGH table.
- `_store.decide`, `validate_decisions`, `merge_decisions` removed; `gate_of` removed.
- `cut_board.review_report`: header has no gate line (`gate` argument accepted, ignored).

Tests: `tests/unit/test_approval_035.py`.
