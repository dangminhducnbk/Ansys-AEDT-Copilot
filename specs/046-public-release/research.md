# Research — 046 public repository

## R1 Where the hooks live

- Decision: committed `.githooks/` + `git config core.hooksPath .githooks` (set by `public_guard.py install`).
- Rationale: hooks in `.git/hooks` are lost on a fresh clone and invisible in reviews; `core.hooksPath` is repo-local
  config, re-applied by `install` (FR-008). Scripts are `sh` (Git for Windows runs hooks through its bash).
- Python lookup in the hook: `.venv/Scripts/python.exe` → `py -3` → `python`; none → refuse with a message.
- Missing `.public_guard.local.json` → refuse (fail closed). Colleagues never commit, so they are not blocked.
- Alternatives: pre-commit framework (extra dependency, network install) — rejected.

## R2 What the pre-push hook checks

- stdin lines `<local ref> <local sha> <remote ref> <remote sha>`; outgoing commits =
  `git rev-list <local sha> --not --remotes=origin` (new branch / zero remote sha) else `<remote sha>..<local sha>`.
  Deleted refs (local sha zero) skipped. Tags pushed → the commit they point to is checked the same way.
- Per commit: author + committer e-mail; changed files (`git diff-tree --no-commit-id -r --root -M <c>`, statuses
  A/M/R/C) read as blobs at that commit (`git cat-file blob <c>:<path>`).
- Pre-commit: staged paths `git diff --cached --name-only -z --diff-filter=ACMR`, content from the index
  (`git show :<path>`), e-mail from `git var GIT_AUTHOR_IDENT` / `GIT_COMMITTER_IDENT`.
- Rationale: content is checked as committed, not as on disk (a fixed working file does not hide a bad staged blob).

## R3 Rules

| Rule | Detail |
|---|---|
| term | each list pattern (regex, case-insensitive unless `case: true`) on every line of text blobs |
| path | fnmatch patterns on the repo path (`tests/*`, `specs/*/mock/*`, `CLAUDE.local.md`, ...) |
| binary | NUL byte in the first 8000 bytes or binary extension → needs `approved_binaries[path] == sha256` |
| email | author and committer e-mail must equal `email` of the list |
| size | blob > `max_bytes` (default 5 MB) → refuse (large pages are usually board data) |

Finding = `{rule, path, line, text (term only, shortened), fix}`; exit 1 when any finding.

## R4 Scrub (switch + later fixes)

- Same `replace` pairs as the trial export (`D:\work\project\tool\aedt_copilot_publish\make_public.py`), moved into
  the local list; ordered; plain or regex; same length where goldens care (goldens are local now, kept anyway).
- Applies to tracked text files only, in place, UTF-8, line endings kept; dry run prints `path: n replacements`.
- Paths of the repo folder are not protected (a local test compares with the machine path).

## R5 Private notes for the assistant

- Decision: `CLAUDE.local.md` (Claude Code loads it automatically next to `CLAUDE.md`; ignored by git).
- Today's `CLAUDE.md` (customer facts, status, `@` imports of the owner's global docs, init-project block) moves there
  unchanged. Public `CLAUDE.md` = short: purpose, `INSTALL.md`, contributor rules.
- `.claude/settings.json` holds hooks with the owner's paths → move to `.claude/settings.local.json` (ignored, merged
  by Claude Code). Note: `/init-project` re-checks write `.claude/settings.json`; the guard then refuses the paths →
  move again (noted in the public CLAUDE.md contributor rules).

## R6 MCP registration for Claude Code

- Claude Code user-scope servers live in `~/.claude.json` (`mcpServers`). Preferred: `claude mcp add-json
  aedt_copilot '<json>' --scope user` when `claude` is on PATH (not on the owner's PC: desktop app only); else edit
  `~/.claude.json` (backup `.bak`, keep every other key, only `mcpServers.aedt_copilot`).
- Same server JSON as Claude desktop: absolute `command` (`.venv\Scripts\python.exe`), `args` (`mcp_server\server.py`),
  `env` (`AEDT_COPILOT_HOME`). Claude Code reads the file at start → restart / new session.
- Generic MCP client (VS Code, Cursor): `INSTALL.md` prints the same command / args / env; `register_claude.py --print`
  outputs the JSON.

## R7 Switch order and safety

1. Preconditions: clean tree, HEAD = release, nobody holds files open.
2. `git bundle create <outside>\ansys_aedt_copilot_full_<time>.bundle --all` + `git bundle verify`.
3. Files: CLAUDE.md split, settings move, new files (guard, hooks, guide, entries), `.gitignore`.
4. `scrub` (dry run → review → apply); `scan --all` = 0 findings on the files to be committed.
5. `git checkout --orphan public`; `git read-tree --empty` (`git rm --cached` refuses files changed by scrub); `git add -A` (ignore rules apply); commit with
   `user.email` = hidden e-mail (repo config). Unit tests + server start (tool count) before the commit.
6. Old refs: delete local branch `main` (old) and all old tags — they live in the bundle and the archive repo; rename
   `public` → `main`; tag `v5.6.0` (or the release) on the new commit.
7. GitHub (owner, in the browser): rename old repo `Ansys-AEDT-Copilot` → `Ansys-AEDT-Copilot-archive` (stays
   private); create new PUBLIC `Ansys-AEDT-Copilot`, empty.
8. Remotes: `origin` → `archive` + `git remote set-url --push archive DISABLED`; add `origin` = new URL.
9. `public_guard.py install`; owner go → `git push -u origin main` + `git push origin v5.6.0` (pre-push runs).
- Rehearsal on a COPY of the folder first (steps 2-6, no remote), compare file lists before / after (SC-003).

## R8 Constitution amendment (owner, `/speckit-constitution`)

Proposed (MINOR, new principle XI + V wording):
- XI "Public Repository Hygiene": committed files MUST NOT contain customer / project / board names, customer net
  names, internal addresses or local paths of a PC; customer detail lives in `CLAUDE.local.md` / local files; every
  commit and push MUST pass `tools/public_guard.py`.
- V: "`tests/` is local to the developer's PC (not committed); regression and unit tests still MUST pass before a
  release."
