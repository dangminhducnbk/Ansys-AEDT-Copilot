# Feature Specification: One page per request — layout review (NOT OK points to resolve) + settings, full screen

**Feature Branch**: `main` (no branch; repo owner works on main) | **Created**: 2026-11-17 | **Updated**: 2026-11-17 (round 2)

**Status**: Draft — mock waiting for the user's review: `mock/review_page_demo_boarda.html` (REAL board BOARDA PCIE_HSA_HSB,
15 NOT OK points; built by `mock/build_demo.py <request folder>` from the request's config page + review record + old
review report + board stackup; not committed: 31 MB). `mock/review_page_demo.html` = round 1 (fake board, superseded).

**Input**:
- Round 1: "tôi muốn bổ sung ở bước review layout, sẽ có ảnh snag của khu vực trace cần cut, có stackup, các cấu trúc
  giống board thật 100%. Trên đó sẽ có các điểm NOT OK dưới dạng đánh dấu để người dùng rê chuột vào xem. Trên biển
  đánh dấu khi bấm vào sẽ hiển thị chi tiết NOT OK là gì, người dùng có thể nhấn resolve để xác nhận có thể bỏ qua bug
  này. Chỉ khi tất cả các NOT OK được resolve thì mới cho save lại file để chạy tiếp. Có thêm 1 nút resolve all để
  người dùng có thể resolve toàn bộ."
- Round 2: "Tôi muốn file review và settings sẽ merge lại thành 1 html. Mỗi channel cần cut sẽ gồm 1 tab review layout
  và 1 tab settings. Mục review layout, tại các NOT OK khi nhấn ra sẽ hiện ra chi tiết như file review cũ cho từng
  section review. Ở mục này bạn thiếu hình biểu diễn số đo được tế. Thứ 2 là cửa số quá nhỏ, bạn cần cho full màn
  hình để thể nhìn rõ hơn." + "Hình chưa có fit zoom khi double click vào hình. Ở mục review layout, chỉ khi nào tất
  cả bug được resolve thì tab settings mới được unlock để settings. Ngoài ra phải có nút resolve all cho tất cả các
  NOT OK." + (topology screenshot) "Mục topology này vẫn phải để lại trong review."

## Context

- Since 5.2.0 (039) the steps are: `isim_layout_review` → M0 (review report file per channel) → Q0 answered in chat →
  `isim_review_answer` → config page (038 / 040, M1) → Save + "xong" → `isim_config_check` → `isim_go`.
- The user handles two files (review report, config page) and answers Q0 in chat between them.
- The review report (033 / 043) is a static document: one picture per NOT OK point, read top to bottom; the user cannot
  see the whole cut area with all layers, nor mark which NOT OK points were looked at and accepted.

This feature merges both into **one page per request**, full screen. Each channel has two tabs: **Review layout**
(board picture of the cut area with a marker per NOT OK point; the details of a point = the old report row with its
picture and measured values; Resolve / Resolve all) and **Settings** (the config page content). The Settings tab of a
channel unlocks only when its NOT OK points are resolved; Save only when every point of every channel is resolved.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One full-screen page, two tabs per channel (Priority: P1)

After the review step the user gets ONE page for the request. It fills the browser window. A channel selector at the
top; for the selected channel two tabs: "1 · Review layout" (with resolved / total count) and "2 · Settings".

**Independent Test**: run the review step on a board copy with known NOT OK points (BOARDA PCIE_U14_J25); one page is
written; the Review layout tab has one marker per NOT OK point; the Settings tab shows the same content as the config
page of 5.5.0.

**Acceptance Scenarios**:

1. **Given** a request with 2 channels, **When** the page opens, **Then** the channel selector shows both with their
   resolved count (e.g. "0/15") and the Review layout tab of the first channel is shown.
2. **Given** a 1366 × 768 or 1920 × 1080 window, **Then** the page uses the whole window (no fixed-width column, no
   page scroll); the board picture takes all the space left by the detail panel and the layer panel.
3. **Given** the Settings tab, **Then** it holds every setting of the config page (content, cut area, component model,
   analysis setup, model extents) with the same behaviour.

---

### User Story 2 - See every NOT OK point on the real board picture (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a review with N NOT OK points, **Then** the picture shows N markers (points closer than ~28 px on screen
   grouped into one "k points" marker; clicking it zooms in), numbered as the review record.
2. **Given** the layer panel (config page Layers table + stackup thickness / dielectric rows), **When** a layer is
   switched off / on, **Then** its copper disappears / appears.
3. **Given** the picture, **When** the user zooms (wheel) or pans (drag), **Then** markers stay on their points; **When**
   the user double-clicks the picture, **Then** it returns to the whole cut area (same as the config page).

---

