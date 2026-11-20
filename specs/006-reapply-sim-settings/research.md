# Research: Re-apply simulation settings

## R1 — Rewriting the setup of a cut design with PyEDB

- Decision: delete the existing HFSS setup(s) (`edb.setups[name].delete()`), then call `cutter.apply_setup` (creates
  setup + sweep + arc step) and `cutter.apply_airbox` (extent info), `edb.save()`.
- Evidence: `HfssSimulationSetup` attributes listed 2026-11-06 include `delete`; `create_hfss_setup` with an existing
  name is avoided by deleting first. To confirm on the board1 copy in the AEDT check.
- Alternative rejected: editing the setup in place field by field (many PyEDB setters, harder to keep identical to the
  first apply).

## R2 — Geometry unchanged proof

- Decision: compare `collect_metrics` (ports, components pins / GND pins, GND vias, GND by layer) of the re-applied
  design with the previous `result.json`; `max_pin_shift_mm` copied from the previous result (stage-1 positions are not
  re-measured, geometry untouched).

## R3 — Merged interface

- Decision (user 2026-11-06): step `merged` → `applied` after a re-apply; the earlier merge kept in `merged_before`;
  workspace untouched; next `isim_merge` adds a new design (`_v2` rule of `merge_designs`).
