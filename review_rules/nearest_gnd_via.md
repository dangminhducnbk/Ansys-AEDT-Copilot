<!-- Signal via without a GND via / pin close by -->
# Nearest GND via

| Field | Value |
|---|---|
| id | nearest_gnd_via |
| findings | Nearest GND via = GND via too far from signal via |
| section | via |
| not ok when | the distance > the limit |
| thresholds | review.gnd_via_flag_mm |
| limit key | review.gnd_via_flag_mm |
| code | yes |

## What
Per signal via stack: nearest GND via or GND pin, its (x, y) and the centre distance; flagged when farther
than `review.gnd_via_flag_mm`.

## Why
the signal via has no close GND return path: longer return loop, more crosstalk and radiation.

## Fix
add a GND via within {lim:g} mm of this via.

## Discuss
Give the distance next to the limit and where the nearest GND via is.

## Report
- Nearest GND via: GND via too far from a signal via.

## Issue
Signal via of {net} has no GND via nearby.

## Recommendation
Add a GND via next to this via.
