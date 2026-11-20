"""File của snapshot (feature 023): index.json, window.json + geom.wkb, snapshot.json, khoá build.

read_* trả None khi thiếu / hỏng / khác schema / khác khoá (= cũ -> build lại).
Khoá build: file .build.lock của CHÍNH tool (O_EXCL, pid + giờ); người sau chờ; chỉ xoá lock của mình hoặc lock của
pid đã chết. Không bao giờ đụng tới .lock của AEDT.
"""
import contextlib
import json
import os
import struct
import time

from . import SCHEMA_VERSION

INDEX, WINDOW, GEOM, REPORT, LOCK = "index.json", "window.json", "geom.wkb", "snapshot.json", ".build.lock"


def _wjson(path, data):
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    os.replace(tmp, path)


def _rjson(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def write_index(folder, index):
    os.makedirs(folder, exist_ok=True)
    _wjson(os.path.join(folder, INDEX), index)


def read_index(folder, key):
    d = _rjson(os.path.join(folder, INDEX))
    if not d or d.get("schema_version") != SCHEMA_VERSION or d.get("kind") != "index" or d.get("key") != key:
        return None
    return d


# ----------------------------------------------------------------------------- WKB records
def pack(blobs):
    """[bytes] -> (bytes, [(off, len)]) - bản ghi nối liền, offset lưu trong window.json."""
    out, refs, off = [], [], 0
    for b in blobs:
        out.append(struct.pack("<I", len(b)) + b)
        refs.append((off + 4, len(b)))
        off += 4 + len(b)
    return b"".join(out), refs


def write_window(folder, window, geom):
    os.makedirs(folder, exist_ok=True)
    tmp = os.path.join(folder, GEOM + ".part")
    with open(tmp, "wb") as f:
        f.write(geom)
    os.replace(tmp, os.path.join(folder, GEOM))
    _wjson(os.path.join(folder, WINDOW), window)          # window.json ghi SAU geom: có window.json = đủ file


def read_window(folder, index_key):
    d = _rjson(os.path.join(folder, WINDOW))
    if not d or d.get("schema_version") != SCHEMA_VERSION or d.get("kind") != "window" or d.get("index_key") != index_key:
        return None
    try:
        with open(os.path.join(folder, GEOM), "rb") as f:
            geom = f.read()
    except OSError:
        return None
    if len(geom) != d.get("geom_bytes"):
        return None
    return d, geom


def write_report(folder, report):
    _wjson(os.path.join(folder, REPORT), report)


def read_report(folder):
    return _rjson(os.path.join(folder, REPORT))


def windows(folder):
    """Thư mục cửa sổ con của một index (tên w_*)."""
    try:
        return [os.path.join(folder, n) for n in sorted(os.listdir(folder)) if n.startswith("w_")]
    except OSError:
        return []


def folder_mb(folder):
    n = 0
    for dp, _, fs in os.walk(folder):
        for f in fs:
            try:
                n += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return round(n / 1e6, 2)


# ----------------------------------------------------------------------------- build lock
def _alive(pid):
    if pid == os.getpid():
        return True
    try:
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))       # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return bool(ok) and code.value == 259                                  # STILL_ACTIVE
    except Exception:
        try:
            os.kill(int(pid), 0)
            return True
        except Exception:
            return False


@contextlib.contextmanager
def build_lock(folder, wait_s=600, poll_s=1.0, log=None):
    """Giữ .build.lock trong folder; lock của pid khác còn sống -> chờ (tối đa wait_s) rồi TimeoutError."""
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, LOCK)
    t0, said = time.time(), False
    while True:
        try:
            fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as f:
                f.write(json.dumps({"pid": os.getpid(), "time": time.time()}))
            break
        except FileExistsError:
            d = _rjson(p) or {}
            if d.get("pid") and not _alive(d["pid"]):
                with contextlib.suppress(OSError):
                    os.remove(p)                               # lock của tool, tiến trình đã chết
                continue
            if time.time() - t0 > wait_s:
                raise TimeoutError(f"snapshot build lock held by pid {d.get('pid')}: {p}")
            if log and not said:
                log(f"[snapshot] waiting for another build ({p})")
                said = True
            time.sleep(poll_s)
    try:
        yield p
    finally:
        with contextlib.suppress(OSError):
            os.remove(p)
