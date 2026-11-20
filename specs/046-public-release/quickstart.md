# Quickstart — 046 switch runbook + validation

All `git` / python commands from the repo root in Git Bash; `PY=.venv/Scripts/python.exe`.

## A. Guard offline tests (local)

`$PY -m unittest tests.unit.test_public_guard_046 -v` → seeded term / path / binary / e-mail / size findings,
clean blob OK, pre-push range parsing (new branch, update, delete, tag), scrub counts, list validation errors.

## B. Rehearsal on a COPY of the folder (no remote)

1. Copy the repo folder to `<scratch>/rehearsal` (incl. `.git`, without `.venv`).
2. Run steps C2-C6 there.
3. Expected: file list before = after (every path, same bytes for ignored files) (SC-003); `scan --all` 0 findings;
   unit tests PASS; server starts with all tools; 1 commit; 1 tag; no old tags / branches.
4. Seed leaks: commit a file with a protected term → refused; `--no-verify` commit → `pre-push` (simulated stdin)
   refused; image not approved → refused; wrong e-mail → refused; clean commit → OK in < 10 s (SC-002).

## C. Switch (real folder, with the owner)

1. Tree clean, HEAD = release commit; AEDT / editors not holding repo files.
2. Backup: `git bundle create <outside>/ansys_aedt_copilot_full_<time>.bundle --all && git bundle verify ...`.
3. Files: `CLAUDE.md` → `CLAUDE.local.md`; new public `CLAUDE.md`, `INSTALL.md`, `AGENTS.md`,
   `.github/copilot-instructions.md`; `.claude/settings.json` hooks → `.claude/settings.local.json`; `.gitignore`.
4. `$PY tools/public_guard.py scrub` (review counts) → `scrub --apply` → `scan --all` = 0.
5. Unit tests PASS; `$PY -c "import mcp_server.server"` tool count = today's.
6. `git checkout --orphan public && git read-tree --empty && git add -A && git commit -m "Ansys AEDT Copilot 5.x"`
   (hidden e-mail); delete old local tags + old `main`; `git branch -m public main`; `git tag v<release>`.
7. OWNER on GitHub: rename old repo → `Ansys-AEDT-Copilot-archive` (private); create new public
   `Ansys-AEDT-Copilot` (empty, no README).
8. Remotes: `git remote rename origin archive && git remote set-url --push archive DISABLED &&
   git remote add origin <new url>`; `$PY tools/public_guard.py install`.
9. OWNER GO → `git push -u origin main && git push origin v<release>` (pre-push runs).
10. Anonymous check: repo page opens without login; archive still 404 anonymously (SC-005 / SC-006).

## D. Install guide test (SC-005)

Fresh clone into a path without spaces on a test folder / colleague PC; open in Claude Code; "install this repo" →
the assistant follows `INSTALL.md`; `about` answers with the version and tool count. Repeat with `--client desktop`.
