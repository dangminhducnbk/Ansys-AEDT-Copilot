<!-- Layout edit / improvement of an EDB (planes, voids, traces, stitch vias) on a COPY: layout_region -> plan -> layout_edit -->
# Layout edit (improvement) – guide for Claude

Use for any request to CHANGE copper or vias of an `.aedb` (PI/SI improvement: widen a plane neck, carve copper from
another net, add stitch vias, re-route a short power trace, open a routing channel, fix an antipad...).
**Never write ad-hoc pyedb / pyaedt scripts for this.** Everything is done by 2 tools of this server:

| Step | Tool | What |
|---|---|---|
| 1 | `layout_region(board, box, layers, nets)` | Read only. Polygons (id, net, area), traces, vias per net + `vias` list (id, net, padstack, x, y, from, to; max 200, filter with `nets`), padstacks, PNG per layer, `region.json` |
| 2 | (Claude) | Write the plan (ops below). Use numbers from step 1; keep it short |
| 3 | `layout_edit(plan)` | One EDB session on a COPY: all ops, automatic antipads + sliver-void cleanup, save, checks, PNG before/after, `changes.md` |
| 4 | (Claude) | Report: result `.aedb` path (full absolute path), check table (FAIL first), images, what changed. Ask user to review |

Layout snapshot (2.7, template `snapshot.use_for_region`, default on)
- `layout_region` reads the board from the cached layout snapshot (`<board dir>\Ansys AEDT Copilot\snapshots\`):
  result identical to a live read (same ids, coordinates, images). The first call on a board builds the whole-board
  snapshot (board opened read-only once; slower on a big board); every later box answers in seconds without opening
  the board. A review / preview snapshot that already contains the box is reused.
  Board saved since → rebuilt automatically, never used stale.
- `source` in the result: `snapshot` (index / window `reused` or `built`) or `live` + `warning` (why: board open in
  AEDT and a build was needed, data missing, ...). On `live` with a warning, tell the user in one line; results are
  still correct (live read).
- `layout_edit` reuses the snapshot for its "before" read when a cached window already contains the region
  (`before_source` in the result); otherwise it reads the copy live as before. Call `layout_region` on the area first
  (normal flow) and the edit starts faster. The "after" read and checks are always live on the result copy.

Rules
- The source board is never opened for writing. Result: `<board dir>\Ansys AEDT Copilot\layout_edit\<name>_<time>\<board>_<name>.aedb`
  (+ `plan.json`, `changes.json`, `result.json`, `changes.md`, `img\`). To chain edits, use the previous result as `board`.
- One `layout_edit` call = one plan with ALL ops of the request (one open / one save). Do not call it once per op.
- If an op fails, nothing is saved and the copy is deleted; fix the plan and call again.
- Any check FAIL -> tell the user before anything else; do not hide it. WARN -> explain.
- Units: mm. Shapes: `[x0, y0, x1, y1]` (box), `[[x, y], ...]` (polygon), `{"ext": [...], "holes": [[...]]}`,
  `{"box": [...]}`, `{"circle": [x, y, r]}`.
- Defaults: `templates/layout_edit_template.csv` (plane_gap 0.254, min_copper_gap 0.1, antipad_margin 0.125,
  via_pitch 0.6, via_search 0.8 ...). Override per plan in `"rules": {...}` only when the user asks or the board needs it.
- Layer names / padstack names / net names must be exactly as in `layout_region` output.

## Plan
```json
{
 "board": "D:\\...\\board.aedb",
 "name": "ASM_1P1V_U200neck",
 "purpose": "Widen ASM_1P1V L9 neck at U200, reroute VCC_1P2V on L12",
 "region": [60, 55, 90, 75],
 "rules": {},
 "ops": [ ... ],
 "checks": [ ... ]
}
```
`region` optional (default = bbox of all ops + 2 mm). Checks and images use this region.

## Ops
| op | fields | does |
|---|---|---|
| `add_copper` | layer, net, shape, [keep_out], [gap], [clip=true], [merge=true] | Adds copper for `net` in `shape` minus other-net copper + gap minus other-net via clearance; merges with touching same-net polygon. `clip=false` = shape already has clearances |
| `carve` | layer, net, from_net, shape, [keep_out], [gap], [allow_cut_vias=false] | Takes copper of `from_net` for `net` inside `shape` (same layer): void in from_net (+gap), new copper for net, merge. Refuses if the cut would remove copper under a from_net via/pin |
| `remove_copper` | layer, net, shape | Cuts the outline of `net` polygons (not only a void): e.g. "VCC_1P2V L9 removed east of x=71.746" |
| `void` | layer, net, shape | Adds a void in `net` polygons intersecting `shape` |
| `trace` | layer, net, pieces=[{points, width}] or points+width, [clear_pours=gap] | Draws trace(s). `clear_pours`: cuts a channel (width/2 + gap) in other-net pours along it. Reports min gap to other copper |
| `via` | net, padstack, from, to, points, [land], [void_layers], [pitch], [pitch_same], [search], [antipad_margin] | Places vias. Landing on each `land` layer (default from/to): centre inside own-net POLYGON → pad + land_margin must be fully inside that polygon (plane landing); centre outside polygons → OK if the centre is on own-net trace copper or on an own-net pin/via pad (trace end, SMD pad = via-in-pad). Keep pad + min_copper_gap from other-net traces; centre distance ≥ `pitch` (via_pitch) to other-net vias/pins and ≥ `pitch_same` (via_pitch_same) to same-net vias/pins and other new vias; else moved ≤ `search`, else dropped (reported). Antipads (pad + antipad_margin) cut in other-net polygons on every spanned layer |
| `delete` | ids | Deletes primitives AND vias (padstack instances) by id, as listed by layout_region. Component pins are refused. A plan with only `delete` needs `region` |

Ops run in order and see the result of earlier ops (e.g. `remove_copper` then `add_copper` in the freed area,
`carve`/`add_copper` on a plane then `via` landing on the new copper).

## Checks (always run) + optional
Always: new copper overlap between nets, gap of new copper to other nets (≥ min_copper_gap), copper pieces per edited
net/layer (split = WARN), via/pin contacts of edited nets lost (FAIL; WARN "contacts removed by design, connectivity OK"
only when every net that lost contacts has a `connected` check that PASSes), new vias: landing on the op's `land` layers
(own copper or own pin/via pad), pad clearance, pad-to-pad.
Images: GND/VSS nets always blue; other nets from the rest of the palette.
Optional in `"checks"`:
- `{"type": "min_width", "layer", "net", "window": shape, "from": shape, "to": shape, "min": 1.0}` — narrowest copper
  path (current neck) between two zones, before → after.
- `{"type": "connected", "net", "from": "U138", "to": ["R561", "R562"]}` — EDB connectivity from a component pin.

## Patterns (from real cases)
- **Plane neck too narrow (PI-DC current density / IR drop)**: `layout_region` around the neck → `min_width` check
  before → `carve` from a neighbour net (or `remove_copper` of a net that can move + `add_copper`) → `min_width` check.
- **Two planes of same net on different layers, weak link**: `carve`/`add_copper` on one layer if needed, then `via`
  stitch points along the overlap (land = both layers). Dropped points are reported; re-plan if too few.
- **Moved net needs a new route**: `remove_copper` of the old plane part, `trace` with `clear_pours` on the routing
  layer, `via` to join layers, `connected` check.
- **Missing antipad / clearance**: `void` with a circle.

## Report to the user (reply language = user's)
1. Result path (full), PASS/WARN/FAIL counts, FAIL details first.
2. What changed (ops table from `changes.md`), dropped/moved vias.
3. Images (full paths) before/after. 4. Machine time (`total_s`).
