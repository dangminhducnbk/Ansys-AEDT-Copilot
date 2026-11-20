# Implementation Plan: frame style per issue type (043)

**Branch**: `main` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md) | Release 5.4.1 (patch: report drawing)

## Summary

- `cut_board/review.py`: `FRAME_STYLES` {check: (colour, dash factors (on, off) × base dash, label)} for
  Loss of reference (pink, dashed 1 / 0.6 — the 2.11 look), Near plane edge (orange, dotted 0.25 / 0.45),
  SOV (purple, dash-dot 1 / 0.35 / 0.2 / 0.35), Ref to other net (brown, long dash 2 / 0.6), Trace over via clearance
  (teal, dashed 0.6 / 0.6); `FRAME_FALLBACK` list for other names; `frame_style(check, seen)` (pure).
- `_fault_rect(pts, pad, sw, dash, colour=FAULT_COLOR, pattern=(1, 0.6))` — default call = old output.
- `svg_ref_panels`: style per check in order of first appearance in `items`; k-th style padded `+ k × 1.5 × sw`;
  legend: one entry per drawn check "<check> (<pattern> frame)" in place of "stretch without reference (dashed frame)".
- Nothing else changes (points, counts, other pictures).

## Constitution Check

I–IX unaffected (report drawing only, no gate / data change). Golden `post033_report.html` changes only where a
reference picture is drawn: deliberate, refreshed with a diff check that only `<rect ... stroke=` frame lines and the
legend entry change.

## Tests

`tests/unit/test_frame_styles_043.py`: style per known check, fallback order, padding increments, legend entries for
1 / 2 checks, same check twice = one legend entry; old default `_fault_rect` output byte-identical.
Copy: BOARDA review re-rendered (snapshot) → point 1.3 picture has `#ff1493` + `#ff8c00` frames (SC-001), browser look.
