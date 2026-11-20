# Research: Layout snapshot (phase 1)

## R1. Where today's review time goes (spike, board1 copy, 2 channels, 2026-11-10)

| Phase | s |
|---|---|
| `Board.other_prims` (PyEDB walk of plane-layer primitives) | 40.7 |
| `Copper.net_at` 180 882 calls (.NET `PointInPolygon`, incl. index build 4.7) | 14.6 |
| `trace_channel` | 12.4 |
| EDB open / close | 10.0 / 2.6 |
| `Board.__init__` | 9.1 |
| `Copper.voids_at` 2 121 calls | 4.8 |
| `_collect` | 3.1 |
| via rows + trace stubs + lengths (pure Python) | 0.4 |
| **measure total** | **86.1** (+ open / close ≈ 100 s wall) |

Decision: the gain is from removing EDB access, not from vectorizing the sampling (pure compute is 0.4 s). The check
loops stay as they are; only the object answering `PointInPolygon` changes.

## R2. Accuracy of shapely chords vs EDB arcs

- Arc encoding: a point with `Y > 1e300` is an arc marker, `X` = arc height between the previous and next point.
  Normal sign −1 (left normal × −1) matched `ArcData.GetMidPoint()` (0.39 µm at 1 nm tolerance vs 150 µm with +1).
- Replaying the 180 882 `net_at` and 2 121 `voids_at` queries of a live review against shapely polygons built with a
  1 µm chord tolerance: **0 differences**. Boundary semantics: `intersects` (contains ∪ boundary).
- 2 of 579 window polygons were invalid for GEOS; point tests on the raw ring still matched. Decision: no
  `make_valid` for point tests (it can move edges); count reported as info.

Decision: `snapshot.arc_tol_um = 1`; hard criterion = identical items / ids / severities / points; coordinates are the
same sample points on both paths, so identical too.

## R3. Direct .NET read cost (same board)

| Read | s |
|---|---|
| `layout.Primitives` metadata, 27 021 prims (layer, net, type, void, bbox) | 2.8 |
| outline + voids of 579 window prims (526 840 points) | 6.4 |
| 47 189 padstack instances (id, net, position, pin flag, def) | 2.8 |
| shapely build of window polygons | 0.6 |

Decision: 2 tiers. Board index (≈ 15–25 s incl. open) once per board version; window geometry (≈ 10 s) per window.

## R4. Format (clarify Q2 = A)

Decision: `index.json` + `window.json` (metadata, `schema_version`), `geom.wkb` (length-prefixed WKB records of
outline / void polygons; offsets in `window.json`). Pickle rejected: ties files to the shapely / Python version.

## R5. Plane rule needs board-wide data (review note 1)

`Board.planes` = layers whose largest reference-net polygon area ≥ ratio × board max. Decision: the index stores per
(ref net, layer) the max non-path polygon area and its primitive id + bbox. Facade yields the real primitive when it
is in the window, else a geometry-less stub with that area. The ratio stays a review parameter (no rebuild when it
changes).

## R6. Nearest GND via is board-wide

`Board.gnd_ps` = every padstack instance of the reference nets. Decision: the index keeps all instances (light rows),
so the facade returns the same list.

## R7. Validity key (review note 6)

EDB touches a 0-byte `edb.def.tmp` on every open; `edb.def` is unchanged by read-only opens. Decision: key = absolute
`.aedb` path (normcase) + cell + `edb.def` size + `st_mtime_ns` + `SCHEMA_VERSION`. Window adds arc tolerance + window.

## R8. Order and rounding

PyEDB rounds `bbox` to 9 and pin / via `position` to 6 decimals and applies the component transform to pins.
Build applies the same. Order: the facade returns per-net primitives / instances in layout order and component pins in
pin-list order. T012 result: board1 (2 channels) and test1 (PCIe) outputs are identical to the live golden, including
item ids, point ids and summary text (any order difference would change ids on ties) → layout order accepted.

## R9. Pin bounding box for `end_type`

`end_type` uses `pin.bounding_box` (layout object instance `GetBBox`) of the first signal pin of each end. The window
stores `GetBBox` of every non-power pin inside the window. Measured (T012, board1): PyEDB `bounding_box` costs 65 ms
per pin because it calls `GetLayout().GetLayoutInstance()` for every pin (2 632 pins = 186 s). Taking
`GetLayoutInstance()` once (7 s, first call) and `GetLayoutObjInstance(pin, None).GetBBox()` per pin = 12 µs →
2 632 pins + 1 608 backdrill reads = 8 s. A missing box raises `SnapshotMissing` (BaseException) inside the facade,
so `end_type`'s `except Exception` cannot hide it; the index-only tracing pass uses `lenient=True` (ValueError, result
discarded).

## R10. Concurrency (review note 5)

Tested (T020, test1 copy, `tests/snapshot_check.py` step 5): a `snapshot --op=build` subprocess (index + window
rebuilt after a board change) and a live review in another process open the same `.aedb` read-only at the same time;
both finish, review = golden. No board-level serialization needed; the per-folder build lock stays.

## R11. Golden

Live outputs captured on copies BEFORE any code change (`tests/unit/golden/pre023_review_board1.json`,
`pre023_review_test1.json`): board1 CPHY_U14_U26 24 items / 0 points, CPHY_U21_J25 29 items / 11 points; test1
PCIE_U14_J25 (19 HIGH / 46 MEDIUM / 24 INFO).
