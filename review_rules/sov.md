<!-- Trace runs over a void / split of one reference plane -->
# Signal over void (SOV)

| Field | Value |
|---|---|
| id | sov |
| findings | SOV = Signal over void (SOV) |
| section | reference |
| not ok when | a reference plane has no copper under the trace |
| thresholds | review.sample_step_mm, review.pad_exclusion_mm |
| limit key | review.sample_step_mm |
| code | yes |

## What
Samples along every signal trace (centre + both edges, every `review.sample_step_mm`). A sample where ONE of
its two reference planes (nearest plane above / below) has no copper in a REAL gap (slot, split, cutout) while the other
plane is present → SOV on that plane; consecutive samples form ONE finding with its length (032: one finding per
stretch). All reference planes missing → `loss_of_reference` instead (never both). Not counted: samples within
`review.pad_exclusion_mm` of a same-net pad / via centre, and spots inside a VIA CLEARANCE (void around via / pin
centres, rule `via_clearance`: own-net via silent, other-net via = OK data row). Copper of ANOTHER net at the spot →
`ref_other_net`.

## Why
the trace crosses a void of its reference plane: impedance jump and a detour of the return current.

## Fix
keep the trace over solid GND on {planes} (move the trace, or fill / shrink the void).

## Discuss
Give net, layer, reference plane, uncovered length and location. Short crossings (< 0.5 mm) near
break-out areas are often accepted: ask the engineer instead of judging. Never mark it dismissed yourself.

## Report
- Signal over void: trace runs over a void in one reference plane.

## Issue
{net} ({layer}) is routed over a void in {planes}.

## Recommendation
Keep the trace over solid GND on {planes}.
