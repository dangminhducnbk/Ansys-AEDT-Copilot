<!-- Trace close to the edge of its reference plane or a large void -->
# Trace near reference plane / void edge (3H)

| Field | Value |
|---|---|
| id | plane_edge |
| findings | Near plane edge = Trace close to the edge of its reference plane |
| section | reference |
| not ok when | trace nearer than factor × H to a plane / void edge over ≥ the minimum length |
| thresholds | review.plane_edge_factor, review.plane_edge_min_mm, review.plane_edge_min_len_mm, review.neckdown_zone_mm |
| limit key | review.plane_edge_factor |
| code | yes |

## What
Per reference plane: GND under the trace centre but no GND at D = max(`review.plane_edge_factor` × H,
`review.plane_edge_min_mm`) to one side (H = dielectric between trace and plane, from the stackup elevations).
Antipads (voids ≤ 2 mm) ignored; no GND under the centre = `sov`. Runs ≥ `review.plane_edge_min_len_mm`. ONE finding
per stretch listing every plane whose edge is close, each with its distance limit (032, user 2026-11-11 "Gộp"); one
row per net and layer (longest stretch located, number of stretches, total length).

## Why
the return current under the trace is squeezed at the plane / void edge: impedance rises and the field fringes (radiation, crosstalk).

## Fix
keep the trace ≥ {fac:g} × H from the edge of the GND on {ref} (move the trace or extend the plane).

## Discuss
Give the plane, the distance limit (3H) and the stretch length.

## Report
- Near plane edge: trace runs too close to the edge of its reference plane.

## Issue
{net} ({layer}) is routed too close to the GND plane edge on {planes}.

## Recommendation
Move the trace away from the plane edge or extend the GND plane.
