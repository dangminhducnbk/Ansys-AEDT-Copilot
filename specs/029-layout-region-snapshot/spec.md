# Feature Specification: layout_region on the layout snapshot

**Feature Branch**: `029-layout-region-snapshot` (worktree branch `claude/029-layout-region-snapshot-b47d85`)

**Created**: 2026-11-11

**Status**: Draft

**Input**: Parent session task: "`layout_region` (layout edit read tool) reads the board from the layout snapshot
instead of opening EDB each time — the last part of snapshot phase 2 (027 clarify Q1 A put layout_region later).
Output identical to the live read for the same box; snapshot window extended / rebuilt when the box is outside the
cached window; stale board → rebuilt, never used stale; `layout_edit` still edits a COPY with EDB, its 'before'
region may come from the snapshot only if results stay identical (decide in plan, measure); template row to fall
back to live (like `snapshot.use_for_preview`)."

## Clarifications

### Session 2026-11-11 (answers relayed by the parent session: "Theo đề xuất của bạn.")

- Q1: Equality of coordinates / images vs live? → A: identical. The snapshot stores the EDB original points (arc
  markers included) and converts arcs exactly like the live read; `region.json` equal number for number, PNG equal.
  Snapshot format changes (schema 2); older snapshots are rebuilt once automatically.
- Q2: Area cached for a box outside every cached window? → **B** (user correction, verbatim "Q1: A, Q2: B, Q3: A",
  replaces the first "theo đề xuất" answer A): build the WHOLE BOARD geometry once (first call slower on a big
  board), then every box is answered from it; any existing window (review / preview / board) that contains the box
  is reused. Full-board build time + size reported for B04 and board1.
- Q3: Board open in AEDT (`.lock`) with a valid snapshot? → A: the snapshot is used (board not opened); when a build is
  needed → live read + note (lock never touched).
- Plan decisions accepted: `layout_edit` "before" from the snapshot only if `result.json` / `changes.json` stay
  identical; template row `snapshot.use_for_region` default true.
- Decided by agent, user asleep ("bạn cứ chạy và tự làm tiếp, không cần hỏi tôi"): `layout_edit` "before" read
  KEPT on the snapshot — B04 stitch / neck / delete-via `result.json` + `changes.json` identical to the live read;
  it only reuses an existing snapshot window of the source board (never builds during an edit, so an edit without a
  prior `layout_region` costs nothing extra). Edit "after" read stays live (new file).

## Problem

Layout edit (PI / SI improvement on a COPY of a board) starts with `layout_region(board, box)`: the engineer and
Claude look at an area (polygons, traces, vias with ids, padstacks, PNG per layer) and write a plan. Every call opens
the board and converts it; on the B04 PI board the region read alone takes 25–40 s, and an improvement session
calls `layout_region` several times (different boxes, layers, nets). `layout_edit` reads the same area again
("before") right after copying the board: another 25–40 s.

The layout snapshot (023 / 027) already reads a board once into files and answers review / cut preview in seconds
with identical results. `layout_region` is the remaining reader.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Region read in seconds (Priority: P1)

The engineer asks for a region of a board (box, optional layers / nets). The result comes from the layout snapshot:
same summary, same `vias` list (ids), same padstacks / components, same `region.json` content and same PNG per layer
as a live read of the same box — without opening the board when the snapshot already covers the box.

**Independent Test**: board1 and an B04 copy: same box live vs snapshot → summary, vias, padstacks, components,
`region.json` compared (ids, counts, coordinates per FR-002), PNG compared; second call with the same / another box
inside the cached area does not open the board.

**Acceptance Scenarios**:

1. **Given** a valid snapshot whose cached area contains the box, **When** `layout_region` runs, **Then** the board is
   not opened and the result equals the live one (FR-002).
2. **Given** no snapshot, or a box outside every cached area, **When** `layout_region` runs, **Then** the snapshot is
   built / extended for the box (board opened read-only once) and the result equals the live one.
3. **Given** a board saved since the snapshot (stale), **When** `layout_region` runs, **Then** the snapshot is rebuilt
   first; stale data is never used.
