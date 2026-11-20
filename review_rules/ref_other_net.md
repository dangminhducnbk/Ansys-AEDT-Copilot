<!-- Trace references another net's copper instead of GND -->
# Reference to another net

| Field | Value |
|---|---|
| id | ref_other_net |
| findings | Ref to other net = Trace references another net |
| section | reference |
| not ok when | a reference plane has copper of another net under the trace |
| thresholds | review.sample_step_mm, review.pad_exclusion_mm |
| limit key | review.sample_step_mm |
| code | yes |

## What
Same sampling as `sov`. The reference plane has no GND at the spot but copper of ANOTHER net (power,
other signal) → the trace references that net (user definition of "reference change GND → other net").

## Why
the return current flows on {other} instead of GND: noise coupling between the signal and that net, impedance change.

## Fix
route this segment over GND (or move the other net's copper away from under the trace).

## Discuss
Name the other net and the plane. Referencing a power plane can be acceptable with stitching
capacitors near the transition: ask the engineer.

## Report
- Reference to other net: trace runs over copper of another net.

## Issue
{net} ({layer}) references {other_net} copper on {planes} instead of GND.

## Recommendation
Route this segment over GND.
