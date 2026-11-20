# Verify changes (033) — every intended result change, per channel (before 2.10.0 → after 2.11.0)

All runs on COPIES in the session scratchpad (test1 `BOARDA_PN00000000-A_01_EDB_20260915`, board1 `simulation`), layout
snapshot. "Before" = 2.10.0 code (git archive of 468bb54) on the same copy; "after" = 033 code. Counts = review items
(findings) by check and suggested severity.

## SERLINK (test1 copy) — `U14-U15:SERLINK_RAP*_L[01]*; U14-J8:SERLINK_M2M_AC_TX_L[23]*; U14-U227:SERLINK_M2M_AC_RX_L[23]_RDV*`

| Channel | Check | Before | After | Why |
|---|---|---|---|---|
| SERLINK_U14_U15 | Via count (MEDIUM) | 8 | 0 | rule removed (FR-011); via counts are in the cross-section |
| SERLINK_U14_U15 | Pair gap (MEDIUM) | 2 | 0 | both splits lie inside length-matching serpentines of the same pair (FR-010) |
| SERLINK_U14_U15 | Serpentine (MEDIUM) | – | 6 | new rule: all A > 3W (A 0.310–0.571 mm vs 3W 0.294–0.297 mm); G / c / 90° OK |
| SERLINK_U14_J8 | Via count (MEDIUM) | 4 | 0 | rule removed |
| SERLINK_U14_J8 | Serpentine (MEDIUM) | – | 2 | new rule, A > 3W |
| SERLINK_U14_U227 | Pair gap (MEDIUM) | 1 | 1 | real split (not in a serpentine) |
| SERLINK_U14_U227 | Serpentine (MEDIUM) | – | 2 | new rule, A > 3W |
| all | other checks (Near plane edge 2 / 0 / 1, Via stub 0 / 4 / 0, INFO Ref plane change 32 / 12 / 8, via clearance 5 / 3 / 1, No stackup table 1 each) | = | = | unchanged |

Totals: **Serpentine 10, Pair gap 1, Via count 0** = mock numbers (SC-002, no ±1 needed). Serpentine measures identical
to the mock (e.g. DEVA2DEVB_L0_P: A 0.571 mm, G 0.310 mm, c 0.141 mm). Routing boxes: 8 (4 / 2 / 2), cross-section
lines and length tables identical to the mock text (e.g. TX_L2: Vias 3 · Backdrilled 0 · With stub 1 (J8 through-hole
pin), P 96.36 = 85.72 L3 + 10.64 L5).

## PCIe (test1 copy) — `PCIE_U14_J25` (`tests/pcie_check.py`, reference updated deliberately)

| Channel | Check | Before | After | Why |
|---|---|---|---|---|
| PCIE_U14_J25 | Via count (MEDIUM) | 4 | 0 | rule removed |
| PCIE_U14_J25 | Serpentine (MEDIUM) | – | 2 | HSA2HSB_L0_P / L1_P on Layer 3: A 0.363 / 0.370 mm > 3W 0.294 mm (checked in the picture: real serpentines on a diagonal pair) |
| PCIE_U14_J25 | Pair gap (MEDIUM) | 1 | 1 | not in a serpentine |
| PCIE_U14_J25 | items HIGH / MEDIUM / INFO | 5 / 16 / 45 | 5 / 14 / 45 | −4 via count, +2 serpentine |
| PCIE_U14_J25 | points HIGH / MEDIUM | 5 / 13 | 5 / 11 | 4 via-count points gone, 2 serpentine points |
| PCIE_U14_J25 | gate verdict | STOP (5 HIGH) | STOP (5 HIGH) | unchanged (pair skew 2 + loss of reference 3) |

## board1 (copy) — `U14-U26:CPHY_B02DEVA_*; U21-J25:CPHY_LC2HSB_*`

| Channel | Before | After | Why |
|---|---|---|---|
| CPHY_U14_U26 | Near plane edge 1, INFO 25 | identical | trios: no serpentine / pair gap; no via-count finding before |
| CPHY_U21_J25 | Ref plane change HIGH 2, Nearest GND via 2, Via stub 9, Near plane edge 1, INFO 17 | identical | |

## HTML form (all boards) — intended

Header 3 lines, one tab per connection, OK / NOT OK only, no Reference data, Issue / Recommendation from the steering,
pink dashed fault marks, routing boxes in 2.1 (golden `tests/unit/golden/post033_report.html` replaces the 2.6.0 HTML
golden; the 2.6.0 explain data golden is unchanged).

## Success criteria

