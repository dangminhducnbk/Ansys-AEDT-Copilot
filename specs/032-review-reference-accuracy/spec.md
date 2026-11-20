# Feature Specification: Accurate reference findings and readable pictures

**Feature Branch**: `032-review-reference-accuracy` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-11

**Status**: Draft

**Input**: User description: "các vấn đề mà file review layout đã review chưa ổn. Cùng thảo luận để chỉnh lại cách
review. Khu vực mà tool đang report là void của via, không phải là vùng bất kỳ bị mất reference. Picture không thể
hiện được rõ vị trí mất reference, zoom in quá to và thông tin layer bên dưới đưa ra cũng không phân biệt được layer
nào. Report cùng 1 lỗi cho SERLINK_M2M_AC_TX_L2_N là Signal over void (SOV)"

Seen on: 2.9.0 review of SERLINK on a test1 copy (`layout_review_20261111_204829.html`), REF-01 = net
SERLINK_M2M_AC_TX_L2_N, channel SERLINK_U14_J8, Layer 3 from (126.119, 137.531) to (126.662, 138.630) mm, 1.55 mm.

## Problem

| # | What the report does | What is wrong (engineer) |
|---|---|---|
| P1 | Flags "Loss of reference" HIGH where the Layer 3 trace runs inside the clearance void (antipad) around a via on Layer 2 and Layer 4 | That void belongs to a via (breakout into the via), it is not an arbitrary hole in the plane; calling it loss of reference is wrong and stops the cut for nothing. All 12 HIGH of U14_J8 are of this kind (1.55 mm near J8 vias, 0.35 mm next to the AC-cap vias) |
| P2 | Same stretch reported 3 times: Loss of reference (HIGH) + SOV on Layer 2 (MEDIUM) + SOV on Layer 4 (MEDIUM) | One defect = one finding |
| P3 | Picture: zoomed so far that the via, the void outline and where the trace leaves the plane cannot be seen; the issue is a thin line + circle | Engineer cannot locate the problem |
| P4 | Picture: Layer 2 GND and Layer 4 GND drawn as two similar pale fills on top of each other; legend colours too close | Cannot tell which layer is missing copper where |

## Clarifications

### Session 2026-11-11

- Q1: How are via-clearance crossings reported? → A: own-net via clearance → not reported; other-net via clearance →
  new rule "Trace over via clearance", INFO, with via / net / void size.
- Q2: Picture layout? → A: one panel per reference plane, side by side, each with that layer's GND copper, the trace,
  the vias and the highlighted missing stretch.
- User review of the 032 reports (2026-11-11): "Gộp rồi release" → "Near plane edge" (rule `plane_edge`) follows
  the same one-stretch-one-finding rule: one finding per stretch listing every plane with its edge distance / limit,
  one Why / Fix (no Layer 2 block + Layer 4 block for the same stretch). → T008.
- Q3: Replace the 2026-11-08 rule "loss of reference stays HIGH even when grazing an antipad"? → A: yes, replaced by
  Q1 for via clearances; real gaps stay HIGH.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A via clearance is not a loss of reference (Priority: P1)

A trace that runs into the clearance void of a via (typically to reach that via, or passing a via of its own pair)
is not reported as loss of reference / SOV; a real hole or gap in the plane under the trace still is.

**Why this priority**: false HIGH findings stop the cut (025 gate) and destroy trust in the review.

**Independent Test**: test1 SERLINK_U14_J8: the 12 HIGH points of 2.9.0 are no longer HIGH loss of reference (they
become: own-net via clearance → not reported; other-net via clearance → INFO "Trace over via clearance", Q1 A); a synthetic trace over a real plane slot
(no via in the void) is still HIGH; board1 / PCIe results change only where the cause is a via clearance (listed).

**Acceptance Scenarios**:

1. **Given** a trace stretch whose missing reference copper is entirely inside the clearance void of one or more vias,
   **When** reviewed, **Then** it is not "Loss of reference" / "SOV"; it is handled per Q1, naming the via(s), their
   net and the void size.
2. **Given** a stretch over a void that contains no via (plane slot, split, cutout), **When** reviewed, **Then** it is
   reported as today (loss of reference HIGH / SOV MEDIUM).
3. **Given** a stretch partly in a via clearance and partly over a real gap, **When** reviewed, **Then** only the real
   gap part is reported, with its own length.

---

### User Story 2 - One defect, one finding (Priority: P1)

The same trace stretch is reported once, with the most severe classification and the per-layer detail inside it.

