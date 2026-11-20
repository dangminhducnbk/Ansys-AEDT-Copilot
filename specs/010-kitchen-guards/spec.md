# Feature Specification: Kitchen guards — lock Principle X in code

**Feature Branch**: `010-kitchen-guards` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-07

**Status**: Draft

**Input**: User description: "Viết spec" — the code locks of constitution 1.2.0 Principle X (Kitchen: utensils and
recipes), approved by the repo owner 2026-11-07: "làm sao để tất cả các MCP tool sau này đều tuân thủ quy trình này và
quy trình của spec-kit?"

## Problem

- Constitution 1.2.0 Principle X says every MCP tool is a utensil in the catalog with a safety level, risky utensils
  need a server-side approval flag, new ways of working are recipes, and offline tests lock this.
- Feature 008 (0.11.0) built the catalog and two tests (catalog names = server tools; gated levels have a real gate
  flag). What is still only a written rule:
  - a tool can be added to the server without the catalog: only a unit test notices, the server itself starts fine;
  - no check that each catalog entry has a contract (Principle VII);
  - no check that a gated tool actually refuses when the flag is false;
  - only one recipe is checked for unknown utensils; a broken team recipe is found only when listed;
  - the plan template has no "Kitchen check" section, and converge has no catalog step.
- Result: a future feature (by Claude or another developer) can still add a fixed-process tool, an unregistered tool
  or a risky tool without a gate, and it is caught late or not at all.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A tool without a catalog entry cannot run (Priority: P1)

A developer adds a new MCP tool but forgets the catalog entry (or the safety level, or the gate flag for a risky
level). The server refuses to start and says which tool and what is missing; the offline tests fail with the same
message.

**Why this priority**: this is the hard lock; everything else relies on the catalog being complete.

**Independent Test**: offline, add a dummy tool without a catalog entry in a test copy of the registration; start-up
check refuses with the tool name; remove it and start-up passes.

**Acceptance Scenarios**:

1. **Given** a tool registered without a catalog entry, **When** the server starts, **Then** it refuses to start and
   names the tool and the missing entry.
2. **Given** a catalog entry with a gated safety level (original / workspace / remote) but no approval flag in the tool
   inputs, **When** the server starts or the tests run, **Then** both refuse, naming the tool and the flag.
3. **Given** a catalog entry for a tool that no longer exists, **When** the tests run, **Then** they fail naming it.
4. **Given** a complete catalog, **When** the server starts, **Then** start-up time and tool list are unchanged.

---

### User Story 2 - Gates proven, not only declared (Priority: P1)

For every gated utensil, an offline test calls it with the approval flag false (and otherwise valid inputs) and checks
it refuses before touching any file.

**Why this priority**: SC-005 of 008 ("0 risky operations without the engineer's go") must be proven by tests, not by
reading code.

**Independent Test**: offline test suite; every gated catalog entry is called with flag false; each returns a refusal
naming the gate; no file is created or changed in the temp folder.

**Acceptance Scenarios**:

1. **Given** each gated utensil, **When** called with its flag false, **Then** it refuses and names the flag.
2. **Given** a new gated utensil added later, **When** the tests run, **Then** it is covered automatically (no test
   edit needed).

---

### User Story 3 - Contracts and recipes stay in sync (Priority: P2)

Every catalog entry points to its contract block; every recipe (team and personal format) names only existing
utensils. Tests fail otherwise.

**Why this priority**: keeps Principle VII and recipes honest as tools change; lower than the hard locks.

**Independent Test**: offline; remove one contract block in a test copy → test fails naming the tool; add an unknown
utensil to a test recipe → test fails naming the recipe and step.

**Acceptance Scenarios**:

1. **Given** a catalog entry, **When** the tests run, **Then** a contract for that tool exists under
   `specs/*/contracts/`, or the test fails naming the tool.
2. **Given** all team recipes, **When** the tests run, **Then** every step names an existing utensil.
3. **Given** a recipe step naming a `process` tool, **When** the tests run, **Then** it is allowed only in recipes of
   that process (process tools are not general utensils).

