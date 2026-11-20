# Implementation Plan: Layout snapshot for fast review (phase 1)

**Branch**: `023-layout-snapshot` (worktree `claude/023-layout-snapshot-6e40d0`) | **Date**: 2026-11-10 |
**Spec**: [spec.md](spec.md) | Research: [research.md](research.md) | Data: [data-model.md](data-model.md) |
Contracts: [contracts/](contracts/) | Validation: [quickstart.md](quickstart.md)

## Summary

Read the board once into a 2-tier file snapshot (board index + window geometry) and run today's review checks on it
through a **read-only EDB facade**: objects that answer exactly the PyEDB attributes the review code reads
(`nets.nets[n].primitives / padstack_instances / components`, `components.instances`, `stackup`,
`padstacks.definitions`, `modeler.primitives_by_layer`, `PointInPolygon`, ...). `cut_board/review.py`,
`cut_board/inspect_board.trace_channel` and the check modules run UNCHANGED on the facade, so results are identical
by construction (same inputs, same order, same rounding). The spike showed > 99 % of today's time is EDB access and
that shapely point tests on 1 µm chords give 0 differences on 180 882 board1 queries.

## Technical Context

| Item | Value |
|---|---|
| Language | Python 3.12 (repo `.venv`), pyedb 0.85 .NET (build only), shapely 2 (already in requirements, layout_edit) |
| Storage | files under `<board folder>/Ansys AEDT Copilot/snapshots/` — JSON + WKB |
| Testing | `unittest` offline (`tests/unit/test_layout_snapshot_023.py`, fake snapshots); AEDT on copies: `tests/review_check.py` (extended), `tests/snapshot_check.py` (new: test1 PCIe review, timing, board unchanged), `tests/regression.py`, `tests/isim_check.py` |
| Platform | Windows, AEDT 2026 R1 non-graphical EDB (no GUI) |
| Performance goal | re-run ≤ 10 % of live (board1 ≤ 10 s vs ~100 s); first run (build + review) not slower than live |
| Constraints | board never written; `.lock` never deleted; check / threshold / wording unchanged; 022 files untouched |

## Design

### 1. Package `aedt_copilot/layout_snapshot/` (new)

| Module | Kind | Content |
|---|---|---|
| `__init__.py` | — | `SCHEMA_VERSION = 1`, public re-exports |
| `arcs.py` | pure | `to_coords(raw, tol_m)`: EDB point list with arc markers (`Y > 1e300`, `X` = height) → chord points (sign = −1 verified in spike vs `ArcData.GetMidPoint`) |
| `key.py` | pure (fs stat only) | `board_key(aedb, cell)` (path, `edb.def` size + mtime_ns, schema), `root(aedb)`, `index_dir`, `window_dir`, `check_board_lock`, window maths (`expand`, `contains`, `union`) |
| `store.py` | pure IO | write / read board index (`index.json`), window (`window.json` + `geom.wkb`), `snapshot.json` report, build lock (`.build.lock`, O_EXCL, wait / stale pid), `list_snapshots` |
| `build.py` | EDB (.NET direct) | `build_index(edb, aedb, cell, refs)` and `build_window(edb, index, window, tol)`; cached layer / net names, no PyEDB wrapper in loops except per padstack definition |
| `facade.py` | pure | `SnapEdb(index, window)`: the read-only PyEDB-like facade (see data-model.md §Facade) |
| `api.py` | orchestration | `build(...)`, `status(...)`, `list_(...)`, `for_review(aedb, cell, specs, R, ...)`; op table for CLI |

Board index content and window content: [data-model.md](data-model.md).

### 2. Exactness rules (why results are identical)

| Today reads | Snapshot stores / facade returns |
|---|---|
| `p.bbox` (rounded 9) | `GetPolygonData().GetBBox()` rounded 9 |
| `v.position` (component transform for pins, rounded 6) | same transform + rounding at build |
| `p.center_line` raw points incl. arc markers | raw points incl. markers (filtered by `review._pts` as today) |
| `p.width` (`GetWidth()`), `p.length` (ArcData lengths + end caps) | same .NET calls at build |
| `polygon_data.core.PointInPolygon(pt)` | `shapely.intersects_xy(prepared polygon, x, y)` on chords ≤ `snapshot.arc_tol_um` (1 µm); voids kept as separate polygons (Copper tests them one by one as today) |
| `p.area()` for the plane rule | board-wide per (ref net, layer) max area stored in the index; the max-area primitive outside the window is a geometry-less stub (bbox + area) so `Board.planes` is board-wide; its bbox never overlaps the window so `Copper` never asks its geometry |
| `nets.power`, components, pins, layer ranges, backdrill, pad sizes, pin bbox | stored values of the same PyEDB / .NET calls |
| order of `net.primitives` / `padstack_instances` / `comp.pins` | layout order / component pin-list order (checked on board1 in T005: equals per-net .NET order) |

`Copper` / `Board` / `_collect` / `check_reference` / `trace_stubs` / `via_rows` / `lengths` / `trace_channel` are
called unchanged. `review_checks/_context.py` is unchanged (it takes the `edb` object it is given).

### 3. Review integration — `review_checks/__init__.py`

`measure_channels(board, specs, checks, cell, version, log, snapshot="auto")`:

