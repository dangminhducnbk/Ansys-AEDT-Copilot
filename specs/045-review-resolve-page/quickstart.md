# Quickstart — 045 validation

1. Offline: `.venv\Scripts\python -m unittest discover -s tests/unit -t .` → all PASS (new `test_review_page_045`).
2. Board copy (BOARDA, `D:\data\client_boarda\for_ai_testing`): `.venv\Scripts\python tests/review_page_check.py`
   - new request (review_page) → trace → `isim_layout_review` → `config.html` written, M0p;
   - markers = NOT OK points of review.json, each with its report rows;
   - check before Save → refused (unresolved); save via the service with all resolved → check OK, Q2 line
     "N NOT OK points resolved"; review touched → refused (outdated).
3. Browser (preview pane, 1920×1000 and 1366×768): tabs, lock, Resolve / Resolve all, Settings frame, Save in place,
   Print issue to image, topology with series bodies; no console error.
4. Old flow: `tests/config_flow_check.py` + `tests/regression.py` (board1 copies) PASS.
