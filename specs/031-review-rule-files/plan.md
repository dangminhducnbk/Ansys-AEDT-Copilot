# Implementation Plan: One file per layout review rule (031)

**Branch**: `main` | **Date**: 2026-11-11 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/review-rules.md](contracts/review-rules.md)

## Summary

A rule = one steering file `review_rules/<id>.md` (repo, team) + at most one code file
`aedt_copilot/review_checks/<id>.py`. Title, report section, finding titles, limit key (hover) and the report's Why /
Fix sentences are read from the steering file (single source); the code keeps measuring, labelled rows and picture
layers. `reference` splits into `sov`, `ref_other_net`, `loss_of_reference` (one cached `check_reference` run shared);
`vias` into `via_stub`, `nearest_gnd_via` and `ref_plane_change` (cached `via_rows` shared). Old names stay as
`select()` aliases. Personal rules: `~/.aedt_copilot/review_rules/` (env `AEDT_COPILOT_REVIEW_RULES`), team wins on id
clash (personal shown shadowed), personal code runs only when enabled. New MCP tool `review_rules`
(list / get / enable / disable). Guide `review_measure` keeps the process + a generated rule list.

## Decided by agent, user asleep

| Decision | Why |
|---|---|
| Steering folder `review_rules/` at repo root (like `guides/`, `workflows/`) | team files the owner edits; served by a tool |
| Report text single source: steering sections `## Why` / `## Fix` hold the exact report sentences (`{placeholders}` filled by the code; `- \`variant\`: text` bullets for rules with several findings) | byte-identical report, one place to edit |
| Finding titles / section / limit key in the steering header table | report reads them from there |
| New tool `review_rules` (catalog + contract + tests) instead of overloading `get_guide` | Principle IX: `get_guide` schema / description unchanged |
| Enabling personal code: `review_rules(op="enable", rule_id, user_approved_personal_code=true)` → `<personal>/enabled.json` | personal code never runs silently (Q3 B) |
| Steering-only rule (md without code): listed, `has_code=false`; Claude judges it on request; never in measure results, never in the gate (Q2 A) | |
| Result `checks` keys / `checks_run` use the new rule ids; findings, ids, points, severities, HTML identical | 025 records of 2.8.0 are not reused (checks list differs) → measured again once (seconds on the snapshot) |
| Rule `routing` keeps the via-independent length data; the via table moves from `checks.vias.data.rows` to `checks.via_stub.data.rows`; `plane_layers` data to `checks.sov.data` | data follows the rule that owns it |

## Files

| Piece | Change |
|---|---|
| `review_rules/*.md` (14) | sov, ref_other_net, loss_of_reference, ref_plane_change, trace_stubs, via_stub, nearest_gnd_via, routing, pair_skew, pair_gap, coupling, plane_edge, via_count, stackup_width; `_template.md` (not a rule) |
| `review_checks/_rules.py` | folders, parse (header table, sections, variants), `rules()` list (team + personal, shadowed, enabled), `get(id)`, `text(id, part, variant, **fmt)`, `report(id, describe, layers)` → REPORT entries, `personal_modules()`, enable / disable |
| `review_checks/{sov, ref_other_net, loss_of_reference, ref_plane_change, via_stub, nearest_gnd_via}.py` | new; `reference.py`, `vias.py` removed |
| 030 rule files + `trace_stubs.py` | REPORT via `_rules.report`; Why / Fix strings removed from code |
| `review_checks/__init__.py` | `checks()` = team + enabled personal code; `select()` aliases reference / vias |
| `cut_board/review.py` | BUILTIN_CHECKS = new ids |
| tool `review_rules` + CLI `review-rules` + catalog + contract | list / get / enable / disable |
| guide `review_measure` | per-rule text removed (2d table, H4, H5); process + `<!-- rules:begin/end -->` generated list (CLI `review-rules --op=guide-list` regenerates; unit test keeps it current) |

## Tests

`tests/unit/test_review_rules_031.py`: every registered rule has a complete steering (mandatory parts); every steering
with `code` has the module and vice versa; REPORT why / fix equal the steering text; personal folder: clash → team
wins + shadowed, personal steering-only listed, personal code not loaded until enabled, enabled → measured + labelled
personal; aliases; guide list current. Goldens: pre028 report / explain identical; 014 / 020 tool + command lists.

## AEDT (copies, one after another)

board1 `review_check.py` (golden pre023 on the 4-old-check aliases; HTML live vs snapshot; HTML byte compare vs a
2.8.0 HTML of the same copy), `regression.py`, `isim_check.py`; test1 `pcie_check.py` (21 / 57 / 25).

## Constitution Check (2.0.1)

| Principle | Status |
|---|---|
| III Defaults: thresholds stay in the template; steering names keys only | PASS |
| IV Guides: rule steering = guides for Claude, served by a tool | PASS |
| V Regression: identical results; golden + AEDT | PASS |
| IX / X: new tool with catalog entry, contract, tests; gate for personal code | PASS |
