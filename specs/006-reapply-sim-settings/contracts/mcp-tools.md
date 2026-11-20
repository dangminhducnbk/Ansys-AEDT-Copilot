# Contracts: MCP tools (changes)

| Tool | Change | Gate / precondition | Output |
|---|---|---|---|
| `isim_apply(request_id, name, values, handling="", user_agreed_settings=false)` | step `applied` / `merged` → re-apply (simulation group only) via CLI op `reapply`; step `ends_checked` → first apply (unchanged) | GATE B flag; re-apply: server runs `validate_reapply` first and refuses with the errors (cut-group change, handling change, rule errors) | first apply: unchanged; re-apply: `apply.reapply` output (task) |
| `isim_validate_settings(request_id, name, values, handling="")` | applied / merged → `validate_reapply` | none | `{valid, errors, table_md}` |
| `isim_settings_form`, `isim_validate_form` | applied / merged tabs enabled (cut group locked) | none | as 005 + `reapply`, `note` |

No new tool. CLI op added: `reapply`.
