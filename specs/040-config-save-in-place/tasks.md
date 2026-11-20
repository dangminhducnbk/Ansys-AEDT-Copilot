# Tasks — 040 config Save in place (local link)

- [x] T001 `interface_sim/config/serve.py`: token_for, page_url, rev, save_state (SaveError), HTTP handler (health /
  page / save / shutdown), idle exit, main(port), ensure (state file, health, version restart, detached start).
- [x] T002 `flow.page_data` adds `built_at`; `flow.config` calls `serve.ensure` → `config_url`, `A.m1(path, url)`.
- [x] T003 `answers.m1(path, url=None)` link texts (VI + EN).
- [x] T004 `assets/page.js`: link mode save via fetch (200 / 4xx / network fallback), BASE rev, hint text.
- [x] T005 CLI `config-serve --port` (parser + commands); `config.yaml` comment `config_port`.
- [x] T006 [P] `tests/unit/test_config_serve.py` (service on port 0 in a thread); CLI golden ADDED command; answers test.
- [x] T007 Offline suite PASS.
- [x] T008 Browser check on a board1 copy request (quickstart 2–5).
- [x] T009 Guide `interface_sim` §0 link; contract mapping; VERSION 5.1.0, CHANGELOG, CLAUDE.md row; graphify update; commit + tag.
