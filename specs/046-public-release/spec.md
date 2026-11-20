# Feature Specification: One public repository, checked before every push

**Feature Branch**: `046-public-release`

**Created**: 2026-11-18

**Status**: Draft

**Input**: User description: "bạn lên kế hoạch để loại bỏ các file có tên của khách hàng, địa chỉa IP, các file test không liên quan để bỏ ra, không upload nó lên git."

## Context

The repo `Ansys-AEDT-Copilot` is private (400 commits, 53 tags). The owner wants ONE repository from now on, PUBLIC,
that the team clones / pulls. Development continues in the same folder on the owner's PC. Customer data must never
reach GitHub: customer / project / board names, customer net names, fab names, internal IP addresses, local paths
of the owner's PC, tests that run on customer boards, and layout pictures / data of customer boards.

A scan of 5.6.0 found: customer / board names in 42 / 17 / 5 tracked files (three customers), 76 files under `specs/`,
an internal IP in 3 files, customer-board tests under `tests/`, a 30 MB mock page built from a customer board.
A trial clean copy (2026-11-18, outside the repo) proved name replacement keeps all 693 unit tests passing.

The existing history cannot become public (it holds all of the above). The public repository therefore starts from
ONE clean commit; the old private repository is kept as an archive.

## Clarifications

### Session 2026-11-18

- Q: Private repo kept for development, public copy exported per release? → A: No. From now on one repository,
  public; the owner pushes to it directly from the development folder. Every push passes a check first.
- Q: Where do the customer files go? → A: They stay in the owner's folder on the PC, never committed (ignored by git).
- Q: What must the repository contain for the team? → A: an install guide that a colleague's AI IDE reads and follows
  to install and register the MCP server.
- Q: Is the sample board `board1` (used in unit-test goldens: net names, coordinates) publishable? → A: Not needed:
  tests are for the developer only, colleagues do not run them. The whole `tests/` folder stays local (ignored by
  git); with it every golden / reference built from `board1` or a customer board. All `specs/*/mock/` files stay local.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Switch to one clean public repository (Priority: P1)

One time: the development folder gets a new history that starts with one clean commit of the current release; the
remote becomes a new public GitHub repository; the old private repository stays on GitHub as a private archive.
Customer files stay on disk, ignored by git. Spec files, changelog and code comments keep their content with customer
names replaced by neutral names.

**Why this priority**: the base of everything else.

**Independent Test**: after the switch, the folder still has every file it had before (nothing deleted on disk);
`git` tracks only clean files; the public repository has one commit; an anonymous visitor sees it; the old private
repository is unchanged and still private.

**Acceptance Scenarios**:

1. **Given** the folder at 5.6.0, **When** the switch runs, **Then** every file on disk before still exists after
   (same content for ignored customer files), and the tracked files contain 0 protected terms.
2. **Given** the switch, **When** unit tests run in the folder, **Then** all pass.
3. **Given** the old private repository, **Then** its commits, tags and visibility are unchanged.
4. **Given** the first push, **Then** it happens only after the owner's explicit go.

### User Story 2 - Check before every commit and push (Priority: P1)

Every commit and every push from the owner's folder runs an automatic check. Refused when an outgoing file: holds a
protected term; is a protected path (customer tests, private notes, mock pages built from customer boards); is a new
binary / unscannable file not approved by the owner; or the commit author e-mail is not the hidden GitHub e-mail.
The refusal names file, line, reason, and what to do (replace the name, ignore the file, approve the binary).

**Why this priority**: once the repository is public, a single wrong push publishes customer data.

**Independent Test**: seed each kind of leak in a scratch commit → refused at commit; make a commit with the commit
check skipped → refused at push; clean commit → passes.

**Acceptance Scenarios**:

1. **Given** a staged file with a customer name / internal IP / owner path, **When** committing, **Then** refused with
   file + line + term.
2. **Given** a staged protected path, **When** committing, **Then** refused.
3. **Given** a new image / binary not approved, **When** committing, **Then** refused until the owner looks at it and
   approves it.
4. **Given** outgoing commits, **When** pushing, **Then** every file of every outgoing commit is checked again; any hit
   refuses the push (catches a skipped commit check).
5. **Given** a clean change, **Then** commit and push checks pass in a few seconds each.
6. **Given** the check itself, **Then** its list of protected terms is never committed (it names them).

### User Story 3 - A colleague's AI IDE installs the tool from the guide (Priority: P1)

A team member clones the public repository and asks their AI IDE "install this". The IDE finds the install guide at
the root by itself, checks prerequisites, runs the setup, registers the MCP server `aedt_copilot` in THAT client,
verifies it, and says what to restart. The same guide covers updating after `git pull`.

**Why this priority**: the team's way to start; without it each colleague needs the owner.

**Independent Test**: fresh clone on a PC without the tool, AI IDE told "install this repo" → done with no extra hint;
the server's "about" answers with the release version.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** the AI IDE opens it, **Then** an entry file it reads automatically points to the
   install guide.
2. **Given** a missing prerequisite (no AEDT, wrong Python), **Then** the IDE stops and says exactly what is missing.
3. **Given** install done, **Then** the verification step reports version + tool count, or the exact error.
4. **Given** a later `git pull`, **Then** the guide says whether setup must run again or only a restart / new chat.
5. **Given** the client is Claude desktop, Claude Code or another MCP client, **Then** the guide gives the registration
   step for it (generic: command + arguments + environment).

