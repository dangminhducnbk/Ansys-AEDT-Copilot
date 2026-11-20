# Tasks: One file per layout review rule (031)

- [X] T001 `aedt_copilot/review_checks/_rules.py` (folders, parse, rules, get, text, report, personal enable / load)
- [X] T002 `review_rules/*.md` steering for the 14 rules + `_template.md` (text moved from guide H4 / H5 / 2d and from the code's Why / Fix, exact report sentences)
- [X] T003 Split code: `sov.py`, `ref_other_net.py`, `loss_of_reference.py`, `ref_plane_change.py`, `via_stub.py`, `nearest_gnd_via.py` (shared cached computations); remove `reference.py`, `vias.py`; all rule modules build REPORT from the steering
- [X] T004 `review_checks/__init__.py` checks() team + enabled personal code, select() aliases; `cut_board/review.py` BUILTIN_CHECKS
- [X] T005 MCP tool `review_rules` + CLI `review-rules` + catalog entry + contract; goldens
- [X] T006 Guide `review_measure`: process only + generated rule list; developer section (add a rule = steering + code)
- [X] T007 `tests/unit/test_review_rules_031.py`; existing tests adapted (names); golden pre028 identical; full suite; `graphify update .`
- [X] T008 AEDT copies: board1 review_check + HTML byte compare vs 2.8.0, regression, isim_check; test1 pcie_check
- [X] T009 Converge; release 2.9.0

## Verify (2026-11-11, copies, one after another, no AEDT GUI)

| Check | Result |
|---|---|
| HTML board1 (2 channels) 2.8.0 vs 031, same copy | identical (1 076 237 bytes, date / version / timing line removed) |
| HTML test1 PCIe 2.8.0 vs 031, same copy | identical (5 670 947 bytes) |
| board1 `review_check.py` | PASS (pre023 golden through the legacy check shape; 27 / 2 and 32 / 13 items / points as 2.8.0) |
| board1 `regression.py`, `isim_check.py` | PASS |
| test1 `pcie_check.py` | PASS (21 / 57 / 25) |
| unit | full suite PASS; golden pre028 identical |

## Converge

- FR-001 one steering + ≤ 1 code file per rule (14 rules); FR-002 Why / Fix / titles / section / limit key from the
  steering (unit test: no Why / Fix text left in code); FR-003 identical results / HTML; FR-004 guide = process +
  generated list (test keeps it current); FR-005 / FR-006 tool `review_rules` get / list; FR-007 personal folder,
  shadowed on clash, code enabled explicitly; FR-008 unit tests; FR-009 030 rules one per file.
- Known effect: 2.8.0 review records are not reused (rule list in the key changed) → measured again once.
- Nothing open.

