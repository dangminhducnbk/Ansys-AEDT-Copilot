<!-- Signal trace runs parallel and close to another net -->
# Coupling to other nets (3W)

| Field | Value |
|---|---|
| id | coupling |
| findings | Coupling to other net = Long parallel run next to another net |
| section | Crosstalk |
| not ok when | edge-to-edge gap < factor × width over ≥ the minimum length |
| thresholds | review.coupling_gap_factor, review.coupling_min_len_mm, review.neckdown_zone_mm |
| limit key | review.coupling_gap_factor |
| code | yes |

## What
Other nets' TRACES (not pours, not reference nets) on the same layer in the channel window. Flagged where
the edge-to-edge gap < `review.coupling_gap_factor` × trace width over ≥ `review.coupling_min_len_mm`. One row per net,
layer and other net.

## Why
a long parallel run close to another net couples noise into the signal (crosstalk).

## Fix
increase the spacing to ≥ {fac:g} × the trace width, or shorten the parallel run.

## Discuss
Name the other net; its kind matters (clock / switching power vs quiet signal): ask the engineer.

## Report
- Coupling: long parallel run next to another net.

## Issue
{net} ({layer}) runs parallel and close to {other_net}.

## Recommendation
Increase the spacing or shorten the parallel run.
