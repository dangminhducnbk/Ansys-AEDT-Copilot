# Implementation Plan: No severity, standard answer, netlist-based schematic check (036)

**Branch**: work on `main` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: `specs/036-no-severity-netlist/spec.md` (6 points agreed in chat 2026-11-14/15; user asleep during plan /
tasks / implement: "Làm xong triển khai luôn đi" — decisions below taken by the agent, recorded in research.md).

## Summary

Review findings carry `status` OK / NOT OK instead of a severity level; every rule decides by its threshold. Counts
are NOT OK numbers per check. The interface flow gets a tool-written channel answer (`answer_md`). Requests accept a
schematic netlist (Altium Protel 2.0, Allegro / Telesis) parsed by code; board vs schematic comparison works on pin
connectivity, so off-page renames, unread pins and swapped 2-pin parts no longer produce questions. Series parts stay
0 Ω silently. MAJOR 4.0.0.

## Technical Context

**Language/Version**: Python 3.12 (repo `.venv`)
**Primary Dependencies**: pyedb 0.85 / pyaedt 1.9 (unchanged), mcp<2
**Storage**: request folder `netlist.json` (new), `review.json`, `user_settings.json` (`review.approval.counts` new
shape), review records (`_store` SCHEMA 4), review HTML in `autocut/`
**Testing**: unit `python -m unittest discover -s tests/unit -t .`; AEDT on copies: `tests/regression.py`,
`tests/isim_check.py`, `tests/review_check.py`, `tests/preview_check.py`, `tests/review_gate_check.py`,
`tests/pcie_check.py` (test1 = BOARDA), new `tests/netlist_check.py` (BOARDA copy + user netlist)
**Target Platform**: Windows 11, AEDT 2026 R1
**Project Type**: Python package + CLI + MCP server (thin layers)
**Performance Goals**: netlist 7.8 MB parsed < 10 s (SC-004); review time unchanged
**Constraints**: cut results identical to 3.0.0 (SC-005); board / netlist never written
**Scale/Scope**: cut_board/review.py + review_report.py, review_checks (all rule modules, _rules, _report, _verdict,
_store, __init__), review_rules/*.md, interface_sim (review, content, schematic, request, cut_preview, new netlist +
answer), server / catalog / CLI docs, guides interface_sim + review_measure, prompt, workflows, tests

## Constitution Check

| Principle | Check |
|---|---|
| I Gates locked in code | PASS. Gates unchanged (GATE A approval of the current review). |
| II User data safety | PASS. Netlist read only; board read only; outputs in the request folder. |
| III Single source of defaults | PASS. Thresholds unchanged (template `review.*`); series 0 Ω default unchanged. |
| IV Usage rules in guides | PASS. interface_sim (answer_md pasted verbatim, netlist in Phase 0), review_measure (OK / NOT OK), rule steering, prompt, workflows. |
| V Regression before release | PASS. All AEDT checks on copies; references updated to NOT OK counts (deliberate), cut numbers unchanged. |
| VI Windows & encoding | PASS. Edit / Write; netlist read with encoding fallback (utf-8 → cp1252). |
| VII Contracts | PASS. contracts/review-status.md, contracts/netlist.md, contracts/answer.md. |
| VIII Thin layers | PASS. Parsing in interface_sim/netlist.py, answer in interface_sim/answer.py; server passes args. |
| IX Stable interface | JUSTIFIED: result fields `severity` / `severity_suggested` / counts HIGH-MEDIUM-INFO / `SEVERITY_RULE` / steering field `severity` replaced → MAJOR 4.0.0 + CHANGELOG. New optional arg `netlist` on `isim_start`; new field `answer_md`. |
| X Catalog | PASS. No tool added / removed; catalog descriptions updated. |

## Tool catalog check

| Item | Answer |
|---|---|
| Tools (MCP) added / changed | changed: `isim_start` (+`netlist`), `isim_review` / `design_review` (status OK / NOT OK, `not_ok` counts), `isim_cut_preview` + `isim_review` (+`answer_md`), `isim_trace` (pin-based `schematic_diffs`, `schematic_info`), `isim_schematic_status` (netlist info), `review_rules` (field `not ok when`) |
| Safety level | unchanged |
| Approval flag | unchanged |
| Catalog entry + contract | tools.py descriptions; contracts in this folder |
| Registration | unchanged |
| Workflows affected | `workflows/interface-sim.md`, `workflows/layout-review.md` (wording) |
| New fixed-process tool | none |

## Design

### D1 Status instead of severity (FR-001..005)
- Finding dict: key `status` = `"NOT OK"` / `"OK"` replaces `severity`. Each rule sets it from its threshold:
  Loss of reference / SOV / Ref to other net / Trace stub / Via stub (> 0) / Nearest GND via (> limit) / pair skew /
  pair gap / coupling / plane edge / serpentine / width / gap beyond tolerance → NOT OK; ref plane change with a GND via
  within the limit, via clearance, "no stackup table / value" → OK (kept as data, not listed).
- `review.points` merges NOT OK findings only; overview marker one colour; sorting by status then check / net
  (`STATUS_ORDER`). Report rows sort by channel / point (no severity order) → row order may change (golden deliberate).
- `review_report.counts` → `{section: {channel: n_not_ok}}`; `danger` / `DANGER` removed.
- `review_checks`: item `status` (was `severity_suggested`); `_verdict.channel_findings` → `{not_ok, by_check,
  failed_checks, incomplete}`; `findings_md` → `**name**: NOT OK n (check a n, check b n)`.
- Rule modules: `TITLE, RULE = X.meta(NAME)`; registry required attrs `NAME, ORDER, TITLE, RULE, run`; steering field
  `not ok when` (old `severity` still read for personal rules). `checks_available` → `{title, rule}`.
- `_store.SCHEMA = 4` (3.0.0 records ignored → gate out of date → measured again).
- interface_sim review / approval: `counts` = `{"NOT OK": n}` + `by_check`; `SEVERITIES` removed.
- Old `review.html` field / HTML unchanged except no severity anywhere (hover titles included).
- pi_dc: out of scope (PASS / WARN / FAIL of current density are not review severities).

### D2 Channel answer (FR-006..008)
- `interface_sim/answer.py` `build(rid, name)`: needs review gate `ready` / `approved` (html exists) and the last
  preview with the current settings key and no errors; else `None` + reason.
- Text (Vietnamese): title `**<name>: vùng cut dự tính (<w> × <h> mm, <area> mm²)**`, picture path line, `ends_lines`,
  `Review: <html path>`, question lines (unresolved real schematic diffs, >2 end candidates), final
  `Đọc review rồi xác nhận cut <name>?`.
- Returned as `answer_md` (+ `answer_image`) by `isim_cut_preview` and `isim_review` when available.
- Guide Phase 1 step 5: send `answer_image`, paste `answer_md` verbatim, nothing else.

### D3 Netlist (FR-009..012)
- `interface_sim/netlist.py`: `parse(path)` → `{format, design, components {rd: {part, value, pins}}, nets {name:
  [[rd, pin]]}, warnings}`; formats detected by content: `PROTEL NETLIST 2.0` / `[` blocks + `(` nets; `$PACKAGES` /
  `$NETS` (Allegro / Telesis; `!`-separated package lines, `,` continuation, quoted names, repeated sections merged).
  Value: Protel `Value` / `Capacitance` / `Resistance` / `Inductance` field, else first value token of PARTTYPE
  (`220nF`, `10k`, `0Ohm`); Telesis third `!` field.
- `request.start(..., netlist=)`: path checked, parsed, saved `<request>/netlist.json`, summary in the start result
  (format, design, counts, warnings).
- `schematic.load_parsed`: netlist.json first (source `netlist`), else schematic.md (source `pdf`).
  `schematic.status` reports `netlist` (path, counts) and `up_to_date` true when a netlist is present (no PDF reading
  needed).
- Design check at trace: ends + series refdes missing from the netlist → share < 50 % → refused
  ("netlist does not match the board"); design name shown in warnings.

### D4 Pin-based comparison (FR-013..016)
- `content.compare(facts, sch, patterns)` → `{diffs, board_only, renamed}`; `diff()` = `compare()["diffs"]`.
- Pin key: 2-pin parts → `(rd, "*")`; others `(rd, pin)`.
- Board net pins B (facts components). Known = pins present anywhere in the schematic. Known empty → `board_only`.
  Schematic nets S containing known pins: one net S whose pins on facts components ⊆ B and known ⊆ S → same net
  (name differs → `renamed`); else `pin_mismatch` with both pin sets.
- `missing_on_board`: PDF source as before; netlist source only for schematic nets matching the trace net patterns.
- `series_value`: numeric compare (SI prefixes, ±1 %); unparsable → skipped.
- Removed kinds: `name_case_or_prefix`, net-level `missing_in_schematic`; component `missing_in_schematic` →
  `board_only`.

### D5 Series parts silent (FR-017)
- No code change in the cut (default 0 Ω already). The answer never mentions them; guide says so.

## Phases

1. D1 severity removal (code + steering + tests) — largest.
2. D3 + D4 netlist + comparison (unit tests with the BOARDA netlist excerpt).
3. D2 answer + guide / prompt / workflows.
4. AEDT checks on copies, references updated; release 4.0.0 locally (no push).
