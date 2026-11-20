# Quickstart / validation: 035

Copies only (board1 → b*, test1 → t*). Never the user's files.

1. Unit: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` → all PASS (incl. test_approval_035).
2. board1 copy, CPHY_U14_U26: `tests/regression.py <copy>.aedt`
   - after trace: review → `html` exists; status `report ready`; `isim_cut` refused (no approval)
   - GATE A without preview refused; preview → `image` final region (no dashed base, legend "Cut region")
   - GATE A → `review.approval` in user_settings; cut OK; results = 2.12.0 (24 ports, 126 GND vias, planes
     901–923 mm², pin shift 0.21)
   - `isim_cut` / `isim_check_ends` results have `next` naming the settings form
3. test1 copy PCIe (7 HIGH): `tests/pcie_check.py` → approval without override; cut OK; numbers = 2.12.0 (16 ports …).
4. `tests/review_gate_check.py` (rewritten approval check): touch edb.def after approval → status `approval out of
   date` / cut refused; review again → `report ready`.
5. `tests/isim_check.py`, `tests/preview_check.py`, `tests/review_check.py` PASS (no override step).
6. Server import: tool count = 2.12.0 count − 3; `isim_review_decide`, `isim_review_override`, `design_review_decide` absent.
7. Guide read-through: interface_sim Phase 1 = trace → review → preview → 3-part answer → one go; no STOP text in
   guides / server instructions / about (grep `STOP`, `override`, `review_decide` → 0 in user-facing text).
