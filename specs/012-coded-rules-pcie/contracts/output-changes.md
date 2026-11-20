# Contract: output changes (012)

Tool names and inputs unchanged. Outputs:

| Tool / op | Change |
|---|---|
| `isim_check_ends` (op ends) | `ends[rd].default_handling = {rule, value, options, source}` for connector ends; `default_handling {rd: value}`; connector no longer in `unusual` |
| `isim_validate_settings` (op validate) | `handling` = effective handling (team default < previous run kept < engineer) |
| `isim_apply` (op apply / reapply) | stores effective handling; `self_check.series = [{refdes, type, part, nets, model, r_ohm, ok}]`; `self_check.signal_paths`, `self_check.expected_ports_2x_paths` (replaces `expected_ports_2x_nets`); mismatch item `ports vs 2 x signal paths` |
| `isim_settings_form` | `tabs[].unusual[rd].default` for defaulted ends; `handling` prefilled |
| `review_layout` HTML / summary, `design_review`, `isim_review` | point issue lines unique (same text once); findings / counts / severities unchanged |

Template: new row `interface_sim.connector_handling` (job, text, default `smd_rebuild`, one of
`keep_component | smd_rebuild | no_solder_ball | stop_interface`).
