# Feature Specification: Interface Simulation

**Feature Branch**: `003-interface-simulation` (work on `main`)

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description (Vietnamese, summarised): "Theo những feature đã thảo luận, tạo quy trình gọi là
interface simulation. (1) Người dùng cung cấp net và/hoặc refdes của các component cần simulation; agent và người
dùng trao đổi qua lại; agent đọc EDB file và schematic, thống nhất net và component có trong channel; người dùng chốt
thì chuyển bước. (2) Agent cut interface từ board lớn, kiểm tra component, pad của chip / connector / IC có trên board,
in ra bảng các settings cần thiết, trao đổi với người dùng, thống nhất rồi mới settings. (3) Lặp lại cho mọi interface
người dùng yêu cầu, sau đó merge tất cả channel đã settings xong vào 1 file workspace. Nếu người dùng yêu cầu chạy thì
chạy simulation luôn; đường dẫn hay máy cần dùng người dùng sẽ cung cấp."

Context: discussion of 2026-11-04/05 — **code measures and executes, the agent decides with the user** (guides +
data from code; unknown cases are reported, never guessed). This feature is the user-facing process built on that
split; it reuses the existing cut / merge abilities.

## Clarifications

### Session 2026-11-05

- Q: Which schematic files are read? → A: Schematic = PDF; BOM = Excel or CSV. Reading is a separate step done
  BEFORE any interface discussion and saved as a markdown file; interface discussions use that file.
- Q: Where is the workspace? → A: The engineer prepares the AEDT workspace (main project) beforehand; a separate
  stackup file may be given for EDB work. Each interface is cut by its own sub-agent on a COPY of the EDB / AEDT file;
  results are merged back into the engineer's main workspace.
- Q: How is simulation run? → A: On a remote server. The engineer gives the simulation directory; the agent copies the
  workspace there and runs the files one after another.

## User Scenarios & Testing *(mandatory)*

Actors: **SI engineer** (user, talks to the agent in Vietnamese), **agent** (Claude with the Copilot tools and guides),
**sub-agent** (one per interface, does the cut and settings on a copy).

### User Story 0 - Read schematic and BOM once (Priority: P1)

Before any interface is discussed, the engineer gives the schematic (PDF) and BOM (Excel / CSV). The agent reads them
and writes one markdown file (components with refdes / part / value, nets per page, connections between parts,
series parts) next to the board output. All later steps use this file, not the PDF.

**Why this priority**: interface agreement (US1) needs it; reading a large PDF once avoids re-reading and different
answers per interface.

**Independent Test**: give board1 schematic PDF + BOM; the markdown lists U14, U26, U21, J25 with part numbers and
the CPHY nets between them; the engineer can open and correct it.

**Acceptance Scenarios**:

1. **Given** PDF + BOM, **When** read, **Then** a markdown file is written with: source files + date, component table
   (refdes, part, value, description, page), net table (net, connected refdes.pin, page), and a list of items the agent
   could not read clearly.
2. **Given** BOM and schematic disagree (refdes in one only, different value), **Then** each difference is listed in
   the markdown.
3. **Given** the markdown already exists for the same source files, **When** a new request starts, **Then** it is
   reused (no re-read) unless the engineer asks to re-read or the source files changed.
4. **Given** no schematic / BOM, **Then** the agent says interface content will be checked against the board only.

### User Story 1 - Agree the interface content (Priority: P1)

The engineer names an interface loosely ("MIPI CSI giữa U14 và U26", a few nets, or only refdes). The agent reads the
board and the schematic markdown (US0), proposes the nets (signal, diff pairs / trios, series parts on the path) and the components
at each end, shows what it is unsure of, and corrects the list with the engineer until the engineer confirms.

**Why this priority**: a wrong net / component list makes every later step (cut, ports, simulation) wasted work.

**Independent Test**: on board1, give "U14-U26" only; the agent proposes the CPHY trio nets and both end components;
the engineer removes / adds one net; the confirmed list is recorded and is the only input to the cut.

**Acceptance Scenarios**:

1. **Given** only refdes (e.g. `U14, U26`), **When** the agent analyses the board, **Then** it lists all nets
   connecting them directly or through 2-pin series R/C/L, grouped into diff pairs / trios, with end pins per net.
2. **Given** only nets (or a net pattern), **When** analysed, **Then** the agent lists the components at both ends and
   series parts on each net.
3. **Given** board and schematic disagree (net name, missing part, different connection), **When** analysed, **Then**
   the agent shows each difference in a table and asks the engineer which is right; nothing is assumed.
4. **Given** the engineer has not explicitly confirmed, **When** the agent would start the cut, **Then** the cut is
   refused.
