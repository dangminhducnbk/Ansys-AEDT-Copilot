# Research: Atomic design tools

## R1 — Reuse of cut-flow code

- Setup: `cutter.apply_setup(edb, P, log)` creates setup + sweep + arc step (0.7.0). Sweep part extracted to
  `apply_sweep(st, P, log)` (delete existing sweeps, `add_sweep`, interpolation settings) so `sweep` op can change only
  the sweep. Airbox: `apply_airbox(edb, P)`. Solder ball: `set_solder_ball(edb, P, rd, nets, short_side, log)` with the
  mm-string fix. Ports: loop in `apply_stage` (`p.create_coax_port(name=f"{rd}.{pin}.{net}")`) extracted to
  `create_ports(edb, rd, nets, log)`.
- Setup delete: `edb.setups[name].delete()` (used by 006 `reapply_sim`, verified on board1 copy 2026-11-06).

## R2 — Read-back

- Setup / sweep / arc step: `interface_sim.apply.read_setup` (0.7.0, verified). Airbox: `read_airbox` (0.7.2,
  verified). Ports: `edb.ports` / `edb.excitations` names (count + names). Solder ball: component property
  `GetSolderBallProperty().GetDiameterValue()` / `GetHeightValue()` (strings with mm, verified 2026-10-23).

## R3 — Lock

- Refuse when `<project>.aedt.lock` exists for the `.aedt` of the same name, or a `*.lock` inside the `.aedb`
  (AEDT holds it while open). Never delete a lock.

## R4 — Copy naming

- `<stem>_<op>_<YYYYmmdd_HHMMSS>.aedb` next to the source (suffix `_2`, `_3` if taken). In place:
  `<stem>_old_<time>.aedb`. Copy ignores `*.lock`.
