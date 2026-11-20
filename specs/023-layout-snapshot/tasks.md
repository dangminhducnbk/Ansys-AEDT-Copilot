# Tasks: Layout snapshot for fast review (phase 1)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [contracts/](contracts/), [research.md](research.md)

Tests are required by the spec (SC-001..006) and the constitution (VII offline tests, V regression).

## Phase 1: Setup

- [X] T001 Store live golden (captured on copies before any code change) in tests/unit/golden/pre023_review_board1.json and tests/unit/golden/pre023_review_test1.json (board path replaced by `<board>`)
- [X] T002 Add template rows `review.use_snapshot` (bool, true), `snapshot.window_margin_mm` (num, 5), `snapshot.arc_tol_um` (num, 1), job scope, in templates/autocut_template.csv; extend golden allow-lists (`ADDED_PREFIXES` / ADDED_DEFAULTS) in tests/unit/_golden.py and tests/unit/test_thin_layers_014.py

## Phase 2: Foundational (pure modules)

- [X] T003 [P] `arcs.to_coords(raw, tol_m)` in aedt_copilot/layout_snapshot/arcs.py (arc marker `Y > 1e300`, `X` = height, normal sign −1; CopilotInputError tol ≤ 0)
- [X] T004 [P] `key.py`: `board_key` (`edb.def` size + mtime_ns, never `edb.def.tmp`, schema), `check_board_lock` (refuse, never delete), `root / index_dir / window_dir`, `window_of`, `contains`, `union` in aedt_copilot/layout_snapshot/key.py; `SCHEMA_VERSION = 1` + `SnapshotMissing(BaseException)` / `SnapshotFallback(Exception)` in aedt_copilot/layout_snapshot/__init__.py
- [X] T005 [P] `store.py`: index / window JSON + length-prefixed WKB, read → None on missing / schema / key mismatch, `build_lock` (O_EXCL `.build.lock`, wait while live pid, remove own only), `list_snapshots` in aedt_copilot/layout_snapshot/store.py
- [X] T006 `facade.SnapEdb(index, window)` with every attribute of data-model.md §Facade (class names `Path` / `Polygon`, bbox / position as stored, plane-area stubs, prepared shapely `PointInPolygon` via `intersects_xy`, `SnapshotMissing` on absent data) in aedt_copilot/layout_snapshot/facade.py
- [X] T007 Offline tests: arcs, key / stale / lock, store round trip, window maths, fake snapshot (2 components, GND plane with void, plane on 2 layers, trace with stub, via) driving `review_checks.measure_edb` for every check and checking expected items in tests/unit/test_layout_snapshot_023.py

## Phase 3: User Story 1 — review re-run in seconds (P1) 🎯 MVP

**Independent test**: board1 copy review twice → second run reuses snapshot, ≤ 10 % time, identical to live / golden.

- [X] T008 [US1] `build.build_index` (direct .NET: stackup, nets / power flag, prims meta bbox9, insts with component transform + round 6, comps + pin order, plane_area per ref net / layer, pad_defs of via defs) in aedt_copilot/layout_snapshot/build.py
- [X] T009 [US1] `build.build_window` (outline + voids overlapping window via arcs.to_coords, paths center / width / length, backdrill of non-power vias, pin_bbox of non-power pins, unsupported list, counts / times) in aedt_copilot/layout_snapshot/build.py
- [X] T010 [US1] `api.build / status / list_ / for_review` (index reuse, window reuse when it contains the need, margin ≥ 1 + zoom_margin + 2 mm, end-pin box check, SnapshotFallback on unsupported, report `snapshot.json`) in aedt_copilot/layout_snapshot/api.py
- [X] T011 [US1] `measure_channels(..., snapshot="auto")` + `review.use_snapshot` + `source` + live fallback with warning (SnapshotFallback / SnapshotMissing) in aedt_copilot/review_checks/__init__.py; `snapshot` pass-through in aedt_copilot/interface_sim/review.py
- [X] T012 [US1] Spike-check on board1 copy: per-net primitive / instance order = layout order for channel nets; pin bbox build time; record in research.md (R8, R9)
- [X] T013 [US1] Extend tests/review_check.py: live vs snapshot build vs snapshot reuse identical + golden pre023 + timing table; board `edb.def` checksum unchanged

## Phase 4: User Story 2 — explicit build / status / list (P2)

- [X] T014 [US2] CLI `snapshot --op=build|status|list --args-file=` and `review-measure --snapshot=` in aedt_copilot/cli/parser.py, aedt_copilot/cli/commands.py
- [X] T015 [US2] MCP `layout_snapshot` (`@tool()`, input validation refusals) + `snapshot` arg on `design_review` / `isim_review` in mcp_server/server.py; catalog entry (group review, kind tool, safety read) + contract path in aedt_copilot/catalog/tools.py
- [X] T016 [US2] Interface tests: tool added (test_interface_unchanged, test_thin_layers_014 ADDED_TOOLS / ADDED_PARAMS / ops), CLI help / bad input exit 2 in tests/unit/test_layout_snapshot_023.py
- [X] T017 [US2] tests/snapshot_check.py: test1 copy PCIe review via snapshot = golden, build / re-run timing (window + board scope), status valid → touch `edb.def` → stale → rebuilt, board checksum unchanged

## Phase 5: User Story 3 — developer checks on fake snapshots (P3)

- [X] T018 [US3] Fake-snapshot builder helper (`fake_index` / `fake_window`) in tests/unit/_snapshot_fixture.py used by T007 tests; docstring in aedt_copilot/layout_snapshot/facade.py says how to add a check

## Phase 6: Polish

- [X] T019 [P] Guides: guides/review_measure.md (snapshot section: built / reused / stale / fallback, `layout_snapshot`, `snapshot=off`), guides/interface_sim.md (after `isim_trace` start `layout_snapshot build` with the content nets in background)
- [X] T020 Concurrent read-only opens (background build while another process opens the board) on test1 copy (tests/snapshot_check.py step 5); result in research.md R10; serialize if needed
- [X] T021 AEDT: tests/regression.py + tests/isim_check.py on fresh board1 copies PASS (references unchanged); timing table into spec.md Results
- [X] T022 CHANGELOG.md "Unreleased" entry (restart Claude: new tool + guide change; no setup.bat); CLAUDE.md §3 / §8 rows; `graphify update .`; full unit suite 0 failures

## Dependencies

T001–T002 → T003–T005 (parallel) → T006 → T007; T008–T010 → T011 → T012–T013; US2 needs T010; T019–T022 last.
MVP = Phases 1–3.

## Phase 7: Convergence

- [X] T023 Count invalid outline / void polygons in build_window (`invalid_polygons`, no repair) and correct the spec Results line per research R2 / FR-010 (partial)
- [X] T024 Refuse `margin_mm < 0` in api.status at entry + unit test per contract api.status (partial)
- [X] T025 Remove unused SnapEdb.covers / overlaps helpers in aedt_copilot/layout_snapshot/facade.py per plan §1 (unrequested)
