# Feature Specification: No-GND end — keep the exposed GND pad

**Feature Branch**: `019-no-gnd-keep-exposed-pad` (work stays on `main`)

**Created**: 2026-11-09

**Status**: Done 0.15.0 (clarified 2026-11-09: Q1 A, Q2 A, Q3 A)

**Input**: Parent session, user go 2026-11-09 (ROADMAP 019): add an option to the 015 no-GND end question: extend the
cut extent so the end keeps its exposed GND pad. With the pad kept the component has a GND pin, the port reference
uses it, no plate is needed. Offer it only when the end really has a GND pin outside the extent; the image shows the
pad and the extended extent.

## Problem

| Fact (board1 copy, read only) | U26 | U21 |
|---|---|---|
| Part | QFN64P50_900x900_H80_T630 (Top Layer) | same |
| GND pin | 65 = exposed pad 6.3 × 6.3 mm at the body centre | same |
| Pad inside the cut extent | 35 % (centre outside → pin removed by the cut) | outside |
| GND vias in the pad | 25 (5 × 5, Top → Bottom) | 25 |
| Other-net copper ≤ 0.1 mm from the pad | none | none |

Today (0.14.0) the cut drops pin 65, the end check sees 0 GND pins and asks: plate / existing copper / keep / stop.
The real board has a large GND pad under the IC; keeping it is closer to the hardware than a drawn plate.

## Clarifications

### Session 2026-11-09 (user via parent session: "A A A")

- Q1 → **A**: extended extent = today's extent ∪ (each kept GND pad + margin). Margin = new template row
  `interface_sim.keep_pad_margin_mm` = 0.5 mm. GND vias inside the pad come with it.
- Q2 → **A**: interface simulation + design end check only. Excel flow unchanged (propose asks the 015 questions).
- Q3 → **A**: offer the option even when other nets lie in the extension; the image and the question name those nets
  (the cut keeps only channel + reference nets, so they do not enter the design).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Option "keep exposed pad" offered only when it exists (P1)
For a non-BGA / TH end with 0 GND pins inside the cut extent but ≥ 1 GND pin of the component outside it (on the
source board), the question lists a new option `gnd_keep_pad` "Extend the cut extent to keep the GND pad(s) <pins>
(<size>)". Not offered (with reason in `omitted`) when the component has no GND pin at all.
**Independent Test**: board1 copy U26 / U21 → option offered with pin 65, 6.3 × 6.3 mm; an end without GND pins on the
source board → option omitted with reason.

### User Story 2 - Image shows pad + extended extent (P1)
The 015 image adds: the GND pad(s) outside the cut (outlined), today's extent edge and the extended extent edge, and
the GND vias in the pad.

### User Story 3 - Cut with the extended extent (P1)
Choosing `gnd_keep_pad` → the interface is cut again with extent = today's extent ∪ (pad + 0.5 mm). The end keeps its
GND pin; the SMD rebuild uses it as for any end with own GND pins (no plate); ports refer to it; self-check
`gnd_reference = own_pins (kept pad)`. Other options give results identical to 0.14.0 (option 1 plate identical).
Other-net copper / pins inside the extension: option still offered; image + question list those nets.
**Independent Test**: board1 copy CPHY_U14_U26 with U26 = `gnd_keep_pad` → U26 has pin 65, 0 plate, ports reference
GND, self-check OK; with `gnd_plate_vias` → identical to 0.14.0 reference; `regression.py` PASS.

### User Story 4 - Excel flow
Not changed: `propose` keeps the 015 questions; `gnd_keep_pad` is not offered there (017 retires Excel).

## Requirements *(mandatory)*

- **FR-001**: Facts (source board, read only): GND pins of the end outside the cut extent (pin, pad bbox, size,
  layer), GND vias inside each pad, the extended extent polygon.
- **FR-002**: Option `gnd_keep_pad` only when FR-001 finds ≥ 1 pad; else in `omitted` with a reason.
- **FR-003**: Image (015 renderer): pad outline, current extent, extended extent, vias in pad.
- **FR-004**: Apply with `gnd_keep_pad` re-cuts with the extended extent (stage1 stores both extents + the choice);
  the rebuild sees own GND pins; metrics `gnd_reference` = own pins (kept pad).
- **FR-005**: Gate and storage as 015 (`user_approved_gnd`, `gnd_decisions`, re-cut asks to confirm).
- **FR-006**: Other options unchanged; option 1 (plate) results identical; `regression.py` PASS.

## Success Criteria *(mandatory)*

- **SC-001**: board1 copy: U26 and U21 questions list `gnd_keep_pad` with pin 65, 6.3 × 6.3 mm, 25 vias.
- **SC-002**: `gnd_keep_pad` on CPHY_U14_U26 → U26 has its GND pin in the cut design, no plate, self-check OK.
- **SC-003**: plate option + `regression.py`: identical to 0.14.0.
- **SC-004**: unit tests for facts / options / extent union / image PASS.

## Assumptions

- The cut keeps only the channel nets + reference nets (today's cutout); other nets in the extension are not kept.
- AEDT checks run on board1 copies only; no push.
