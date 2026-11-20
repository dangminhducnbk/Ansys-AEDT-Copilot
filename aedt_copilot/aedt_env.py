"""Tìm bản cài Ansys AEDT và đưa cho pyedb / pyaedt / SIwave (không phụ thuộc biến môi trường của tiến trình cha).

Thứ tự tìm: config.yaml `aedt_root` -> biến ANSYSEM_ROOT### -> registry Windows -> quét
C:\\Program Files\\ANSYS Inc\\v###\\AnsysEM. Phiên bản: config.yaml `aedt_version` ("2026.1", "2025.2" hoặc "auto" = mới nhất).

ensure() PHẢI chạy TRƯỚC `import pyedb` / `import ansys.aedt.core`: pyedb đọc ANSYSEM_ROOT### đúng một lần lúc import.
Module này không import pyedb ở mức module (server.py import được mà không nạp .NET).
"""
import glob
import os
import re

SCAN_GLOB = r"C:\Program Files\ANSYS Inc\v[0-9][0-9][0-9]\AnsysEM"
REG_BASES = (r"SOFTWARE\Ansoft\ElectronicsDesktop", r"SOFTWARE\WOW6432Node\Ansoft\ElectronicsDesktop")
REG_VALUES = ("InstallationDirectory", "InstallDir", "InstallPath")
_STATE = {}          # version -> {"version", "root", "source", "env_var"}
_LAST = {}           # bản ensure() gần nhất (mặc định của tiến trình)
_ENV_ADDED = {}      # biến lấy từ môi trường Windows đã lưu (registry) vì tiến trình cha không truyền
# Biến Ansys/license cần cho EDB/AEDT/SIwave. Claude desktop có thể spawn MCP server với env thiếu các biến hệ thống.
_ENV_RE = re.compile(r"^(ANSYSEM_ROOT\d{3}|ANSYSEM_PY_CLIENT_ROOT\d{3}|AWP_ROOT\d{3}|ANSYSLMD_LICENSE_FILE|"
                     r"ANSYSLI_SERVERS|ANSYSLIC_DIR|ANS_FLEXLM_DISABLE_DEFLICPATH|ANSYSCL\d{3}_DIR)$", re.I)


