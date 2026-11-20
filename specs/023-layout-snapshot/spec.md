# Feature Specification: Layout snapshot for fast review (phase 1)

**Feature Branch**: `023-layout-snapshot` (worktree branch `claude/023-layout-snapshot-6e40d0`; user merges)

**Created**: 2026-11-10

**Status**: Clarified

**Input**: User description: "Layout snapshot (digitized board) for fast review — PHASE 1 of docs/prd-layout-snapshot.md:
snapshot build + file cache + new MCP tool layout_snapshot + review_checks (design_review / isim_review) running on the
snapshot behind template row review.use_snapshot. Phase 2 consumers (022 cut preview, end check / gnd_decision,
layout_region) are out of scope (follow-up feature)."

Source: [docs/prd-layout-snapshot.md](../../docs/prd-layout-snapshot.md) (PRD, 2026-11-10).

## Problem

- Every layout review reads the board again from EDB, one object at a time, and throws the result away. Changing one
  threshold or re-running one check costs the full time again.
- Measured on a board1 copy (spike 2026-11-10, 2 channels U14-U26 + U21-J25, today's code, see table): **~100 s per
  review run** (EDB open 8–10 s + measure 86 s + close 2.5 s).

### Spike: where today's time goes (board1 copy, 2 channels)

| Phase | Time | Kind |
|---|---|---|
| Other-net copper on plane layers (`Board.other_prims`, walks every primitive of each plane layer through PyEDB) | 40.7 s | EDB read |
| Point-in-copper tests (`Copper.net_at`, 180 882 calls; incl. lazy index build 4.7 s) | 14.6 s | EDB call per point |
| Channel trace (components, nets, end types) | 12.4 s | EDB read |
| EDB open / close | 10.0 s / 2.6 s | EDB |
| Board model (stackup, GND copper, plane layers, GND vias) | 9.1 s | EDB read |
| Own-antipad tests (`Copper.voids_at`, 2 121 calls) | 4.8 s | EDB call per point |
| Collect channel traces / vias / pins | 3.1 s | EDB read |
| Via rows, trace stubs, lengths (pure Python) | 0.4 s | compute |

Conclusion: **> 99 % of the time is EDB access**, not computation. Pure sampling compute is negligible; the gain comes
from reading the board once into files and answering the point tests from that copy.

| Spike measurement (direct .NET reads, same board) | Result |
|---|---|
| Metadata of all 27 021 primitives (layer, net, type, bbox) | 2.8 s |
| Full outline + voids of the 579 primitives overlapping the 2-channel window (526 840 points, arcs as chords ≤ 1 µm) | 6.4 s |
| Position / net / def of all 47 189 padstack instances | 2.8 s |
| Build 2D polygons from that data | 0.6 s (2 needed a validity fix) |
| Same 180 882 point tests answered from the copy vs today's EDB answers | **0 differences** |
| Same 2 121 own-antipad tests | **0 differences** |

## Clarifications

### Session 2026-11-10

User answers (relayed by the parent session, verbatim "Q1–Q5 đều A"):

- Q1: Phase 2 consumers (022 cut preview, end check / `gnd_decision`, `layout_region`) → a later feature. → Assumptions.
- Q2: Geometry format → WKB + JSON with `schema_version` (portable, not tied to the shapely version). → FR-007.
- Q3: Primitive that cannot be converted inside the window → the WHOLE review falls back to the live path with a warning
  naming the primitive ids (never silent). → FR-021.
- Q4: HTML report → stays live in phase 1; snapshot numbers must equal the HTML numbers. → FR-015.
- Q5: Background build → the guide tells Claude to call `layout_snapshot build` (task) after `isim_trace`; a review
  builds the snapshot itself when missing / stale / too small. No code trigger in `isim_trace`. → FR-019, FR-012.
- Accepted with the questions: 2-tier snapshot (board index + window geometry), window margin default 5 mm, key on
  `edb.def` only (not `edb.def.tmp`), `cut_board/review.py` measuring code unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Re-run a review in seconds (Priority: P1)

An engineer reviews a board (`design_review`) or an interface (`isim_review`). The first run reads the board once and
keeps a snapshot. Later runs (other threshold, one check only, next day) reuse the snapshot and answer in seconds with
exactly the same items, points and numbers as a live review.

**Why this priority**: it is the whole value of the feature; today every run costs ~100 s on board1.

**Independent Test**: run `design_review` twice on a board1 copy; the second run reuses the snapshot, takes ≤ 10 % of
today's time, and its output equals the live output.

**Acceptance Scenarios**:

1. **Given** a board with no snapshot, **When** the engineer runs `design_review`, **Then** a snapshot is built, the
   review runs on it, and items / points / via rows / routing data equal today's live result.
2. **Given** a valid snapshot covering the channels, **When** the engineer re-runs the review (any thresholds, any
   check subset), **Then** the board is not opened and the run takes ≤ 10 % of today's time.
3. **Given** `review.use_snapshot = false`, **When** the engineer runs a review, **Then** today's live path runs
   unchanged.

---

### User Story 2 - Build / inspect snapshots explicitly (Priority: P2)

Claude starts a snapshot build in the background (e.g. right after `isim_trace`, while the content is discussed at
Gate A) with the new tool `layout_snapshot`, and can ask its status or list snapshots of a board.

**Why this priority**: removes the build time from the engineer's waiting time; gives visibility (counts, build time,
warnings, stale or not).

