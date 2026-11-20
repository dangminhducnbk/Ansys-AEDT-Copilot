# Contracts — 040 config save

## `serve.save_state(rid, token, state, base_rev) -> dict`
- In: `rid` registered request id (str, non-empty); `token` 32 hex (equal to `<work>/config_token`); `state` dict with
  `channels` = the disk page's channels, every `folder` valid (038 rules: not empty, no space / `<>:"/\|?*;`, not
  `_work`, unique case-insensitive); `base_rev` str.
- Out: `{"path": <request>/config.html, "saved_at": iso, "rev": str}`.
- Errors (`SaveError(status, message)`): 404 unknown request / no config page; 403 token; 409 read-only page or
  `base_rev` != disk rev; 400 state invalid (message lists channel + field).
- Effect: only `<request folder>/config.html` replaced (temp + `os.replace`).

## `serve.token_for(req) -> str`
- In: loaded request. Out: 32 hex; created once in `<work>/config_token`, then stable.

## `serve.page_url(req, port) -> str`
- `http://127.0.0.1:<port>/r/<rid>/<token>/`; port int 1..65535 else CopilotInputError.

## `serve.ensure(log=print) -> int | None`
- Port of a running service of this tool version (started detached when needed); `None` when it cannot start in 5 s.

## HTTP (127.0.0.1 only)
| Method / path | Body | Response |
|---|---|---|
| GET `/health` | — | 200 `{service, version, pid}` |
| GET `/r/<rid>/<token>/` | — | 200 config.html (no-store) / 403 / 404 |
| POST `/r/<rid>/<token>/save` | JSON `{state, base_rev}` | 200 `{path, saved_at, rev}` / 400 / 403 / 404 / 409 / 415 |
| POST `/shutdown` | JSON `{secret}` | 200, process exits / 403 |

## `isim_config` result (added key)
- `config_url`: str or null (service not available → M1 038 text).

## `answers.m1(path, url=None) -> str`
- Two lines (VI, EN); with url both contain the url and the file path.
