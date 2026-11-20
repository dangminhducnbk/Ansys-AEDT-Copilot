# Research: Kitchen model

## R1 — Where the missing operations live today

| Operation | Code today | Bound to |
|---|---|---|
| trace | `inspect_board.trace_channel(edb, a, b, patterns, refs)`, `interface_sim.content._board_trace` | Excel propose / isim request |
| cutout | `cutter.channel_sets` + `cutter.cut_stage(edb, ch, P, cell, dst, "create_new", log, ...)` on a board COPY (`interface_sim.cut.copy_source`) | isim request / Excel batch |
| GND cleanup | `cutter.cleanup_gnd(edb, P, nets, ends, bga_ends, extent_area, protect_ids, protect_polys, log)` | `apply_stage` |
| end check | `interface_sim.ends._measure(edb, rd, nets, refs, bga, th)` + `classify_unusual(end, th)` | isim state (`cut`) |
| self-check | `interface_sim.apply.self_check(aedb, P, ch, stage1, metrics, version)` | isim apply |
| merge | `cut_board.merge.merge_designs(orig, sources, out_dir, port, log)` | Excel job / isim request |

All take plain arguments (Python dicts, paths) → wrappers can call them without the process state.

## R2 — Cleanup without stage 1

- `cleanup_gnd` needs `bga_ends` and `extent_area`. Decision: if `stage1.json` sits next to the design (made by
  `design_cutout`), read them; else `bga_ends` = ends whose type (`inspect_board.end_type` on signal pins) is BGA /
  through-hole, `extent_area` = area of the largest GND polygon's outline on a plane layer (same rule as
  `cleanup_gnd`'s plane detection, ratio to that area). Report says which source was used.

## R3 — Catalog source of truth

- Decision: Python list in `kitchen/catalog.py`. Test parses `mcp_server/server.py` with `ast` (as
  `test_interface_unchanged` does) and checks: same set of tool names; for safety `original / workspace / remote`
  the gate parameter named in the entry exists in the tool's signature.

## R4 — Recipe format

- Markdown + YAML front matter (PyYAML already used for `config.yaml`); body free text so the agent reads it like a
  guide. Prompts already use front matter (`description:`), so the pattern is familiar.

## R5 — Personal folder

- `%USERPROFILE%\.aedt_copilot\recipes\` (the same root as the isim registry `~/.aedt_copilot`); env
  `AEDT_COPILOT_RECIPES` for tests / other PCs.