**Independent Test**: `layout_snapshot(op=build, aedb, nets)` returns a task; `task_result` gives the snapshot report;
`op=status` says valid / stale / missing; `op=list` lists snapshots of the board with size and date.

**Acceptance Scenarios**:

1. **Given** a board and a net list, **When** `layout_snapshot build` runs, **Then** a snapshot is written only under
   `<board folder>/Ansys AEDT Copilot/snapshots/`, with a report (counts per kind / layer, time per phase, warnings).
2. **Given** a snapshot, **When** the board changes (`edb.def` size or mtime), **Then** `status` reports it stale and a
   review rebuilds it (never uses it silently).
3. **Given** a board locked by AEDT (`.lock`), **When** a build is requested, **Then** it stops with a message and
   never deletes the lock.

---

### User Story 3 - Developer adds a check without PyEDB (Priority: P3)

A developer writes a new review check against the snapshot data (layers, copper by layer / net, vias, pins,
components) and tests it offline with a small fake snapshot.

**Independent Test**: unit tests build a fake snapshot in memory and run every existing check on it without EDB.

### Edge Cases

- Window too small for a later request (other channels, larger zoom margin) → the snapshot is not used; a larger one is
  built (never a partial answer).
- Two builds of the same snapshot at once (review + background build) → build lock per snapshot; the second caller
  waits for the first and reuses its result.
- Board read by another process at the same time (isim_trace + background build) → read-only opens must work together
  (verified in implement); otherwise builds are serialized with the lock.
- Primitive that cannot be converted (unknown shape, conversion error) → listed in the report (id + layer + net); the
  review does not silently drop it (handling: Clarifications).
- Old snapshot schema after an upgrade → treated as stale, rebuilt.
- Board with no GND copper / no plane layer → same result as today (check `reference` reports its error).
- Snapshot folder deleted by the user → rebuilt on the next review.

## Requirements *(mandatory)*

### Functional Requirements

