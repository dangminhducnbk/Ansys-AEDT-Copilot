# Implementation Plan: One public repository, checked before every push

**Branch**: `046-public-release` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/046-public-release/spec.md`

## Summary

Three parts, then a one-time switch:

1. **Guard** (`tools/public_guard.py`, generic, committed) + **protected list** (`.public_guard.local.json`, local,
   ignored). Subcommands: `scan` (whole tree / given paths), `pre-commit`, `pre-push`, `scrub` (apply replacements in
   place, dry run by default), `install` (git hooks via `core.hooksPath=.githooks`, repo e-mail). Hooks
   `.githooks/pre-commit|pre-push` (committed, call the guard; no list → refuse).
2. **Install guide** for AI IDEs: `INSTALL.md` (English, imperative) + entry files `CLAUDE.md` (public part),
   `AGENTS.md`, `.github/copilot-instructions.md` → all point to `INSTALL.md`. `tools/register_claude.py --client
   code|desktop|all` (Claude Code user scope: `claude mcp add-json` when the CLI exists, else `~/.claude.json` with
   backup); `setup.bat` registers both. README (Vietnamese) without private paths.
3. **Private notes split**: today's `CLAUDE.md` → `CLAUDE.local.md` (ignored; Claude Code reads it automatically);
   `.claude/settings.json` hooks with local paths → `.claude/settings.local.json` (ignored).
4. **Switch** (runbook in [quickstart.md](quickstart.md), step by step with the owner): backup bundle of the full
   history → scrub tracked text in place → `.gitignore` (tests/, specs/*/mock/, local files) → `git rm --cached` →
   orphan commit with the hidden e-mail → delete old local tags / branch (kept in the bundle + archive) → remotes
   (`archive` push-disabled, `origin` = new public repo) → guard `scan --all` + unit tests + server start → owner go →
   push `main` + tag `v5.6.0`.

## Technical Context

**Language/Version**: Python 3.12 (repo `.venv`; guard needs stdlib only, runs with any Python 3.10+)

**Primary Dependencies**: git (Git Bash runs the hooks: `sh` scripts), stdlib `json`, `re`, `fnmatch`, `hashlib`,
`subprocess`

**Storage**: local JSON list `.public_guard.local.json`; backup `git bundle` outside the repo

**Testing**: offline unit tests (local `tests/unit/test_public_guard_046.py`, temp git repos); switch verified on a
COPY of the repo folder first

**Target Platform**: Windows 11, Git for Windows (hooks via Git Bash `sh`)

**Project Type**: dev tooling + documentation (no MCP tool change)

**Performance Goals**: pre-commit / pre-push < 10 s (SC-002) on ~360 files

**Constraints**: no file on disk deleted by the switch (SC-003); no push without the owner's go; no force push

**Scale/Scope**: ~650 tracked files today → ~360 public; 1 owner commits, team only pulls

## Constitution Check

| Principle | Status |
|---|---|
| I gates | No MCP tool / gate change. Pushes / GitHub repo create / rename need the owner's explicit go (FR-015) |
| II user data | Switch deletes NO file on disk (`git rm --cached` only); full history backed up as a bundle before anything; archive repo untouched |
| III defaults | No template change |
| IV guides | Usage rules unchanged; install guide added (`INSTALL.md`). Dev rule "no customer data in committed files" goes to public `CLAUDE.md` (contributor rules) |
| V regression | `tests/` stays local and keeps running; release rules unchanged. Regression / pidc_check not affected (no package change); unit tests run after the switch |
| VI encoding | Guard reads / writes UTF-8 bytes; scrub keeps line endings; no PowerShell rewrite |
| VII contracts | New public functions of `tools/public_guard.py` + `register_claude.py --client` → [contracts/public-guard.md](contracts/public-guard.md); input validation → `ValueError` (tool outside the package, no `aedt_copilot` import; documented deviation) |
| VIII layers | Guard is a dev tool in `tools/`, pure logic split from git calls (testable offline) |
| IX interface | MCP tools / guides / prompts / outputs unchanged. Repo URL changes (team re-clones: guide + CHANGELOG say so) |
| X catalog | No tool added / changed |

Deviation: `tools/public_guard.py` raises `ValueError`, not `CopilotInputError` — it must run without the package
(hooks run before `.venv` exists on a fresh clone). Justified.

Owner action (Governance: amendments by owner only): add to the constitution, via `/speckit-constitution`, a rule
"committed files MUST NOT hold customer data; checked by the guard" and update Principle V (tests local). Proposed text
in [research.md](research.md) R8.

## Tool catalog check

| Item | Change |
|---|---|
| MCP tools | none added / changed / removed |
| Safety levels | unchanged |
| Workflows | none affected |

## Project Structure

### Documentation (this feature)

```text
specs/046-public-release/
├── spec.md
├── plan.md              # this file
├── research.md          # decisions R1-R8
├── data-model.md        # protected list, findings, hook inputs
├── quickstart.md        # switch runbook + checks
├── contracts/
│   └── public-guard.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
tools/public_guard.py          NEW  guard: rules (pure) + git adapters + CLI (scan / pre-commit / pre-push / scrub / install)
tools/register_claude.py       CHG  --client desktop|code|all (Claude Code user scope)
.githooks/pre-commit           NEW  sh -> python tools/public_guard.py pre-commit
.githooks/pre-push             NEW  sh -> python tools/public_guard.py pre-push "$@" (stdin = refs)
setup.bat                      CHG  register desktop + Claude Code; print INSTALL.md hint
INSTALL.md                     NEW  install guide for AI coding assistants (English)
AGENTS.md                      NEW  entry -> INSTALL.md
.github/copilot-instructions.md NEW entry -> INSTALL.md
CLAUDE.md                      CHG  public: what the repo is, -> INSTALL.md, contributor rules (no customer data)
CLAUDE.local.md                NEW, LOCAL (ignored): today's CLAUDE.md (customer facts, status)
.claude/settings.local.json    NEW, LOCAL (ignored): hooks with local paths (moved from settings.json)
.public_guard.local.json       NEW, LOCAL (ignored): protected list
.gitignore                     CHG  tests/, specs/*/mock/, CLAUDE.local.md, .claude/settings.local.json,
                                    .public_guard.local.json
README.md                      CHG  public clone URL, -> INSTALL.md, no private paths
CHANGELOG.md                   CHG  5.7.0 entry (new repo URL: re-clone)
tests/unit/test_public_guard_046.py  NEW, LOCAL
```

**Structure Decision**: guard in `tools/` next to `register_claude.py` (dev / install scripts, not the package).

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
|---|---|---|
| Push check on top of commit check | catches commits made with the commit check skipped (`--no-verify`) | commit check alone can be bypassed |
| Binary approval by hash | images cannot be scanned for names | approve by path only would let a changed picture through |
| Orphan history | old history holds customer data | rewriting 400 commits risks the archive and gains nothing (archive stays) |