| SC | Check | Result |
|---|---|---|
| SC-001 | SERLINK HTML: 3 tabs; HIGH / MEDIUM / INFO / "Reference data" in visible text | 3 tabs; 0 / 0 / 0 / 0 — PASS |
| SC-002 | SERLINK Serpentine 10, Pair gap 1, Via count 0 | 10 / 1 / 0 — PASS |
| SC-003 | every pair has a box; length table = review routing lengths (± 0.001 mm) | SERLINK 8 boxes / 16 members, PCIe 4 / 8, board1 7 / 21 (trios); 0 differences — PASS |
| SC-004 | HTML on the snapshot ≤ 2 × 2.10.0 | SERLINK CLI (measure + HTML, snapshot reused) 15 s → 16 s; board1 HTML on snapshot 5.6 s (2.10.0 ≈ 6 s) — PASS |
| SC-005 | user finds NOT OK items < 30 s | user review pending (user asleep) |

## Browser check (built-in browser, served over localhost)

1366 px and 1920 px: no horizontal page scroll (scrollWidth 1351 / 1905); tabs switch; boxes collapse / expand; zoom
buttons on every top view (8 on SERLINK). Compared side by side with `autocut/mock/SERLINK_short_mock.html`: same
layout; difference fixed: h2 underline added (mock had it).

## AEDT scripts (copies)

| Script | Copy | Result | Time | Note |
|---|---|---|---|---|
| `tests/pcie_check.py` | test1 | FAIL (first run: only the review counts, as intended) → reference updated → PASS | 338 s / 270 s | items 5 / 14 / 45, points 5 / 11; cut, ports 16, caps shorted, J25 GND pins 64 → 32 unchanged |
| `tests/review_check.py` | board1 | PASS | 715 s | live = snapshot = HTML findings / points / rows; golden pre023 equal; live HTML 268 s, snapshot HTML 5.6 s |
| `tests/regression.py` | board1 | PASS | 452 s | 24 ports, 126 GND vias, planes 901–923 mm², pin shift 0.21 mm, arc 30 (2.1.0 reference unchanged) |
| `tests/isim_check.py` | board1 | PASS | 942 s | U21_J25 18 ports (references unchanged) |
| `sc003.py` (scratch) | test1 SERLINK / PCIe, board1 | PASS | 8–65 s | SC-001 / SC-003 numbers above |

Final SERLINK HTML (copy): `C:\Users\user1\AppData\Local\Temp\claude\291370f77bea5e72\b8e6ff88-74a7-440b-bef7-c0e2a87aa729\scratchpad\tA\autocut\layout_review_20261112_023236.html`.

## 2.11.1 (user review R1–R3) — before 2.11.0 → after 2.11.1, copies

| Channel | Serpentine (net, layer) | 2.11.0 | 2.11.1 | Why |
|---|---|---|---|---|
| SERLINK_U14_U15 | DEVA2DEVB_L0_P, Layer 5 (picture 1) | 3 bumps, A 0.571 mm | 2 bumps, A 0.425 mm | R2: the P / N split toward the U14 pins was the 3rd "bump"; now a fan-out (still NOT OK: 0.425 > 3W 0.297) |
| SERLINK (other 9) | DEVA2DEVB_L0_P* 0.310, L1_P 0.475, L1_P* 0.375, DEVB2DEVA_L0_P* 0.313, L1_P* 0.375, TX_L2_N* 0.318, TX_L3_N* 0.363, RX_L2_RDV_N 0.389, RX_L3_RDV_N 0.398 | = | = | real serpentines (checked in the pictures) |
| PCIE_U14_J25 | HSA2HSB_L0_P* 0.363, L1_P* 0.370 | = | = | real serpentines |

Counts unchanged: SERLINK Serpentine 10 (6 / 2 / 2), Pair gap 1, Via count 0; PCIe items 5 / 14 / 45, points 5 / 11
(`tests/pcie_check.py` reference unchanged). Only the A value of one serpentine changed.

Rejected first try (recorded, decided by agent): "far run touching the pin / via zone OR a path end = fan-out" removed
5 real serpentines (SERLINK L1_P ×2, DEVB2DEVA_L1_P*, TX_L3_N*, PCIe L1_P*: 2-bump serpentines with one bump within
1 mm of a via or at a primitive joint; PCIe L1_P checked in the 2.11.0 picture = 2 clear bumps) and brought back a pair
gap. Final rule: fan-out = far run next to the pin / via zone that stays far from the partner until the path end
(never comes back). Path ends alone are segment joints, not pins.