5. **Given** confirmation, **Then** the confirmed interface (name, nets, groups, end components, series parts) is
   saved to a file the engineer can open, with the time of confirmation.

---

### User Story 2 - Cut, check ends, agree settings, apply (Priority: P1)

For one confirmed interface a sub-agent cuts it from a COPY of the engineer's EDB / AEDT file (original never
modified; separate stackup file used when EDB work needs it), checks every end
component (chip / IC / BGA / connector / SMD): pads present, pad shape, GND pins near the signal pins, solder balls /
via-in-pad, anything unusual. It then shows a settings table (ports per end, solder ball, series part values,
frequency sweep, solver setup, airbox ...) with proposed values and the reason for each, discusses with the engineer,
and applies the settings only after the engineer agrees.

**Why this priority**: this is the simulation model itself; settings chosen without the engineer are not trusted.

**Independent Test**: cut CPHY_U14_U26 from a COPY of board1; the end check reports U14 BGA and U26 QFN with GND
pins found; the settings table is shown; after "đồng ý" the design has 24 ports, setup and sweep as agreed, and
matches today's regression reference.

**Acceptance Scenarios**:

1. **Given** a confirmed interface, **When** cut, **Then** a separate cut design is created and the full board file
   is unchanged.
2. **Given** the cut design, **When** ends are checked, **Then** a table per end component shows: type, pin count,
   signal pins, GND pins near each signal pin, pad shape and size, solder ball present, and an "unusual" column
   (e.g. no GND pin within the limit, non-round pad, connector) with measured values.
3. **Given** an unusual end (case not covered by an agreed rule), **When** found, **Then** the agent explains it with
   the measured data and proposes options; it does NOT apply a default silently.
4. **Given** the settings table, **When** the engineer changes a value, **Then** the table is re-shown with the change
   and validation (e.g. sweep start < stop, step > 0) before applying.
5. **Given** the engineer has not agreed the settings, **When** the agent would apply them, **Then** applying is
   refused.
6. **Given** agreement, **When** settings are applied, **Then** the design is self-checked (port count = 2 × signal
   nets, pins not moved > 1 mm, setup / sweep values read back equal agreed values) and the result shown.
7. Agreed settings are saved with the interface record so the same interface can be re-cut with identical settings.

---

### User Story 3 - Many interfaces, one workspace (Priority: P2)

The engineer requests several interfaces. Each goes through US1 + US2; US2 work of different interfaces runs in
separate sub-agents, each on its own copy (questions to the engineer still go through the main agent, one at a time).
When all requested interfaces are set up, the agent merges them into the engineer's main workspace (prepared by the
engineer), one design per interface.

**Why this priority**: a project review / simulation run is done per board on all interfaces together.

**Independent Test**: two interfaces of board1 (CPHY_U14_U26, CPHY_U21_J25) → one workspace with 2 designs; ports,
setups and sweeps of each design equal those of its cut design.

**Acceptance Scenarios**:

1. **Given** a list of requested interfaces, **When** the engineer asks for status, **Then** a table shows each
   interface's step (content agreed / cut / ends checked / settings agreed / applied / merged) and open questions.
2. **Given** all requested interfaces have settings applied, **When** the engineer approves the merge, **Then** the
   main workspace contains one new design per interface named after it; name clash → `_v2`, `_v3`, never overwrite;
   designs already in the workspace are untouched.
3. **Given** an interface not yet applied, **When** merge is asked, **Then** the agent lists what is missing and merges
   only with the engineer's explicit choice (all ready ones, or wait).
4. **Given** the merge, **Then** each design's ports / setups / sweeps are compared with its cut design and
   differences reported; existing user files are backed up before any write.

---

### User Story 4 - Run the simulation on request (Priority: P3)

If the engineer asks, the agent copies the workspace into the simulation directory the engineer gives on the remote
server and runs the files there one after another, reports progress, and tells where results are.

**Why this priority**: simulation is long and runs on the server; doing it from the same process saves manual copy
and start.

**Independent Test**: on request with a simulation directory, the workspace copy appears there, files are solved one
by one, the agent reports each file's state, and S-parameter results exist at the reported path when done.

**Acceptance Scenarios**:

1. **Given** no explicit run request, **Then** nothing is copied and no simulation is started.
2. **Given** a run request without the simulation directory, **Then** the agent asks for it.
3. **Given** the directory, **When** copying, **Then** the workspace (project + its data folders) is copied there;
   existing files in that directory are never overwritten (new sub-folder per run).
4. **Given** the copy, **When** running, **Then** files run strictly one after another; the agent reports per file:
   start / end time, status, solver message on failure; a failed file does not stop the next.
