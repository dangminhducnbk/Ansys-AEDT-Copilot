# Feature Specification: Layout review report redesign (tabs, OK / NOT OK, routing view, serpentine)

**Feature Branch**: `033-review-report-redesign` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "đọc tóm tắt này và phân task cho subsession làm nhé." Summary agreed with the user
(2026-11-11/12, SERLINK mock session): `mock/report_redesign_summary.md` (copied into this folder). Visual reference:
`D:\work\project\tool\ansys_aedt_copilot\autocut\mock\SERLINK_short_mock.html` (git-ignored); mock scripts in
`mock/*.py` are form references only (monkey-patches; real code follows the repo architecture). User asleep: "xong
plan cứ triển khai luôn, khỏi hỏi tôi" → open points decided by agent (see Clarifications).

## Problem

The 2.10.0 review HTML (026 template + 032 pictures) still reads like a measurement dump: severity labels
HIGH / MEDIUM / INFO, a long "Reference data" part, all channels in one page, no view of how a pair is routed, and
pair-gap false findings where the gap is a length-matching serpentine. The engineer wants a short pass / fail report
per connection.

## Clarifications

### Session 2026-11-12 (agreed with the user in the mock session; summary §1–§5)

All items of summary §1–§5 are decisions of the user, not open questions.

### Session 2026-11-12 (summary §6 open points — decided by agent, user asleep)

| # | Open point | Decision (agent) |
|---|---|---|
| 1 | Serpentine must be near the skew source | DROPPED (user 2026-11-14: not needed) |
| 2 | Draw ESD / hanging branches (D151 …) in cross-section / top view | OUT of scope: main path only, as the mock |
| 3 | Verdict column of 2.x tables always NOT OK | Kept as the mock (user did not ask to remove) |
| 4 | Summary: connection column = Verdict in a 1-connection tab | Kept as the mock (both columns) |
| 5 | Backdrill legend entry in cross-section | Not added |
| 6 | Through-hole connector pin stub | Layers only (e.g. "Layer 3 → Bottom"), no mm |
| 7 | Picture limit `review.max_images` 40 per channel | Still applies |

### Session 2026-11-12 (user review of 2.11.0)

| # | User | Change |
|---|---|---|
| R1 | "mũi tên bạn cho mảnh thôi, đang bị trùng" | Serpentine picture: thin measuring arrows; arrow heads small and never longer than 1/3 of the arrow (short c arrow no blob); labels A / G / c / W with a white halo, not overlapping each other or the arrows. → T020 |
| R2 | "2 đầu mũi tên chỉ không đúng chỗ" | Cause (SERLINK_DEVA2DEVB_L0_P, Layer 5): the pair's split toward the pins (fan-out) was taken as a bump, so A = 0.571 mm measured the P–N split, not the bump. Fix: a far run next to a pin / via exclusion zone or a path end is a fan-out, never a bump; A / G / c / W arrow tips sit exactly on the measured points (A: base-line centre → bump-top centre of a real bump; G / W: trace edges; c: chamfer ends). Serpentine counts / A values change on purpose (re-check SERLINK + PCIe, list before → after). → T021 |
| R3 | "note layer của series component (tụ, điện trở) và layer của 2 linh kiện 2 đầu" | Routing view (2.1): every end component and series part shows its placement layer next to its refdes in the top view and the cross-section, e.g. "U14 (Top)", "C172 (Bottom)". → T022 |
| R2b | (decided by agent, user asleep) | "Path end" alone is NOT a fan-out sign (paths are split into primitives; a joint is not a pin): a far run is a fan-out only when it touches the pin / via exclusion zone AND stays far from the partner up to the path end. A real bump within 1 mm of a via comes back to the partner and is kept. Reason: the wider rule dropped 5 real 2-bump serpentines (SERLINK, PCIe). |
| R4 | "bổ sung thêm thông tin về via type trên biểu đồ mặt cắt ngang" | Cross-section (2.1): every via shows its type from the board data (through / blind / buried / microvia, backdrilled when drilled), short label next to the via, e.g. "Through", "Blind Top–L3", "Micro", "Through, backdrilled"; legend line explains the labels. → T024 |
| R5 | "Ghi thêm kích thước via nữa, ví dụ 18D8 (Pad 18, hole 8)" | Cross-section: each via label also gives its size as `<pad>D<hole>` in mil, rounded to whole mil (e.g. "Through 18D8"); pad = pad diameter on the signal entry layer, hole = finished drill diameter, from the padstack definition; legend explains "18D8 = pad 18 mil, hole 8 mil". → T025 |

