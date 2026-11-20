# Implementation Plan: Layout review report redesign (033)

**Branch**: `main` (no feature branch, user repo) | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md) |
**Contract**: [contracts/review-report-033.md](contracts/review-report-033.md) | **Research**: [research.md](research.md)

## Summary

The review HTML becomes a short OK / NOT OK report: shared 3-line header, one tab per connection rendered from ONE
measurement run, Summary + sections 2.1 Routing · 2.2 Reference · 2.3 Trace stub · 2.4 Via · 2.5 Stackup (extra
sections such as Crosstalk only when they have findings), NOT OK rows only with `Issue:` / `Recommendation:` lines
taken from the rule steering files, pink dashed fault marks, no Reference data. 2.1 Routing gets a collapsed routing
box per pair (top view, cross-section, length table, zoom lock) built from routing data collected during the review
measurement (works on the snapshot). New rule `serpentine` (G ≥ 3H, A ≤ 3W, no 90°, chamfer c ≥ 1.5W −5 %); `pair_gap`
skips stretches inside a serpentine of the same pair; rule `via_count` removed. Gate (025) and JSON results keep
HIGH / MEDIUM / INFO.

## Technical Context

**Language/Version**: Python 3.12 (repo `.venv`), PyEDB 0.85 (live) or layout snapshot facade (SnapEdb)
**Primary Dependencies**: existing only (shapely, numpy for `_si`; no new package)
**Storage**: none new (review records 025 unchanged; HTML under `<board dir>/autocut/`)
**Testing**: `python -m unittest discover -s tests/unit -t .`; AEDT scripts on board copies (`tests/review_check.py`,
`pcie_check.py`, `regression.py`, `isim_check.py`) + SERLINK `design_review html` on a test1 copy
**Target Platform**: Windows 11, AEDT 2026 R1 (EDB read-only)
**Project Type**: Python package + MCP server (thin) + CLI
**Performance Goals**: HTML on the snapshot ≤ 2 × the 2.10.0 time for the same channels (SC-004)
**Constraints**: HTML English, self-contained (inline SVG / CSS / JS); code comments Vietnamese; no live board read
when the snapshot is used (FR-008)
**Scale/Scope**: SERLINK 3 connections / 12 nets; PCIe test1; board1 CPHY 2 channels

## Decided by agent (user asleep: "xong plan cứ triển khai luôn, khỏi hỏi tôi")

