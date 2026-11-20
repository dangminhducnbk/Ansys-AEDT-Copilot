# Contracts: `aedt_copilot.interface_sim.ends`

Tests: `tests/unit/test_isim_ends_settings.py` (`classify_unusual` with fake measurements), board part by `tests/isim_check.py`.

## `check(request_id, name, version=None) -> dict`

Precondition: step == `cut`. Opens `stage1/<name>.aedb` READ-ONLY. Measures per end component (data-model End
check): type (`inspect_board.end_type` + `connector` when part name / refdes prefix matches
`interface_sim.connector_patterns`), pins, signal pins with pad shape / size (pad bbox only for signal pins — slow on
BGA otherwise), GND pins within `cleanup.bga_gnd_pin_keep_dist_mm` (BGA) or pad-adjacent search (SMD), solder ball,
via-in-pad. Output: `ends` dict + `ends_md`; advances to `ends_checked`. EDB saved: no.

## `classify_unusual(end, th) -> list[dict]`

Pure. `th` = `thresholds(P)`. Rules (ids from data-model), thresholds from template `interface_sim.*`:
`no_gnd_near_signal` (a signal pin has 0 GND within the limit), `non_round_pad_bga` (BGA signal pad aspect
> `interface_sim.round_pad_aspect_max`), `connector_end`, `unknown_type`, `pad_size_mismatch` (signal pads of one end
differ > `interface_sim.pad_size_tol_pct`). Each item: `{rule, detail, values, options}`; options ⊆
`smd_rebuild, keep_component, no_solder_ball, stop_interface`.