**Independent Test**: REF-01 situation (both reference planes missing on the same stretch) → exactly one finding
"Loss of reference" listing Layer 2 and Layer 4 as missing; no separate SOV lines for the same stretch.

**Acceptance Scenarios**:

1. **Given** both reference planes missing on a stretch, **When** reported, **Then** one "Loss of reference" finding
   (layers listed), no SOV for that stretch.
2. **Given** only one of two reference planes missing, **When** reported, **Then** one "SOV" finding naming that plane.
3. **Given** the counts in the summary, **When** compared with 2.9.0, **Then** the drop equals the removed duplicates
   (listed per channel).

---

### User Story 3 - Picture shows where and which layer (Priority: P1)

The engineer looks at the picture and sees the via(s), the void outline on each reference layer, the trace, and the
exact stretch without reference, and can tell the layers apart.

**Independent Test**: REF-01 picture: the J8 / AC-cap via, the void outline of Layer 2 and of Layer 4 and the missing
stretch are visible and distinguishable without reading the coordinates; checked by the user on the test1 report.

**Acceptance Scenarios**:

1. **Given** a reference finding, **When** drawn, **Then** the view shows the whole stretch plus context
   (the via(s) involved and a margin) and the stretch without reference is highlighted along its length (not only a
   circle).
2. **Given** two reference planes, **When** drawn, **Then** each plane is distinguishable: one picture panel PER reference plane side by side (e.g. "Layer 2 – GND" | "Layer 4 – GND"),
   each with that layer's GND copper + trace + vias + the highlighted stretch (Q2 A).
3. **Given** the legend, **When** read, **Then** every drawn layer has a clearly different style and its name.

---

### Edge Cases

- Via clearance of a via of ANOTHER net (trace passes an unrelated via's antipad): handled per Q1 (still a
  discontinuity, smaller than a plane slot).
- Clearance voids of several vias merged into one big void (pin field, connector, BGA): the void is "via clearance"
  only when every part of the missing stretch is within the clearance of some via; else the remainder is a real gap.
- Outer layer (one reference plane): loss of reference = SOV on that plane → one finding.
- Old review records / goldens: severities and counts change on purpose; review_check / pcie_check references are
  updated deliberately with a list of every changed point.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The reference rules MUST classify each missing-reference stretch as either via clearance (all missing
  copper inside clearance voids of vias) or real gap; only real gaps are "Loss of reference" / "SOV".
- **FR-002**: Via-clearance stretches: clearance of a via of the SAME net (trace entering its own via) → not
  reported; clearance of a via of ANOTHER net → new rule "Trace over via clearance", severity INFO, naming the
  via(s), net(s) and void size (Q1 A). It never stops a cut.
- **FR-003**: One stretch MUST give one finding: both planes missing → "Loss of reference" (layers listed); one plane
  missing → "SOV" (plane named). No double / triple reporting.
- **FR-004**: The previous user rule "loss of reference stays HIGH, also when the trace only grazes a via antipad"
  (2026-11-08) is REPLACED by FR-001 / FR-002 for via clearances (Q3 A, user 2026-11-11); real gaps stay HIGH.
- **FR-005**: Pictures of reference findings MUST show the full stretch + the via(s) involved + a margin, highlight the
  missing stretch along its length, and draw reference planes so each is distinguishable (Q2 A: one panel per reference plane); legend styles clearly
  different.
- **FR-006**: Rule steering files (`sov`, `loss_of_reference`, new rule if Q1 needs one) and the guide list MUST
  describe the new behaviour (031 layout).
- **FR-007**: Results MUST be re-checked on test1 SERLINK + PCIe and board1; every changed point listed (before →
  after, reason).

### Key Entities

- **Reference stretch**: net, layer, start / end, length, missing planes, cause (via clearance with via ids / net /
  void size, or real gap), severity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: test1 SERLINK_U14_J8: 0 HIGH caused by via clearances (12 today).
- **SC-002**: 0 stretches reported more than once in any report (board1, test1).
- **SC-003**: A real plane gap under a trace is still reported HIGH (synthetic / known case), 100 %.
- **SC-004**: The user can point to the missing-reference location on the REF-01 picture without the coordinates
  (user review).

## Assumptions

- Via clearance = the void around a via / pin pad on a reference plane (antipad), possibly merged with neighbours;
  measured from the board data, no new input.
- Signal-net own via exit is already partly excluded today (void ≤ 2 mm containing a same-net via); this feature
  generalises it (any via, merged voids) and makes it visible instead of silent, per Q1.
- Report language English; danger wording unchanged.
- Version: minor (review results change).
