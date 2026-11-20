# Feature Specification: No-GND end decision (user chooses, with image)

**Feature Branch**: `015-no-gnd-end-decision` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-09

**Status**: Clarified 2026-11-09

**Input**: Parent session, user go 2026-11-09 ("Đồng ý"): coded rule, minor 0.14.0. When an end has NO GND pin and a
rebuild would be needed, the tool must NOT decide: it stops, sends the user an image and asks a multiple-choice
question with every case the tool can do plus "other" (free-text instruction).

## Clarifications

### Session 2026-11-09 (user via parent session, "Làm theo bạn đề xuất")

- Q1: What does option 2 "use existing GND copper" build? → A: GND vias inside the body that land on existing GND
  copper of the placement layer become GND pins; no new copper. Offered only when such vias exist.
- Q2: How does the Excel flow ask? → A: propose detects the case (image + options in the propose output, warning in
  the Excel "warnings" column); the agent asks at GATE 2; `start_cut_batch` gets optional `gnd_handling`
  (JSON {channel: {refdes: option}}) + `user_approved_gnd`; refused without an answer; at CLI level the channel stops
  with an error. Excel format unchanged. Regression passes U26 = `gnd_plate_vias` → reference unchanged.
- Assumptions confirmed: non-BGA / TH ends only; ends with GND pins but far from a signal pin keep
  `no_gnd_near_signal`; unmapped "other" → end undecided, apply refused.
- Note: the Excel flow may be retired later (separate MAJOR feature) → keep the Excel part of 015 minimal.

## Problem

Board1 CPHY: U26 / U21 (QFN64P50_900x900, SMD) have 0 GND pins. The end check flags `no_gnd_near_signal`; with
`smd_rebuild` the cutter silently draws a GND rectangle on the placement layer bounding the GND vias inside the body
(+ via radius + `port.smd_gnd_plane_gap_mm`, shrunk away from signal pads) and turns those vias into GND pins
(U26 plate [120.13, 36.83, 125.82, 38.82] mm, U21 [84.93, 33.18, 86.82, 38.82] mm, 10 vias each). With no GND via
either, it only warns and continues. The Excel flow does the same with no question at all. The user wants to see the
area and choose every time.

| Path | Today | Target |
|---|---|---|
| Interface simulation (end check → Gate B → apply) | `no_gnd_near_signal`, options smd_rebuild / keep / stop; plate drawn silently | new rule `no_gnd_pin`: image + case-specific options; plate only after the user's choice (server flag) |
| Excel flow (propose → cut batch) | plate drawn silently, no question | the case is found before the cut; the user chooses (see Q2) |
| Re-cut "như lần trước" | old handling reused silently when still valid | image + previous answer shown again, user confirms |
| Design tools | no tool calls the SMD rebuild | unchanged (no gate needed); stated in the plan Kitchen check |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The engineer sees the area and chooses (Priority: P1)

An interface end (SMD IC or connector) has no GND pin. The end check stops that end, writes an image of the IC body
area and lists the options the tool can do for this case; the agent asks a multiple-choice question and never chooses.

**Why this priority**: the GND reference of a port changes S-parameters; the tool must not invent a reference silently.

**Independent Test**: offline — fake geometry (signal pads, GND vias, GND copper) gives the right option list per
case and an image file; apply without the choice is refused. AEDT (board1 copy): CPHY_U14_U26 stops at U26 with image
+ options; choosing option 1 gives the same plate coordinates and metrics as today's reference.

**Acceptance Scenarios**:

1. **Given** an SMD end with 0 GND pins and GND vias inside the body, **When** the end check runs, **Then** it returns
   rule `no_gnd_pin`, an image path and options: 1 GND rectangle bounding the vias (with its size), 3 keep component,
   4 stop interface, 5 other; option 2 only when GND copper exists on that layer inside the body area.
2. **Given** 0 GND pins and NO GND via in the body, **When** the end check runs, **Then** it also stops; options that
   need vias are left out with the reason shown.
3. **Given** no answer for that end, **When** apply is called, **Then** it is refused naming the end; no plate drawn.
4. **Given** option 1 on board1 U26, **When** apply runs, **Then** the plate is [120.13, 36.83, 125.82, 38.82] mm,
   10 vias become pins, ports / GND vias / planes equal the current reference.
5. **Given** option 5 "other" with text, **When** the agent can map it to an existing option, **Then** the mapped
   option is used and the text is stored; **When** it cannot, **Then** the agent says no utensil exists and the end
   is not applied (no ad-hoc script, Principle X).

---

### User Story 2 - Answer stored, shown again on re-cut (Priority: P1)

