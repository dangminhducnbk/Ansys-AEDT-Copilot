---
description: "Tasks for feature 005 Full settings form with tabs and Set default"
---

# Tasks: Full settings form with tabs and "Set default"

**Input**: `specs/005-settings-form-tabs/` (plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md)

**Tests**: REQUIRED (Principle VII): offline `unittest` in `tests/unit/`; AEDT check on a board1 COPY only after the
user's OK (T016).

**Rules for every task**: Python = `.venv\Scripts\python.exe`; write files UTF-8 with editor tools; do not touch
`test/`, `_backup_20261104_2026r1/`. Code comments Vietnamese, guides English. Commit after each phase. No push.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 `templates/autocut_template.csv`: Description of `airbox.extent_type` and `airbox.dielectric_extent_type`
  = `conforming | bounding_box | convex_hull` (keys / defaults unchanged); unit tests that read the template stay PASS

---

## Phase 2: User Story 1 - See and edit every setting (P1)

**Goal**: full descriptor list per interface + grouped fallback table. **Independent Test**: offline fixture.

- [X] T002 [US1] Create `aedt_copilot/interface_sim/form.py` per `contracts/isim-form.md`: `choices(desc, typ)`,
  `descriptors(state, ends, values)` (on `settings.proposal`; group = key prefix in template order; locked +
  reason for `cutout.*` / `series.keep`; `default` = coerced template default, None when empty), `table_md(tab)`
- [X] T003 [US1] `form.build(request_id)`: one tab per `request.json.interfaces` (request order): step, enabled
  (`ends_checked` / `applied`), reason, applied, recut_from, descriptors (with `ends.json`), unusual
  `{rd: {rules, options}}`, handling pre-fill (re-cut `kept` handling from feature 004); `groups`; `table_md` of all tabs
- [X] T004 [US1] `form.validate(request_id, entries)`: per interface `settings.validate_for`; per-interface errors
  (step / input) in its own result, never raised for others; unknown interface / not an object → CopilotInputError
- [X] T005 [US1] CLI ops `form`, `validate_form` in `aedt_copilot/interface_sim/api.py`; MCP tools
  `isim_settings_form`, `isim_validate_form` in `mcp_server/server.py` per `contracts/mcp-tools.md` (thin, read-only,
  no gate); `about()` / INSTRUCTIONS line
- [X] T006 [P] [US1] Tests `tests/unit/test_isim_form.py`: descriptor count = channel-scope rows (SC-001); groups in
  template order; locked rows; mandatory sweep `default` None + value empty; choices parsed (`radiation | pml`,
  `mixed | first | second`, airbox extent, bool); re-cut source labels pass through; `table_md` has every key
- [X] T007 [US1] Extend `tests/unit/test_interface_unchanged.py`: new tools present, nothing removed

**Checkpoint**: unit suite PASS → commit.

---

## Phase 3: User Story 2 - "Set default" (P1)

- [X] T008 [US2] Tests in `tests/unit/test_isim_form.py`: applying every descriptor `default` to the editable keys
  (what the widget's "Set default" does) gives `build_params` P equal to template defaults (arc 10, airbox +Z 0.2,
  max passes 30) and keeps mandatory sweep as given / empty (FR-005, SC-002); validate after "Set default" + sweep →
  valid
- [X] T009 [US2] Guide rule "Set default" / "Set default for all tabs" (widget behaviour, mandatory sweep kept) in
  `guides/interface_sim.md` INPUT FORMS

---

## Phase 4: User Story 3 - One tab per interface (P2)

- [X] T010 [US3] Tests: 2 interfaces (one at `ends_checked`, one at `cut`) → 2 tabs, second disabled with its step;
  `validate` with one bad tab → other tab valid; unknown interface → CopilotInputError; handling stays per tab
- [X] T011 [US3] Guide rule: tabs (name, disabled tabs with step, > 8 tabs shortened names + full name on hover),
  "Copy to all tabs" (editable non-locked values only, not handling), submit JSON shape → `isim_validate_form`,
  then per interface `table_md` + explicit go → `isim_apply` per interface

---

## Phase 5: Guide, docs, release

- [X] T012 `guides/interface_sim.md`: replace the GATE B subset field table with "full form from
  `isim_settings_form`" (groups, locked read-only, mandatory empty, unusual-end choice groups); fallback = full grouped
  `table_md`; form = input only (unchanged rule); Excel flow unchanged
- [X] T013 [P] `prompts/interface-sim.md` one line; `README.md` (Vietnamese) form section; `CLAUDE.md` §3 / §8
- [X] T014 `VERSION` → 0.8.0; `CHANGELOG.md` 0.8.0 (restart Claude, no setup.bat)
- [X] T015 Full unit suite + `graphify update .`; commit

---

## Phase 6: AEDT check (ask the user first — board1 COPY)

- [X] T016 (2026-11-06: board1 copy PASS - 2 tabs x 52 descriptors, validate_form both valid, apply both self-check OK, U14_U26 metrics = text flow 20261106_193617; converge -> T017) Ask the user for OK, then quickstart §2: 2 interfaces at `ends_checked` on a board1 copy →
  `isim_settings_form` → `isim_validate_form` → apply both → self-check OK, metrics equal to the text flow (SC-004);
  tag `v0.8.0` locally; run `/speckit-converge`

## Dependencies

- T001 → T002 → T003 → T004 → T005; T006-T008, T010 after T004. Guide tasks (T009, T011, T012) any time after T005.
- T016 after Phase 5 and the user's OK.

## Implementation strategy

MVP = Phase 1-3 (full form for one interface + Set default). Then tabs (US3), docs, release 0.8.0 after the AEDT check.

## Phase 7: Convergence

- [X] T017 Offline test of the CLI ops `form` / `validate_form` through `api.call` and of the MCP tool `isim_validate_form` refusing bad JSON (thin layer, no CLI call) in `tests/unit/test_isim_run_gates.py` per Constitution VII / contracts/mcp-tools.md (missing)
