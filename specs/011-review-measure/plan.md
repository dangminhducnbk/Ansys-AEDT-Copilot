# Implementation Plan: Review layout — code measures, agent interprets

**Branch**: `main` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

## Summary

1. **Checks registry** `aedt_copilot/review_checks/` (FR-001, Principle VIII): one module per check, registry entries
   `NAME, ORDER, SEVERITY_RULE, run(cctx) -> {"items": [...], "data": {...}}`:
   | Check | Code reused (unchanged) | Items (suggested severity, today's rules) |
   |---|---|---|
   | `reference` | `review.check_reference` | SOV (MEDIUM), Ref to other net (MEDIUM), Loss of reference (HIGH) |
   | `trace_stubs` | `review.trace_stubs` | Trace stub (MEDIUM) |
   | `vias` | `review._stacks` + `review.via_rows` | Via stub (MEDIUM), Nearest GND via (MEDIUM), Ref plane change (HIGH / INFO); data: via rows |
   | `routing` | `review._chains` + `review.lengths` | none; data: length per chain / layer, widths, pair / trio skew + layer match |
   Shared lazy context `_context.py` (board index, trace, collected primitives, window, copper index ONLY when
   `reference` runs, via rows shared by `vias` / `routing`) → one check alone does not pay for the others (SC-002).
   A check raising → `{"error": ...}` for that check, others continue. No plane layer → `reference` returns
   `{"error": "no plane layer"}`.
2. **Measure API** `review_checks.measure(board, channels, checks=None, cell="")` and
   `measure_channels(board, specs, ...)` (specs = `[{comp_a, comp_b, patterns}]`): same order / ids / point grouping as
   `review.review()` (findings sorted `(severity, check, net, x)`, ids `c.i`, `review.points`) → numbers identical to
   today (FR-003). Output in mm, JSON-safe; `summary_md` = table of suspect points (HIGH / MEDIUM, numbers).
3. **Old path unchanged** (FR-010): `review.review()`, `review_layout`, its HTML, Gate 1 and `propose_channels` lock are
   not edited. HTML on request (FR-007) = `review.review()` on the same board / channels (same HTML as today).
4. **Utensil** `design_review(board, channels, checks="", cell="", html=False)` (read). CLI
   `review-measure --board --channels [--checks] [--cell] [--html]`.
5. **Interface simulation step** (FR-008/009): process tools (thin wrappers on the request state):
   - `isim_review(request_id, name, checks="", html=False)` — interface at `content_agreed` or later; measures the
     agreed `comp_a / comp_b / nets`; writes `<interface>/review.json`; returns items + `summary_md`.
   - `isim_review_decide(request_id, name, decisions)` — decisions `[{point, decision accepted|dismissed,
     severity_final?, reason?, note?}]`; point ids must exist in `review.json`; `severity_final` ≠ suggested needs a
     reason; saved in `user_settings.json` section key `review` (`{measured_at, review_json, decisions[]}`), no new file.
6. **Guides / recipes**: new guide `review_measure` (interpretation rules = today's severity rules as guidance, summary
   format, cite numbers only, change severity only with reason, decisions); `interface_sim` Phase 1.6 optional review;
   team recipe `layout-review` (design_review); recipe `interface-sim` gains optional step `isim_review`.
7. Version 0.12.0 (minor: new tools); ROADMAP 011 done.

## Kitchen check

| Item | Answer |
|---|---|
| Utensils added | `design_review` (utensil, group review): board / design + channels → measurements per check |
| Process tools added | `isim_review`, `isim_review_decide` (group interface-sim) — justification: thin wrappers binding `design_review`'s measure to the request (agreed nets, `review.json`, decisions in `user_settings`); no logic of their own |
| Safety / gate | all `read` (reports / request files only; board never written) — no gate |
| Catalog + contract | 3 entries, `contracts/review-checks.md`, `contracts/mcp-tools.md` |
| Registration | `@tool()` |
| Recipes affected | new `layout-review`; `interface-sim` optional step `isim_review` (checkpoint) |
| New fixed-process tool | none beyond the two wrappers above |

## Technical Context

| Item | Value |
|---|---|
| New code | `aedt_copilot/review_checks/{__init__,_context,_report,reference,trace_stubs,vias,routing}.py`, `interface_sim/review.py` |
| Changed code | `mcp_server/server.py` (+3 tools), `kitchen/catalog.py` (+3), `__main__.py` (`review-measure`), `interface_sim/{api,user_settings}.py`, guides, recipes |
| Unchanged | `cut_board/review.py` (byte-identical), `review_layout`, Excel flow |
| Tests | offline: registry, lazy context (fake), error isolation, ordering / ids, decisions validation, user_settings key; AEDT on board1 copies: `tests/review_check.py` (all checks vs old `review()` captured data: identical findings / via rows / lengths; one check timing; isim_review + decide) |

## Constitution Check (1.2.0)

| Principle | Check | Status |
|---|---|---|
| I Gates | no write to designs; isim_review needs agreed content (state) | PASS |
| II Data safety | read-only EDB | PASS |
| III Defaults | thresholds from `review.*` rows | PASS |
| IV Guides | `review_measure`, `interface_sim` updated | PASS |
| V Regression | old review byte-identical source; numbers compared on board1 | PASS |
| VII Contracts | `contracts/` for package + tools | PASS |
| VIII Package by function | one module per check, registry | PASS |
| IX Stable interface | additions only | PASS |
| X Kitchen | see Kitchen check | PASS |
