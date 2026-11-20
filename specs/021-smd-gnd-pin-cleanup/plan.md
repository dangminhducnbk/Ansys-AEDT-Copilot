# Implementation Plan: GND pin cleanup on SMD / connector ends

**Branch**: `main` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md) | **Contract**: [contracts/gnd-pin-cleanup.md](contracts/gnd-pin-cleanup.md)

## Summary

One pure selector decides which own GND pins of an end stay: pins within `cleanup.smd_gnd_pin_keep_dist_mm`
(1.6 mm, centre to centre) of any signal pin, plus each signal pin's nearest GND pin (warning when it is farther),
plus protected pins (022 end GND pin / pad, 019 kept pads). `rebuild_smd_component` applies it to own GND pins before
the component is rebuilt (removed pins are deleted, the new component holds signal + kept GND pins; FR-005 check
unchanged). Plate / existing-copper references (015) are never pruned (they are the GND set chosen by the user).
`design_cleanup` applies the same selector to non-BGA ends. BGA / through-hole ends keep their rule.

### 1. `cut_board/gnd_pins.py` (new, pure)

| Function | What |
|---|---|
| `select(sig_xy, gnd {name: (x, y)}, keep_m, protect=())` | → `{keep: [names], removed: [names], nearest: {sig_i: name}, far: [sig_i…]}`: keep = within keep_m of ≥ 1 signal pin ∪ nearest per signal pin ∪ protect; no signal pin → keep all + `no_signal` |
| `report(rd, before, sel, keep_mm)` | `{refdes, gnd_pins_before, gnd_pins_after, removed, keep_dist_mm, warnings[]}` (warnings: signal pin without GND within keep distance → nearest kept; no signal pin → nothing pruned) |
| `protected_names(stage1, rd)` | 022 `end_gnd.ends[rd]` `gnd_pin_inside` + `gnd_pins_gained` pins, 019 `kept_pads[rd]` |

### 2. `cut_board/cutter.py`

- `rebuild_smd_component(..., protect_names=())`: own `gnd_pins` (not plate / copper) → `gnd_pins.select` with signal
  pin positions from the plan (original centres); removed pins deleted before `detach_pins`; returned `gnd_ref` gains
  `gnd_pin_cleanup` = report. Plate / copper branches unchanged.
- `apply_stage`: passes `protect_names` from stage1; `metrics["gnd_pin_cleanup"]` = list of reports; log line per end.
- `cleanup_gnd(..., smd_ends=(), smd_protect=None)`: new optional block after the BGA block: for `smd_ends` prune with
  the same selector (`p.delete()`), used by `design_cleanup` only (isim prunes in the rebuild). Default `()` →
  identical behaviour.

### 3. Template + history (Principle III, Q1 / Q3)

- `templates/autocut_template.csv`: `cleanup.smd_gnd_pin_keep_dist_mm,SMD / connector GND pin keep distance,mm,num,
  channel,no,1.6,…` (cut group, Gate B).
- `interface_sim/defaults_history.py`: `HISTORY["cleanup.smd_gnd_pin_keep_dist_mm"] = [((2, 3, 0), 1.6)]` → older runs:
  NOT_YET → current rule applies, row source "team default (new)" (re-cut diff shows it).

### 4. Interface simulation / design tools / guide

- `interface_sim/apply.py` self-check: per end `gnd_pin_cleanup` (before → after, keep distance, warnings) in the
  result + `self_check.gnd_pin_cleanup`; any signal pin left with no GND pin within the keep distance and no nearest
  kept → mismatch (cannot happen by construction, checked).
- `design_tools/cleanup.py`: non-BGA ends → `smd_ends`, protect from stage1.json; report `gnd_pins_removed`.
- `guides/interface_sim.md` verification items 4 / 4c + N5; `guides/design_tools.md` one line.
- `tests/pcie_check.py`: J25 GND pins after < 64, every J25 signal pin has a GND pin ≤ keep distance, report printed.

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | none (outputs of `isim_apply` / `design_cleanup` gain `gnd_pin_cleanup`) |
| Safety level | unchanged |
| Approval flag | unchanged |
| Catalog entry + contract | no catalog change; contract `contracts/gnd-pin-cleanup.md` |
| Registration | n/a |
| Workflows affected | none |
| New fixed-process tool | none |

## Technical Context

| Item | Value |
|---|---|
| Changed | `cut_board/{gnd_pins (new), cutter}.py`, `interface_sim/{apply, defaults_history}.py`, `design_tools/cleanup.py`, template, guides, `tests/pcie_check.py` |
| Untouched | request / folder-id code (feature 024 runs in parallel), extent code (022) |
| Tests | `tests/unit/test_gnd_pins_021.py`: selector (near kept, far removed, nearest fallback + warning, protect, no signal), 022 interaction (end GND pin / kept pad / plate / copper never pruned; every signal pin keeps its nearest), rebuild with fake EDB, template + history, design cleanup wiring |
| AEDT (fresh copies, one after another) | test1 `pcie_check.py` (J25 64 → fewer, 16 ports, self-check OK, review unchanged); board1 `regression.py` + `isim_check.py` (references 2.1.0 unchanged) |

## Constitution Check (2.0.1)

| Principle | Check | Status |
|---|---|---|
| I Gates | value shown at Gate B; no new gate | PASS |
| II Data safety | copies only | PASS |
| III Defaults | template row + history entry | PASS |
| IV Guides | interface_sim / design_tools guides | PASS |
| V Regression | board1 references unchanged; test1 PCIe reference updated (J25 count) on purpose | PASS |
| VII Contracts | contract file; pure selector | PASS |
| VIII Package | selector in `cut_board/gnd_pins.py`; isim / design tools only pass data | PASS |
| IX Stable interface | additive outputs; result change only for SMD / connector ends → minor | PASS |
| X Tool catalog | see Tool catalog check | PASS |
