# Feature Specification: More layout review rules (pair skew, pair gap, coupling, plane edge, via count, width / gap vs stackup table)

**Feature Branch**: `030-review-rules-si` (work stays on `main`; 029 = layout_region on snapshot, other session)

**Created**: 2026-11-11

**Status**: Clarified

**Input**: User: "Theo những gợi ý của bạn. Ngoài ra cho tôi thêm luật check trace width, spacing so với stackup."
Rules 1–5 = suggestions accepted by the user; rule 6 = the user's new rule.

## Clarifications

### Session 2026-11-11

- User correction (rule 6): "Không cần tính trở kháng, chỉ cần so sánh spacing giữa 2 dây và trace width của dây có
  giống trong stackup hay không là được." → NO impedance calculation (Q-b dropped; no dielectric / Dk data needed).
  Rule 6 = compare each signal trace's width per layer, and the gap between the two traces of a pair per layer, with
  the values the stackup specifies for that layer / interface (Q-a = per-layer width / gap table).
- User answer (verbatim) "Theo đề xuất của bạn." →
  - Q-a2 → A: the user gives the fab stackup file (PDF / Excel); Claude reads it ONCE into a per-layer width / gap
    table, the user confirms it, the tool stores it (per board); re-import / edit = same tool again.
  - Q-c → A: width or pair gap differing from the table by more than ±0.01 mm → MEDIUM (never stops the cut).
  - Q-d → A: defaults as proposed, editable template rows: rule 1 pair / trio length skew > 0.127 mm (5 mil) HIGH;
    rule 2 pair gap > nominal × 1.5 over ≥ 0.5 mm MEDIUM; rule 3 edge gap to another net < 3 × width over ≥ 2.5 mm
    MEDIUM; rule 4 trace centre closer than 3 × dielectric height (min 0.2 mm) to its reference-plane / void edge
    over ≥ 0.5 mm MEDIUM; rule 5 > 2 vias per net, or pair / trio members with different via counts, MEDIUM;
    neck-down zone 1 mm around pads / vias skipped by width / gap / spacing rules.
  - Q-e → A: every review incl. the mandatory 025 review; only rule 1 can be HIGH (STOP).
  - Guide must tell Claude how the user changes a rule threshold and where the stackup table is stored / how to
    re-import or edit it.

### Decided by agent (user asleep, 2026-11-11: "bạn cứ chạy và tự làm tiếp, không cần hỏi tôi")

- Rule 2 (and the gap part of rule 6) applies to 2-member diff pairs only; CPHY trios get rule 1 (skew) only
  (board1 trios are not routed side by side: median member gap 1.6 mm → 73 meaningless rows).
- Rules 2, 3, 4 give one row per net / layer (/ plane / other net) with the longest stretch located, number of
  stretches and total length (first board1 run gave 201 + 73 rows).
- Rule 4 ignores voids ≤ 2 mm (antipads of nearby vias, same rule as SOV's own antipad).
- No per-run threshold argument (it would change the tool schemas): thresholds = template rows; the guide tells
  Claude how the user gets one changed.
- Stackup table tool `review_stackup_table` (new MCP tool), save gated by `user_confirmed_table`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pair / trio integrity (Priority: P1)

The review flags a diff pair / CPHY trio whose members differ in length beyond a limit (rule 1, HIGH), whose
members split apart beyond a gap limit over a minimum length (rule 2, MEDIUM), or whose members have different via
counts / too many vias (rule 5, MEDIUM).

**Independent Test**: board1 U21_J25 / U14_U26 and test1 PCIe: numbers per pair (skew mm, max gap deviation, via
counts) reported and plausible vs the routing data already measured (lengths per net, 011).

### User Story 2 - Return path and crosstalk (Priority: P1)

The review flags a signal trace closer than a limit to the edge of its reference plane / a void edge (rule 4), and a
signal trace running parallel to another net closer than a gap for longer than a length (rule 3).

### User Story 3 - Width / gap vs the stackup table (Priority: P1)

Per signal layer the review compares each trace's width, and the gap between the two traces of a pair, with the
width / gap the stackup specifies for that layer (and interface: single-ended / diff pair type). A mismatch beyond the
tolerance is flagged; the row shows layer, measured width / gap, stackup value, difference. No impedance is
computed.

### Edge Cases

- Neck-down near pins / BGA break-out: width / gap / spacing rules skip a zone around pads (template distance).
- Layer / interface without a stackup width / gap entry (rule 6) → INFO "no stackup value for <layer>" (no guess).
- Existing 4 checks: results unchanged (numbers, ids, points, HTML).

## Requirements *(mandatory)*

- **FR-001**: Each rule = one file in `aedt_copilot/review_checks/` with the 028 `REPORT` interface (title, labelled
  rows value vs limit, Why, Fix, involved layers, section).
- **FR-002**: Thresholds = template rows `review.*` (Gate B / design_review values), defaults per Q-d.
- **FR-003**: Rules run on the layout snapshot (trace width / centre line / pairs already there); no dielectric data
  needed; live fallback as 023.
- **FR-004**: Severity feeds the 025 gate (HIGH → STOP) and the 026 report sections (Routing / new "Stackup").
- **FR-005**: Rule 6 = measured width / pair gap per layer vs the stackup table (source per Q-a2), tolerance /
  severity per Q-c. No impedance calculation.
- **FR-006**: Existing 4 checks unchanged (`tests/review_check.py`, regression references).
- **FR-007**: Guide `review_measure` lists the new rules and how to read them.

## Success Criteria *(mandatory)*

- **SC-001**: board1 + test1 copies: existing results unchanged; each new rule reports plausible numbers (listed in
  tasks.md verify table); HTML shows the new sections.
- **SC-002**: Rule 6 flags exactly the traces / pair segments whose width / gap differ from the table beyond the
  tolerance (unit test with a fake table + fake traces, incl. neck-down zones skipped).

## Assumptions

- Pairs / trios = `naming.group_diff` groups (P/N, _DP/_DN, +/-, CPHY _A/_B/_C), as routing (011).
- Minor release (2.7.0) after user review; not released here.