5. **Given** all files done, **Then** a summary table lists each file / design, status, run time, result path.

### Edge Cases

- Refdes not on the board, or net not found → agent says so and suggests close matches (similar names).
- Net touches more than two components / branches (T-branch, test point) → shown to the engineer; ends chosen by them.
- Series part with more than 2 pins, or active part on the path → stop tracing there, ask.
- Schematic not given → agent works from the board only and says the check against schematic was skipped.
- Schematic PDF scanned / unreadable page → listed in the markdown as unreadable; agent asks the engineer for that part.
- BOM column names differ from expected (Refdes / Designator / Reference ...) → agent maps them and states the mapping.
- Stackup file and EDB stackup disagree → shown to the engineer; nothing changed in the EDB without agreement.
- Two sub-agents finish at the same time with questions → main agent asks them one at a time, interface name first.
- Simulation directory not reachable / no write permission → stop, tell the engineer, nothing copied.
- Workspace too large for the target disk → stop before copying, show sizes.
- Schematic and board net names differ only by prefix / case → shown as a probable match, still needs confirmation.
- IC end with no GND pin within the limit → reported with the nearest GND pins / vias and distances; engineer decides.
- Connector end, non-round pads → reported as unusual until an agreed rule exists.
- Cut fails or times out → partial output removed (only what this run created), interface marked failed with reason.
- Same interface requested twice → the agent asks whether to replace or create `_2`.
- Workspace already exists → new designs added, nothing overwritten, backup first.
- Original board open in AEDT by the user (lock) → agent asks; never deletes the lock.
- Engineer changes the interface content after the cut → that interface goes back to US1; its cut and settings are
  redone.

## Requirements *(mandatory)*

### Functional Requirements

**Process and gates**

- **FR-001**: The process MUST have: once per request, schematic / BOM read → markdown; per interface: content agreed
  → cut → ends checked → settings agreed → settings applied; then, for the request: merged → (optional) simulated.
- **FR-002**: Three gates per interface and two per request MUST be enforced by the tool, not only by guidance:
  content confirmed (before cut), settings agreed (before apply), merge approved (before merge), run requested (before
  simulation). A gate is passed only by the engineer's explicit go in the current conversation.
- **FR-003**: The state of every interface (step, agreed content, agreed settings, open questions, results) MUST be
  saved to files in the board's output folder so the process can continue in a new chat.

**Step 0 — Schematic and BOM**

- **FR-018**: The agent MUST read the schematic (PDF) and BOM (Excel / CSV) before any interface discussion and write
  one markdown file (sources + date, component table, net / connection table, unreadable items, BOM-vs-schematic
  differences) in the board output folder; the engineer can open and correct it.
- **FR-019**: The markdown MUST be reused for later interfaces and requests while the source files are unchanged
  (same name, size, modified time); re-read only on change or on request.

**Step 1 — Interface content**

- **FR-004**: Input MUST accept nets, net patterns, refdes, or a mix, for one or many interfaces in one message.
- **FR-005**: The agent MUST read the board to list, per interface: signal nets, diff pair / trio grouping, components
  at both ends with pins, 2-pin series R/C/L on the path, and the nets on both sides of each series part.
- **FR-006**: When the schematic markdown exists, the agent MUST compare it with the board (nets, refdes,
  connections, series parts, part values from BOM) and show each difference.
- **FR-007**: Every measured fact shown to the engineer MUST come from the board / schematic data, with the source;
  anything inferred (grouping, probable name match) MUST be marked as a proposal.

**Step 2 — Cut, end check, settings**

- **FR-020**: Each interface's cut and settings MUST run in its own sub-agent on its own COPY of the engineer's EDB /
  AEDT file; the engineer's files are never opened for writing by a sub-agent. Questions from sub-agents reach the
  engineer only through the main agent. The separate stackup file (if given) is the source for layer data when the
  EDB needs it.
- **FR-008**: The cut MUST follow today's agreed cut rules (extent, GND cleanup, series parts 0 Ω, ports, solder balls,
  component rebuild, self-check) and give identical results for interfaces today's flow handles.
- **FR-009**: The end check MUST report, per end component: type (BGA / IC / SMD / connector / other), pins, signal
  pins, GND pins within the agreed distance of each signal pin, pad shape and size, solder ball, via-in-pad, and any
  case not covered by an agreed rule ("unusual") with its measured values.
- **FR-010**: The settings table MUST list every setting that the cut design needs, with the proposed value, unit,
  source (team default / measured / engineer) and a one-line reason; defaults come only from the team templates.
- **FR-011**: Settings MUST be validated (type, range, sweep rule) before they can be agreed; invalid values are shown
  with the expected range.
