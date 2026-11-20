---
description: "Tasks for feature 003 Interface Simulation"
---

# Tasks: Interface Simulation

**Input**: `specs/003-interface-simulation/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Prerequisite**: feature 002 (`aedt_copilot/core/`: `CopilotInputError`, `validate`, `config`, `edb`) implemented
and released (0.5.1). Do not start 003 before.

**Tests**: REQUIRED (Principle VII): offline `unittest` in `tests/unit/` for pure logic; AEDT checks
`tests/regression.py` (old flow identical) and new `tests/isim_check.py` — AEDT runs only with the user's OK, on
COPIES of board1.

**Rules for every task**: Python `.venv\Scripts\python.exe`; files UTF-8 via editor tools; never touch `test/`,
`_backup_20261104_2026r1/`; no change to existing MCP tools, prompts, guides (except adding new ones), Excel format,
output folders; code comments Vietnamese; commit after each phase; `graphify update .` after code phases.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Confirm 002 is done (`aedt_copilot/core/` exists, `tests/unit` PASS); else STOP and tell the user
- [X] T002 Create package `aedt_copilot/interface_sim/__init__.py` (docstring: process steps, folder layout from plan.md)
- [X] T003 Add job-scope rows to `templates/autocut_template.csv` (comment block `# interface_sim`):
  `interface_sim.connector_patterns` (list, default `J*,CN*,CON*`), `interface_sim.round_pad_aspect_max` (num, 1.1),
  `interface_sim.pad_size_tol_pct` (num, 10), `interface_sim.gnd_near_smd_mm` (num, 1.0); verify the channel
  Excel `Settings` matrix is unchanged (job scope rows are not in it) with an offline test
  `tests/unit/test_isim_template.py`
- [X] T004 [P] Add a COMMENTED `sim_servers` example (name, host, port, sim_dir_local, sim_dir_server) to
  `config.yaml` (comment lines only, no value change) and document it in `README.md`; `core.config.machine()`
  passes the key through unchanged

---

## Phase 2: Foundational (request + state machine, blocks all stories)

- [X] T005 Implement `aedt_copilot/interface_sim/request.py` per `contracts/isim-request.md`: `start`, `load`,
  `folder`, registry `~/.aedt_copilot/isim_requests.json`, `get_state`, `set_state` (atomic temp + `os.replace`,
  history append), `require_step`, `advance` (only `started → content_agreed → cut → ends_checked → applied →
  merged`, `failed` from any; `started` from any renames outputs `*_old_<time>`, never deletes), `busy` lock
  (`O_CREAT|O_EXCL`, PID + time, stale when PID dead); request folder
  `<workspace dir>/Ansys AEDT Copilot/interface_sim/<YYYYmmdd_HHMMSS>/`; interface names validated with
  `cut_board.excel_io.name_errors` rules (unique case-insensitive, no `<>:"/\|?*;` or space)
- [X] T006 [P] Implement `aedt_copilot/interface_sim/report.py`: markdown table helpers (escape `|`, mm with 3
  decimals) used by content / ends / settings / status / run
- [X] T007 Tests `tests/unit/test_isim_request.py`: start validation errors, transitions allowed / refused,
  rename-not-delete on reset, atomic write, busy lock (held, stale PID, released on exception), name rules
- [X] T008 (implemented as ONE sub-command `isim --op=<op> --args|--args-file`, op table in interface_sim/api.py) Add CLI sub-command group in `aedt_copilot/__main__.py`: `isim-start`, `isim-bom`, `isim-schematic`,
  `isim-trace`, `isim-confirm`, `isim-cut`, `isim-ends`, `isim-validate`, `isim-apply`, `isim-status`, `isim-merge`,
  `isim-run`, `isim-run-status` (args only, `--key=value`, JSON on stdout; call package functions); existing
  sub-commands untouched

**Checkpoint**: unit suite PASS → commit.

---

## Phase 3: User Story 0 - Read schematic and BOM once (P1)

**Goal**: one `schematic.md` per source version. **Independent Test**: BOM fixtures parse; markdown template round-trips;
up-to-date check reuses.

