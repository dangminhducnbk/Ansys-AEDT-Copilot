<!-- Atomic design tools: one operation on ANY existing .aedb (setup, sweep, airbox, coax ports, solder balls), on a COPY by default, with read-back and a short report. Use for "tạo port", "set frequency / sweep", "đổi airbox", "thêm solder ball" on a design that is not (or not only) part of a cut / interface-simulation request. -->
# DESIGN TOOLS — ATOMIC OPERATIONS

## 1. MISSION
Do ONE change on an existing design the engineer names: simulation setup, sweep, airbox, coax ports or solder balls.
Code executes and checks. You show the values, run the tool, and report exactly what changed.

## 2. RULES OF ENGAGEMENT
- Use ONLY these tools: `design_read`, `design_setup`, `design_sweep`, `design_airbox`, `design_ports`,
  `design_solder_ball`. No pyaedt-mcp, no ad-hoc PyEDB scripts.
  Since 0.11.0 more tools (trace, cutout, cleanup, end check, check, merge) and workflows chaining them:
  `get_guide("catalog")`.
- Input = an `.aedb` folder (an `.aedt` path is mapped to its `.aedb`), optional `cell`.
- Pick the right tool for the request:
  | Request | Use |
  |---|---|
  | one change on any design ("tạo port U5", "sweep 0-20 GHz", "airbox pml") | these tools |
  | interface from a full board, agreed content / settings, merge into the workspace | `get_guide("interface_sim")` |
  | change setup / sweep / airbox of an interface already applied by interface_sim | `isim_apply` re-apply (keeps `user_settings.json` and state consistent) — say so; use these tools only if the engineer insists |
- COPY by default: the tool writes `<name>_<op>_<time>.aedb` next to the original and reports its path. The original
  is not changed. Tell the engineer the result path every time.
- IN PLACE (`in_place=true`) only when the engineer asks for it: say which file will be changed and that a backup
  `<name>_old_<time>.aedb` is made, wait for an explicit go ("đồng ý"), then call with `user_approved_in_place=true`.
  Never set the flag without that go in THIS conversation.
- Design open in AEDT (`.lock`) → the tool refuses. Ask the engineer to close it. Never delete a lock.
- Values: template defaults (`templates/autocut_template.csv`) + the engineer's values only. Never invent the
  mandatory sweep values (`sweep.start_ghz`, `stop_ghz`, `step_ghz`) — ask.
- `design_cutout` applies the END GND RULE (2.1.0, as interface simulation): GND pins of each end are detected on
  the source board; an end that has GND pins but none fully inside the extent gets only its region (body +
  `cutout.end_region_margin_mm`) enlarged by `cutout.end_expansion_step` per try until one is inside (no maximum).
  Report `created.end_gnd` per end (`met` / `enlarged` + factor / `no_gnd_pin_on_board`, GND pins detected); a
  geometry error (region covered, no GND inside) fails the cut. `design_end_check` with `stage1.json` beside the
  design shows the table +
  image (`end_gnd`). Tell the user every `enlarged` end (factor, added area, other nets not kept). `design_cleanup`
  keeps the GND vias in the pad of an enlarged end.
- `design_cleanup` (2.3.0) also prunes own GND pins of SMD / connector ends to those within
  `cleanup.smd_gnd_pin_keep_dist_mm` of a signal pin, plus each signal pin's nearest; the end GND rule pin / kept pad
  is never removed. Report `created.gnd_pin_cleanup` (before → after per end, warnings).
- End without GND pin (`design_end_check` → `no_gnd_pin`, `gnd_questions` with an image under `.tasks/`): send the
  image, ask a multiple-choice question with exactly its `options` (never choose). No design tool rebuilds an end or
  draws a GND plate; the answer is used by `isim_apply` (`user_approved_gnd`).
  With `stage1.json` next to the design (design_cutout output) the finding has `keep_pad`: GND pad(s) of the end that
  the cut lost (e.g. exposed pad). Tell the user; option `gnd_keep_pad` is applied only by interface simulation
  (`isim_apply`), so it is listed under `omitted` here.
- Open a result in AEDT with nets highlighted (signal red, GND blue): `finish_in_aedt(aedb, port)` on request (AEDT GUI:
  ask the user first).
- Reply in the user's language. Short. Tables. Always give file paths.

## 3. EXECUTION
1. `design_read(board)` → show the current values relevant to the request (setups / sweeps / airbox / ports /
   solder balls).
2. Build the values / targets with the engineer:
   | Tool | values | targets |
   |---|---|---|
   | `design_setup` | `setup.*` + `sweep.start_ghz/stop_ghz/step_ghz` (mandatory) + other `sweep.*` | `setup_name` (default template `setup.name`; same name = replaced) |
   | `design_sweep` | `sweep.*` | `setup_name` (must exist; empty = the only setup) |
   | `design_airbox` | `airbox.*` (empty = defaults) | — |
   | `design_ports` | — | `refdes` (comma list), `nets` (empty = all non-reference nets of those parts), `replace` |
   | `design_solder_ball` | `solder_ball.*` (empty = defaults: diameter = ratio × short side of the signal pad) | `refdes` |
3. Call the tool (copy mode needs no gate). A long run returns `task_id` → `task_result`.
4. Report from the result: `result` path (+ `backup` in place), `changes` (old → new), `skipped` (with reason),
   read-back (`mismatches` empty = OK; else show each item). Point to the report file `<result>.design_tools.md`.
5. Several operations on the same design: call the next tool on the RESULT of the previous one (its `result` path) so
   all changes are in one design. The copy keeps the original name (`<original>_<op>_<time>.aedb`, no growing
   suffixes) and its report `<result>.design_tools.md` carries every earlier section + the new one.
6. Input errors (unknown refdes / net / setup, invalid values) come with the expected value and the closest names:
   show them, ask, retry. Nothing was changed.