**Snapshot content** (enough to run today's review checks exactly; units mm in files)

- **FR-001**: Board level (once per board version): stackup (metal layers top → bottom, elevation, thickness),
  per-layer largest reference-net polygon area over the WHOLE board (plane-layer rule stays board-wide even when the
  geometry is a window), net list with power / ground flag, components (refdes, part, type, pin count, placement layer,
  pins in board order with net, layer range, absolute position), all padstack instances (id, net, def, absolute
  position as today's API returns it, layer range, pin flag, component), reference-net via / pin positions board-wide
  (nearest GND via stays board-wide), metadata of every primitive (id, kind, layer, net, void flag, bbox) and the
  primitive / instance order of each net.
- **FR-002**: Window level: full outline + voids of every primitive whose bbox overlaps the window (arcs approximated
  with a chord error ≤ `snapshot.arc_tol_um`, default 1 µm), trace centerlines / width / length exactly as today's
  review reads them, padstack definition sizes used by today's via label, backdrill data and pin boxes needed by the
  end type.
- **FR-003**: Window = bbox of the requested nets + `snapshot.window_margin_mm` (default 5 mm; today's review copper
  window is channel bbox + 1 + `review.zoom_margin_mm` + 2 mm = 4 mm at default). Scope `board` = whole board.
- **FR-004**: A request is served by an existing valid snapshot when its window contains the request window (a
  board-scope snapshot contains every window).

**Cache and validity**

- **FR-005**: Location `<board folder>/Ansys AEDT Copilot/snapshots/<board stem>/<cell>_<key>/`; never inside the
  `.aedb`; the board files are never written.
- **FR-006**: Key = board path + cell + `edb.def` size + mtime + schema version (+ arc tolerance for geometry). The
  0-byte `edb.def.tmp` that EDB touches on every open is NOT part of the key. Any mismatch = stale = rebuilt; never used
  silently.
- **FR-007**: Versioned format with `schema_version`; metadata JSON, geometry as WKB.
- **FR-008**: Build lock per snapshot folder; board `.lock` → build refused with a message; the lock is never deleted.
- **FR-009**: Old snapshots are kept; `list` shows them; removing one needs the user's go (not part of this feature's
  tool: the user deletes the folder).

**Build**

- **FR-010**: Build reads EDB through direct .NET calls with cached layer / net objects (no per-object PyEDB wrapper in
  loops) and writes `snapshot.json`: counts per kind / layer, time per phase, board key, warnings.
- **FR-011**: Build runs as a task (`task_result`) when started from the MCP tool.

**Review on the snapshot**

- **FR-012**: `review_checks` (`design_review`, `isim_review`, CLI `review-measure`) run on the snapshot when template
  row `review.use_snapshot` is true (default true). Check code, thresholds, severity rules and report wording do not
  change. The snapshot is built automatically when missing / stale / too small.
- **FR-013**: `review.use_snapshot = false` → today's live path, unchanged (kept for comparison until one release after
  acceptance).
- **FR-014**: The review output says which source was used (`source: snapshot | live`, snapshot folder, built or
  reused) and the arc tolerance.
- **FR-015**: `design_review(html=true)` / `isim_review(html=true)`: the HTML report stays on the live path in phase 1; measured numbers come from the snapshot and must equal the HTML numbers.

**Interface (Principles IX / X)**

- **FR-016**: New MCP tool `layout_snapshot` with ops `build` (aedb, cell?, nets or scope=board, margin?), `status`
  (same arguments → valid / stale / missing + report), `list` (board → snapshots). Safety `read` (writes only to the
  Copilot output folder). Catalog entry + contract + tests (010 registration rules).
- **FR-017**: CLI `python -m aedt_copilot snapshot --op=build|status|list --args-file=`.
- **FR-018**: Existing tools keep names and arguments; `design_review` / `isim_review` get an optional `snapshot`
  argument (`auto` default | `off`). No breaking change → minor version.
- **FR-019**: Guides `review_measure` and `interface_sim` say when a snapshot is built / reused, how to start it in the
  background after `isim_trace`, and what stale means.
- **FR-021**: A primitive inside the window that cannot be converted → the snapshot records it; a review on that
  snapshot runs the live path instead and warns with the primitive ids.
- **FR-020**: Template rows `review.use_snapshot`, `snapshot.window_margin_mm`, `snapshot.arc_tol_um` in
  `templates/autocut_template.csv` (Principle III).

### Key Entities

- **Board index**: stackup, nets, components + pins, padstack instances, primitive metadata, per-net order, board-wide
  GND area per layer and GND via positions. One per board version (key).
