"""Registry: mỗi file = một rule (check / handler / skill), tự tìm trong package (contract: core-registry.md).

Entry = module có NAME (str, duy nhất), ORDER (int, thứ tự chạy), run (callable). File bắt đầu bằng '_' là helper.
Thêm rule mới = thêm một file, không sửa file cũ.
"""
import importlib
import pkgutil
import types

from .errors import CopilotInputError, RegistryError

BASE = ("NAME", "ORDER", "run")


def _package(package):
    if isinstance(package, str):
        try:
            package = importlib.import_module(package)
        except ImportError as ex:
            raise CopilotInputError("package", "importable package", package) from ex
    if not isinstance(package, types.ModuleType) or not hasattr(package, "__path__"):
        raise CopilotInputError("package", "importable package", package)
    return package


def load(package, required=BASE):
    """-> danh sách module entry, sắp theo (ORDER, NAME)."""
    required = tuple(required)
    if not set(BASE) <= set(required):
        raise CopilotInputError("required", "must contain NAME, ORDER, run", required)
    pkg = _package(package)
    entries, seen = [], {}
    for info in sorted(pkgutil.iter_modules(pkg.__path__), key=lambda i: i.name):
        if info.ispkg or info.name.startswith("_"):
            continue
        full = f"{pkg.__name__}.{info.name}"
        try:
            mod = importlib.import_module(full)
        except Exception as ex:
            raise RegistryError(f"{full}: import lỗi: {type(ex).__name__}: {ex}") from ex
        for a in required:
            if not hasattr(mod, a):
                raise RegistryError(f"{full}: missing {a}")
        if not isinstance(mod.NAME, str) or not mod.NAME.strip():
            raise RegistryError(f"{full}: NAME must be non-empty str")
        if isinstance(mod.ORDER, bool) or not isinstance(mod.ORDER, int):
            raise RegistryError(f"{full}: ORDER must be int")
        if not callable(mod.run):
            raise RegistryError(f"{full}: run must be callable")
        if mod.NAME in seen:
            raise RegistryError(f"{pkg.__name__}: duplicate NAME '{mod.NAME}' in {seen[mod.NAME]} and {full}")
        seen[mod.NAME] = full
        entries.append(mod)
    return sorted(entries, key=lambda m: (m.ORDER, m.NAME))


def by_name(entries):
    out = {}
    for m in entries:
        if m.NAME in out:
            raise RegistryError(f"duplicate NAME '{m.NAME}' in {out[m.NAME].__name__} and {m.__name__}")
        out[m.NAME] = m
    return out
