"""Kiểm tra đầu vào ở đầu hàm public -> CopilotInputError (contract: core-validate.md)."""
import math
import os
import re

from .errors import CopilotInputError


def _type_names(types):
    types = types if isinstance(types, tuple) else (types,)
    return " or ".join(t.__name__ for t in types)


def require_type(name, value, types):
    types_t = types if isinstance(types, tuple) else (types,)
    if isinstance(value, bool) and bool not in types_t:
        raise CopilotInputError(name, _type_names(types), value)
    if not isinstance(value, types_t):
        raise CopilotInputError(name, _type_names(types), value)
    return value


def _bounds_text(lo, hi, lo_incl, hi_incl):
    parts = []
    if lo is not None:
        parts.append(f"{'>=' if lo_incl else '>'} {lo}")
    if hi is not None:
        parts.append(f"{'<=' if hi_incl else '<'} {hi}")
    return " and ".join(parts)


def require_number(name, value, lo=None, hi=None, lo_incl=True, hi_incl=True):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CopilotInputError(name, "number", value)
    bad = (lo is not None and (value < lo if lo_incl else value <= lo)) or \
          (hi is not None and (value > hi if hi_incl else value >= hi))
    if bad:
        raise CopilotInputError(name, _bounds_text(lo, hi, lo_incl, hi_incl), value)
    return value


def require_int(name, value, lo=None, hi=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise CopilotInputError(name, "integer", value)
    return require_number(name, value, lo, hi)


def require_choice(name, value, choices):
    choices = list(choices)
    if not choices:
        raise TypeError("require_choice: choices rỗng")
    if value not in choices:
        raise CopilotInputError(name, "one of " + ", ".join(str(c) for c in choices), value)
    return value


def require_text(name, value, pattern=None, forbidden=""):
    if not isinstance(value, str) or not value.strip():
        raise CopilotInputError(name, "non-empty text", value)
    v = value.strip()
    if pattern is not None and not re.fullmatch(pattern, v):
        raise CopilotInputError(name, f"text matching {pattern}", value)
    if forbidden and any(c in v for c in forbidden):
        raise CopilotInputError(name, f"text without {forbidden}", value)
    return v


def require_path(name, path, kind="any"):
    require_choice("kind", kind, ("any", "file", "dir"))
    if isinstance(path, os.PathLike):
        path = os.fspath(path)
    if not isinstance(path, str) or not path.strip().strip('"').strip():
        raise CopilotInputError(name, "non-empty path", path)
    p = os.path.abspath(path.strip().strip('"').strip())
    ok = {"any": os.path.exists, "file": os.path.isfile, "dir": os.path.isdir}[kind](p)
    if not ok:
        raise CopilotInputError(name, {"any": "existing path", "file": "existing file", "dir": "existing folder"}[kind], p)
    return p