- **FR-012**: For an unusual case the agent MUST propose at least one option with its effect and wait for the
  engineer's choice; the chosen handling is recorded in the interface record.
- **FR-013**: After apply, the self-check MUST read back the design and compare with the agreed settings and expected
  port count; mismatches are shown.

**Step 3 — Merge and run**

- **FR-014**: The merge MUST put all applied interfaces into the engineer's main workspace (AEDT project prepared by
  the engineer), one new design per interface; back up the workspace first, never overwrite or change an existing
  design, check the workspace is not open / locked by the engineer (ask, never delete a lock), and compare each merged
  design with its cut design.
- **FR-015a** (2026-11-05, user): the server runs the PyAEDT service manager (RPyC, port 17878). The tool MUST use
  it: open a session, launch AEDT non-graphical on the server (gRPC port in the firewall range 50000-50010), upload the
  workspace through the session when the simulation folder is not shared, solve, then close the AEDT it launched.
  Direct gRPC to an AEDT the engineer opened (`-grpcsrv`) stays available.
- **FR-015**: Simulation MUST start only on the engineer's request: copy the workspace into the simulation directory
  on the remote server given by the engineer (new sub-folder per run, nothing overwritten), then run the files there
  strictly one after another; report per file start / end, status, solver message, result path.
- **FR-016**: The existing cut-board tools, prompts, guides, channel Excel and output folders MUST keep working
  unchanged (Principle IX); interface simulation is added beside them.
- **FR-017**: A guide for the agent (English, military style) MUST define the process, gates, tables and questions;
  every rule agreed for this process is written there (Principle IV).

### Key Entities

- **Interface request**: main workspace (AEDT project), board EDB, stackup file (optional), schematic PDF + BOM
  (optional), list of interfaces asked, run request.
- **Schematic markdown**: source files (name, size, time), component table, net / connection table, unreadable
  items, BOM differences.
- **Interface**: name, nets, groups (pairs / trios), end components + pins, series parts, schematic differences and
  how they were resolved, confirmation time, step, failure reason.
- **End check**: per end component: type, pins, GND neighbours, pad data, unusual findings, chosen handling.
- **Settings set**: per interface: each setting with value, unit, source, reason, agreed time.
- **Workspace**: engineer's main project path, designs added (one per interface), merge comparison, backup location.
- **Simulation run**: simulation directory, run sub-folder, file order, per-file start / end time, status, result paths.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For board1, the interfaces CPHY_U14_U26 and CPHY_U21_J25 go from request to merged workspace with the
  engineer answering only content, settings and merge questions (no manual file editing).
- **SC-002**: 100 % of cut / settings / merge / run actions happen only after the matching engineer confirmation
  (tool refuses otherwise; tested by calling without approval).
- **SC-003**: Interfaces handled by today's flow give the same cut results (ports, pins, GND vias, plane areas,
  pin shift) as today's regression reference.
- **SC-004**: 100 % of end components with a case not covered by an agreed rule are reported as unusual with measured
  values; 0 silent defaults for such cases.
- **SC-005**: A process interrupted at any step can be resumed in a new chat from the saved state without repeating
  confirmed steps.
- **SC-007**: Schematic + BOM are read once per source-file version; 0 re-reads across interfaces of one request.
- **SC-008**: 0 writes to the engineer's original EDB / AEDT files by sub-agents; 0 overwritten files in the workspace
  or the simulation directory.
- **SC-006**: Agent time per interface (excluding AEDT run time) under 10 minutes for a 2-component interface on
  board1.

## Assumptions

- Builds on the code/agent split agreed 2026-11-04/05: tools measure and execute; the agent decides with the engineer
  using guides; unknown cases are reported, not guessed.
- Reuses today's cut, verify and merge abilities and team defaults (`templates/autocut_template.csv`); the settings
  table replaces the channel-Excel step for this process only (Excel flow stays for the old process).
- Layout review (today's Phase 1) is offered as an optional step after content agreement, not a mandatory gate.
- One board per request; several boards = several requests.
- Remote run: the simulation directory is a path the engineer's PC can write to (shared / mapped folder on the
  server) and the server's AEDT solves files placed there; how the solver is started on the server (remote AEDT
  session vs batch command) is decided in the plan with the engineer's server details.
- "Run the files one after another" = one AEDT project file per run step; if the workspace is one project with many
  designs, designs are solved one at a time in the given order.
- Feature number: next free is 003; `specs/ROADMAP.md` (restructure 003-014) must be renumbered / re-planned after this
  spec is agreed, since the code/agent split changes the roadmap.
- AEDT 2026 R1 (2025 R2 fallback); cut and merge run on the engineer's PC, simulation on the remote server.
