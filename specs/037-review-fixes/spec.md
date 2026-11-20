# Feature Specification: Review fixes after the 4.0.0 test (037)

**Feature Branch**: `main` (no branch; repo works on main)

**Created**: 2026-11-15

**Status**: Draft

**Input**: User: "Sửa lại tool theo report của session test", report
`D:\data\client_boarda\for_ai_testing\fix_review_issues.md` (test session, 2026-11-15, board BOARDA,
interface PCIE_HSA2HSB_L0L1, U14 → J25, 12 nets, request `20261115_122953`). Three items:

1. Cross-section of `PCIE_HSB2HSA_L0_P` stops on Layer 14 after 237.1 mil with "path not traced to the last pin"
   (bug in the drawing: the path walk takes the FIRST path end within 0.3 mm, not the nearest; at a dense chain of
   short lines + arcs it skips arcs and walks back).
2. Pair gap inside the BGA area is an intentional break-out (user rule 2026-11-15): never NOT OK there.
3. Pair skew: the allowed skew depends on each interface spec, which the user knows. The tool only reports the P / N
   lengths: no threshold, no OK / NOT OK, no question, no recommendation (user rule 2026-11-15).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cross-section reaches the last pin (Priority: P1)

The engineer opens a pair box of the review and sees the cross-section from the first end pin to the last end pin with
every via on the way, also where the trace is a dense chain of short segments and arcs.

**Independent Test**: unit test with the real geometry of the dense chain at (101.3–102.7, 79.3–80.1) mm (net
`PCIE_HSB2HSA_L0_P`, Layer 14, from the snapshot window); the walk reaches the J25 pin.

**Acceptance Scenarios**:

1. **Given** the PCIE_HSA2HSB_L0L1 review, **When** the HTML is written, **Then** all 4 pairs are drawn to J25, no
   "path not traced to the last pin" note, and `PCIE_HSB2HSA_L0_P` shows Vias: 2 (18D8 through, 18D10 blind L14 →
   Bottom).
2. **Given** any review, **When** measured, **Then** lengths and via stub numbers are unchanged (the walk is drawing
   only).

### User Story 2 - No pair gap NOT OK inside a BGA body (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a pair split whose middle lies inside the body box of a BGA end (+ `review.bga_breakout_margin_mm`,
   default 0), **When** reviewed, **Then** no item is produced; the count of skipped stretches is in the check data
   (`skipped_in_bga`).
2. **Given** a split outside every BGA body, **Then** it is reported as before.

### User Story 3 - Pair skew = lengths only (Priority: P1)

**Acceptance Scenarios**:

1. **Given** any review, **Then** no Pair skew item exists (no NOT OK, no OK row, no Issue / Recommendation); NOT OK
   counts, `findings_md`, `summary_md`, `answer_md` never mention skew.
2. **Given** the HTML, **Then** each pair box has a P / N length table: Net | Total (trace + via) | per layer | Vias,
   through series parts, no status column, no colour.
3. **Given** the template, **Then** `review.pair_skew_mm` no longer exists; nothing else reads it.
4. Same for `design_review` (standalone).

### Edge Cases

- Two path ends at the same distance: either is taken (data is continuous); an exact end (≤ 1 µm) always wins.
- No BGA end (SMD / connector ends): pair gap unchanged.
- Body box not readable: no skip for that part (reported as before).
- Old review records: thresholds changed → measured again once.

## Requirements *(mandatory)*

- **FR-001**: The routing walk takes, at each step, the nearest end among all unused paths (accepted only ≤ 0.3 mm) and
  the nearest end pin.
- **FR-002**: Pair gap skips a stretch whose middle lies in the body box of a BGA end of the channel (+ margin key);
  counted in `skipped_in_bga`.
- **FR-003**: New template key `review.bga_breakout_margin_mm` (mm, num, job, default 0).
- **FR-004**: Pair skew produces no item; its data = per pair `{group, lengths_mm, by_layer}`; rule is data only.
- **FR-005**: Pair box length table adds Vias column; Total = trace + via barrel (= `routing` / former pair skew
  lengths).
- **FR-006**: Template key `review.pair_skew_mm` removed; steering `review_rules/pair_skew.md` and
  `review_rules/pair_gap.md` updated; guide rule table regenerated.

## Success Criteria *(mandatory)*

- **SC-001**: PCIE_HSA2HSB_L0L1 (copy of BOARDA): 4 / 4 cross-sections reach J25.
- **SC-002**: Same channel: no Pair gap item at (100.59, 79.90) mm, `skipped_in_bga ≥ 1`; NOT OK count lower by the 4
  pair skew items and the BGA pair gap item.
- **SC-003**: P / N totals in the HTML = 108.137 / 109.053, 109.039 / 110.283, 108.525 / 111.086, 107.409 / 110.304 mm.
- **SC-004**: Cut results unchanged (regression / isim_check / pcie_check cut numbers).

## Assumptions

- "BGA end" = end type `bga` from the channel trace (as `isim_trace` end_types).
- Release 4.1.0 (minor: rule change, no tool interface change), local tag only.
