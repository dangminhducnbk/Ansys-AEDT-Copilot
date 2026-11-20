# Feature Specification: Retire the Excel cut flow

**Feature Branch**: `017-retire-excel-flow` (work stays on `main`)

**Created**: 2026-11-09

**Status**: Done 1.0.0 (clarified 2026-11-09: Q1 A, Q2 A, Q3 A; inventory approved as listed).

**Input**: Parent session, user go 2026-11-09 (ROADMAP 017): remove the Excel cut flow (review → channel Excel →
batch cut → report → merge). Interface simulation (`isim_*`), atomic design tools (`design_*`), kitchen recipes and
review measure are the way to cut from now on. Breaking change → MAJOR 1.0.0.

## Clarifications

### Session 2026-11-09 (user via parent session: "A A A", no objection to the inventory)

- Q1 → **A**: remove `review_layout` (tool + CLI `review`); the HTML report comes from `design_review(html=true)`;
  guide content moves into `review_measure`.
- Q2 → **A**: keep `finish_in_aedt` (+ CLI `finish`); document its use after interface simulation / design tools.
- Q3 → **A**: nothing reads old Excel jobs; CHANGELOG: to finish an old job, checkout tag `v0.15.0`.
- Inventory approved as listed. Anything else found to remove → ask first.
- Constitution amendment (I, III, V, IX) is the user's (`/speckit-constitution`); the plan carries proposed wording.

## Inventory (what goes, what stays, why)

Usage checked with graphify + grep on 0.15.0. "Used by" = interface_sim, design_*, kitchen recipes, review_measure.

### MCP tools

| Item | Used by the other flows? | Proposal | Reason |
|---|---|---|---|
| `propose_channels` | no | **remove** | Excel only |
| `read_channels` | no | **remove** | Excel only |
| `start_cut_batch` | no | **remove** | Excel only (isim_cut / isim_apply cut) |
| `job_status` | no | **remove** | Excel jobs only (isim has isim_status / task_result) |
| `get_report` | no | **remove** | Excel jobs only (isim apply returns self_check) |
| `merge_to_project` | no (isim_merge / design_merge call `merge_designs` directly) | **remove** | job wrapper only |
| `review_layout` | recipe `excel-cut` only; same HTML via `design_review(html=true)` | **remove** (Q1 A) | duplicate of design_review html |
| `finish_in_aedt` | recipe `excel-cut` only; works on ANY cut .aedb | keep (Q2 A) | useful after isim / design tools |
| `inspect_board`, `show_defaults`, `get_guide`, `about`, `task_result` | yes | keep | shared |

### Prompts / guides / recipes

| Item | Proposal | Reason |
|---|---|---|
| prompts `cut-board`, `cut-run`, `cut-status`, `cut-report`, `cut-open`, `cut-rerun` | **remove** | Excel flow prompts |
| prompt `copilot-help` | keep, rewrite | lists the Excel flow today |
| guide `workflow` | **remove** | Excel phases / gates 1–3 |
| guide `setup_note` | **move** into `interface_sim` (setup / sweep notes) | rules still valid |
| guide `verify` | **move** criteria into `interface_sim` step 7 (already referenced there) | checks still valid |
| guide `review_layout` | **move** into `review_measure` (HTML report part) | report kept via design_review |
| recipe `excel-cut` | **remove** | Excel flow |
| server `instructions` (start with `get_guide("workflow")`) | rewrite: start with `kitchen` / `interface_sim` | entry point changes |
| `about` / CLI docs steps (review_layout → … → finish) | rewrite | |

### CLI / code

