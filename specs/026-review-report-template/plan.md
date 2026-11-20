# Implementation Plan: Layout review report template

**Branch**: `main` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/review-report.md](contracts/review-report.md)

## Summary

The HTML report becomes a fixed view of the same review data: header (+ 025 gate verdict) → Summary (one row per
category section, counts per severity per channel, worst severity, danger verdict) → one Detail section per category
(table Index / Description / Picture, HIGH + MEDIUM rows) → Reference data (collapsed: today's summary tables,
channel overviews, all findings incl. INFO, via table, lengths, thresholds). Measurement code is untouched; only the
report layout and the zoom picture change. Pictures draw ONLY the involved layers (FR-005 table) with a legend.

### 1. `cut_board/review_report.py` (new, pure: no EDB)

| Function | What |
|---|---|
| `SECTIONS` | fixed order: `reference` Reference `REF` (Loss of reference, Ref to other net, SOV, Ref plane change), `trace_stub` Trace stub `STB` (Trace stub), `via` Via `VIA` (Via stub, Nearest GND via), `routing` Routing `RTE` (no rated finding today: data only) |
| `section_of(check)` | check name → section key; an unknown check → its own section (key / title = check name, prefix = initials), appended after the fixed ones in first-seen order (new review check = new section, no code change) |
| `rows(chans)` | per channel: each abnormal point (025 / 011 merge by net + location, unchanged) split by section → one row per (point, section) with its HIGH / MEDIUM items; row severity = worst item; sorted per section by severity, channel, point id; index `<PREFIX>-<nn>` stable within the report |
| `counts(chans)` | {section: {channel: {HIGH, MEDIUM, INFO}}} from the findings (INFO included) → sum over sections = `finding_counts` of the review |
| `danger(counts)` | worst severity + verdict: HIGH "Dangerous — stop", MEDIUM "Review needed", INFO only "Information", none "OK — no issue" (English: HTML rule 2026-10-22; the spec's Vietnamese wording translated) |
| `row_layers(items, ref_layers, metal)` | FR-005: trace issue → trace layer + its reference planes (SOV / LoR: `ref`, Ref to other net: plane of `ref`, Trace stub: `ref_layers(layer)`); Ref plane change → `used[0]`, `used[-1]` + reference planes of both; Via stub / Nearest GND via → `used` layers + their reference planes; unknown → issue layer only + note. Union over the row items, stack order → `(signal_layers, plane_layers, note)` |
| `limit_text(f, P)` | value vs limit per check (Nearest GND via → `gnd_via_flag_mm`, Ref plane change → `ref_change_gnd_via_mm`, SOV / LoR / Ref to other net → any length (sample `sample_step_mm`), stubs → none allowed) + severity reason (check `SEVERITY_RULE` wording) |
| `render(info, chans)` | the HTML (CSS / JS inline, self-contained, English) |

### 2. `cut_board/review.py`

- `svg_zoom(win, cu, planes, paths, signals, vrows, gnd_ps, items, oc)`: GND coverage of each plane in `planes` only
  (fixed palette, semi-transparent), other-net copper (orange) on planes of `Ref to other net` items, traces ONLY on
  `signals` (fixed palette per layer, solid; no dashed other layers), GND vias / pins, signal vias, issue marks of all
  row items. Returns `(svg, legend [(colour, text)])`.
- `review(..., gate=None)`: after `points()` (unchanged) → `review_report.rows([ch])` per channel; first
  `review.max_images` rows (severity order) per channel get a picture centred on the union bbox of the row items +
  `review.zoom_margin_mm`. `ch["rows"]` added; findings / points / ids / summary return value unchanged.
  `info["gate"] = gate` ({channel: {verdict, reason}} or None).
- `render_html(info, chans)` keeps its name / signature (tests/review_check.py grabs it) → `review_report.render`.

### 3. Gate verdict in the header (US1-4)

- `review_checks.measure_report(html=True)`: passes `{name: verdict_final}` of the record just saved.
- `interface_sim/review.run(html=True)`: passes `{interface: out["verdict"] + gate status}` (stop / continue /
  overridden when `review.override` is set). Without gate data the header says "Gate verdict: not recorded".

### 4. Guide

- `guides/review_measure.md`: report structure (summary first, category tables, danger wording, picture = involved
  layers only); chat summary uses the same section order and wording.

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | none (HTML content of `design_review(html=true)` / `isim_review(html=true)` changes) |
| Safety level | unchanged (read) |
| Approval flag | unchanged |
| Catalog entry + contract | no catalog change; contract `contracts/review-report.md` |
| Registration | n/a |
| Workflows affected | none |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| Changed | `cut_board/{review_report (new), review}.py`, `review_checks/__init__.py`, `interface_sim/review.py`, `guides/review_measure.md` |
| Untouched | measuring functions, `review_checks` items / points / verdicts, `tests/review_check.py`, review records (025) |
| Tests | `tests/unit/test_review_report_026.py`: sections + unknown check, row split / index / order, counts = finding counts, danger wording, row_layers per issue type (FR-005 table), render (structure order, 3 columns, INFO not in tables, no-issue section, failed channel = incomplete, gate header, picture limit note, self-contained: no external `src=` / `href=http`), svg_zoom draws only given layers (fake copper) |
| AEDT (copies, one after another) | board1 `review-measure --html` U14_U26 + U21_J25; `tests/review_check.py` PASS (numbers unchanged); test1 PCIe report (`pcie_check` channels); HTML paths sent to the user for review before converge |
| Performance | SC-004: board1 HTML build time vs 2.4.0 ≤ +20 % (rows ≈ points; planes per picture 1 → ≤ 4 grids of 48×48) |

## Constitution Check (2.0.1)

| Principle | Check | Status |
|---|---|---|
| I Gates | gate verdict shown only; no gate change | PASS |
| II Data safety | read-only review; copies for checks | PASS |
| III Defaults | reuses `review.max_images`, `review.zoom_margin_mm`; no new row | PASS |
| IV Guides | review_measure guide | PASS |
| V Regression | review_check.py numbers unchanged | PASS |
| VII Contracts | contract file; pure report module with input checks | PASS |
| VIII Package | report = `cut_board/review_report.py`; review.py only measures + draws | PASS |
| IX Stable interface | same tools / outputs; HTML layout change → minor | PASS |
| X Tool catalog | see Tool catalog check | PASS |
