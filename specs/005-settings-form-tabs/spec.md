# Feature Specification: Full settings form with tabs and "Set default"

**Feature Branch**: `005-settings-form-tabs` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "Chỗ cái table hiện lên để tôi config, bạn có thể hiện toàn bộ thông số lên không? Có nút
set default để set mặc định toàn bộ thông số theo những gì đã thảo luận. Người dùng có thể chỉnh sửa sau. Bảng này có
nhiều tab cho các file người dùng yêu cầu."

## Clarifications

### Session 2026-11-06

- Q: What are the tabs and what does "Set default" restore? → A: Confirmed by the user: one tab per interface of the
  request; "Set default" restores the team template defaults (mandatory sweep values never invented). Its purpose is
  a reset when something was set by mistake; otherwise the engineer sets values normally (proposal pre-filled, free
  edits).

## Problem

- The Gate B input form (0.7.1 / 0.7.2) shows only a subset of the settings: sweep, sweep type, basis order, max
  passes, delta S, arc step and the airbox group. The other agreed settings (cleanup, ports, solder ball, the rest of
  setup and sweep) can only be changed by typing in chat.
- There is no one-click way to put every value back to the agreed team defaults after edits.
- A request usually has several interfaces (several cut files). Today the engineer configures them one at a time in
  separate forms; there is no single view of all of them.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See and edit every setting of an interface (Priority: P1)

