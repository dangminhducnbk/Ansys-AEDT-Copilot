# Contracts: MCP tools (additions)

Thin: arguments → CLI subprocess (`design`, `kitchen` sub-commands). Existing tools unchanged.

| Tool | Inputs | Safety / gate | Output |
|---|---|---|---|
| `kitchen_utensils(group="", kind="", safety="")` | filters | read | `{utensils[], table_md}` |
| `kitchen_recipes()` | — | read | `{recipes[], table_md, team_dir, personal_dir}` |
| `get_recipe(name, source="")` | recipe name | read | recipe + body |
| `save_recipe(name, markdown, overwrite=False)` | front matter + body | copy (personal folder only) | saved recipe + path |
| `design_trace(board, refdes, nets="", cell="")` | | read | trace JSON |
| `design_cutout(board, comp_a, comp_b, nets, series="", name="", values="", cell="")` | | copy | report + new `.aedb` (task) |
| `design_cleanup(board, ends, nets="", values="", cell="", in_place=False, user_approved_in_place=False)` | | copy / original (gate) | report |
| `design_end_check(board, refdes, nets="", cell="")` | | read | ends + `ends_md` |
| `design_check(board, ends, nets="", values="", setup_name="", cell="")` | | read | `{ok, mismatches}` |
| `design_merge(workspace, designs, port=0, user_approved_merge=False)` | | workspace (gate) | merge result (task) |

CLI: `python -m aedt_copilot kitchen --op=<utensils|recipes|get|save> --args=<json>`; `design --op=<trace|cutout|
cleanup|end_check|check|merge> ...`. INSTRUCTIONS: "kitchen: kitchen_utensils / kitchen_recipes first for any request
that is not clearly one process; get_guide('kitchen')".
