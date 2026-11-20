# Contract: reference classification (feature 032)

## review.check_reference(B, cu, paths, excl_pts, R, step, oc=None) -> [finding]

Per path sample (centre + both edges, `review.sample_step_mm`, samples within `review.pad_exclusion_mm` of a channel
pad / via skipped), per reference plane: `cov` | `own` (via clearance, nearest via in the void same net as the trace)
| `other` (via clearance, nearest via of another net) | `onet` (no GND, other-net copper at the centre) | `gap`.
Runs of equal labels → one finding each:

| Label | Finding | Severity | ref |
|---|---|---|---|
| every plane `gap` / `onet` | Loss of reference | HIGH | all planes `, ` |
| one plane `onet` (others not missing) | Ref to other net | MEDIUM | `<plane>: <net>` |
| one plane `gap` (others not missing) | SOV | MEDIUM | `<plane>` |
| no missing plane, ≥ 1 `other` | Trace over via clearance | INFO | planes with `other` |

Extra keys: `trace_pts` (sample centres of the stretch, m), `vias` ([x, y, net] of the clearance vias),
`void_mm` ([w, h] largest void), `planes_missing`.

Via clearance: point in a void (bbox + polygon) containing ≥ 1 padstack instance centre; distance(point, convex hull
of those centres) ≤ min(void w, h) / 2 + 0.05 mm.

## Board.insts_in(window) -> [(x, y, net)]

All padstack instances (vias + pins) with centre in the window; cached per Board.

## review.svg_ref_panels(win, cu, planes, paths, signals, vrows, gnd_ps, items, oc=None) -> (html, legend)

One SVG panel per plane (title = plane name), inline flex container.
