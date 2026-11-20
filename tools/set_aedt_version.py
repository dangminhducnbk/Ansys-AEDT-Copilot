"""Ghi aedt_version vào config.yaml (giữ nguyên comment). Gọi từ setup.bat: python tools/set_aedt_version.py 2026.1"""
import os
import re
import sys


def main(version):
    if not re.fullmatch(r"\d{4}\.\d", version):
        print(f"[LOI] version khong hop le: {version!r} (vd 2026.1)")
        return 1
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new, n = re.subn(r'(?m)^aedt_version:.*$', f'aedt_version: "{version}"', text)
    if not n:
        new = f'aedt_version: "{version}"\n' + text
    if new != text:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    print(f"[ok] config.yaml aedt_version = {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ""))