def _windows_env():
    """Biến môi trường đã lưu của Windows (HKLM System rồi HKCU User đè lên). Chỉ đọc."""
    out = {}
    try:
        import winreg
    except ImportError:
        return out
    for hive, path in ((winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                       (winreg.HKEY_CURRENT_USER, "Environment")):
        try:
            with winreg.OpenKey(hive, path) as k:
                i = 0
                while True:
                    try:
                        name, val, typ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    i += 1
                    if isinstance(val, str):
                        out[name] = os.path.expandvars(val) if typ == winreg.REG_EXPAND_SZ else val
        except OSError:
            continue
    return out


def sync_env():
    """Thêm vào os.environ các biến Ansys/license có trong env Windows đã lưu mà tiến trình này thiếu. Trả {tên: giá trị}."""
    if "_done" not in _ENV_ADDED:
        _ENV_ADDED["_done"] = True
        try:
            for k, v in _windows_env().items():
                if _ENV_RE.match(k) and v and k.upper() not in {x.upper() for x in os.environ}:
                    os.environ[k] = v
                    _ENV_ADDED[k] = v
        except Exception:
            pass
    return {k: v for k, v in _ENV_ADDED.items() if k != "_done"}


def vid(version):
    """'2026.1' -> '261'."""
    v = str(version).strip()
    if re.fullmatch(r"\d{3}", v):
        return v
    m = re.fullmatch(r"20(\d\d)\.(\d)", v)
    if not m:
        raise ValueError(f"aedt_version không hợp lệ: '{version}' (dạng 2026.1 hoặc auto)")
    return m.group(1) + m.group(2)


def ver(v3):
    """'261' -> '2026.1'."""
    return f"20{v3[:2]}.{v3[2]}"


def _key(v):
    return tuple(int(x) for x in v.split("."))


def _valid(root):
    return bool(root) and os.path.isfile(os.path.join(root, "ansysedt.exe"))


def _ver_from_path(root):
    m = re.search(r"[\\/]v(\d{3})[\\/]", os.path.normpath(root) + os.sep)
    return ver(m.group(1)) if m else None


def _from_env():
    out = {}
    for k, v in os.environ.items():
        m = re.fullmatch(r"ANSYSEM_ROOT(\d{3})", k)
        if m and _valid(v):
            out[ver(m.group(1))] = (v, f"env:{k}")
    return out


def _from_registry():
    """HKLM\\SOFTWARE\\Ansoft\\ElectronicsDesktop\\<ver>\\... giá trị InstallationDirectory (chỉ đọc)."""
    out = {}
    try:
        import winreg
    except ImportError:
        return out

    def walk(key, path, depth):
        for name in REG_VALUES:
            try:
                d = str(winreg.QueryValueEx(key, name)[0]).rstrip("\\/")
            except OSError:
                continue
            for cand in (d, os.path.dirname(d)):              # có bản ghi ...\AnsysEM\Win64
                if _valid(cand):
                    v = _ver_from_path(cand) or (re.search(r"20\d\d\.\d", path) or [None])[0]
                    if v:
                        out.setdefault(v, (cand, "registry:HKLM\\" + path))
                    break
        if depth <= 0:
            return
        try:
            n = winreg.QueryInfoKey(key)[0]
        except OSError:
            return
        for i in range(n):
            try:
                sub = winreg.EnumKey(key, i)
                with winreg.OpenKey(key, sub) as k2:
                    walk(k2, path + "\\" + sub, depth - 1)
            except OSError:
                continue

    for base in REG_BASES:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as k:
                walk(k, base, 2)
        except OSError:
            continue
        except Exception:
            continue
    return out


def _from_scan():
    out = {}
    for d in glob.glob(SCAN_GLOB):
        v = _ver_from_path(d)
        if v and _valid(d):
            out.setdefault(v, (d, "scan"))
    return out


def installed():
    """{version: (root, source)} - ưu tiên env > registry > scan."""
    found = {}
    for src in (_from_env, _from_registry, _from_scan):
        try:
            for v, rs in src().items():
                found.setdefault(v, rs)
        except Exception:
            pass
    return found


def _machine():
    from .core import config                              # lớp core, không phụ thuộc cut_board
    return config.machine()


def resolve(cfg=None, version=None):
    """-> (version, root, source). version: ép phiên bản (vd tham số hàm); None = theo config."""
    cfg = cfg if cfg is not None else _machine()
    want = str(version or cfg.get("aedt_version") or "auto").strip()
    root = (cfg.get("aedt_root") or "").strip().strip('"')
    if root:
        if not _valid(root):
            raise RuntimeError(f"config.yaml aedt_root không có ansysedt.exe: {root}")
        rv = _ver_from_path(root)
        if want == "auto" and not rv:
            raise RuntimeError(f"aedt_version 'auto' cần aedt_root dạng ...\\v###\\AnsysEM: {root}")
        if want == "auto" or not rv or rv == want:
            return (rv if want == "auto" else want), root, "config:aedt_root"
    found = installed()
    if want == "auto":
        if not found:
            raise RuntimeError("Không tìm thấy Ansys AEDT (env ANSYSEM_ROOT###, registry, C:\\Program Files\\ANSYS Inc).")
        want = max(found, key=_key)
    vid(want)
    if want not in found:
        raise RuntimeError(f"Không thấy AEDT {want}. Đã cài: {sorted(found, key=_key) or 'không có'}. "
                           f"Sửa aedt_version / aedt_root trong config.yaml.")
    r, s = found[want]
    return want, r, s


def ensure(cfg=None, version=None):
    """Đặt ANSYSEM_ROOT<vid> trong tiến trình này (nếu chưa có). Trả info dict. Gọi trước import pyedb/pyaedt."""
    key = version or "_default"
    sync_env()
    if key not in _STATE:
        v, root, src = resolve(cfg, version)
        var = f"ANSYSEM_ROOT{vid(v)}"
        if not _valid(os.environ.get(var, "")):
            os.environ[var] = root
        _STATE[key] = {"version": v, "root": os.environ[var], "source": src, "env_var": var}
        if version is None:
            _LAST.update(_STATE[key])
    return dict(_STATE[key])


def info():
    """Thông tin AEDT đã chọn + các bản đã cài (không raise)."""
    try:
        d = ensure()
    except Exception as ex:
        d = {"error": str(ex)}
    try:
        d["installed"] = {v: r for v, (r, _) in sorted(installed().items(), key=lambda kv: _key(kv[0]))}
    except Exception:
        pass
    d["env_added_from_windows"] = sorted(sync_env())
    d["license_env"] = {k: os.environ[k] for k in ("ANSYSLMD_LICENSE_FILE", "ANSYSLI_SERVERS", "ANSYSLIC_DIR")
                        if k in os.environ}
    return d


def child_env(cfg=None):
    """os.environ + ANSYSEM_ROOT<vid> đã chọn (cho subprocess). Không tìm thấy AEDT -> env gốc."""
    env = dict(os.environ)
    try:
        d = ensure(cfg)
        env[d["env_var"]] = d["root"]
    except Exception:
        pass
    env.setdefault("PYTHONUTF8", "1")
    return env


def siwave_exe(version=None):
    d = ensure(version=version)
    exe = os.path.join(d["root"], "siwave.exe")
    if not os.path.exists(exe):
        raise RuntimeError(f"Không thấy siwave.exe: {exe}")
    return exe


def open_edb(path, cell=None, readonly=True, version=None):
    """Mở EDB: luôn version tường minh + grpc=False (code dùng API .NET; pyedb 0.85 mặc định gRPC từ 2026.1)."""
    d = ensure(version=version)
    from pyedb import Edb                                  # import SAU khi đặt env
    kw = dict(edbpath=path, version=d["version"], isreadonly=bool(readonly), grpc=False)
    if cell:
        kw["cellname"] = cell
    return Edb(**kw)
