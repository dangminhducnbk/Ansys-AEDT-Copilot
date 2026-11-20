# Tasks: Layout review gate (025)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contracts/](contracts/), [research.md](research.md)

Implement ONLY after `main` contains features 021 and 024 and `main` is merged into this branch (T000).
Tests are required (SC-001..004, constitution V / VII).

## Phase 0: Base

- [X] T000 Merge `main` (with 021 + 024) into `claude/025-review-gate-ca985b`; re-read interface_sim request / folder code changed by 024 and adjust plan file references if names moved; unit tests PASS before any 025 code

## Phase 1: Foundational (pure + store)

- [X] T001 [P] `channel_verdict`, `thresholds`, `match_key`, `diff` in aedt_copilot/review_checks/_verdict.py (contract review-gate.md; CopilotInputError at entry)
- [X] T002 [P] `folder`, `save`, `find`, `decide` in aedt_copilot/review_checks/_store.py (records `review_<time>.json`, never overwrite, unreadable skipped, decisions validated like 011)
- [X] T003 `measure_report` takes board key before measuring, calls `store.save` (source `standalone`), adds `review_file`, per-channel `verdict`, `verdict_md` in aedt_copilot/review_checks/__init__.py; measured numbers unchanged
- [X] T004 Offline tests verdict (HIGH / dismissed / lowered with reason / incomplete check / trace error / MEDIUM only), match key + diff, store save / find newest / skip bad / decide in tests/unit/test_review_gate_025.py

## Phase 2: User Story 1 + 2 — mandatory review, STOP on HIGH (P1) 🎯 MVP

**Independent test**: board1 copy: Gate A / cut refused before review; U14_U26 CONTINUE → passes; U21_J25 STOP → refused.

- [X] T005 [US1] `interface_sim/review.run` any step after trace (proposal / content basis), all checks → review.json + record, partial → review_partial.json, `reuse` path (`store.find`, `reused_from`, decisions copied with record measured_at), returns `verdict`, `gate`, `stop_md` in aedt_copilot/interface_sim/review.py
- [X] T006 [US1] `gate_status` / `require` (statuses not_reviewed / out_of_date / stop / continue / decided / override; decisions + override bound to measured_at; message with HIGH points / diffs / ways forward) in aedt_copilot/interface_sim/review.py
- [X] T007 [US1] Gate call sites: `content.confirm` (new Gate A only; unchanged content at later step skips, FR-013) in aedt_copilot/interface_sim/content.py; `cut.run` in aedt_copilot/interface_sim/cut.py
- [X] T008 [US2] `request.status` review column (`review` per row + `Review` in table_md) in aedt_copilot/interface_sim/request.py
- [X] T009 [US1] Server: `isim_confirm_content` and `isim_cut` refuse on gate (`review_gate` block); `isim_review` description (mandatory step 1.5, reuse) + `reuse` param; `isim_review_decide` description in mcp_server/server.py
- [X] T010 [US1] Offline gate matrix: confirm / cut with no review, out-of-date nets / ends / board key / thresholds, STOP, CONTINUE, legacy request past Gate A (apply path untouched), review at step started on proposal; server refusals with fake request folders in tests/unit/test_review_gate_025.py

## Phase 3: User Story 4 — engineer's decision on a STOP (P2)

- [X] T011 [US4] `review.decide` any step + returns verdict / gate; `review.override(reason)` in aedt_copilot/interface_sim/review.py; op `review_override` in aedt_copilot/interface_sim/api.py
- [X] T012 [US4] MCP `isim_review_override` (`@tool()`, flag + reason refusals) in mcp_server/server.py; catalog entry (interface-sim / process / read, gate `user_approved_review_override`) + contract path 025 for isim_review / isim_review_decide / isim_review_override in aedt_copilot/catalog/tools.py
- [X] T013 [US4] `recut.start` result `previous_review` (verdict + override of source, display only) in aedt_copilot/interface_sim/recut.py
- [X] T014 [US4] Tests: decisions resolve STOP → decided; override → ok; override / decisions of an older measured_at ignored; override refused when CONTINUE / reason empty; reused review never carries override in tests/unit/test_review_gate_025.py

## Phase 4: User Story 3 — standalone review + reuse (P2)

- [X] T015 [US3] CLI `review-decide --file= --channel= --decisions-file=` in aedt_copilot/cli/parser.py, aedt_copilot/cli/commands.py
- [X] T016 [US3] MCP `design_review_decide` (`@tool()`) + `design_review` description (record + verdict) in mcp_server/server.py; catalog entry (review / tool / read) + contract in aedt_copilot/catalog/tools.py
- [X] T017 [US3] Tests: standalone record → isim review reuses (same points / verdict, no measure call), mismatch (board key / nets / checks / thresholds) → measure; record decisions carried; in tests/unit/test_review_gate_025.py
- [X] T018 Interface golden lists: tools 54 → 56 (tests/unit/test_rename_020.py), ADDED_TOOLS / changed descriptions / added param `reuse` / new command `review-decide` / new isim op in tests/unit/test_thin_layers_014.py; catalog guard tests pass (gated entry refuses with flag false)

## Phase 5: Guides, workflows, prompts, docs

- [X] T019 guides/interface_sim.md: phases table + Phase 1.5 mandatory review (after trace, before cut preview / Gate A), STOP handling, override only after explicit "vẫn cut" + reason, other interfaces continue, Phase R reuse / old override shown; remove Phase 1.6
- [X] T020 [P] guides/review_measure.md (verdict rule, record + reuse, design_review_decide, step 5); workflows/layout-review.md (+ design_review_decide, verdict file); workflows/interface-sim.md and workflows/re-cut.md (isim_review after trace / recut); prompts/interface-sim.md one line; server instructions REVIEW line in mcp_server/server.py
- [X] T021 [P] CHANGELOG.md Unreleased entry (proposed MINOR, no setup.bat rerun; restart Claude), CLAUDE.md §3 / §8 row

## Phase 6: AEDT checks on copies (one after another)

- [X] T022 tests/review_gate_check.py (new): board1 copy — U14_U26 refused before review → CONTINUE → Gate A OK; U21_J25 STOP → refused → override → Gate A OK; standalone design_review U21-J25 → isim reuse < 5 s same points; touched edb.def → re-measured; board edb.def unchanged
- [X] T023 Adapt tests/regression.py and tests/isim_check.py (review step after trace; U21_J25 override with reason "isim_check"); run both on board1 copies: PASS with existing references
- [X] T024 Adapt tests/pcie_check.py (review STOP 19 HIGH, override "pcie_check"); run on test1 copy: PASS, numbers unchanged
- [X] T025 `python -m unittest discover -s tests/unit -t .` PASS; `graphify update .`; commit

## Dependencies

T000 → all. T001-T002 → T003-T005. T005-T006 → T007-T010. T011-T012 after T006. T015-T017 after T002. T018 after T012 + T016. T019-T021 any time after T009. T022-T024 after T018, sequential (AEDT).

## Phase 7: Convergence

- [X] T026 Validate inputs of `_store.save` (out dict with board + channels) and `_store.folder` (non-empty path) with CopilotInputError + tests per Constitution VII (partial)
- [X] T027 Test CLI `review-decide` bad decisions file -> exit 2 + input error JSON per Constitution VII / plan section 4 (partial)