- [X] T009 [US0] Implement `aedt_copilot/interface_sim/schematic.py` per `contracts/isim-schematic.md`: `parse_bom`
  (xlsx via openpyxl first sheet with header row, csv `utf-8-sig` with `,`/`;` sniffing; column map
  refdes ← `Refdes|Designator|Reference|Ref Des|RefDes|Part Reference`, part ← `Part Number|PartNumber|MPN|
  Manufacturer Part Number|Part`, value ← `Value|Comment`, desc ← `Description|Desc`; expand `R1-R4`, `R1, R2 R3`),
  `fingerprints`, `is_up_to_date`, `template()` (sections `## Sources`, `## Components` `| Refdes | Part | Value |
  Description | Page |`, `## Nets` `| Net | Pins (refdes.pin, ...) | Page |`, `## Unreadable`, `## BOM differences`
  `| Refdes | In BOM | In schematic | Note |`), `save` (validate sections, write md + `schematic.sources.json`, BOM
  vs table differences as warnings), `parse`
- [X] T010 [P] [US0] Test fixtures `tests/unit/fixtures/isim/bom_designator.xlsx` (create with openpyxl in the test
  setup, not committed binary), `bom_semicolon.csv`, `schematic_ok.md`, `schematic_missing_nets.md`; tests
  `tests/unit/test_isim_schematic.py` (mapping, ranges, duplicate refdes warning, missing refdes column error,
  missing section error, parse round-trip, fingerprint change → not up to date)
- [X] T011 [US0] MCP tools in `mcp_server/server.py`: `isim_start`, `isim_bom`, `isim_schematic_status`,
  `isim_save_schematic` per `contracts/mcp-tools.md` (thin: validate args → `_cli(["isim-...", ...])`); `isim_start`
  also returns `schematic.template()` when no up-to-date markdown exists

---

## Phase 4: User Story 1 - Agree the interface content (P1)

**Goal**: confirmed content per interface. **Independent Test**: board1 `U14,U26` → CPHY trio proposal; confirm gate.

- [X] T012 [US1] Implement `aedt_copilot/interface_sim/content.py` per `contracts/isim-content.md`: `trace` (open
  board READ-ONLY with `core.edb.edb_session`; refdes only → `inspect_board.trace_channel` per pair; nets only →
  components on nets excluding reference nets, 2-pin R/C/L followed as series; patterns with fnmatch; grouping
  `propose.group_diff`; end types pre-check `inspect_board.end_type`; > 2 end candidates → `candidates` list with pin
  counts; unknown names → CopilotInputError with ≤ 5 difflib matches; structural settings = template defaults of
  `cutout.*`, `series.keep`; writes state `started` + `content.md`), `diff` (pure: `missing_in_schematic`,
  `missing_on_board`, `pin_mismatch`, `name_case_or_prefix` probable, `series_value`), `confirm` (validate content
  fields, every schematic diff has `resolution`, advance `content_agreed`, write `content.md`)
- [X] T013 [P] [US1] Tests `tests/unit/test_isim_content.py`: `diff` cases with fake board facts + parsed schematic;
  `confirm` validation errors (net not on board, group not subset, unresolved diff, duplicate name) using a fake
  board-facts provider (inject function)
- [X] T014 [US1] MCP tools `isim_trace`, `isim_confirm_content` (GATE A: refuse unless
  `user_confirmed_content=true`; refusal text names the gate) in `mcp_server/server.py`

---

## Phase 5: User Story 2 - Cut, check ends, agree settings, apply (P1) 🎯 core value

**Goal**: applied, self-checked design per interface; settings re-applicable without re-cut.
**Independent Test**: quickstart §2 (old flow identical) + §3 (two-stage identical, ends table).

- [X] T015 [US2] Split `aedt_copilot/cut_board/cutter.py` per `contracts/cutter-split.md`: move the body of `_cut`
  into `cut_stage(edb, ch, P, cell, dst, mode, log) -> stage1` (open-time checks, `bga_ends`, `bodies`, `sig_pos0`,
  extent, cutout, delete other cells, rename cell, delete non-kept components) and `apply_stage(edb, stage1, ch, P,
  log)` (series 0 Ω, SMD rebuild, cleanup, BGA rebuild, ports, pin shift, solder ball, setup, airbox, save, metrics,
  check); `_cut` calls both on the SAME open EDB (statement order unchanged); add `save_stage1` / `load_stage1`
  (tuples ↔ lists). `cut_channel` signature / return unchanged
- [X] T016 [US2] (2026-11-05: one-pass CPHY_U14_U26 after split identical to 0.5.1, regression OK) Ask the user for OK, run quickstart §2 (`cut --only CPHY_U14_U26 --wait` on the board1 copy +
  `tests/regression.py`); metrics must equal the 0.5.1 baseline; on difference STOP and fix T015
