# Contracts: MCP tools (additions)

| Tool | Inputs | Gate | Output |
|---|---|---|---|
| `isim_settings_form(request_id="")` | — | none (read-only) | `form.build` output |
| `isim_validate_form(request_id, entries)` | `entries` JSON `{interface: {values, handling}}` | none (never applies) | `form.validate` output |

`isim_apply` unchanged: Gate B per interface after the engineer's explicit go. CLI ops: `form`, `validate_form`.
