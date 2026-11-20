# Research — 040 config save in place

## R1 Overwrite without a picker
- Decision: page served by a local tool service; Save = POST of the state; the service writes the file.
- Rationale: a `file://` page cannot write to disk; File System Access API always needs one picker per page/session
  (a stored handle in IndexedDB still needs a permission prompt after reload, and `file://` origins are opaque).
- Alternatives: stored handle (still prompts), download + reader (038, stray copies, no overwrite), browser extension (install pain).

## R2 Where the service runs
- Decision: detached process `python -m aedt_copilot config-serve`, started by `isim_config` when not running, one per
  PC, idle exit 8 h, state file `~/.aedt_copilot/config_service.json` (port, pid, version, secret).
- Rationale: outlives the tool call and the Claude session; several sessions share it; a version change (git pull)
  restarts it (`/shutdown` with the secret).
- Alternatives: thread in the MCP server (dies with that session, one port per session), Windows service (admin rights).

## R3 Security
- Decision: bind 127.0.0.1; per-request random token in the URL; JSON body only (415 otherwise: a cross-site HTML form
  cannot send `application/json` without CORS preflight, and no CORS headers are sent); path from the registry,
  never from the page; only `config.html` of a registered, not read-only request.
- Rationale: blocks other machines, other websites (CSRF) and path tricks.

## R4 What the page sends
- Decision: state only; the service rebuilds the page from the disk file's data block + state (`page.build`).
- Rationale: the saved file is always tool-generated (no arbitrary HTML written), smaller body, same 038 format.

## R5 Stale page
- Decision: revision = data `built_at` + state `saved_at`; mismatch → 409 "reload".
- Rationale: `isim_config` may rebuild the page (new data) while an old tab is open; the old tab must not overwrite it.

## R6 Port
- Decision: `config.yaml` `config_port` (default 17880), try +0..+9 when taken by another program (health check tells ours).