### Session 2026-11-13 (user review of 2.11.1 — demo `mock/serp_dim_demo.html` approved: "Đồng ý triển khai")

| # | User | Change |
|---|---|---|
| R6 | "sử dụng chuẩn ký hiệu như trong bản vẽ cơ khí … rất khó nhìn được bạn đo gì" | Serpentine picture follows mechanical-drawing dimensioning (ISO 129 style): thin extension lines perpendicular to the measured edge (small gap from copper, ~2 mm past the dimension line in picture scale); thin dimension line parallel to the measured distance with an arrow at BOTH ends touching the extension lines / edges; value centred beside the dimension line with its unit (`A = 16.7 mil`); too narrow → arrows outside pointing in, text beside (W); trace centre line dash-dot. → T026 |
| R7 | (demo) | Two views: overview of the pair only circles the measured bump with a dashed circle labelled "A" (no numbers); a "Detail A (x N)" frame enlarges that one bump and carries all dimensions W / A / G / c. → T026 |
| R8 | "Khoảng cách từ cạnh đến cạnh" | A and G drawn edge to edge. G = facing edges of adjacent bump legs (unchanged). A = straight-trace edge → bump-top edge on the same side (numerically = centre → centre, so A values do not change). → T026 |
| R9 | "chưa hình dung c đo gì" | c = length of the 45° chamfer along the trace centre line; drawn as an aligned dimension (extension lines perpendicular to the chamfer, dimension line parallel to it). Rule text unchanged (c ≥ 1.5W). → T026 |
| R10 | "Đơn vị nên là mil" / "nút gạt qua mil, um và mm" | Report header has a unit switch mil / µm / mm, default mil, choice remembered by the browser (try/catch; works without storage). It changes EVERY length in the report: serpentine picture, routing view (cross-section sizes, length table), Summary / section rows, Issue / Recommendation values and limits. Rounding: mil 1 decimal, µm whole, mm 3 decimals. Not changed: area (mm²), angle, %, via name `<pad>D<hole>` (stays mil). HTML carries the value in metres (data attribute) and JS formats it; without JS the text shows mil. → T027 |

### Session 2026-11-14 (user review of 2.11.2)

| # | User | Change |
|---|---|---|
| R11 | "chữ của W = .... và C =... đang bị chồng lên nhau" (screenshot: SERLINK Detail A (x2), "W = 3.9 mil" runs into "c = 5.6 mil") | No two dimension values (W / A / G / c) in the Detail frame overlap each other. When the default place of a value collides with another value, the value moves to another free place next to its own dimension (other side of the arrow, further out along the dimension); the frame grows to keep every value inside. Dimension lines / numbers unchanged. → T029 |
| R12 | "Hình vẽ này bị vỡ ảnh … tự vẽ lại khu vực này cho sắc nét hơn" (screenshot: reference panels Layer 2 / Layer 4 - GND with stair-step void edges); demo `autocut/review_033/demo_vector_ref.html` approved: "Đồng ý triển khai" | Every review picture that shows plane copper (reference panels of SOV / loss of reference / ref to other net / via clearance / plane edge, and zoom pictures) draws the copper as vector shapes: the real outline and voids of the reference-net copper of that layer (arcs as fine chords), clipped to the picture frame; other-net copper the same way (where no GND). Sharp at any zoom. Findings, counts and values unchanged (drawing only). When the copper shapes cannot be read, the picture falls back to the old grid drawing. → T030 |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Short pass / fail report, one tab per connection (Priority: P1)

The engineer opens the review HTML and sees one tab per connection; each tab has a Summary table and sections
2.1–2.5 with only OK / NOT OK and the NOT OK rows.

**Why this priority**: the report's main reading path.

**Independent Test**: SERLINK on a test1 copy (3 connections U14_U15, U14_J8, U14_U227): 3 tabs; header 3 lines; no
HIGH / MEDIUM / INFO word, no "Reference data", no link bar, no "Overall" line; counts per section = HIGH + MEDIUM
findings of that connection (after FR-010 / FR-011 changes).

**Acceptance Scenarios**:

