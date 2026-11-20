# Data model: Layout snapshot (schema_version 1)

Units in files: **metres** (same as EDB / today's review code, so the facade returns values unchanged; the PRD's "mm in
files" is replaced by "units of the source" to keep results bit-identical). Reports (`snapshot.json`, tool output)
use mm.

## Folder

```text
<board folder>/Ansys AEDT Copilot/snapshots/<board stem>/<cell>_<key8>/
  index.json            board index
  .build.lock           while building (tool's own file)
  w_<x0>_<y0>_<x1>_<y1>/   window (µm integers) or w_board/
    window.json  geom.wkb  snapshot.json  .build.lock
```

`key8` = first 8 hex of sha1(board key). A changed board → new key → new folder; old folders kept (FR-009).

## Board index (`index.json`)

| Field | Content |
|---|---|
| `schema_version`, `kind: "index"` | 1 |
| `key` | `{aedb, cell, def_size, def_mtime_ns, schema}` |
| `built_at`, `times` | ISO time, seconds per phase |
| `layers` | metal layers top → bottom: `[name, lower_elevation, thickness]` |
| `power_nets` | names with `is_power_ground` (order of `nets.power`) |
| `nets` | all net names (order of `nets.nets`) |
| `prims` | rows `[id, kind ("Path"/"Polygon"/...), layer, net, is_void, bbox9]` in layout order, metal layers only |
| `insts` | rows `[id, net, def, x6, y6, start, stop, is_pin, comp, name]` in layout order |
| `comps` | refdes → `{type, part, numpins, layer, pins: [inst id, ...]}` (pin-list order) |
| `plane_area` | ref net → layer → `[max area, prim id, bbox9]` |
| `pad_defs` | def name → `{hole_diameter, hole_props0, pads: {layer: [v, v]}}` (values converted like `padstack_dims.si` input) |
| `refs` | reference nets at build (template `cutout.reference_nets`) |

## Window (`window.json` + `geom.wkb`)

| Field | Content |
|---|---|
| `schema_version`, `kind: "window"`, `index_key`, `window` (m), `scope` (`window`/`board`), `arc_tol_um`, `margin_mm` | — |
| `geoms` | prim id → `{off, len, voids: [[void id, bbox9, off, len], ...]}` (outline + voids overlapping the window) |
| `paths` | prim id → `{center: raw points, width, length}` |
| `backdrill` | via id → backdrill dict (PyEDB format) for non-pin instances of non-power nets in the window |
| `pin_bbox` | pin id → `[[x0, y0], [x1, y1]]` for non-power pins in the window |
| `unsupported` | `[{id, layer, net, reason}]` |
| `counts`, `times` | per kind / layer; seconds per phase |

Validation: missing / unreadable file or schema / key mismatch → state `stale` (rebuild). `contains(window, need)` =
need inside window (board scope contains all).

## Facade (`facade.SnapEdb`) — PyEDB attributes answered

| Attribute | Used by |
|---|---|
| `edb.active_cell.GetName()`, `edb.close()` (no-op), `edb.core.Geometry.PointData(x, y)` → `(x, y)`, `edb.edb_value(v)` → `float(v)` | review_checks, Copper |
| `stackup.signal_layers` (ordered dict-like), `stackup.layers[n].lower_elevation / thickness` | Board, layer_range_names |
| `nets.nets[n].primitives / padstack_instances / components`, `nets.power` | Board, _collect, trace_channel, routing |
| `components.instances[rd]`: `type, partname, numpins, pins{name: inst}` | trace_channel, end_type |
| `modeler.primitives_by_layer[lay]` (window prims, layout order) | Board.other_prims |
| `padstacks.definitions[name]`: `hole_diameter`, `hole_properties`, `pad_by_layer[l].parameters_values` | Board.padstack_dims |
| primitive: class name `Path` / `Polygon`, `id, layer_name, net_name, is_void, bbox, area(), voids, polygon_data.core.PointInPolygon(pt), center_line, width, length` | Board, Copper, _collect |
| instance: `id, net_name, position, padstack_definition, is_pin, start_layer, stop_layer, layer_range_names, component_name, backdrill_parameters, bounding_box` | _collect, Board, end_type |

A geometry or value that is not in the snapshot raises `SnapshotMissing` (never a silent default).
