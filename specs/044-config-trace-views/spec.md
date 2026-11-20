# Feature Specification: Config page — traces of every signal pad in the top and 3D views, slider fill follows the thumb

**Feature Branch**: `main` (no branch; repo owner works on main) | **Created**: 2026-11-17

**Status**: Accepted (user 2026-11-17: "sửa 2 lỗi mà tôi nói ở trên")

**Input**: Two user reports on the 5.3.0 config page (screenshots):
1. Port position slider: "Cái vùng xanh không chuyển động cùng với con trỏ khi kéo."
2. J25 (BOARDA, via-in-pad connector on Bottom Layer): "Tôi chưa thấy trace được vẽ trên 3D để người dùng biết hướng
   trace đi vào."

## Context

- The slider reuses the style of the solder ball "Diameter" slider, whose blue fill follows a value the page sets on
  every move; the port slider never sets it, so the fill stays at 0.
- 5.3.0 (FR-008 of 041) draws only traces on the end's placement layer, in the top view only. A via-in-pad pad has no
  trace on that layer: the trace leaves through the via on an inner layer, so J25 shows no trace at all; the 3D view
  draws pads, solder balls and ports, never traces.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Slider fill follows the thumb (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the port position slider, **When** the user drags it or presses a quick button (0 / 50 / 100 %), **Then**
   the coloured part runs from the left end to the thumb at every position.
2. **Given** the page opens with a saved value (e.g. 28 %), **Then** the fill already reaches the thumb.

### User Story 2 - The user sees where each signal trace comes from (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an end whose signal pads hold a via (J25), **When** the config page is shown, **Then** the top view draws
   the signal traces that leave those vias on other layers, each layer in its own colour with a dashed line, and the
   legend names each layer ("Trace <layer>").
2. **Given** an end with traces on its placement layer (U26 QFN), **Then** these stay drawn as in 5.3.0 (solid).
3. **Given** the 3D view, **Then** placement-layer traces are drawn on the board surface and inner-layer traces dashed on
   a plane under the board, with a vertical line at each via from the pad down to that plane; rotating / zooming keeps
   them in place with the pads.
4. **Given** an end with no signal trace in its frame on any layer, **Then** nothing extra is drawn and no error.

### Edge Cases

- A via going to several inner layers with traces: each layer drawn (one colour per layer).
- Traces only partly inside the end frame: drawn as given (the view clips them).
- BGA ends: same rules (traces of the signal pins' vias / layer).
- Pages built before this release (data without the new trace list): drawn as in 5.3.0; a new `isim_config` brings the
  new data.

## Requirements *(mandatory)*

- **FR-001** Slider fill = position of the thumb (0–100 %) at load and on every change (drag, quick buttons).
- **FR-002** Page data per end: traces of the end's signal nets on the placement layer (as 5.3.0) AND on every other
  layer, when the trace touches a via that lies inside a signal pad of the end (or is that pad's pin padstack spanning
  the layer) and has a point inside the end frame; each with its layer name. Maximum count as 5.3.0 (400 per end).
- **FR-003** Top view: placement-layer traces solid (unchanged); other-layer traces dashed, thinner, one colour per
  layer from a fixed list; legend one entry per layer drawn.
- **FR-004** 3D view: placement-layer traces on the board surface; other-layer traces dashed on one plane under the
  board (symbolic depth, not the real layer height); vertical segment at the via from pad to that plane; colours =
  top view.
- **FR-005** Nothing else changes (port positions, saved values, validation, build).

## Success Criteria *(mandatory)*

- **SC-001** Browser, board1 copy request: slider at 0 / 28 / 50 / 100 % and the 3 quick buttons → fill ends at the
  thumb each time.
- **SC-002** BOARDA copy request, J25: top view and 3D view show the inner-layer traces of all 8 signal pads, legend
  names their layer(s); U14 / U26-type ends keep their 5.3.0 drawing.
- **SC-003** Unit tests: trace selection (placement layer, via in pad on another layer, via outside the pads ignored,
  arc markers dropped, limit), layer colour assignment, fill value set by the slider code.

## Assumptions

- "Hướng trace đi vào" = the direction in which each trace leaves the pad / via, seen from above; true layer depth in
  3D is not needed.
- Re-running `isim_config` on an existing request is acceptable to get the new data.
