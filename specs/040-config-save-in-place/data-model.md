# Data model — 040

| Item | Where | Fields |
|---|---|---|
| Page data (038) | `cfg-data` block | + `built_at` (ISO time of the build) |
| Page state (038) | `cfg-state` block | `saved_at` set by the service on save (server time) |
| Revision | computed | `"<built_at>|<saved_at or ''>"` |
| Request token | `<request>/_work/config_token` | 32 hex, one per request |
| Service record | `~/.aedt_copilot/config_service.json` | `port`, `pid`, `version`, `secret` (32 hex), `started` |
| Machine setting | `config.yaml` | `config_port` (optional, default 17880) |
