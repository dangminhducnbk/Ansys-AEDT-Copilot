# Implementation Plan: More layout review rules (030)

**Branch**: `main` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/review-rules.md](contracts/review-rules.md)

## Summary

Six new check modules in `review_checks/` (028 interface: `run` + `REPORT`), sharing pure geometry helpers
(`_si.py`) and a lazily computed pair / trio context in `ChannelCtx`. Thresholds = new template rows `review.*`
(they enter the 025 record key automatically). Rule 6 compares width / pair gap per layer with a per-board stackup
table (`_stackup.py`), saved by a new MCP tool `review_stackup_table` (get / template / save, save gated by
`user_confirmed_table`). All run in every review (snapshot or live); the HTML report runs them through
`review._extra_findings` (028). Existing 4 checks: findings unchanged; finding / point ids renumber because new
findings join the same sorted list (documented).

## Rules

| # | Module (NAME) | Finding | Severity | Section | How |
|---|---|---|---|---|---|
| 1 | `pair_skew` | Pair skew | HIGH | routing | group (naming.group_diff) chain lengths (review.lengths, trace + via barrel): max − min > `review.pair_skew_mm` |
| 2 | `pair_gap` | Pair gap | MEDIUM | routing | per member sample (sample step) on each layer: edge gap to the nearest other member trace; nominal = stackup table gap or median; runs with gap > nominal × `review.pair_gap_ratio` ≥ `review.pair_gap_min_len_mm`; neck-down zone skipped |
| 3 | `coupling` | Coupling to other net | MEDIUM | Crosstalk | other-net traces (not reference nets) on the same layer in the channel window; edge gap < `review.coupling_gap_factor` × width over ≥ `review.coupling_min_len_mm` |
| 4 | `plane_edge` | Near plane edge | MEDIUM | reference | for each reference plane: centre covered by GND but a point at D = max(`review.plane_edge_factor` × H, `review.plane_edge_min_mm`) to either side is not (H = copper-to-copper height from the stackup elevations); runs ≥ `review.plane_edge_min_len_mm` |
| 5 | `via_count` | Via count | MEDIUM | via | via stacks per chain > `review.via_count_max`; members of a group with different counts |
| 6 | `stackup_width` | Width vs stackup / Pair gap vs stackup / No stackup value | MEDIUM / INFO | Stackup | per path width vs table (single-ended or pair width) and per group / layer median gap vs table, \|Δ\| > `review.stackup_tol_mm`; no table / no layer entry → INFO |

Neck-down zone `review.neckdown_zone_mm` (1 mm) around pads / vias of the channel: skipped by rules 2, 3, 4, 6.

## Stackup table

- File `<board dir>/Ansys AEDT Copilot/stackup/<board stem>.json`:
  `{board, source_file, confirmed_at, note, layers: {<signal layer>: {se_width_mm, pairs: [{name, width_mm, gap_mm}]}}}`.
- Tool `review_stackup_table(board, op=get|template|save, table, source_file, user_confirmed_table)`: template =
  board signal layers with empty values; save validates layer names / positive mm values, backs up the old file
  (`move_aside`), needs `user_confirmed_table=true` (Claude read the fab PDF / Excel, showed the table, user said OK).
- Record key: `current_thresholds(board)` adds the table hash → a changed table re-measures (025 reuse rule).

## Plumbing

- `Ctx(edb, log, board=None)`; `measure_edb(..., board=)`; `review._review_edb(..., aedb)` → `_extra_findings`.
- `ChannelCtx.groups` (cached): chains, groups, chain lengths (as routing).
- Report: new sections "Crosstalk", "Stackup" via REPORT; routing note text unchanged when routing has no rows.

## Tool catalog check

| Item | Answer |
|---|---|
| New tool | `review_stackup_table` (group review, kind tool, safety read — writes only under `Ansys AEDT Copilot/stackup/`; gate `user_confirmed_table` on op=save) |
| Contract | `contracts/review-rules.md` |
| Workflows | none |

## Technical Context

| Item | Value |
|---|---|
| Tests | `tests/unit/test_review_rules_030.py`: each rule on fake geometry (flag / no flag / neck-down / min length), stackup table validate / save gate / hash in thresholds, REPORT contract (028 test covers), tool + CLI refusals, goldens (tool list, template rows) |
| AEDT copies | board1 `review_check.py` (4-check golden compared with checks restricted to the 4), HTML sections; `regression.py`, `isim_check.py` (verdict expectations updated if rule 1 flags); test1 `pcie_check.py` (review counts reference updated with the new numbers); numbers per rule reported |

## Constitution Check (2.0.1)

| Principle | Status |
|---|---|
| I Gates: new save gate; rule 1 HIGH feeds 025 STOP (user accepted) | PASS |
| II Data safety: board never written; table file only under Copilot folder, old file moved aside | PASS |
| III Defaults: template rows | PASS |
| IV Guides: review_measure (rules, thresholds, stackup table) | PASS |
| V Regression: references updated on purpose (new findings) | PASS |
| VII Contracts / X Catalog: contract + catalog entry + tests | PASS |
