# Feature Specification: GND pin cleanup on SMD / connector ends

**Feature Branch**: `021-smd-gnd-pin-cleanup` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-09

**Status**: Clarified

**Input**: User description: "tôi thấy hiện tại GND pin J25 chưa được cleanup, không cần nhiều pin GND như vậy, có thể
xóa bớt. GND via bao vòng quanh signal pin là đủ rồi" — seen on the 2.0.0 test cut of PCIE_U14_J25 (copy of
`test/test1`, request 20261109_230606): J25 kept 64 GND pins for 8 signal pins, U14 (BGA) kept only 28.

## Clarifications

### Session 2026-11-10 (user "okay" to the recommended answers, relayed by the parent session)

- Q1 → A: new template row `cleanup.smd_gnd_pin_keep_dist_mm`, unit mm, team default 1.6 (same as
  `cleanup.bga_gnd_pin_keep_dist_mm`), scope channel, shown at Gate B (cut group, like the BGA row).
- Q2 → A: the rule applies to every rebuilt SMD / SMD via-in-pad / connector end (`smd_rebuild` path). Ends with
  `keep_component` are not rebuilt and are not pruned.
- Q3 → B: a re-cut of an older run applies the new rule; the change is recorded as a default change in
  `defaults_history` so the re-cut diff shows it.
- Base 2.2.0 includes 022: the end GND rule guarantees ≥ 1 end GND pin / pad fully inside the cut extent. Pruning
  MUST NEVER remove that pin / kept pad, a plate or existing-copper reference (FR-003), nor leave a signal pin
  without its nearest GND pin (FR-004).

- Fix (user "Đồng ý cả 3" 2026-11-10, after the first AEDT run): distance signal pin → GND pin is measured from the
  signal pin centre to the GND pad EDGE (pad bounding box; 0 when overlapping), for the keep test and the "no GND pin
  within" warning, so an exposed pad (U26 / U21 pin 65, 6.3 mm) next to the signal pins gives no false warning. BGA
  rule unchanged (centre to centre).