1. `use = snapshot != "off" and template review.use_snapshot`.
2. `use` → `layout_snapshot.api.for_review(aedb, cell, specs, version, log)`:
   load / build index → trace each channel on an index-only facade (nets) → needed window = bbox of all channel nets
   (prim bboxes + instance positions) + `snapshot.window_margin_mm` (≥ 1 + `review.zoom_margin_mm` + 2 mm, the
   review copper window) → reuse a valid window that contains it (FR-004) or build one → facade.
   Unsupported primitive inside the window → `SnapshotFallback` → live path + warning naming the ids (FR-021).
3. `measure_edb(facade, specs, names, log)` — unchanged.
4. Output adds `source` = `{kind: snapshot|live, folder, index: built|reused, window: built|reused, arc_tol_um,
   times, warnings}` (FR-014).

`review.use_snapshot = false` or `snapshot="off"` → today's path byte-for-byte (FR-013). `measure_report(html=True)`
and `isim_review(html=True)` call `review.review()` live as today (FR-015).

### 4. Interface

| Layer | Change |
|---|---|
| MCP | new `layout_snapshot(op, board, cell="", nets="", scope="window", margin_mm=0)` → CLI (task when > 45 s); `design_review` / `isim_review` + optional `snapshot: str = "auto"` (`auto` / `off`) |
| CLI | new `snapshot --op=build|status|list --args-file=`; `review-measure --snapshot=auto|off` |
| isim | `interface_sim/review.run(..., snapshot="auto")` passes through |
| Template | `review.use_snapshot` (bool, true), `snapshot.window_margin_mm` (5), `snapshot.arc_tol_um` (1) — job scope |
| Guides | `review_measure` (snapshot section: built / reused / stale / fallback, `layout_snapshot`), `interface_sim` (after `isim_trace` start `layout_snapshot build` with the content nets, background) |
| Catalog | entry `layout_snapshot` group `review`, kind tool, safety `read`; contract `specs/023-layout-snapshot/contracts/mcp-tools.md` |

### 5. Concurrency (spec edge case, review note 5)

Build lock per index / window folder (`.build.lock`, O_EXCL; second caller waits up to 10 min, then reuses).
Two read-only EDB opens of the same board from two processes (background build + `isim_trace`) are tested in T020;
if they fail, `api.build` serializes on a board-level lock and the plan / guide records it.

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | added `layout_snapshot` (ops build / status / list); `design_review`, `isim_review`: optional `snapshot` argument (additive) |
| Safety level | `layout_snapshot` = `read` (writes only `<board folder>/Ansys AEDT Copilot/snapshots/`) |
| Approval flag | none (read) |
| Catalog entry + contract | `aedt_copilot/catalog/tools.py` entry + `specs/023-layout-snapshot/contracts/mcp-tools.md` |
| Registration | `@tool()` (010); test_catalog / guards automatic |
| Workflows affected | none (review steps keep names); guide text only |
| New fixed-process tool | none |

## Constitution Check (2.0.1)

| Principle | How | Result |
|---|---|---|
| I Gates | no gate change; read-only tool | PASS |
| II Data safety | board never written (checksum test), `.lock` refused never deleted, old snapshots kept, own build-lock only | PASS |
| III Defaults | 3 template rows; functions take values as arguments | PASS |
| IV Guides | review_measure + interface_sim updated | PASS |
| V Regression | regression.py + isim_check.py on copies; no release in this feature run (parent decides) | PASS |
| VI Encoding | UTF-8 JSON, no PowerShell rewrites, paths from board folder | PASS |
| VII Contracts | contracts for every public function of `layout_snapshot` + changed review entry points; validation at entry | PASS |
| VIII Layers | new feature package; pure modules (arcs, key, store, facade) separate from `build.py`; server / CLI thin | PASS |
| IX Interface | names kept; additive argument + tool → minor | PASS |
| X Catalog | see Tool catalog check | PASS |

## Project Structure

```text
specs/023-layout-snapshot/   spec.md plan.md research.md data-model.md quickstart.md contracts/ tasks.md
aedt_copilot/layout_snapshot/ __init__.py arcs.py key.py store.py build.py facade.py api.py   (new)
aedt_copilot/review_checks/__init__.py        measure_channels snapshot path + source
aedt_copilot/interface_sim/review.py          snapshot argument pass-through
aedt_copilot/cli/parser.py, commands.py       snapshot command, review-measure --snapshot
mcp_server/server.py                          layout_snapshot tool, snapshot argument
aedt_copilot/catalog/tools.py                 entry + contract path
templates/autocut_template.csv                3 rows
guides/review_measure.md, guides/interface_sim.md
tests/unit/test_layout_snapshot_023.py        offline
tests/unit/golden/pre023_review_*.json        live golden (board1, test1) captured before the change
tests/review_check.py (extended), tests/snapshot_check.py (new)
```

Not touched: `cut_board/review.py`, `cut_board/inspect_board.py`, `review_checks/_context.py` and check modules,
`cut_board/end_gnd.py`, `interface_sim/cut_preview.py` (022 patch in another checkout).

## Complexity Tracking

| Deviation | Why | Simpler alternative rejected |
|---|---|---|
| Facade mimics a subset of PyEDB attributes | keeps every measuring function unchanged → identical results, no second implementation to keep in sync | rewriting checks on a new snapshot API (two code paths, risk of drift; PRD non-goal "no change to checks") |
| Hot paths (`PointInPolygon`, facade properties) skip `core.validate` | called ~200 k times per review | validation at `api` entry only |
