# ROADMAP (rev 9, 2026-11-08)

Rev 8: 009 setup defaults (arc step 30, done 0.11.1) and 010 kitchen guards (Principle X locks) inserted; review layout → 011, later features +2.

Rev 7: new 008 kitchen (utensils + recipes); review layout → 009, later features +1.

Rev 6: new 007 atomic design tools (one MCP tool per operation on any design: ports, setup, sweep, airbox, solder ball); review layout → 008, later features +1.

Rev 5: new 006 re-apply simulation settings (setup / sweep / airbox editable after apply; cut group locked); review layout → 007, later features +1.

Rev 4: new 005 full settings form (all settings, tabs per interface, "Set default"); review layout → 006, later features +1.
Rev 3: new 004 re-cut from previous settings (user 2026-11-06); review layout → 005, later features +1.

Rev 1 (2026-11-04) split every agreed rule into its own code file (features 003-014). Rev 2 follows the split agreed
2026-11-04/05: **code measures and executes; the agent decides with the engineer via guides; unknown cases are
reported with measured values, never guessed.** A case becomes a coded rule only after it has repeated and is stable.

## Rules for every feature

| Type | Result change | Version | Gate before release |
|---|---|---|---|
| restructure | NONE (Principle IX) | patch | `tests/regression.py` + `tests/pidc_check.py` identical to before |
| new process / tool | new behaviour beside the old one | minor | old references PASS + new check script PASS |
| coded rule | changes results for a case | minor | new reference data + old references PASS |

- Each feature: specify → clarify → plan (contracts/ for every new/changed public function, format
  `specs/CONTRACTS.md`) → tasks → implement → converge. Commit after each step.
- No change to existing MCP tool names, guides, prompts, Excel / CSV formats, output folders (additions allowed).
- Old import paths keep working (thin re-exports) until a MAJOR release.

## Features (in order)

