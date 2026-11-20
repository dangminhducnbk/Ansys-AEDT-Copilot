# Feature Specification: AEDT 2026 R1 Migration

**Feature Branch**: `001-aedt-2026r1-migration`

**Created**: 2026-11-04

**Status**: Approved (user: "do it step by step")

**Input**: Audit `aedt_copilot_2026r1_audit.md` (2026-11-04): move Ansys AEDT Copilot 0.4.0 from AEDT 2025 R2 to 2026 R1.

## Problem

- Every EDB-opening tool (`inspect_board`, `layout_region`, review, propose, cut) fails today:
  MCP server process has no `ANSYSEM_ROOT###` -> pyedb `INSTALLED_VERSIONS = None` -> `TypeError`.
- Tool depends fully on env vars; does not find AEDT itself.
- pyedb 0.85 picks the gRPC backend by default for `version >= 2026.1`; tool code uses the .NET API.
- argparse rejects `--box -3.3,...` (value starts with `-`).
- `2025.2` hard-coded in config, function defaults and SIwave path.

## User Scenarios & Testing

### US1 - Tool finds AEDT by itself (P1)

Team member calls `inspect_board` / `layout_region` from Claude desktop with no `ANSYSEM_ROOT*` in env.

**Independent Test**: run both tools on BoardB 19x19 board, config `2025.2` -> success.

1. **Given** no `ANSYSEM_ROOT*` env, **When** `inspect_board(board)`, **Then** summary returned, no TypeError.
2. **Given** config `aedt_root` set, **When** any EDB tool, **Then** that root is used.

### US2 - Box values starting with "-" (P2)

**Independent Test**: `layout_region(box="-3.3,-8.4,4.8,-3.0")` (no leading space) succeeds.

### US3 - Run on AEDT 2026 R1 (P1)

**Independent Test**: config `2026.1`; `inspect_board` + `layout_region` give same layers / net counts /
region primitives as 2025.2; board file not modified.

### US4 - Cut, layout edit, PI-DC, merge on 2026 R1 (P2, later steps)

Validated on COPIES against 2025.2 results; merge/finish last (saves project in 2026 R1 format).

### Edge Cases

- Configured version not installed -> clear error listing installed versions.
- `aedt_version: "auto"` -> newest installed.
- Board saved by 2026 R1 cannot be reopened in 2025 R2 -> read-only for checks; write ops on copies.

## Requirements

- **FR-001**: Resolve AEDT root in order: config `aedt_root` -> `ANSYSEM_ROOT###` env -> Windows registry -> scan `C:\Program Files\ANSYS Inc\v*\AnsysEM`.
- **FR-002**: Set `ANSYSEM_ROOT<vid>` in-process before any pyedb / pyaedt import.
- **FR-003**: One shared `open_edb()`; always explicit `version` and `grpc=False`.
- **FR-004**: `siwave.exe` path from the resolver.
- **FR-005**: Server passes env with resolved root to child processes; free-value CLI args as `--key=value`.
- **FR-006**: `about` / `show_defaults` report resolved AEDT version + root.
- **FR-007**: No hard-coded `2025.2` defaults in function signatures.
- **FR-008**: Read-only tools MUST NOT modify the board (`isreadonly=True`).

## Success Criteria

- **SC-001**: `inspect_board` + `layout_region` pass under Claude desktop without restart (2025.2).
- **SC-002**: Same results 2025.2 vs 2026.1 (signal layers, n_nets, n_components, region primitives).
- **SC-003**: `tests/regression.py` + `tests/pidc_check.py` PASS on 2026.1 before release 0.5.0.

## Assumptions

- No package upgrade needed (pyedb 0.85.0, pyaedt 1.9.0 already latest).
- AEDT v242, v252, v261 installed on this machine; 2025.2 kept as fallback.
