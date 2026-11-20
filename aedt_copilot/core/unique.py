"""Tạo thư mục / file / đổi tên không bao giờ trùng (feature 024).

Tên theo giờ (YYYYMMDD_HHMMSS) trùng khi 2 lần chạy bắt đầu cùng 1 giây. Hàm ở đây giữ tên cũ khi không trùng,
trùng thì thêm _2, _3 ... ; việc tạo là nguyên tử (mkdir / O_EXCL) nên 2 tiến trình không bao giờ nhận cùng tên.
Hợp đồng: specs/024-request-id-fix/contracts/unique.md.
"""
import contextlib
import os
import time

from .errors import CopilotInputError

MAX_TRIES = 10000
PERM_GRACE = 2.0           # giây: file_lock coi PermissionError liên tiếp là "đang xoá" (Windows) trong khoảng này


def _check(name, path):
    if not isinstance(path, (str, os.PathLike)) or not str(path).strip():
        raise CopilotInputError(name, "non-empty path", path)
    return os.path.abspath(os.fspath(path))


def candidates(path):
    """path, path_2, path_3 ... (đuôi .aedb / .html giữ ở cuối: X.aedb -> X_2.aedb)."""
    root, ext = os.path.splitext(path)
    if ext and not ext[1:].isalpha():                 # vd. "20261110_104028" không có đuôi thật
        root, ext = path, ""
    yield path
    for k in range(2, MAX_TRIES):
        yield f"{root}_{k}{ext}"


def claim_dir(path):
    """Tạo thư mục mới (nguyên tử). -> đường dẫn tuyệt đối thư mục CHÍNH lần gọi này tạo."""
    path = _check("path", path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for p in candidates(path):
        try:
            os.mkdir(p)
            return p
        except FileExistsError:
            continue
    raise FileExistsError(path)


def claim_file(path):
    """Tạo file rỗng mới (O_EXCL). -> đường dẫn tuyệt đối; người gọi ghi nội dung."""
    path = _check("path", path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for p in candidates(path):
        try:
            os.close(os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return p
        except FileExistsError:
            continue
    raise FileExistsError(path)


def move_aside(src, dst):
    """Đổi tên src -> dst (hoặc dst_2 ...), không bao giờ ghi đè. -> đường dẫn cuối."""
    src, dst = _check("src", src), _check("dst", dst)
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    for p in candidates(dst):
        if os.path.exists(p):
            continue
        try:
            os.rename(src, p)                         # Windows: lỗi nếu p đã có (không ghi đè)
            return p
        except FileExistsError:
            continue
    raise FileExistsError(dst)


@contextlib.contextmanager
def file_lock(path, timeout=30.0, stale=60.0):
    """Khoá loại trừ bằng file (O_EXCL). Khoá cũ hơn `stale` giây (tiến trình chết) bị lấy lại."""
    path = _check("path", path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    t0 = time.monotonic()
    denied = None                                     # lúc bắt đầu chuỗi PermissionError liên tiếp
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except PermissionError:
            # Windows: file khoá chủ trước vừa xoá còn "đang xoá" vài ms -> báo access denied thay vì đã tồn tại.
            # Coi là bận; bị từ chối liên tục > PERM_GRACE giây = lỗi quyền thật -> báo ra.
            now = time.monotonic()
            denied = denied if denied is not None else now
            if now - denied > PERM_GRACE:
                raise
            time.sleep(0.05)
            continue
        except FileExistsError:
            denied = None
            try:
                if time.time() - os.path.getmtime(path) > stale:
                    os.remove(path)                   # khoá của chính tool, chủ đã chết
                    continue
            except OSError:
                continue
            if time.monotonic() - t0 > timeout:
                raise TimeoutError(f"lock busy: {path}")
            time.sleep(0.05)
    try:
        os.write(fd, f"{os.getpid()} {time.time():.3f}".encode())
        os.close(fd)
        yield path
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
