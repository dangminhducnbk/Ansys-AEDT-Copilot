# Contracts: MCP tools (additions, `mcp_server/server.py`)

Thin: args → CLI `isim --op=...` subprocess. Existing tools unchanged except the outputs noted.

| Tool | Inputs | Gate / precondition | Output |
|---|---|---|---|
| `isim_previous(name, workspace="")` | name rules | — (read-only) | `{runs[...], table_md}` |
| `isim_recut(request_id, name, source, nets="")` | `source` = request id / folder / `user_settings.json` path | new request; interface at `started` or absent | `isim_trace` output + `recut_from, recut_diffs, old_values, old_handling, dropped` |
| `isim_confirm_content` | unchanged; `content.recut_diffs` must all have `resolution` | GATE A | + `user_settings` path |
| `isim_check_ends` | unchanged | step `cut` | + `handling_compare` (re-cut only); `settings_md` pre-filled from source |
| `isim_apply` | unchanged | GATE B | + `user_settings` path; no `settings.json` / `settings.md` |

CLI ops added: `previous`, `recut`.
