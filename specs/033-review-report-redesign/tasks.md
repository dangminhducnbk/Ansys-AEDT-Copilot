---
description: "Tasks for feature 033 - layout review report redesign"
---

# Tasks: Layout review report redesign (033)

**Input**: `specs/033-review-report-redesign/` (spec.md, plan.md, research.md, data-model.md, contracts/review-report-033.md)
**Tests**: unit tests requested by the project rules (constitution V) + AEDT checks on copies (spec FR-013, SC-001..004).

## Phase 1: Setup

- [X] T001 Add template rows `review.serp_gap_factor` 3, `review.serp_amp_factor` 3, `review.serp_chamfer_factor` 1.5, `review.serp_chamfer_tol` 0.05, `review.serp_rise_factor` 1.5, `review.serp_bump_max_mm` 2, `review.serp_bump_spacing_mm` 2, `review.serp_bump_ratio` 1.43, `review.serp_min_bumps` 2, `review.serp_excl_mm` 1, `review.serp_step_mm` 0.01; remove `review.via_count_max` in templates/autocut_template.csv; update key lists in tests/unit/_golden.py and tests/unit/test_thin_layers_014.py

## Phase 2: Foundational (rule text from steering)

- [X] T002 Extend aedt_copilot/review_checks/_rules.py: `text(rule, part, variant, **fmt)` for parts why / fix / issue / recommendation (variants as `- \`k\`: sentence`, missing placeholder left visible, never raise); `report(rule, describe, layers, picture=None, fields=None)` adds `picture` / `fields` / `rule`; `report_lines(rule)` -> [(name, text)] from `## Report` (`- Name: text`)
- [X] T003 Add `## Report`, `## Issue`, `## Recommendation` parts (sentences of the mock `short()`, placeholders {net} {layer} {planes} {group} {other_net} {what}) to review_rules/{sov,loss_of_reference,ref_other_net,plane_edge,via_clearance,ref_plane_change,trace_stubs,via_stub,nearest_gnd_via,pair_skew,pair_gap,coupling,stackup_width,routing}.md and review_rules/_template.md

## Phase 3: User Story 3 - Serpentine rule, pair gap, via count removed (P1)

**Goal**: SERLINK Serpentine 10 NOT OK, Pair gap 3 → 1, Via count 0. **Independent test**: unit geometry tests + SERLINK copy counts.

- [X] T004 [US3] Create aedt_copilot/review_checks/_serp.py: `pairs(chains)` (group_diff on first net of each chain, P / A first), `height(B, layer)` (min positive dielectric distance to `B.ref_layers`), `find(path, others, H, excl, P)` (port of mock serp.find with template constants), `found(cc)` cached per channel (both directions of each pair, exclusion = pair pins / vias), `svg(f, paths)` (arrows A / G / c / W, layer + net top-left, scale bar) + compare lines "X = … mm (… mil) must be ≤ / ≥ … → OK / NOT OK"
- [X] T005 [US3] Create aedt_copilot/review_checks/serpentine.py (NAME serpentine, ORDER 65, items "Serpentine" MEDIUM with `serp`, `group`, bbox; REPORT with `picture` and `fields` giving {problems} {actions} built from steering variants A / G / C / S) and review_rules/serpentine.md (section routing, thresholds review.serp_*)
- [X] T006 [US3] aedt_copilot/review_checks/pair_gap.py: drop raw stretches whose midpoint lies in a serpentine box (+0.5 mm) of a pair containing the stretch net (before merge); steering review_rules/pair_gap.md says so
- [X] T007 [US3] Remove aedt_copilot/review_checks/via_count.py and review_rules/via_count.md; update tests/unit/test_review_rules_030.py, tests/unit/test_review_checks.py, tests/unit/test_thin_layers_014.py, tests/review_check.py
- [X] T008 [US3] Unit tests tests/unit/test_report_033.py: serpentine on synthetic geometry (A > 3W flagged, G < 3H flagged, 90° corner flagged, passing serpentine not listed), pair_gap skips a split inside a serpentine, via_count absent from registry

