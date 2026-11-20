# Tasks: Coded rules from the PCIe self-test (012)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/output-changes.md](contracts/output-changes.md)

## Phase 1: Setup

- [X] T001 Add row `interface_sim.connector_handling` (job, text, default `smd_rebuild`) to `templates/autocut_template.csv`; update unit golden if the template rows test needs it (`tests/unit/`)

## Phase 2: User Story 1 - Connector end without a stop (P1)

- [X] T002 [US1] Tests first in `tests/unit/test_coded_rules_012.py`: connector end → `default_handling`, no `connector_end` unusual; other rules still asked; effective handling order (default < kept < given); validate refuses an option outside the connector options; old ends.json with `connector_end` unusual still needs a choice; compare_handling keeps old choice of a defaulted end; form tab prefills default
- [X] T003 [US1] `aedt_copilot/interface_sim/ends.py`: `thresholds` reads `connector_handling` (invalid → `smd_rebuild`); `classify_unusual` drops `connector_end`; `_measure` sets `default_handling`; `ends_md` table "End handling (team default)"; `check` output `default_handling`
- [X] T004 [US1] `aedt_copilot/interface_sim/settings.py`: `effective_handling`; `validate` checks defaulted ends' options; `validate_for` returns effective `handling` (kept from re-cut included) and shows it in `table_md`
- [X] T005 [US1] `aedt_copilot/interface_sim/apply.py`: `run` uses / stores `chk["handling"]`
- [X] T006 [US1] `aedt_copilot/interface_sim/recut.py` `compare_handling` and `form.py` `_tab` / `table_md`: defaulted ends

## Phase 3: User Story 2 - Series list + port metric (P1)

- [X] T007 [US2] Tests in `tests/unit/test_coded_rules_012.py`: `signal_paths` (no series = nets; 4 caps on 12 nets = 8), `self_check` with fake EDB lists series parts and uses `expected_ports_2x_paths`
- [X] T008 [US2] `aedt_copilot/interface_sim/apply.py`: `signal_paths`, `series_report`, `self_check` keys `series`, `signal_paths`, `expected_ports_2x_paths` + mismatch

## Phase 4: User Story 3 - Unique review lines (P2)

- [X] T009 [US3] Test: `issue_lines` keeps order, removes identical lines; `_report.point` uses it
- [X] T010 [US3] `aedt_copilot/cut_board/review.py` `issue_lines` (HTML card, tooltip, summary top) + `aedt_copilot/review_checks/_report.py`

## Phase 5: Polish

- [X] T011 Guides `guides/review_measure.md` (via stub vs data rate, reason) and `guides/interface_sim.md` (connector default, series shorted, port metric)
- [X] T012 `tests/pcie_check.py`: PCIE_U14_J25 on a test1 copy (0 connector_end questions, 4/4 caps shorted, ports 16 = expected 16, review counts + 0 duplicate lines)
- [X] T013 Unit tests all PASS; `graphify update .`
- [X] T014 AEDT: `tests/pcie_check.py` (test1 copy), `tests/regression.py`, `tests/isim_check.py`, `tests/review_check.py` (board1 copies) PASS, references unchanged
- [X] T015 VERSION 0.13.0, CHANGELOG, CLAUDE.md status, ROADMAP 012 done; commit + local tag v0.13.0

## Dependencies

T001 → T002..T006 (US1); T007..T008 (US2) and T009..T010 (US3) independent; T011..T015 last.
