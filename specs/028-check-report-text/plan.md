# Implementation Plan: Report text lives in the review check file

**Branch**: `main` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/check-report.md](contracts/check-report.md)

## Summary

Move the per-finding report knowledge out of `cut_board/review_report.py` into the check modules as an optional
`REPORT` dict keyed by finding name; `review_report` merges the registry's `REPORT`s; generic fallback kept. The
HTML report also runs registry checks beyond the built-in four so a new rule reaches it. Output of the 4 checks is
byte-identical (golden pre028 from 2.6.0).

## Design

| Piece | Where | What |
|---|---|---|
| Helpers | `review_checks/_text.py` (private) | `mm`, `num`, `planes`, `via_row` (moved verbatim from review_report) |
| reference.py | `REPORT` | SOV, Loss of reference, Ref to other net: section `reference`, title, limit_key, describe, layers |
| trace_stubs.py | `REPORT` | Trace stub: section `trace_stub` |
| vias.py | `REPORT` | Ref plane change (section `reference`), Nearest GND via, Via stub (section `via`) |
| routing.py | `DATA_ONLY = True` | no finding |
| review_report | `report_specs()` | merged `{finding: spec}` from `review_checks.checks()`; duplicate finding name → `RegistryError`; `section_of`, `explain`, `row_layers` use it, fallback unchanged; `SECTIONS` keeps the fixed order (key, title, prefix) and no longer lists checks |
| review.review | `_review_edb` | after the built-in measures: registry checks not in `BUILTIN` (reference, trace_stubs, vias, routing) run on a `ChannelCtx` sharing the Board; their findings join `fs` before sort / ids |
| Example | `review_checks/_example.py` | not registered (underscore); commented skeleton with REPORT |
| Docs | guide `review_measure` "Developer: add a review check"; CLAUDE.md note under review_checks |

Section of a finding whose spec names a section that is not one of the fixed four: new section, title = that name,
prefix = initials (existing rule).

## Tool catalog check

No tool / schema / catalog change.

## Technical Context

| Item | Value |
|---|---|
| Tests | `tests/unit/test_check_report_028.py`: golden HTML + explain / layers / sections equal; registry contract (every finding of a module described or DATA_ONLY; no duplicate); fake new check module (temp package registered via mock) → own section, rows / Why / Fix, layers; check without REPORT → generic; review.review runs an extra registry check (fake EDB path via snapshot fixture) |
| AEDT | board1 copy: `tests/review_check.py` (HTML identical, numbers unchanged) + HTML text diff vs 2.6.0 file |

## Constitution Check (2.0.1)

| Principle | Status |
|---|---|
| III Defaults / IV Guides | guide developer note | PASS |
| V Regression | golden + review_check | PASS |
| VII Contracts | contract file + registry contract test | PASS |
| VIII Package by function | rule text with its rule (check module) | PASS |
| IX Stable interface | no tool change; patch | PASS |