| Item | Used by the other flows? | Proposal |
|---|---|---|
| CLI `propose`, `cut`, `status`, `report`, `merge`, `run-job`, `worker` | no | **remove** |
| CLI `review` (HTML review) | review_layout only | **remove** (Q1 A) |
| CLI `finish` | finish_in_aedt | keep (Q2 A) |
| CLI `inspect`, `isim`, `design`, `kitchen`, `review-measure`, `layout-*`, `pidc*` | yes | keep |
| `cut_board/excel_io.py` | `default_name`, `unique_name`, `board_paths` used by isim content, design cutout, review_checks | **move** these 3 to `cut_board/naming.py`, remove the rest (openpyxl Excel) |
| `cut_board/propose.py` | `parse_request`, `group_diff` used by review_checks, isim content | **move** these 2 to `cut_board/naming.py`, remove the rest (incl. Excel gnd_questions) |
| `cut_board/batch.py` | no | **remove** |
| `cut_board/merge.py` | `merge_designs` used by isim_merge / design_merge | keep `merge_designs`, remove job `merge()` |
| `cut_board/aedt_finish.py` | `apply_display` used by `merge_designs` | keep |
| `cut_board/review.py` | functions used by review_checks; `review()` HTML by design_review html | keep |
| `cut_board/cutter.py` `cut_channel` (one-pass, Excel worker) | no (isim uses cut_stage / apply_stage) | **remove** `cut_channel`, keep the stages |
| server gates for Excel (`user_approved_review`, `user_approved_excel`, `user_approved_verify`, Excel part of `user_approved_gnd`) | — | **remove** with their tools; isim gates A–D + `user_approved_gnd` stay |

### Template `templates/autocut_template.csv`

| Rows | Proposal | Reason |
|---|---|---|
| `run.channel_timeout_min`, `run.max_parallel` | **remove** | batch only |
| `run.output_subdir` (`autocut`) | keep | review HTML output folder |
| `display.*`, `review.*` | keep | merge colours, review thresholds |
| columns Scope / Mandatory ("yellow cell") | keep | isim form uses them |
| every channel-scope row | keep | isim settings |

### Tests

| Item | Proposal |
|---|---|
| `tests/regression.py` (reads an Excel job) | **rewrite**: run CPHY_U14_U26 through interface simulation (U26 = `gnd_plate_vias`) and check the SAME reference `tests/reference/CPHY_U14_U26.json` (24 ports, 101 GND vias, planes 845–865 mm², pin shift ≤ 1 mm). `tests/isim_check.py` already passes it on 0.15.0 |
| unit tests of Excel parts (015 Excel gate / batch, 014 golden for removed tools) | remove those cases; golden lists the removed tools as intentionally gone |

### Constitution (user amends via `/speckit-constitution`)

| Principle | Today | Needed |
|---|---|---|
| I | "review, channel-Excel and verify gates" | gates of interface simulation (A–D) + `user_approved_gnd` |
| III rationale | "reproducible from the Excel" | "from `user_settings.json`" |
| V | `tests/regression.py` + `pidc_check.py`; MAJOR = "breaking Excel/workflow" | keep names (regression.py now isim-based); MAJOR = "breaking workflow / tool interface" |
| IX | "Excel / CSV template formats and output folders (`autocut/`…)" must not change | drop "Excel"; keep CSV template + output folders |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inventory approved before deletion (P1)
The user sees the tables above and approves them (with Q1–Q3 answered) before any file is removed.

### User Story 2 - Only one cut flow (P1)
After 1.0.0 the server lists no Excel tool / prompt / guide; asking to "cut a board" leads to interface simulation or
design tools (server instructions + kitchen).

### User Story 3 - Same results (P1)
`tests/regression.py` (isim-based) gives the same reference numbers as the Excel flow did; `pidc_check`,
`isim_check`, `design_check`, `kitchen_check` PASS.

### User Story 4 - Migration note (P1)
CHANGELOG 1.0.0: what was removed, the replacement for each tool, what to do with old `autocut/` jobs, `setup.bat`
not needed / restart Claude.

## Requirements *(mandatory)*

- **FR-001**: Remove every "remove" item of the approved inventory; "move" items keep their behaviour.
- **FR-002**: Kitchen catalog = server tool set (existing test) after removal; recipes reference no removed tool.
- **FR-003**: Guides / prompts / instructions mention no removed tool.
- **FR-004**: `tests/regression.py` runs the interface-sim flow and checks the existing reference.
- **FR-005**: CHANGELOG migration note; VERSION 1.0.0; constitution amendment proposed to the user (not edited by Claude).

## Success Criteria *(mandatory)*

- **SC-001**: 0 references to removed tools in code / guides / prompts / recipes (grep).
- **SC-002**: board1 copy: new regression.py PASS with the unchanged reference; isim_check PASS.
- **SC-003**: unit tests PASS.

## Assumptions

- Old `autocut/` folders on users' disks are not touched.

## Open questions

None (answered 2026-11-09).
