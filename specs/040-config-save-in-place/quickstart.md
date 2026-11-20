# Quickstart — 040 validation

1. Offline: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` — all PASS, incl. `test_config_serve`
   (save OK → file replaced + `read.find_saved` returns it; bad token 403; unknown request 404; stale rev 409;
   read-only 409; bad folder 400; not JSON 415; path never taken from the body).
2. Board1 copy request (scratchpad): run `isim_config` (CLI `isim --op=config`) → result has `config_url`, M1 shows
   link + path.
3. Open the link in the browser pane, fill the folder, Save → message "Saved to …\config.html"; no download, no
   dialog; file mtime changed; `isim --op=config_check` reads the folder name.
4. Rebuild the page (`isim --op=config` again) with the old tab open, Save in the old tab → "reload" message, file not
   overwritten.
5. Stop the service (kill pid from `~/.aedt_copilot/config_service.json`), Save → "Cannot reach the tool" + 038
   fallback.
6. `tests/config_flow_check.py` on a board1 copy — PASS (flow unchanged).
