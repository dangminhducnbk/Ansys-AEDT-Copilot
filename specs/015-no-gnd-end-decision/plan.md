# Implementation Plan: No-GND end decision

**Branch**: `main` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

A non-BGA end with 0 GND pins is no longer rebuilt silently. One module computes the facts (GND vias in the body,
proposed rectangle, GND vias on existing copper), the options and the image; the end check (interface sim, design end
check) and propose (Excel flow) report it; apply / cut batch need the user's answer + `user_approved_gnd`.

### 1. Shared module `cut_board/gnd_decision.py`

| Function | Kind | What |
|---|---|---|
| `OPTIONS` | const | `gnd_plate_vias`, `gnd_existing_copper`, `keep_component`, `stop_interface`, `other` (question only) |
| `EXECUTABLE` | const | options apply can run (all but `other`) |
| `options_for(n_vias, n_copper_vias)` | pure | → `(options, omitted[{option, reason}])`; plate needs ≥ 1 via, copper option needs ≥ 1 via on GND copper |
| `plate_rect(vias, pads, gap)` | pure | rectangle bounding vias (+ max via radius + gap), shrunk away from signal pads — code moved verbatim from `rebuild_smd_component` (identical result) |
| `context(edb, P, rd, nets, body_bbox)` | EDB, read | placement layer, part, signal pin plan (`plan_smd_pin`), GND pins, GND vias in the body (same filter as today), rect, GND copper polygons of the reference nets on the layer touching the body, vias on that copper (point in polygon, not in a void) |
| `finding(ctx)` | pure | JSON-able dict (mm): refdes, part, layer, body, pads, vias, rect_mm (+ w / h), copper (polys, area), copper_vias, options, omitted |
| `render(finding, path)` | pure (PIL) | body area + 0.5 mm: GND copper (light blue), signal pads (red), GND vias (blue; on-copper outlined), proposed rectangle (dashed, `W x H mm`), title refdes / part / layer, 1 mm scale bar |

`cutter.rebuild_smd_component(edb, P, rd, nets, body_bbox, protect_polys, log, gnd_choice=None)` uses `context`:
- own GND pins → unchanged (choice ignored).
- 0 GND pins: `gnd_plate_vias` → today's plate (`plate_rect`) + vias → pins; `gnd_existing_copper` → copper vias → pins,
  no new copper; anything else (None, `smd_rebuild`) → `RuntimeError` "<rd>: no GND pin - GND decision needed".
- returns also `gnd_ref` {kind: own_pins | plate_vias | existing_copper, rect_mm?, pins}. `apply_stage` collects
  `metrics["gnd_reference"]` per end (`keep_component` → `none (kept component)`; BGA / TH → `own_pins`).
- `apply_stage` handling values `gnd_plate_vias` / `gnd_existing_copper` → rebuild with that choice.

### 2. Interface simulation

- `ends._measure(edb, rd, nets, refs, bga, th, P=None, body=None, image_dir=None)`: non-BGA / TH end with 0 GND pins
  → rule `no_gnd_pin` (replaces `no_gnd_near_signal` for that end) with `values` = finding (rect, counts, image),
  `options` = case options, `omitted`. `ends.check` passes P, stage1 body and the interface folder
  (`<iface>/gnd_<refdes>.png`). Connector with 0 GND pins: question instead of team default (default_handling not
  used while `unusual` exists — already so).
- `ends_md`: section "GND decision needed" (image path, rect size, options, omitted with reason).
- `settings.validate`: `other` → error "map 'other' to a listed option"; handling for a `no_gnd_pin` end must be one of
  its options. `ALL_OPTIONS` includes the new options.
- `settings.apply_route(..., user_approved_gnd=False)`: refusal (before validation) when the interface has a
  `no_gnd_pin` end and the flag is false: "GND: show the image + options of <refdes> as a multiple-choice question,
  wait for the user's answer, then call again with user_approved_gnd=true."
- `apply.run(..., gnd_notes=None)`: stores `gnd_decisions` {refdes: {option, rect_mm | copper_vias, image, note,
  decided_at}} in `user_settings.json` (via `S.save`) and state; result / self-check: `gnd_reference` per end.
- `recut.compare_handling`: an end with `no_gnd_pin` → result `needs_confirm` (never `kept`), `previous` answer
  (`smd_rebuild` of old runs shown as `gnd_plate_vias (smd_rebuild)`); `handling_md` shows it; not pre-filled.
