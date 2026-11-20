# Feature Specification: Port location honoured for every SMD end

**Feature Branch**: `main` (no branch; repo owner works on main)

**Created**: 2026-11-16

**Status**: Accepted (user 2026-11-16: "tổng hợp với đề xuất 039 và 041 để implement 1 lần"); FR-001..006 released
in 5.2.0. Extension 2026-11-16 (clarify): port slider FR-007 + traces on the page FR-008, SC-005 — not implemented.

**Input**: Bug report `D:\data\client_boarda\for_ai_testing\bug_port_location_J25.md` (test session,
5.0.0): J25 (connector, via-in-pad pads) set to `port_location = "end"` in config.html; the merged design has all 8
ports at the pad centre. Self-check OK.

## Context

Cause (confirmed in code and in the run log `J25: 0 pin dời về đầu pad`):

- The pin plan of an SMD end returns "pin not moved" for a pad with a via inside, and for a pad with no trace on its
  layer, before the user's `port_location` is considered. So "end" and "centre" give the same result there.
- The config page preview draws the port at the pad end (body side) for those pads: preview and build disagree.
- The self-check does not compare the port position with the choice.
- The J25 solder ball WAS applied (log: Ø0.475 mm, 0.20 mm); `ends.json` `[0, 0]` is the source board value. Not a bug.

## Clarifications

### Session 2026-11-16

- Q: Lựa chọn port cho pad không tròn gồm những vị trí nào? → A: 3 lựa chọn theo thân linh kiện: Tâm pad (`centre`) /
  Đầu pad phía thân (`end`, giữ tên cũ) / Đầu pad phía ngoài, xa thân (`end_outer`, mới). (Thay bằng câu sau.)
- Q: (user đổi ý) Vị trí port trên pad không tròn chọn thế nào? → A: Thanh trượt dọc trục dài của pad. Port tròn
  Ø = bề rộng pad; tâm port đi từ W/2 đến L − W/2 (vd. pad 10 × 2 mm: 1 → 9 mm). Hai đầu thanh = phía thân / phía
  ngoài; giữa = tâm pad. Câu hỏi "theo trace hay theo thân" bỏ: hướng luôn theo thân linh kiện khi có lựa chọn.
- Q: Thanh trượt tính theo đơn vị nào, áp cho pad nào? → A: Một thanh mỗi đầu linh kiện, đơn vị %: 0 % = sát đầu
  phía thân (W/2), 50 % = tâm, 100 % = sát đầu phía ngoài (L − W/2); cùng % cho mọi pad tín hiệu của đầu (mẫu
  đã duyệt). Thêm (user): trang config vẽ trace nối vào từng pad để thấy trace tiếp cận từ hướng nào.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - "Pad end" moves the port on via-in-pad pads (Priority: P1)

The user sets an SMD / connector end with via-in-pad pads to "Pad end (body side)". The built design has every
signal port of that end at the pad end on the body side.

**Independent Test**: re-cut PCIE_U14_J25 of the BOARDA board (copy) with J25 = end: 8 J25 pins moved, shift > 0 and
≤ pad length; self-check OK.

**Acceptance Scenarios**:

