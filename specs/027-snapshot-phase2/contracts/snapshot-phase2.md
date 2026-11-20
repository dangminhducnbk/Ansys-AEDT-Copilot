# Contract: layout snapshot phase 2 (feature 027)

## layout_snapshot.preview

### extent_key(P, nets, factor) -> dict
`{nets: sorted, extent_type, unitless, round_corner, increments, factor}`; factor None → `P.cutout.expansion`.
Bad nets (empty / not strings) → `CopilotInputError`.

### ExtentCache(folder, P, nets, opener, log)
`get(factor)` → extent points (mm, as `cutter.compute_extent_mm`). File `<index folder>/extents/<sha1(key)>.json`
`{key, pts_mm}`; miss → `opener()` (opened EDB) + compute + write. `hits`, `misses` counters. Same board key =
same index folder, so a changed board never reuses an extent.

### comp_pins(opener, idx, folder, refdes) -> {iid: [[x0, y0], [x1, y1]]}
Every pin of the component; file `<index folder>/comp_pins/<refdes>.json`; miss → board opened once.

### open_for_preview(aedb, cell, P, nets, comps, version=None, log=None) -> context manager
Yields `(edb: SnapEdb, extent: callable(factor), source: dict)`. Window = net window (snapshot margin) ∪ pin
positions of `comps` + 5 mm ∪ base extent bbox + 1.5 mm. Raises `SnapshotFallback` (unsupported primitives, board
locked when something must be built). The EDB opened for misses is closed on exit.

## facade.SnapEdb
- `SnapEdb(index, window=None, lenient=False, extra_pin_bbox=None)`.
- `prim.polygon_data.points` → [[x, y]] exterior (m). `pin.pin_number` = pin name.

## cutter.cut_extent(edb, P, nets, ends, log, end_factors=None, strict=True, extent=None)
`extent(factor)` replaces `compute_extent_mm(edb, ...)` (base = `extent(None)`).

## cut_preview.run → result / preview.json
`source`: `{kind: snapshot | live, index, window, extent_cache: {hits, misses}, seconds, warning?}`.

## review.review(..., snapshot="auto")
`auto` + `review.use_snapshot` → `layout_snapshot.api.for_review`; fallback live + `info.source.warning`.
