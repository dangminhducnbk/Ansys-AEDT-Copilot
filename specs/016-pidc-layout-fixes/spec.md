# Feature Specification: PI-DC + layout edit fixes

**Feature Branch**: `016-pidc-layout-fixes` (work stays on `main`)

**Created**: 2026-11-09

**Status**: Done 0.14.1 (clarified 2026-11-09: Q1 A, Q2 A, Q3 A)

**Input**: Parent session, user go 2026-11-09 ("Có, sau 015"): fixes from a PI-DC run on
`D:\data\boardb_19x19\simulation\20261108\siwave\pi-dc` (package 19 x 19 mm, RDL layers; user data,
read only). Patch 0.14.1.

## Problem

| # | Bug | Evidence (user data) |
|---|---|---|
| 1 | VRM voltage read as ~0 V → drop wrong | `voltage_distribution._sources` uses data cell 9 as VRM V; SIwave "Voltage Sources" cell 9 = **Series R Voltage(V)** (header row: Magnitude(V), Phase, Source R, + net, − net, + terminal, − terminal, Current(A), Series R Voltage(V)). DDR_VDDQ VRM V = 2.0e-7, drop -789 mV / -1.26e7 % |
| 2 | Thin copper → NO_DATA, silent | 505 / 532 pairs NO_DATA ("no copper with current" 366, "no current" 76, "copper narrower than the window" 63); 297 of them have colour-bar max above the limit; verdict ignores them |
| 3 | `.siw` without power / ground net list | verdict PASS with 0 checked pairs; voltage_distribution crashes |
| 4 | `layout_edit` op `delete` cannot delete vias | `Editor.op_delete` → `core()` only looks in primitives |
| 5 | `pidc.image_width` 12258 but SIwave caps at 10000 | template default |
| 6 | Via IPC ΔT is a fixed template value (35 °C) | user rule: ΔT = T_sim − T_base; T_sim = `GlobalTemperature` of the DC-IR run cfg (`<run>/<run>.cfg`, = `.siw` SIDIRECT_GLOBAL_BOARD_TEMPERATURE), T_base = 25 °C (new row `pidc.via_base_temp_C`); BOARDB ΔT = 90 − 25 = 65 |

## Clarifications

### Session 2026-11-09 (user via parent session)

- Q1 (narrow / tiny copper) → **A**: when no 0.5 mm window has enough copper, average J over **copper pixels only** in
  a window `pidc.cd_narrow_window_mm` (new template row, default 0.1 mm); judge that value against the limit as usual
  (PASS / WARN / FAIL), reason "narrow copper". Copper pieces < 0.002 mm² (`pidc.cd_tiny_area_mm2`) → **INFO only**,
  never PASS / FAIL. A pair whose colour-bar max is above the limit is never silent NO_DATA; the verdict counts it.
- Q2 (no power / ground net list in the `.siw`) → **A**: stop with a clear error (no new net argument). A run with
  0 checked pairs is never PASS; voltage_distribution does not crash.
- Q3 (T_sim missing) → **A**: stop with a clear error (no fallback). Row `pidc.via_dT_C` is **removed**; new row
  `pidc.via_base_temp_C` = 25. Unit test workbook case r = 2 mil, ΔT = 60 → 0.9107 A; `pidc_check` reference
  updated with the reason.
- Out of scope (ROADMAP row only): new no-GND end option "extend the cut extent to keep the exposed GND pad".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct VRM voltage and drop (P1)
VRM output voltage = Magnitude − Series R Voltage (columns found by header name; header missing → fall back to
today's positions with a warning); load drop = VRM output − load voltage. The report DCIR table names the columns
the same way.
**Independent Test**: offline — the user's `report.htm` table rows (copied as a fixture) give DDR_VDDQ VRM V ≈ set
voltage and drop ≥ 0; sample BOARDB_B04 results unchanged (`pidc_check`).

### User Story 2 - Thin copper is measured or flagged, never silent (P1)
Copper narrower than the 0.5 mm window: J averaged over copper pixels in a 0.1 mm window (`pidc.cd_narrow_window_mm`),
judged against the limit, reason "narrow copper". Copper < 0.002 mm² → INFO. A pair whose colour-bar max is above the limit is never silently NO_DATA: it gets a status that the verdict counts
(WARN / PENDING) with the reason.

### User Story 3 - No power nets → clear stop (P1)
No power / ground net list in the `.siw` → stop with a clear error naming the file. Verdict is never PASS with 0 checked pairs; voltage_distribution does not crash on empty input.

### User Story 4 - Layout edit deletes vias (P2)
`delete` accepts padstack instance ids (as listed by `layout_region` vias); deleted via .NET; recorded in
`changes.md`; guide `layout_edit` updated.

### User Story 6 - Via ΔT from the simulation (P1)
ΔT = T_sim − T_base. T_sim from the DC-IR run cfg `GlobalTemperature` (ignore EM Uniform_temperature and Icepak).
T_sim not found → stop with a clear error (no fallback); row `pidc.via_dT_C` removed.
ΔT ≤ 0 or outside IPC-2221 10..100 °C → warning. Report shows T_sim, T_base, ΔT. Formula unchanged; unit test
r = 2 mil, ΔT = 60 → 0.9107 A. `pidc_check` reference changes (via util) → updated with the reason.

### User Story 5 - Image width default 10000 (P3)
Template default `pidc.image_width` = 10000; a value > 10000 warns (SIwave caps it).

## Requirements *(mandatory)*

- **FR-001**: SIwave source tables parsed by header name (Voltage / Current Sources), shared by voltage_distribution
  and report.
- **FR-002**: VRM output V = Magnitude − Series R Voltage when that column equals I x R_source; otherwise (remote-sense
  VRM, e.g. BOARDB_B04: column = 0.8114 V = output) V = column; recorded `V_source` (how it was computed). Found in plan.
- **FR-003**: Current density: narrow copper → copper-only mean J in `pidc.cd_narrow_window_mm` (0.1 mm); copper
  < `pidc.cd_tiny_area_mm2` (0.002 mm²) → INFO; above-limit colour bar never silently NO_DATA;
  verdict counts it.
- **FR-004**: Empty power net list → clear error (stop); verdict never PASS with 0 checked pairs.
- **FR-005**: layout_edit `delete` handles padstack instance ids; `changes.md` lists them.
- **FR-006**: `pidc.image_width` default 10000 (defaults history if needed), warning above 10000.
- **FR-008**: Via ΔT = T_sim (run cfg GlobalTemperature) − `pidc.via_base_temp_C` (25); T_sim missing → stop;
  row `pidc.via_dT_C` removed; warnings outside 10..100 °C;
  report shows the three values.
- **FR-007**: Results unchanged where a fix does not apply: `pidc_check` on BOARDB_B04 copies, `layout_edit_b04`.

## Success Criteria *(mandatory)*

- **SC-001**: user data (copy): VRM V = set − series drop for every VRM; drops ≥ 0 within rounding.
- **SC-002**: no pair with colour-bar max > limit stays silent NO_DATA; verdict not PASS with such pairs.
- **SC-003**: BOARDB_B04 sample: current density / via / voltage results identical except where a fix applies.
- **SC-004**: unit tests for each item PASS; layout_edit_b04 identical.

## Assumptions

- The user's folder is read only; reruns on a copy (`--skip-export`, no SIwave).
- Power tree skill not run (opens SIwave).
