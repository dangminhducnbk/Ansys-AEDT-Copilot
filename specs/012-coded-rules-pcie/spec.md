# Feature Specification: Coded rules from the PCIe self-test (connector end, series report, review lines, port metric)

**Feature Branch**: `012-coded-rules-pcie` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-08

**Status**: Clarified

**Input**: User description: "Đưa vào 012" — the 5 issues found by the self-test of 2026-11-07 (interface simulation on a
copy of `test/test1`, interface PCIE_U14_J25: U14 BGA_RAP1 3021 pins ↔ J25 connector 248 pins, PCIe TX/RX L0/L1,
AC caps C951 / C958 / C959 / C1015 220 nF on TX, sweep 0–50 GHz). ROADMAP 012 "Coded rules from 003 experience".

## Clarifications

### Session 2026-11-08

- Q1: How are series AC caps modelled? → B: keep today's rule (short, R = `series.model_r_ohm` = 0 Ω). Only the
  self-check report must name every series part that was shorted.
- Q2: Port rule for a connector end? → B: default handling `smd_rebuild` (same as SMD ICs), no `unusual` stop; the
  existing GND pins of the connector are used as reference (code already does this); a GND plate is drawn only when the
  component has no GND pin left (unchanged rule). Overridable at Gate B; re-cut reuses the stored choice.
- Q3: Loss of reference where the trace grazes via antipads? → keep HIGH ("Đây là lỗi nghiêm trọng"); no severity
  change. Only the duplicate SOV lines per point are removed.

## Problem

| # | Issue (self-test) | Decision |
|---|---|---|
| 1 | Series AC caps (220 nF) are shorted (R = 0 Ω); the reports do not say so | Keep short; report each shorted part |
| 2 | Connector end J25 stops with `connector_end` "no agreed port rule yet"; agent picked a handling ad hoc | Default `smd_rebuild`, no stop |
| 3 | Review lists SOV twice in each loss-of-reference point | Remove duplicates; severity unchanged (HIGH) |
| 4 | Self-check `expected_ports_2x_nets` = 24 while correct = 16 (nets on both sides of a series part counted as ends) | Expected = 2 × signal paths |
| 5 | 8 MEDIUM via stubs 0.257 mm (through vias, no backdrill) | No code change; guide: judge stub vs interface data rate |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connector end handled without a stop (Priority: P1)

A connector end gets `smd_rebuild` by default, shown in the settings table; the engineer may override it at Gate B;
a re-cut reuses the stored choice.

**Why this priority**: connectors are on almost every interface; today each one stops the flow.

**Independent Test**: re-cut PCIE_U14_J25 on a test1 copy: no `connector_end` question; J25 rebuilt with its own GND
pins (no GND plate); ports = signal pins; pins not shifted; re-cut "như lần trước" keeps the handling.

**Acceptance Scenarios**:

1. **Given** a connector end with GND pins, **When** the end check runs, **Then** `smd_rebuild` is proposed as default
   (not an open question) and apply uses the connector's own GND pins.
2. **Given** the engineer chose another handling at Gate B, **When** the interface is re-cut, **Then** the stored
   handling is used.
3. **Given** a connector end with no GND pin, **When** apply runs, **Then** today's rule applies (GND plate from GND
   vias under the body, else warning).

---

### User Story 2 - Reports say what was shorted and count ports right (Priority: P1)

The self-check lists every series part with the model used (shorted, R value) and compares ports with 2 × signal
paths.

**Why this priority**: the engineer must see from the report that AC caps are not in the model, and the port check
must not show a false mismatch.

**Independent Test**: PCIE_U14_J25 self-check lists C951 / C958 / C959 / C1015 as shorted (0 Ω) and shows expected 16,
ports 16; board1 channels show expected 24 / 18 as before.

**Acceptance Scenarios**:

1. **Given** an interface with series parts, **When** the self-check runs, **Then** each part is listed with refdes,
   type and model (R value).
2. **Given** an interface with series parts, **When** the self-check runs, **Then** expected ports = 2 × signal paths.
3. **Given** an interface without series parts, **When** the self-check runs, **Then** numbers are unchanged.

---

### User Story 3 - Review points without duplicate lines (Priority: P2)

Each review point lists each finding once.

**Independent Test**: review PCIE_U14_J25 on a test1 copy: same HIGH / MEDIUM / INFO counts as the self-test, 0
duplicate SOV lines; board1 review numbers unchanged.

**Acceptance Scenarios**:

1. **Given** a point with one SOV, **When** it is listed (chat data or HTML), **Then** SOV appears once.

---

### Edge Cases

- Series part not 2-pin (common-mode choke, ferrite array): today's trace rules, unchanged.
- Connector with a stored handling from a run before 0.13.0: stored value wins (feature 009 defaults history).
- Old Excel flow: connector default applies only where the Excel flow uses the same end handling; board1 references
  must stay identical (no connector end in CPHY_U14_U26).
- Loss-of-reference severity: unchanged everywhere (Q3).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The end check MUST propose `smd_rebuild` as the default handling of a connector end (template default,
  Principle III) instead of an open `unusual` question; the engineer MAY override it at Gate B.
- **FR-002**: The chosen connector handling MUST be stored in `user_settings` and reused by re-cut.
- **FR-003**: `smd_rebuild` MUST keep using the component's own GND pins when any exist; the GND plate rule stays only
  for components without GND pins (no change to cut geometry).
- **FR-004**: The self-check MUST list every series part: refdes, type, model used (short, R value).
- **FR-005**: The self-check expected ports MUST be 2 × signal paths between the two ends (series parts do not add
  ends).
- **FR-006**: A review point MUST list each finding once; severities MUST NOT change.
- **FR-007**: The `review_measure` / `interface_sim` guides MUST tell the agent to judge via stub length against the
  interface data rate and state the reason (011 rule), and to tell the engineer that series caps are shorted.
- **FR-008**: Results without connector ends / series parts MUST be unchanged (`tests/regression.py`,
  `tests/isim_check.py` PASS, references unchanged).
- **FR-009**: A check script MUST cover PCIE_U14_J25 on a test1 copy (connector default, series list, port metric,
  review lines).

### Key Entities

- **Connector handling**: refdes, part number, handling, source (template default / engineer / previous run).
- **Series part report**: refdes, type (R / L / C), value if known, model used.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: PCIE_U14_J25 runs from start to apply with 0 `connector_end` questions; ports = 16 = expected.
- **SC-002**: PCIE_U14_J25 self-check lists 4 / 4 AC caps as shorted.
- **SC-003**: PCIE_U14_J25 review: severity counts equal the self-test (19 HIGH loss of reference kept), 0 duplicate
  lines.
- **SC-004**: board1 regression and isim check PASS with unchanged references.

## Assumptions

- Test board: copy of `test/test1` (original never touched); AEDT checks on copies only.
- Version: coded rule → minor 0.13.0; restart Claude.
