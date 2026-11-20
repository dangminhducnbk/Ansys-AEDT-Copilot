# CLAUDE.md — Ansys AEDT Copilot

Ansys AEDT Copilot = MCP server `aedt_copilot` + Python package `aedt_copilot`: cuts signal channels / interfaces
from a full Ansys AEDT / EDB board into simulation-ready HFSS 3D Layout designs (ports, setup, sweep, airbox, solder
balls, GND cleanup), reviews layouts, edits layouts, builds PI-DC reports. Windows + Ansys AEDT 2026 R1 (2025 R2
fallback).

## Install / update on this PC

Read and follow [INSTALL.md](INSTALL.md) step by step.

## Using the tool

After install, the MCP server's instructions say which guide to read (`get_guide("interface_sim")`, `catalog`, ...).
Guides (`guides/*.md`) and prompts (`prompts/*.md`) hold every usage rule. Reply to the user in their language.

## Layout

| Path | What |
|---|---|
| `aedt_copilot/` | package (`python -m aedt_copilot <cmd>`): `core/`, `cut_board/`, `interface_sim/`, `design_tools/`, `review_checks/`, `layout_snapshot/`, `pi_dc/`, `edit_layout/`, `catalog/`, `cli/` |
| `mcp_server/server.py` | MCP server (thin: arguments + gates, runs the CLI) |
| `guides/`, `prompts/`, `workflows/`, `review_rules/` | what the assistant does (read at run time) |
| `templates/*.csv` | team defaults (single source of default values) |
| `specs/` | Spec Kit features (spec / plan / contracts / tasks) |
| `tools/` | `register_claude.py` (MCP registration), `public_guard.py` (commit / push guard), `set_aedt_version.py` |

## Contributor rules (owner's PC)

- This repository is PUBLIC. Committed files MUST NOT contain customer / project / board names, customer net names,
  fab names, internal IP addresses or local paths of a PC. Use neutral names (`board1`, `BOARDA`, `U14`, ...).
- Customer detail, machine facts and status notes go to `CLAUDE.local.md` (ignored by git, read by Claude Code).
- Every commit and push passes `tools/public_guard.py` (hooks in `.githooks/`, list `.public_guard.local.json` =
  local only). Never bypass it (`--no-verify`); fix the finding (`public_guard.py scrub --apply <file>`, or keep
  the file local).
- `tests/` and `specs/*/mock/` are local only (developer tests on real boards, mock pages built from boards).
- `/init-project` re-checks may write `.claude/settings.json` with local paths: move such hooks to
  `.claude/settings.local.json`.
- Features go through Spec Kit (`/speckit-specify` → plan → tasks → implement); constitution
  `.specify/memory/constitution.md`.
