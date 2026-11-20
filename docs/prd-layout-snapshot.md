# PRD: Layout snapshot (digitized board) for fast review

Status: draft for `/speckit-specify` · Date: 2026-11-10 · Owner: repo owner · Target: minor release (2.x)

## 1. Problem

Every review-type step reads geometry live from EDB through PyEDB / .NET:

| Step | How it reads today | Cost |
|---|---|---|
| `design_review` / `isim_review` (review_checks) | Opens EDB, builds a copper index per channel window, `PolygonData.PointInPolygon` per sample point, lazy per layer | ~60 s for 2 channels on board1; repeated in full on every re-run |
| 022 cut preview (`isim_cut_preview`) | Opens EDB, computes extent, finds end GND pins | EDB open + per-object calls on every recompute |
| End check / GND decision (015 / 019) | Opens EDB again | Same |
| `layout_region` (layout_edit) | Opens EDB, converts region to shapely | Own conversion, not shared |

Each tool opens the board again, walks objects one .NET call at a time, and then throws the result away. Changing one threshold or adding one check means reading the board again.

## 2. Goal

Read the board **once** into a **layout snapshot**: a pure-Python, file-cached copy of the geometry, nets, layers, padstacks and components. Review steps then run on the snapshot without EDB, with the **same results** as today.

### Success criteria

| ID | Criterion |
|---|---|
| SC-1 | `tests/review_check.py`: results from the snapshot are identical to today's live-EDB results for board1 (U14_U26 24 items / 0 points; U21_J25 29 items / 11 points) and for the test1 PCIe interface (19 HIGH / 46 MEDIUM / 24 INFO), with the same ids, severities and point coordinates within 1 µm |
| SC-2 | Re-running a review on an existing, valid snapshot takes ≤ 10 % of today's time (target: seconds) |
| SC-3 | Snapshot build time is measured and reported for board1 and test1 (full board and net-window modes). Baseline numbers go into the spec |
| SC-4 | The board `.aedb` is never modified; the snapshot is written only under the Copilot output folder |
| SC-5 | A stale snapshot (board changed) is never used silently: it is rebuilt, or the step stops with a message |

### Non-goals

- Writing geometry back to EDB. layout_edit keeps its own edit path; it may read from the snapshot later.
- Replacing EDB for cutting, ports, setup or solving.
- Any change to review thresholds, severity rules or report wording.

## 3. Users and flows

| User | Flow |
|---|---|
| Engineer (via Claude) | `isim_start` → the snapshot of the interface nets' window is built in the background while content is discussed → Gate A → review runs on the snapshot |
| Engineer re-reviewing | Changes a threshold → review re-runs in seconds from the snapshot |
| Engineer on any board | `design_review(aedb, ...)` builds or reuses the snapshot automatically |
| Developer | New review check = a function on the snapshot API; no PyEDB knowledge needed; offline unit tests use small fake snapshots |

## 4. Functional requirements

### 4.1 Content of the snapshot

| FR | Item | Detail |
|---|---|---|
| FR-01 | Stackup | Layers in order: name, type (signal / dielectric), elevation, thickness, material. Plane-layer flag per the existing rule (largest GND polygon area ≥ `review.plane_area_ratio` × board max) |
| FR-02 | Nets | Name, GND / power / signal class (same classification as today) |
| FR-03 | Polygons | Per layer + net: outline and voids as shapely Polygon. Arcs approximated with chord error ≤ 1 µm (setting). Primitive id kept |
| FR-04 | Traces (paths) | Centerline points, width, end caps, layer, net, primitive id; plus a buffered shapely shape |
| FR-05 | Padstack instances (vias + pins) | Position, rotation, net, padstack def, start / stop layer, `is_pin`, component, backdrill info |
| FR-06 | Padstack defs | Per layer: pad / antipad / thermal shape and size (circle, rectangle, oval, polygon); hole size and plating |
| FR-07 | Components | Refdes, part, type (R / C / L / IC / connector), pins, placement layer, transform, body bbox, RLC values for 2-pin parts |
| FR-08 | Spatial index | STRtree per layer (copper by net) built on load, not stored |

### 4.2 Scope modes

