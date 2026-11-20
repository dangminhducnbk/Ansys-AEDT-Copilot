# Implementation Plan: AEDT 2026 R1 Migration

**Branch**: `001-aedt-2026r1-migration` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: `specs/001-aedt-2026r1-migration/spec.md` + audit `aedt_copilot_2026r1_audit.md`

## Summary

Tool finds AEDT itself (new `aedt_copilot/aedt_env.py`), sets `ANSYSEM_ROOT<vid>` before pyedb/pyaedt import,
opens every EDB through one `open_edb()` with explicit version + `grpc=False` (.NET backend kept).
Then switch config to `2026.1`. Server: pass env to children, `--key=value` args.

## Technical Context

**Language/Version**: Python 3.12 (`.venv`)

**Primary Dependencies**: pyedb 0.85.0 (.NET backend), pyaedt 1.9.0, mcp<2 - unchanged

**Target Platform**: Windows, AEDT 2026 R1 (v261); 2025 R2 (v252) fallback

**Project Type**: CLI package + MCP server (stdio)

**Constraints**: no pip install; no AEDT GUI; read-only checks on the user board; write ops on copies only

## Design

| Item | Decision |
|---|---|
| Resolver | `aedt_env.resolve()`: config `aedt_root` -> env `ANSYSEM_ROOT###` -> registry `HKLM\SOFTWARE\Ansoft\ElectronicsDesktop` (+WOW6432Node, values `InstallationDirectory`/`InstallDir`/`InstallPath`, accepted only if `ansysedt.exe` exists) -> scan `C:\Program Files\ANSYS Inc\v###\AnsysEM` |
| Version | config `aedt_version` (`"2026.1"` / `"2025.2"` / `"auto"` = newest) |
| Env | `ensure()` first runs `sync_env()` (copies missing `ANSYSEM_ROOT###`, `AWP_ROOT###`, `ANSYSLMD_LICENSE_FILE`, `ANSYSLI_SERVERS`, `ANSYSLIC_DIR` from saved Windows env: HKLM Session Manager\Environment + HKCU\Environment, read-only), then sets `ANSYSEM_ROOT<vid>` if missing; called first in `__main__.main()` (errors deferred to first EDB open) |
| EDB | `aedt_env.open_edb(path, cell, readonly, version)` -> `Edb(..., version=ver, isreadonly=readonly, grpc=False)` |
| SIwave | `common.siwave_exe()` -> `aedt_env.siwave_exe()` |
| Server | `env=aedt_env.child_env()` for Popen; `--box=...` etc.; about/show_defaults show `aedt_env.info()` (needs Claude desktop restart) |
| Not changed now | merge.py / aedt_finish.py (pyaedt `Desktop`/`Hfss3dLayout`): use config version; env set by `ensure()` -> works. Revisit in step 9 |

## Constitution Check

| Principle | Status |
|---|---|
| I. Gates in code | No gate touched - PASS |
| II. User data safety | Read-only checks (`isreadonly=True`); write tests on copies; backups in `_backup_20261104_2026r1/` - PASS |
| III. Single source of defaults | Machine config only (`config.yaml`), no template change - PASS |
| IV. Rules in guides | No usage rule change yet; guides/README/CLAUDE.md updated in step 10 - PASS |
| V. Regression before release | Required before 0.5.0 (step 10) - PENDING |
| VI. Windows & encoding | UTF-8 files, no PowerShell rewrite - PASS |
| Technical Constraints "Target AEDT 2025 R2" | **Deviation (justified)**: this feature changes the target to 2026 R1; constitution amendment by owner via `/speckit-constitution` at release |

## Project Structure

```text
aedt_copilot/
├── aedt_env.py            NEW  resolver + ensure + open_edb + siwave_exe + child_env
├── __main__.py            ensure() first
├── cut_board/config.py    default aedt_version
├── cut_board/inspect_board.py  open_edb -> aedt_env
├── cut_board/cutter.py    Edb(...) -> aedt_env.open_edb
├── edit_layout/run.py     _open -> aedt_env.open_edb
└── pi_dc/common.py        siwave_exe -> resolver
mcp_server/server.py       env, --key=value, about text (restart)
config.yaml                aedt_version
```

## Risks

- .NET backend on 2026.1 emits `DOTNET_USAGE_WARNING`; EDB .NET DLL in v261 must load.
- Files saved by 2026 R1 do not open in 2025 R2 (cut output, layout_edit copy, merge/finish).
- SIwave 2026 R1 scripting (`Scr*`, report env vars, colour bar OCR) untested.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Target AEDT 2026 R1 vs constitution 2025 R2 | Team moves to 2026 R1 | Staying on 2025 R2 blocks the team |