1. **Given** a review of N connections, **When** the HTML opens, **Then** a shared header (bold labels "Layout
   version:" board name without `.aedb`, "Review gate verdict:" as today, "Review date:" `dd/mm/yyyy - hh:mm:ss`)
   and N tabs, each a full report of that connection only, built from one measurement run.
2. **Given** a tab, **When** read, **Then** Summary (section 1) table columns Index (1..5, centred) · Section (bold
   name + one short sentence) · connection cell (`OK` or `NOT OK` + "N issue(s)") · Verdict (`OK` / `NOT OK`); rows
   in order Routing, Reference, Trace stub, Via, Stackup with the sentences of summary §2.
3. **Given** a section 2.x, **When** read, **Then** "This section checks:" numbered list (bold check name: short
   text, generated from the rule steering files so a new rule appears by itself), lead line `NOT OK — N issues` or
   `OK`, and (only when NOT OK) a table Index · Verdict · Description · Picture listing NOT OK rows only.
4. **Given** a NOT OK row, **When** read, **Then** Description is exactly two lines `Issue: <one sentence>` /
   `Recommendation: <one sentence>`; measured values use the symbols drawn in the picture (A, G, c, W, H) with mm and
   mil.
5. **Given** any text, **When** shown, **Then** black, except OK (bold #0050c8) and NOT OK (bold #d00000); table
   headers background #dce6f2; title 18 px, h2 / h3 14 px, other text 12 px (SVG text excluded).

---

### User Story 2 - See how each pair is routed (Priority: P1)

In 2.1 Routing the engineer opens a collapsed box per pair and sees a scaled top view (P and N, colour per layer, end
and series components with real body / pads), a cross-section from first pin to last pin (layers, segment lengths,
vias, stubs, backdrill, series parts) and a length table.

**Why this priority**: replaces the removed via-count checks and the Reference data tables.

**Independent Test**: SERLINK U14_J8 TX_L2 pair: box title `<channel>: <P> / <N> (U14 → J8)`; top view shows U14, J8
and the AC caps with refdes; cross-section line `Cross-section <net> (same for <N>): Vias: n · Backdrilled: n · With
stub: n`; length table P / N Total + per layer equal to today's routing lengths.

**Acceptance Scenarios**:

1. **Given** a pair, **When** the box is opened, **Then** the top view draws only the traces of P and N (no GND, no
   unused pads), colour per routing layer (different per layer in one picture), P dark / N light shade of the same
   colour, thin lines, true scale; end components (body outline + real pad sizes) and series parts (real pads);
   small refdes not overlapping (P / N caps: above / below), vertical text for vertical parts; legend line with layer
   colours + "P: dark shade, N: light shade" + frame size in mm.
2. **Given** a picture, **When** loaded, **Then** zoom is locked ("Zoom locked (click to unlock)"); unlocked: wheel
   zooms at the cursor, drag pans, double-click resets; text keeps its screen size.
3. **Given** the cross-section, **When** drawn, **Then** rows = stackup layers (Top first, GND layers light blue),
   trace red with segment length, vias black between entry and exit layer, stub pink, backdrilled part dashed pink,
   series parts and end pins as boxes with refdes; not to length scale; a through-hole connector pin drawn as a via
   (stub visible) but not counted as a via; a member whose topology differs from P (layer / via / backdrill) gets its
   own cross-section.
4. **Given** the length table, **When** read, **Then** rows P and N, columns Total (mm) + each layer (mm).
5. Trios (C-PHY): drawn the same way with all members; cross-section of member A (+ differing members).

---

### User Story 3 - Serpentine rule and no pair-gap false findings (Priority: P1)

Length-matching serpentines are measured against fixed limits; a pair separating inside its own serpentine is not
a pair-gap issue.

**Independent Test**: SERLINK: Pair gap 3 → 1, Serpentine 10 NOT OK (all A > 3W), 0 violations of G / c / 90°
(mock numbers; small differences allowed only with a reason in verify notes).

**Acceptance Scenarios**:

1. **Given** a pair member with ≥ 2 repeated bumps relative to the other member (centre distance > nominal gap +
   1.5W, bump length < 2 mm, spacing < 2 mm, heights within 0.7–1.43×), outside 1 mm around the pair's pins / vias,
   **When** reviewed, **Then** it is one serpentine.
2. **Given** a serpentine, **When** checked, **Then** NOT OK when any of: G (edge-to-edge gap between adjacent parallel
   segments) < 3H (H = dielectric distance trace layer → nearest reference GND layer from the stackup); A (base-line
   centre → bump-top centre) > 3W; a 90° corner; a 45° chamfer c (segment at ~45° to the pair direction) < 1.5W with
   5 % tolerance. One row per serpentine; passing serpentines not listed.
3. **Given** the row picture, **When** drawn, **Then** labelled measuring arrows (A, G, c, W), no circle; layer + net in
   the top-left corner; under the picture lines "X = … mm (… mil) must be ≤ / ≥ … → OK / NOT OK".
4. **Given** a pair separation that lies inside a serpentine of the same pair, **When** Pair gap runs, **Then** it is
   not reported.

---

### Edge Cases

- Single-ended net (no pair): top view / cross-section of the net alone; no pair rules.
- Section with no issue: only the line `OK`, no table.
- Pair whose members are routed to different end components: box title uses the first chain's ends.
- Pairs found in reverse naming direction (e.g. DEVA2DEVB): grouped from the net names of each chain.
- More rows than `review.max_images`: rows beyond have no picture (as today).
- Review gate (025): still uses HIGH / MEDIUM internally; only the HTML hides them. JSON results of design_review /
  isim_review keep severity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The review HTML MUST be one file with a shared 3-line header and one tab per connection, each tab built
  from the same single measurement run (no re-measure per tab).
- **FR-002**: Removed from the HTML: top link bar, "Overall" line, section "3. Reference data" and every reference to
  it, "↑ summary" lines, every HIGH / MEDIUM / INFO label. Issue = HIGH or MEDIUM finding; INFO is not shown.
- **FR-003**: Summary table and sections follow US1 (columns, order 1 Routing, 2 Reference, 3 Trace stub, 4 Via,
  5 Stackup, sentences, colours, font sizes).
- **FR-004**: Each section's "This section checks:" list and each rule's Issue / Recommendation sentences MUST come
  from the rule steering files `review_rules/<id>.md` (031 single source); a new rule appears without HTML code edits.
- **FR-005**: Description = `Issue:` + `Recommendation:` lines only (no Why, no number table).
- **FR-006**: Pictures: fault marked by a dashed pink (#ff1493) frame / ring (no orange fill), no colour legend under
  the picture, line `Location: X = … mm, Y = … mm` under it; reference pictures keep one panel per plane (032) with
  the pink frame around the stretch.
- **FR-007**: 2.1 Routing contains, before its NOT OK table, "Signal routing per pair" (view only, no verdict) per
  US2: collapsed box per pair with top view, cross-section, length table, zoom control.
- **FR-008**: Routing data (paths, via rows, pins, series chains, stackup, component boxes / pad boxes) MUST be
  collected during the review measurement (channel data), work on the layout snapshot (no live board read when the
  snapshot is used) and use real pin pad boxes (not padstack-name guesses).
- **FR-009**: New rule `serpentine` (section Routing, steering + code file per 031) per US3; thresholds in
  `templates/autocut_template.csv` (`review.*`: 3H gap factor, 3W amplitude factor, 1.5W chamfer factor, 5 %
  tolerance, detection constants).
- **FR-010**: Rule `pair_gap` MUST NOT report separations inside a serpentine of the same pair.
- **FR-011**: Rules `via_count` and pair via-count mismatch MUST be removed (via counts shown in the cross-section);
  steering, catalog / rule list, template rows and tests updated.
- **FR-012**: Guide `review_measure` and steering files MUST describe the new report (OK / NOT OK wording, tabs,
  routing view, serpentine); Claude's chat summary uses OK / NOT OK per section.
- **FR-013**: Intended result changes (via_count removed, serpentine added, pair gap reduced, HTML form) MUST be
  listed per channel (before → after) on test1 SERLINK + PCIe and board1; goldens / references updated deliberately.

### Key Entities

- **Connection tab**: channel name, ends, sections with verdict and issue rows.
- **Pair routing view**: members, ends, series parts, per-member path (segments with layer / length, vias with
  layers / stub / backdrill), length per layer, top-view geometry.
- **Serpentine**: net, layer, bump list, measured A / G / c / corner angles, W, H, verdict.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: SERLINK test1 report: 3 tabs; 0 occurrences of HIGH / MEDIUM / INFO / "Reference data" in the HTML text.
- **SC-002**: SERLINK: Serpentine 10 NOT OK, Pair gap 1, Via count 0 (±1 per rule with a written reason).
- **SC-003**: Every pair in SERLINK, PCIe and board1 has a routing box whose length table equals the review's routing
  lengths (± 0.001 mm).
- **SC-004**: HTML build time on the snapshot ≤ 2 × the 2.10.0 time for the same channels (pictures added).
- **SC-005**: The user finds the NOT OK items of one connection from its Summary in under 30 seconds (user review).

## Assumptions

- Mock look (`autocut/mock/SERLINK_short_mock.html`) is the visual target; mock code is not copied as-is.
- Report language English; code comments Vietnamese.
- Gate (025) logic and review records unchanged except removed / added rules.
- Version: minor (report form + rules change, Claude restart for guide changes).
- Test boards: copies only (test1 SERLINK + PCIe, board1).
