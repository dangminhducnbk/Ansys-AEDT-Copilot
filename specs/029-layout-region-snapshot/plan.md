# Implementation Plan: layout_region on the layout snapshot

**Branch**: `claude/029-layout-region-snapshot-b47d85` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/region-snapshot.md](contracts/region-snapshot.md)

## Summary

`edit_layout/extract.extract_region` runs UNCHANGED on the snapshot look-alike (`facade.SnapEdb(..., region=True)`),
as review / preview do (023 / 027). The snapshot gains what that function reads and the live read computes from EDB:
the EDB original points of every primitive / void in a window (arc markers kept; Q1 A) so `points(arc_segments=16)`
gives the same floats as PyEDB, the padstack table in raw units, component boxes. Schema 2 (older snapshots rebuilt
once). Region: a cached window that contains the box is reused, else the WHOLE-BOARD geometry is built once (Q2 B)
and every later box uses it. `layout_edit` "before" read uses the snapshot of the SOURCE board only when a valid window already covers the
region (no build inside an edit); otherwise live as today.

## Findings (code read)

| Item | Live read (`extract_region`, PyEDB 0.85) | Snapshot today | Consequence |
|---|---|---|---|
| Outline / void points | `p.points(16)`: `_get_points_for_plot` over `PolygonData.Points` (arc marker → `compute_arc_points(prev, next, h, 16)`) + `orient_polygon(clockwise)` | WKB chords ≤ 1 µm | store original points (float64, marker `Y > 1e300`, `X` = arc height) in `geom.wkb` records; facade runs the same pure PyEDB functions → identical floats |
| bbox prefilter | `GetPolygonData().GetBBox()` unrounded | index bbox rounded 9 | facade `core.GetPolygonData().GetBBox()` = index bbox ± 1e-9 m: superset prefilter, decision stays on the points (points lie inside the true bbox) → same set |
| Path | `center_line` raw points, `GetWidth()` | stored (023) | reuse |
| Instances | `padstacks.instances` (position like 023 index, layers, `component.refdes`) | index `insts` (027 facade `instances`) | reuse; order = layout order (checked live vs snapshot) |
| Pad table | `pad_table`: `geometry_type`, `parameters_values` / MM, antipads, `hole_properties[0]` / MM | review subset only | `extract.pad_table(..., scale=1.0)` at index build for every board definition → raw floats; facade `region=True` returns them, `extract` divides by MM itself → identical |
| Component box | PyEDB `bounding_box` = `GetLayoutObjInstance(comp).GetBBox()` round 6 (re-fetches LayoutInstance per component) | none | index `comps[rd].bbox` with LayoutInstance taken once |
| Window content | — | prims / voids whose bbox overlaps the window (signal layers) | box ⊂ window ⇒ every prim / void the live read keeps is in the window |
| Missing data | live error entry `{"err"}` | `SnapshotMissing` (BaseException) | not caught by `extract` → whole read falls back live + warning (never a different result) |

B04 baseline (2.6.1 on copies): `read_before` 25–41 s, `read_after` 25–41 s per `layout_edit`; `layout_region` read
same order.

## Design

### 1. `layout_snapshot/__init__.py`
- `SCHEMA_VERSION = 2`.

### 2. `layout_snapshot/build.py`
- `_poly_wkb` also returns the original points; `build_window` packs them (`array('d')`) as extra records in
  `geom.wkb`: geoms entry `"r": [off, n]`, void row `[vid, bbox, off, n, roff, rn]`.
- `build_index`: `pad_table` = `edit_layout.extract.pad_table(edb, all definitions, scale=1.0)`; `comps[rd]["bbox"]`
  (LayoutInstance once, round 6 like PyEDB; failure → `None`).

### 3. `edit_layout/extract.py`
- `pad_table(edb, names, scale=MM)` (default unchanged). Nothing else changes.

