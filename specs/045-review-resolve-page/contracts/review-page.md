# Contracts — 045 review page

## MCP `isim_layout_review(request_id)` (safety copy: writes only in the request folder)
- Request 5.6.0+ (`review_page`): reviews of every channel (board read-only) → page `<request>/config.html` (review
  + settings) → `{request_id, channels[{name, review_html, measured_at, not_ok, error}], ready, config_html,
  config_url, answer_md = M0p}`; a channel review error → no page, `answer_md` = M0 table (no question).
- Request 5.2-5.5: unchanged (M0 + Q0, contract 039). Before 5.2.0: refused.
- `isim_review_answer` on a 5.6.0+ request: refused (no Q0).
- `isim_config_check` / `isim_go` on a 5.6.0+ request: refused while a NOT OK point is unresolved on the saved page or
  the page was built from an older review.

## interface_sim/config/review_data.py (pure)

### `report_rows(html_text, tab) -> (rows, sections, topo)`
- html_text: str (review report written by `cut_board/review.py`); tab: int ≥ 1 (channel tab of the report).
- rows: {point id: [{rid, sec, desc, pic}]}; sections: {title: intro html}; topo: str ('' when none).
- Missing tab / structure → empty results (never raises for content). Bad types → `CopilotInputError`.

### `channel_review(review_doc, report_text, stackup, layer_order) -> ReviewData`
- review_doc: dict (review.json); report_text: str | None; stackup: list; layer_order: list[str].
- Raises `CopilotInputError` when review_doc has no channel / no measured_at.

### `validate_resolutions(state_review, data_review) -> [str]`
- Shape errors of `cfg-state.review` (unknown channel, point id not in the data, bad types). [] = ok.

### `unresolved(state, data) -> {channel: [point id]}`
- Points not resolved for the CURRENT measurement (measured_at mismatch → all points of that channel).

### `carry_over(old_state_review, data_review, tol_mm=0.01) -> (state_review, carried_count)`
- Keeps resolutions whose measured_at equals the data; else carries matching check + net + location (≤ tol) with
  `carried: true`.

## interface_sim/config/page.py
### `build(data, state, readonly=False)`
- Unchanged for data without `review`. With `data.review` (dict per channel) → merged page (assets review.*);
  `cfg-data`, `cfg-state`, request meta are the first blocks; config page template embedded escaped.
- Raises `CopilotInputError` when `data.review` channels ≠ `data.channels`.

## interface_sim/config/flow.py
### `review_step(request_id)` — 045 requests (`review_page`): reviews of every channel, then `config()` → returns
`{request_id, channels, ready, config_html, config_url, answer_md (M0p)}`; channel review error → no page, M0 rows.
### `review_answer(...)` — 045 requests: `CopilotInputError` ("not used: resolve the points on the page").
### `require_resolved(req, saved)` — check / go of 045 requests: no saved page → (check returns M1 + Q1 as before);
unresolved / outdated → `CopilotInputError("review", ...)` naming channels + counts.
### `check(...)` records `_work/resolutions.json`; Q2 gains the line "N NOT OK points resolved by the user".

## interface_sim/config/data.py
### `ends_data(...) -> (ends, choices, rot, stackup)`; `channel_data` adds `stackup`.

## cut_board/review_routing.py
### `fmt_value(v, ctype) -> str` — '2.2e-07' + Capacitor → '220nF'; text values returned as given; '' for none.
### `package_of(part) -> str` — first of 0201 / 0402 / 0603 / 0805 / 1206 / 1210 / 2512 in the part text, else ''.
### `top_svg` / `cross_svg`: series parts (rt `series_info`) of the pair nets drawn as body rectangle; cross-section
label row "<refdes>" / "<value> - <package>" under the part column.

## cut_board/review.py
### `review(..., series_values=None)` — {refdes: value text}; passed to routing data (`series_info`).
