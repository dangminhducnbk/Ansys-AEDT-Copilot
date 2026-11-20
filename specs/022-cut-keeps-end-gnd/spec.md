# Feature Specification: Cut keeps the GND pins of IC / connector ends

**Feature Branch**: `022-cut-keeps-end-gnd` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-10

**Status**: Done 2.1.0

**Input**: User description: "tôi muốn chỉnh lại về phương pháp cut. Một IC, connector tín hiệu không thể không có pin
GND được. Do phương pháp cut làm mất pin GND của nó. Vậy nên đối với khu vực IC/connector, cần phải kiểm tra xem việc
cut có làm mất pin GND không. Nếu có thì phải chỉnh lại khu vực ở phía IC/connector đó."

## Clarifications

### Session 2026-11-10

- Rule (user): "Ví dụ tôi chọn hệ số cut là 0.06 thì mọi vùng đều phải tuân thủ quy tắc này. Chỉ riêng vùng 2 đầu của
  IC/connector, nếu nguyên tắc này vi phạm quy định là phải có GND pin/exposed pad GND ở vùng này thì chỉ riêng vùng này
  sẽ phải chỉnh lại hệ số cut to hơn để có thể lấy được GND pin/exposed pad."
- Agreed values (user "Đồng ý"): step +0.02 per try; maximum end factor 0.30; end region = component body + 1 mm;
  maximum reached without GND → today's 015 question with image. Feature 021 (GND pin cleanup) stays separate, later.
- Re-cut of older runs (no user answer needed, follows the rule): a re-cut uses the current cut method; an enlarged
  end region is reported as a difference to the previous run.
- Correction (user 2026-11-10): "Bạn phải có thêm chức năng phát hiện pin GND của IC/connector, nếu kiểm tra nó có pin
  GND thì phải tăng hệ số cut đến khi lấy được pin/exposed pad GND." → the tool first DETECTS the GND pins / exposed pad
  of each end component on the source board. Has GND → the end factor is raised until one is fully inside, with NO
  stop at a maximum (the 0.30 maximum is dropped). The 015 question is asked ONLY when detection finds no GND pin on
  the board.