At Gate B the engineer sees ONE form that lists every per-interface setting of the team template, grouped by topic
(cut, cleanup, series, port, solder ball, setup, sweep, airbox), pre-filled with the proposal (team defaults, or the
previous run's values on a re-cut). Each setting shows its name, unit and a short description. The engineer edits any
editable value and submits.

**Why this priority**: this is the request itself; without it the form stays partial and the chat stays the only way
to change most values.

**Independent Test**: open Gate B for one interface on a board1 copy; count the settings shown against the team
template's per-interface rows; change one value from each group, submit, and check the validated settings table shows
exactly those changes.

**Acceptance Scenarios**:

1. **Given** an interface at Gate B, **When** the form opens, **Then** every per-interface template setting is shown
   once, in its group, with its current proposed value, unit and description.
2. **Given** a setting that is fixed by the content agreement (cut extent, reference nets, series keep), **When** the
   form opens, **Then** it is shown read-only with a note that it changes only by going back to the content step and
   re-cutting.
3. **Given** the three mandatory sweep values without a value, **When** the form opens, **Then** they are empty and
   marked mandatory; the form never invents them.
4. **Given** the engineer submits the form, **When** the values are checked, **Then** the same validation as today
   applies and errors are shown per setting; the submit is input only, the gate still waits for an explicit "đồng ý".

---

### User Story 2 - "Set default" button (Priority: P1)

The form has a "Set default" button. Pressing it puts every editable setting back to the agreed team default. The
engineer can then edit values again before submitting.

**Why this priority**: explicitly requested; it is the fast way back to a known-good configuration after many edits
or after a re-cut pre-filled old values.

**Independent Test**: change several values in the form, press "Set default", check every editable value equals the
team template default and the mandatory sweep values follow the rule below; edit one value again and submit.

**Acceptance Scenarios**:

1. **Given** edited values, **When** "Set default" is pressed, **Then** every editable setting shows the team template
   default (for example arc step 10 deg, airbox vertical padding 0.2, max passes 30).
2. **Given** "Set default" was pressed, **When** the engineer edits a value, **Then** the edit is kept and submitted.
3. **Given** a form with several tabs, **When** "Set default" is pressed on one tab, **Then** only that tab changes;
   a separate "Set default for all tabs" action resets every tab.
4. **Given** the mandatory sweep values, **When** "Set default" is pressed, **Then** they keep the value already
   entered for this interface in the current session (they have no team default) and stay empty if none was entered.

---

### User Story 3 - One tab per requested file (Priority: P2)

When the request contains several interfaces (cut files), the form shows one tab per interface, named after it, all
in one form. The engineer can fill and submit all tabs at once, and can copy the values of one tab to the others.

**Why this priority**: saves repeating the same form per interface, but each interface still works with a one-tab
form (Story 1), so it is not needed for the first delivery.

**Independent Test**: a request with two interfaces on board1 copies; open the form; check two tabs with each
interface's own proposal and unusual-end choices; copy tab 1 to tab 2; submit; check two validated tables.

**Acceptance Scenarios**:

1. **Given** a request with N interfaces at Gate B, **When** the form opens, **Then** it has N tabs, each with that
   interface's values and its own unusual-end choices.
2. **Given** tab 1 edited, **When** "Copy to all tabs" is used, **Then** the other tabs receive tab 1's editable
   values except locked settings and unusual-end choices, which stay per interface.
3. **Given** the form is submitted, **When** values are checked, **Then** each interface is validated and approved
   on its own; a tab with errors does not block or change the others.
4. **Given** an interface not yet at Gate B (still cutting or checking ends), **When** the form opens, **Then** its
   tab is shown disabled with its current step.

---

### Edge Cases

- Client cannot render interactive forms: the full settings table is shown in chat (all settings, grouped) and the
  engineer edits by text, as today.
- The team template gains or loses a setting: the form follows the template automatically, no form change needed.
- An interface was re-cut with previous values (feature 004): tabs are pre-filled with the old values; "Set default"
  replaces them with team defaults.
- More interfaces than fit as tabs (for example more than 8): tabs still work; names are shortened with the full
  name shown on hover.
- A value outside its valid range (negative padding, step larger than the sweep span): error on that setting after
  submit; nothing is applied.
- Job-scope settings (run, display, review, interface_sim thresholds) are not per interface and are not shown.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST provide, for each interface at Gate B, the full list of per-interface settings: key,
  label, unit, type, allowed choices when known, team default, current proposed value, group, mandatory flag and
  locked flag.
- **FR-002**: The list MUST be built from the team template so that a template change appears in the form without
  form changes (Principle III: the template stays the only source of defaults).
- **FR-003**: The form MUST show every setting of FR-001 grouped by topic, editable unless locked; locked settings MUST
  be shown read-only with the reason.
- **FR-004**: The form MUST have a "Set default" action per tab that sets every editable setting to its team default,
  and a "Set default for all tabs" action.
- **FR-005**: "Set default" MUST NOT invent values for settings without a team default (the mandatory sweep values);
  those keep the value entered in this session or stay empty.
- **FR-006**: The form MUST show one tab per interface of the request, named after the interface; interfaces not at
  Gate B MUST appear disabled with their step.
- **FR-007**: The form MUST offer "Copy to all tabs" for editable values; locked settings and unusual-end handling
  MUST stay per interface.
- **FR-008**: Submitted values MUST pass the existing settings validation per interface; errors MUST be reported per
  interface and per setting.
- **FR-009**: The submitted form MUST be treated as input only; Gate B approval still requires the engineer's
  explicit go per interface (Principle I); the server gate is unchanged.
- **FR-010**: Agreed values MUST be stored in the existing `user_settings` file of the request (feature 004); no new
  file is added.
- **FR-011**: When the client cannot show forms, the agent MUST show the full grouped table in chat with the same
  content.
- **FR-012**: The rule MUST be written in the `interface_sim` guide (Principle IV); the old Excel workflow is
  unchanged.

### Key Entities

- **Setting descriptor**: one per-interface setting: key, label, unit, type, choices, default, proposed value, group,
  mandatory, locked + reason.
- **Settings form**: one tab per interface of a request, each with its descriptors, unusual-end choices and step.
- **User settings file**: the existing single file of the request holding the agreed values (feature 004).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % of the per-interface template settings appear in the form (count equals the template).
- **SC-002**: After "Set default", 100 % of editable settings equal the team default; mandatory sweep values are never
  filled with an invented value.
- **SC-003**: For a request with 2 interfaces, the engineer configures both in one form, in under 2 minutes, without
  typing setting names in chat.
- **SC-004**: Results of a cut with the form are identical to the same values entered by text (same self-check, same
  metrics on a board1 copy).
- **SC-005**: Existing references (`tests/regression.py`, `tests/pidc_check.py`, `tests/isim_check.py`) still PASS.

## Assumptions

- "Các file người dùng yêu cầu" = the interfaces (cut files) of the current request; one tab per interface.
- "Theo những gì đã thảo luận" = the team template defaults (including arc step 10 deg and the airbox values agreed
  2026-11-06); mandatory sweep values have no team default.
- Only per-interface (channel-scope) settings are shown; job-scope settings stay out of the form.
- The form is rendered by the agent's client (Claude desktop widget / elicitation form); the MCP server only provides
  the data and validates. Other clients fall back to the chat table.
- Gate C (merge) and Gate A (content) forms are out of scope except where they already exist.
- Version: minor (new behaviour beside the old one), 0.8.0; restart Claude, no `setup.bat` rerun unless requirements
  change.