### User Story 3 - Open a NOT OK point: details as the old report (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a marker, **When** the mouse rests on it, **Then** a tip shows point id, check(s), net, measured value.
2. **Given** a marker or a list row, **When** clicked, **Then** the detail panel shows for each report row of that
   point: the section ("2.1 Routing", "2.2 Reference", "2.4 Via" ...) with its report id (RTE-01, REF-03, VIA-02 ...),
   "What this section checks" (collapsed), Issue / Recommendation, and **the report picture with the measured values**
   (e.g. serpentine overview + Detail A with W / A / G / c dimensions and the "must be ≤ / ≥ → OK / NOT OK" lines;
   reference panels per plane; via picture), location; plus a stackup cross-section at the point. Content identical
   to the old report row (same sentences, same pictures, same numbers).
3. **Given** the detail panel, **Then** the board picture centres on the point, its layer becomes active and its
   reference / via layers are switched on; "‹ / ›" walk the points in report order.
4. **Given** the unit switch (mil / µm / mm), **Then** every length in the detail panel (text and measured values)
   is shown in that unit.
5. **Given** an open point, **When** the user presses "Print issue to image", **Then** a PNG is saved: header with the
   issue, left = overview of the cut area with the issue circled and an arrow from the circle to the right picture,
   right = zoom at the issue. No point id (1.1, 1.9...) is drawn on the image.

5. **Given** the Review layout tab, **When** the user switches the picture to "Topology per pair", **Then** the old
   report's "Signal routing per pair" boxes are shown unchanged (one box per pair: top view with zoom lock,
   cross-section from first pin to last pin with via labels, length table trace + via per layer); "Board picture"
   switches back; opening a NOT OK point switches back to the board picture.

---

### User Story 4 - Resolve one, or Resolve all (Priority: P1)

**Acceptance Scenarios**:

1. **Given** an open point, **When** "Resolve" is pressed (optional note), **Then** it is marked resolved (green
   marker, counters +1) and the next unresolved point opens.
2. **Given** a resolved point, **When** "Unresolve" is pressed, **Then** it is NOT OK again (and the channel's Settings
   tab locks again).
3. **Given** unresolved points, **When** "Resolve all NOT OK" is pressed (footer, and in the point list), **Then** a
   confirmation shows the number of points per channel; on confirm EVERY NOT OK point of every channel is resolved.

---

### User Story 5 - Settings locked until resolved; Save only when all resolved (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a channel with unresolved NOT OK points, **Then** its Settings tab is locked (🔒, tip "resolve the k
   NOT OK point(s) of <channel> first") and cannot be opened.
2. **Given** all NOT OK points of the channel resolved, **Then** its Settings tab unlocks.
3. **Given** at least one unresolved point in any channel, **Then** Save is disabled and its tip lists what is left
   per channel.
4. **Given** everything resolved, **When** Save is pressed, **Then** the page (resolutions + settings) is saved in
   place through the local save service (040), else as a download (038).
5. **Given** a saved page, **When** the user tells Claude "xong", **Then** the check step runs (M2 / Q2) and refuses
   (with the reason) if the page is missing, has unresolved points, or was built from an older review.
6. **Given** a channel with 0 NOT OK points, **Then** its Settings tab is unlocked from the start.

### Edge Cases

- Review measured again (board changed): old resolutions do not count; a new page is written; points with the same
  check + net + location (within 0.01 mm) are shown pre-ticked as a suggestion only (still need Save).
- More than 100 points in a channel: grouping keeps the picture readable; zooming in splits groups.
- A point outside the cut area: shown at the area edge, still must be resolved.
- A NOT OK point with no report row (rule without picture): the detail shows Issue / Recommendation / measured value
  from the review record.
- Unresolving a point while the Settings tab is open: the view returns to Review layout, settings already typed are
  kept.
- The user rejects the review in chat ("không" / "no"): the request is stopped as in 039; no page needed.
- Old requests (before this feature): unchanged (separate review report + Q0 + config page).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** The review step writes ONE page per request (replaces the separate config page for new requests); the
  review report file is still written unchanged.
- **FR-002** The page fills the browser window at 1366 × 768 and above (header, channel selector, tabs, work area,
  footer; work area = detail panel | board picture | layer panel, the picture taking the remaining space).
- **FR-003** Per channel two tabs: Review layout (count resolved / total) and Settings (config page content, same
  fields, validation and behaviour as 5.5.0).
- **FR-004** Board picture = the config page snapshot drawing (copper of every layer, signal pink, GND blue, other
  nets grey, active layer emphasised; component boxes; cut region outline); wheel = zoom, drag = pan, double-click =
  whole cut area, buttons + / − / Fit.
- **FR-005** Layer panel = config page Layers table + copper thickness and a dielectric row (material, thickness) per
  layer; layers of the selected point highlighted.
