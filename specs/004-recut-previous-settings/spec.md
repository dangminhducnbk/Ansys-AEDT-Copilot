# Feature Specification: Re-cut from previous settings

**Feature Branch**: `004-recut-previous-settings` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User request 2026-11-06 (relayed by the parent session, approved there): "cut lại X như lần trước". The
tool finds earlier interface-simulation runs of the same workspace for that interface (or takes a request id / a
path, also a file copied from another PC), loads the old content + settings + end handling, re-traces on the current
board and shows ONLY the differences, then runs the normal gates (A content, B settings pre-filled, C merge).
When the engineer agrees, ONE file `user_settings` stores ALL settings and the cut method of that run ("không nên
tạo ra quá nhiều file"). Same feature: HFSS setup arc step size (Advanced Meshing → circle and arc approximation)
default 30 deg → 10 deg, as a team-template row, applied in both flows and read back by the self-check.
User report: feature 003 tested for real, "khá đạt yêu cầu".

## Clarifications

### Session 2026-11-06

- Q: Where is the `user_settings` file and what does it cover? → A: ONE file per request, covering every interface of
  the request: `<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/user_settings.json`. A re-cut finds it
  through the request registry or the engineer gives its path (also a copy from another PC). No copy beside the
  workspace.
- Q: Which existing per-interface files does it replace? → A: `settings.json` and `settings.md` are no longer
  written. `content.md`, `ends.md` (tables for the engineer) and `state.json`, `stage1.json`, `ends.json`,
  `result.json` (needed by code) stay.

## Problem

- A second cut of the same interface (new board revision, new sweep, lost design) today repeats the whole 003
  dialogue: the engineer re-types nets, ends, series parts, cutout values, end handling and sweep values.
- What was agreed lives in several files per interface (`state.json`, `content.md`, `ends.json`, `ends.md`,
  `settings.json`, `settings.md`, ...); there is no single file the engineer can keep, copy to another PC and
  hand back to the tool.
- AEDT default arc step 30 deg gives a coarse mesh of round pads / vias / arcs; the team wants 10 deg on every cut.

## User Scenarios & Testing *(mandatory)*

Actors: **engineer** (team user, talks to the agent in Claude desktop), **agent** (follows `guides/interface_sim.md`).

### User Story 1 - Re-cut an interface "like last time" (Priority: P1)

The engineer says "cut lại CPHY_U14_U26 như lần trước". The agent lists the earlier runs of that interface for this
workspace (date, sweep, last step); the engineer picks one (or the agent uses the only one). The tool re-traces the
interface on the current board and shows only what changed. With no change the engineer just says "đồng ý" at each
gate; cut, end check, apply and merge run as in 003 with the old values pre-filled.

**Why this priority**: the main reason for the feature; saves the whole content / settings dialogue.

**Independent Test**: on a board1 copy with a finished 003 request, start a re-cut of CPHY_U14_U26 from it: 0
differences are shown, settings are pre-filled with the old values, the applied design has the same metrics as the
first run (ports, pins, GND vias, plane areas, pin shift) except the arc-step change of US3.

**Acceptance Scenarios**:

1. **Given** two finished runs of CPHY_U14_U26 for this workspace, **When** the engineer asks to cut it "như lần
   trước", **Then** the agent lists both (request id, date, sweep start / stop / step, last step) newest first and
   waits for a choice.
2. **Given** a chosen run and an unchanged board, **When** the tool re-traces, **Then** it reports "no difference"
   and gate A needs only the engineer's go.
3. **Given** the board changed (net added / removed, end pin changed, series part added / removed, board file
   size / time changed), **When** the tool re-traces, **Then** each difference is listed with old and new value and
   gate A waits for the engineer's resolution of each.
4. **Given** the cut is done, **When** ends are checked, **Then** every end whose old handling no longer fits the
   new measurements (new unusual case, unusual case gone, handled end no longer unusual) is shown; ends that match
   keep the old handling.
5. **Given** gate B, **When** the settings table is shown, **Then** every value comes from the old run (source
   "previous run <id>") and the engineer can change any value before agreeing.

---

### User Story 2 - One file keeps everything agreed (Priority: P1)

After the engineer agrees, one `user_settings` file holds all that is needed to re-cut later: per interface the
content (nets, groups, ends, series parts, schematic resolutions), cutout / structural values, end handling and all
settings values, plus where they came from (workspace, board, request, time). The engineer can copy it to another PC
and give its path to the tool.

**Why this priority**: user requirement; the re-cut of US1 reads from this file, and it is the only file the engineer
needs to keep.

**Independent Test**: offline: after gates A and B of a fake request, the file exists, has every interface, and
loading it gives back exactly the agreed content, handling and values; a copy in another folder loads the same.

**Acceptance Scenarios**:

1. **Given** gate A or gate B is passed for an interface, **When** the tool saves, **Then** the `user_settings` file
   of the request holds the agreed content / settings of that interface (other interfaces untouched).
2. **Given** a `user_settings` file copied from another PC, **When** the engineer gives its path, **Then** the tool
   uses it as the previous run (board paths in the file are information only; the current workspace / board are
   used).
3. **Given** a `user_settings` file with a missing or wrong field, **When** loaded, **Then** the tool names the field
   and the expected value, and nothing is cut.
4. **Given** the files of a request folder, **When** compared with 003, **Then** no NEW file type is added per
   interface; files that `user_settings` makes redundant are removed from the process.
   (`settings.json` and `settings.md` are replaced by `user_settings.json`; see Clarifications.)

---

### User Story 3 - Finer arc step in every cut (Priority: P2)

Every cut design (interface simulation and the old Excel flow) gets HFSS arc step size 10 deg (team default, one
template row, editable like other settings); the self-check reads it back.

**Why this priority**: mesh quality; small change but changes results, so needs a new regression reference.

**Independent Test**: offline: the template row exists with default 10 and is validated (range); the self-check
compare reports a design with 30 deg as a mismatch. On a board1 copy (after the engineer's OK): the cut design's
setup shows arc step 10 deg; regression reference updated.

**Acceptance Scenarios**:

1. **Given** default settings, **When** a channel is cut (either flow), **Then** the HFSS setup arc step = 10 deg.
2. **Given** the engineer sets another value in the settings table / channel Excel, **When** applied, **Then** that
   value is used; a value outside the valid range is refused with the range.
3. **Given** an applied design, **When** the self-check runs, **Then** the read-back arc step equals the agreed value,
   else a mismatch is shown.

### Edge Cases

- No earlier run of the interface for this workspace → say so; offer the normal 003 process.
- Interface name of the old run differs from the new request → the engineer picks the old run by id / path; the new
  name follows channel name rules.
- Old run stopped before gate B (no settings) → content is reused; settings come from team defaults (shown as such).
- Old run failed after gate B → content and settings reused; the failure reason is shown.
- Template got new rows since the old run (e.g. arc step) → the new rows use team defaults, marked "new setting".
- Old file has a key no longer in the template → shown as dropped, not applied.
- The old run's end refdes no longer exists on the board → difference at gate A; nothing is cut until resolved.
- `user_settings` file from another PC refers to a board of another revision → only differences found by re-trace
  matter; paths are not used.
- Re-cut in the same request as the old run → refused (new request), so old outputs are never overwritten.

## Requirements *(mandatory)*

### Functional Requirements

**Re-cut process**

- **FR-001**: The tool MUST list earlier runs that contain a given interface name for the same workspace, from the
  request registry, with request id, date, sweep start / stop / step and last step, newest first.
- **FR-002**: The tool MUST accept as source of a re-cut: a request id, a path to a `user_settings` file (also from
  another PC), or the choice from the FR-001 list.
- **FR-003**: The tool MUST re-trace the interface on the current board with the old ends and nets and report only
  differences: nets added / removed, end pins changed, series parts added / removed / changed value, diff groups,
  board file changed (size / modified time), schematic difference resolutions no longer valid.
- **FR-004**: Gate A MUST still be required for a re-cut; with zero differences it needs only the engineer's go;
  each difference needs a resolution (same rule as 003).
- **FR-005**: After the end check, the tool MUST compare the old handling of each end with the new measurements and
  report: kept, no longer needed, new unusual case without handling. A new unusual case needs the engineer's choice
  (same options as 003).
- **FR-006**: Gate B MUST show the settings table pre-filled from the old run with source "previous run <id>";
  template rows missing in the old run use team defaults marked "new"; old keys not in the template are listed as
  dropped.
- **FR-007**: A re-cut MUST run in a NEW request (never writes into the old request's folder) and then follow 003
  (cut, apply, self-check, merge with gate C; run only on request).

**One settings file**

- **FR-008**: The tool MUST write one file per request,
  `<workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/user_settings.json`, holding, per interface: content (nets, diff groups, ends,
  series parts, schematic resolutions), structural cut values (`cutout.*`, `series.keep`), end handling, all
  settings values, the time of each agreement, and a header (tool version, workspace, board, request id).
- **FR-009**: The file MUST be updated when gate A or gate B is passed (only that interface changes) and be valid
  JSON / readable by the engineer.
- **FR-010**: Loading the file MUST validate every field (types, known keys, channel name rules) with a clear error
  naming the field.
- **FR-011**: The number of files per interface MUST NOT grow; files made redundant by `user_settings` are no longer
  written: `settings.json` and `settings.md` are replaced by the request's `user_settings.json`.

**Arc step**

- **FR-012**: A team-template row (channel scope, unit deg, default 10, valid range > 0 and ≤ 90 deg) MUST set the
  HFSS setup arc step size (circle and arc approximation) in `apply_stage` setup, for both flows.
- **FR-013**: The self-check MUST read the arc step back and compare it with the agreed value.
- **FR-014**: Changes results → minor version bump (0.7.0), CHANGELOG, new regression reference for CPHY_U14_U26
  (AEDT run on a board1 copy only after the engineer's OK).

**Guide**

- **FR-015**: `guides/interface_sim.md` MUST say: "như lần trước" / "settings cũ" / a request id / a `user_settings`
  path ALWAYS uses this process; never re-type old values by hand; show only differences.
- **FR-016**: No existing MCP tool, prompt, Excel layout or output folder is renamed or removed (Principle IX);
  new tools / arguments are additions.

### Key Entities

- **Previous run**: request id, workspace, interface name, date, last step, sweep values, source (registry / path).
- **User settings file**: header (tool version, workspace, board, request id, updated) + per interface: content,
  structural values, handling, settings values, agreement times.
- **Re-cut difference**: item, old value, new value, resolution.
- **Handling comparison**: end refdes, old handling, new unusual cases, result (kept / not needed / needs choice).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Re-cut of an unchanged interface on board1 needs only 3 engineer answers (go at gates A, B, C) and 0
  re-typed values.
- **SC-002**: 100 % of differences between the old run and the current board (in the FR-003 list) are shown; 0
  shown when nothing changed (offline test with fake board facts).
- **SC-003**: A `user_settings` file copied to another folder reproduces the same content, handling and values
  (offline round-trip test, 0 differences).
- **SC-004**: Files written per interface ≤ 003 count.
- **SC-005**: Cut designs of both flows have arc step 10 deg by default; self-check reports a mismatch otherwise.
- **SC-006**: Old references PASS except the agreed arc-step change; new CPHY_U14_U26 reference recorded.

## Assumptions

- "Same workspace" = same absolute `.aedt` path in the request registry; runs from another PC are found only by
  `user_settings` path or request id.
- Interface name used for search = the old interface name (case-insensitive).
- The arc step row lives in `templates/autocut_template.csv` (single source of defaults), so the channel Excel of the
  old flow gets the row automatically (Settings matrix = channel-scope rows).
- PyEDB exposes the arc step of an HFSS setup (to be confirmed in plan research on a board1 copy).
- Work stays on branch `main`; spec folder `specs/004-recut-previous-settings`.
