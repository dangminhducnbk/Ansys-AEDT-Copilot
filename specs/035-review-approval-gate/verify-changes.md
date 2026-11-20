# Verify changes: 035 (3.0.0)

Copies only (session scratchpad `c35/`: board1 → b1–b5, test1 → t1). 2026-11-14.

| Check | Copy | Result | Notes |
|---|---|---|---|
| Unit suite | — | 573 PASS | test_approval_035 (22), 025 tests replaced, goldens: post033 HTML without the gate line (deliberate), 014 golden lists `REMOVED_TOOLS_035` |
| tests/review_gate_check.py --cut | b1 | PASS | GATE A refused before review / before preview; approval stored (report path = review html); U21_J25 2 HIGH → gate `ready` (not blocked), server isim_cut refused before approval, allowed after; status approved → after edb.def touch `approval out of date`, cut refused; review again (measured, 72 s) → `ready` → GATE A with unchanged content re-approves → approved; `review-decide` CLI exit 2; edb.def unchanged |
| tests/regression.py | b2 | PASS | = 2.12.0: 24 ports, 126 GND vias, planes 901–923 mm², pin shift 0.21 mm, arc 30, U26 enlarged 0.16 (+59.2 mm², pin 65) |
| tests/isim_check.py | b3 | PASS | U14_U26 + U21_J25 (2 HIGH, no override needed), 18 ports U21_J25, recut part PASS |
| tests/pcie_check.py | t1 | PASS | review HIGH 7 / MEDIUM 11 / INFO 45 (= 2.12.0), cut after approval, 16 ports, series caps shorted, J25 GND pins 64 → 32 |
| tests/preview_check.py | b4 | PASS | `image` = final cut region (legend Signal / Cut region / GND pin / GND via), zoom + detail kept; preview = cut extent |
| tests/review_check.py | b5 | PASS | live = snapshot = golden; isim review html written, gate ready, no verdict text in the report |

Before → after (behaviour):

| Item | 2.12.0 | 3.0.0 |
|---|---|---|
| Review HTML in interface simulation | only on request | always (`html` in result) |
| Interface with HIGH findings | STOP; override / per-point decisions needed | `ready`; user's one approval at GATE A |
| GATE A | content go | content + cut area + review go; refused without review / report / preview |
| Cut | review not STOP | approval of the current review recorded |
| Tools | +isim_review_decide, isim_review_override, design_review_decide | removed (55 tools) |
| Preview image | base dashed + added green + other nets hatched | final region only (`cut_detail.png` keeps the old drawing) |
| After cut | settings asked in chat (test chat) | `next` = settings form, guide makes the form mandatory |
| Reused review time (board1 U21_J25) | ~0.4 s | ~11 s (HTML re-rendered on the snapshot) |
