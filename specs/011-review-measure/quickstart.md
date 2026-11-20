# Quickstart: review measure

1. Offline: unit suite PASS (`test_review_checks`, kitchen tests with the 3 new tools).
2. Board1 copy: `tests/review_check.py <board copy .aedb> <workspace copy .aedt>`:
   - old `review.review()` (HTML) with captured channel data vs `measure` all checks: identical findings (check, net,
     layer, value, severity, x, y), via rows, lengths for CPHY_U14_U26 and CPHY_U21_J25;
   - `trace_stubs` alone: same subset, time < half of all checks;
   - isim request → confirm → `isim_review` → decide (dismiss one) → `user_settings.json` key `review`.
3. `tests/regression.py` PASS (Excel flow unchanged).