- [X] T017 [US2] Implement `aedt_copilot/interface_sim/cut.py` per `contracts/isim-cut.md`: inside `request.busy`,
  copy board `.aedb` → `<iface>/_src/` (skip if same size + mtime), open the COPY writable via `core.edb`,
  `cut_stage` → `<iface>/stage1/<name>.aedb`, save, `stage1.json`, advance `cut`; on error `failed` +
  `cutter.remove_partial` only for outputs created by this run; worker runs in a subprocess (CLI `isim-cut`) like
  `batch.worker`, log `<iface>/cut.log`
- [X] T018 [US2] Implement `aedt_copilot/interface_sim/ends.py` per `contracts/isim-ends.md`: `check` (READ-ONLY on
  stage1; type incl. `connector` by `interface_sim.connector_patterns`; signal pins pad shape / size from pad bbox
  only for signal pins; GND pins within `cleanup.bga_gnd_pin_keep_dist_mm` (BGA) or `interface_sim.gnd_near_smd_mm`
  (SMD); solder ball; via-in-pad; `ends.json` + `ends.md`; advance `ends_checked`) and pure `classify_unusual`
  (rules `no_gnd_near_signal`, `non_round_pad_bga`, `connector_end`, `unknown_type`, `pad_size_mismatch`; options ⊆
  `smd_rebuild, keep_component, no_solder_ball, stop_interface`)
- [X] T019 [P] [US2] Tests `tests/unit/test_isim_ends.py` (`classify_unusual` each rule + thresholds from template,
  options lists)
- [X] T020 [US2] Implement `aedt_copilot/interface_sim/settings.py` per `contracts/isim-settings.md`: `proposal`
  (channel-scope template rows, defaults, mandatory sweep empty, measured info only in `reason`, structural rows
  `locked (re-cut to change)`), `validate` (`cut_board.config.build_params` messages + handling checks + structural
  change → "re-cut needed"), `save` (`settings.json` + `settings.md`)
- [X] T021 [P] [US2] Tests `tests/unit/test_isim_settings.py`: proposal rows == template channel rows; validate
  messages identical to `build_params` for empty sweep / start ≥ stop / step > span; missing handling for an unusual
  end; structural change detected
- [X] T022 [US2] Implement `aedt_copilot/interface_sim/apply.py` per `contracts/isim-cut.md`: `run` (inside busy;
  validate; copy stage1 → `final/<name>.aedb`, existing final renamed `_old_<time>`; apply handling
  (`keep_component` → skip SMD rebuild for that refdes, `no_solder_ball` → skip ball for that refdes,
  `stop_interface` → `failed` with reason, `smd_rebuild` = default); open writable; `apply_stage`; save;
  `self_check`; `result.json`; advance `applied`), `self_check` (read-only reopen: ports == 2 × signal nets,
  `max_pin_shift_mm` ≤ 1, setup / sweep read back == P, end components present with signal pins)
- [X] T023 [US2] Handling hooks in `cutter.apply_stage`: optional `handling` dict argument (default None = today's
  behaviour) for `keep_component` / `no_solder_ball` per refdes; `cut_channel` passes None (identical results)
- [X] T024 [US2] MCP tools `isim_cut` (needs step `content_agreed`; returns task_id), `isim_check_ends`,
  `isim_validate_settings`, `isim_apply` (GATE B: refuse unless `user_agreed_settings=true` AND `validate` valid AND
  step `ends_checked`) in `mcp_server/server.py`
- [X] T025 [US2] Write `tests/isim_check.py` (AEDT, board1 copy folder argument): run start → trace U14,U26 →
  confirm → cut → ends → apply (defaults + sweep 0/10/0.1) → compare metrics with
  `tests/reference/CPHY_U14_U26.json` (same checks as `regression.check`); repeat U21,J25 (expect `connector_end`
  or `through_hole` for J25 in ends); exit 1 on FAIL
- [X] T026 [US2] (2026-11-05: isim_check both interfaces OK; two-stage == one-pass except component def suffix _cut_2, caused by the earlier merge in the same workspace copy) Ask the user for OK, run `tests/isim_check.py`; if two-stage metrics differ from reference →
  apply research R2 fallback (apply runs full `cut_channel` from `_src` with agreed P) and record it in plan.md