| # | Name | Type | Scope | Depends on | Status |
|---|---|---|---|---|---|
| 002 | Architecture + core/ | restructure | `core/` (errors, validate, config/template, edb session, geometry, units, registry); contract format; re-exports | — | done 0.5.1 |
| 003 | Interface simulation | new process | schematic/BOM → markdown; agree content; cut (stage 1) on copies by sub-agents; end check + settings table; apply (stage 2) + self-check; merge into the engineer's workspace; remote sequential run. Cutter split `cut_stage` / `apply_stage` | 002 | done 0.6.0 |
| 004 | Re-cut from previous settings | new process + small rule | re-cut an interface "như lần trước": list earlier runs (registry / request id / `user_settings` path), re-trace, show only differences, gates A-B-C with old values pre-filled; ONE `user_settings` file per agreement; HFSS arc step 10 deg (template row, both flows, self-check) | 003 | done 0.7.2 |
| 005 | Full settings form | new process | Gate B form shows ALL per-interface template settings grouped, locked rows read-only, "Set default" (team defaults, sweep never invented), one tab per interface, copy to all tabs; values stored in `user_settings`; chat-table fallback | 004 | done 0.8.0 |
| 006 | Re-apply simulation settings | new process | after apply, `setup.*` / `sweep.*` / `airbox.*` stay editable: re-apply overwrites only the simulation setup of the cut design (backup `*_old_<time>`, Gate B again, self-check, `user_settings` updated); cut group (`cutout.*`, `series.*`, `cleanup.*`, `port.*`, `solder_ball.*`) locked after apply (change = re-cut); form opens applied tabs with the cut group read-only | 005 | done 0.9.0 |
| 007 | Atomic design tools | new tools | one MCP tool per operation on ANY existing design (not only interface_sim output): ports, setup, sweep, airbox, solder ball; template defaults, input validation, copy by default, backup, self-check read-back, short report; guide `design_tools` | 006 | done 0.10.0 |
| 008 | Kitchen: utensils + recipes | new tools + structure | utensil catalog (every operation alone, safety level, approvals on the utensil), recipe catalog (team recipes in repo + personal per-user folder), missing utensils (cutout, cleanup, end check, self-check, merge any design, ...); existing processes rebuilt as recipes later | 007 | done 0.11.0 |
| 009 | Setup defaults | small rule | arc step default 30 deg, max refine per pass 1..100; default history keeps earlier runs' values on re-cut / re-apply | 004, 006 | done 0.11.1 |
| 010 | Kitchen guards | structure | Principle X locks: shared tool registration (server refuses unregistered tools), contract per catalog entry, gate refusal tests, recipe checks, plan "Kitchen check", converge catalog step | 008 | done 0.11.2 |
| 011 | Review layout (measure + interpret) | new tool + restructure | code gives measurements per channel (signal / GND via, routing, SOV, loss of ref, ref plane change, ref other net, trace stub) as data; agent interprets with the engineer; optional step of 003 after content agreement; old `review_layout` HTML kept | 003 | 0.12.0 |
| 012 | Coded rules from 003 experience | coded rule | cases that repeated in 003 `unusual` (connector end, non-round pads, IC missing GND with gate `user_approved_gnd`) → new handling options of `apply_stage` | 003 runs on real boards | 0.13.0 (PCIe self-test: connector default `smd_rebuild`, series list, port metric 2 x paths, unique review lines; non-round pads / IC without GND still open) |
| 013 | PI-DC + layout edit on core | restructure | `pi_dc`, `edit_layout` use `core` (registry, geometry, units) | 002 | done 0.13.1 (skill registry, core EDB session / aedb path / MM, validation at entry; results identical) |
| 014 | MCP + CLI thin layers | restructure | `aedt_copilot/cli/`; `mcp_server/server.py` args + gates only | 003-013 | done 0.13.2 (cli/ parser + handlers + tasks runner + docs; server logic moved to package; golden tools / schemas / refusals / CLI identical) |
| 015 | No-GND end decision | coded rule | end with no GND pin: code measures (GND vias in body, proposed rectangle, vias on existing GND copper) + image + options; the USER chooses (multiple choice, `other` = free text mapped to an option); gate `user_approved_gnd` on `isim_apply` / `start_cut_batch`; answer in `user_settings.json`; re-cut asks again | 012 | done 0.14.0 |
| 016 | PI-DC + layout edit fixes | fix (patch 0.14.1) | VRM voltage by header name (0 V Drop bug), narrow copper current density (no silent NO_DATA; rule in clarify), empty power net list -> clear error, verdict never PASS with 0 pairs, layout_edit delete vias (padstack ids), pidc.image_width 10000, via ΔT = T_sim (run cfg) − 25 °C | 015 | done 0.14.1 |
| 017 | Retire Excel flow | breaking (MAJOR 1.0.0) | remove Excel-flow MCP tools (review_layout?, propose_channels, read_channels, start_cut_batch, job_status, get_report, merge_to_project, cut-* prompts, workflow guide parts) after checking which are still used by interface_sim / kitchen; move tests/regression.py reference to the interface_sim flow; CHANGELOG migration note | 015 | done 1.0.0 |
| 018 | Multi-board test | test | references for more boards | 012 | later |
| 019 | No-GND end: keep exposed pad | coded rule (option) | new no-GND end option: extend the cut extent to keep the exposed GND pad of the end (e.g. board1 U26 / U21 pin 65 lies just outside the cut) | 015 | done 0.15.0 |
| 022 | Cut keeps end GND pins + Gate A cut form / preview | coded rule + tools (minor 2.1.0) | detect each end's GND pins; an end with GND pins but none fully inside the cut grows only its region (+0.02 per try, no maximum) until one is inside; per-end table + image; Gate A cut settings form (tabs, end factor per end) + read-only cut preview (same extent as the cut); manual end factor; board1 reference changed on purpose (U26 / U21 keep the exposed pad) | 015, 019 | done 2.1.0 |
| 020 | Rename: catalog / tools / workflows | breaking (MAJOR 2.0.0) | remove the kitchen metaphor from names: package / guide / prompt / CLI kitchen -> catalog, utensil -> tool, recipe -> workflow, MCP list_tools / list_workflows / get_workflow / save_workflow, folders workflows/ + ~/.aedt_copilot/workflows (old personal folder still read) | 017 | done 2.0.0 |
| — | Stackup config | postponed | — | — | — |

Dropped from rev 1: fine-grained file-per-rule splits of review / cut / cleanup / ports / sim_setup / batch / merge
(old 003-008) — replaced by the stage split in 003 and measure-only tools in 008; splits are done only when a feature
needs them.

## Target layout (after 014)

```
aedt_copilot/
  aedt_env.py        AEDT resolver (core layer)
  core/              errors validate config edb geometry geometry_edb units registry   (no feature imports)
  cut_board/         inspect_board propose excel_io batch merge(merge_designs) aedt_finish review
                     cutter (cut_stage / apply_stage / cut_channel)   config.py geometry.py = re-exports
  interface_sim/     request schematic content cut ends settings apply merge run report
  pi_dc/  edit_layout/
  cli/               (014)
mcp_server/server.py args + gate locks
guides/  prompts/    usage rules (Principle IV)
tests/unit/          offline tests      tests/regression.py  tests/pidc_check.py  tests/isim_check.py
```

Registry entry (when a registry is used): module-level `NAME` (unique), `ORDER` (int), `run(...)`; files starting
with `_` are helpers (`specs/002-architecture-core/contracts/core-registry.md`).
