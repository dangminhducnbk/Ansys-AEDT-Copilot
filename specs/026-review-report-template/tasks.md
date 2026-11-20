# Tasks: Layout review report template (026)

**Input**: spec.md, plan.md, contracts/review-report.md. Commit after each step. AEDT on copies, one after another.
Measuring code unchanged (tests/review_check.py numbers equal).

## Phase 1: Foundational

- [X] T001 New `aedt_copilot/cut_board/review_report.py`: `SECTIONS`, `section_of`, `sections`, `rows`, `counts`, `danger`, `row_layers`, `limit_text` per contract (pure, input checks)

## Phase 2: US3 — picture of the involved layers only (P1)

- [X] T002 [US3] `aedt_copilot/cut_board/review.py` `svg_zoom(win, cu, planes, paths, signals, vrows, gnd_ps, items, oc)` → (svg, legend): coverage only for `planes`, traces only on `signals`, no dashed other layers
- [X] T003 [US3] `review.review(gate=None)`: rows per channel, pictures for the first `review.max_images` rows (union bbox + `zoom_margin_mm`), `ch["rows"]`; findings / points / return value unchanged

## Phase 3: US1 + US2 — summary first, category tables (P1)

- [X] T004 [US1] [US2] `review_report.render(info, chans)`: header + gate verdict, summary table per section × channel (counts, worst, verdict, link), detail section per category (Index / Description / Picture, HIGH + MEDIUM, "No issue"), Reference data collapsed (summary tables, overviews, all findings incl. INFO, via table, lengths, thresholds); `review.render_html` delegates
- [X] T005 [US1] Gate verdict: `review_checks.measure_report(html=True)` and `interface_sim/review.run(html=True)` pass `gate`
- [X] T006 [P] `tests/unit/test_review_report_026.py` (sections, rows, counts, danger, row_layers table, render structure / 3 columns / INFO excluded / incomplete / gate / limit note / self-contained, svg_zoom layers)

## Phase 4: Polish + verify

- [X] T007 Guide `guides/review_measure.md` (report structure, danger wording, chat summary order)
- [X] T008 All unit tests; `graphify update .`
- [X] T009 AEDT copies: board1 `review-measure --html` (U14_U26, U21_J25) + `tests/review_check.py`; test1 PCIe report; build time vs 2.4.0; send HTML paths for user review (before converge / release)

## Verify (2026-11-10, copies, one after another)

- board1 `review.review` build time: 2.4.0 91.3 s → 026 94.3 s (+3 %, SC-004 ≤ 20 %); counts identical (U14_U26 24 INFO; U21_J25 2 HIGH / 11 MEDIUM / 16 INFO).
- board1 `review-measure --html`: header gate U14_U26 CONTINUE, U21_J25 STOP (high); rows REF-01..02, VIA-01..11; no dashed layer.
- test1 PCIe `review-measure --html`: STOP, 19 HIGH / 46 MEDIUM / 24 INFO (= review data), REF-01..19 + VIA-01..08, all with pictures.
- `tests/review_check.py` PASS (numbers unchanged). Fixed the test's isim part (broken since 025: review now runs right after trace, before Gate A; confirm removed).
- User reviewed the HTML 2026-11-10: "Ổn, release 2.5.0"; review points accepted as built (English danger wording, both-side planes on ref-change pictures, one row per category for shared points, Routing "No issue").

## Converge (2026-11-10)

- FR-001..009 / SC-001..004 checked against code. Gap found: US2-3 (index clicked from the summary jumps to the row) —
  summary linked sections only → T010.
- [X] T010 `review_report.render`: summary row lists the first 8 row indexes linking to `#r-<index>` (+N more); contract + unit test
- 473 unit tests PASS. Nothing else open.

## Phase 5: Fix — readable description + legend inside the cell (user review 2026-11-10)

- [X] T011 `aedt_copilot/cut_board/review_report.py` `explain(f, P, c)` + `_desc`: per finding title, Net (channel), labelled lines (via / trace location, layers, reference, value — limit ✗/✓, stub / backdrill), Why, Fix; internal keys + ids in the hover title only; unit tests (REF-01 template, every check has Why / Fix, no `review.` / `point #` in visible text)
- [X] T012 Legend: `review.svg_zoom` labels "<layer> – signal" / "<layer> – GND (ref)" / "GND via" / "signal via" / "issue"; `.leg` flex-wrap block inside the picture cell (max 390 px), no `.legend span` rule; unit test
- [X] T013 Regenerate board1 (U14_U26, U21_J25) + test1 PCIe HTML on copies; check REF-01 at 1366 / 1920 px; paths to the user for review
  Result 2026-11-10: board1 + test1 HTML regenerated from the snapshot (seconds); REF-01 checked at 1366 px (legend wraps in the cell) and 1920 px (0 / 27 picture cells overflow on test1). Awaiting user review.