4. **Given** the snapshot cannot be used (board open in AEDT and data missing, object not convertible, template row
   off), **When** `layout_region` runs, **Then** it reads live as before and the result says why (never silent).

---

### User Story 2 - layout_edit "before" without a second read (Priority: P2)

`layout_edit` copies the board and reads the area "before" the ops. When that read can come from the snapshot of the
source board with identical edit results, it does; otherwise it stays live. Editing, saving, the "after" read and the
checks stay on the COPY with EDB (unchanged).

**Independent Test**: `tests/layout_edit_b04.py` stitch + neck: `result.json` (ops, checks, summary) and
`changes.json` identical to 2.6.1 (times excluded); `read_before` time before / after measured.

**Acceptance Scenarios**:

1. **Given** a valid snapshot of the source board, **When** `layout_edit` runs, **Then** edit results / checks /
   changes are identical to the live "before" read (decision and measurement in the plan).
2. **Given** a plan that deletes vias (016), **When** it runs on an B04 copy, **Then** results are identical to 2.6.1.

---

### Edge Cases

- Board changed after the snapshot → stale → rebuilt (023 key rule: `edb.def` size + mtime).
- Box partly outside the board outline → same result as live (empty layers stay absent).
- Board open in AEDT (`.lock`): an existing valid snapshot is used (Q3 A, no board open); building one is
  refused → live fallback with a note (lock never deleted).
- Object the snapshot cannot represent → live fallback naming the ids (023 FR-021 rule).
- `layout_edit` "before" read on the COPY vs snapshot of the SOURCE: same content only because the copy was just made
  from that source; the plan decides whether this is used.
- Template row off → live as before 2.7 (no snapshot read / build).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `layout_region` MUST read the board from the layout snapshot when the template row allows it (default
  on); tool name and arguments unchanged.
- **FR-002**: Output MUST equal the live read for the same box: primitive / via / pin ids, nets, layers, types,
  counts, summary, `vias` list, padstacks, components; coordinates identical (arcs converted exactly like
  the live read, Q1 A); PNG per layer identical.
- **FR-003**: Box outside every cached window → the whole-board geometry is built once (Q2 B); a cached window
  containing the box (any scope) is reused; the board is opened read-only once for the build; never written.
- **FR-004**: Stale or missing snapshot is never used silently: rebuild, or live fallback with the reason in the
  result (`source`).
- **FR-005**: A template row (job scope, like `snapshot.use_for_preview`) switches `layout_region` back to live.
- **FR-006**: `layout_edit` keeps editing a COPY with EDB; its "before" read may use the snapshot only when results are
  identical (plan decision, measured on B04); `result.json` / `changes.json` of the B04 cases identical to 2.6.1.
- **FR-007**: The result reports the source (snapshot folder / built / reused, or live + reason) and the read time.
- **FR-008**: Guide `layout_edit` says `layout_region` uses the cached snapshot (first call builds it, then seconds)
  and what the engineer sees on fallback.

### Key Entities

- **Layout snapshot** (023 / 027): board index + windows cached per board key; gains what the region read needs
  (per FR-002: geometry as the live read converts it, padstack pad / antipad table, component boxes).
- **Region result**: summary per layer, `vias`, padstacks, components, `region.json`, PNG per layer, `source`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `layout_region` with a valid snapshot covering the box: ≤ 10 % of the live time on B04 (live 25–40 s).
- **SC-002**: 0 differences vs live in the comparison checks (board1 + B04 copy, per FR-002).
- **SC-003**: B04 stitch + neck and delete-via: results identical to 2.6.1; `read_before` time reported before / after.
- **SC-004**: Unit tests PASS; review / cut preview on the snapshot unchanged (board1 `review_check.py`,
  `preview_check.py` PASS if the snapshot format changes).

## Assumptions

- Checks run on COPIES of board1 / B04 only, one after another; originals never opened for writing.
- The snapshot format may be extended (new schema version → old snapshots rebuilt automatically, as 023 / 027).
- No MCP argument added (027 precedent: template row only).
- Version: minor (proposed 2.7.0); no release / tag / push in this feature session.