The answer per end (option, rectangle or copper used, the user's note) is stored in `user_settings.json`. A re-cut
"như lần trước" shows the image and the previous answer and waits for the user to confirm (no silent reuse).

**Independent Test**: offline — saved answer read back; re-cut handling compare marks the end `needs_confirm` (not
`kept`) and shows the previous answer.

---

### User Story 3 - Excel flow does not decide either (Priority: P2)

The Excel flow finds the case at propose (image + options, warning in the Excel) and the user chooses at GATE 2; the
answer goes to `start_cut_batch` (`gnd_handling` + `user_approved_gnd`). Kept minimal (Excel flow may be retired).

**Independent Test**: `tests/regression.py` on a board1 copy with option 1 for U26 → PASS, reference unchanged.

---

### User Story 4 - Report names the GND reference (Priority: P3)

Self-check / report lists per end the GND reference used: own GND pins / plate from vias (rect mm) / existing copper /
none (kept component).

## Edge Cases

- The rule applies to non-BGA ends (SMD ICs and connectors with `smd_rebuild`): BGA / through-hole rebuild never
  draws a plate. A connector with 0 GND pins gets the question instead of the team default.
- An end that has GND pins but some signal pin far from them keeps today's `no_gnd_near_signal` (unchanged).
- Found on board1 (2026-11-09): U26 / U21 DO have a GND pin on the board (pin 65, exposed pad 6.3 x 6.4 mm at the
  body centre) but it lies outside the cut extent, so the cut design has none. Propose (source board) therefore
  counts only GND pins / vias inside the cut extent and notes the GND pins lost by the cutout.
- The image is made without the AEDT GUI (PIL, from EDB geometry read in the end check session).
- The proposed rectangle in the image MUST equal the one apply would draw (same computation, one function).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The end check MUST detect a non-BGA end with 0 GND pins and return rule `no_gnd_pin` with measured
  values: GND vias in the body (count, positions), proposed rectangle (mm), existing GND copper on the placement layer
  inside the body area (area mm²), and an image path.
- **FR-002**: Options MUST be listed per case: `gnd_plate_vias` (only with GND vias), `gnd_existing_copper` (only when GND
  vias in the body land on existing GND copper: those vias become GND pins, no new copper), `keep_component`, `stop_interface`, `other` (free text);
  options left out carry the reason.
- **FR-003**: The image MUST show the body area on the placement layer: signal pads (red), GND vias (blue), proposed
  rectangle (dashed, size in mm), existing GND copper (if any), refdes, part, layer, scale.
- **FR-004**: The plate MUST only be drawn after the user's choice: server flag `user_approved_gnd` on the tools that
  can draw it (isim_apply; Excel flow per Q2); refused otherwise, naming the end.
- **FR-005**: The answer MUST be stored per end in `user_settings.json` (option, rectangle / copper used, note).
- **FR-006**: Re-cut MUST show the image and the previous answer again and require confirmation.
- **FR-007**: Self-check / report MUST name the GND reference used per end.
- **FR-008**: Guides (interface_sim, design_tools, workflow / verify for the Excel flow, kitchen if relevant) MUST tell
  the agent to show the image and the options as a multiple-choice question and never choose.
- **FR-009**: Option `gnd_plate_vias` MUST give the same geometry as today's `smd_rebuild` plate.

### Key Entities

- **No-GND end finding**: refdes, part, layer, body bbox, GND vias, proposed rectangle, GND copper, image, options.
- **GND decision**: refdes → {option, rect_mm | copper, note, decided_at}.

## Success Criteria *(mandatory)*

- **SC-001**: board1 copy: CPHY_U14_U26 stops at U26 (and CPHY_U21_J25 at U21) with an image and options; 0 plates
  drawn before the choice.
- **SC-002**: option 1 → plate coordinates and metrics equal the current reference; `tests/regression.py` PASS.
- **SC-003**: unit tests: option list per case (vias / copper / none), image file from fake geometry, gate refusal,
  stored answer, re-cut needs confirmation — all PASS.

## Assumptions

- Minor 0.14.0: new rule id, new options, new optional tool flag `user_approved_gnd`; existing tool names unchanged.
- `smd_rebuild` stays valid for ends WITH GND pins; for a 0-GND-pin end it is replaced by the explicit options.
- `other`: the free text is stored; the agent maps it to one listed option (stored as `mapped_to`) or reports that no
  utensil exists — then the end stays undecided and apply stays refused.
- Old requests (before 0.14.0) whose handling says `smd_rebuild` for a 0-GND-pin end: on re-cut they are shown as
  "previous answer: GND rectangle from vias (smd_rebuild)" and need confirmation.