---

### User Story 4 - Spec Kit asks the kitchen questions (Priority: P2)

Every new plan has a "Kitchen check" section; converge runs the catalog tests and lists missing entries / contracts /
tests as new tasks.

**Why this priority**: catches design mistakes at plan time, before code, for Claude and other developers.

**Independent Test**: run `/speckit-plan` on a dummy feature: plan contains the Kitchen check section; run converge on a
feature that adds a tool without a contract: it appends a task for it.

**Acceptance Scenarios**:

1. **Given** a new plan, **When** it is generated, **Then** it has a Kitchen check: utensils added / changed, safety
   level, gate flag, recipes affected, and "no new fixed-process tool" (or justification).
2. **Given** converge, **When** catalog tests fail, **Then** each failure becomes a task.

---

### Edge Cases

- Existing `process` tools (Excel cut, isim_*, pidc_*): allowed as they are (Principle IX); a NEW process tool needs a
  justification in the plan Kitchen check.
- A tool whose safety depends on an argument (e.g. copy by default, in place with a flag): catalog keeps the highest
  level with its condition, as today; the gate test uses the risky argument.
- Personal recipes on a user PC naming an unknown utensil: not a test failure (not in the repo); they stay "broken" in
  the recipe list, as today.
- Contracts of features 001–007 written before the catalog: the test maps each tool to a contract block; tools that
  have none today are listed once and get their contract in this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: MCP tools MUST be registered through one shared registration path that looks the tool up in the catalog.
- **FR-002**: The server MUST refuse to start when a registered tool has no catalog entry, no safety level, or a gated
  level without an approval flag in its inputs; the message MUST name the tool and what is missing.
- **FR-003**: Offline tests MUST fail for: tool not in catalog, catalog entry without tool, gated level without flag,
  catalog entry without contract, team recipe naming an unknown utensil, process tool used outside its process recipe.
- **FR-004**: An offline test MUST call every gated utensil with the flag false and check refusal with no file written;
  new gated utensils MUST be covered without test edits.
- **FR-005**: Missing contracts for existing tools MUST be written in this feature (Principle VII).
- **FR-006**: The plan template MUST include a "Kitchen check" section; the converge step MUST run the catalog tests
  and turn failures into tasks.
- **FR-007**: Tool names, inputs, outputs and results MUST NOT change (Principle IX); only registration and checks
  change.
- **FR-008**: The `kitchen` guide MUST state the rule for the agent: never call or propose an unregistered operation or
  ad-hoc script; a missing utensil goes through Spec Kit.

### Key Entities

- **Catalog entry**: tool name, group, kind, safety, gate, condition, contract reference (new).
- **Registration path**: the single way a tool becomes an MCP tool; checks the catalog.
- **Kitchen check**: plan section listing utensil changes, safety, gates, recipes affected.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % of MCP tools are registered through the shared path; a tool without catalog entry stops the server
  at start-up (shown by an offline test).
- **SC-002**: 100 % of gated utensils refuse with the flag false in the offline suite, with 0 files written.
- **SC-003**: 100 % of catalog entries have a contract; 100 % of team recipe steps name existing utensils.
- **SC-004**: The next feature's plan contains a Kitchen check without anyone asking for it.
- **SC-005**: Existing results unchanged: unit tests, `tests/regression.py`, `tests/isim_check.py`, `tests/pidc_check.py`
  PASS with no reference change.

## Assumptions

- No AEDT run is needed except the final regression (registration only changes how tools are wired).
- The Spec Kit plan template change is a project override (`.specify/templates/plan-template.md`), not a change to the
  Spec Kit package.
- Version: patch-level structural change → 0.11.2 (restart Claude; no `setup.bat` rerun).
- Numbering: this spec takes 010; ROADMAP features planned as 010+ (coded rules, PI-DC on core, thin layers,
  multi-board) shift by one; ROADMAP is updated in the plan step.