| FR | Mode | Detail |
|---|---|---|
| FR-09 | Window | Bbox of the given nets + margin (default 3 mm, same as today's copper index window). This is the default for review and isim |
| FR-10 | Full board | Whole board, on request (`scope=board`) |
| FR-11 | Reuse | A window request that falls inside an existing valid snapshot (full board or a larger window) reuses it |

### 4.3 Cache and validity

| FR | Item | Detail |
|---|---|---|
| FR-12 | Location | `<output root>/Ansys AEDT Copilot/snapshots/<board stem>/<key>/`. Never inside the `.aedb` |
| FR-13 | Format | Versioned. Geometry as WKB (or pickle of shapely ≥ 2, decided in plan), metadata as JSON. `schema_version` field; a schema change means rebuild |
| FR-14 | Key / validity | Board path + `edb.def` size + mtime + scope + arc tolerance + schema version. Any mismatch → rebuild (SC-5) |
| FR-15 | Lock | Build skips with a message if the board is locked by AEDT (`.lock`), same as other tools. Never deletes the lock |
| FR-16 | Clean-up | Old snapshots are kept; a `list` / `remove` op exists. Removing a snapshot asks the user (it is a user file) |

### 4.4 Build

| FR | Item | Detail |
|---|---|---|
| FR-17 | Speed | Direct .NET calls with cached net / layer / padstack objects (the layout_edit `ops.py` approach), not per-object PyEDB wrappers |
| FR-18 | Background | Build runs as a task (`task_result`), so Claude can continue talking at Gate A |
| FR-19 | Report | Build writes `snapshot.json`: counts per type / layer, build time per phase, board key, warnings (unsupported shapes) |
| FR-20 | Unsupported shapes | Any primitive that cannot be converted is listed with id + layer; checks touching it fall back to live EDB, or the step warns (decided in plan). Never dropped silently |

### 4.5 Consumers

| FR | Consumer | Change |
|---|---|---|
| FR-21 | `review_checks` (reference, trace_stubs, vias, routing) | `_context.py` reads from the snapshot. Check functions get the same inputs; output is identical (SC-1) |
| FR-22 | `cut_board/review.py` HTML (`design_review html=true`) | Images and numbers from the snapshot; HTML identical apart from timing lines |
| FR-23 | Phase 2 (separate tasks, same feature or a follow-up, decided in plan) | 022 cut preview, end check / `gnd_decision`, `layout_region` read from the snapshot |
| FR-24 | Fallback | Setting `review.use_snapshot` (template row, default true). False = today's live path, kept for comparison until one release after acceptance |

### 4.6 Interface (Principle IX / X)

| FR | Item | Detail |
|---|---|---|
| FR-25 | New MCP tool `layout_snapshot` | Ops `build` (aedb, nets or scope=board, margin), `status`, `list`. Safety `read` (writes only to the output folder). Catalog entry + contract + test (registration rules of 010) |
| FR-26 | Existing tools | `design_review`, `isim_review`, `isim_cut_preview` keep their names and arguments; optional `snapshot` argument (path or `auto`). No breaking change → minor version |
| FR-27 | CLI | `python -m aedt_copilot snapshot --op=build|status|list --args-file=` |
| FR-28 | Guides | `review_measure` and `interface_sim` explain when a snapshot is built and reused, and what to do when it is stale |

## 5. Data model (summary)

```
Snapshot
  meta: schema_version, board_path, board_key, scope (window bbox | board), arc_tol_um, built_at, build_s
  layers[]: name, kind, elevation_mm, thickness_mm, is_plane
  nets{}: name -> class
  copper[layer]: list of {id, net, kind: polygon|trace|pad, geom (shapely), width_mm?, centerline?}
  padstack_defs{}: name -> {hole_mm, plated, per_layer: {pad, antipad, thermal}}
  instances[]: {id, net, def, x, y, rot, start, stop, is_pin, comp, pin, backdrill}
  components{}: refdes -> {part, type, layer, transform, bbox, pins[], rlc?}
```

Units: mm in the snapshot (EDB metres are converted once at build).

## 6. Accuracy rules

- Coordinates in absolute board space. Pin positions = component transform ∘ local (the bug lesson from 2026-10-21: never use local coordinates).
- The arc chord error is a setting; checks that measure distances report it as part of their tolerance.
- SOV own-antipad rule, via stack merge (0.15 mm), and used-layer rules stay in the check code, unchanged. Only the geometry source changes.

## 7. Testing

| Test | Content |
|---|---|
| Unit (offline) | Snapshot schema round-trip; key / stale logic; window reuse; fake snapshot drives each review check; catalog + contract tests for `layout_snapshot` |
| Golden | Live-EDB review outputs of board1 + test1 captured before the change (`tests/unit/golden/pre0xx`) |
| AEDT (copies only) | `tests/review_check.py` on board1 copy and `tests/pcie_check.py` review part on test1 copy: identical to golden (SC-1); timing table build / re-run (SC-2, SC-3); board files unchanged (SC-4) |
| Regression | `tests/regression.py`, `tests/isim_check.py` PASS, references unchanged |

## 8. Performance expectations (to be replaced by measurements)

| Board | Window build | Full build | Re-run review |
|---|---|---|---|
| board1 | < 30 s | ~1–2 min | seconds |
| test1 (~240 MB) | < 1 min | ~3–10 min | seconds |

The first implementation task is a **measurement spike** on copies: time the EDB open, primitive walk, void extraction and padstack read with direct .NET calls; record the numbers in the plan before choosing the cache format.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Results differ slightly (arc approximation, polygon validity) | Golden comparison; `make_valid` with a logged count; arc tolerance setting |
| Full board build too slow / too large on huge boards | Window mode is the default; full board only on request |
| Stale cache used after the user edits the board | Key on `edb.def` size + mtime + schema (FR-14) |
| Two consumers build the same snapshot at once | Build lock file per key; the second caller waits or reuses |
| Memory for full board | Per-layer lazy load of geometry files |

## 10. Rollout

1. Spike: measure (copies of board1, test1).
2. Snapshot build + cache + `layout_snapshot` tool.
3. review_checks on snapshot behind `review.use_snapshot`; golden identical.
4. Phase 2 consumers (022 preview, end check, layout_region) as separate tasks.
5. Release minor, CHANGELOG (restart Claude: new tool + guide change). Remove the live path one release later only on the user's go.

## 11. Constraints (from project rules)

- Spec Kit flow: specify → clarify → plan → tasks → implement → converge. Commit after each step. Guard hook is never bypassed.
- Work on copies of `test/` boards; never touch originals; never delete user files (including `.lock` and old snapshots) without permission.
- No AEDT GUI use while the user is on the machine.
- Defaults in `templates/autocut_template.csv` (Principle III).
- The user pushes. Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Independent of feature 022: if run in parallel, use its own worktree (one active feature per checkout).

## 12. Open questions for `/speckit-clarify`

1. Phase 2 consumers in this feature or in a follow-up feature?
2. Cache format: WKB + JSON (portable, diff-friendly metadata) or pickle (fastest)?
3. Unsupported shapes: fall back to live EDB per check, or warn and skip?
