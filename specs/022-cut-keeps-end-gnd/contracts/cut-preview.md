# Contract: Gate A cut form + cut preview + manual end factor (feature 022, US4 / US5)

## MCP `isim_cut_preview(request_id, name, values="", end_factors="")` — safety `read`, no gate

- `values`: JSON `{cutout.* | series.keep: value}` (form values; empty = stored structural of the content / proposal).
- `end_factors`: JSON `{refdes: number | "" | null}` (empty / null = automatic; omitted = stored `content.end_factors`).
- Step must be `started` (traced) or `content_agreed`; after the cut → refusal "already cut: change the cut settings =
  Gate A again (isim_confirm_content) + re-cut".
- Validation first (no EDB): unknown key → `structural`; bad value → `cutout.<key>: …`; end factor ≤ 0 / not a
  number → `cutout.end_factor.<refdes>: …`; refdes not an end → `cutout.end_factor.<refdes>: not an end`.
  → `{ok: false, validation: true, errors, table_md}`.
- Source board opened READ ONLY; `cutter.cut_extent(..., strict=False)` (same function as the cut).
- Writes only `<interface>/preview/cut_region.png`, `<interface>/preview/end_<refdes>.png` (enlarged / manual ends),
  `<interface>/preview.json`.
- Returns `{name, ok, errors, rows[{refdes, gnd_pins_on_board, gnd_inside_at_base, result, factor_used, manual,
  added_mm2, gnd_gained, other_nets, error}], image, zooms{refdes: path}, extent_area_mm2, extent_size_mm,
  structural, end_factors, table_md, preview_json}`. Often a task (`task_id` → `task_result`).

## MCP `isim_cut_form(request_id="")` — safety `read`, no gate

`{request_id, tabs[{name, step, enabled, locked, reason, content_agreed, descriptors[], preview}], table_md}`.
Descriptor: `{key, label, unit, type, choices, default, value, source, group, mandatory, copy, per_end, refdes?,
locked, locked_reason, desc}`. Template `cutout.*` + `series.keep` rows: `copy: true`. Per end
`cutout.end_factor.<refdes>`: `per_end: true, copy: false, default: null`. Tab disabled before `isim_trace`; locked
after the cut. `preview` = last preview.json summary, `current` = computed with the tab's current settings.

## Manual end factor

- `content.end_factors {refdes: number > 0}` (refdes = comp_a / comp_b) in `isim_confirm_content`; stored in content and
  `user_settings.json`; re-cut proposal keeps it for ends still in the interface.
- `end_gnd.apply_rule(manual={rd: f})`: region extent = `(current − region) ∪ (extent(f) ∩ region)`, result `manual`,
  `base_inside` (GND inside at the base factor). No GND pin / pad fully inside → error
  `end factor <rd> = <f> leaves no GND pin / pad fully inside the cut extent`; end without GND pin on the board →
  error `<rd> has no GND pin on the board: leave its end factor empty`. strict (cut) → RuntimeError before cutout;
  preview → `rows[].error`, `errors`.
- `isim_confirm_content` refused when `preview.json` computed with the same settings has errors.

## Same computation (SC-005)

`cutter.cut_extent(edb, P, nets, ends, log, end_factors=None, strict=True) -> (pts, end_gnd)` used by
`cut_stage` and the preview. `settings_key(P, end_factors, nets)` identifies the settings; `isim_cut` returns
`preview_check {compared, equal, area_diff_mm2}` (stage1 too).

## Image (`end_gnd.render_scene(scene, path, view=None, title=None)`, pure PIL)

Signal primitives / vias red; base extent grey outline; added end area light green + label
`<refdes>: <factor>, +N mm²`; end region dashed; end + series components frame + refdes; GND pins / pad kept blue,
still outside blue with red outline; other-net primitives in the added area light grey + names (≤ 12 labels);
1 mm scale bar; overall size `W x H mm` in the header.
