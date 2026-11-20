# Feature Specification: One frame style per issue type in review reference pictures

**Feature Branch**: `main` | **Created**: 2026-11-17 | **Status**: Accepted (user 2026-11-17: "B: khung khác kiểu")

**Input**: User screenshot (BOARDA review, point 1.3 PCIE_HSA2HSB_L1_N): "File review layout bị khoanh 2 lần".

## Context

A review point groups the NOT OK findings of one net at one location. The reference pictures (one panel per GND plane)
draw one pink dashed frame per finding. Point 1.3 holds "Loss of reference" (0.6 mm stretch) and "Near plane edge"
(1.4 mm, 2 stretches): two identical-looking frames nested in each other, read as "circled twice".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Each issue type has its own frame (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a point with Loss of reference + Near plane edge, **When** the report is drawn, **Then** each panel shows
   two frames of different colour AND line pattern, and the legend under the picture names each frame with its issue.
2. **Given** a point with one issue, **Then** one frame, legend names that issue (no other frame entries).
3. **Given** two findings of the same issue in one point, **Then** same style for both.
4. **Given** two frames with the same extent, **Then** both stay visible (the second is drawn slightly outside).

### Edge Cases

- Unknown / personal rule names: styles from a fixed fallback list, in order of first appearance.
- Pictures of other sections (vias, stubs: ring marks) and rule pictures (serpentine): unchanged.

## Requirements *(mandatory)*

- **FR-001** Fixed styles: Loss of reference = pink #ff1493 dashed (unchanged); Near plane edge = orange #ff8c00
  dotted; SOV = purple #8e44ad dash-dot; Ref to other net = brown #a0522d long dash; others = fallback list.
- **FR-002** Legend: one entry per issue type drawn in the picture ("<issue> (frame)"), replacing the single
  "stretch without reference (dashed frame)" entry.
- **FR-003** Frames of the 2nd, 3rd… issue type are padded by one line width more than the previous one.
- **FR-004** Counts, points, issue lines, HTML of other sections: unchanged.

## Success Criteria *(mandatory)*

- **SC-001** BOARDA review (copy): point 1.3 picture = 1 pink dashed + 1 orange dotted frame per panel, legend lists both.
- **SC-002** Unit tests: style per check, legend entries, padding; report goldens changed only in the reference pictures.

## Assumptions

- The legend swatch shows the colour; the line pattern is named in the label ("dashed", "dotted"...).
