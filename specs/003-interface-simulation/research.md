# Research: Interface Simulation

## R1 — Who reads the schematic PDF

- **Decision**: the agent (Claude) reads the PDF itself (Claude desktop / Code read PDFs natively) and fills a FIXED
  markdown template; the tool `isim_save_schematic` validates the template (required tables + headers), stores source
  fingerprints (name, size, mtime). BOM (xlsx / csv) is parsed by code (openpyxl / csv) — deterministic.
- **Rationale**: no PDF library in `.venv` (no pypdf / PyMuPDF); schematic symbols and wires are graphics, text
  extraction alone would not give connections anyway; the agent can look at pages. Code parses the markdown tables
  back for the board-vs-schematic diff, so the diff itself is deterministic.
- **Alternatives**: add pypdf (text only, needs `setup.bat` rerun, still no connectivity) — kept as a later option to
  cross-check refdes lists; netlist import — not available per user (PDF only).

## R2 — Cut before settings (cutter split)

- **Decision**: `cut_stage` (until non-kept components deleted, saved) + `apply_stage` (rest), `cut_channel` calls
  both in one session. Stage-1 context (`bga_ends`, body bboxes, original signal pin positions, nets, ends) saved as
  JSON because it is computed on the full board before the cutout.
- **Risk**: save + reopen between stages could change something read by `apply_stage` (pin positions, component
  transforms, padstack defs). **Check**: `tests/isim_check.py` cuts CPHY_U14_U26 both ways and compares all metrics
  (ports, pins, GND pins, GND vias, plane areas, pin shift) exactly / within reference tolerance.
- **Fallback** if not identical: `isim_apply` runs the full `cut_channel` from `_src` with the agreed P (stage-1
  output then only feeds the end check); cost: one more cutout (~5 min) per apply.
- **Alternatives**: settings first then one-pass cut (rejected: spec order, end check needs the cut); end check on
  the full board read-only (kept as fast pre-check inside `isim_trace`: end types only).

## R3 — Copies for sub-agents

- **Decision**: copy the source `.aedb` into `<iface>/_src/` before `cut_stage`; one worker process per interface;
  `.busy` lock file per interface folder (created atomically with `os.open(O_CREAT|O_EXCL)`, removed at end, stale
  if the PID is gone).
- **Rationale**: spec FR-020; today's cut opens the source writable; one process cannot open the same EDB twice.
- **Alternatives**: shared read-only source (unproven), AEDT-level copy (slower).

## R4 — Gates against a state machine

- **Decision**: each interface `state.json` step ∈ `started → content_agreed → cut → ends_checked → applied →
  merged`, plus `failed`; a tool refuses when the step is wrong OR the approval flag is false. Content change after
  `content_agreed` → back to `started` (cut/settings invalidated, kept files renamed `*_old_<time>`, never deleted).
- **Rationale**: Principle I; spec FR-002, edge case "content changed after cut".

## R5 — Remote solve

- **Decision**: pyaedt `Desktop(machine=host, port=port, new_desktop=False, version=...)` to an AEDT gRPC session the
  engineer starts on the server; project opened by its server-side path; designs solved one at a time
  (`Hfss3dLayout.analyze_setup(setup)`), save after each; progress JSON written by a local background process.
- **Rationale**: grpcio is already installed (pyaedt 1.9 uses it); the user's existing remote practice is a running
  AEDT on the server; no new dependency.
- **Alternatives**: PyAEDT RPC service (rpyc not installed → requirements change); `ansysedt -batchsolve` over
  PsExec / WinRM (needs admin rights, not agreed); cluster submit (not requested).
- **Open for the engineer at run time** (asked by the agent, not a spec gap): server host, gRPC port, sim dir as seen
  from this PC and from the server.

## R5b — Remote solve through the PyAEDT service manager (user, 2026-11-05)

- **Decision**: default mode `service`: `create_session(server, client_port, launch_aedt_on_server=True, aedt_port,
  non_graphical=True, secure=False, listen_all=True)` (service manager port from `settings.remote_rpc_service_manager_port`,
  default 17878), then `Desktop(machine=server, port=cl.aedt_port)`; workspace copied either to a shared folder
  (`sim_dir`) or uploaded with `cl.filemanager.upload` into `sim_dir_server/<run_id>/` (never overwrite:
  `cl.root.pathexists`); after the loop the launched AEDT is closed (license freed). Mode `grpc` = R5.
- **Dependency**: `rpyc==6.0.2` (same as the user's proven client `C:\work`) → requirements change, `setup.bat`
  rerun for other users. Ports default client 18050 / AEDT 50000 (user's firewall ranges 18000-18100 / 50000-50010).
- `PYAEDT_USE_PRE_GRPC_ARGS` only for AEDT 2025.2 without SP (config `sim_servers[*].pre_grpc_args`); server is v261.

## R6 — Settings validation reuse

- **Decision**: `cut_board.config.build_params(values)` (same rules, same messages as the Excel flow); the table is a
  view of the same template keys. Measured proposals are shown but only template-default or engineer values are used
  (no hidden measured overrides).

## R7 — Merge target

- **Decision**: refactor `cut_board.merge.merge` into `merge_designs(target_aedt, sources, out_dir, port, log)`; old
  `merge(job_id, only, port, log)` becomes a thin wrapper (same results). Interface sim calls `merge_designs` with the
  engineer's workspace.