1. **Given** J25 = "end" and its pads hold a via, **When** the design is built, **Then** each signal pin of J25 is at
   the pad end nearest the component body centre (along the pad's long axis), the old pad copper stays, the via stays.
2. **Given** a pad with a trace leaving on its layer, **When** "end", **Then** the end opposite the trace (as before).

### User Story 2 - "Pad centre" means the pad centre (Priority: P1)

**Acceptance Scenarios**:

1. **Given** "centre", **When** built, **Then** no signal pin of the end moves (port at the pad centre = pin position;
   for via-in-pad pads the via is NOT the port position). The config page says "Pad centre (pin position)".

### User Story 3 - Mismatch is reported, never silent (Priority: P1)

**Acceptance Scenarios**:

1. **Given** "end" on a pad where no direction can be found (square / round pad, pad on the body centre line),
   **When** built, **Then** that pin stays at the centre, a warning names the pin and the reason, and the self-check
   fails with a "port location" line.
2. **Given** any built design, **Then** `result.json` holds per end: requested location, pins moved / total, pins not
   moved with reason; the self-check compares the requested location with the pin positions read back from the
   saved design (pin vs. source pad centre).

### Edge Cases

- BGA / through-hole ends: always centre (unchanged, page has no choice).
- End kept as is (`keep_component`): no rebuild, location not applied; reported as "component kept".
- Requests and step tools without a per-end choice (no `component.model` entry for the end): the old behaviour stays
  (pins with a trace → end; via-in-pad / no-trace pins → centre). Old cut results do not change.
- Config page default for an end whose signal pads have no trace exit (via-in-pad): "centre" (= what the tool built
  before). The user picks "end" to move them.

## Requirements *(mandatory)*

- **FR-001** One function computes the pad-end position of a signal pin: trace exit on the pad layer → opposite end;
  no trace exit → end towards the component body centre along the long axis; no long axis or no side → no position +
  reason. The build and the config page preview use it (the page gets the positions from the tool, not its own math).
- **FR-002** Build: per-end choice `end` → every signal pin with a position moves there; `centre` → no pin moves.
  No per-end choice → old behaviour (FR edge case).
- **FR-003** Rebuild report per end in `result.json` / metrics `port_location`: {requested, explicit, pins, moved,
  not_moved [{pin, reason}]}.
- **FR-004** Self-check item "<refdes> port location": read back each signal pin, distance to its source pad centre
  (> 1 µm = moved). Explicit `end` → all moved; explicit `centre` → none moved; else not checked. Mismatch →
  self-check not OK.
- **FR-005** Config page: per-pin port position from the tool data; label "Pad centre (pin position)"; default
  "centre" for an end with via-in-pad / no-trace signal pads; note on such ends ("Via in pad: …").
- **FR-007** Port position slider for non-round pads: ONE slider per end, value 0–100 % (step 1 %). The port
  (circle Ø = pad width W) moves along each pad's long axis; its centre = W/2 + p × (L − W) measured from the
  body-side end of that pad (pad 10 × 2 mm: 0 % → 1 mm, 100 % → 9 mm; pad 6 × 2 mm: 0 % → 1 mm, 100 % → 5 mm), the
  same % for every signal pad of the end. 0 % = old `end`, 50 % = `centre`, 100 % = pad end away from the body.
  Direction = towards the component body centre for every pad when the user sets a value (the trace rule stays only
  without a choice). Page shows the % and, per pad, the offset in mm and mil (the config page has no unit switch). Build moves each
  signal pin there; report (FR-003) holds the requested % and per-pin offsets; self-check (FR-004) compares the
  read-back pin offset with the requested one (± 1 µm). Pads with L − W < 1 µm (round / square): no slider, centre.
  Old saved values map: `end` → 0 %, `centre` → 50 %. Default: 0 % for an end whose signal pads have a trace exit,
  50 % for via-in-pad / no-trace ends (= what the tool built before).
- **FR-008** Config page end picture draws, for each signal pad, the trace segments attached to the pad on its layer
  (trimmed to the picture), so the user sees from which side the trace reaches the pad.
- **FR-006** Unchanged: solder ball, BGA ends, GND via selection under the body (it keeps using the trace-direction plan).

## Success Criteria *(mandatory)*

- **SC-001** BOARDA PCIE_U14_J25 copy, J25 = end: 8 / 8 J25 signal pins moved, self-check OK, ports 16.
- **SC-002** Same with J25 = centre: 0 moved, self-check OK.
- **SC-003** board1 regression (no per-end choice) and pcie_check: numbers unchanged.
- **SC-005** (slider) BOARDA J25 copy at 0 / 50 / 100 %: every J25 signal pin read back at the requested offset
  (± 1 µm), self-check OK; config page shows the traces attached to each pad and the port at the slider position.
- **SC-004** Unit tests: plan function (trace / via-in-pad / square pad), self-check item, page default.

## Assumptions

- The pad end towards the body centre is the contact side of the component lead (true for the connectors and QFN /
  SOIC parts seen so far).
- The merged design of the bug run stays untouched as the reference.
