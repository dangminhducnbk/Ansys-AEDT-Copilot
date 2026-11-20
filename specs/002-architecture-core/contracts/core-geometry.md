# Contracts: `aedt_copilot.core.geometry` (pure) + `aedt_copilot.core.geometry_edb`

Units: metres (EDB). Moved verbatim from `cut_board/geometry.py`; results bit-identical (golden JSON, `==`).
Validation: NONE per call (hot path, plan Complexity Tracking); preconditions are the caller's duty.
Side effects: none. Tests: `tests/unit/test_core_geometry.py`.

| Function | Inputs (precondition) | Output |
|---|---|---|
| `point_seg_dist(px, py, ax, ay, bx, by) -> float` | 6 finite floats; zero-length segment allowed | distance point → segment |
| `seg_seg_dist(a, b) -> float` | `a`, `b` = `(x0, y0, x1, y1)` finite | 0.0 on proper crossing, else min end-point distance |
| `point_in_poly(x, y, pts) -> bool` | `pts` list of `(x, y)` | even-odd rule; < 3 points → False |
| `poly_area(pts) -> float` | list of `(x, y)` | absolute shoelace area |
| `bbox_of(pts) -> (xmin, ymin, xmax, ymax)` | non-empty list | bbox; empty → ValueError (unchanged) |
| `edges(pts) -> list[(x0, y0, x1, y1)]` | list of `(x, y)` | closed ring; first edge = last → first point |

## `geometry_edb.prim_points(p) -> list[(x, y)]`

Input: PyEDB primitive. Output: outline points (m), ≥ 3, else bbox corners. Getter order unchanged
(`polygon_data.points` → `points()` → .NET `Points`). Never raises for an unreadable outline (falls back to
`p.bbox`); AttributeError if `p` has no `bbox`. Offline test with fake objects for the fallback order.

`aedt_copilot.cut_board.geometry` re-exports all 7 names unchanged.
