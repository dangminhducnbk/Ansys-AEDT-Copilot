# Feature Specification: AEDT 2026 R1 only (no 2025 R2 fallback)

**Feature Branch**: `047-aedt-2026-only`

**Created**: 2026-11-19

**Status**: Draft

**Input**: User description: "Bạn xóa dự phòng cho tôi được không?" → option A: the tool drops the AEDT 2025 R2
fallback and uses only AEDT 2026 R1.

## Context

Today the tool targets AEDT 2026 R1 and falls back to 2025 R2: `setup.bat` picks `ANSYSEM_ROOT261`, else
`ANSYSEM_ROOT252`; the version resolver accepts any installed version (`aedt_version` "2025.2" or "auto" = newest);
README, about(), the help prompt and the constitution state "2025 R2 fallback". Files saved by 2026 R1 do not open in
2025 R2, so a run on 2025 R2 gives results the team cannot mix with 2026 R1 work. The owner wants one version only.

## Clarifications

### Session 2026-11-19

- Q: Remove the fallback in the tool, or uninstall 2025 R2 from the PC? → A: In the tool (option A). The PC keeps its
  installs; the tool never selects 2025 R2.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The tool always runs on AEDT 2026 R1 (Priority: P1)

Every EDB / AEDT / SIwave call uses AEDT 2026 R1. When 2026 R1 is not found, the tool stops with a clear message
(what is missing, how to fix) instead of silently using 2025 R2.

**Why this priority**: mixing versions gives files the team cannot open together; silent fallback hides it.

**Independent Test**: on a PC with both versions, the resolver returns 2026.1; with 2026 R1 hidden (scratch config /
environment), the tool refuses with the message, even when 2025 R2 is installed.

**Acceptance Scenarios**:

1. **Given** 2026 R1 and 2025 R2 installed, **When** any tool call opens an EDB, **Then** it uses 2026.1.
2. **Given** only 2025 R2 installed, **When** a tool call needs AEDT, **Then** it is refused: "AEDT 2026 R1 not found
   (found: 2025.2). Install AEDT 2026 R1 or set aedt_root in config.yaml." No file is written.
3. **Given** `config.yaml` `aedt_version: "2025.2"` (old setting) or `aedt_root` pointing at a 2025 R2 folder,
   **Then** refused with the same kind of message naming the setting to change.
4. **Given** `aedt_version: "auto"`, **Then** it picks the newest installed version that is 2026.1 or newer; older
   ones are never picked.

### User Story 2 - Setup and texts say 2026 R1 only (Priority: P1)

`setup.bat` requires AEDT 2026 R1 (stops with a message if missing, does not write 2025.2 into config.yaml). README,
about(), the help prompt, CLAUDE notes and guides no longer mention a 2025 R2 fallback.

**Independent Test**: run setup's version step with only `ANSYSEM_ROOT252` set (scratch environment) → stops with the
message; search the committed texts for "2025 R2" fallback wording → none left (history in CHANGELOG stays).

**Acceptance Scenarios**:

1. **Given** no `ANSYSEM_ROOT261`, **When** `setup.bat` runs, **Then** it stops before writing config.yaml and says to
   install AEDT 2026 R1.
2. **Given** a colleague asks "what do I need", **Then** about() / README / help say "Ansys AEDT 2026 R1".

### Edge Cases

- A newer release (2026 R2, 2027 R1) installed later: allowed (minimum = 2026.1); `auto` picks the newest.
- `config.yaml` already says 2026.1 on the owner's PC: nothing changes for the owner.
- Remote simulation server option `pre_grpc_args` (for a server running AEDT 2025.2 without service pack): it is a
  server setting, not a local fallback; kept unchanged (out of scope).
- CHANGELOG history and old specs keep their 2025 R2 text (history, not instructions).
- Results already saved by 2025 R2 runs (if any) are not touched.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The resolver accepts only AEDT versions 2026.1 or newer; an older version from any source (config
  `aedt_version`, `aedt_root`, a `version` argument, `auto`) is never selected.
- **FR-002**: When no allowed version is found, the refusal names: the minimum version, the versions found, and the
  setting to change (`aedt_version` / `aedt_root` in config.yaml). Raised before any EDB / AEDT / SIwave work.
- **FR-003**: `setup.bat` uses 2026 R1 (or newer) only; missing → error message, exit code non-zero, config.yaml
  unchanged.
- **FR-004**: `tools/set_aedt_version.py` refuses versions older than 2026.1.
- **FR-005**: Texts updated: README, about() `requires`, `prompts/copilot-help.md`, constitution Technical Constraints
  (owner amendment via `/speckit-constitution`), CLAUDE notes; no "2025 R2 fallback" wording remains outside history.
- **FR-006**: The minimum version is one value in one place (changing it later = one edit).
- **FR-007**: Results for 2026 R1 runs are identical before / after (only version selection changes).

### Key Entities

- **Minimum AEDT version**: 2026.1 (single value).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 code paths can select AEDT 2025 R2 (resolver tests cover config version, root, argument, auto).
- **SC-002**: With only 2025 R2 available, 100 % of AEDT-needing calls are refused with the message, 0 files written.
- **SC-003**: On the owner's PC (2026 R1 present) regression results are unchanged.
- **SC-004**: 0 occurrences of fallback wording in README / about / prompts / guides.

## Assumptions

- Minimum is 2026.1; newer releases are allowed (the team will move forward, never back).
- The remote simulation server setting `pre_grpc_args` stays (server side, separate decision).
- The constitution text change is made by the owner (governance); the plan gives the proposed wording.
- Work starts after feature 046 (public repository) finishes, because both touch `setup.bat`, README and CLAUDE notes.