**Checkpoint**: §2 + §3 PASS → commit, `graphify update .`.

---

## Phase 6: User Story 3 - Many interfaces, one workspace (P2)

**Goal**: merged designs in the engineer's workspace. **Independent Test**: quickstart §5.

- [X] T027 [US3] Refactor `aedt_copilot/cut_board/merge.py` per `contracts/isim-merge.md`: `merge_designs(target_aedt,
  sources, out_dir, port, log)` holds the moved logic (backup, prepare, CopyDesign/Paste, `_vN`, compare); `merge()`
  builds `sources` from the job and calls it (same results / messages)
- [X] T028 [US3] Implement `aedt_copilot/interface_sim/merge.py` `run(request_id, names, port)` (each `applied`;
  target = request workspace; lock check → ask message; `merge.json`; advance `merged`) and
  `aedt_copilot/interface_sim/request.py` `status_table(request_id)` (step per interface, open questions, warnings)
- [X] T029 [US3] MCP tools `isim_status`, `isim_merge` (GATE C: refuse unless `user_approved_merge=true`; names ⊆
  applied, else list missing) in `mcp_server/server.py`
- [X] T030 [US3] (2026-11-05: isim_merge -> CPHY_U14_U26_v2, CPHY_U21_J25_v2; old merge_to_project ok) Ask the user for OK, run quickstart §5 on a scratch copy of `board1/simulation.aedt`; also re-run
  the old `merge_to_project` path on a scratch copy (results unchanged)

---

## Phase 7: User Story 4 - Run the simulation on request (P3)

**Goal**: copy + sequential remote solve. **Independent Test**: unit tests with fake solver; manual §6.

- [X] T031 [US4] Implement `aedt_copilot/interface_sim/run.py` per `contracts/isim-run.md`: `plan_copy` (exclude
  `*.aedtresults`, `*.lock`, `_backup`; free space ≥ bytes × 1.1), `server_path`, `start` (new folder
  `<sim_dir>/<request_id>_<time>/`, never overwrite; `run_<time>.json` all `queued`; background process CLI
  `isim-run`), `solve_loop` (one Desktop connection `machine=server, port, new_desktop=False`; open project by server
  path; per design `analyze_setup` + `save_project`; failure → `failed` + message, continue; never close other
  projects; `solver` hook), `status`
- [X] T032 [P] [US4] Tests `tests/unit/test_isim_run.py`: plan_copy exclusions / free-space error (monkeypatched
  `shutil.disk_usage`), server_path mapping and error, start refuses existing folder, solve_loop order + failure
  continues with a fake solver, status table
- [X] T033 [US4] MCP tools `isim_run` (GATE D: refuse unless `user_requested_run=true`; ≥ 1 merged design; ask for
  missing sim_dir / server / port), `isim_run_status` in `mcp_server/server.py`

---

- [X] T041 [US4] (FR-015a) Service-manager mode in `aedt_copilot/interface_sim/run.py`: `mode` service|grpc, `aedt_port`,
  `client_port`, upload transfer (staging copy with EXCLUDE, `cl.filemanager.upload`, refuse existing remote folder),
  `_service_solver` (create_session secure=False listen_all=True, Desktop(machine, port=cl.aedt_port), close launched
  AEDT); `requirements.txt` + `rpyc==6.0.2`
- [X] T042 [P] [US4] Tests in `tests/unit/test_isim_run_gates.py`: service mode argument checks, upload plan (staging
  excludes results / locks), solve_loop with fake service solver + fake upload
- [X] T043 [US4] MCP `isim_run`: `mode` (default service), `aedt_port`, `client_port`; sim_dir optional in service mode,
  sim_dir_server required when not shared; guide `interface_sim` Phase 4 + README updated
- [X] T044 [US4] (2026-11-05: connection + AEDT launch on 192.0.2.27 OK; upload OK (share read-only -> upload mode); solve started, test stopped by the user before the end) Ask the user for OK, test on server 192.0.2.27 (service manager 17878) with the merged workspace copy

## Phase 8: Guide, prompt, polish, release

- [X] T034 Write `guides/interface_sim.md` (English, MISSION / RULES OF ENGAGEMENT / EXECUTION): steps 0-4, the 4
  gates and their flags, tables to show (content, ends, settings, status, run), unusual cases → explain with numbers
  + options, never default; schematic: read PDF, fill `schematic.template()`, save via tool, reuse when up to date;
  sub-agents: one per interface for cut → ends, never ask the engineer directly, return questions; old cut-board
  workflow untouched
