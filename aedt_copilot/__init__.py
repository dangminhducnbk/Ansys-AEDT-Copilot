"""Ansys AEDT Copilot - công cụ tự động hoá Ansys AEDT (module: cut_board)."""
import os

_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    with open(os.path.join(_here, "VERSION"), encoding="utf-8") as _f:
        __version__ = _f.read().strip()
except OSError:
    __version__ = "0.0.0"