- Extension (user "Đồng ý" 2026-11-10, after "phải có ảnh hiển thị để người dùng hình dung ra vùng cut" and "nếu trong
  lúc review tôi thấy hệ số cut này không ổn, thì thay đổi để chọn lại hệ số cut ra sao?"): Gate A gets (a) a cut
  settings FORM with one tab per interface, (b) a cut PREVIEW computed before cutting (per-end table + cut-region
  image, recomputed when a value changes), (c) a per-end MANUAL end factor (empty = automatic; a value is used as given,
  still checked for GND: no GND fully inside → error, no cut).

- Patch 2.1.1 (user "Đồng ý" 2026-11-10, after reviewing the preview images): LESS TEXT on cut_region.png and
  end_<refdes>.png. Title one line ("<interface> · W × H mm"; zoom "<interface> · <refdes>"); legend = colour swatches
  + 1-2 English words in the footer next to the scale bar (Signal, Base cut, Added, End region, GND pin, GND via, Other
  net; only items present); image label "<refdes> <factor>" only (added area stays in the table); other nets in the
  added area = grey fill only (no numbers, no name list on the image; names stay in table_md / preview.json). Scale
  bar, canvas fit, GND vias, refdes inside the frame kept. Extent computation untouched.

- Patch 2.1.2 (user "Gạch chéo, 2.1.2" 2026-11-10): other nets in the added area are drawn WITHOUT solid fill — dark
  grey outline + diagonal grey hatch only — so the green added area stays green underneath; legend "Other net" swatch
  = same hatch. 2.1.1 stays as released.

## Problem

- The cut extent is built from the signal nets with one factor (`cutout.expansion`, e.g. 0.06). GND pins of an end
  component outside it are cut away.
- Board1: U26 / U21 (QFN64) have a GND exposed pad (pin 65, 6.3 × 6.3 mm, 25 GND vias); only 35 % / 41 % of it lies
  inside the extent, so the cut removes it. The end then has "no GND pin" and the flow stops with the 015 question.
- Engineer's rule: a signal IC / connector ALWAYS has a GND pin; losing it is a defect of the cut. The cut must fix it,
  only where it happens.

## The rule

| # | Step |
|---|---|
| 1 | **Detect** the GND pins / GND exposed pad of each end component (IC / connector, any end type) on the SOURCE board (pins of the component on a reference net, `cutout.reference_nets`), before cutting. |
| 2 | The whole interface is cut with the engineer's factor (`cutout.expansion`), as today. |
| 3 | End has GND pins (step 1) and at least one GND pin / pad lies FULLY inside the extent → nothing changes for that end. |
| 4 | End has GND pins but none fully inside → ONLY the end region (component body + `cutout.end_region_margin_mm` 1 mm) gets a larger factor: factor + `cutout.end_expansion_step` (0.02) per try, repeated UNTIL a GND pin / exposed pad is fully inside (no maximum). Only the part of the larger extent inside the end region is added; the rest of the interface keeps the base factor. The end region contains all pins of the component, so the loop always ends; if the whole region is covered and still no GND pin is inside (geometry error), the cut stops with an error naming the end and pin. |
| 5 | End has NO GND pin on the board (step 1) → no enlargement; the 015 question (image + options) as today. |
| 6 | The end check reports per end: GND pins detected on the board, base factor, factor used, added area, GND pin / pad gained, other nets inside the added area (not kept by the cut), with the end image (base extent, added area, GND pin / pad). Shown before Gate B. |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Only the end region is enlarged to reach a GND pin (Priority: P1)

**Why this priority**: this is the requested change of the cut method.

**Independent Test**: cut CPHY_U14_U26 on a board1 copy with factor 0.06: U26 end region uses a larger factor
and keeps pin 65 (exposed pad) fully with its GND vias; the rest of the extent equals the 0.06 extent; no 015 question
for U26; 24 ports; self-check OK; `gnd_reference` U26 = own pins.

**Acceptance Scenarios**:

1. **Given** an end that has GND pins on the board but none fully inside the base extent, **When** the cut runs,
   **Then** only the end region is enlarged, step by step, until one is fully inside (no maximum); the factor used is
   reported.
2. **Given** an end that already has a GND pin fully inside, **When** the cut runs, **Then** its region is unchanged.
3. **Given** an interface where both ends meet the rule, **When** it is cut, **Then** the result is identical to today
   (test1 PCIE_U14_J25: same extent, 16 ports).
4. **Given** an end component with no GND pin on the board, **When** detection runs, **Then** no enlargement is made
   and the 015 question appears.

---

### User Story 2 - Engineer sees each enlargement before Gate B (Priority: P1)

**Why this priority**: the extent is a cut setting (locked after cut); the engineer must see where it changed.

**Independent Test**: board1 copy: end check of CPHY_U14_U26 shows U26 "factor 0.06 → x, + N mm², pin 65 kept" and the
image.

**Acceptance Scenarios**:

1. **Given** an enlarged end, **When** ends are checked, **Then** the table row and image show base extent, added
   area, factor used and the GND pin / pad gained.

---

### User Story 3 - Settings and re-cut (Priority: P2)

**Why this priority**: boards differ; the engineer must be able to tune and re-run.

**Independent Test**: step / margin rows appear with the cut settings (locked group after cut); a re-cut of a
0.15.0 board1 run lists "end region enlarged" as a difference.

**Acceptance Scenarios**:

1. **Given** the cut settings, **When** content is agreed (Gate A), **Then** the two new rows are shown with their
   defaults and can be changed there (re-cut to change later).
2. **Given** a re-cut of an older run, **When** content is shown, **Then** the enlargement is listed as a difference.

---

### User Story 4 - Gate A cut settings form + preview image, per interface (Priority: P1)

At Gate A the engineer sees, for each interface (one tab each), the cut settings form (factor, unit, extent type,
end step, end margin, reference nets, and one "end factor" field per end) and a PREVIEW computed on the source board
before any cut: per-end table and an image of the cut region. Changing a value recomputes the preview.

**Why this priority**: the engineer must picture the cut region and choose the factor before the (slow, locked) cut.

**Independent Test**: board1 copy, request with CPHY_U14_U26 and CPHY_U21_J25: 2 tabs; preview of U14_U26 at 0.06 shows
U26 enlarged to the computed factor with + area, pin 65 blue inside, image file per interface + zoom per enlarged end;
change factor to 0.10 → preview recomputed; nothing written to the board.

**Acceptance Scenarios**:

1. **Given** content proposed, **When** the preview runs, **Then** per interface it returns: per-end rows (GND pins
   on board, GND fully inside at the base factor yes/no, factor used, added area mm², GND pin / pad gained, other nets
   in the added area) and image paths.
2. **Given** the image, **When** the engineer opens it, **Then** it shows: signal traces / vias (red), base extent
   (grey outline), added end area (light green, label "<refdes>: <factor>, +N mm²"), end region frame (dashed), end and
   series components (frame + refdes), GND pins / pad kept (blue), GND pins still outside (blue, red outline), other
   nets in the added area (light grey + name), mm scale and overall size; plus one zoom image per end.
3. **Given** the form is submitted, **When** values come back, **Then** they are validated and the preview is
   recomputed; the submit is input only — Gate A still needs the engineer's explicit go.
4. **Given** several interfaces, **When** the form is shown, **Then** "Set default" (tab) and "Copy to all tabs"
   (editable cut values, never the per-end factors) work as in the Gate B form.

---

### User Story 5 - Engineer sets an end factor by hand (Priority: P2)

After reviewing, the engineer may type a factor for one end (e.g. U26 = 0.20). Empty = automatic.

**Why this priority**: lets the engineer narrow or widen one end region without changing the whole interface.

**Independent Test**: board1 copy: U26 end factor 0.20 → preview and cut use 0.20 for U26 only; U26 factor 0.06 (no
GND inside) → refused with the end and the reason, nothing cut.

**Acceptance Scenarios**:

1. **Given** a manual end factor, **When** preview / cut run, **Then** that end region uses it exactly (no stepping),
   the rest keeps the base factor.
2. **Given** a manual end factor that leaves no GND pin / pad fully inside, **When** preview runs, **Then** it reports
   the error for that end; Gate A / the cut is refused until it is fixed or cleared.
3. **Given** the cut is done, **When** the engineer wants another factor, **Then** it is changed only through Gate A
   again and a re-cut (cut group locked), old outputs renamed `*_old_<time>`.

---

### Edge Cases

- BGA end (test1 U14, 1666 GND pins): GND balls next to the signal balls are already inside → no change.
- Added area overlaps other nets: the cut keeps only channel nets + GND; those nets are listed, not added.
- Two ends close together: each end region is enlarged on its own; overlap is simply joined.
- Part with no GND pin anywhere on the board: detected before the cut → 015 question (keep component / plate / stop ...).
- 019 "keep pad" option: pads reached by the rule are kept automatically; the option stays only for the 015 fallback.
- Excel flow: removed in 1.0.0; nothing to change.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Before the cut, the tool MUST detect the GND pins / GND exposed pad of each end component on the source
  board. The cut MUST use the engineer's factor for the whole interface and MUST check each end that has GND pins for at
  least one GND pin or GND exposed pad fully inside the extent.
- **FR-002**: When an end breaks the rule, the tool MUST enlarge ONLY the end region (component body + margin) by
  raising the factor in steps (`cutout.end_expansion_step` 0.02) until a GND pin / pad is fully inside (no maximum;
  region fully covered without GND = error naming end and pin); outside the end region the extent MUST equal the base extent.
- **FR-003**: The two values MUST be template rows (Principle III): `cutout.end_expansion_step` 0.02,
  `cutout.end_region_margin_mm` 1.0; shown and agreed with the cut settings at Gate A,
  stored in `user_settings.json`, locked after cut like the other `cutout.*` rows.
- **FR-004**: The GND vias inside a kept GND pad MUST be kept by cleanup (as 019).
- **FR-005**: An end that meets the rule with the base factor MUST give a cut identical to today.
- **FR-006**: An end component with no GND pin on the board (detection) → the 015 question MUST appear unchanged (image
  + options); an end with GND pins MUST NEVER reach the 015 question.
- **FR-007**: Cut report and end check MUST state per end: GND pins detected on the board, base factor, factor used, added area, GND pin / pad gained,
  other nets in the added area; the end image MUST show base extent, added area and the GND pin / pad.
- **FR-008**: Re-cut MUST use the current method and list an enlargement as a difference to the previous run.
- **FR-009**: The same rule MUST apply to `design_cutout` (design tools).
- **FR-010**: The `interface_sim` and `design_tools` guides MUST state the rule; the board1 regression reference MUST be
  updated on purpose (U26 GND reference = own pad instead of plate) with the change in CHANGELOG; the PCIe check on
  test1 MUST still PASS unchanged.
- **FR-011**: A read-only cut PREVIEW MUST be available before the cut (per interface; source board opened read-only;
  nothing written): per-end table (FR-007 fields) + cut-region image + one zoom image per enlarged end (US4 scenario 2).
  It MUST be the same computation the cut uses (identical extent).
- **FR-012**: Gate A MUST offer a cut settings FORM per interface (tabs; fields from the template `cutout.*` rows +
  one optional end factor per end; "Set default", "Copy to all tabs"); the form is input only; validation errors name
  the field; Gate A go stays explicit (Principle I). Clients without widgets get the same as markdown tables + image
  paths.
- **FR-013**: A per-end manual factor (`cutout.end_factor` per refdes, empty = automatic) MUST be used exactly when
  given, validated (> 0, same unit as `cutout.expansion`), checked for a GND pin / pad fully inside (else error, no
  cut), stored in `user_settings.json`, and reused by re-cut.
- **FR-014**: New / changed MCP tools MUST follow Principle X (catalog entry, safety read for the preview, contract,
  tests); the `interface_sim` guide MUST describe the Gate A form + preview flow.

### Key Entities

- **End GND check**: per end, GND pins / pads fully inside at the base factor, factor used, enlargement polygon, added
  area, other nets in it, result (met / enlarged / max reached).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Board1 CPHY_U14_U26 and CPHY_U21_J25: U26 / U21 keep their GND pad; 0 "no GND pin" questions; ports
  24 / 18; self-check OK.
- **SC-002**: Outside the end regions the extent equals the base-factor extent (area difference 0 outside the regions).
- **SC-003**: Interfaces whose ends already meet the rule give an identical cut (test1 PCIE_U14_J25: 16 ports, same
  extent).
- **SC-004**: 100 % of end components that have GND pins on the board keep ≥ 1 GND pin / pad in the cut result; the 015
  question appears only for parts with no GND pin on the board.
- **SC-005**: Before any cut, the engineer gets per interface a preview table + cut-region image; the preview extent
  equals the extent then cut (area difference 0).
- **SC-006**: A changed factor (base or per end) gives a new preview without writing any file on the board.

## Assumptions

- "IC / connector" = the two end components of an interface (any end type).
- "Fully inside" = the GND pin's pad outline (or the exposed pad outline) lies inside the extent polygon.
- Copies only (board1, test1); originals never touched.
- Version: change of cut method and of the board1 reference → minor 2.1.0 (reference change in CHANGELOG); ROADMAP
  updated. Feature 021 (GND pin cleanup) is separate and comes later.
