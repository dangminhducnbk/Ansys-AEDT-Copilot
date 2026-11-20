@echo off
setlocal
rem Cai dat aedt_copilot tren may nay (chay 1 lan; chay lai khi requirements doi hoac doi cho thu muc repo).
set "HERE=%~dp0"
set "HERE=%HERE:~0,-1%"
echo == aedt_copilot: %HERE%

rem AEDT: uu tien 2026 R1, sau do 2025 R2 (fallback).
set "AEDT_VER="
if not "%ANSYSEM_ROOT261%"=="" (
  set "AEDT_VER=2026.1"
  echo [ok] AEDT 2026.1: %ANSYSEM_ROOT261%
) else if not "%ANSYSEM_ROOT252%"=="" (
  set "AEDT_VER=2025.2"
  echo [ok] AEDT 2025.2: %ANSYSEM_ROOT252% - khong thay 2026 R1, dung 2025 R2
) else (
  echo [!] Khong thay ANSYSEM_ROOT261 / ANSYSEM_ROOT252 - kiem tra Ansys AEDT 2026 R1 da cai chua.
)

where py >nul 2>nul && (set "PY=py -3") || (set "PY=python")
if not exist "%HERE%\.venv\Scripts\python.exe" (
  echo == Tao .venv
  %PY% -m venv "%HERE%\.venv" || goto :err
)
"%HERE%\.venv\Scripts\python.exe" -m pip install --upgrade pip || goto :err
"%HERE%\.venv\Scripts\python.exe" -m pip install -r "%HERE%\requirements.txt" || goto :err

if not "%AEDT_VER%"=="" (
  "%HERE%\.venv\Scripts\python.exe" "%HERE%\tools\set_aedt_version.py" %AEDT_VER% || goto :err
)

setx AEDT_COPILOT_HOME "%HERE%" >nul
echo [ok] Da dat AEDT_COPILOT_HOME=%HERE%

echo == Kiem tra
"%HERE%\.venv\Scripts\python.exe" -c "import pyedb, ansys.aedt.core, openpyxl, yaml, mcp; print('pyedb', pyedb.__version__)" || goto :err
echo == Dang ky MCP server aedt_copilot voi Claude desktop
"%HERE%\.venv\Scripts\python.exe" "%HERE%\tools\register_claude.py" --client code || goto :err
"%HERE%\.venv\Scripts\python.exe" "%HERE%\tools\register_claude.py" --client desktop || (
  echo [!] Claude desktop chua dang ky ^(app dang chay^). Thoat han Claude desktop roi chay:
  echo     "%HERE%\.venv\Scripts\python.exe" "%HERE%\tools\register_claude.py" --client desktop
)
echo.
echo Xong. Huong dan day du: INSTALL.md. Client MCP khac: python tools\register_claude.py --print
echo Claude Code: mo session moi. Claude desktop: thoat han roi mo lai; menu "+" co prompt interface-sim, copilot-help...
exit /b 0
:err
echo [LOI] Cai dat that bai.
exit /b 1
