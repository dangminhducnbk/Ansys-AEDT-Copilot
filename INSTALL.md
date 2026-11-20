# INSTALL — Ansys AEDT Copilot (for AI coding assistants)

MISSION: install the MCP server `aedt_copilot` on THIS Windows PC and register it in the user's AI client.
Read every step. Run the commands exactly. Stop and tell the user when a check fails; never half-install.
Shell: commands below are for `cmd.exe` / PowerShell from the repo root unless marked Git Bash.

## RULES OF ENGAGEMENT

- Do not edit code to make the install pass. Do not delete user files. Do not change AEDT settings.
- Ask the user before closing Claude desktop or any running application.
- The repo folder path MUST NOT contain spaces (AEDT and `.bat` break). If it does: tell the user to move the clone,
  e.g. `D:\tools\Ansys-AEDT-Copilot`.
- Each user has their own AEDT license. Never copy license settings from elsewhere.

## 1. CHECK PREREQUISITES (stop on the first failure)

| Check | Command | Expected |
|---|---|---|
| Windows | `ver` | `Microsoft Windows ...` |
| AEDT 2026 R1 (or 2025 R2 fallback) | `echo %ANSYSEM_ROOT261%` then `echo %ANSYSEM_ROOT252%` | at least one prints a folder that exists |
| Python 3.10-3.12 | `py -3 --version` (else `python --version`) | `Python 3.10.x` .. `3.12.x` (3.12 tested) |
| git | `git --version` | `git version ...` |
| Repo path | `cd` | no spaces in the path |

Failure text to give the user: what is missing + where to get it (Ansys AEDT installer from their IT; Python from
python.org, "Add to PATH" ticked; Git for Windows).

## 2. SETUP

```bat
setup.bat
```

Expected (last lines): `[ok] AEDT 2026.1: ...`, `pyedb 0.85.0`, `[ok] Da dang ky aedt_copilot cho Claude Code ...`,
then either `[ok] Da dang ky aedt_copilot: ...claude_desktop_config.json` or the notice that Claude desktop is running.

What it does: creates `.venv`, installs `requirements.txt` (pyedb 0.85, pyaedt 1.9.0, mcp<2), writes the AEDT version to
`config.yaml`, sets user env `AEDT_COPILOT_HOME`, registers the MCP server.

If `pip install` fails behind a proxy: tell the user (corporate proxy / pip config); do not change requirements.

## 3. REGISTER THE MCP SERVER (per client)

| Client | Command | Then |
|---|---|---|
| Claude Code (CLI, VS Code extension, desktop app Code tab) | `.venv\Scripts\python tools\register_claude.py --client code` | open a NEW Claude Code session |
| Claude desktop (chat) | user quits Claude desktop fully (tray icon → Quit), then `.venv\Scripts\python tools\register_claude.py --client desktop` | reopen Claude desktop |
| Other MCP client (VS Code Copilot, Cursor, ...) | `.venv\Scripts\python tools\register_claude.py --print` | put the printed `command`, `args`, `env` into that client's MCP config (server name `aedt_copilot`, transport stdio) |

`setup.bat` already ran `--client code` and tried `--client desktop`. Run the desktop line again only if setup said
Claude desktop was running.

## 4. VERIFY

```bat
type VERSION
.venv\Scripts\python -c "import sys; sys.path.insert(0, 'mcp_server'); import server, asyncio; print(len(asyncio.run(server.mcp.list_tools())))"
```

Expected: the version (e.g. `5.7.0`) and the tool count (60 at 5.7.0; any number > 50 is fine).
Then, in the client (new session): call the MCP tool `about` → it answers with the tools and guides.
Report to the user: version, tool count, which clients are registered, what to restart.

## 5. UPDATE (after `git pull`)

1. `git pull`
2. Read the newest entries of `CHANGELOG.md`: if one says `setup.bat` must be rerun → run `setup.bat`.
3. Otherwise only: new Claude Code session / restart Claude desktop (server, guides, prompts are re-read on start).
4. Moved the repo folder → rerun `setup.bat` (registration stores absolute paths).

## 6. UNINSTALL

```bat
.venv\Scripts\python tools\register_claude.py --remove --client all
```
Then delete the repo folder (user's decision) and the user env `AEDT_COPILOT_HOME`
(`reg delete HKCU\Environment /v AEDT_COPILOT_HOME /f`).

## 7. COMMON ERRORS

| Symptom | Cause / fix |
|---|---|
| `Failed to initialize Dlls` (pyedb) | AEDT not found / wrong Python: check step 1, rerun `setup.bat` |
| Tools time out (60 s) | an AEDT dialog is open: user closes it or restarts AEDT |
| `aedt_copilot` missing in Claude desktop | registered while the app was running: quit fully, run `--client desktop` again |
| `aedt_copilot` missing in Claude Code | old session: start a new one; check `~/.claude.json` has `mcpServers.aedt_copilot` |
| License error | user's AEDT license (`ANSYSLMD_LICENSE_FILE`): ask their IT |
| Path with spaces | move the clone to a path without spaces, rerun `setup.bat` |
| Clone of the old private repository | re-clone this public repository; the old one is archived |

## 8. USING THE TOOL

After install, the user asks in plain words (e.g. "cut board X channel U14-U26") or picks a prompt
(`interface-sim`, `copilot-help`, ...). The server tells the assistant which guide to read (`get_guide`).
