# Tasks — 046 One public repository, checked before every push

Spec: [spec.md](spec.md) · Plan: [plan.md](plan.md) · Research: [research.md](research.md) ·
Contract: [contracts/public-guard.md](contracts/public-guard.md) · Runbook: [quickstart.md](quickstart.md)

Story order follows dependencies, not only priority: the switch (US1) needs the guard (US2), the protected list (US4)
and the install files (US3) first. Nothing is pushed and nothing on GitHub is changed without the owner's explicit go.

## Phase 1 — Setup

- [x] T001 Add ignore rules to `.gitignore` (block "# 046 local only"): `tests/`, `specs/*/mock/`, `CLAUDE.local.md`,
  `.claude/settings.local.json`, `.public_guard.local.json` — do NOT `git rm --cached` yet (switch step T030 does)
- [x] T002 Create the local protected list `.public_guard.local.json` from the trial export mapping in
  `D:\work\project\tool\aedt_copilot_publish\make_public.py` (`REPLACE` → `replace`, `LEAK` → `terms`, `EXCLUDE` +
  tests/mock → `paths`), `email` = `dangminhducnbk@users.noreply.github.com`, `max_bytes` 5000000,
  `approved_binaries` = sha256 of the 2 glyph `.npz` files (data-model.md shape; never committed)

## Phase 2 — Foundational (guard core, pure)

- [x] T003 `tools/public_guard.py`: `load_list(path)` — validation per data-model.md: "`version` 1; `email` contains
  `@`; every `terms[].pattern` / regex `replace[].from` compiles; `paths` non-empty strings; `approved_binaries`
  values 64 hex chars"; missing file → `ValueError("protected list not found: <path> ...")`
- [x] T004 `tools/public_guard.py`: `check_blob(lst, path, data)` (rules path / size / binary (NUL in first 8000 bytes
  or binary extension → approved sha256) / term per line, UTF-8 errors replaced), `check_email`, `scrub_text`,
  `report`; Finding fields `rule, path, line, text (<= 120 chars), commit, fix` (data-model.md)
- [x] T005 [P] `tests/unit/test_public_guard_046.py` (local): list validation errors, each rule seeded + clean blob,
  scrub counts / line endings kept, report text

## Phase 3 — US2 Check before every commit and push (P1)

Independent test: seeded term / path / binary / e-mail / size refused at commit; `--no-verify` commit refused at push;
clean commit passes < 10 s.

- [x] T006 [US2] `tools/public_guard.py`: `outgoing(lines, rev_list)` (pre-push stdin `<local ref> <local sha>
  <remote ref> <remote sha>`; zero remote sha → `rev-list <sha> --not --remotes=<remote>`; deleted ref skipped;
  oldest first; bad line → `ValueError`)
- [x] T007 [US2] `tools/public_guard.py`: git adapters — staged blobs (`git diff --cached --name-only -z
  --diff-filter=ACMR`, `git show :<path>`), commit blobs (`git diff-tree --no-commit-id -r --root -M -z <c>`,
  `git cat-file blob <c>:<path>`), e-mails (`git var GIT_AUTHOR_IDENT / GIT_COMMITTER_IDENT`, `git log -1
  --format=%ae%n%ce <c>`), tracked + would-be-added files for `scan --all`
- [x] T008 [US2] `tools/public_guard.py` CLI: `scan [--all | paths]`, `pre-commit`, `pre-push <remote> <url>`,
  `scrub [--apply] [paths]`, `install` (core.hooksPath=.githooks, repo `user.email` = list e-mail, list loads);
  exit 0 OK / 1 findings / 2 bad input; stdout UTF-8
- [x] T009 [P] [US2] `.githooks/pre-commit` and `.githooks/pre-push` (sh, LF endings): python lookup
  `.venv/Scripts/python.exe` → `py -3` → `python`, none → refuse; pass args + stdin to the guard
- [x] T010 [US2] Tests in `tests/unit/test_public_guard_046.py`: `outgoing` cases (new branch, update, delete, tag);
  temp git repo end-to-end: install, seeded commit refused, `--no-verify` commit then `pre-push` refused, clean OK,
  timing < 10 s
- [x] T011 [US2] `.gitattributes`: `.githooks/* text eol=lf` (hooks must keep LF on Windows)

## Phase 4 — US3 A colleague's AI IDE installs the tool from the guide (P1)

Independent test: fresh clone, "install this repo" in Claude Code → done via `INSTALL.md` only; `about` returns the
version and tool count.

- [x] T012 [US3] `tools/register_claude.py`: `--client desktop|code|all` (default desktop = today), `--print`,
  `--remove` per client; Claude Code user scope: `claude mcp add-json aedt_copilot <json> --scope user` when `claude`
  is on PATH, else `~/.claude.json` (backup `.bak`, change only `mcpServers.aedt_copilot`, keep every other key);
  unknown client → exit 2; unreadable JSON → no write, exit 1 (contract)
- [x] T013 [P] [US3] Tests (local) for `register_claude.py --client code` on a temp HOME: add / update / remove keeps
  other keys, `.bak` written, bad JSON untouched, `--print` writes nothing
