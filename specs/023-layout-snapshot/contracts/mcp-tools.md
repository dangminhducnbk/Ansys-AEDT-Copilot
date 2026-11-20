# Contracts: MCP tools / CLI (023)

| Tool | Inputs | Safety | Output |
|---|---|---|---|
| `layout_snapshot(op, board, cell="", nets="", scope="window", margin_mm=0)` | op `build` / `status` / `list`; board `.aedb` / `.aedt`; nets comma list of names or fnmatch patterns (window = their bbox + margin); scope `window` / `board`; margin_mm 0 = template `snapshot.window_margin_mm` | read (writes only `<board folder>/Ansys AEDT Copilot/snapshots/`) | build: `snapshot.json` report (folder, key, window mm, counts, times, warnings, unsupported); status: `{state: valid / stale / missing / too_small, folder, report}`; list: snapshots of the board `[{folder, cell, valid, window_mm, scope, size_mb, built_at}]`. Long build → `{pending, task_id}` |
| `design_review(board, channels, checks="", cell="", html=False, snapshot="auto")` | + `snapshot` `auto` / `off` | read (+ snapshot folder) | as 011 + `source` |
| `isim_review(request_id, name, checks="", html=False, snapshot="auto")` | + `snapshot` | read (writes `review.json`, snapshot folder) | as 011 + `source` |

Errors (refused before any EDB call, `{ok: false, error}` / CLI exit 2): op not in the list; board missing / not an
`.aedb`; board locked by AEDT (`.lock`, never deleted); nets empty with scope window for build / status; margin_mm < 0;
snapshot not in `auto` / `off`.

CLI: `python -m aedt_copilot snapshot --op=build|status|list --args-file=<json>`;
`review-measure ... [--snapshot=auto|off]`.
