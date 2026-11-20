# Tasks: AEDT 2026 R1 Migration

**Input**: `specs/001-aedt-2026r1-migration/` (spec.md, plan.md)

**Board for checks**: `D:\data\boardb_19x19\simulation\20261102_2667\BOARDB-19X19mm-2026-1103_downrev_2667.aedb`
(region box `-3.3,-8.4,4.8,-3.0`, layer `RDL4`)

**Backups**: original of every modified file -> `_backup_20261104_2026r1\<same path>`

## Format: `[ID] [P?] [Story] Description -> Verify`

---

## Phase 1: Setup

- [x] T001 Create `specs/001-aedt-2026r1-migration/` (spec, plan, tasks) -> files exist
- [x] T002 Create backup folder `_backup_20261104_2026r1/` -> folder exists

## Phase 2: Foundational - resolver + shared open_edb (Step A, still 2025.2)

- [x] T003 [US1] New `aedt_copilot/aedt_env.py`: resolve (config `aedt_root` -> env -> registry -> scan), `ensure()`, `info()`, `child_env()`, `siwave_exe()`, `open_edb(grpc=False)` -> imports without pyedb
- [x] T004 [US1] `aedt_copilot/__main__.py`: `aedt_env.ensure()` before dispatch; add `aedt` info to `inspect` / `layout-region` output -> output shows version/root/source
- [x] T005 [P] [US1] `cut_board/inspect_board.py`: `open_edb` -> `aedt_env.open_edb`, default version None -> review/propose/inspect unchanged otherwise
- [x] T006 [P] [US1] `edit_layout/run.py`: `_open` -> `aedt_env.open_edb` -> region/edit unchanged otherwise
- [x] T007 [P] [US1] `cut_board/cutter.py`: `Edb(src, cellname, version)` -> `aedt_env.open_edb(..., readonly=False)`; default version None -> cut unchanged (not run now)
- [x] T008 [P] [US1] `pi_dc/common.py` `siwave_exe` -> resolver; drop `"2025.2"` defaults in `pi_dc/export.py`, `pi_dc/skills/power_tree.py` -> not run now
- [x] T009 [US1] Verify 2025.2: `inspect_board` + `layout_region` (box `" -3.3,-8.4,4.8,-3.0"`, `RDL4`) -> both PASS without Claude restart; record layers, n_nets, n_components, primitives
  - 2026-11-04 PASS: 7 signal layers (RDL6..RDL1, DIE), 602 nets, 59 comps, 37 P/G nets; region 231 prims, 5584 via/pin, 13 comps, 14 padstacks
  - Extra root cause found: process also lacked `ANSYSLMD_LICENSE_FILE` ("Can't acquire license") -> `aedt_env.sync_env()` copies Ansys/license vars from saved Windows env (registry, read-only)

**Checkpoint**: tools work again on 2025.2.

## Phase 3: Server (Step B - needs Claude desktop restart)

- [x] T010 [US2] (edited; verify after restart) `mcp_server/server.py`: Popen `env=aedt_env.child_env()`; `--key=value` for board/box/layers/nets/channels/sim/cell/excel/only/dir/aedb/plan; `about.requires` + `aedt` info in about/show_defaults -> after restart: `layout_region(box="-3.3,-8.4,4.8,-3.0")` PASS; about shows 2026 R1

## Phase 4: Switch to 2026.1 (Step C)

- [x] T011 [US3] `config.yaml` `aedt_version: "2026.1"`; `cut_board/config.py` default `"2026.1"` -> `show_defaults` (after restart) shows 2026.1
- [x] T012 [US3] Confirm read-only open (`isreadonly=True`) for inspect/region; board `.aedb` mtime unchanged -> no upgrade/save
- [x] T013 [US3] Verify 2026.1: `inspect_board` + `layout_region` -> PASS; diff vs T009 (layers, n_nets, n_components, region primitives) = none
  - 2026-11-04 PASS: inspect identical; region.json byte-identical to 2025.2; edb.def mtime unchanged

**Checkpoint**: read-only tools on 2026 R1. STOP here for user review.

## Phase 5: Write operations on copies (later)

- [x] T014 [US4] Cut 1 small channel (`start_cut_batch`) on a COPY -> `get_report` PASS; compare ports/components/setup with 2025.2; opens in AEDT 2026 R1
  - 2026-11-04 PASS (CLI propose + cut --wait on copy of board1): regression OK, 339 s; 24 ports, 101 GND vias, planes 845-865 mm2,
    U14 47/35, U26 22/10, pin shift 0.21 mm = identical to 2025.2. "Opens in AEDT 2026 R1" (GUI) deferred to T017
- [x] T015 [US4] `layout_edit` small B04 plan on a COPY -> checks + before/after images same as 2025.2
  - 2026-11-04 PASS (`tests/layout_edit_b04.py all`, needs `PYTHONIOENCODING=utf-8` when output is redirected):
    8 op results + 16 checks identical to `tests/_out_*.log`; 67.8 s / 61.7 s. Images not pixel-compared
