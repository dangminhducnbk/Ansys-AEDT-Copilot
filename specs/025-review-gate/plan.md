# Implementation Plan: Layout review gate (mandatory review + stop before cut)

**Branch**: `claude/025-review-gate-ca985b` (worktree) | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md) |
Research: [research.md](research.md) | Data: [data-model.md](data-model.md) | Contracts: [contracts/](contracts/) |
Validation: [quickstart.md](quickstart.md)

## Summary

Review measuring stays exactly as 2.2.0 (`review_checks.measure_channels`, snapshot). New on top:

1. A pure **verdict** per channel (STOP if any final-severity HIGH point or an incomplete review, else CONTINUE).
2. Every review (standalone `design_review` and interface `isim_review`) writes a **review record** under
   `<board dir>/Ansys AEDT Copilot/reviews/<board stem>/` with a **match key** (board key from 023, cell, ends, nets,
   checks, review thresholds). Interface review **reuses** a matching record instead of measuring.
3. `isim_review` runs right after `isim_trace` (step `started`, on the proposal) — Phase 1.5, mandatory.
4. A **review gate** (pure function over state + review.json + user_settings) is checked by the server AND the
   package in Gate A (`isim_confirm_content` / `content.confirm`) and cut (`isim_cut` / `cut.run`): refuses when no
   review, out of date (ends / nets / board), STOP without the engineer's decision.
5. Engineer's decision on a STOP: per-point decisions (existing `isim_review_decide`, now bound to the review) or a new
   gated tool `isim_review_override(reason, user_approved_review_override=true)`. Standalone decisions: new tool
   `design_review_decide` writes them into the record (FR-010).

## Technical Context

| Item | Value |
|---|---|
| Language | Python 3.12 (repo `.venv`); no new dependency |
| Storage | JSON: `reviews/<stem>/review_<time>.json` (record), `<iface>/review.json` (gate review), `user_settings.json` keys `review` (+ `override`) |
| Testing | `unittest` offline: `tests/unit/test_review_gate_025.py` (verdict, match, gate matrix, store, server refusals with fake files); AEDT on copies: `tests/review_gate_check.py` (new), `tests/regression.py`, `tests/isim_check.py`, `tests/pcie_check.py` adapted |
| Platform | Windows, AEDT 2026 R1 non-graphical EDB (read only for review) |
| Performance | reuse of a valid record < 5 s (no EDB open; stat of `edb.def` only) |
| Constraints | measured numbers / points / severities identical to 2.2.0 golden; board never written; no GUI |
| Depends on | `main` with 021 + 024 merged before implement (024 changes request / folder id code used by interface_sim) |

## Design

### 1. `aedt_copilot/review_checks/_verdict.py` (new, pure)

| Function | Does |
|---|---|
| `channel_verdict(ch, decisions=None)` | final severity per point = decision `severity_final` (if decision for that point; `dismissed` → not counted) else `severity_suggested`; incomplete = `ch.error` or any `checks[*].error`; → `{verdict: CONTINUE/STOP, reason: high/incomplete/none, counts{HIGH,MEDIUM,INFO}, high_points[{id, issues, net, layer, x, y}], failed_checks[], incomplete}` |
| `thresholds(defaults_review)` | template `review.*` without `use_snapshot` (sorted dict) |
| `match_key(board_key, cell, comp_a, comp_b, nets, checks, thresholds)` | normalised dict: aedb (normcase abs), def_size, def_mtime_ns, cell, ends (sorted pair), nets (sorted unique), checks (sorted), thresholds |
| `same(a, b)` / `diff(a, b)` | equality / list of differing fields (`board_changed`, `ends`, `nets`, `checks`, `thresholds`, `cell`) for messages |

### 2. `aedt_copilot/review_checks/_store.py` (new, file IO only)

| Function | Does |
|---|---|
| `folder(aedb)` | `<board dir>/Ansys AEDT Copilot/reviews/<stem>` |
| `save(out, requested_cell, source)` | writes `review_<YYYYmmdd_HHMMSS_ffffff>.json` = measure output + per channel `verdict` + `key`; returns path. `source` = `standalone` / `isim:<request>/<iface>` |
| `find(aedb, key)` | newest record + channel whose key `same` → `(path, channel)` or `None`; unreadable files skipped |
| `decide(path, channel, decisions)` | validates like `isim_review_decide` (point ids, decision, severity change needs reason) → stores `decisions` in the channel, recomputes `verdict_final`; returns channel summary |

