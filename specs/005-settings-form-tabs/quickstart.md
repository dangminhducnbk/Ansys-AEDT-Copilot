# Quickstart: Full settings form

1. Offline: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` → PASS.
2. Board1 copy (user OK first): request with CPHY_U14_U26 + CPHY_U21_J25 at `ends_checked` → `isim_settings_form` →
   2 tabs, descriptor count = channel-scope template rows; `isim_validate_form` with sweep values for both → both
   valid; apply each with the go → self-check OK; metrics equal to the text flow (SC-004).
3. In Claude desktop: the agent renders tabs, "Set default", "Copy to all tabs"; submit → validated tables in chat.
