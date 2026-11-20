# Implementation Plan: Coded rules from the PCIe self-test

**Branch**: `main` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

## Summary

1. **Connector end default** (FR-001..003, Principle III):
   - Template row `interface_sim.connector_handling` (job, text, default `smd_rebuild`; must be one of
     `OPTIONS["connector_end"]`, else `smd_rebuild` + warning in `thresholds`).
   - `ends.classify_unusual`: a connector no longer adds the `connector_end` unusual question; `_measure` sets
     `end["default_handling"] = {rule: connector_end, value, options, source: "team default"}`. Other unusual rules
     (no GND near signal, pad mismatch...) still ask as today.
   - `settings.effective_handling(ends, handling, kept=None)` = team defaults < handling kept from the previous run
     (re-cut, 004) < handling given by the engineer. `validate` checks a given handling of a defaulted end against its
     options. `validate_for` returns `handling` (effective), `table_md` shows it; `apply.run` / `reapply` use and
     store the effective handling in `user_settings` (FR-002).
   - `recut.compare_handling`: a defaulted end counts as having rule `connector_end` → old choice `kept`.
   - `form._tab`: defaulted ends appear in `unusual` with `default`; `handling` prefilled with the default.
   - `ends_md` / `ends.check` output: `default_handling {refdes: value}`, table "End handling (team default)".
   - Cut geometry unchanged: `cutter.apply_stage` with `smd_rebuild` = today's SMD rebuild (own GND pins, plate only
     without GND pins). Old `ends.json` with `connector_end` unusual still validates (stored choice wins).
2. **Series parts in the self-check** (FR-004): `apply.self_check` reads every series part of the content in the saved
   design: `{refdes, type (content), part, nets, model: "short", r_ohm (read back), ok}`; key `series`. Also in
   `cutter.check`? No (Excel flow unchanged).
3. **Port metric** (FR-005): `signal_paths(nets, series)` = connected groups of nets joined by 2-net series parts
   (union-find, pure). `self_check` key `expected_ports_2x_paths` (+ `signal_paths`) replaces `expected_ports_2x_nets`;
   mismatch `ports vs 2 x signal paths` when different. board1: 24 / 18 unchanged (no series).
4. **Review lines** (FR-006): `review.issue_lines(items)` = unique `"check: value"` lines in order; used by HTML card
   list, overview tooltip, `review()` summary `top`, and `review_checks._report.point`. Findings, counts, points,
   severities unchanged.
5. **Guides** (FR-007): `review_measure` — judge via stub vs interface data rate (quarter-wave / Nyquist rule of thumb),
   state the reason; `interface_sim` — connector default handling, tell the engineer series caps are shorted (list from
   self-check), port metric.
6. Check script `tests/pcie_check.py` (FR-009) on a test1 copy; version 0.13.0.

## Kitchen check

| Item | Answer |
|---|---|
| Utensils added | none |
| Process tools added | none |
| Tool names / inputs | unchanged (outputs gain keys: `default_handling`, `self_check.series`, `expected_ports_2x_paths`) |
| Safety / gate | unchanged |
| Catalog + contract | no new entry; output change written in `contracts/output-changes.md` |
| Registration | n/a |
| Recipes affected | none (interface-sim steps unchanged) |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| Changed code | `interface_sim/{ends,settings,apply,recut,form}.py`, `cut_board/review.py` (line dedupe only), `review_checks/_report.py`, `templates/autocut_template.csv` (+1 row) |
| Unchanged | `cut_board/cutter.py`, Excel flow, review findings / severities |
| Tests | offline: classify (connector → default, no unusual), effective handling order, validate of defaulted end, compare_handling kept, form prefill, signal_paths, issue_lines, self_check series (fake EDB); AEDT: `tests/pcie_check.py` on test1 copy, `tests/regression.py`, `tests/isim_check.py`, `tests/review_check.py` on board1 copies |

## Constitution Check (1.2.0)

| Principle | Check | Status |
|---|---|---|
| I Gates | handling still agreed at Gate B (default shown, overridable) | PASS |
| II Data safety | copies only | PASS |
| III Defaults | connector handling from template row | PASS |
| IV Guides | `review_measure`, `interface_sim` updated | PASS |
| V Regression | board1 references unchanged | PASS |
| VII Contracts | `contracts/output-changes.md` | PASS |
| IX Stable interface | tool names / inputs unchanged; output keys added, one renamed (`expected_ports_2x_nets` → `_paths`) | PASS |
| X Kitchen | see Kitchen check | PASS |
