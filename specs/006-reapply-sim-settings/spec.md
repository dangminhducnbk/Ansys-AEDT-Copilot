# Feature Specification: Re-apply simulation settings after apply

**Feature Branch**: `006-reapply-sim-settings` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User rule 2026-11-06 (relayed by the parent session): "settings chốt xong mới apply cut, khi đã apply cut
rồi là không sửa gì nữa", then corrected: "Chỉ có các settings cho phần cut là không thể sửa sau khi cut rồi, còn
setup frequency, airbox, converge,... vẫn có thể sửa được."

## Clarifications

### Session 2026-11-06

- Q: After a re-apply of an interface already merged into the workspace, what happens in the workspace? → A: Re-apply
  changes the interface's own cut design; the interface goes back to "applied"; a new merge (Gate C) adds it to the
  workspace as a NEW design (name `_v2`, `_v3` ... as today); the design merged before stays unchanged (never
  overwritten).

## Problem

- After Gate B the interface is `applied` and the tool refuses any further settings change (`isim_apply` needs step
  `ends_checked`), while the guide says "re-apply with new values is allowed (no re-cut)". The two disagree.
- The engineer often wants another sweep range, more adaptive passes, a different delta S, arc step or airbox after
  seeing the first design — today that means a full re-cut (feature 004), which redoes the geometry for nothing.
- Geometry settings (cut extent, series parts, cleanup, ports, solder balls) must NOT change silently after the design
  was built: changing them means a new cut.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Change simulation settings of an applied interface (Priority: P1)

The engineer says "đổi sweep CPHY_U14_U26 lên 20 GHz" after apply. The agent shows the settings of that interface:
cut / geometry settings read-only ("đã cắt, đã khoá"), simulation settings (setup, sweep, airbox) editable with the
agreed values. The engineer changes them, approves (Gate B again); the tool keeps a copy of the previous design,
rewrites only setup / sweep / airbox in the design, reads the values back and records them.

**Why this priority**: the request itself; removes a needless re-cut and the guide / code contradiction.

**Independent Test**: on a board1 copy, an applied CPHY_U14_U26: change sweep stop 10 → 20 GHz and max passes 30 → 20;
re-apply; self-check reads back 20 GHz / 20 passes; ports, pins, GND vias, plane areas and pin shift are identical to
the first apply; the previous design exists as a backup.

**Acceptance Scenarios**:

1. **Given** an applied interface, **When** the engineer asks to change a simulation setting, **Then** the agent shows
   the simulation settings editable with the agreed values and the cut settings read-only.
2. **Given** changed simulation values, **When** the engineer gives the explicit go, **Then** only setup, sweep and
   airbox are rewritten in the cut design; the previous design is kept as a backup named with `_old_<time>`.
3. **Given** the re-apply is done, **When** the self-check runs, **Then** every setup / sweep / arc step / airbox value
   read back equals the new values and the geometry metrics equal those of the previous apply.
