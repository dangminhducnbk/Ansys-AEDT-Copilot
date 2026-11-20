# Tasks: Report text lives in the review check file (028)

- [X] T001 `aedt_copilot/review_checks/_text.py` helpers; `REPORT` in `reference.py`, `trace_stubs.py`, `vias.py` (text moved verbatim); `DATA_ONLY` in `routing.py`
- [X] T002 `aedt_copilot/cut_board/review_report.py`: `report_specs()`, `section_of` / `explain` / `row_layers` via specs + fallback; SECTIONS without check lists
- [X] T003 `aedt_copilot/cut_board/review.py` `_review_edb`: extra registry checks reach the HTML
- [X] T004 `aedt_copilot/review_checks/_example.py` skeleton; guide `review_measure` developer section; CLAUDE.md note
- [X] T005 `tests/unit/test_check_report_028.py` (golden, registry contract, fake check, no-REPORT fallback, extra check in review.review); full suite; `graphify update .`
- [X] T006 AEDT board1 copy: `tests/review_check.py` + HTML text diff vs the 2.6.0 file

## Verify + converge (2026-11-10)

- Unit: golden pre028 (report HTML + explain / layers / sections from 2.6.0) identical; registry contract (every
  finding name made by cut_board/review.py has a REPORT; every check has REPORT or DATA_ONLY; duplicate finding name
  refused); fake new check renders its own section / rows / Why / Fix / layers and is measured by the HTML report;
  check without REPORT → generic block. Full suite PASS.
- AEDT board1 copies: HTML regenerated vs the 2.6.0 file → identical (945 305 bytes, date / version / timing line
  removed); `tests/review_check.py` PASS (24 / 0 and 29 / 11, HTML snapshot 2.6 s vs live 93.2 s).
- FR-001..007, SC-001..002 met. Nothing open.

