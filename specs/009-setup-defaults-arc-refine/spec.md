# Feature Specification: HFSS setup defaults — arc step 30 deg, max refinement per pass 10 %

**Feature Branch**: `009-setup-defaults-arc-refine` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "chỉnh lại arc step size là 30deg, maximum refinement per pass là 10%"

## Clarifications

### Session 2026-11-07

- Q: Did AEDT show a value other than 10 % for max refinement per pass? → A: No, AEDT already shows 10 % (option B:
  confirmation only, no bug fix).

## Problem

- The team default for the HFSS arc step size (Advanced Meshing, circle / arc approximation) is 10 deg since 0.7.0.
  The engineer now wants 30 deg as the team default.
- The engineer wants "Maximum refinement per pass" = 10 % in the HFSS setup. The team template already holds 10 for
  this setting and AEDT already shows 10 % (confirmed by the engineer); this part is a confirmation: keep 10 %, add
  range validation and self-check read-back.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - New cuts use arc step 30 deg (Priority: P1)

The engineer cuts a new interface (interface simulation or Excel flow) or runs a design tool that creates a setup, without
touching the arc step. The HFSS setup in AEDT shows Arc step size = 30 deg.

**Why this priority**: this is the requested default change.

**Independent Test**: cut one interface on a board1 copy with team defaults; open the setup in AEDT 2026 R1: Advanced
Meshing → arc step 30 deg; self-check reads back 30.

**Acceptance Scenarios**:

1. **Given** team defaults, **When** a new cut or setup is created, **Then** the arc step is 30 deg in AEDT and in the
   self-check read-back.
2. **Given** the settings form / settings table, **When** it opens, **Then** the arc step shows 30 deg as the team
   default, and "Set default" restores 30 deg.
3. **Given** the engineer enters another value (0 < value ≤ 90), **When** the cut runs, **Then** that value is used.

---

### User Story 2 - Max refinement per pass is 10 % in AEDT (Priority: P1)

Every setup created by the copilot shows "Maximum Refinement Per Pass" = 10 % in the AEDT setup dialog.

**Why this priority**: requested; the value must be the one the engineer sees in AEDT, not only in the template.

**Independent Test**: cut one interface on a board1 copy with team defaults; open the setup dialog in AEDT 2026 R1:
Maximum Refinement Per Pass = 10 %; self-check reads back 10.

**Acceptance Scenarios**:

1. **Given** team defaults, **When** a setup is created, **Then** AEDT shows 10 % and the self-check reads back 10.
2. **Given** the read-back value differs from the agreed value, **When** the self-check runs, **Then** it reports a
   mismatch.

---

### User Story 3 - Earlier runs keep their own values (Priority: P2)

A re-cut "như lần trước" of an interface cut before this change keeps the arc step that run used (10 deg), unless the
engineer chooses the new team default.

**Why this priority**: results must stay reproducible (feature 004).

**Independent Test**: re-cut the 0.7.x board1 request on a copy: proposal shows arc step 10 (previous) and 30 (team
default) as a difference.

**Acceptance Scenarios**:

1. **Given** a previous run with arc step 10, **When** it is re-cut, **Then** the proposal keeps 10 and shows the new
   team default 30 as a difference.
2. **Given** a previous run from before arc step existed (0.6.0), **When** it is re-cut, **Then** the proposal uses the
   team default 30 and marks it as new.

---

### Edge Cases

- Designs already cut, merged or re-applied keep their values; nothing is changed retroactively.
- A re-apply of simulation settings (feature 006) on an old design uses the agreed values of that design unless the
  engineer changes them.
- Arc step outside 0 < value ≤ 90: refused as today.
- Max refinement per pass outside its valid range: refused before anything is written.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The team default arc step MUST be 30 deg (template, the only source of defaults — Principle III).
- **FR-002**: The team default max refinement per pass MUST be 10 % and MUST appear as 10 % in the AEDT setup dialog
  of every setup created by the copilot (cut flows and design tools).
- **FR-003**: The self-check MUST read back both values and report a mismatch with the agreed values.
- **FR-004**: Max refinement per pass MUST be validated (whole percent, 1 ≤ value ≤ 100) before any file is written;
  errors name the setting and the valid range.
- **FR-005**: Re-cut of earlier runs MUST keep their stored values and show the new team default as a difference.
- **FR-006**: Guides and notes that state the old arc step default (10 deg) MUST be updated (Principle IV).
- **FR-007**: Existing designs and results MUST NOT be changed.

### Key Entities

- **Team template row**: `setup.arc_step_deg`, `setup.max_refine_per_pass` (key, unit, default, description).
- **Self-check read-back**: values read from the saved design and compared with the agreed values.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new cut with team defaults shows arc step 30 deg and max refinement per pass 10 % in AEDT 2026 R1
  (checked on a board1 copy).
- **SC-002**: Self-check read-back matches for both values in 100 % of new cuts and design-tool setups.
- **SC-003**: Re-cut of an earlier run keeps its old arc step and lists exactly one difference for it.
- **SC-004**: Apart from these two setup values, results of a cut are identical to before (`tests/regression.py`,
  `tests/isim_check.py` PASS; reference updated only for the arc step).

## Assumptions

- "Arc step size" = HFSS 3D Layout setup → Advanced Meshing → circle / arc approximation (the setting added in 0.7.0).
- "Maximum refinement per pass" = adaptive setting "Maximum Refinement Per Pass" (percent), template key
  `setup.max_refine_per_pass`.
- Both flows (interface simulation, Excel cut) and the design tools share the template, so all get the new defaults.
- Version: patch-level default change plus any fix → 0.10.1 (or the next minor if released with 008); restart not
  needed for template-only changes.
- Feature number 009 shifts the planned ROADMAP features after 008 by one.
