# Tasks: layout_region on the layout snapshot (029)

**Input**: [spec.md](spec.md), [plan.md](plan.md), [contracts/region-snapshot.md](contracts/region-snapshot.md)
**Baseline (2.6.1, B04 copies, scratch)**: stitch total 76.3 s (read_before 28.4, read_after 27.3), neck 71.1 s
(read_before 16.1, read_after 17.7); PASS 7 / 7 + 2 WARN.

## Phase 1 — Snapshot data (US1)

- [x] T001 `edit_layout/extract.py`: `pad_table(edb, names, scale=MM)` (default unchanged).
- [x] T002 `layout_snapshot/__init__.py` SCHEMA_VERSION 2; `build.py`: original point records in `geom.wkb`
  (geoms `r`, void rows + `roff, rn`), index `pad_table` (all definitions, scale 1), `comps[rd].bbox` (LayoutInstance
  once, round 6).
- [x] T003 `layout_snapshot/facade.py`: `_Prim.core` / `type` / `points`, `_Void` rows of 6 + `points`, `_Layer.type`,
  `clear_cache`, `_Comp.bounding_box`, `SnapEdb(region=True)` pad table objects.
- [x] T004 `layout_snapshot/api.py` `_window(..., build_need=)` (`"board"` = whole board, Q2 B), `_defaults`
  `use_region`; new `layout_snapshot/region.py` `open_for_region(aedb, cell, bbox_mm, build=True, ...)`: reuse any
  window containing the box, else build the whole board once.
- [x] T005 Template row `snapshot.use_for_region` (bool, job, true).

## Phase 2 — Consumers (US1, US2)

- [x] T006 `edit_layout/run.py` `region()`: snapshot path + live fallback + `source`.
- [x] T007 `edit_layout/run.py` `edit()`: before read from an existing snapshot window (no build), `before_source`.

## Phase 3 — Tests

- [x] T008 Unit tests `tests/unit/test_region_snapshot_029.py`: points = PyEDB algorithm (arcs / markers / orient),
  raw records, bbox prefilter, pad table + comps, `extract_region` fake live vs snapshot identical, window reuse /
  build need, fallbacks (lock, missing), `run.region` source + template off, schema 2. Fix fixture for schema 2.
- [x] T009 `tests/region_check.py` (AEDT): live vs snapshot `region.json` / summary / vias / PNG identical, timings,
  second call board not opened.

## Phase 4 — Docs

- [x] T010 Guide `layout_edit` (snapshot source, fallback, before reuse); CHANGELOG Unreleased (proposed 2.7.0);
  CLAUDE.md §3 / §8; `graphify update .`.

## Phase 5 — AEDT checks (copies, one after another)

- [x] T011 board1 copy `region_check.py`; B04 copy `region_check.py` (stitch area box); report whole-board build time
  + snapshot size (MB) for both boards.
- [x] T012 B04 stitch + neck via scratch wrapper (region built first so before reuses it) vs baseline: `result.json`
  (ops / checks / summary) + `changes.json` identical; times.
- [x] T013 B04 copy delete-via plan: live before vs snapshot before identical.
- [x] T014 board1 copy `review_check.py` + `preview_check.py` PASS on schema 2 (review HTML live 115.7 s → snapshot
  3.2 s, identical; preview snapshot = live, cut area diff 0.0, again 1.8–2.2 s vs live 102–287 s).

## Results (2026-11-11, copies in the session scratchpad)

| Check | Result | Times |
|---|---|---|
| board1 `region_check` box 115,30,130,45 + box2 70,55,90,75 | PASS: region.json / summary / vias / PNG identical, box2 board not opened | read live 87.8 / 84.9 s → snapshot 3.9 / 4.3 s; whole-board build 130 s (open 7 + index 29 + geometry 84 + pins / vias 3.5 s), 237 MB (6.56 M points) |
| board1 window mode (first Q2 A run, kept for info) | PASS identical | build 52 s (25×25 mm window), read 1.3 s |
| B04 `region_check` box 36,33,82,72 + box2 60,55,90,75 | PASS identical | read live 43.3 / 19.2 s → 2.9 / 1.8 s; whole-board build 24 s, 36 MB |
| B04 neck board `region_check` 60,50,90,78 | PASS identical | live 24.3 s → 1.9 s; build 28 s |
| B04 stitch vs 2.6.1 | result.json + changes.json IDENTICAL | read_before 28.4 → 4.7 s, total 76.3 → 62.3 s |
| B04 neck vs 2.6.1 | IDENTICAL | read_before 16.1 → 2.6 s, total 71.1 → 67.5 s |
| B04 delete-via (3 VCC_1P8V vias) live vs snapshot before | IDENTICAL, PASS 5 | read_before 26.1 → 3.8 s, total 86.3 → 58.6 s |

Note: `edit` time grows 2–5 s with the snapshot before read (PyEDB caches no longer warmed by the before read);
net gain stays 4–28 s per edit.
