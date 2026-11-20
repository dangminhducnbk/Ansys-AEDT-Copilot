# Quickstart: Kitchen model

1. Offline: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` → PASS (catalog ↔ server sync, recipes
   parse / list / save, new utensils with fake EDB).
2. Board1 copies (user OK first): `tests/kitchen_check.py <board1 copy .aedt>`:
   design_trace U14,U26 → design_cutout (new cut) → design_end_check → design_cleanup (on a hand-made / 007 design) →
   design_ports / design_setup (007) → design_check OK → design_merge into a COPY of the workspace (flag set by the
   script) → new design present, backup present; existing references unchanged (`tests/regression.py`).
3. New chat: "bạn làm được gì" → recipes + utensils in one answer; follow recipe `cut-sweep-merge` end to end.
