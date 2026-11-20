# Research: Re-cut from previous settings

## R1 — PyEDB arc step API

- Decision: `HfssSimulationSetup.curve_approx_settings.arc_angle` (str with unit). Set `f"{v:g}deg"`.
- Evidence (2026-11-06, copy of the 003 CPHY_U14_U26 final `.aedb`, pyedb 0.85 .NET, AEDT 2026.1): read `'30deg'`
  (default); other fields `arc_to_chord_error '0meter'`, `max_arc_points 8`, `start_azimuth '0deg'`,
  `use_arc_to_chord_error False`. Set `'10deg'` + `edb.save()` → reopen read-only → `'10deg'`.
- Open: confirm in the AEDT GUI (Setup → Advanced Meshing → circle / arc approximation) during the board1 check.
- Alternatives: `advanced_mesh_settings` (no arc field), AEDT script after merge (not EDB, both flows would need it).

## R2 — Previous-run source

- Decision: `user_settings.json` first; 0.6.0 folders fall back to `state.json` (`content`, `settings.values`,
  `settings.handling`), so runs made before 004 are reusable.
- Workspace match: `os.path.normcase(os.path.abspath())` of `request.json.workspace`.
- Rejected: scan disk for request folders (slow, may hit other projects); registry is the agreed index.

## R3 — Difference on re-trace

- Decision: re-use `content.trace` (same board facts as 003) with old ends + old nets; pure `recut.diff` compares old
  content + old board fingerprint with new facts. Board fingerprint = size + mtime of `<board>.aedb/edb.def`.
- Diff resolution reuses the 003 rule (every diff needs `resolution` before gate A).

## R4 — Handling compare

- Decision: pure function on `ends.json` data (`unusual[].options`); no new measurement code.

## R5 — File consolidation

- Decision (user 2026-11-06): `user_settings.json` per request replaces `settings.json` + `settings.md`.
  Code readers of `settings.json`: none (apply / run read `state.json["settings"]`) → safe to stop writing it.
