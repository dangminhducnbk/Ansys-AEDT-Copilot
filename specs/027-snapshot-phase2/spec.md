# Feature Specification: Layout snapshot phase 2 (more steps read the cached board)

**Feature Branch**: `027-snapshot-phase2` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-10

**Status**: Draft

**Input**: User: "Sau đó là C" — option C = "Layout snapshot phase 2: cut preview, end check, layout_region chạy trên
snapshot cho nhanh". Source: [docs/prd-layout-snapshot.md](../../docs/prd-layout-snapshot.md) FR-22 / FR-23 and
[023 spec](../023-layout-snapshot/spec.md) Q1 / Q4 (phase 2 consumers deferred to a follow-up feature).

## Problem

Phase 1 (2.2.0) reads the board once into a layout snapshot; the review checks run on it in seconds. Other steps
still open the board in AEDT/EDB every time:

| Step | Today | Cost |
|---|---|---|
| Layout review HTML report (`design_review html=true`, `isim_review html=true`) | measures the board LIVE again after the snapshot review | ~90 s on board1 for 2 channels, on every report |
| Cut preview (`isim_cut_preview`, Gate A) | opens the board, computes the cut extent, finds end GND pins, draws the scene | EDB open (~10 s) + extent + scene on every factor change |
| `layout_region` (layout edit) | opens the board, converts the region | EDB open per call |

The engineer iterates on the cut preview (change an end factor, look again) and asks for review reports; each
iteration waits for the board to open.

## Clarifications

### Session 2026-11-10

- Q1: Which steps are in this feature? → A: HTML review report + cut preview (largest waits); `layout_region` is a
  later feature (US3 out of scope).
- Q2: Cut extent on the snapshot? → A: take AEDT's extent once per (nets, factors) and cache it in the snapshot:
  preview identical to the real cut; a NEW factor opens the board once (then cached).
- Q3: Equality vs live? → A: numbers / ids / severities / end GND results identical; pictures may differ slightly
  (arcs as chords ≤ 1 µm).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review HTML report in seconds (Priority: P1)

After the review ran on the snapshot, the engineer asks for the HTML report. It is built from the same snapshot, in
seconds, with the same numbers as the review it shows.

**Independent Test**: board1 U14_U26 + U21_J25: HTML from the snapshot vs today's live HTML: same summary counts,
same rows / indexes, same severities; build time ≤ 10 % of the live build once the snapshot exists.

**Acceptance Scenarios**:

1. **Given** a valid snapshot of the board, **When** the HTML report is asked, **Then** the board is not opened and
   the report equals the live one (per Q3).
2. **Given** a snapshot missing a needed area (window too small), **When** the report is asked, **Then** the snapshot
   is extended or the report falls back to live with a visible warning (never silent).
3. **Given** a stale snapshot (board saved since), **When** the report is asked, **Then** it is rebuilt first.

---

### User Story 2 - Cut preview without opening the board (Priority: P1)

At Gate A the engineer changes an end factor and looks at the preview again. The preview is drawn from the snapshot.

**Independent Test**: board1 CPHY_U14_U26 + CPHY_U21_J25 and test1 PCIE_U14_J25: preview from the snapshot vs live:
same end GND result per end (met / enlarged + factor), same extent area within tolerance (per Q2), same images
content; a second preview with another factor runs without opening the board (per Q2).

**Acceptance Scenarios**:

1. **Given** a valid snapshot covering the interface, **When** `isim_cut_preview` runs, **Then** end GND results,
   extent area / size and images are produced from the snapshot.
2. **Given** the snapshot result, **When** the interface is cut later, **Then** the cut uses the real board (as
   today) and the cut extent equals the previewed one (or the difference is reported, per Q2).
3. **Given** no snapshot or a stale one, **When** the preview runs, **Then** it builds / rebuilds the snapshot or runs
   live as today with a note.

---

### User Story 3 - layout_region from the snapshot (OUT OF SCOPE — Q1 A, later feature)

`layout_region` (layout edit) reads the region from the snapshot instead of opening the board.

**Independent Test**: B04 / board1 region: same primitives, nets, voids, vias (ids) as the live read.

---

### Edge Cases

- Board changed between snapshot and step → stale → rebuild (023 key rule), never used silently.
- Region / interface outside the snapshot window → extend the window or fall back live with a warning.
- Snapshot cannot represent an object (023 FR-021) → live fallback with the object ids named.
- The cut itself, apply, merge, end check of the CUT design stay on EDB (they change or read the cut design, not the
  board snapshot).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The layout review HTML report MUST be built from the snapshot when one is valid; numbers / ids /
  severities equal the snapshot review it accompanies (and the live report, per Q3).
- **FR-002**: `isim_cut_preview` MUST read the board from the snapshot: end GND pin detection, end region growth,
  scene drawing; the extent per Q2.
- **FR-003**: `layout_region` stays live (Q1 A; later feature).
- **FR-004**: A stale or missing snapshot is never used silently: rebuild, or live fallback with a warning in the
  result.
- **FR-005**: Tool names and arguments unchanged; the existing `snapshot` option (`auto` / `off`) applies to the new
  consumers; `off` = live as today.
- **FR-006**: The cut / apply / merge results are unchanged (regression references of board1 and test1 unchanged).
- **FR-007**: Guides (`review_measure`, `interface_sim`, `layout_edit`) say which steps use the snapshot and what the
  engineer sees on fallback.

### Key Entities

- **Layout snapshot** (023): board geometry cached per board key; gains what the new consumers need (component
  bodies / pin pads for the scene, cached extents per Q2).
- **Consumer**: a step reading the snapshot through the read-only board look-alike, with live fallback.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: HTML report on board1 (2 channels) with a valid snapshot: ≤ 10 % of the live time (~90 s today).
- **SC-002**: Repeated cut preview with a valid snapshot: ≤ 10 s per call on board1 (per Q2 for a new factor).
- **SC-003**: 0 differences vs live in the comparison checks (counts, ids, end results; extent per Q2; images per Q3).
- **SC-004**: board1 `regression.py`, `isim_check.py`, `preview_check.py`, test1 `pcie_check.py` unchanged.

## Assumptions

- Phase 1 snapshot format (023: index.json + window WKB, schema_version) is extended, not replaced; a new
  schema_version rebuilds old snapshots automatically.
- Checks run on board1 / test1 COPIES only, one after another.
- Version: minor (2.6.0).
