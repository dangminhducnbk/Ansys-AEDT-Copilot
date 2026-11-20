<!-- Length-matching serpentine of a diff pair: bend gap, bump height, corners, chamfers -->
# Serpentine (length matching) geometry

| Field | Value |
|---|---|
| id | serpentine |
| findings | Serpentine = Serpentine outside the geometry rules |
| section | routing |
| not ok when | a serpentine breaks a geometry limit (one finding per serpentine; passing ones are not listed) |
| thresholds | review.serp_gap_factor, review.serp_amp_factor, review.serp_chamfer_factor, review.serp_chamfer_tol, review.serp_rise_factor, review.serp_bump_max_mm, review.serp_bump_spacing_mm, review.serp_bump_ratio, review.serp_min_bumps, review.serp_excl_mm, review.serp_step_mm |
| limit key | review.serp_amp_factor |
| code | yes |

## What
Diff PAIRS only (pairs from the first net of each series chain, both naming directions). Detection: one member has
≥ `review.serp_min_bumps` repeated bumps relative to the other member (centre distance > nominal gap +
`review.serp_rise_factor` × W, bump shorter than `review.serp_bump_max_mm`, bumps closer than
`review.serp_bump_spacing_mm`, neighbour heights within 1/`review.serp_bump_ratio` .. `review.serp_bump_ratio`), outside
`review.serp_excl_mm` around the pair's pins / vias (break-out). A far run that touches that zone and never comes
back to the partner before the path end is the pair splitting toward its pins / vias (fan-out), not a bump (2.11.1). Measures: G = edge-to-edge gap between adjacent
parallel segments of the serpentine (≥ `review.serp_gap_factor` × H, H = dielectric distance from the trace layer to
the nearest reference plane), A = base line centre → bump top centre (≤ `review.serp_amp_factor` × W), no 90° corner,
45° chamfer c (segment at ~45° to the pair direction) ≥ `review.serp_chamfer_factor` × W with
`review.serp_chamfer_tol` tolerance. One finding per serpentine that breaks a rule. A pair separation inside a
serpentine of the same pair is not a `pair_gap` finding.

## Why
- `A`: tall bumps couple the bends to each other and to the partner: the delay saved by the serpentine is wrong and the impedance varies.
- `G`: bends closer than 3H couple to each other (self crosstalk): the signal shortcuts the serpentine.
- `C`: 90° corners add capacitance and reflections.
- `S`: short chamfers act like 90° corners.

## Fix
- `A`: lower the bumps (A ≤ 3W), use more bumps of smaller height.
- `G`: space the bends at least 3H apart.
- `C`: use 45° chamfers or arcs.
- `S`: make every 45° chamfer at least 1.5W long.

## Discuss
Quote A / G / c with W and H (mm and mil); several serpentines on one pair with the same violation can be summarised.

## Report
- Serpentine: bends at least 3H apart, bump height at most 3W, no 90° corner, 45° chamfer at least 1.5W.

## Issue
Serpentine on {net} ({layer}): {problems}.
- `A`: bump height A = {A} is more than {amp} × trace width W = {A_lim}
- `G`: gap between bends G = {G} is less than {gap} × height to GND H = {G_lim}
- `C`: {n90} corner(s) of 90°
- `S`: 45° chamfer c = {c} is shorter than {cham} × trace width W = {c_lim}

## Recommendation
{actions}.
- `A`: lower the bumps so that A ≤ {amp}W = {A_lim}
- `G`: space the bends so that G ≥ {gap}H = {G_lim}
- `C`: replace the 90° corners with 45° chamfers or arcs
- `S`: make every 45° chamfer c ≥ {cham}W = {c_lim}
