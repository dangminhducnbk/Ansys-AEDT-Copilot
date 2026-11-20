# Contracts: MCP tools (additions)

All thin: arguments → CLI `python -m aedt_copilot design --op=<op> --args-file=<json>` (task id for long runs).
In-place calls without `user_approved_in_place=true` are refused by the server (no CLI call).

| Tool | Inputs | Gate | Output |
|---|---|---|---|
| `design_read(board, cell="")` | `.aedb` | none (read-only) | snapshot |
| `design_setup(board, values, setup_name="", cell="", in_place=False, user_approved_in_place=False)` | `values` JSON of `setup.*` (+ mandatory `sweep.*`) | in place only | report |
| `design_sweep(board, values, setup_name="", cell="", in_place=False, user_approved_in_place=False)` | `sweep.*`; setup must exist | in place only | report |
| `design_airbox(board, values="", cell="", in_place=False, user_approved_in_place=False)` | `airbox.*` (empty = defaults) | in place only | report |
| `design_ports(board, refdes, nets="", replace=False, cell="", in_place=False, user_approved_in_place=False)` | `refdes` / `nets` comma separated | in place only | report |
| `design_solder_ball(board, refdes, values="", cell="", in_place=False, user_approved_in_place=False)` | `refdes` comma separated; `solder_ball.*` | in place only | report |

New guide `design_tools` (served by `get_guide`); new prompt `design-tools`.