- [X] T035 [P] Write `prompts/interface-sim.md` (frontmatter `description:`, body: call `get_guide("interface_sim")`
  first, `$ARGUMENTS` = workspace / interfaces)
- [X] T036 [P] Server `instructions` text in `mcp_server/server.py`: one line for interface simulation ("call
  get_guide('interface_sim') first"); `about()` lists the new process
- [X] T037 Test `tests/unit/test_isim_gates.py`: call every gated server function with flag false / wrong step →
  `refused` (import server module functions directly, `_cli` monkeypatched)
- [X] T038 [P] `CLAUDE.md`: §3 layout (`interface_sim/`), §4 new process row, §8 status; `README.md` short section
- [X] T039 `VERSION` 0.6.0 (minor: new feature); `CHANGELOG.md` entry (new tools / guide / prompt; restart Claude,
  no setup.bat rerun)
- [X] T040 Run full unit suite + `graphify update .`; commit; tag `v0.6.0` locally (push by user); run
  `/speckit-converge`

## Dependencies

- 002 → Phase 1 → Phase 2 → US0 ‖ US1 (US1 diff uses US0 `parse`, but trace works without schematic) → US2 → US3 →
  US4 → Phase 8. Guide (T034) can be drafted any time, finalised last.
- T015 → T016 (regression) before T017-T026. T023 before T022 uses handling. T027 before T028.
- AEDT runs (T016, T026, T030) need the user's OK.

## Parallel examples

- Phase 2: T006 ‖ T007 after T005.
- US0: T010 ‖ T011 after T009. US1: T013 ‖ T014 after T012.
- US2: T019 ‖ T021 after T018 / T020; T018 and T020 are different files (parallel) once T017 exists.
- US4 (T031-T033) offline parts can start after Phase 2.

## Implementation strategy

MVP = Phases 1-5 (one interface end-to-end, applied design, old flow identical). Then US3 merge, US4 remote run,
guide + release 0.6.0.

## Phase 9: Convergence

- [X] T045 CRITICAL: validate the interface `name` before it is used as a folder in `aedt_copilot/interface_sim/request.py` `iface_dir` (non-empty, no `<>:"/\|?*;`, space or `..` -> CopilotInputError, same rules as `check_name`) so `get_state` / `set_state` / settings / ends never touch a path outside the request folder per Constitution VII (contradicts)
- [X] T046 CRITICAL: validate `port` in `aedt_copilot/interface_sim/merge.py` `run` (None / 0 = no attach, else int 1..65535 -> CopilotInputError) per Constitution VII / contracts/mcp-tools.md isim_merge (missing)
- [X] T047 Add offline tests for T045 (`../x`, `a b`, `a/b` -> CopilotInputError from get_state / iface_dir) in `tests/unit/test_isim_request.py` and T046 (port -1, 70000, "abc") in `tests/unit/test_isim_run_gates.py` per Constitution VII (missing)
- [X] T048 Sync contracts with the code: `contracts/cutter-split.md` (cut_stage args nets/ends/keep/refs, apply_stage protect_polys/handling, stage1_to_json/stage1_from_json instead of save_stage1/load_stage1), `contracts/isim-cut.md` (self_check(aedb, P, ch, stage1, metrics, version)), `contracts/isim-ends.md` (classify_unusual(end, th), test file test_isim_ends_settings.py), `contracts/isim-settings.md` (proposal(state, ends, values), validate(..., structural), save(..., rows)), `contracts/isim-run.md` start signature with mode/aedt_port/client_port and test file test_isim_run_gates.py, `contracts/mcp-tools.md` isim_run args mode/aedt_port/client_port + sim_dir optional in service mode per Constitution VII (partial)
- [X] T049 Add to `guides/interface_sim.md` Phase 2 the rule for the stackup file: when the EDB lacks layer data (thickness, material, Dk/Df) read the stackup file from `request.json` and show the values to the user; never edit the EDB stackup without a go per FR-020 (partial)
- [X] T050 (2026-11-05: board1 copies U14_U26 + U21_J25 OK, wrong P detected) Extend `aedt_copilot/interface_sim/apply.py` `self_check` to read back setup / sweep VALUES (max passes, max delta S, sweep start / stop / step, type) and compare with P; verify on the board1 copy (needs AEDT / PyEDB, ask the user first) per FR-013 (partial)
