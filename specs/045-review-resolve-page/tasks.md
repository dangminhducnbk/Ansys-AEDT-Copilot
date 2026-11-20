# Tasks — 045 One page per request (review + settings)

Spec: [spec.md](spec.md) · Plan: [plan.md](plan.md) · Contract: [contracts/review-page.md](contracts/review-page.md)

## Phase 1 — Setup
- [x] T001 Request flag `review_page: true` in `aedt_copilot/interface_sim/request.py` create (045)

## Phase 2 — Foundation (data)
- [x] T002 `aedt_copilot/cut_board/review_routing.py`: `fmt_value`, `package_of`; series bodies in `top_svg` (parts on
  the pair nets, `rt["comp_bb"]`); label row "<refdes>" / "<value> - <package>" in `cross_svg` (FR-007a)
- [x] T003 `aedt_copilot/cut_board/review.py`: `review(..., series_values=None)` → rq; `routing_data` → `series_info`
- [x] T004 `aedt_copilot/interface_sim/review.py::_html`: series values from netlist / board facts
- [x] T005 `aedt_copilot/interface_sim/config/data.py`: stackup read in `ends_data` → channel data `stackup`
- [x] T006 `aedt_copilot/interface_sim/config/review_data.py` (pure): report_rows, channel_review, validate_resolutions,
  unresolved, carry_over (contract)

## Phase 3 — US1-US4 page (P1)
- [x] T007 Assets `aedt_copilot/interface_sim/config/assets/review.html|css|js` ported from the approved mock (full
  screen, tabs, markers, detail = report rows, topology, layer panel + stackup, cross-section, Resolve / Resolve all,
  Print issue to image, units); picture data from `cfg-data` channels; cut region from extents + Settings state
- [x] T008 `page.js`: embedded mode (no header / Save, `window.cfgState()`, `window.setCh` used by the outer page)
- [x] T009 `page.py::build` merged page when `data.review` (blocks order, escaped config template)

## Phase 4 — US5 lock / save / check (P1)
- [x] T010 Outer Save: service POST (040 protocol) / browser fallback; disabled until all resolved; Settings lock
- [x] T011 `serve.py::_check_state`: `review` shape via `review_data.validate_resolutions`
- [x] T012 `flow.py`: review_step for 045 requests → reviews + `config()` (merged page, carry over) + M0p;
  review_answer refused; `require_resolved` in check / go; `_work/resolutions.json`; Q2 line (FR-012, FR-013)
- [x] T013 `answers.py`: `m0p`, resolutions line in `q2`

## Phase 5 — Interface text
- [x] T014 `mcp_server/server.py` instructions + `isim_layout_review` / `isim_review_answer` docstrings;
  `catalog/tools.py` entry (safety copy, contract 045)
- [x] T015 `guides/interface_sim.md`: 045 flow (page, resolve, Save, "xong")

## Phase 6 — Tests / verification
- [x] T016 `tests/unit/test_review_page_045.py`: review_data, page build / parse, flow guards, routing series, answers
- [x] T017 Run all unit tests; fix goldens only where the change is deliberate
- [x] T018 `tests/review_page_check.py` on an BOARDA copy (request → page → refusals → save → check)
- [x] T019 Browser check of the generated page (tabs, lock, resolve, save in place, PNG, topology)
- [x] T020 Old flow: `tests/config_flow_check.py` + `tests/regression.py` on board1 copies

## Phase 7 — Release
- [x] T021 VERSION 5.6.0, CHANGELOG, CLAUDE.md status row, `graphify update .`, tag v5.6.0 (not pushed)