- **FR-006** One marker per NOT OK point (report point id, colour by check family as the 043 frames, resolved = green
  ✓); close markers grouped.
- **FR-007** Point details = the old report row(s) of the point, unchanged content: section name + report id, section
  "checks" text, Issue / Recommendation, picture with measured values and limits, location; plus stackup
  cross-section at the point; plus measured value text of the review record.
- **FR-007a** Topology per pair (033 routing boxes: top view, cross-section, length table) kept in the Review layout
  tab as a second picture view ("Board picture" | "Topology per pair"), same content as the review report.
  Change vs the report (user 2026-11-17, applies to the review report too): series R / C / L parts ON THE NETS OF
  THE PAIR are drawn in the top view as their body rectangle (component box from the board) instead of two pin dots
  (parts of other pairs are not drawn; label stays "<refdes> (<layer>)"). Value and package are written in the
  cross-section, in the label row under the drawing at the part's position: "<refdes>" / "<value> - <package>"
  (e.g. "C951" / "220nF - 0402"; value from the netlist / BOM, package from the part name), never over the drawing.
- **FR-007b** "Print issue to image" (camera icon) in the point detail header, right of the point id / status line
  (NOT OK and resolved): saves one PNG
  `<channel>_<point id>_issue.png` = header, black text, bold labels: **Issue:** <check(s)> (no 'NOT OK'); **Layout version:**
  <board name>; **Issue description:** short but complete (Issue sentence(s) with net / layer / planes + channel
  (ends) + location), wrapped; captions centred under each picture: "Overview" (left) and "Zoom in" (right)
  + left: overview of the whole cut area with the issue circled (dashed box = zoom area) and a red arrow from the
  circle whose tip stops at the left edge of the zoom picture (never inside it) + right: zoom at the issue (point in the middle, 043 frames, scale bar, active / shown
  layers in the caption). The point id (1.1, 1.9...) is NOT drawn anywhere on the image (only in the file name). Same layers as the
  page shows at that moment; lengths in the page unit. Made in the browser (no AEDT, no server).
- **FR-008** Units mil / µm / mm (default mil) apply to all lengths of the page, detail panel included.
- **FR-009** Resolve / Unresolve per point with optional note; "Resolve all NOT OK" resolves every NOT OK point of
  every channel after one confirmation.
- **FR-010** Settings tab of a channel locked while the channel has an unresolved NOT OK point.
- **FR-011** Save disabled until every NOT OK point of every channel is resolved; Save writes resolutions + settings
  (in place via the local save service, else download).
- **FR-012** Continuing past the page ("xong" → check) requires a saved page of this request, every point resolved,
  resolutions bound to the current review of every channel (same measured time). Enforced in code (server +
  package), not only in the guide.
- **FR-013** Resolutions (point id, check, net, location, time, note) are stored in the request and listed in later
  answers (M2 / Q2: "N NOT OK points resolved by the user").
- **FR-014** The page works offline (no external files) in Chrome / Edge.

### Key Entities

- **Request page**: request id, channels; per channel: review data (picture layers, markers, report rows, stackup,
  review measured time) and settings (config page data + state).
- **NOT OK point**: id, channel, check(s), net(s), layers, location, measured value, report row(s) (section, report
  id, description, picture).
- **Resolution**: point id, check, resolved, note, time; bound to the review measured time.

## Success Criteria *(mandatory)*

- **SC-001** On the BOARDA PCIE_U14_J25 copy every NOT OK point has exactly one marker at its location (0 missing,
  0 extra) and its detail shows the same report row(s) as the old report (same report ids, same numbers).
- **SC-002** At 1920 × 1080 the board picture is at least 50 % of the window area; at 1366 × 768 nothing needs page
  scrolling.
- **SC-003** A user can read and resolve 15 points in under 5 minutes; "Resolve all" + open Settings + Save in under
  30 s.
- **SC-004** 100 % of attempts to open a locked Settings tab or to continue with an unresolved, unsaved or outdated
  page are refused with a reason.
- **SC-005** Page with 2 channels opens in under 3 s on the user's PC; zoom / pan stays fluid.

## Assumptions

- Board data for the picture = the layout snapshot already used by the review / config page (no extra AEDT run).
- "Giống board thật 100 %" = the board's own geometry in 2D (top view + cross-section), not a 3D model.
- The chat question Q0 ("Review layout ổn, chuyển sang config không?") is dropped for new requests: resolving every
  point on the page replaces it; the user still says "xong" after Save (same as 038 / 040).
- Resolving does not change the review record or the report.
- The Settings tab lock is per channel (a channel's settings unlock when that channel's points are resolved); Save
  needs all channels resolved.
- One user per request (no concurrent editing).