### User Story 4 - Keep the protected list up to date (Priority: P2)

The protected terms, replacements, protected paths and approved binaries are one local file the owner can edit. A new
customer = one new line; from then on the check refuses that name.

**Independent Test**: add a term, stage a file containing it → refused.

### Edge Cases

- Owner's private notes for the AI assistant (today `CLAUDE.md`, full of customer facts): kept locally in a file git
  ignores and the assistant still reads; the committed `CLAUDE.md` holds only public rules + pointer to the guide.
- Spec Kit "commit after each step": spec files stay committed, so new specs must use neutral names; the check refuses
  customer names in them (the owner replaces or moves customer detail to the local notes).
- Tests are local only: no backup on GitHub for them; the owner keeps their own backup of the folder (the archive
  repository still holds the tests up to 5.6.0).
- Mock pages / pictures (e.g. 30 MB demo page built from a customer board): local only.
- A replacement must not create a diff-pair / trio suffix (`_P/_N`, `_A/_B/_C`).
- A test compares with a machine path (the repo folder): the repo folder path is not a protected term.
- Tags: the public repository starts with tag of the current release only; old tags stay in the archive.
- Colleagues who cloned the old private repository: they re-clone the public one (guide says so).
- `graphify-out/`, `.venv`, board / result files stay ignored as today.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: One-time switch: the development folder gets a new history starting from one clean commit of the
  current release; remote = new public repository; old repository = private archive, untouched.
- **FR-002**: No file on disk is deleted by the switch; customer files become ignored by git.
- **FR-003**: Ignored (local only): private assistant notes, the whole `tests/` folder (unit tests, goldens, board
  checks, references: developer only), all `specs/*/mock/` files, the protected list and the check's data.
- **FR-004**: Committed files keep their content with protected terms replaced by neutral names (same length where
  test goldens hold them): customer / project / board names, board file names, customer net-name parts, fab names,
  internal IPs (→ 192.0.2.x), owner user folder and project-data paths.
- **FR-005**: Commit check and push check (FR-006 rules) installed in the owner's folder; push check covers every file
  of every outgoing commit.
- **FR-006**: Refusal rules: protected term in content; protected path; unapproved binary; author e-mail not the
  hidden GitHub e-mail. Message: file, line, reason, fix.
- **FR-007**: One local protected list (terms, replacements, protected paths, approved binaries), editable without code.
- **FR-008**: The check is installed again automatically when missing (e.g. after a fresh clone by the owner).
- **FR-009**: Unit tests (local) pass in the folder after the switch (693 at 5.6.0); the public files alone start the
  MCP server (all tools registered) without the `tests/` folder.
- **FR-010**: Install guide at the root for AI coding assistants (English, terse steps, exact commands, expected
  output) + entry files common AI IDEs read automatically, pointing to it.
- **FR-011**: The guide covers: prerequisites (Windows, AEDT 2026 R1 / 2025 R2, Python 3.10-3.12, git), clone location
  without spaces, setup, MCP registration per client (Claude desktop, Claude Code, generic), verification (version +
  tool count), restart, update after `git pull`, uninstall, common errors.
- **FR-012**: Registration for Claude Code works without code edits (setup or a documented command), as for Claude
  desktop today.
- **FR-013**: README (Vietnamese, humans) without private paths, clone URL = public repository, links the guide.
- **FR-014**: The project rules for the assistant (constitution / guides / CLAUDE rules) say: never write customer
  data in committed files; customer detail goes to the local notes.
- **FR-015**: Nothing is pushed without the owner's explicit go; never force push to the public repository.

### Key Entities

- **Protected list** (local): terms (patterns) + replacement, protected paths, approved binaries, required e-mail.
- **Local notes** (local): the owner's assistant notes with customer facts.
- **Public repository**: clean history from the switch on.
- **Archive**: the old private repository, read-only by convention.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 protected terms in any committed file of the public repository (100 % of text files swept).
- **SC-002**: 100 % of seeded leaks (term, path, binary, e-mail) refused at commit or push; clean commit + push check
  under 10 seconds each.
- **SC-003**: 100 % of files on disk before the switch still exist after it.
- **SC-004**: 100 % of unit tests pass after the switch.
- **SC-005**: An anonymous visitor opens the public repository; a colleague's AI IDE installs and verifies the tool
  from a fresh clone using only the guide (0 questions to the owner), under 15 minutes excluding downloads.
- **SC-006**: The archive repository is identical before / after (commits, tags, visibility).

## Assumptions

- Neutral names follow the trial export mapping (kept in the local protected list, never in committed files): boards →
  BOARDA / BOARDB, customer → client, customer net parts → SERLINK / DEVA / HSA2HSB; `board1` / `test1` / refdes stay.
- New public repository name chosen by the owner at the switch (the archive may be renamed `...-archive` so the new one
  keeps `Ansys-AEDT-Copilot`).
- Commits use the hidden GitHub e-mail (`<user>@users.noreply.github.com`); the GitHub username is public anyway.
- Team AI IDEs: mainly Claude Code / Claude desktop; others get generic registration data. Each colleague has their own
  AEDT license; colleagues only pull.
- Customer-board checks (regression on customer boards) keep running locally from the ignored files.
