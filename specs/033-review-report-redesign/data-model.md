# Data model (033)

## Channel routing data `ch["routing"]` (built in `review._review_edb`, metres)

| Field | Content |
|---|---|
| `comp_a`, `comp_b`, `name` | ends, channel name |
| `metal` | signal layers top → bottom; `gnd_layers` = plane layers (`Board.planes`) |
| `paths` | `{net, layer, w, pts, len}` (as `_collect`) |
| `vias` | via rows of `via_rows` (`net, x, y, range, used, kind, has_bd, stub_mm`) |
| `pins` | `{net, comp, x, y, range, def, bbox}` (bbox = pad box or None) |
| `chains` | `{start net: [nets through series parts]}` |
| `comp_bb` | `{refdes: [x0, y0, x1, y1]}` end + series components |
| `H` | `{layer: dielectric distance to nearest reference plane}` |

## Pair routing view (derived in `review_routing`)

`members` (P first / A first), `walk[member]` = steps `pin | seg(layer, len) | via(from, to, v) | comp`,
`signature` (layers / vias / backdrill / stub, no length), `lengths[member] = {layer: m}`.

## Serpentine finding (`check = "Serpentine"`, MEDIUM, section routing)

`net, layer, x, y, bbox, group` + `serp = {W, H, A, G, base, n_bumps, x0..y1, peak, peak_n, gpair, c90, chams, short,
violations [(code, text)]}`; codes `A` (A > 3W), `G` (G < 3H), `C` (90° corner), `S` (chamfer c < 1.5W − 5 %).

## Report rows

Row = one abnormal point × section, HIGH or MEDIUM items only (as 026); rendered Index (1..n per section), Verdict
NOT OK, Description (`Issue` / `Recommendation` per item, duplicates removed), Picture (+ `Location`).
