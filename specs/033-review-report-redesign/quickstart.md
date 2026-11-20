# Quickstart (033)

1. Unit: `.venv\Scripts\python -m unittest discover -s tests/unit -t .` → all PASS.
2. SERLINK (copy of test1 in the scratchpad):
   `.venv\Scripts\python -m aedt_copilot review-measure --board <copy>.aedb --channels "U14-U15:SERLINK_RAP*_L[01]*; U14-J8:SERLINK_M2M_AC_TX_L[23]*; U14-U227:SERLINK_M2M_AC_RX_L[23]_RDV*" --html`
   → 3 tabs; Serpentine 10, Pair gap 1, Via count 0; no HIGH / MEDIUM / INFO / Reference data text.
3. AEDT scripts on copies: `tests/review_check.py`, `tests/pcie_check.py`, `tests/regression.py`, `tests/isim_check.py`.
4. Open the HTML in a browser at 1366 / 1920 px next to `autocut/mock/SERLINK_short_mock.html`.
