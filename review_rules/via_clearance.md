<!-- Trace runs over the clearance void (antipad) of another net's via -->
# Trace over via clearance

| Field | Value |
|---|---|
| id | via_clearance |
| findings | Trace over via clearance = Trace over the clearance of another net's via |
| section | reference |
| not ok when | never: OK, kept as data (trace over another net's via clearance) |
| thresholds | review.sample_step_mm, review.pad_exclusion_mm |
| limit key | none |
| code | yes |

## What
Same sampling as `sov`. A spot of a reference plane without copper is a VIA CLEARANCE when it lies in a void that
holds at least one via / pin centre and is within the hull of those centres + half the void's short side (round
antipads, oblong pair antipads, merged pin-field voids). The nearest via of that void decides: same net as the trace
(the trace entering its own via) → not reported; another net (e.g. the partner of the pair, an unrelated via) → this
OK data row, with the via count, their nets, the planes and the void size. A stretch where a plane is missing
outside any via clearance is a real gap (`sov` / `loss_of_reference`), not this rule.

## Why
the trace passes over the clearance void of another net's via: a short reference discontinuity (small, but it adds up on long via fields).

## Fix
route around the via clearance if the interface is sensitive, or accept it (normal in pin / via fields).

## Discuss
Always OK (data). Mention only when asked, with the via nets and stretch length.
Replaces the 2026-11-08 rule that counted a trace grazing an antipad as loss of reference (user 2026-11-11,
feature 032): via clearances are no longer loss of reference.

## Report
- Via clearance: trace runs over the clearance of another net's via.

## Issue
{net} ({layer}) crosses the clearance of another net's via on {planes}.

## Recommendation
Route around the via clearance if the interface is sensitive.
