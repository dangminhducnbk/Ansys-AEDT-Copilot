<!-- Diff pair members farther apart than the nominal gap -->
# Pair members split apart

| Field | Value |
|---|---|
| id | pair_gap |
| findings | Pair gap = Pair / trio members split apart |
| section | routing |
| not ok when | gap > nominal gap × ratio over ≥ the minimum length |
| thresholds | review.pair_gap_ratio, review.pair_gap_min_len_mm, review.neckdown_zone_mm, review.bga_breakout_margin_mm |
| limit key | review.pair_gap_ratio |
| code | yes |

## What
Diff PAIRS only (not CPHY trios). Per layer, edge-to-edge gap to the partner trace along the member;
nominal gap = the stackup table (rule `stackup_width`) or the measured median; flagged where gap > nominal ×
`review.pair_gap_ratio` over ≥ `review.pair_gap_min_len_mm`. The neck-down zone around pads / vias is skipped. One row
per pair and layer (longest stretch located, number of stretches and total length). A stretch whose middle lies inside
a length-matching serpentine of the same pair (rule `serpentine`, box + 0.5 mm) is not a pair gap (2.11.0). A stretch
whose middle lies in the body of a BGA end (+ `review.bga_breakout_margin_mm`, default 0) is an intentional break-out
between the balls / vias and is never checked (4.1.0); the count is in the data (`skipped_in_bga`).

## Why
the pair loses its coupling here: the differential impedance rises and the pair picks up more noise.

## Fix
route the members side by side at the nominal gap (keep them together around obstacles).

## Discuss
Give the largest gap next to the nominal and the stretch length.

## Report
- Pair gap: pair / trio members split apart (serpentine for length matching and BGA break-out excluded).

## Issue
Pair {group} splits apart on {layer}.

## Recommendation
Route the pair members side by side.
