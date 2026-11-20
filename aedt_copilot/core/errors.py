"""Lỗi dùng chung (contract: core-errors.md)."""

MISSING = object()


class CopilotInputError(ValueError):
    """Đầu vào sai của một hàm public. Thông điệp: '<name>: expected <expected>, got <got!r>'."""

    def __init__(self, name, expected, got=MISSING):
        if not isinstance(name, str) or not name.strip():
            raise TypeError("CopilotInputError: name phải là chuỗi khác rỗng")
        if not isinstance(expected, str) or not expected.strip():
            raise TypeError("CopilotInputError: expected phải là chuỗi khác rỗng")
        self.name, self.expected, self.got = name, expected, got
        msg = f"{name}: expected {expected}"
        if got is not MISSING:
            msg += f", got {got!r}"
        super().__init__(msg)


class RegistryError(RuntimeError):
    """Package registry sai cấu trúc (trùng NAME, thiếu thuộc tính, lỗi import)."""
