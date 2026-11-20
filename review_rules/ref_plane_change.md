<!-- Signal via changes reference planes without a nearby GND via -->
# Reference plane change at a via

| Field | Value |
|---|---|
| id | ref_plane_change |
| findings | Ref plane change = Ref plane change at signal via |
| section | reference |
| not ok when | no GND via within the limit (with one: OK, kept as data) |
| thresholds | review.ref_change_gnd_via_mm |
| limit key | review.ref_change_gnd_via_mm |
| code | yes |

## What
Per signal via stack: the reference-plane set of the entry layer differs from the exit layer. With a GND
via within `review.ref_change_gnd_via_mm` the return current has a path (OK, kept as data); without one → NOT OK.

## Why
the return current changes plane here; with no GND via close by it takes a longer path (loop inductance, crosstalk).

## Fix
add a GND stitching via within {lim:g} mm of this via.

## Discuss
Give from / to layers and planes and the nearest GND via distance next to the limit. OK rows are data:
mention them only when asked.

## Report
- Reference plane change: signal via changes plane without a GND via nearby.

## Issue
{net} changes reference plane at a via without a GND via nearby.

## Recommendation
Add a GND stitching via next to this via.
