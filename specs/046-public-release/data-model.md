# Data model — 046

## Protected list `.public_guard.local.json` (local, ignored)

```json
{
  "version": 1,
  "email": "<user>@users.noreply.github.com",
  "max_bytes": 5000000,
  "terms": [
    {"pattern": "<regex>", "case": false, "note": "customer A board"}
  ],
  "replace": [
    {"from": "<text or regex>", "to": "<neutral>", "regex": false}
  ],
  "paths": ["tests/*", "specs/*/mock/*", "CLAUDE.local.md", ".public_guard.local.json",
            ".claude/settings.local.json"],
  "approved_binaries": {"aedt_copilot/pi_dc/data/siwave_colorbar_glyphs_h1000.npz": "<sha256>"}
}
```

Validation: `version` 1; `email` contains `@`; every `terms[].pattern` / regex `replace[].from` compiles; `paths`
non-empty strings; `approved_binaries` values 64 hex chars. Bad list → `ValueError` naming the key.

## Finding

| Field | Type | Note |
|---|---|---|
| rule | `term` / `path` / `binary` / `email` / `size` | |
| path | str | repo path (`/`), or commit id for `email` |
| line | int / None | term only |
| text | str | matched term in context, <= 120 chars |
| commit | str / None | pre-push only |
| fix | str | e.g. "replace the name (scrub) or move the detail to CLAUDE.local.md" |

## Outgoing set (pre-push)

`[(commit, author_email, committer_email, [(path, blob_bytes)])]` from the stdin refs (research R2).

## Switch record (quickstart)

`<outside>/switch_<time>.json`: bundle path + `verify` result, file list before / after (hash per path),
scrub counts per file, scan result, unit-test result, server tool count, new commit id.
