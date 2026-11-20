# Tasks — 039 review before config (released with 041 as 5.2.0)

- [x] T001 `request.start`: `review_first: true` in new requests.
- [x] T002 `answers.py`: m0 / q0 / m0x texts, `m0(rows)`, `m0x(rows)`, QUESTIONS += q0, q2 "review updated" note.
- [x] T003 `flow.py`: `review_step`, `review_answer`, `require_review_ok`; guard in config / check / go; check marks
  `review_updated` per channel.
- [x] T004 `api.py` ops `layout_review`, `review_answer`; server tools `isim_layout_review`, `isim_review_answer`
  (gate); catalog entries + contract path.
- [x] T005 [P] `tests/unit/test_review_first_039.py`: M0 / Q0 / M0x, one question per answer, refusals (no
  decision, stopped, changed review), old request unaffected; catalog / golden lists updated.
- [x] T006 Guide `interface_sim` §0, prompt `interface-sim`, server instructions.
- [x] T007 `tests/config_flow_check.py`: Q0 step; run on a board1 copy.
