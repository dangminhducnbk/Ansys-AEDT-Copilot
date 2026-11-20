# Contract: layout_region / layout_edit on the layout snapshot (029)

## `layout_region(board, box, layers, nets)` (MCP, CLI unchanged)

Result = 2.6.1 keys + `source`:

| Key | Value |
|---|---|
| `source.kind` | `snapshot` or `live` |
| `source.folder` | snapshot window folder (snapshot) |
| `source.index` / `source.window` | `reused` / `built` |
| `source.window_mm` | cached window (mm); `null` = whole-board window (built when no cached window contains the box, Q2 B) |
| `source.warning` | live only when the snapshot was wanted: reason (board locked and a build needed, data missing + ids, error) |
| `source.seconds` | snapshot part time |

Equality (Q1 A): for the same board / box / layers / nets, `region.json`, `layers`, `vias`, `padstacks`, `components`,
`signal_layers` and PNG bytes equal the live read.

Template `snapshot.use_for_region` false → live, `source = {"kind": "live"}`.

## `layout_edit(plan)`

Result / `result.json` gain `before_source` (`snapshot` folder, or `live` + reason). The before read uses the snapshot
of `plan.board` only when a valid window already contains the region (never builds inside an edit). Ops, checks,
`changes.json`, images: unchanged rules.

## Snapshot files (schema 2)

| File | Added |
|---|---|
| `index.json` | `pad_table` {def: {pads {layer: [geometry_type str, raw params]} / err, antipads, hole raw}}; `comps[rd].bbox` [m, round 6] or null |
| `window.json` | geoms `"r": [off, n]` (original points record); void rows `[id, bbox, off, n, roff, rn]` |
| `geom.wkb` | + original point records (float64 x, y pairs; arc marker y > 1e300, x = arc height) |

Schema 1 folders are ignored (stale) and rebuilt on demand; never deleted by the tool.