- [x] T014 [US3] `setup.bat`: register `--client all`; final lines point to `INSTALL.md` and say what to restart
- [x] T015 [US3] `INSTALL.md` (English, for AI coding assistants, terse imperative, exact commands + expected output):
  prerequisites check (Windows, `ANSYSEM_ROOT261` / `ANSYSEM_ROOT252`, Python 3.10-3.12, git), clone path without
  spaces, `setup.bat`, registration per client (Claude desktop, Claude Code, generic via `--print`), verification
  (`.venv\Scripts\python -m aedt_copilot about` + MCP `about`), restart, update after `git pull` (CHANGELOG "setup.bat"
  rule), uninstall (`--remove --client all`), common errors (AEDT dialog open, license, path with spaces, old private
  clone → re-clone)
- [x] T016 [P] [US3] Entry files pointing to `INSTALL.md`: `AGENTS.md`, `.github/copilot-instructions.md`
- [x] T017 [US3] New public `CLAUDE.md`: what the repo is, "to install read INSTALL.md", contributor rules (no
  customer data in committed files, customer detail → `CLAUDE.local.md`, guard must pass, `/init-project` writes
  `.claude/settings.json` → move hooks to `settings.local.json`); move today's `CLAUDE.md` to `CLAUDE.local.md`
  unchanged (content + `@` imports + init-project block)
- [x] T018 [P] [US3] `README.md` (Vietnamese): public clone URL `https://github.com/dangminhducnbk/Ansys-AEDT-Copilot`,
  clone path example without private folders, link `INSTALL.md`, Claude Code registration line
- [x] T019 [US3] Move `.claude/settings.json` hooks (graphify, project-guard: local paths) to
  `.claude/settings.local.json`; leave `.claude/settings.json` without local paths (or remove it if empty)

## Phase 5 — US4 Keep the protected list up to date (P2)

Independent test: add a term to the list, stage a file containing it → refused.

- [x] T020 [US4] `tools/public_guard.py`: `list-check` command (loads the list, prints counts per section, compiles
  every pattern); refusal messages say which list entry matched (`note`)
- [x] T021 [P] [US4] Test: term added → staged file refused with its `note`; removed → passes

## Phase 6 — US1 Switch to one clean public repository (P1)

Independent test: rehearsal on a COPY — every file on disk kept, 0 findings, unit tests PASS, server starts, 1 commit.

- [x] T022 [US1] `tools/public_guard.py scrub` dry run on the real folder; review counts per file; check no replacement
  hits a diff-pair / trio suffix (`_P/_N`, `_A/_B/_C`)
- [x] T023 [US1] Rehearsal: copy the repo folder (with `.git`, without `.venv`) to the session scratchpad; run
  quickstart C2-C6 there; write the switch record `switch_<time>.json` (bundle verify, file list + hashes before /
  after, scrub counts, scan, unit tests, tool count, commit id)
- [x] T024 [US1] Rehearsal checks (quickstart B3-B4): file lists equal (SC-003), `scan --all` 0, unit tests PASS,
  `import mcp_server.server` tool count unchanged, seeded leaks refused, clean commit OK
- [x] T025 [US1] Report the rehearsal to the owner (table) and get the go for the real switch
- [x] T026 [US1] Real folder: backup `git bundle create D:\work\project\tool\_backup\ansys_aedt_copilot_full_<time>.bundle
  --all` + `git bundle verify`
- [x] T027 [US1] Real folder: `scrub --apply`; `scan --all` = 0; unit tests PASS; server tool count unchanged
- [x] T028 [US1] Real folder: orphan branch, `git read-tree --empty`, `git add -A`, commit "Ansys AEDT Copilot
  5.7.0" with the hidden e-mail; delete old local tags + old `main` (kept in bundle + archive); rename to `main`;
  tag `v5.7.0`
- [x] T029 [US1] OWNER on GitHub (guided in the browser): rename `Ansys-AEDT-Copilot` → `Ansys-AEDT-Copilot-archive`
  (private); create public `Ansys-AEDT-Copilot`, empty
- [x] T030 [US1] Remotes: `origin` → `archive` (`set-url --push archive DISABLED`), add new `origin`;
  `public_guard.py install`; file list vs before (SC-003)
- [x] T031 [US1] OWNER GO → `git push -u origin main` + `git push origin v5.7.0` (pre-push runs); anonymous check:
  public repo opens, archive 404 (SC-005 / SC-006)

## Phase 7 — Polish

- [x] T032 `VERSION` 5.7.0, `CHANGELOG.md` 5.7.0 (new public repo URL: colleagues re-clone; setup.bat rerun for Claude
  Code registration), done before T028 so the clean commit holds them
- [x] T033 `CLAUDE.local.md` status row 046 (local only); memory note: public repo + guard
- [x] T034 Install test from a fresh clone of the public repo into a scratch path (quickstart D) with Claude Code
  registration printed / dry; record result
- [x] T035 `graphify update .`; propose the constitution amendment text (research R8) for the owner's
  `/speckit-constitution`

## Dependencies

- T001-T002 → T003-T005 → US2 (T006-T011) → US4 (T020-T021)
- US3 (T012-T019) needs only Phase 1; can run beside US2
- US1 (T022-T031) needs US2, US3, US4 and T032; T025 / T029 / T031 wait for the owner
- T034 after T031

## Parallel examples

- After T004: T005 tests || T009 hooks || T012 register_claude || T015 INSTALL.md
- US3: T016 entry files || T018 README || T013 tests

## Implementation strategy

MVP = guard + hooks (US2) working on the current private repo (protects every commit from now on), then install files
(US3), then the rehearsal; the real switch only after the owner approves the rehearsal report.