- [x] T016 [US4] PI-DC on a COPY of solved SIwave folder: `siwave_exe` -> v261; 6 images, size, colour bar OCR, Vias.txt; skills + report vs 2025.2
  - 2026-11-04 PASS (`pidc --dir <copy>` + `tests/pidc_check.py`): 1717 s, SIwave v261; 59 images, verdicts
    CD WARN / via PASS / voltage INFO / power tree FAIL = same as 2025.2 output
- [x] T017 [US4] merge / finish last (saves 2026 R1 format) -> backup confirmed, user informed; designs present, net colours right
  - 2026-11-04 BLOCKED: merge (copy of board1 + T014 job) fails in prepare at `apply_display` -> `oEditor.SetNetColor`
    "Failed to execute gRPC AEDT command". A/B same board: 2025.2 OK, 2026.1 FAIL (non-graphical AND GUI).
    `HighlightNet`, `ZoomToFit` OK. Scripting guide 2026 R1 shows the same syntax. Also failed: Check_Containment /
    Via_Persistence args, list/float colour, ChangeProperty on `Nets:<n>`. Copy project not modified (backup made).
    Needs: 2026 R1 recorded script for net colour (user, Tools > Record Script) and/or colour failure -> warning.
- [x] T017a [US4] `cut_board/aedt_finish.py` `apply_display`: `SetNetColor` failure -> warning (not error); `merge.py` /
  `finish()` report it (`warnings` per channel / in result) -> merge on copy of board1 runs: design pasted, ports/setups/sweeps
  equal, warning "net colour not set" shown (user decision A+B 2026-11-04)
  - 2026-11-04 PASS: merge -> `CPHY_U14_U26` state ok (ports/setups/sweeps equal), backup made, warning shown.
    `finish` (AEDT 2026 R1 GUI) PASS: 13 nets, 24 ports, Setup1, warning shown. Also fixed: `finish` called
    `release_desktop(close_on_exit=...)` -> pyaedt 1.9 name is `close_desktop` (finish had never been run).
    Guides verify §7 + workflow Phase 7: colour warning = WARN, not error
- [x] T017b [US4] (closed: not possible on 2026 R1, user accepted warning 2026-11-04) Use the 2026 R1 net-colour syntax from the user's recorded script (waiting for user) -> colours red/blue in AEDT 2026 R1
  - 2026-11-04: recorded script (`D:\work\project\tool\record_script\color_net_aedt.py`) = SAME syntax. Cause = gRPC path
    (pyaedt `oeditor.SetNetColor`, also via `SetActiveEditor("Layout")`) rejected; same call inside AEDT via
    `oDesktop.RunScript(<temp .py>)` works (non-graphical + GUI). `apply_display`: gRPC first, fallback RunScript, warning
    only if both fail. `finish` on merged design (GUI): warnings [] . Colours not in .aedt (stored in edb.def) ->
    visual check by user pending
  - 2026-11-04 user: colours WRONG (unchanged). Cause: RunScript does not propagate script errors; inside AEDT
    SetNetColor also fails ("call failed"), non-graphical and GUI, standalone and merged project. The user's own
    recorded script replayed via RunScript fails the same way -> AEDT 2026 R1 scripting bug; only manual GUI action works.
    RunScript fallback removed (false success); back to T017a warning. Colours on 2026 R1: not possible by script now

## Phase 6: Polish / release 0.5.0

- [x] T018 `setup.bat` (check `ANSYSEM_ROOT261` then 252, write version), README, CLAUDE.md, guides (2026 R1) -> text review
  - 2026-11-04: setup.bat picks 261 then 252, writes `config.yaml` via new `tools/set_aedt_version.py` (tested 2025.2 <-> 2026.1,
    bad input rc=1); README (2026 R1 + limits), prompt copilot-help, CLAUDE.md (env, gotchas, finish status). Guides: colour WARN (T017a)
- [x] T019 Constitution amendment (target 2026 R1) via `/speckit-constitution` -> owner only
  - 2026-11-04: 1.1.1 (PATCH, Technical Constraints only), approved by owner ("Đồng ý, làm tiếp")
- [x] T020 `tests/regression.py` + `tests/pidc_check.py` PASS on 2026.1; VERSION 0.5.0; CHANGELOG (setup.bat rerun: yes); tag `v0.5.0` -> PASS
  - 2026-11-04: regression PASS (T014), pidc_check PASS (T016); VERSION 0.5.0; CHANGELOG; local tag v0.5.0 (push = owner)
- [x] T021 `graphify update .` -> graph updated

## Dependencies

T003 -> T004..T008 -> T009 -> T010 -> T011..T013 -> T014..T017 -> T018..T021
