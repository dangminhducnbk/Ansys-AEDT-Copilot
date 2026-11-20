# Implementation Plan: Accurate reference findings and readable pictures (032)

**Branch**: `main` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/reference.md](contracts/reference.md)

## Summary

`cut_board/review.check_reference` (shared by the review checks and the HTML report) classifies every sample of a
trace per reference plane: covered / via clearance (own net) / via clearance (other net) / other-net copper / gap,
then turns runs of the same per-sample label into ONE finding per stretch:

| Planes missing (gap or other-net copper) | Finding |
|---|---|
| all reference planes | Loss of reference (HIGH), `ref` lists the planes |
| one (of two) | SOV (gap) or Ref to other net (other-net copper) on that plane |
| none, but a plane is only missing in the clearance of another net's via | Trace over via clearance (INFO, new rule `via_clearance`) |
| none, own-net via clearance only | nothing |

Via clearance (data-driven, no new input): the uncovered point lies in a void of the plane that contains at least
one via / pin centre, and its distance to the convex hull of those centres ≤ half the void's smaller bbox side + 0.05 mm
(covers round antipads, oblong pair antipads, merged pin-field voids; a slot with a via at one end keeps its far part
as a real gap). Own vs other net = net of the nearest via in that void. This replaces the old silent "own antipad
≤ 2 mm" exclusion (Q3 A: the 2026-11-08 "stays HIGH on antipads" rule is replaced).

Pictures of reference findings: one panel per reference plane side by side (Q2 A), each with that plane's GND copper
(own colour, finer grid), other-net copper, the trace layer, signal / GND vias, the clearance via(s) ringed and the
missing stretch highlighted along its samples; the view covers the stretch + involved vias + `review.zoom_margin_mm`.

## Decided by agent

| Decision | Why |
|---|---|
| Clearance radius = half the smaller side of the void bbox (+0.05 mm), distance to the hull of the via centres in the void | REF-01 void 4.2 × 2.2 mm around the J8 pin pair (2 mm apart): the trace start is 1.41 mm from its pin, outside a per-pin circle but inside the pair stadium |
| Outer layer (one reference): missing = all → Loss of reference only (no SOV twin) | FR-003 |
| Finding values for LoR / SOV / Ref to other net keep their text; INFO via-clearance value names via count, nets, planes, void size | readable diffs |
| `review.pad_exclusion_mm` exclusion kept | unchanged behaviour near own pads |
| Panels inline-styled (no CSS change) | golden 028 report unchanged |

## Files

| File | Change |
|---|---|
| `cut_board/review.py` | `Board.insts_in(window)` (all padstack instances x, y, net, cached); `check_reference` rewritten (classification, one finding per stretch, `trace_pts`, `vias` on findings); `svg_ref_panels`; picture loop uses panels for reference findings |
| `review_checks/_refcheck.py` | `via_clearance` added to the shared measurement; `review_checks/via_clearance.py` + `review_rules/via_clearance.md` (new rule, INFO, section reference) |
| `review_rules/sov.md`, `loss_of_reference.md` | new behaviour; 2026-11-08 rule replaced |
| `cut_board/review.py` BUILTIN_CHECKS, `review_checks.ALIASES` (`reference` + via_clearance) | |
| guide list (generated) | |
| tests | unit: classification on fake copper (own clearance silent, other-net INFO, real slot HIGH, slot with via at one end → remainder gap, one finding per stretch, outer layer), panels SVG; references updated deliberately (pcie_check, review_check golden comparison) |

## Constitution Check (2.0.1)

| Principle | Status |
|---|---|
| I Gates: fewer false HIGH; real gaps still HIGH | PASS |
| V Regression: every changed point listed per channel; references updated deliberately | PASS |
| X Catalog: no tool change | PASS |
