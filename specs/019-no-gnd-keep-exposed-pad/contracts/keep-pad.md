# Contract — 019 keep exposed GND pad

## cut_board.gnd_decision

- `KEEP_PAD = "gnd_keep_pad"` ∈ `OPTIONS`, `EXECUTABLE`.
- `options_for(n_vias, n_copper_vias, keep_pad=None) -> (options, omitted)`; `keep_pad=None` → identical to 0.14.0.
  `keep_pad={"offered": bool, "reason": str}`.
- `outside_pads(edb, P, rd, nets, extent_mm) -> dict | None` (read only):
  `{pads: [{pin, layer, pad_mm[4], size_mm[2], inside_frac, vias_mm[[x, y]]}], rects_mm[[4]], touches: bool,
  other_nets: [str], margin_mm}`. None when the end has a GND pin inside the extent, no GND pin at all, or no signal pin.
- `extend_extent(extent_mm, rects_mm) -> [[x, y]]`: union; not a single polygon → `CopilotInputError("extent")`.
- `finding(ctx, keep_pad=None)`: adds `keep_pad` (facts + offered + reason) when given.

## cut_board.cutter.cut_stage(..., keep_pads=None)

- stage1 adds `gnd_pads_outside` {rd: facts}. With `keep_pads`: `extent_base_pts_mm`, `kept_pads` {rd: [pins]};
  refdes without touching facts → `RuntimeError` before the cutout.
- `apply_stage`: handling `gnd_keep_pad` → `gnd_reference[rd] = {"kind": "kept_pad", "pins": n}`.

## interface_sim

- `ends.check`: `no_gnd_pin` options include `gnd_keep_pad` per the rules in plan §3; finding `keep_pad`.
- `apply.run`: any `gnd_keep_pad` → re-cut (`cut.cut_design(..., keep_pads)`) into `final/`, `stage1_keep_pad.json`,
  apply on it. `gnd_decisions[rd].pads`.

## Template

`interface_sim.keep_pad_margin_mm` (num, mm, job) = 0.5.
