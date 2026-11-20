# Implementation Plan: Layout snapshot phase 2 (HTML report + cut preview)

**Branch**: `main` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/snapshot-phase2.md](contracts/snapshot-phase2.md)

## Summary

Two more consumers read the 023 layout snapshot through the read-only PyEDB look-alike (`facade.SnapEdb`):
(1) the review HTML report (`review.review`) — same `layout_snapshot.api.for_review` as the review checks;
(2) the cut preview (`isim_cut_preview`) — end GND rule, other nets, scene drawn from the snapshot, while the cut
extent itself still comes from EDB `expanded_extent` and is cached per (nets, extent settings, factor) (Q2 A): the
preview extent stays exactly the cut extent (preview_check area diff 0.0). Snapshot missing / stale / not usable →
live as today + warning (never silent).

## Findings (code read)

| Item | Finding | Consequence |
|---|---|---|
| Window pin boxes | `build_window` skips pins of power / GND nets | end GND rule needs GND pad boxes → new per-component pin box file (all pins of the end / series components) |
| `prim_points` | facade `polygon_data` has no `.points` → silently falls back to the bbox | add `points` (exterior of the snapshot polygon, arcs as chords ≤ 1 µm) |
| `pin.pin_number` | missing in the facade | add (= pin name, as PyEDB) |
| Extent | AEDT conforming algorithm (`expanded_extent`) | cached JSON (floats round-trip exactly) per board key; miss → board opened once, kept open for further misses of the same call |
| `tests/preview_check.py` | calls GATE A without the 025 mandatory review | fix: review (+ override when STOP) before confirm, as regression / isim_check |

## Design

### 1. `layout_snapshot/facade.py`
- `_PDHolder.points` → exterior coordinates of the polygon (m); `_Inst.pin_number` = name.
- `SnapEdb(index, window, lenient, extra_pin_bbox=None)`: extra pin boxes merged into `pin_bbox`.

### 2. `layout_snapshot/preview.py` (new)
- `extent_key(P, nets, factor)`: nets sorted + `cutout.extent_type / expansion_unitless / round_corner / increments`
  + effective factor (None → `cutout.expansion`).
- `ExtentCache(folder, P, nets, session)`: `get(factor)` → cached `extents/<sha1>.json` or `cutter.compute_extent_mm`
  on the opened board (then stored). Counts hits / misses.
- `comp_pins(session, idx, folder, refdes)`: `comp_pins/<rd>.json` {iid: [[x0, y0], [x1, y1]]} for every pin of the
  component (LayoutInstance once, as `build_window`); built on miss.
- `open_for_preview(aedb, cell, P, nets, comps, version, log)` → context manager yielding `(edb, extent_fn, source)`:
  index (reuse / build) → base extent (cache / EDB) → window need = net window (margin) ∪ pin positions of `comps`
  (+5 mm, pads up to 10 mm) ∪ base extent bbox (+1.5 mm) → window (reuse / build) → component pin boxes → `SnapEdb`.
  Unsupported primitives / board locked while a build is needed → `SnapshotFallback`.

### 3. `cut_board/cutter.cut_extent(..., extent=None)`
- `extent(factor)` injected (preview); `None` = EDB as today (cut unchanged).

### 4. `interface_sim/cut_preview.run`
- `snapshot.use_for_preview` (template, default true): snapshot path; `SnapshotFallback` / `SnapshotMissing` → live
  (today's code) + `source.warning`. Result + `preview.json` gain `source` {kind, index, window, extent_cache {hits,
  misses}, seconds}.

### 5. `cut_board/review.review(..., snapshot="auto")`
- `review.use_snapshot` and snapshot != off → `for_review` → `SnapEdb`; fallback live + warning; `info["source"]`
  shown in the report header line. Measuring body moved unchanged into `_review_edb(edb, reqs, R, refs, step, log)`.
- `review_checks.measure_report(snapshot=)` and `isim_review(html)` pass their snapshot mode.

### 6. Template / guides
- Row `snapshot.use_for_preview` (bool, job, true). Guides `interface_sim` (preview reads the snapshot, first
  preview of a new factor opens the board once), `review_measure` (HTML from the snapshot).

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | none (results gain `source`) |
| Safety / gate | unchanged (read) |
| Catalog entry + contract | no catalog change; contract `contracts/snapshot-phase2.md` |
| Workflows affected | none |

## Technical Context

| Item | Value |
|---|---|
| Changed | `layout_snapshot/{facade, preview (new)}.py`, `cut_board/{cutter, review}.py`, `interface_sim/{cut_preview, review}.py`, `review_checks/__init__.py`, template, guides, `tests/{preview_check, review_check}.py` |
| Untouched | cut / apply / merge (EDB), review checks numbers, `layout_region` (later, Q1 A) |
| Tests | unit: facade points / pin_number / extra pins, extent key + cache (fake), comp pin file, cut_extent injected extent, preview fallback (fake), review snapshot fallback |
| AEDT (fresh copies, one after another) | board1 `preview_check.py` (+ live vs snapshot preview identical: end results, extent, other nets, gnd pins; timings), `review_check.py` (+ HTML live vs snapshot: counts / rows identical; timings), `regression.py`, `isim_check.py`; test1 `pcie_check.py` |

## Constitution Check (2.0.1)

| Principle | Check | Status |
|---|---|---|
| I Gates | unchanged | PASS |
| II Data safety | board read only; files only under `Ansys AEDT Copilot/snapshots/` | PASS |
| III Defaults | template row `snapshot.use_for_preview` | PASS |
| IV Guides | interface_sim / review_measure | PASS |
| V Regression | references unchanged; preview = cut extent | PASS |
| VII Contracts | contract file; input checks | PASS |
| VIII Package | snapshot logic in `layout_snapshot/`; consumers only choose the board object | PASS |
| IX Stable interface | additive (`source`), minor | PASS |
| X Tool catalog | no change | PASS |