4. **Given** a re-apply, **When** it finishes, **Then** the request's `user_settings` file holds the new values with
   the time of the new agreement (the previous values are kept in the file's history).
5. **Given** values that break a rule (step larger than the span, arc step 0), **When** submitted, **Then** the same
   validation errors as at the first apply are shown and nothing is changed.

---

### User Story 2 - Cut settings stay locked after apply (Priority: P1)

After apply, a request to change a cut / geometry setting (cut extent, series parts, cleanup, port, solder ball) is
refused with the reason and the way out: go back to the content step / re-cut (feature 004).

**Why this priority**: the user's rule; prevents a design whose geometry no longer matches its recorded settings.

**Independent Test**: offline: re-apply values containing `cleanup.gnd_via_keep_dist_mm` or `solder_ball.height_mm`
are refused naming the key; values with only setup / sweep / airbox keys are accepted.

**Acceptance Scenarios**:

1. **Given** an applied interface, **When** re-apply values contain any cut-group key with a value different from the
   agreed one, **Then** the tool refuses, naming each key and "đã cắt, đã khoá — cut lại để đổi".
2. **Given** re-apply values that repeat the agreed cut values unchanged, **When** submitted, **Then** they are
   ignored (no refusal).
3. **Given** end handling (unusual ends), **When** re-applying, **Then** it cannot change (it shaped the geometry).

---

### User Story 3 - Settings form shows applied tabs (Priority: P2)

The Gate B form (feature 005) opens applied interfaces too: cut group read-only with "đã cắt, đã khoá", simulation
group editable and pre-filled with the agreed values. Submitting validates as a re-apply.

**Why this priority**: convenience on top of US1; text works without it.

**Independent Test**: offline: form of a request with one interface at `ends_checked` and one `applied`: both tabs
enabled; in the applied tab every cut-group descriptor is locked with the "already cut" reason, simulation
descriptors editable with the agreed values.

**Acceptance Scenarios**:

1. **Given** an applied interface, **When** the form opens, **Then** its tab is enabled, marked "applied", cut group
   locked, simulation group editable.
2. **Given** a merged interface, **When** the form opens, **Then** its tab is enabled like an applied one, with a note
   that a re-apply needs a new merge (new design in the workspace).
3. **Given** "Set default" on an applied tab, **When** pressed, **Then** only simulation settings go back to team
   defaults; cut settings stay as cut.

### Edge Cases

- Interface already merged into the workspace: re-apply is allowed; the interface goes back to "applied" (the earlier
  merge is kept in its history); the workspace changes only through a new Gate C merge, which adds a new design
  (`_v2` ...); the earlier merged design is never overwritten.
- Re-apply while the interface is busy (another process) → refused like other steps.
- Self-check after re-apply reports a mismatch → design kept, mismatch shown, the engineer decides (same as first
  apply).
- Re-apply fails in the middle → the backup is still there; the interface stays `applied` with the error shown; the
  previous design can be restored from the backup by the engineer's decision.
- Interface re-cut later (feature 004) → its re-cut starts from the latest agreed values, including re-applied ones.
- Old Excel flow: unchanged (no re-apply there).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Settings MUST be split into a cut group (`cutout.*`, `series.*`, `cleanup.*`, `port.*`, `solder_ball.*`
  and end handling) and a simulation group (`setup.*`, `sweep.*`, `airbox.*`), derived from the template key prefix
  (no per-key list to maintain).
- **FR-002**: After apply, the tool MUST accept a re-apply that changes only simulation-group values, behind Gate B
  (explicit go each time, Principle I).
- **FR-003**: A re-apply MUST refuse any cut-group value that differs from the agreed one, naming each key, and refuse
  a handling change.
- **FR-004**: A re-apply MUST first keep a copy of the current design named `<name>_old_<time>` (never delete), then
  rewrite only setup, sweep and airbox of the design; geometry, ports, components and solder balls MUST NOT change.
- **FR-005**: The self-check MUST run after a re-apply and compare all simulation values read back with the new values
  and the geometry metrics with the previous apply.
- **FR-006**: The `user_settings` file MUST hold the re-applied values and time; the previous values stay in the
  file's history.
- **FR-007**: Validation of re-apply values MUST be the same as at the first apply (same messages).
- **FR-008**: The settings form MUST open applied tabs with the cut group read-only ("đã cắt, đã khoá") and the
  simulation group editable; "Set default" on such a tab resets only the simulation group.
- **FR-009**: The `interface_sim` guide MUST state: cut settings are fixed after apply (change = re-cut), simulation
  settings may be re-applied with a new Gate B go; the old "re-apply any value" line is replaced (Principle IV).
- **FR-011**: A re-apply of a merged interface MUST set it back to "applied" (earlier merge kept in the history) so a
  new Gate C merge adds a new design; the workspace MUST NOT be written by the re-apply.
- **FR-010**: Existing tools keep their names; the old Excel flow is unchanged (Principle IX). Version 0.9.0.

### Key Entities

- **Settings group**: cut or simulation, from the key prefix.
- **Re-apply**: interface, new simulation values, backup design path, time, self-check result.
- **User settings file**: per request (feature 004), now with a history of re-applied values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A simulation-only change on an applied interface takes one Gate B go and no re-cut; geometry metrics are
  identical before / after (0 differences on a board1 copy).
- **SC-002**: 100 % of cut-group changes after apply are refused with the key named (offline tests).
- **SC-003**: 100 % of re-applied simulation values are read back equal by the self-check.
- **SC-004**: 0 deleted files: every re-apply leaves the previous design as `*_old_<time>`.
- **SC-005**: Existing references (`tests/regression.py`, `tests/isim_check.py`, unit tests) still PASS.

## Assumptions

- Re-apply works on the interface's own cut design (`final/<name>.aedb`); it reuses the setup / airbox code of the
  first apply.
- "converge" in the user's words = adaptive convergence settings (max passes, delta S, min passes ...), all in `setup.*`.
- Handling of unusual ends belongs to the cut group (it changes components / solder balls).
- Version minor: 0.9.0; restart Claude; no `setup.bat` rerun.
