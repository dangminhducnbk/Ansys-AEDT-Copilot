<!-- No GND on any reference plane under a trace stretch -->
# Loss of reference

| Field | Value |
|---|---|
| id | loss_of_reference |
| findings | Loss of reference = Loss of reference |
| section | reference |
| not ok when | no GND on any reference plane over a stretch |
| thresholds | review.sample_step_mm, review.pad_exclusion_mm |
| limit key | review.sample_step_mm |
| code | yes |

## What
Same sampling as `sov`. A stretch where ALL its reference planes (above and below; the only one on an
outer layer) miss copper in a REAL gap (or hold another net's copper) → no return path there; ONE finding per stretch
listing the planes (032: no SOV twins for the same stretch). Spots inside a via clearance (void around via / pin
centres) are not a loss of reference: rule `via_clearance`.

## Why
no GND under the trace on either reference layer: the return path is lost (impedance, EMI).

## Fix
reroute over GND, or add GND copper under this segment.

## Discuss
Real gaps are NOT OK (user 2026-11-08: "Đây là lỗi nghiêm trọng"). Via clearances are not loss of reference (user
2026-11-11, feature 032). The engineer reads the report and decides whether to cut. Give the length and location;
never judge or rank the finding for them (4.0.0: OK / NOT OK only).

## Report
- Loss of reference: trace runs over a void in all its reference planes.

## Issue
{net} ({layer}) is routed over a void in all its reference planes ({planes}).

## Recommendation
Reroute over solid GND or add GND copper under this segment.
