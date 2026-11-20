# Quickstart: Kitchen guards

1. Offline: `.venv\Scripts\python.exe -m unittest discover -s tests/unit -t .` → PASS, incl.
   `test_kitchen_guards` (registration refusal, contracts, gate refusals with no file written, recipe misplaced).
2. Start check: `.venv\Scripts\python.exe -c "import runpy; runpy.run_path('mcp_server/server.py')"` imports without
   error (55 tools registered); remove one catalog entry in a scratch copy → import fails naming the tool.
3. Board1 copy: `tests/regression.py` (Excel flow) PASS, reference unchanged.