| Decision | Why |
|---|---|
| Pairs of the routing view and of `serpentine` = `naming.group_diff` on the first net of each series chain (as the mock); existing rules (`pair_skew`, `pair_gap`, `stackup_width`) keep their groups | mock numbers; existing results unchanged except FR-010 |
| `pair_gap`: a raw stretch is dropped when its midpoint lies in the box (+0.5 mm) of a serpentine whose pair contains the stretch's net; filtering BEFORE merging stretches (mock filtered merged findings) | a finding whose longest stretch is a serpentine but which has a real split elsewhere is still reported; count difference (if any) written in verify notes |
| Serpentine severity MEDIUM (issue, gate CONTINUE); one finding per detected serpentine with violations; detection constants as template rows | gate unchanged for length-matching style problems |
| Short texts: steering gets `## Report` (one `- Name: text` line per check shown under "This section checks:"), `## Issue` and `## Recommendation` (variants per finding / sub-case, `{placeholders}` filled by code). `Why` / `Fix` stay (JSON / guide / chat) | FR-004 single source; FR-005 |
| Fixed sections: routing, reference, trace_stub, via, Stackup (in this order, shown even when OK); other sections (e.g. Crosstalk) only when they have findings | spec FR-003; mock shows 5 rows |
| Section one-line sentences of the Summary live in `review_report.SECTIONS` (code), unknown section → steering description of its first rule | summary §2 sentences are per section, not per rule |
| Gate verdict text in the header: verdict word (STOP / CONTINUE / OVERRIDDEN) + reason translated (`high` → "NOT OK issues to resolve", `incomplete` → "review incomplete") | SC-001 (no HIGH word in the HTML) |
| Pictures: `svg_zoom` / `svg_ref_panels` draw the fault as a pink (#ff1493) dashed ring / frame; legend still returned (tests, JSON) but not rendered | FR-006 |
| Rule picture hook: REPORT entry may carry `picture(f, paths) -> html`; serpentine uses it (arrows A / G / c / W + compare lines) | new rule without HTML code edits |
| Pin pad boxes: `pin.bounding_box` of the channel's end / series pins (snapshot `pin_bbox`; live: per pin); missing → circle of the padstack pad size | FR-008 (real pads); snapshot has the boxes of window pins |
| `review.reference_html` and the old summary tables stay in `review.py` (not called) | `tests/review_check.py` / earlier goldens import them; removal = later cleanup |
| ESD branches, serpentine-near-skew-source: out of scope (spec Clarifications) | |

## Files

| File | Change |
|---|---|
| `aedt_copilot/review_checks/_serp.py` (new, private) | serpentine detection + measures (port of mock `serp.find`, constants from `R`), `found(cc)` cached per channel, `pairs(chains)`, `height(B, layer)` (H), `svg(f, paths)` |
| `aedt_copilot/review_checks/serpentine.py` + `review_rules/serpentine.md` (new) | rule: items MEDIUM "Serpentine" with `serp` measures; REPORT with `picture` and issue placeholders |
| `aedt_copilot/review_checks/pair_gap.py` | skip stretches inside a serpentine of the same pair |
| `aedt_copilot/review_checks/via_count.py`, `review_rules/via_count.md` | removed |
| `aedt_copilot/review_checks/_rules.py` | `text()` reads any variant part (issue / recommendation), `report()` passes `picture` / `fields`, `checks_lines(section)` for "This section checks:" |
| `review_rules/*.md` | `## Report`, `## Issue`, `## Recommendation` for every rule with findings; `_template.md` |
| `aedt_copilot/cut_board/review_routing.py` (new, pure) | routing data per channel (pairs, walk, cross-section SVG, top view SVG, length table, zoom JS) |
| `aedt_copilot/cut_board/review.py` | `_review_edb`: `ch["routing"]` (paths, vias, pins + pad boxes, chains, comp boxes, H, metal); pictures pink dashed, no legend; serpentine picture through REPORT hook |
| `aedt_copilot/cut_board/review_report.py` | new `render` (header, tabs, Summary, sections, Issue / Recommendation, Location, routing box); no Reference data / HIGH words |
| `templates/autocut_template.csv` | `review.serp_*` rows; `review.via_count_max` removed |
| `guides/review_measure.md` | new report (tabs, OK / NOT OK, routing view, serpentine), generated rule list |
| tests | unit: serpentine geometry, pair_gap skip, routing walk / tables, report structure (tabs, no severity words, Issue / Recommendation from steering), via_count gone; goldens 026 / 028 updated deliberately; AEDT scripts references updated + `verify-changes.md` |

## Constitution Check (2.0.1)

| Principle | Status |
|---|---|
| I Gates locked in code | PASS — gate (025) logic unchanged; serpentine MEDIUM does not STOP |
| II User data safety | PASS — review read-only; AEDT checks on copies |
| III Single source of defaults | PASS — serpentine thresholds in `templates/autocut_template.csv` |
| IV Usage rules in guides | PASS — `review_measure` + steering updated (FR-012) |
| V Regression before release | PASS — SERLINK / PCIe / board1 changes listed per channel in `verify-changes.md` |
| VI Windows & encoding | PASS — UTF-8 file writes, no PowerShell rewrites |
| VII Contracts & validation | PASS — `render` keeps its input check; contract in `contracts/` |
| VIII Package by function | PASS — routing view in its own pure module; rule = steering + code file (031) |
| IX Stable public interface | PASS — tool names / args unchanged; HTML form changes (minor version 2.11.0) |
| X Tool catalog | PASS — no tool change (see below) |

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | none (design_review / isim_review produce the new HTML / rule list) |
| Safety level of each | n/a |
| Approval flag | n/a |
| Catalog entry + contract | none |
| Registration | n/a |
| Workflows affected | none |
| New fixed-process tool | none |

## Project Structure

```text
specs/033-review-report-redesign/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md, verify-changes.md
├── contracts/review-report-033.md
└── mock/ (form reference only)
aedt_copilot/cut_board/{review.py, review_report.py, review_routing.py}
aedt_copilot/review_checks/{_serp.py, serpentine.py, pair_gap.py, _rules.py}
review_rules/*.md, templates/autocut_template.csv, guides/review_measure.md, tests/unit/test_report_033.py
```

**Structure Decision**: existing package layout (031 rule = steering + code; 026 report module pure).

## Complexity Tracking

None.