- Server: `isim_apply(..., gnd_notes: str = "", user_approved_gnd: bool = False)`.
- Form (005): unusual options already listed per end; `other` shown; no form change beyond option list.

### 3. Excel flow (minimal; may be retired later)

- `propose`: for each non-BGA end with 0 GND pins (on the source board): finding + image
  `<output_dir>/gnd_<channel>_<refdes>.png`; row warning "U26: no GND pin - GND decision needed (see image)";
  `gnd_questions.json` next to the Excel; CLI / tool output adds `gnd_questions`.
- `start_cut_batch(excel, only, user_approved_excel, gnd_handling: str = "", user_approved_gnd: bool = False)`:
  after Excel validation, `batch.gnd_missing(excel, only, handling)` → refusal listing each channel / refdes and its
  options when unanswered, or when answered without `user_approved_gnd`.
- CLI `cut --gnd-handling=<json>` → `batch.start(..., gnd_handling)` → `job.json` → worker →
  `cutter.cut_channel(..., handling=)` → `apply_stage(handling=)`. Without an answer the channel stops with the
  RuntimeError of the rebuild (error in the report).
- Regression: Excel cut of board1 passes `{"CPHY_U14_U26": {"U26": "gnd_plate_vias"}}` → reference unchanged.

### 4. Design tools

No design tool calls the SMD rebuild → no gate needed. `design_end_check` reports `no_gnd_pin` with finding +
options; image under `<repo>/.tasks/` (read-only tool never writes next to the design).

### 5. Guides

`interface_sim` (Gate B: for `no_gnd_pin` show the image + ask a multiple-choice question listing exactly the
options, plus omitted reasons; never choose; "other" → map or say no utensil; pass `user_approved_gnd`; re-cut:
show image + previous answer, confirm), `workflow` (GATE 2: same for `gnd_questions`; `start_cut_batch` args),
`design_tools` / `kitchen` (end check reports the case; no tool decides), `verify` (report names GND reference).

## Kitchen check

| Item | Answer |
|---|---|
| Utensils added | none |
| Process tools added | none |
| Tool inputs | `isim_apply` + `gnd_notes`, `user_approved_gnd`; `start_cut_batch` + `gnd_handling`, `user_approved_gnd` (optional, default off) |
| Outputs | `isim_check_ends` / `design_end_check` / `propose_channels`: rule `no_gnd_pin`, image, options; apply / cut metrics `gnd_reference` |
| Safety / gate | unchanged levels; new server-side flag `user_approved_gnd` (refusal tests added) |
| Catalog + contract | descriptions note the flag; contracts in `contracts/gnd-decision.md` |
| Recipes affected | none (steps unchanged) |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| New code | `cut_board/gnd_decision.py` |
| Changed | `cut_board/{cutter,propose,batch}.py`, `cli/{parser,commands}.py`, `interface_sim/{ends,settings,apply,recut}.py`, `design_tools/end_check.py`, `mcp_server/server.py`, `kitchen/catalog.py`, guides |
| Tests | `tests/unit/test_gnd_decision_015.py` (options per case, plate_rect golden vs old formula, image from fake geometry, validation, gate refusals, user_settings, recut needs_confirm, batch gnd_missing); existing tests updated for the new rule id where they use 0-GND-pin fixtures |
| AEDT | `tests/isim_check.py`-style run on a board1 copy: U26 / U21 stop with image + options; option 1 → plate coords + metrics equal reference; `tests/regression.py` with gnd_handling |

## Constitution Check (1.2.0)

| Principle | Check | Status |
|---|---|---|
| I Gates | `user_approved_gnd` checked server-side; refusal tests | PASS |
| II Data safety | runs on copies; read-only tools write images only to tool folders | PASS |
| III Defaults | no new template default (gap / margin reused) | PASS |
| IV Guides | usage rules in guides | PASS |
| V Regression | regression.py with answer; isim on board1 copy | PASS |
| VII Contracts | contracts + validation at entry | PASS |
| VIII Package | facts / options / image in one module; server only flags | PASS |
| IX Stable interface | names unchanged; optional params; Excel format unchanged; minor 0.14.0 | PASS |
| X Kitchen | see Kitchen check | PASS |
