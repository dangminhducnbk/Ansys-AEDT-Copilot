# Feature Specification: Layout review report template

**Feature Branch**: `026-review-report-template` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "tôi muốn có template cho report của review layout. Yêu cầu là template có mục summary
ban đầu cho từng section con bên dưới, có đánh giá mức độ nguy hiểm của issue nếu có. Bên dưới mục chi tiết, mỗi phân
loại hạng mục kiểm tra có các issue được trình bày theo dạng bảng, cột đầu là index, cột thứ 2 là mô tả, cột 3 là hình
ảnh khu vực đó (không bật all layer, sai chỗ nào chụp chỗ đó)."

Number note: 025 is taken by the review-gate feature on its own branch (not yet in `main`), so this feature is 026.

## Problem

Today's layout review report (HTML, `design_review(html=true)`):

| Part today | Gap vs the request |
|---|---|
| Summary = 2 tables Item × channel (signal via, signal routing) + "Abnormal points" list | No summary per detail section; no severity verdict per section |
| Detail = one section per CHANNEL, abnormal points as picture cards in a grid | Not grouped by check category; not a table index / description / picture |
| Zoom picture: problem layer solid red, OTHER layers dashed, light-blue GND of the ref layer | Other layers are drawn ("all layer"): the picture is busy; the user wants only the layers involved in that issue |
| All findings (incl. INFO) in a collapsed table per channel | Kept as reference data, not the issue tables |

## Clarifications

### Session 2026-11-10

- Q: Template form? → A: fixed structure in code, the same for every board (no editable template file).
- Q: Do INFO findings get rows in the category tables? → A: no; tables hold HIGH + MEDIUM only, INFO is counted in the
  Summary and listed in Reference data.
- Q: Output format? → A: one self-contained HTML file, as today (no Word / PDF).

### Session 2026-11-10 (user review of 2.5.0)

- User (on REF-01, U21_J25): "Hình bị tràn text khỏi khung, phần description bạn viết lại đi, đọc quá khó hiểu."
  → (1) Picture legend wraps INSIDE the picture cell: one swatch + name per item ("Top Layer – signal",
  "Layer 2 - GND – GND (ref)", "GND via", "signal via", "issue"), small font, no overflow (cause: the old CSS rule
  `.legend span{width:14px}` also hit the name spans). (2) Description = short labelled lines per finding: title +
  severity, Net (channel), location, layers, measured value next to its limit (✗ / ✓), "Why" and "Fix" in plain
  English per check. Internal key names and point / finding ids only in the hover title. → T011, T012.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Summary first, with a danger rating per section (Priority: P1)

The engineer opens the review report and reads, at the top, one summary block per detail section (check category):
how many issues, the worst severity, and a one-line danger verdict. They know in seconds whether the layout is
acceptable and which section to read.

**Why this priority**: the summary is what the engineer (and the 025 review gate) decides on.

**Independent Test**: board1 review of CPHY_U14_U26 + CPHY_U21_J25: the summary lists every detail section in the
same order as the detail part, each with issue count per severity and a danger verdict; numbers equal today's
review data (U14_U26 0 HIGH / 0 MEDIUM; U21_J25 2 HIGH, 16 MEDIUM ...).

**Acceptance Scenarios**:

1. **Given** a review with issues, **When** the report opens, **Then** the first section is the summary: one row /
   block per detail section with count per severity (HIGH / MEDIUM / INFO), worst severity, danger verdict, link to
   the section.
2. **Given** a section with no issue, **When** shown in the summary, **Then** it reads "OK — no issue" (not omitted).
3. **Given** several channels, **When** the summary is shown, **Then** each section's counts are split per channel.
4. **Given** the review gate verdict of 025 (stop / continue / overridden), **When** it exists, **Then** the summary
   shows it at the top.

---

### User Story 2 - Detail: one table per check category (Priority: P1)

Below the summary, each check category has its own section with a table of its issues: column 1 index, column 2
description, column 3 the picture of that area.

**Why this priority**: the request's core format.

**Independent Test**: the U21_J25 HIGH "ref change" issue appears in the reference category table with an index,
a description (channel, net, layer, location, measured value vs limit, severity) and its own picture.

**Acceptance Scenarios**:

1. **Given** a category with issues, **When** rendered, **Then** a table with exactly 3 columns: Index, Description,
   Picture; one row per issue (issues at the same net + location merged into one row, as today).
2. **Given** an issue row, **When** read, **Then** the description states channel, net, layer(s), location (x, y mm),
   what was measured, the value and limit, severity and its reason.
3. **Given** the index, **When** clicked from the summary, **Then** it jumps to the row; the index is stable within the
   report (category prefix + number, e.g. `REF-03`).
4. **Given** a category with no issue, **When** rendered, **Then** the section exists with "No issue".

---

### User Story 3 - Picture shows only the layers involved, zoomed on the fault (Priority: P1)

Each picture is zoomed on the issue location and draws only the layers that issue involves, not all layers.

