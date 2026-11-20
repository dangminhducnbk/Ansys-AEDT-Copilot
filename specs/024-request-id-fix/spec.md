# Feature Specification: Collision-proof run ids / output folders + about() 2.1–2.2 lines

**Feature Branch**: `claude/024-request-id-fix-bd5e0b`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Feature 024 request-id-fix (bug fix, patch). 1) Time-based ids / output folders collide when two runs start in the same second: two isim_start calls got the same request id and wrote into the same folder (PCIe review counts mixed, 2026-11-10). Make creation collision-proof: claim a folder atomically, on clash add _2, _3...; renames aside never overwrite; request registry append serialized. Normal case keeps exact old names. 2) about() payload: add a line in interface_sim for Gate A cut form + read-only cut preview and in review_measure a line for layout_snapshot. No VERSION bump."

## Clarifications

### Session 2026-11-10 (fix 2.5.1)

- Q: `test_threaded_requests` fails now and then with `PermissionError` (Windows) — test bug or real race? → Real race
  in `core/unique.file_lock`: a lock file just deleted by the previous holder stays "delete pending" for a few ms and
  the next `O_EXCL` create gets access denied instead of `FileExistsError`. Parallel `isim_start` (registry lock) can
  hit it. Fix in code: `PermissionError` = busy, retried every 0.05 s; continuous denial > 2 s is re-raised (a real
  access problem stays visible). User: "Có, sửa". → T015.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Two requests started in the same second stay apart (Priority: P1)

An engineer (or two test scripts / two parallel tool calls) starts two interface-simulation requests within
the same second. Each request gets its own id and its own folder; results never mix.

**Why this priority**: On 2026-11-10 two runs got the same id `YYYYMMDD_HHMMSS` and wrote into one folder:
PCIe review counts were mixed. Wrong numbers reach the engineer silently.

**Independent Test**: Start two requests with the clock frozen on one second (and in two threads at once):
two different ids, two folders, each `request.json` holds its own data, both are in the request list.

**Acceptance Scenarios**:

1. **Given** no request for second S, **When** one request starts at S, **Then** its id is exactly `S`
   (old format, unchanged).
2. **Given** a request `S` exists, **When** a second request starts in second S, **Then** it gets `S_2`
   (then `S_3`, …) and its own folder.
3. **Given** two requests start at the same moment in parallel, **When** both finish creating, **Then** ids
   differ, both folders exist, both are listed by the request list (`isim_previous` finds both).

---

### User Story 2 - Every other time-stamped output never overwrites or shares a folder (Priority: P1)

Same-second runs of other tools (design tool copies / backups / cutout / merge folders, interface-simulation
`*_old_<time>` renames on reset / re-cut / re-apply, merge backups, layout review HTML, layout edit work folders)
each get their own folder or file; a rename-aside never replaces an earlier backup.

**Why this priority**: Same root cause; a lost backup cannot be recovered.

**Independent Test**: For each place, create twice in the same (mocked) second: second result has suffix
`_2`, first result untouched.

**Acceptance Scenarios**:

1. **Given** a backup `X_old_S` exists, **When** another rename-aside happens in second S, **Then** it goes to
   `X_old_S_2` and `X_old_S` is unchanged.
2. **Given** a design-tools output `<stem>_<op>_S.aedb` exists or is being created, **When** another call in
   second S creates one, **Then** it gets `<stem>_<op>_S_2.aedb`.

---

### User Story 3 - about() mentions 2.1 / 2.2 features (Priority: P2)

A new user calls `about()` and sees the Gate A cut form + read-only cut preview (end GND rule) and the layout
snapshot (board read once, reviews re-run in seconds).

**Independent Test**: `about()` text contains `isim_cut_form`, `isim_cut_preview` in `interface_sim` and
`layout_snapshot` in `review_measure`.

### Edge Cases

- Old folders (made before this fix) keep their names; reading old requests / `isim_previous` / re-cut works.
- Folder exists as a FILE with the wanted name → treated as taken, next suffix.
- Parent folder missing → created (shared parents may be created by both runs at once without error).
- Design-tools names that end in `_<op>_<time>_<k>` still reduce to the base stem (chained calls).
- Simulation-server copy folder `<request>_<time>`: already created strictly (error instead of overwrite) –
  kept as is.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Creating a time-stamped output folder MUST be atomic: the run that creates the folder owns it;
  any other run in the same second MUST get the next free suffix `_2`, `_3`, … .
- **FR-002**: With no clash, the folder / id name MUST be byte-identical to the old format.
- **FR-003**: Interface-simulation request creation MUST use FR-001 for the request folder; the id is the
  folder name.
- **FR-004**: Adding a request to the shared request list MUST be serialized so parallel starts never lose an
  entry.
- **FR-005**: Moving an existing result aside (`*_old_<time>`) MUST never overwrite an existing path; on clash
  the next suffix is used.
- **FR-006**: Design tools copy / backup names, cutout and merge work folders, merge backups (`_backup/<time>`),
  re-apply backups, layout review HTML file, layout edit region / work folders MUST follow FR-001 / FR-005.
- **FR-007**: `about()` MUST list the Gate A cut form + read-only cut preview (`isim_cut_form`,
  `isim_cut_preview`, end GND rule) under `interface_sim` and `layout_snapshot` under `review_measure`.
- **FR-008**: No change to tool names, arguments, gates, VERSION.

### Key Entities

- **Time-stamped name**: `<prefix><YYYYMMDD_HHMMSS><suffix>` plus optional `_k` (k ≥ 2) on clash.
- **Request list**: shared file of all requests (id, folder, created, workspace).

## Success Criteria *(mandatory)*

- **SC-001**: 2 requests started in the same second (frozen clock and 8 parallel threads) → 2 (8) distinct ids
  and folders, 0 lost list entries.
- **SC-002**: Every place in FR-006 tested with two same-second creations → distinct results, first untouched.
- **SC-003**: All existing unit tests PASS (403 before) + new tests PASS.
- **SC-004**: On a fresh board1 copy: two real request starts in the same second → two folders;
  `tests/regression.py` PASS with unchanged reference.

## Assumptions

- Suffix style `_2`, `_3` matches existing `unique_name` / design-tools `_free` convention.
- Serialization of the request list uses a lock file next to it (same PC; the tool runs locally).
- PI-DC report HTML (`PIDC_report_<time>.html`) is written in place by one engineer at a time: out of scope.
- Simulation-run folder on the server share already refuses to overwrite: out of scope.
