"""Đăng ký / gỡ MCP server 'aedt_copilot' trong Claude desktop (claude_desktop_config.json).

  python tools/register_claude.py            đăng ký (ghi đè mục aedt_copilot, giữ nguyên các server khác)
  python tools/register_claude.py --remove   gỡ
  --force   ghi cả khi Claude desktop đang chạy (không nên)
  --client desktop|code|all   046: Claude desktop (mặc định), Claude Code (user scope), hoặc cả hai
  --print   in cấu hình server (command / args / env) cho client MCP khác (VS Code, Cursor...), không ghi gì

PHẢI thoát hẳn Claude desktop trước: app giữ config trong bộ nhớ và ghi đè file khi lưu, làm mất mục vừa thêm.

Ghi đường dẫn tuyệt đối (Claude desktop không thay biến môi trường trong config). Sao lưu file cũ thành .bak.
Tìm cả bản cài thường (%APPDATA%\\Claude) và bản Microsoft Store / MSIX
(%LOCALAPPDATA%\\Packages\\Claude_*\\LocalCache\\Roaming\\Claude), và bản MSIX mới
(%LOCALAPPDATA%\\Claude-Data\\claude_*). Giữ nguyên mọi khóa khác (preferences...). Gỡ luôn mục cũ 'ansys_aedt_auto_cut_board'.
"""
import glob
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "aedt_copilot"
OLD = ["ansys_aedt_auto_cut_board"]


def config_dirs():
    out = []
    ad = os.environ.get("APPDATA")
    if ad:
        out.append(os.path.join(ad, "Claude"))
    la = os.environ.get("LOCALAPPDATA")
    if la:
        out += glob.glob(os.path.join(la, "Packages", "Claude_*", "LocalCache", "Roaming", "Claude"))
        # Bản MSIX mới (từ ~2026-10-19) đọc config ở đây, không còn đọc 2 chỗ trên.
        out += glob.glob(os.path.join(la, "Claude-Data", "claude_*"))
    return [d for d in out if os.path.isdir(d)]


def desktop_running():
    """Đường dẫn các tiến trình Claude desktop đang chạy (bỏ qua Claude Code CLI cũng tên claude.exe)."""
    if os.name != "nt":
        return []
    import subprocess
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "Get-Process claude -ErrorAction SilentlyContinue | ForEach-Object { $_.Path }"],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return []
    paths = [p.strip() for p in out.splitlines() if p.strip()]
    return sorted({p for p in paths if "WindowsApps" in p or "AnthropicClaude" in p or "\\Claude\\" in p})


def server_entry():
    """Cấu hình server MCP (đường dẫn tuyệt đối) - dùng chung cho Claude desktop, Claude Code, client MCP khác."""
    py = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    return {"command": py, "args": [os.path.join(ROOT, "mcp_server", "server.py")], "env": {"PYTHONUTF8": "1"}}


def claude_code(remove=False, claude_json=None, use_cli=True):
    """046: Claude Code user scope. CLI `claude mcp add-json ... --scope user` nếu có trên PATH, không thì sửa
    ~/.claude.json (sao lưu .bak, chỉ đổi mcpServers.aedt_copilot, giữ mọi khóa khác). Trả về exit code."""
    import subprocess
    exe = shutil.which("claude") if use_cli and claude_json is None else None
    if exe:
        subprocess.run([exe, "mcp", "remove", NAME, "--scope", "user"], capture_output=True)
        if remove:
            print(f"[ok] Da go {NAME} khoi Claude Code (claude mcp remove)")
            return 0
        r = subprocess.run([exe, "mcp", "add-json", NAME, json.dumps(server_entry()), "--scope", "user"],
                           capture_output=True, text=True)
        if r.returncode:
            print(f"[LOI] claude mcp add-json: {(r.stderr or r.stdout).strip()}")
            return 1
        print(f"[ok] Da dang ky {NAME} cho Claude Code (claude mcp add-json, scope user)")
        return 0
    p = claude_json or os.path.join(os.path.expanduser("~"), ".claude.json")
    cfg = {}
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8-sig") as f:
                cfg = json.load(f)
        except ValueError as ex:
            print(f"[LOI] {p} khong phai JSON hop le ({ex}) - khong ghi.")
            return 1
        if not isinstance(cfg, dict):
            print(f"[LOI] {p} khong phai object JSON - khong ghi.")
            return 1
        shutil.copy2(p, p + ".bak")
    srv = cfg.get("mcpServers")
    if not isinstance(srv, dict):
        srv = cfg["mcpServers"] = {}
    if remove:
        srv.pop(NAME, None)
    else:
        srv[NAME] = dict(server_entry(), type="stdio")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"[ok] {'Da go' if remove else 'Da dang ky'} {NAME} cho Claude Code: {p} (mo session Claude Code moi)")
    return 0


def main(remove=False, force=False):
    run = desktop_running()
    if run and not force:
        print("[LOI] Claude desktop dang chay:")
        for p in run:
            print("      " + p)
        print("      Thoat han Claude (chuot phai icon o khay he thong -> Quit, kiem tra Task Manager) roi chay lai.")
        print("      Neu ghi luc Claude dang chay, Claude se ghi de config va mat muc aedt_copilot.")
        return 2
    entry = server_entry()
    py = entry["command"]
    dirs = config_dirs()
    if not dirs:
        print("[!] Khong thay thu muc cau hinh Claude desktop - cai va mo Claude desktop mot lan roi chay lai.")
        return 1
    for d in dirs:
        p = os.path.join(d, "claude_desktop_config.json")
        cfg = {}
        if os.path.exists(p):
            try:
                with open(p, encoding="utf-8-sig") as f:
                    cfg = json.load(f)
            except ValueError as ex:
                print(f"[LOI] {p} khong phai JSON hop le ({ex}) - sua tay roi chay lai.")
                return 1
            shutil.copy2(p, p + ".bak")
        srv = cfg.setdefault("mcpServers", {})
        for k in OLD:
            srv.pop(k, None)
        if remove:
            srv.pop(NAME, None)
        else:
            srv[NAME] = entry
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        print(f"[ok] {'Da go' if remove else 'Da dang ky'} {NAME}: {p}")
    if not remove and not os.path.exists(py):
        print(f"[!] Chua co {py} - chay setup.bat.")
    print("Gio mo lai Claude desktop. Settings -> Developer phai thay aedt_copilot.")
    return 0


CLIENTS = ("desktop", "code", "all")


def cli(argv):
    """--client desktop|code|all (mặc định desktop = như trước), --print, --remove, --force, --claude-json=<p>."""
    client = "desktop"
    claude_json = None
    for a in argv:
        if a.startswith("--client="):
            client = a.split("=", 1)[1]
        elif a.startswith("--claude-json="):
            claude_json = a.split("=", 1)[1]
    if "--client" in argv:
        i = argv.index("--client")
        client = argv[i + 1] if i + 1 < len(argv) else ""
    if client not in CLIENTS:
        print(f"[LOI] --client phai la mot trong {', '.join(CLIENTS)} (nhan '{client}')")
        return 2
    if "--print" in argv:
        print(json.dumps({"mcpServers": {NAME: server_entry()}}, indent=2, ensure_ascii=False))
        return 0
    remove = "--remove" in argv
    rc = 0
    if client in ("desktop", "all"):
        rc = max(rc, main(remove, "--force" in argv))
    if client in ("code", "all"):
        rc = max(rc, claude_code(remove, claude_json))
    return rc


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
