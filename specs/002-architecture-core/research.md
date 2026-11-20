# Research: Architecture + core/

No NEEDS CLARIFICATION in Technical Context. Decisions below come from reading the current code (2026-11-04).

## R1 — One template reader for 3 CSV formats

- **Found**: `cut_board/config.template_rows` (8 columns by position), `pi_dc/common.params` (positions 0/3/6,
  uses `cut_board.config.coerce`), `edit_layout/run.defaults` (5-column template, `Default` at position 3, `float`).
- **Decision**: `core.config.template_rows(path)` maps columns by HEADER NAME (`Key, Parameter, Unit, Type, Scope,
  Mandatory, Default, Description`); missing columns → today's defaults (`type` "text", `scope` "channel",
  `mandatory` False, `unit` "", `desc` ""). Same comment / blank / BOM handling (`utf-8-sig`, skip `#` and blank
  lines, first remaining line = header, skip empty key).
- **Rationale**: one reader, no template format change (Principle III, IX).
- **Alternatives**: keep three readers (rejected: duplication, cross-feature import); change templates to one
  format (rejected: Principle IX).

## R2 — Error type

- **Decision**: `CopilotInputError(ValueError)` with structured `name`, `expected`, `got`.
- **Rationale**: existing callers catch `ValueError` (build_params, server); subclass keeps them working.
- **Alternatives**: `RuntimeError` subclass (rejected: today's bad-value paths use `ValueError`); plain message
  string (rejected: Principle VII needs input name + expected + got).

## R3 — Registry discovery

- **Decision**: auto-discovery with `pkgutil.iter_modules` over the registry package; entries declare `NAME`,
  `ORDER`, `run`; sort `(ORDER, NAME)`; `_*.py` skipped; duplicate / missing → `RegistryError`.
- **Rationale**: user rule "new rule = new file, no edit to old code"; order matters (classify_ends before cleanup).
- **Alternatives**: explicit list like `pi_dc.workflow.SKILLS` (rejected: needs editing an existing file);
  decorator registration (rejected: still needs an import list somewhere).

## R4 — EDB session

- **Decision**: `core.edb.edb_session()` context manager on top of `aedt_env.open_edb` (version explicit,
  `grpc=False`), `edb.close()` in `finally`. Path normalised by `aedb_path` (logic of `edit_layout.run._aedb`).
- **Rationale**: callers today repeat `try/finally edb.close()` (cutter, propose, review, edit_layout).
- **Note**: callers are migrated in 003-009, not in 002 (keeps 002 risk-free for regression).

## R5 — Geometry move without result change

- **Decision**: move the functions verbatim (same float operations / order); EDB-reading `prim_points` goes to
  `geometry_edb.py` so `geometry.py` is pure and importable without PyEDB.
- **Test**: golden JSON from the current module on fixed cases (incl. zero-length segment, crossing segments,
  point on edge, degenerate polygon) compared with `==` (no tolerance).

## R6 — Test runner

- **Decision**: stdlib `unittest`; `pytest` is not in `.venv` and the requirement pins stay unchanged.

## R7 — Golden capture before move

- **Decision**: first task writes `tests/unit/_make_golden.py` and runs it on the CURRENT code →
  `tests/unit/golden/*.json` committed; after the move tests compare core output to golden.
- **Rationale**: proves SC-001-level identity for the offline part without AEDT.
