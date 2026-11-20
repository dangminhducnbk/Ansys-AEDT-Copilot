# Feature Specification: Review recognises pairs whose nets end with `*`

**Feature Branch**: `034-review-pair-star-nets` (work stays on `main`, user repo, no branch workflow)

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "bạn lập kế hoạch fix lỗi trace width ở trên" — the 8 NOT OK "Width vs stackup" rows on
SERLINK_U14_U15 (Layer 3 / Layer 5, 0.098–0.099 mm compared with the single-ended 0.085 mm) after the FAB stackup
table of test1 was saved (2026-11-14).

## Problem

The layout review decides which nets form a differential pair from the names of the nets that start at the first
end component of a channel (suffix `_P` / `_N`, `_DP` / `_DN`, `+` / `-`, `P` / `N`; trio `_A` / `_B` / `_C`). On
SERLINK an AC-coupled pair is two nets per member, joined by the series capacitor: `X_P` and `X_P*`. When the side
at the first component is the `*` net, the name ends with `_P*` and no pair is found. The pair is then reviewed as
two single-ended traces.

Measured on the test1 copy (2026-11-14, review with the stackup table):

| Channel | Nets starting at U14 | Pairs recognised | Visible effect |
|---|---|---|---|
| SERLINK_U14_U15 | DEVA2DEVB_* end with `*`, DEVB2DEVA_* do not | 2 of 4 | 8 false NOT OK "Width vs stackup" (0.098–0.099 mm vs SE 0.085; the 85 Ω pair width 0.101 / 0.102 mm would pass) |
| SERLINK_U14_J8 | all 4 TX nets end with `*` | 0 of 2 | no false row by chance (0.086 mm ≈ SE 0.085), but pair skew / pair gap / coupling / gap vs stackup are not checked at all |
| SERLINK_U14_U227 | no `*` | 2 of 2 | none |

Other review parts already see these pairs (serpentine, routing view use the other net of the chain), so the report
is inconsistent: the routing box shows a pair that the pair checks skipped.

## Clarifications

### Session 2026-11-14

| # | Point | Decision |
|---|---|---|
| Q1 | Which name decorations count | A trailing `*` on a pair member name (the AC-coupling side marker seen on SERLINK). Matching ignores it; the suffix rules themselves do not change. (Agent decision; other markers only if a board shows them.) |
| Q2 | Scope | Layout review only (all review checks and the routing view use one pair list per channel). The interface-simulation content proposal (Gate A diff groups) and the cut are not changed: they group the full net list, where the non-`*` names already pair. (Agent decision, keeps cut results identical.) |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pair checks see every pair of the channel (Priority: P1)

The engineer reviews a channel whose pairs are AC-coupled and named `X_P` / `X_P*`. Whatever side the trace starts
from, each pair is recognised once and gets the pair checks: width and gap vs the stackup pair values, pair skew,
pair gap, coupling.

**Why this priority**: false NOT OK rows make the engineer distrust the report; missing pair checks hide real
problems (skew is a HIGH rule that stops the cut).

**Independent Test**: review SERLINK on a test1 copy with the stackup table; compare the pair list and findings with
the 2.11.4 run.

**Acceptance Scenarios**:

1. **Given** SERLINK_U14_U15 with the FAB stackup table, **When** the review runs, **Then** 4 pairs are recognised and
   the 8 "Width vs stackup" rows on DEVA2DEVB L0 / L1 are gone (widths compared with the pair values, within 0.01 mm).
2. **Given** SERLINK_U14_J8, **When** the review runs, **Then** both TX pairs are recognised and get pair skew /
   pair gap / coupling / gap-vs-stackup results (whatever they are, they are reported, before → after listed).
3. **Given** a channel without `*` names (SERLINK_U14_U227, board1 CPHY, test1 PCIe), **When** the review runs,
   **Then** pairs, findings and counts are identical to 2.11.4.

### User Story 2 - The engineer sees the change (Priority: P2)

The release note and the verification list every finding that appears or disappears because of the fix, per
channel.

**Why this priority**: new findings on J8 (skew, gap) may change the review gate verdict; the engineer must know why.

**Independent Test**: verify-changes.md lists before → after per channel and check.

**Acceptance Scenarios**:

1. **Given** the before / after reviews, **When** they are compared, **Then** every changed row is listed with its
   reason (pair now recognised).

### Edge Cases

- Both names of a pair member end with `*` on the start side (J8): still one pair.
- A net named only `X_P*` with no `X_N*` / `X_N` partner in the channel: stays single-ended (as today).
- Trio (`_A*` / `_B*` / `_C*`): grouped like a pair (same rule).
- A pair whose start nets are `X_P` and `X_N*` (mixed): recognised (the decoration is ignored per name).
- The same base pair appearing twice (start nets `X_P*` / `X_N*` plus `X_P` / `X_N` from the other direction of the
  chain): one pair only, never counted twice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The review MUST recognise a differential pair / trio when the member names, with a trailing `*`
  ignored, follow the existing suffix rules.
- **FR-002**: Every review check that works per pair (pair skew, pair gap, coupling, stackup width and gap,
  serpentine) and the routing view MUST use the same pair list for a channel.
- **FR-003**: Each pair MUST appear once per channel, whichever net of its chain starts at the first component.
- **FR-004**: Channels without `*` names MUST give the same pairs, findings and counts as 2.11.4.
- **FR-005**: The interface-simulation content proposal and the cut MUST NOT change (Gate A diff groups identical).
- **FR-006**: The release note and verify-changes.md MUST list the before → after findings per channel (SERLINK 3
  channels, PCIe, board1).

### Key Entities

- **Pair / trio**: the nets of one differential signal in a channel, each member possibly several nets joined by a
  series part (chain); identified by the base name and suffix of a member name.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: SERLINK_U14_U15: 4 / 4 pairs recognised; "Width vs stackup" rows 8 → 0.
- **SC-002**: SERLINK_U14_J8: 2 / 2 pairs recognised (was 0); its pair-check results listed.
- **SC-003**: SERLINK_U14_U227, board1 (2 channels) and test1 PCIe: findings and counts identical to 2.11.4.
- **SC-004**: Interface-simulation regression (board1) unchanged: same diff groups, same cut numbers.

## Assumptions

- The `*` marker is the only decoration seen so far (SERLINK). Other boards may use other markers; they are out of
  scope until a board shows them.
- Review gate (025): a newly recognised pair may add a HIGH pair-skew finding and turn a channel to STOP; that is the
  intended result, reported to the user, not a regression.
- AEDT checks run on copies (test1 SERLINK + PCIe, board1), never on the user's files.
