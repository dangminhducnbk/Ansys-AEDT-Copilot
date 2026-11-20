# Verify changes: 037 (4.1.0)

Copies only (session scratchpad `c37/`: test1 = BOARDA → t1, t2; board1 → b1, b2). 2026-11-15.

| Check | Copy | Result | Notes |
|---|---|---|---|
| Unit suite | — | 598 PASS | new test_review_fixes_037 (8: real dense-chain geometry of `PCIE_HSB2HSA_L0_P` fails on the old walk, last segment into a via-in-pad, BGA skip in / out / margin / non-BGA, template default); golden post033 HTML: only the Routing section text (pair skew line gone) |
| `review-measure --html` U14-J25 PCIE (report item 1–3) | t1 | PASS | 4 / 4 cross-sections reach J25, no "path not traced" note; HSB2HSA pairs Vias 2 (Through 18D8 stub 0.257 + Blind L14 → Bottom 18D10 stub 0, L14 106.6 mm); HSA2HSB pairs now also show the J25 blind via-in-pad (3 → 4 vias); no Pair skew item / word in the HTML; pair gap at (100.59, 79.90) gone, `skipped_in_bga` 1; P / N totals 108.137 / 109.053, 109.039 / 110.283, 108.525 / 111.086, 107.409 / 110.304 mm (= report) |
| tests/pcie_check.py | t2 | PASS | review NOT OK 16 / OK 45 items, 15 points (4.0.0: 21 / 45, 18); 16 ports, caps shorted (cut unchanged) |
| tests/review_check.py | b1, b2 | PASS | board1 unchanged (26 / 1, 31 / 12; CPHY trios: pair gap is for pairs only); pair_skew data = lengths only |

Not re-run: regression.py / isim_check.py / preview_check.py (no cut code changed; board1 review counts proven unchanged by review_check).

Second walk bug found while verifying (not in the report): the J25 end segment of `PCIE_HSB2HSA_L0_P` ended 0.283 mm
from the pin centre (inside the 0.3 mm pin tolerance), so the walk stopped one segment early and lost the blind via in
the pad. Fix: do not stop at a pin while an unused path joined at the current point goes closer to it; look for the via
at the pin centre too.
