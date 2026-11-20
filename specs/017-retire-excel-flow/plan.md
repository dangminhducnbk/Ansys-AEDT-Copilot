# Implementation Plan: Retire the Excel cut flow

**Branch**: `main` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Remove exactly the approved inventory (spec.md). First move the 5 shared helpers out of the Excel modules, so the
kept flows never import a removed file; then delete tools / CLI / modules / prompts / guides / recipe; then fix
guides, server instructions, tests; rewrite `tests/regression.py` on the interface-sim flow with the unchanged
reference. MAJOR 1.0.0.

### 1. Shared helpers → `cut_board/naming.py` (moved verbatim)

| Function | From | Users kept |
|---|---|---|
| `board_paths`, `default_name`, `unique_name` | `excel_io.py` | `review.py`, `review_checks`, `interface_sim/content.py`, `design_tools/cutout.py` |
| `parse_request`, `group_diff` (+ `DIFF_SUFFIX`, `TRIO_SUFFIX`) | `propose.py` | `review.py`, `review_checks`, `review_checks/routing.py`, `interface_sim/content.py` |

### 2. Removed (approved table)

| Kind | Items |
|---|---|
| MCP tools | `propose_channels`, `read_channels`, `start_cut_batch`, `job_status`, `get_report`, `merge_to_project`, `review_layout` |
| Kitchen catalog | the 7 entries above (catalog test keeps catalog = server tools) |
| CLI | `propose`, `cut`, `status`, `report`, `merge`, `run-job`, `worker`, `review` (+ handlers) |
| Modules | `cut_board/excel_io.py`, `cut_board/propose.py`, `cut_board/batch.py`; `cutter.cut_channel` + `_cut`; `merge.merge` (job) |
| Server | Excel gate code (`user_approved_review/_excel/_verify`, `batch.gnd_missing` refusal), `excel_io.review_reports` / `check_channels` uses |
| Prompts | `cut-board`, `cut-run`, `cut-status`, `cut-report`, `cut-open`, `cut-rerun` |
| Guides | `workflow`, `setup_note` (moved), `verify` (moved), `review_layout` (moved) |
| Recipe | `excel-cut` |
| Template rows | `run.channel_timeout_min`, `run.max_parallel` |

Kept on purpose: `finish_in_aedt` + CLI `finish` (Q2), `merge_designs`, `aedt_finish.apply_display`, `review.py`
(`review()` = design_review html), `inspect_board`, `run.output_subdir`, `display.*`, `review.*`, openpyxl (isim BOM).

### 3. Moved guide content

- `setup_note` → `interface_sim` section "Setup / sweep notes".
- `verify` criteria → `interface_sim` step 7 (verification list).
- `review_layout` (HTML report reading rules, summary first) → `review_measure` section "HTML report".
- `finish_in_aedt` documented in `interface_sim` (after apply / merge) and `design_tools`.
- Server `instructions`, `about`, prompt `copilot-help`: start with `kitchen` / `interface_sim`; no removed tool.
- `README.md`: Excel-flow usage replaced by the interface-sim flow (text only).

### 4. Tests

- `tests/regression.py` rewritten: `python tests/regression.py <workspace.aedt (board copy)>` → isim start / trace
  U14,U26 `CPHY_B02DEVA_*` / confirm / cut / ends / apply (U26 = `gnd_plate_vias`, sweep 0/10/0.1) → `check()` vs
  `tests/reference/CPHY_U14_U26.json` (unchanged numbers). `tests/isim_check.py` imports `check` from it (kept).
- Unit tests: remove Excel cases (`test_gnd_decision_015` Excel part, Excel golden pieces in
  `test_thin_layers_014` / `_make_golden_014`, `test_interface_unchanged` 011 tool list); add `REMOVED_017` sets so
  goldens state the removal; new `test_retire_excel_017.py`: removed tools / CLI / prompts / guides / modules absent,
  naming functions equal to the pre-017 behaviour (cases from golden), no kept module imports a removed one.

### 5. Constitution — proposed wording (user runs `/speckit-constitution`; Claude does not edit it)

| Principle | Proposed text |
|---|---|
| I | "The interface-simulation gates (A content, B settings + `user_approved_gnd`, C merge, D run) and the in-place / merge gates of design tools MUST be enforced by the MCP server, not only by guides." |
| III rationale | "…visible in git diffs; runs are reproducible from `user_settings.json`." |
| V | "`tests/regression.py` (interface-simulation flow, board1 copy) and `tests/pidc_check.py` MUST PASS…"; MAJOR = "breaking workflow / tool interface" |
| IX | "MCP tool names, guides, prompts, the CSV template format and output folders (`Ansys AEDT Copilot/`, `autocut/` for review HTML) MUST NOT change." Rationale: "…they must not have to relearn the tool or redo their settings." |

1.0.0 is a MAJOR release, allowed by IX as it stands.

## Kitchen check

| Item | Answer |
|---|---|
| Utensils removed | `review_layout` |
| Process tools removed | `propose_channels`, `read_channels`, `start_cut_batch`, `job_status`, `get_report`, `merge_to_project` |
| Recipes | `excel-cut` removed; others reference no removed tool (checked) |
| Gates | Excel gates removed with their tools; isim / design gates unchanged |
| Catalog + contract | catalog entries removed; `specs/010-*/contracts/legacy-tools.md` marked "removed in 1.0.0" for these |

## Technical Context

| Item | Value |
|---|---|
| New | `cut_board/naming.py`, `tests/unit/test_retire_excel_017.py` |
| AEDT (board1 copies) | new `tests/regression.py` PASS (same reference), `tests/isim_check.py` PASS, `tests/design_check.py` / `tests/kitchen_check.py` if they used removed tools (checked in tasks) |

## Constitution Check (2.0.0, amended by the user with the §5 wording, d3d3fd3)

| Principle | Check | Status |
|---|---|---|
| I | gates of removed tools go with them; others unchanged | PASS (wording amendment proposed) |
| II | board copies only | PASS |
| III | template stays the source; 2 batch rows removed | PASS |
| V | regression.py kept (isim-based), pidc_check unchanged | PASS (wording amendment proposed) |
| IX | interface change → MAJOR 1.0.0 + CHANGELOG migration note | PASS |
| X | catalog = server tools | PASS |
