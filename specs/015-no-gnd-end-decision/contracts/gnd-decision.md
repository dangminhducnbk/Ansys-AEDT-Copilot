# Contracts: no-GND end decision (015)

Units: EDB-facing values in m, findings / images / reports in mm.

## `cut_board.gnd_decision.options_for(n_vias, n_copper_vias) -> (list[str], list[dict])`

| Input | Type | Valid |
|---|---|---|
| n_vias | int | ≥ 0 GND vias inside the body (today's filter) |
| n_copper_vias | int | ≥ 0, ≤ n_vias: of those, vias landing on existing GND copper of the placement layer |

Output: options in order `gnd_plate_vias` (n_vias ≥ 1), `gnd_existing_copper` (n_copper_vias ≥ 1),
`keep_component`, `stop_interface`, `other`; omitted `[{option, reason}]`. Pure.
Errors: CopilotInputError (`n_vias` / `n_copper_vias`) when negative or not int.

## `cut_board.gnd_decision.plate_rect(vias, pads, gap) -> tuple | None`

| Input | Type | Unit | Valid |
|---|---|---|---|
| vias | list[(x, y, diameter)] | m | GND vias in the body |
| pads | list[(x0, y0, x1, y1)] | m | signal pad bboxes |
| gap | float | m | ≥ 0 (`port.smd_gnd_plane_gap_mm`) |

Output: `(x0, y0, x1, y1)` m — formula moved verbatim from `rebuild_smd_component` (identical floats); None when no
via. Pure.

## `cut_board.gnd_decision.context(edb, P, rd, nets, body_bbox) -> dict`

Preconditions: EDB open (read or write), `rd` an end component, `body_bbox` (m) from stage1 / `comp_bbox`.
Output: `layer, part, plan, gnd_pins, gvias, rect, copper (polygon point lists, m), copper_vias`. Read only.

## `cut_board.gnd_decision.finding(ctx) -> dict`

JSON-able, mm: `refdes, part, layer, body_mm, pads_mm, vias_mm, rect_mm, rect_size_mm, copper_area_mm2,
copper_mm (outlines), n_vias, n_copper_vias, options, omitted`. Pure.

## `cut_board.gnd_decision.render(finding, path) -> str`

PNG of the body area (+0.5 mm): copper light blue, signal pads red, GND vias blue (on-copper with black ring),
proposed rectangle dashed with `W x H mm`, title refdes / part / layer, 1 mm bar. Writes `path` (folders created).
No AEDT.

## `cutter.rebuild_smd_component(edb, P, rd, nets, body_bbox, protect_polys, log, gnd_choice=None) -> (ids, W, gnd_ref)`

Changed: third return value `gnd_ref` {kind: own_pins | plate_vias | existing_copper, rect_mm?, pins}.
0 GND pins: `gnd_plate_vias` → plate + vias → pins (geometry identical to pre-015); `gnd_existing_copper` → copper vias
→ pins, no new copper; other / None → RuntimeError `"<rd>: no GND pin - GND decision needed (...)"` before the
component is changed. EDB not saved here.

## `cutter.apply_stage(edb, stage1, ch, P, log, protect_polys=None, handling=None) -> metrics`

handling values add `gnd_plate_vias`, `gnd_existing_copper`. metrics add `gnd_reference` {refdes: gnd_ref |
{kind: "none (kept component)"} | {kind: "own_pins"} (BGA / TH)}.

## `interface_sim.ends._measure(edb, rd, nets, refs, bga, th, P=None, body=None, image_dir=None) -> dict`

Non-BGA / TH end with 0 GND pins (P given): `unusual` gets `{rule: "no_gnd_pin", detail, values: finding (+ image),
options, omitted}` instead of `no_gnd_near_signal`. `image_dir` None → no image file. Read only (image only).

## `interface_sim.settings.apply_route(request_id, name, values, handling, user_approved_gnd=False) -> tuple`

Adds refusal `{"refused": True, "reason": "GND: ...user_approved_gnd=true.", "ends": [refdes]}` when the interface
has a `no_gnd_pin` end and the flag is false (checked before validation, after the step check).

## `interface_sim.settings.validate(values, handling, ends, structural)`

`other` → error `<rd>: 'other' must be mapped to one of <options> (or no utensil exists: stop)`.

## `interface_sim.apply.run(request_id, name, values, handling=None, version=None, gnd_notes=None)`

| Input | Type | Valid |
|---|---|---|
| gnd_notes | dict / None | {refdes of a `no_gnd_pin` end: str} |

Stores `gnd_decisions` in `user_settings.json` + state. Errors: CopilotInputError (`gnd_notes`) for a non-dict or a
refdes that is not a `no_gnd_pin` end.

## `interface_sim.recut.compare_handling(old_handling, ends) -> list`

`no_gnd_pin` end → `{result: "needs_confirm", old, previous_label}`; never `kept`.

## `cut_board.propose.propose(...)` / `gnd_questions(...)`

Output rows: warning per no-GND end; `<output_dir>/gnd_questions.json` = `{channel: {refdes: finding + image}}`.

## `cut_board.batch.gnd_missing(excel, only, gnd_handling) -> list[str]`

Problems (unanswered channel / refdes, option not offered). Reads `gnd_questions.json` next to the Excel (missing file
→ []). Pure file read.

## `cut_board.batch.start(excel, only=None, wait=False, gnd_handling=None)`

`gnd_handling` {channel: {refdes: option}} stored in `job.json`; worker passes it to `cut_channel(..., handling=)`.

## MCP tools

- `isim_apply(..., gnd_notes: str = "", user_approved_gnd: bool = False)`.
- `start_cut_batch(..., gnd_handling: str = "", user_approved_gnd: bool = False)`: refusal lists missing answers;
  answers without the flag → refusal naming `user_approved_gnd`.

Tests: `tests/unit/test_gnd_decision_015.py`; AEDT: board1 copy run (scratch) + `tests/regression.py`.
