# Feature Specification: Merged project = copy of the original board + the cut channels, stackup checked

**Feature Branch**: `main` (no branch; repo owner works on main)

**Created**: 2026-11-16

**Status**: Draft

**Input**: User (2026-11-16): "tôi muốn file gộp phải có cả file pcb gốc trước khi cut. Tức là bạn copy lại file gốc
tôi gửi, add thêm các channel của bạn đã cut vào. Bạn check lại stackup của board sau khi cut và merge, đảm bảo phải
giống với stackup gốc nhé."

## Context

- Since 5.0.0 (feature 038) `isim_go` merges the cut channels into a NEW EMPTY project `<request>/<request_id>.aedt`.
  Before 5.0.0 the cut designs were merged into the user's own board project, which already held the board.
- Bug found 2026-11-16 (test request BOARDA PCIE_U14_J25, 5.0.0): AEDT "Validation Check" on the merged project hangs
  (> 10 min, reproduced in a background AEDT on copies). The same channel design alone validates in 31 s. In the merged
  design the 4 series capacitors (C951 / C958 / C959 / C1015, set to 0 Ω) have 0 pins and no part name; their 8 pins
  are still in the layout but belong to no component. Removing the 4 capacitors and their pins → validation OK (23 s).
  Rebuilding them before the merge with a new part name (`C0402_cut`) does NOT help: pasting a design with series RLC
  parts into a new empty project loses their pins. board1 (no series parts) merges and validates fine (26 s).
- The merged project is also the user's working file: they want the full original board in it, next to the cut
  channels, and the stackup of every design identical to the original board.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Merged project starts from a copy of the original board (Priority: P1)

The user starts a request on a board. After `isim_go` the request folder holds ONE project that contains the original
board design, unchanged, plus one design per cut channel.

**Why this priority**: it is what the user asked for, and it gives the merged designs the board's own definitions
(parts, materials, padstacks) instead of an empty project.

**Independent Test**: board1 copy request with CPHY_U14_U26 → merged project has the design `main` (same as the
board) + `CPHY_U14_U26`; the user's board file is unchanged (size and date).

**Acceptance Scenarios**:

1. **Given** a request on a board given as `.aedt` (with its `.aedb`), **When** `isim_go` merges, **Then** the merged
   project is a copy of that project (all its designs) with the cut channels added as new designs.
2. **Given** a board given as `.aedb` only, **When** merged, **Then** the merged project is created from a copy of
   that `.aedb` (board design first), then the channels are added.
3. **Given** a channel name equal to a design already in the board project, **When** merged, **Then** the channel
   design is renamed `_v2`, `_v3`… (as the merge always did); the board design is never overwritten.
4. **Given** any merge, **Then** the user's original board files are never opened for writing (copy first; the copy
   lives in the request folder).

### User Story 2 - Stackup identical to the original board (Priority: P1)

After cut and after merge the tool compares the stackup of every channel design with the original board and says
whether it is identical.

**Acceptance Scenarios**:

1. **Given** a cut channel design, **When** the build finishes, **Then** the self-check compares its stackup with the
   original board: same layers in the same order, same name, type, thickness, material and fill material per layer,
   and the same material properties (permittivity, loss tangent, conductivity). Any difference → self-check NOT OK
   with one line per difference.
2. **Given** the merged project, **When** the merge finishes, **Then** the same comparison runs on every merged channel
   design (and the copied board design) as saved in the merged project; any difference → the merge result says
   NOT OK and lists the differences (M3 shows them).
3. **Given** identical stackups, **Then** the result says so ("stackup = board: OK") in the self-check and in M3.

### User Story 3 - Merged designs keep every component pin (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a channel with series parts set to 0 Ω, **When** merged, **Then** every component of the merged design
   has the same pins as the channel design (pin count and pin names per refdes, part name not empty).
2. **Given** a merged design where a component lost pins, **Then** the merge result is NOT OK for that channel with the
   component names, never silent (the channel's own design stays valid next to it).
3. **Given** the merged project of the BOARDA PCIE_U14_J25 test, **When** AEDT Validation Check runs on it, **Then** it
   finishes (no hang), like the channel design alone.

### Edge Cases

- Large boards (BOARDA ~240 MB `.aedb`): the copy takes time and disk; the request folder grows by the board size.
  The result states the size copied.
- Board project open in AEDT (`.lock`): copying is allowed (read only); the tool never deletes a lock.
- Requests merged before this feature (5.0.0–5.3.0 merged projects): unchanged; a new merge of the same request
  (re-run of `isim_go`) produces the new layout. Old merged projects with series parts are reported as affected by the
  bug in the CHANGELOG (user re-runs the merge).
- Step tools `isim_merge` / `design_merge` that merge into a project the user names: unchanged (they already merge into
  the user's project), but they get the same pin and stackup checks.

## Requirements *(mandatory)*

- **FR-001** `isim_go` merge target = copy of the original board in the request folder: `<request>/<request_id>.aedt`
  + `.aedb` copied from the board (`.aedt` + `.aedb` when the board has a project file, else the `.aedb` only).
- **FR-002** The copied board design(s) stay unchanged in the merged project (no colour, no setup, no edit).
- **FR-003** Channels are added as new designs with the existing rules (name = channel folder, conflict → `_vN`,
  backup not needed because the target is the tool's own copy).
- **FR-004** Stackup comparison (one function, used after cut and after merge): layer list in order with name, type,
  thickness, material, fill material; material properties of every material used. Tolerance: thickness ± 0.01 µm,
  properties relative 1e-6. Result: OK or the list of differences.
- **FR-005** Self-check of a cut channel includes "stackup = board".
- **FR-006** After merge, for every merged channel design: components and pins equal to the channel design, and the
  stackup check; differences → channel merge NOT OK with the lines; M3 (VI + EN) shows them.
- **FR-007** The original board files are only read.
- **FR-008** Result / M3 states the merged project path, the board design(s) inside it and the size copied.

## Success Criteria *(mandatory)*

- **SC-001** board1 copy: merged project = board design `main` (unchanged) + CPHY_U14_U26; stackup check OK for both;
  cut numbers unchanged (24 ports, 126 GND vias, shift 0.21).
- **SC-002** BOARDA PCIE_U14_J25 (copy of the test request / board): merged design keeps 4 / 4 series capacitors with
  2 pins each; AEDT Validation Check of the merged design finishes (≤ 2 × the channel alone); stackup check OK.
- **SC-003** A deliberately changed stackup (test with one layer thickness changed on a copy) → self-check NOT OK with
  that layer named.
- **SC-004** Unit tests: stackup comparison (equal / thickness / material / order / property), pin comparison, merge
  target selection (`.aedt` vs `.aedb` board), M3 text with the new lines.

## Assumptions

- "File gốc" = the board given to `isim_start` (`board`), with its project file next to it when present.
- Pasting into a project that already holds the board keeps series RLC pins (old merge behaviour, to be verified in the
  plan on the BOARDA copy; FR-006 makes any loss visible).
- Stackup data compared = what the EDB of each design holds (layers + materials); the AEDT project-level material
  library is compared through the same properties.
- Disk space for one board copy per request is acceptable.