`measure_report` (CLI `review-measure` / `design_review`) calls `store.save` after measuring and adds `review_file`
+ `verdict` per channel (and `verdict_md`). Board key taken BEFORE measuring (`layout_snapshot.key.board_key`).

### 3. `aedt_copilot/interface_sim/review.py` (changed) + gate

| Function | Change |
|---|---|
| `run(request_id, name, checks, html, version, snapshot, reuse=True)` | allowed at EVERY step incl. `started` (needs `proposal` or `content`); spec = content if agreed else proposal (`basis`). All checks + `reuse` → `store.find` match → copy (`reused_from`, measured_at of the record) else measure + `store.save`. Writes `<iface>/review.json` with `basis`, `key`, `verdict`, `record`. Partial checks → `<iface>/review_partial.json` (never the gate file). Reused record decisions → `user_settings.review.decisions` (bound to the record's `measured_at`). Returns `verdict`, `gate` (= `gate_status`), `stop_md` |
| `decide(...)` | allowed at every step; decisions stored with the review's `measured_at`; returns new `verdict` + `gate` |
| `override(request_id, name, reason)` (new) | needs review.json with verdict STOP; reason non-empty → `user_settings[name].review.override = {measured_at, reason, time, verdict, high_points, failed_checks}`; returns `gate` |
| `gate_status(request_id, name, content=None)` (new) | → `{ok, status, message, verdict, high_points, failed_checks, diffs}`; status ∈ `not_reviewed`, `out_of_date`, `stop`, `continue`, `decided` (all HIGH resolved by decisions), `override`. Out of date = review ends / nets ≠ content (or proposal when content None) or board key ≠ now or checks / thresholds ≠ now. Decisions / override count only when their `measured_at` = review.json `measured_at` |
| `require(request_id, name, content=None)` (new) | `gate_status` not ok → `CopilotInputError("review", <message>, status)` |

Gate call sites:

| Where | When |
|---|---|
| `content.confirm` | after `validate_content`, unless step ≠ `started` and content unchanged (FR-013) → `review.require(rid, name, c)` |
| `cut.run` | step `content_agreed` → `review.require(rid, name, st.content)` |
| server `isim_confirm_content`, `isim_cut` | after the existing flag / step checks: `review.gate_status` → `_refuse(message)` + `review_gate` block (server enforces, Principle I) |

`request.status` rows gain `review` (`not reviewed` / `CONTINUE` / `STOP (n HIGH)` / `STOP (incomplete)` /
`decided` / `override` / `out of date`) and a `Review` column in `table_md`.

Recut: `recut.start` result gains `previous_review` (verdict + override of the source run, if any) — shown only, never
applied (FR-012, Q5).

### 4. Interface (MCP / CLI)

| Layer | Change |
|---|---|
| `isim_review` | description: mandatory step 1.5 right after `isim_trace`; reuse; verdict / gate; params unchanged + `reuse: bool = True` |
| `isim_review_decide` | description: any step, verdict recomputed |
| `isim_review_override` (NEW) | `(request_id, name, reason, user_approved_review_override=False)`; flag false → refuse; empty reason → refuse |
| `isim_confirm_content`, `isim_cut` | refuse on gate (message lists HIGH points / diffs and the 3 ways forward) |
| `design_review` | description: stores a review record + verdict per channel |
| `design_review_decide` (NEW) | `(review_file, channel, decisions)`; read-level (writes only the tool's own record) |
| CLI | `isim --op=review_override`, `review-measure` unchanged flags (adds output), new `review-decide --file= --channel= --decisions-file=` |
| Server instructions | REVIEW line: mandatory step after `isim_trace`, STOP on HIGH |

### 5. Guides / workflows / prompts

| File | Change |
|---|---|
| `guides/interface_sim.md` | Phases table: Phase 1 = trace → REVIEW (mandatory) → content / preview → Gate A; new "Phase 1.5 — Mandatory layout review" replaces 1.6; STOP handling (show HIGH points; ways: fix board + `isim_review` again; per-point decisions with reason; `isim_review_override` only after the user's explicit "vẫn cut" + reason); other interfaces continue; Phase R step: review again / reuse, old override shown not reused |
| `guides/review_measure.md` | verdict rule, record file + reuse rule, `design_review_decide`, step 5 updated |
| `workflows/layout-review.md` | steps `design_review` → (`design_review_decide`) ; ends with verdict per channel + record path |
| `workflows/` interface workflows (if they list steps) | add `isim_review` after `isim_trace` |
| `prompts/interface-sim.md` | one line: review mandatory before Gate A |

### 6. Tool catalog check (Principle X)

| Tool | Status | Kind / safety | Gate | Contract |
|---|---|---|---|---|
| `isim_review_override` | NEW | process / read | `user_approved_review_override` | `specs/025-review-gate/contracts/mcp-tools.md` |
| `design_review_decide` | NEW | tool / read (writes its own record only) | — | same |
| `isim_review`, `isim_review_decide`, `isim_confirm_content`, `isim_cut`, `design_review` | CHANGED behaviour / text | unchanged | unchanged | 025 contract (catalog `CONTRACTS` points the 3 review tools to 025) |

Workflows affected: `layout-review` (new step), interface-simulation team workflows listing `isim_*` steps (review step
after trace). Server tool count 54 → 56 (`test_rename_020`, `test_thin_layers_014` ADDED lists, catalog tests).

## Constitution Check

| Principle | Check |
|---|---|
| I Gates in code | review gate enforced by server (`_refuse`) AND package; override needs explicit flag + reason; flags only after the user's words (guide) — PASS |
| II Data safety | board read only; records / review.json new files; old review.json renamed on reset (existing OUTPUTS) — PASS |
| III Defaults | no new template row; thresholds read from template via `config.defaults()` and passed in — PASS |
| IV Guides | interface_sim / review_measure / workflow updated — PASS |
| V Regression | regression.py / isim_check.py adapted deliberately (review step added; U21_J25 path uses override) — PASS before merge |
| VI Encoding | UTF-8 writes via existing `wjson` — PASS |
| VII Contracts | contracts/review-gate.md + mcp-tools.md; `CopilotInputError` at entry — PASS |
| VIII Thin layers | logic in `review_checks/_verdict.py`, `store.py`, `interface_sim/review.py`; server only calls `gate_status` — PASS |
| IX Stable interface | no tool renamed / removed; 2 tools added (MINOR); Gate A now needs a review = behaviour change of a process → MINOR 2.3.0 with CHANGELOG note (owner decides version at release) — PASS (justified: user rule) |
| X Catalog | 2 new tools with entry + contract + gate test; workflows updated — PASS |

## Project Structure (touched)

```
aedt_copilot/review_checks/_verdict.py   NEW pure
aedt_copilot/review_checks/_store.py     NEW
aedt_copilot/review_checks/__init__.py  measure_report -> store.save
aedt_copilot/interface_sim/review.py    run any step / reuse / override / gate_status / require
aedt_copilot/interface_sim/content.py   confirm -> review.require
aedt_copilot/interface_sim/cut.py       run -> review.require
aedt_copilot/interface_sim/request.py   status review column
aedt_copilot/interface_sim/recut.py     previous_review (display)
aedt_copilot/interface_sim/api.py       op review_override
aedt_copilot/cli/{parser,commands}.py   review-decide
aedt_copilot/catalog/tools.py           2 entries, contracts
mcp_server/server.py                    2 tools, gate refusals, texts
guides/, workflows/, prompts/           §5
tests/unit/test_review_gate_025.py      NEW; golden lists in 014 / 020 tests
tests/review_gate_check.py              NEW AEDT check; regression.py / isim_check.py / pcie_check.py adapted
```

## Complexity Tracking

None. Two new tools are needed because the override must be a gated single operation (a gate on
`isim_review_decide` would refuse ordinary point decisions) and standalone decisions have no request.
