# Implementation Plan: Review recognises pairs whose nets end with `*` (034)

**Spec**: `specs/034-review-pair-star-nets/spec.md` | **Date**: 2026-11-14 | **Version**: 2.12.0 (minor: review
results change for boards with `*` names)

## Summary

One review pair function, `naming.review_groups(names)`: the existing `group_diff` rules applied to the names with a
trailing `*` removed, the result mapped back to the original names (one entry per base name). All review places that
build pairs use it; `group_diff` itself stays unchanged (interface-simulation content / Gate A keep their grouping).

## Technical Context

Python 3.12 (repo `.venv`), no new dependency. Review pair sites today:

| Site | Input | Today |
|---|---|---|
| `review_checks/_context.py` `groups` (pair_skew, pair_gap, coupling, stackup_width, plane / paired nets) | start nets | `group_diff` → misses `*` starts |
| `review_checks/routing.py` | start nets | same |
| `cut_board/review.py` `_review_edb` (HTML lengths / skew tables) | start nets | same |
| `cut_board/review_routing.py` `groups` (routing view) | first net of each chain | works by chance (chain order) |
| `review_checks/_serp.py` `pairs` (serpentine) | first net of each chain | works by chance; P-first sort ignores `*` |

## Constitution Check

- Spec Kit flow: spec → plan → tasks → implement → converge (this file). ✓
- Principle I gates: no gate change. ✓
- Cut / interface simulation untouched (FR-005): `group_diff` and `interface_sim/content.py` not edited. ✓
- Tool catalog: no new MCP tool, no contract change (review output fields unchanged, values change). ✓
- Tests: unit tests offline + AEDT checks on copies (test1 SERLINK / PCIe, board1). ✓

## Design

- `naming.review_groups(names)`: `base = {}`; for each name sorted: key = name without trailing `*` → keep the first
  original per key; `group_diff(keys)` → map each member back to its original name. Same order / shape as
  `group_diff` (list of lists).
- Replace `naming.group_diff` by `naming.review_groups` in the 5 review sites; `_serp.pairs` P-first sort uses the
  name without `*`.
- Review records (025, `review_checks/_store.py`): the key holds board / ends / nets / checks / thresholds, not the
  code version, so interface simulation could reuse a 2.11.x record measured with the wrong pairs. `SCHEMA` 1 → 2:
  older records are no longer read (re-measured once, seconds on the snapshot). No test depends on schema 1.

## Verification

- Unit: `review_groups` (`X_P*` / `X_N*`, mixed `X_P` / `X_N*`, trio `_A*`, lone `X_P*`, both `X_P` and `X_P*`
  present → one pair, plain names = `group_diff`); `_context.groups` on a fake trace with `*` starts gives the pair;
  `_serp.pairs` order P first with `*`.
- AEDT copies: SERLINK 3 channels (snapshot) before (2.11.4 record) → after; `tests/pcie_check.py`,
  `tests/review_check.py`, `tests/regression.py` (board1) unchanged. Results in `verify-changes.md`.
