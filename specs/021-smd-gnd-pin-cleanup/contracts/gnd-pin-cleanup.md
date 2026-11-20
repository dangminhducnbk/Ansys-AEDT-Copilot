# Contract: GND pin cleanup on SMD / connector ends (feature 021)

Module `aedt_copilot/cut_board/gnd_pins.py` (pure). Distances centre to centre, metres in, mm in reports.

## select(sig_xy, gnd, keep_m, protect=()) -> dict

- `sig_xy`: [(x, y)] signal pin centres of the end (original positions). `gnd`: {name: (x, y) | (x0, y0, x1, y1)}
  own GND pins: centre or pad box; distance = signal centre → nearest point of the box (0 inside) (fix 2026-11-10).
- `keep` = names within `keep_m` of ≥ 1 signal pin ∪ nearest GND pin of every signal pin ∪ `protect` (∩ gnd).
- `far` = indexes of signal pins whose nearest GND pin is farther than `keep_m` (nearest kept anyway).
- No signal pin → keep all, `no_signal: true`.
- → `{keep: [names sorted], removed: [names sorted], nearest: {i: name}, far: [i], no_signal: bool}`.

## report(rd, before, sel, keep_mm) -> dict

`{refdes, gnd_pins_before, gnd_pins_after, removed: [names ≤ 50], keep_dist_mm, warnings: [text], info: [text]}`.
Exactly one own GND pin (before = 1): no far-pin warning, `info` = ["<rd>: GND duy nhất pin <name>, đã giữ"]
(the only GND pin is the chip's return path; rule 2026-11-10). Several: warning per far signal pin (unchanged).

## protected_names(stage1, rd) -> set

022 `stage1.end_gnd.ends[rd]`: `gnd_pin_inside`, `gnd_pins_gained[].pin`; 019 `stage1.kept_pads[rd]`.

## Use

- `cutter.rebuild_smd_component(..., protect_names)`: own GND pins only (gnd_choice plate / copper → no pruning);
  removed pins deleted before the component is rebuilt; `gnd_ref.gnd_pin_cleanup` = report.
- `cutter.apply_stage` → `metrics.gnd_pin_cleanup = [report]`.
- `cutter.cleanup_gnd(..., smd_ends=(), smd_protect=None)`: `design_cleanup` only; default no change.
- Template `cleanup.smd_gnd_pin_keep_dist_mm` 1.6 mm (Gate B); `defaults_history` since 2.3.0.