### 4. `layout_snapshot/facade.py`
- `_Prim.core` (`GetPolygonData().GetBBox()` from the index bbox ± 1e-9 m; no bbox → raises like PyEDB),
  `_Prim.type` (lower kind), `_Prim.points(arc_segments)` / `_Void.points(arc_segments)` from the original points
  (PyEDB `compute_arc_points` + `GeometryOperators.orient_polygon`, imported from pyedb, pure Python).
- `_Layer.type = "signal"`; `_Modeler.clear_cache()` no-op; `_Comp.bounding_box` from the index.
- `SnapEdb(..., region=True)`: `padstacks.definitions` from `index["pad_table"]` (`pad_by_layer` / `antipad_by_layer`
  objects returning the stored `geometry_type` string and raw `parameters_values`; stored error → raises with the
  same text; `hole_properties`). Review / preview path (region False) unchanged.

### 5. `layout_snapshot/region.py` (new)
- `open_for_region(aedb, cell, bbox_mm, build=True, version, log)` → `(SnapEdb, source)`: index (reuse / build) →
  window containing the box (reuse smallest) else build the whole board (`scope board`, Q2 B; only when `build`) → SnapEdb
  (region=True). Board locked and a build needed / `build=False` and nothing cached → `SnapshotFallback` (reason).
- `api._window(..., build_need=None)`: find with the box, build `build_need` (`"board"` = whole board).

### 6. `edit_layout/run.py`
- `region()`: template `snapshot.use_for_region` (default true) → `open_for_region` + `extract_region(snap)`;
  `SnapshotFallback` / `SnapshotMissing` → live (today's code) + `source.warning`. Result gains `source`.
- `edit()`: "before" = `open_for_region(src, build=False)` when the row is on and a valid window covers the region,
  else live (today). `result.json` gains `before_source`. Decision kept only if B04 stitch / neck / delete-via
  results are identical (measured, T-AEDT); otherwise reverted to live.

### 7. Template / guide / docs
- Row `snapshot.use_for_region` (bool, job, true). Guide `layout_edit`: region from the cached snapshot (first call
  builds the whole board once), `source.warning` on fallback, edit before-read reuse. CHANGELOG Unreleased (proposed 2.7.0),
  CLAUDE.md §3 / §8.

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | none (results gain `source` / `before_source`) |
| Safety / gate | unchanged (`layout_region` read, `layout_edit` copy) |
| Catalog entry + contract | no catalog change; contract `contracts/region-snapshot.md` |
| Workflows affected | none |

## Technical Context

| Item | Value |
|---|---|
| Changed | `layout_snapshot/{__init__, build, facade, api, region (new)}.py`, `edit_layout/{extract, run}.py`, template, guide `layout_edit`, tests |
| Untouched | ops / checks / render of layout edit, review / preview numbers (schema bump only rebuilds) |
| Unit tests | facade points = PyEDB algorithm on raw points (arcs, markers, orientation), raw record packing, region facade pad table / comps / bbox prefilter, `extract_region` on a fake snapshot = on a fake live EDB, window reuse / build need, fallback (lock, missing), `run.region` source, template row, schema 2 |
| AEDT (copies, one after another) | new `tests/region_check.py` (live vs snapshot: `region.json` / summary / vias / images identical, timings, second call no open) on board1 + B04; `tests/layout_edit_b04.py` stitch + neck vs 2.6.1 baseline (via scratch wrapper on copies); delete-via on B04 copy; board1 `review_check.py` + `preview_check.py` (schema 2) |

## Constitution Check (2.0.1)

| Principle | Check | Status |
|---|---|---|
| I Gates | unchanged | PASS |
| II Data safety | board read only; files only under `Ansys AEDT Copilot/snapshots/`; edit still on a COPY | PASS |
| III Defaults | template row `snapshot.use_for_region` | PASS |
| IV Guides | `layout_edit` | PASS |
| V Regression | B04 cases identical; review / preview checks re-run | PASS |
| VII Contracts | contract file; input checks unchanged (`_box`) | PASS |
| VIII Package | snapshot logic in `layout_snapshot/`; `extract` unchanged except `scale` | PASS |
| IX Stable interface | additive (`source`), minor | PASS |
| X Tool catalog | no change | PASS |