- Rule (user "Thêm luật trước" 2026-11-10: "Thực tế board chạy nếu chỉ có 1 pin GND thì pin này chính là đường hồi
  của chip rồi"): an end with exactly ONE own GND pin / pad keeps it (as before) and gets NO "no GND pin within the
  keep distance" warning, whatever the distance; the report shows an info line instead ("U26: GND duy nhất pin 65,
  đã giữ"). An end with several own GND pins keeps the warning. Counted on the own GND pins of the end at cleanup
  (source board pins of the end inside the cut; 022 guarantees the end keeps ≥ 1).

## Problem

| End type | GND pins after cut today |
|---|---|
| BGA / through-hole | Only GND pins within `cleanup.bga_gnd_pin_keep_dist_mm` (1.6 mm) of a signal pin are kept (U14: 28) |
| SMD / SMD via-in-pad / connector (`smd_rebuild`) | ALL own GND pins are kept (J25: 64 of 72 pins) |

GND pins far from the signal pins add mesh and ports' reference spread without changing the result the engineer wants:
the GND pins / vias that ring each signal pin carry the return current.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connector end keeps only the GND ring around signal pins (Priority: P1)

The engineer cuts an interface whose end is a connector or SMD part with many GND pins. After apply, the end keeps the
GND pins around its signal pins only; far GND pins (and the vias that are those pins) are removed.

**Why this priority**: this is the request; it makes connector ends as lean as BGA ends.

**Independent Test**: re-cut PCIE_U14_J25 on a copy of test1: J25 keeps only GND pins near its 8 signal pins (far
fewer than 64); every signal pin still has its nearest GND pins (0.8 mm today); 16 ports = expected; self-check OK.

**Acceptance Scenarios**:

1. **Given** an SMD / via-in-pad / connector end with own GND pins, **When** apply runs, **Then** GND pins farther
   than the keep distance from every signal pin of that end are removed, the others are kept.
2. **Given** the result, **When** the self-check runs, **Then** each signal pin still has ≥ 1 GND pin within the keep
   distance and the report states GND pins before → after per end.
3. **Given** an end whose GND reference was chosen by the user (015 / 019: plate vias, existing copper, kept exposed
   pad), **When** apply runs, **Then** those GND pins are never removed.

---

### User Story 2 - Engineer sees and can change the rule (Priority: P2)

The keep distance is a settings row shown at Gate B like the BGA row; the engineer may change it per interface.

**Why this priority**: boards differ in pin pitch; one fixed number does not fit all connectors.

**Independent Test**: settings table of PCIE_U14_J25 shows the new row with its team default; a changed value is
used and stored in `user_settings.json`.

**Acceptance Scenarios**:

1. **Given** the settings table, **When** it is shown, **Then** the SMD / connector GND pin keep distance row is there
   with its default and unit mm.
2. **Given** an earlier run made before this feature, **When** it is re-cut "như lần trước", **Then** the result
   follows the new rule, and the settings table lists the new row as a default change (Q3 → B).

---

### Edge Cases

- End with no signal pin left after cut: no GND pin is removed (nothing to measure from); warning.
- Exposed GND pad (019 `gnd_keep_pad`): always kept, whatever its distance (pad centre may be far from signal pins).
- Plate vias turned into GND pins (015 `gnd_plate_vias`) and vias on existing copper (`gnd_existing_copper`): kept.
- `keep_component` handling: component not rebuilt; its GND pins are not pruned (Q2 → A).
- End enlarged by the 022 end GND rule: the GND pin / pad gained (`end_gnd.gnd_pins_gained`, `gnd_pin_inside`) is
  always kept.
- BGA / through-hole ends: unchanged (existing rule and value).
- Board1 CPHY ends (2.1.0+: U26 / U21 keep exposed pad 65 = their only GND pin, via the 022 rule): unchanged;
  `tests/regression.py` / `tests/isim_check.py` references (2.1.0) unchanged.
- Signal pin with no GND pin inside the keep distance even before cleanup: keep its nearest GND pin(s) anyway and warn,
  so no signal pin loses its reference.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Apply MUST remove own GND pins of an SMD / via-in-pad / connector end that are farther than the keep
  distance from every signal pin of that end, for every rebuilt end of these types (Q2 → A; not `keep_component`).
- **FR-002**: The keep distance MUST be a template row (Principle III), unit mm, team default
  1.6 mm (`cleanup.smd_gnd_pin_keep_dist_mm`, Q1 → A), shown at Gate B, changeable per interface, stored in
  `user_settings.json`.
- **FR-003**: GND pins that are the user's chosen GND reference (plate vias, existing-copper vias, kept exposed pad)
  or the GND pin / pad kept by the 022 end GND rule MUST NOT be removed.
- **FR-004**: Every signal pin MUST keep at least its nearest GND pin; if none is inside the keep distance, the nearest
  is kept and a warning names the pin.
- **FR-005**: The rebuilt component's pin count MUST equal signal pins + kept GND pins (existing rebuild check).
- **FR-006**: Apply metrics / self-check MUST report per end: GND pins before → after and the keep distance used.
- **FR-007**: The same rule MUST apply in `design_cleanup` (design tools) when it cleans an end of this type.
- **FR-008**: BGA / through-hole behaviour and results without such ends MUST NOT change (`tests/regression.py`,
  `tests/isim_check.py` PASS, references unchanged).
- **FR-009**: The `interface_sim` guide (verification checklist item 4 / 4c) MUST describe the new rule; the PCIe check
  script reference MUST be updated with the new J25 pin count.

### Key Entities

- **End GND pin set**: per end, GND pins before cleanup, kept, removed, reason kept (near signal / user reference /
  nearest fallback).
- **Keep distance setting**: key, unit mm, default, source (team default / engineer / previous run).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: PCIE_U14_J25 on a test1 copy: J25 GND pins drop from 64 to only those near the 8 signal pins; 16 ports
  = expected; self-check OK; max pin shift unchanged (0 mm).
- **SC-002**: 100 % of signal pins on pruned ends keep ≥ 1 GND pin within the keep distance (or the warned nearest).
- **SC-003**: Board1 regression and isim check PASS with unchanged references.
- **SC-004**: The engineer sees GND pins before → after per end in the apply report without opening AEDT.

## Assumptions

- "GND via bao vòng quanh signal pin" = the GND pins / vias nearest each signal pin (the ring at one pin pitch);
  distance = signal pin centre to GND pad edge (fix 2026-11-10; the BGA rule stays centre to centre).
- Vias that are not pins keep their existing cleanup rules (`cleanup.gnd_via_keep_dist_mm` etc.).
- Test board: copies only (test1 for J25, board1 for regression); originals never touched.
- Version: coded rule → minor (proposed 2.3.0, release decided by the user); restart Claude (guide changes).
- Re-cut (Q3 → B): `defaults_history` entry for the new key (absent before → 1.6) so old runs show it.