## Phase 4: User Story 2 - Routing view per pair (P1)

**Goal**: collapsed box per pair with top view, cross-section, length table, zoom lock. **Independent test**: unit walk / table tests + SERLINK U14_J8 TX_L2 box.

- [X] T009 [US2] aedt_copilot/cut_board/review.py `_review_edb`: build `ch["routing"]` (data-model.md fields: metal, gnd_layers, paths, vias, pins with pad `bbox` from `pin.bounding_box`, chains, comp_bb from `edb.components.instances[ref].bounding_box`, H) for end + series components; failures -> None + channel warning
- [X] T010 [US2] Create aedt_copilot/cut_board/review_routing.py (pure): `walk`, `signature`, `cross_svg` (rows = stackup, GND light blue, trace red + segment length, via black, stub pink, backdrill dashed pink, through-hole pin drawn as via, not counted), `top_svg` (colour per layer, P dark / N light, end bodies + real pads, refdes non-overlapping, vertical text for vertical parts, `data-fs`), `len_table`, `pair_box(ch, group)`, `section_html(chans, k)`, `ZOOM_JS`
- [X] T011 [US2] Unit tests in tests/unit/test_report_033.py: walk through a series part and a via, through-hole pin not counted, signature differs -> second cross-section, length table equals chain by_layer (± 0.001 mm)

## Phase 5: User Story 1 - Short report, one tab per connection (P1)

**Goal**: header 3 lines, tabs, Summary, sections with OK / NOT OK, Issue / Recommendation. **Independent test**: unit render tests + SERLINK HTML (SC-001).

