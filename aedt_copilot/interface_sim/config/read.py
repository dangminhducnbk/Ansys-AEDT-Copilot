"""038: find the config page the user saved (request folder, or the browser's download folder)."""
import glob
import os

from ...core.errors import CopilotInputError
from . import page


def downloads_dir():
    return os.path.join(os.path.expanduser("~"), "Downloads")


def candidates(folder, downloads=None):
    """<request>/config.html + <downloads>/config*.html (browser fallback, 'config (1).html' ...)."""
    out = [os.path.join(folder, "config.html")]
    d = downloads if downloads is not None else downloads_dir()
    if d and os.path.isdir(d):
        out += sorted(glob.glob(os.path.join(d, "config*.html")))
    return [p for p in out if os.path.isfile(p)]


def find_saved(request_id, folder, downloads=None):
    """Newest saved page of this request -> {path, state, data, saved_at}; None when the user has not saved one."""
    if not request_id:
        raise CopilotInputError("request_id", "request id", request_id)
    if not os.path.isdir(folder):
        raise CopilotInputError("folder", "existing request folder", folder)
    best = None
    for p in candidates(folder, downloads):
        try:
            rid, st, data = page.read_file(p)
        except (CopilotInputError, OSError, UnicodeDecodeError):
            continue
        if rid != request_id or not st.get("saved_at"):
            continue
        if best is None or str(st["saved_at"]) > str(best["saved_at"]):
            best = {"path": p, "state": st, "data": data, "saved_at": st["saved_at"]}
    return best
