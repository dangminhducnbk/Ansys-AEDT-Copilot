# Implementation Plan: One page per request — layout review (resolve NOT OK points) + settings

**Branch**: `main` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md) | **Mock (approved 2026-11-17)**: `mock/review_page_template.html` + `mock/build_demo.py`

## Summary

New requests (5.6.0+) get ONE page per request, still written as `<request>/config.html` (same file, same save
service 040, same reader 038): a full-screen page with, per channel, a **Review layout** tab (board picture from the
config page data + one marker per NOT OK point of the channel's review, point detail = the old report row(s) parsed
from the review report HTML the tool itself wrote, topology per pair, Resolve / Resolve all, Print issue to image)
and a **Settings** tab (the unchanged 5.5.0 config page, run in a frame, locked until the channel's points are
resolved). Save (service or browser fallback) stores settings + resolutions in the page's `cfg-state`;
`isim_config_check` / `isim_go` refuse when a point is unresolved or a resolution belongs to an older review.
Q0 / `isim_review_answer` are not used for these requests (`isim_layout_review` writes the page directly, answer M0p).
The topology view (033) draws series R / C / L of the pair as body rectangles and writes "<refdes>" /
"<value> - <package>" in the cross-section label row — in the review report too.

## Technical Context

**Language/Version**: Python 3.12 (repo `.venv`), page = HTML + vanilla JS (Chrome / Edge, offline)

**Primary Dependencies**: existing package only (pyedb 0.85 for the live read already done by the config data);
no new library

**Storage**: files in the request folder (`config.html`, `_work/*.json`), review report HTML under `autocut/`

**Testing**: `python -m unittest discover -s tests/unit -t .` (offline), board-copy check script
`tests/review_page_check.py` (BOARDA copy: page build, markers = NOT OK points, report rows, save via service, check
refusals), browser check in the preview pane

**Target Platform**: Windows 11, AEDT 2026 R1 (read-only EDB session for the config data, unchanged)

**Project Type**: Python package + MCP server + generated HTML page

**Performance Goals**: page opens < 3 s with 2 channels (SC-005); page build adds < 2 s to isim_config (report
parse + JSON)

**Constraints**: no new MCP tool; `config.html` blocks `cfg-data` / `cfg-state` / request meta stay the first ones
in the file (038 reader, 040 service); file size ≈ config page + report rows (report pictures are vector SVG)

**Scale/Scope**: 1-4 channels, up to ~100 NOT OK points per channel

## Constitution Check

| Principle | Status |
|---|---|
| I Gates in code | `isim_config_check` / `isim_go` refuse unresolved / outdated resolutions in the package (`flow.require_resolved`); `isim_go(user_approved_cut)` unchanged; Q0 gate not used for 045 requests (the page's resolutions replace it, spec Assumptions) |
| II Data safety | board read-only; only request-folder files written; old pages never deleted (`config.html` rewritten as before) |
| III Defaults | no new template value |
| IV Guides | `guides/interface_sim.md` section 0 + M0p text; server instructions updated |
| V Regression | `tests/regression.py`, `tests/config_flow_check.py` (board1, old flow) must PASS; report HTML of board1 changes only in the routing boxes (series parts: none on board1) |
| VI Encoding | files written UTF-8 by Python; no PowerShell rewrite |
| VII Contracts | `contracts/review-page.md` (review_data, page.build kind, flow guards, routing series) + validation + unit tests |
| VIII Thin layers | logic in `interface_sim/config/review_data.py` (pure) + flow; server only passes args |
| IX Stable interface | tool names unchanged; `isim_layout_review` output for NEW requests = M0p + config page (old requests unchanged); MINOR release 5.6.0 (behaviour of new requests, no tool removed) |
| X Catalog | no new tool; catalog entry of `isim_layout_review` updated (writes the page → safety `copy`) |

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | `isim_layout_review`: for 045 requests also writes the request page (config.html) and returns M0p; `isim_config_check` / `isim_go`: refuse unresolved points (045 requests) |
| Safety level | `isim_layout_review` read → copy (writes only in the request folder) |
| Approval flag | n/a (copy) — `isim_go` keeps `user_approved_cut` |
| Catalog entry + contract | `catalog/tools.py` entries updated, contract `specs/045-review-resolve-page/contracts/review-page.md` |
| Registration | unchanged (`@tool()`) |
| Workflows affected | none |
| New fixed-process tool | none |

## Project Structure

```text
specs/045-review-resolve-page/
├── plan.md  research.md  data-model.md  quickstart.md  contracts/review-page.md  tasks.md
└── mock/ (approved mock, build_demo.py)

aedt_copilot/
├── cut_board/review_routing.py      series parts: body rect (top view) + label row (cross-section); fmt_value / package_of
├── cut_board/review.py              review(series_values=) -> rq; routing_data series_info
├── interface_sim/review.py          _html passes series values (netlist / board facts)
├── interface_sim/request.py         create: review_page flag (045)
├── interface_sim/config/
│   ├── review_data.py   NEW pure: report rows / sections / topology from the report HTML, points of review.json,
│   │                    resolutions (validate, carry over, unresolved)
│   ├── data.py          ends_data also reads the board stackup (same live session) -> channel data 'stackup'
│   ├── page.py          build(..., review=) -> merged page (config page embedded as a template block)
│   ├── flow.py          review_step for 045 requests -> config page + M0p; require_resolved in check / go;
│   │                    resolutions recorded (FR-013)
│   ├── answers.py       m0p, q2 resolutions line
│   ├── serve.py         _check_state: review resolutions shape
│   └── assets/review.html review.css review.js  NEW (ported from the mock); page.js: embedded mode + state getter
mcp_server/server.py                 instructions + isim_layout_review / isim_review_answer docstrings
guides/interface_sim.md              045 flow
tests/unit/test_review_page_045.py   NEW; tests/review_page_check.py NEW (board copy)
```

**Structure Decision**: extend the 038 config package (same file name / reader / save service) instead of a second
page file, so 040 Save-in-place, 038 reader and the check / go guards keep working unchanged for the settings part.

## Complexity Tracking

None.
