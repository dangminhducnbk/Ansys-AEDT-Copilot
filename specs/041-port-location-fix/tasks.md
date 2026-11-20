# Tasks — 041 port location (released with 039 as 5.2.0)

- [x] T001 `cutter`: `pad_end_toward`, `port_end`, `plan_smd_pin(paths=)`, `comp_model` explicit flag.
- [x] T002 `rebuild_smd_component`: port plan by explicit choice, `port_report`; `apply_stage` metrics `port_location`.
- [x] T003 `apply.self_check`: port location item (read-back vs source pad centre).
- [x] T004 Page: `data.ends_data` port_end / port_how / no_trace_exit; `model.defaults` centre for no-trace ends;
  `page.js` portXY + label + note.
- [x] T005 [P] `tests/unit/test_port_location_041.py` (fake pins: trace / via-in-pad / square; self-check item;
  defaults).
- [x] T006 BOARDA copy: PCIE_U14_J25 with J25 end and centre (SC-001 / SC-002); board1 regression + config_flow_check
  (pcie_check on test1 not run: old path unchanged, covered by regression).

## Extension — port slider + traces (release 5.3.0)

- [x] T007 `cutter`: `port_span`, `port_at`; `pad_end_toward` via `port_span`; `comp_model` `port_pct` mapping.
- [x] T008 `rebuild_smd_component(port_pct=)`: targets per pin, 50 % / within 1 µm = not moved; report `pct`,
  `targets`; `apply_stage` passes `port_pct`.
- [x] T009 `apply.port_location_mismatches`: target check (± 1 µm) when `targets` present.
- [x] T010 `config/data.ends_data`: `port_span`, `traces` per end.
- [x] T011 `config/model`: `port_pct` state, defaults, validation, old `port_location` read.
- [x] T012 `page.js`: slider + quick buttons + per-pad offsets, `portXY` from span, traces drawn.
- [x] T013 [P] `tests/unit/test_port_slider_041.py`; existing tests green.
- [x] T014 Guide `interface_sim`, CHANGELOG, VERSION 5.3.0, CLAUDE.md row.
- [x] T015 Copies: BOARDA J25 0 / 50 / 100 % (SC-005); board1 regression + config_flow_check; browser page check.
