"""Layout snapshot (feature 023): đọc board MỘT lần ra file (chỉ mục board + hình học cửa sổ), review chạy trên đó.

Hai tầng (contract: specs/023-layout-snapshot/contracts/layout-snapshot.md):
  index   stackup, net, linh kiện, mọi via/pin, metadata mọi primitive, diện tích GND lớn nhất mỗi lớp (toàn board)
  window  outline + void của primitive trong cửa sổ (WKB), trace, backdrill, bbox pin
facade.SnapEdb trả lời đúng các thuộc tính PyEDB mà code review đọc -> cut_board/review.py chạy KHÔNG đổi.
Đơn vị trong file: mét (như EDB) để kết quả giống hệt.
"""

SCHEMA_VERSION = 2                 # 029: + điểm gốc EDB (có cung), bảng padstack gốc, khung linh kiện


class SnapshotMissing(BaseException):
    """Snapshot thiếu dữ liệu được hỏi. BaseException để `except Exception` trong code đo không nuốt mất."""


class SnapshotFallback(Exception):
    """Snapshot không dùng được cho review (vd primitive không chuyển được) -> chạy live + cảnh báo."""

    def __init__(self, reason, ids=()):
        super().__init__(reason)
        self.reason, self.ids = reason, list(ids)
