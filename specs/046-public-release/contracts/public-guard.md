# Contract — tools/public_guard.py and register_claude.py (046)

Errors: `ValueError` (bad input / bad list; message names the input and the expected value). Tool runs without the
`aedt_copilot` package (documented deviation, plan.md).

## Pure functions

### `load_list(path) -> dict`
- In: path to `.public_guard.local.json` (str, exists). Out: validated dict (data-model.md), regexes compiled.
- Errors: missing file → `ValueError("protected list not found: <path> (create it, see INSTALL.md / CLAUDE.local.md)")`;
  bad key → `ValueError` naming it.

### `check_blob(lst, path, data: bytes) -> list[Finding]`
- path rule, size rule, binary rule (NUL / extension → approved hash), term rule per line (UTF-8, errors replaced).
- Pure; same input → same output; never raises on content.

### `check_email(lst, email, where) -> list[Finding]`
- Finding when `email` (case-insensitive) != `lst["email"]`.

### `scrub_text(lst, text) -> (text, n)`
- Applies `replace` in order; returns new text and replacement count. Line endings unchanged.

### `outgoing(lines, rev_list) -> list[str]`
- In: pre-push stdin lines (4 fields each; else `ValueError`), callable for `git rev-list`. Out: commit ids to check
  (deleted refs skipped, de-duplicated, oldest first).

### `report(findings) -> str`
- Text grouped by rule: `path:line  term  -> fix`; header with counts; empty → "public_guard: OK (<n> files)".

## CLI (exit 0 = OK, 1 = findings / refused, 2 = bad input)

| Command | Does |
|---|---|
| `scan [--all \| <paths>...]` | `--all` = every tracked file + every file `git add -A` would add (index view) |
| `pre-commit` | staged blobs + author / committer e-mail |
| `pre-push <remote> <url>` | stdin refs → outgoing commits → blobs + e-mails |
| `scrub [--apply] [<paths>...]` | default dry run over tracked text files; `--apply` writes in place |
| `install` | `core.hooksPath=.githooks`, `user.email` = list e-mail (repo config), check the list loads |

Postconditions: never writes outside the repo; `scrub --apply` only changes tracked text files; nothing pushes.

## `tools/register_claude.py` (changed)

| Arg | Meaning |
|---|---|
| `--client desktop` | today's behaviour (default when no `--client`) |
| `--client code` | Claude Code user scope: `claude mcp add-json` if on PATH, else `~/.claude.json` (`.bak` first, only `mcpServers.aedt_copilot` changed) |
| `--client all` | both |
| `--print` | print the server JSON (command / args / env) for other MCP clients; writes nothing |
| `--remove` | remove from the chosen client(s) |

Errors: unknown client → exit 2 with the allowed values; unreadable JSON config → no write, message, exit 1.