- **Window geometry**: polygons with voids, traces, padstack definition sizes, pin boxes, backdrill for one window.
- **Snapshot report** (`snapshot.json`): key, scope / window, counts, phase times, warnings.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a board1 copy (`tests/review_check.py`, 2 channels) and the test1 PCIe interface review, the snapshot
  path gives identical item counts, ids, severities, points, via rows and routing data as the live path captured
  before the change (golden). Coordinates and measured distances identical (both paths sample at the same points); any
  difference is listed with its reason and must be within the arc tolerance.
- **SC-002**: Re-running a review on a valid snapshot takes ≤ 10 % of today's time (board1: ≤ 10 s vs ~100 s).
- **SC-003**: Build time (board index, window, board scope) and re-run time are measured for board1 and test1 and
  recorded in this spec (Results section).
- **SC-004**: Board files unchanged after build and review (checksums of `edb.def` before / after).
- **SC-005**: A stale snapshot is never used: unit test (key change → rebuild) and AEDT check (touch board → rebuild).
- **SC-006**: `tests/regression.py` and `tests/isim_check.py` PASS with references unchanged; 0 unit test failures.

## Assumptions

- Phase 1 consumers only: review checks. 022 cut preview, end check / `gnd_decision`, `layout_region` read EDB as today
  (follow-up feature; files under edit by 022 patch 2.1.1 are not touched).
- Today's `cut_board/review.py` measuring functions stay unchanged; the snapshot feeds them the same inputs.
- shapely 2 is available in the repo venv (already used by layout_edit).
- Snapshot size on disk is acceptable (window ~ tens of MB at most); no automatic clean-up.

## Results (2026-11-10, copies, AEDT 2026 R1 non-graphical)

| Check | Result |
|---|---|
| SC-001 board1 `tests/review_check.py` | PASS: live, snapshot (build), snapshot (reuse) identical to golden `pre023_review_board1.json` (CPHY_U14_U26 24 items / 0 points, CPHY_U21_J25 29 items / 11 points; ids, severities, coordinates, via rows, routing, summary text); snapshot = numbers of the live HTML run; isim_review + decide OK |
| SC-001 test1 `tests/snapshot_check.py` | PASS: PCIE_U14_J25 identical to golden `pre023_review_test1.json` (19 HIGH / 46 MEDIUM / 24 INFO, 27 points) live, after build, re-run, after board change |
| SC-004 | `edb.def` sha1 unchanged (board1, test1) |
| SC-005 | test1: touch `edb.def` → status `stale` → rebuilt (new key folder), result = golden; unit tests for key / stale |
| Concurrency (review note 5) | test1: background `snapshot --op=build` in another process while a live review opens the same board: both OK, results = golden |
| SC-006 | `tests/regression.py` PASS on a fresh board1 copy (24 ports, 126 GND vias, planes 901-923 mm², pin shift 0.21 mm, arc 30, U26 enlarged 0.16 = 2.1.0 reference); `tests/isim_check.py` PASS; 402 unit tests OK |
| Unsupported shapes | 0 on board1 / test1 windows and test1 board scope. GEOS-invalid rings (kept as read, not repaired): board1 window 10, test1 window 26 — results still identical to golden |

### Timing (SC-002, SC-003)

| Board (copy) | Live review | Snapshot first run (index + window build + measure) | Re-run on snapshot | Re-run / live |
|---|---|---|---|---|
| board1, 2 channels | 81.7 s | 42.5 s | 2.0 s | 2.5 % |
| test1, PCIe U14-J25 | 59.2 s | 37.6 s (`layout_snapshot build`) + 1.4 s review | 1.4 s | 2.4 % |

| Build phase | board1 | test1 |
|---|---|---|
| Board index (EDB open ~8 s, 27 021 / 23 536 primitives, 47 189 / 52 669 instances, components, plane areas) | ~20 s | ~22 s |
| Window geometry (board1 5 304 prims / 1.11 M points; test1 3 146 prims / 0.46 M points) | 12.4 s | 7.6 s |
| Pin boxes + backdrill (board1 2 632 pins / 1 608 vias; incl. 7 s LayoutInstance) | 8.1 s | 8.1 s |
| Window scope=board (test1: 12 793 prims, 2.93 M points, 18 124 pins, 13 079 vias; index reused) | — | 55.8 s |