**Why this priority**: the user's explicit requirement ("không bật all layer, sai chỗ nào chụp chỗ đó").

**Independent Test**: for a ref-change issue at a via, the picture shows the signal trace layers before / after the
via and their reference planes only; no other signal or plane layer is drawn.

**Acceptance Scenarios**:

1. **Given** an issue, **When** its picture is drawn, **Then** the view is centred on the issue location with a margin
   (template default) and the issue marked.
2. **Given** the issue's layers (see table in Requirements), **When** drawn, **Then** only those layers appear; each
   drawn layer is named in a small legend under the picture.
3. **Given** two issues in the same place, **When** merged into one row, **Then** one picture shows the union of their
   layers.

---

### Edge Cases

- More issues than the picture limit (`review.max_images`, 40 today): rows beyond the limit have no picture and the
  description says so; the summary still counts them.
- Channel that failed to trace: listed in the summary as "review incomplete" (and under 025 = stop), no detail rows.
- Issue whose involved layer cannot be determined: picture falls back to the issue layer only and says so.
- INFO findings: counted in the summary; no rows in the category tables (Q2 A); they stay in the Reference data part.
- Very large board: report size stays reasonable (pictures are zoom crops, not full-board renders).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The review report MUST follow one fixed structure: (1) header (board, design, date, tool version,
  review gate verdict when present), (2) Summary, (3) Detail sections, one per check category, (4) Reference data
  (today's all-findings tables and summary tables, collapsed). The structure is fixed in code, the same for every board (Q1 A); no editable template file.
- **FR-002**: The Summary MUST have one entry per detail section, in the same order, with: count per severity per
  channel, worst severity, danger verdict (one line: "Nguy hiểm — dừng" for HIGH, "Cần xem" for MEDIUM, "Thông tin"
  for INFO only, "OK" for none), link to the section. Severity rules stay those of the review checks (no new
  thresholds).
- **FR-003**: Detail sections MUST be per check category: Reference (SOV, reference to other net, loss of reference,
  reference plane change), Trace stub, Via (stub, backdrill, nearest GND via), Routing (length / width / layer
  matching). A new review check adds a new section automatically (registry order).
- **FR-004**: Each category table MUST have exactly 3 columns: Index, Description, Picture. Rows = HIGH and MEDIUM
  issues only (Q2 A); INFO findings are counted in the Summary and listed in Reference data.
- **FR-005**: Pictures MUST be zoomed on the issue and draw only the involved layers:

  | Issue type | Layers drawn |
  |---|---|
  | Trace issue (SOV, loss of ref, ref to other net, trace stub, width / length) | the trace layer + its reference plane layer(s) |
  | Reference change at a via | signal layer before + after the via + both reference plane layers |
  | Via issue (stub, backdrill, GND via distance) | the layers the via connects / its stub layers + the reference planes there |

  Signal and GND are drawn in the report's fixed colours; a legend under each picture names the layers shown.
- **FR-006**: Numbers, severities and issue ids MUST equal the review data of the same run (the report is a view, not
  a new measurement); `tests/review_check.py` results unchanged.
- **FR-007**: The report MUST stay a self-contained file (no external links needed to view it), English text as
  today (user rule 2026-10-22), opened by `design_review(html=true)`, the standalone `layout-review` workflow, and
  the 025 review step on request.
- **FR-008**: Output format: one self-contained HTML file, as today (Q3 A). No Word / PDF export.
- **FR-009**: Guide `review_measure` MUST describe the new structure (summary first, category tables) so Claude's chat
  summary uses the same order and danger wording.

### Key Entities

- **Report section**: check category, title, order, issues, counts per severity per channel, danger verdict.
- **Issue row**: index (category prefix + number), channel, net, layers, location, measured value, limit, severity,
  reason, picture, layers drawn.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer finds the worst issue of the board from the top of the report in under 30 seconds (summary
  first, worst severity per section).
- **SC-002**: 100 % of issue rows have the 3 columns; 100 % of pictures (within the image limit) show only the layers
  listed for their issue type.
- **SC-003**: board1 (U14_U26, U21_J25) and test1 PCIe reports: counts per severity equal the review data
  (U21_J25 2 HIGH / 16 MEDIUM ...; PCIe 19 HIGH / 46 MEDIUM / 24 INFO).
- **SC-004**: Report build time on board1 is not longer than today's HTML report by more than 20 %.

## Assumptions

- "Template" = the report's standard structure and look, the same for every board; wording of the danger verdict
  above is the default (changeable at clarify).
- Severity per issue stays as computed by the review checks (HIGH / MEDIUM / INFO); the summary verdict is derived
  from it, no new thresholds.
- Picture margin and size come from template rows (`review.zoom_margin` exists, 1.0 mm); a new row only if needed.
- The 025 review gate (separate branch) stores a verdict; this report shows it when present and works without it.
- Pictures are drawn from board data (as today), not exported from AEDT.
- Test boards: copies only (board1, test1). Version: minor (report format change), after 025.
