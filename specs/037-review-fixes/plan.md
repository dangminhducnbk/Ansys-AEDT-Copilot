# Implementation Plan: Review fixes after the 4.0.0 test (037)

**Spec**: [spec.md](spec.md) · **Version**: 4.1.0 (MINOR: review rule change, no tool / CLI interface change)

## Technical Context

Python 3.12 (.venv), PyEDB 0.85 (.NET), offline unittest (`python -m unittest discover -s tests/unit -t .`), AEDT
checks on copies (`tests/pcie_check.py`, `review_check.py`, `regression.py`, `isim_check.py`).

## Constitution Check

| Principle | Status |
|---|---|
| Gates in code, never weakened | No gate touched |
| Copies only | AEDT checks on scratchpad copies of `test/test1` / board1; the user's request folder is not written |
| Template = single source of defaults | New row `review.bga_breakout_margin_mm`; row `review.pair_skew_mm` removed (job scope, never stored in user_settings) |
| One file per review rule (031) | pair_skew / pair_gap code + steering edited in their own files; guide table regenerated |
| Tool catalog (X) | No tool added / removed / renamed |

## Design (research decisions)

| # | Decision | Why |
|---|---|---|
| R1 | `review_routing.walk`: per step min distance over all unused path ends (≤ TOL_PIN); end pin = nearest not-seen pin ≤ TOL_PIN | Report item 1: first-within-0.3-mm skips arcs (0.2–0.35 mm segments) and walks back. Exact ends are the minimum, so they win |
| R2 | Walk is drawing only; `review.lengths` / via rows untouched | Numbers unchanged (SC-004) |
| R3 | BGA ends = `cc.trace["end_types"][rd] == "bga"` for comp_a / comp_b; box = `edb.components.instances[rd].bounding_box` (live and snapshot facade); unreadable box → no skip | Same classification as `isim_trace`; works on SnapEdb |
| R4 | Skip test = middle of the stretch inside box ± margin, before merging (like the 033 serpentine skip) | Report item 2 |
| R5 | `pair_skew`: `DATA_ONLY = True`, items always `[]`, data `{groups: [{group, lengths_mm, by_layer}]}`; steering findings `none`, no `## Report` / Issue / Recommendation; `review_report` routing section text "Pair gap, serpentine." | Report item 3; a data-only rule never reaches counts / answers |
| R6 | Pair box table `len_table`: Total = trace + via barrel of the chain, extra column "Vias"; header says "Total (trace + via)" | Report item 3 table; same numbers as the former pair skew lengths |
| R7 | `_store.SCHEMA` 4 → 5 | pair_gap / pair_skew logic changed in code: 4.0.0 records measured again once |
| R8 | Remove `review.pair_skew_mm` from template; tests ADDED_DEFAULTS / golden keys follow (as `via_count_max` in 033) | Report item 3 |

## Files

`aedt_copilot/cut_board/review_routing.py`, `aedt_copilot/review_checks/pair_gap.py`, `pair_skew.py`, `_store.py`,
`aedt_copilot/cut_board/review_report.py`, `review_rules/pair_gap.md`, `pair_skew.md`, `routing.md`,
`templates/autocut_template.csv`, `guides/review_measure.md`, unit tests, `tests/pcie_check.py` reference, VERSION,
CHANGELOG.md, CLAUDE.md §8.

## Verification (quickstart)

1. Unit suite.
2. Copy of test1 (= BOARDA): review PCIE_HSA2HSB_L0L1 (U14, J25, `PCIE_HSA2HSB_L*`, `PCIE_HSB2HSA_L*`): 4 / 4 cross-
   sections to J25, no pair gap at (100.59, 79.90), `skipped_in_bga ≥ 1`, no Pair skew item, P / N totals = SC-003.
3. `pcie_check.py`, `review_check.py`, `regression.py`, `isim_check.py` on fresh copies: cut numbers unchanged;
   review references updated only for pair skew / BGA pair gap.
