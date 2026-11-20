# Implementation Plan: Port location honoured for every SMD end

**Branch**: `main` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md) | Released with 039 as 5.2.0.

## Summary

- `cutter.plan_smd_pin(edb, pin, layer, paths=None)` unchanged in result; optional `paths` (net paths) for the page.
- New `cutter.pad_end_toward(pin, body_bbox)` → (pos | None, reason): long axis, towards the body bbox centre.
- New `cutter.port_end(edb, pin, layer, body_bbox, paths=None)` → (pos | None, how): trace → `plan_smd_pin`;
  else `pad_end_toward`. ONE function for the build and the page data.
- `comp_model` adds `port_location_explicit` (per-end entry present).
- `rebuild_smd_component(..., port_location, explicit=False, port_report=None)`: ctx plan (trace plan) kept for the
  GND logic; port plan = explicit end → `port_end` for pins without a trace position; explicit centre → none moved;
  not explicit → ctx plan (old behaviour). Fills `port_report`.
- `apply_stage`: metrics `port_location` {rd: report}; kept / BGA ends recorded.
- `apply.self_check`: item "<rd> port location" from read-back pin positions vs `stage1.sig_pos0`.
- Page data `ends_data`: per signal pad `port_end` [x, y] mm or null + `port_how`; end flag `no_trace_exit`.
  `model.defaults`: `centre` for ends with `no_trace_exit`. `page.js portXY` uses `p.port_end`; label
  "Pad centre (pin position)"; note for via-in-pad ends.

## Constitution Check

| Principle | Status |
|---|---|
| I Gates | Unchanged. |
| II Data safety | Cut on copies, unchanged. |
| III Defaults | No template change; page default derived from the board (via-in-pad → centre = old build). |
| V Regression | Old results unchanged when no per-end choice (board1 regression, pcie_check). New: BOARDA J25 end / centre. |
| VII Contracts | `cut_board` functions documented in docstrings; result.json key `metrics.port_location` added. |
| IX Stable interface | Added keys only. |

## Project Structure

`aedt_copilot/cut_board/cutter.py`, `aedt_copilot/interface_sim/apply.py`, `aedt_copilot/interface_sim/config/{data,model}.py`,
`aedt_copilot/interface_sim/config/assets/page.js`. Tests: `tests/unit/test_port_location_041.py`.

---

# Extension (clarify 2026-11-16): port slider + traces on the page — release 5.3.0 (minor)

Spec: FR-007, FR-008, SC-005. Old FR-001..006 stay; "end" / "centre" become points of the slider.

## Summary