- [X] T012 [US1] Rewrite `render` in aedt_copilot/cut_board/review_report.py per contracts/review-report-033.md (header, tabs `t<k>-`, Summary Index / Section / channel / Verdict, fixed sections routing / reference / trace_stub / via / Stackup + dynamic ones, "This section checks:" from steering, lead line, NOT OK table, Issue / Recommendation via steering, Location line, routing boxes in 2.1, CSS black text 12 / 14 / 18 px, OK #0050c8 / NOT OK #d00000, th #dce6f2, gate reason translated); keep `sections`, `rows`, `counts`, `row_layers`, `explain` API
- [X] T013 [US1] aedt_copilot/cut_board/review.py: `svg_zoom` / `svg_ref_panels` fault marks pink #ff1493 dashed ring / frame (no orange); picture loop uses REPORT `picture` hook (serpentine)
- [X] T014 [US1] Update tests/unit/test_review_report_026.py, tests/unit/test_check_report_028.py (golden HTML regenerated deliberately), tests/unit/test_reference_032.py for the new form; add render tests to tests/unit/test_report_033.py (3 tabs, no HIGH / MEDIUM / INFO / Reference data, Issue / Recommendation lines equal steering text, error channel tab)

## Phase 6: Polish & cross-cutting

- [X] T015 guides/review_measure.md: new report (tabs, OK / NOT OK, routing view, serpentine, via count removed), regenerate rule list (`review-rules --op=guide-list`)
- [X] T016 Run `.venv\Scripts\python -m unittest discover -s tests/unit -t .` (all PASS) and `graphify update .`
- [X] T017 AEDT checks on copies (scratchpad): SERLINK design_review html on a test1 copy; tests/pcie_check.py, tests/review_check.py, tests/regression.py, tests/isim_check.py; update references deliberately; write specs/033-review-report-redesign/verify-changes.md (before → after per channel, SC-001..SC-004, timing)
- [X] T018 Browser check of the SERLINK HTML vs autocut/mock/SERLINK_short_mock.html at 1366 / 1920 px; fix layout issues
- [X] T019 Release 2.11.0 locally: VERSION, CHANGELOG.md (Vietnamese, Claude restart needed), CLAUDE.md §8 row, annotated tag v2.11.0 (no push)

- [X] T020 R1: serpentine picture arrows thin, heads <= 1/3 arrow length, label halo, no overlap (`aedt_copilot/review_checks/_serp.py` svg); unit test
- [X] T021 R2: fan-out split next to a pin / via exclusion zone or a path end is not a bump (`_serp.find`); arrow tips on the measured points; unit test (split + real bumps -> A of the bumps only); re-run SERLINK + `tests/pcie_check.py` on copies, reference updated deliberately, before -> after in verify-changes.md
- [X] T022 R3: placement layer next to refdes of end components and series parts in top view + cross-section (`aedt_copilot/cut_board/review_routing.py`); unit test
- [X] T024 R4: via type label per via in the cross-section (`aedt_copilot/cut_board/review_routing.py`, type from the via rows kind / range / backdrill); unit test
- [X] T025 R5: via size `<pad>D<hole>` in mil next to the via type in the cross-section (padstack pad on entry layer + drill; snapshot must carry them); unit test
- [X] T023 Unit tests, `graphify update .`, redraw SERLINK HTML, release 2.11.1 (VERSION, CHANGELOG Vietnamese, CLAUDE.md §8 row, tag v2.11.1, no push)

- [X] T026 R6–R9: serpentine picture in mechanical-drawing style (`aedt_copilot/review_checks/_serp.py` svg): overview with dashed circle "A" only; "Detail A (x N)" frame on one bump with extension lines, double-arrow dimension lines, W outside arrows, A / G edge to edge, c aligned dimension on the 45° chamfer, centre line dash-dot, values with unit; reference `specs/033-review-report-redesign/mock/serp_dim_demo.html`; unit test (extension + dimension elements per W / A / G / c, arrow tips on the measured edges)
- [X] T027 R10: unit switch mil / µm / mm in the report header (`aedt_copilot/cut_board/review_report.py`, `review_routing.py`, `_serp.py`, steering-text values): every length rendered as an element carrying metres + JS formatter, default mil, localStorage in try/catch; area / angle / % / `<pad>D<hole>` unchanged; unit test (no bare mm length left in the HTML text outside the switchable elements; switch present; default mil)
- [X] T028 Unit tests, `graphify update .`, redraw SERLINK HTML on a test1 copy (counts unchanged vs 2.11.1), browser check at 1366 / 1920 px for all 3 units, release 2.11.2 (VERSION, CHANGELOG Vietnamese, CLAUDE.md §8 row, tag v2.11.2, no push)

- [X] T029 R11: no overlap between dimension values W / A / G / c in the Detail frame (`aedt_copilot/review_checks/_serp.py` `_detail_layout`: candidate places per value, pick the first whose text box does not hit the others); unit test (label boxes pairwise disjoint on synthetic bumps incl. a short chamfer next to the W arrow); redraw SERLINK on the test1 copy (counts / values unchanged), browser check; release 2.11.3 (VERSION, CHANGELOG Vietnamese, CLAUDE.md §8 row, tag v2.11.3, no push)
- [X] T030 R12: vector copper in review pictures (`aedt_copilot/cut_board/review.py`: `Copper.shape(layer, window)` = union of copper outlines minus voids clipped to the window (snapshot: chord geometry; live: polygon without arcs); `svg_ref_panels` / `svg_zoom` draw one even-odd path per plane (+ other-net copper minus GND), grid drawing kept as fallback for copper objects without shapes); unit tests (vector path present, no crispEdges grid, void hole drawn, other-net minus GND, fallback); redraw SERLINK (test1 copy) + board1 HTML: counts identical, browser check; release 2.11.4 (VERSION, CHANGELOG Vietnamese, CLAUDE.md §8 row, tag v2.11.4, no push)

## Dependencies

T001 → T002 → T003 → US3 (T004–T008) → US2 (T009–T011) → US1 (T012–T014) → T015–T019. US1 render uses the
serpentine picture hook (T005) and routing boxes (T010); each story testable alone with unit tests.

## Parallel opportunities

T003 steering edits [parallel per file]; T010 (pure module) parallel with T004 (pure module).

## Implementation strategy

Rules first (data changes, counts to verify), then routing data / view, then the HTML that assembles all; AEDT checks
once at the end (one SERLINK run gives SC-001..SC-004).