Pictures (12 serpentines, built-in browser): thin arrows, small heads, labels with white halo and no overlap; A from the
base-line centre to the bump-top centre, G edge to edge of the two parallel legs (pair chosen away from the A arrow),
c with extension lines to the chamfer ends, W across the partner trace. R3: refdes with placement layer in top view and
cross-section (e.g. "U14 (Top)", "C180 (Top)", "J8 (Bottom)", "J25 (Bottom)").

SERLINK HTML 2.11.1 (snapshot, CLI measure + HTML 19 s): `D:\work\project\tool\ansys_aedt_copilot\autocut\review_033\SERLINK_2.11.1.html`.

R4 / R5 (cross-section via labels, 2.11.1): every via has a label under its column from the board data (via rows):
type (Through / Blind a–b / Buried a–b / Micro a–b = one dielectric / Stacked xN a–b), "backdrilled" when drilled, size
`<pad>D<hole>` mil (padstack of the board, same `size` as the via table, works on the snapshot); "TH pin" for a
through-hole connector pin. SERLINK TX_L2: "Blind Top–L5 18D6", "Blind Top–L5 18D6", "Blind Top–L3 18D10", "TH pin".
Legend line under the cross-section legend. Counts unchanged.

## 2.11.2 (user review R6–R10) — copies

| Check | Result |
|---|---|
| Unit tests | 563 PASS (new: overview circle / no numbers, Detail frame, dimension tips = measured A / W / c / G, 2 extension lines + 2 arrow heads for A / c, W outside arrows, dash-dot centre line; unit switch default mil, localStorage in try/catch, no bare `<n> mm` text outside switchable elements, rounding mil 1 / µm 0 / mm 3). Golden `post033_report.html` regenerated on purpose. |
| SERLINK, test1 copy | Item counts per check and serpentine A / G / W identical to 2.11.1 (SERLINK 10 serpentines, Pair gap 1). HTML: `autocut/review_033/SERLINK_2.11.2.html` (git-ignored). |
| Browser | 1366 / 1920 px: no horizontal scroll; mil / µm / mm switch changes 277 lengths (serpentine, cross-section, length table + header, Box, Location, Issue / Recommendation); choice survives reload; 0 bare mm lengths left. All 10 serpentine pictures looked at. |
| Decisions (agent) | Overview window ≥ 3 mm so the pair context is visible and Detail is ~x2 (SERLINK bumps are only ~0.5 mm wide; the demo's x5 assumed a long straight run). G drawn on the minimum-gap leg pair closest to the measured bump (may be inside the bump). c drawn on the chamfer on the side opposite the A dimension, nearest the bump top. Coordinates (Location, `(x, y) mm` in text) switch units too. |

## 2.11.3 (R11, 2026-11-14)

| Check | Result |
|---|---|
| Unit tests | 564 PASS (new `TestDimensionLabels2113`: 5 bump shapes x 2 directions, W / A / G / c label boxes disjoint) |
| SERLINK, test1 copy (with the FAB stackup table) | counts identical to the run before the fix: U14_U15 16 MEDIUM / 37 INFO, U14_J8 6 / 15, U14_U227 4 / 9; serpentine A / G / W unchanged |
| Browser (real font metrics) | 2.11.2 HTML: 4 pictures with W over c (mm); 2.11.3: 10 pictures x mil / µm / mm, 0 overlaps, 0 values outside the frame. HTML: `autocut/review_033/SERLINK_2.11.3.html` (git-ignored) |

## 2.11.4 (R12, 2026-11-14)

| Check | Result |
|---|---|
| Unit tests | 568 PASS (new `TestVectorCopper2114`: shape clipped with hole, one even-odd path per panel, other-net copper minus GND, grid fallback) |
| SERLINK, test1 copy, snapshot | counts unchanged (U14_U15 16 / 37, U14_J8 6 / 15, U14_U227 4 / 9); 0 grid cells (was 2194), 28 vector paths; HTML 650 → 413 KB |
| SERLINK U14_U15, live EDB (`snapshot=off`) | counts unchanged (16 / 37); 0 grid cells, 20 vector paths (live polygon without arcs) |
| board1 copy, snapshot | U14_U26 0 / 1 / 25, U21_J25 2 / 10 / 17 (U21_J25 = previous record); 0 grid cells (was 3328), 43 vector paths; HTML 875 → 573 KB |
| Browser | panels sharp, arcs smooth (SERLINK snapshot + live, board1). Demo: `autocut/review_033/demo_vector_ref.html` |