| Area | Change |
|---|---|
| `cutter.port_span(pin, body_bbox)` (new) | → `((p0, p1) | None, reason)`, metres. Long axis of the pad bbox; p0 = point W/2 from the pad end on the body side, p1 = W/2 from the far end. None: square / round (L − W ≤ 1 µm), no body, pad on the body centre line (same reasons as `pad_end_toward`). |
| `cutter.port_at(span, pct)` (new, pure) | `p0 + pct/100 · (p1 − p0)`. 50 % = pad centre exactly (pin not moved). |
| `pad_end_toward` | = `port_span` → p0 (kept for callers / tests). `port_end` unchanged (no-choice path + 5.2.0 tests). |
| `comp_model` | new key `port_pct` (float or None). Per-end entry `port_pct` wins; else per-end `port_location` maps `end` → 0, `centre` → 50 (5.2.0 pages); `port_location_explicit` = either key present. Template `component.port_location` unchanged (no per-end entry = old rule). |
| `rebuild_smd_component(..., port_pct=None)` | explicit → every signal pad: span → target = `port_at`; target within 1 µm of the pin → not moved (pin kept, like centre); no span → not moved + reason (warning). Not explicit → old rule (trace plan). GND logic still uses the ctx trace plan. Report adds `pct` and `targets` [{pin, net, at_mm, offset_mm}] (offset from the body-side pad end). |
| `apply_stage` | passes `cm["port_pct"]`; metrics `port_location[rd]` = report above. |
| `apply.port_location_mismatches` | if `targets` present: each target needs a read-back signal pin of the same net within 1 µm → else line "<rd> port location (<pct> %)" with pins off target; old report shape (no targets) = 5.2.0 count check. |
| `config/data.ends_data` | per signal pad: `port_span` [[x,y],[x,y]] mm or null + `port_how` (reason); `port_end` kept = `port_span[0]` (old pages); per end `traces`: signal-net paths on the placement layer with a point inside the end frame (+ margin): `{net, w_mm, pts [[x,y]...]}`; arc marker points (|v| > 1e100) dropped; ≤ 400 paths per end. `no_trace_exit` unchanged. |
| `config/model` | state `cm[rd].port_pct` (number 0..100, step 1). Default: BGA → none (no slider); `no_trace_exit` → 50; else template `end` → 0 / `centre` → 50. Validation: non-BGA end with a span on any pad needs 0 ≤ pct ≤ 100; old `port_location` still read when `port_pct` missing (5.2.0 saved pages). `component.model` JSON carries `port_pct` (dict copied as is). |
| `page.js` | Component model tab: slider 0–100 % (`Outer` ← → `Body side`, body side = 0 %) + value, offset per pad size in mm + mil (no unit switch on this page), "Centre" / "Body end" / "Outer end" quick buttons (= 50 / 0 / 100). `portXY` = interpolate `port_span`; null span → pad centre. `topStatic` draws `traces` as polylines (net colour of the signal, width w_mm, under the pads) clipped by the frame. Note for pads without span ("square / round pad: port at the centre"). |
| Guide `interface_sim` | config page row: port position slider (0 % body side / 50 % centre / 100 % outer), traces drawn; self-check line. |

## Constitution Check

| Principle | Status |
|---|---|
| I Gates | Unchanged (isim_go). |
| II Data safety | Copies only; J25 bug-run design untouched (tests on copies). |
| III Defaults | No template row change; page defaults derived as in 5.2.0 (0 % ≙ end, 50 % ≙ centre). |
| V Regression | No per-end choice → identical (board1 regression, config_flow_check). 5.2.0 saved pages: `end` → 0 % — same pins for via-in-pad / no-trace pads; for a pad with a trace that leaves towards the body (rare) the port now follows the body side as the name says (noted in CHANGELOG). |
| VII Contracts | Data keys `port_span`, `traces`; state key `port_pct`; metrics `targets` — added keys only. |
| IX Stable interface | No tool / CLI change. |

## Tests

- Unit `tests/unit/test_port_slider_041.py`: `port_span` (horizontal / vertical pad, body left / right, square → None,
  centre line → None), `port_at` 0 / 50 / 100 (pad 10 × 2 → 1 / 5 / 9 mm from the body end; 6 × 2 → 1 / 3 / 5),
  `comp_model` mapping (pct wins, end → 0, centre → 50, none → not explicit), self-check targets (hit / miss 2 µm),
  model defaults + validation (pct out of range, BGA), data `traces` filter (fake paths: layer, net, arc markers).
- Existing 041 / config tests stay green (port_end, centre / end mapping).
- AEDT (copies): BOARDA PCIE_U14_J25 J25 at 0 / 50 / 100 % → offsets read back ± 1 µm, 16 ports, self-check OK
  (SC-005); board1 `regression.py` + `config_flow_check.py` unchanged; browser: config page on a board1 copy request
  shows traces + slider moves the port marks.

## Project Structure

`aedt_copilot/cut_board/cutter.py`, `aedt_copilot/interface_sim/apply.py`,
`aedt_copilot/interface_sim/config/{data,model}.py`, `aedt_copilot/interface_sim/config/assets/page.js`,
`guides/interface_sim.md`, `CHANGELOG.md`, `VERSION` 5.3.0, `CLAUDE.md` status row.
