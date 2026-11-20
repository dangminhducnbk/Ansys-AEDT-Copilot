"""040: local save service of the config page (contract: specs/040-config-save-in-place/contracts/config-save.md).

The tool serves `<request>/config.html` at http://127.0.0.1:<port>/r/<request_id>/<token>/ ; Save on that page POSTs
the page state (JSON) and the service rebuilds the page (data block of the file on disk + new state) and replaces the
file. The path always comes from the request registry, never from the page. One detached service per PC
(`python -m aedt_copilot config-serve`), started on demand by isim_config, exits after IDLE_S without requests.
"""
import datetime as dt
import json
import os
import re
import secrets
import subprocess
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ...core.errors import CopilotInputError
from .. import request as R
from . import model as M, page

SERVICE = "aedt_copilot config"
PAGE = "config.html"
TOKEN_FILE = "config_token"
DEFAULT_PORT = 17880
PORT_TRIES = 10
IDLE_S = 8 * 3600
MAX_BODY = 5 * 1024 * 1024
_HEX32 = re.compile(r"[0-9a-f]{32}")
_RID = re.compile(r"[A-Za-z0-9_.\-]+")
_LOCK = threading.Lock()
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # never through a system proxy


class SaveError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status, self.message = status, message


def state_file():
    return os.path.join(os.path.expanduser("~"), ".aedt_copilot", "config_service.json")


def _version():
    from ... import __version__
    return __version__


def _registry():
    """Request registry this process reads (a service started by a test with another registry is not reused)."""
    return os.path.normcase(os.path.abspath(R._registry_file()))


def _same(h):
    return isinstance(h, dict) and h.get("version") == _version() and h.get("registry") == _registry()


def _utc_now():
    """Same form as the page's own saved_at (JS toISOString) so read.find_saved compares like with like."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ----------------------------------------------------------------------------- request side (pure-ish)
def token_for(req):
    """32 hex, created once per request in <work>/config_token."""
    p = os.path.join(R.work_dir(req), TOKEN_FILE)
    try:
        with open(p, encoding="utf-8") as f:
            t = f.read().strip()
        if _HEX32.fullmatch(t):
            return t
    except OSError:
        pass
    t = secrets.token_hex(16)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)
    return t


def page_url(req, port):
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise CopilotInputError("port", "TCP port 1..65535", port)
    return f"http://127.0.0.1:{port}/r/{req['request_id']}/{token_for(req)}/"


def rev(data, state):
    return f"{(data or {}).get('built_at') or ''}|{(state or {}).get('saved_at') or ''}"


def _request(rid, token):
    if not isinstance(rid, str) or not _RID.fullmatch(rid):
        raise SaveError(404, "unknown request")
    try:
        req = R.load(rid)
    except (CopilotInputError, OSError, ValueError):
        raise SaveError(404, f"unknown request {rid}") from None
    if req.get("request_id") != rid:
        raise SaveError(404, f"unknown request {rid}")
    try:
        with open(os.path.join(R.work_dir(req), TOKEN_FILE), encoding="utf-8") as f:
            good = f.read().strip()
    except OSError:
        good = ""
    if not good or not isinstance(token, str) or not secrets.compare_digest(good, token):
        raise SaveError(403, "wrong link (token)")
    path = os.path.join(req["folder"], PAGE)
    if not os.path.isfile(path):
        raise SaveError(404, "no config page in the request folder (run isim_config)")
    return req, path


def page_text(rid, token):
    _, path = _request(rid, token)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _check_state(state, data):
    if not isinstance(state, dict) or not isinstance(state.get("channels"), dict):
        raise SaveError(400, "state {channels{...}} expected")
    names = set(data.get("channels") or {})
    if set(state["channels"]) != names:
        raise SaveError(400, f"channels differ from the page: {sorted(state['channels'])} vs {sorted(names)}")
    errs = []
    for n in sorted(names):
        ch = state["channels"][n]
        if not isinstance(ch, dict):
            raise SaveError(400, f"{n}: channel state must be an object")
        taken = [state["channels"][o].get("folder") for o in sorted(names) if o != n
                 and isinstance(state["channels"][o], dict) and state["channels"][o].get("folder")]
        msg = M.check_folder(ch.get("folder"), taken)
        if msg:
            errs.append(f"{n}: channel folder — {msg}")
    if data.get("review") is not None:                                  # 045: resolutions of the review page
        from . import review_data as RD
        errs += RD.validate_resolutions(state.get("review"), data["review"])
    if errs:
        raise SaveError(400, "; ".join(errs[:20]))


def save_state(rid, token, state, base_rev):
    """Replace <request>/config.html with the page rebuilt from the disk data + state. -> {path, saved_at, rev}."""
    req, path = _request(rid, token)
    with _LOCK:
        try:
            prid, disk_state, data = page.read_file(path)
        except (CopilotInputError, OSError, UnicodeDecodeError) as ex:
            raise SaveError(409, f"config page on disk unreadable: {ex}") from None
        if prid != req["request_id"]:
            raise SaveError(409, "config page belongs to another request")
        if data.get("readonly"):
            raise SaveError(409, "read-only page (channel already cut)")
        if rev(data, disk_state) != str(base_rev or ""):
            raise SaveError(409, "a newer version of the page is on disk — reload the page")
        _check_state(state, data)
        st = dict(state, saved_at=_utc_now())
        try:
            text = page.build(data, st)
        except CopilotInputError as ex:
            raise SaveError(400, str(ex)) from None
        tmp = f"{path}.tmp{os.getpid()}"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    return {"path": path, "saved_at": st["saved_at"], "rev": rev(data, st)}


# ----------------------------------------------------------------------------- HTTP
class _Handler(BaseHTTPRequestHandler):
    server_version = "aedt_copilot"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else (json.dumps(body, ensure_ascii=False) if not isinstance(body, str)
                                                     else body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def _host_ok(self):
        """DNS rebinding guard: only 127.0.0.1 / localhost on our port."""
        port = self.server.server_address[1]
        return (self.headers.get("Host") or "") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def _route(self):
        self.server.touch()
        if not self._host_ok():
            self._send(403, {"error": "host"})
            return None
        return self.path.split("?", 1)[0]

    def do_GET(self):
        p = self._route()
        if p is None:
            return
        if p == "/health":
            return self._send(200, {"service": SERVICE, "version": _version(), "pid": os.getpid(),
                                    "registry": _registry()})
        m = re.fullmatch(r"/r/([^/]+)/([^/]+)/(?:config\.html)?", p)
        if not m:
            return self._send(404, {"error": "not found"})
        try:
            return self._send(200, page_text(m.group(1), m.group(2)), "text/html; charset=utf-8")
        except SaveError as ex:
            return self._send(ex.status, {"error": ex.message})

    def _json_body(self):
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
            raise SaveError(415, "JSON body expected")
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > MAX_BODY:
            raise SaveError(400, "body size")
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise SaveError(400, "invalid JSON") from None

    def do_POST(self):
        p = self._route()
        if p is None:
            return
        try:
            if p == "/shutdown":
                body = self._json_body()
                if not secrets.compare_digest(str(body.get("secret") or ""), self.server.secret):
                    raise SaveError(403, "secret")
                self._send(200, {"ok": True})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            m = re.fullmatch(r"/r/([^/]+)/([^/]+)/save", p)
            if not m:
                raise SaveError(404, "not found")
            body = self._json_body()
            if not isinstance(body, dict):
                raise SaveError(400, "object expected")
            return self._send(200, save_state(m.group(1), m.group(2), body.get("state"), body.get("base_rev")))
        except SaveError as ex:
            return self._send(ex.status, {"error": ex.message})


class Service(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port=0, idle_s=IDLE_S):
        super().__init__(("127.0.0.1", port), _Handler)
        self.secret = secrets.token_hex(16)
        self.idle_s, self.last = idle_s, time.monotonic()
        self._stop = threading.Event()
        threading.Thread(target=self._watch, daemon=True).start()

    @property
    def port(self):
        return self.server_address[1]

    def touch(self):
        self.last = time.monotonic()

    def _watch(self):
        while not self._stop.wait(30):
            if time.monotonic() - self.last > self.idle_s:
                self.shutdown()
                return

    def server_close(self):
        self._stop.set()
        super().server_close()


def main(port=DEFAULT_PORT):
    """CLI config-serve: run until idle / shutdown; record port + secret in the state file."""
    srv = Service(int(port))
    rec = {"port": srv.port, "pid": os.getpid(), "version": _version(), "secret": srv.secret, "started": R._now()}
    R.wjson(state_file(), rec)
    try:
        srv.serve_forever()
    finally:
        srv.server_close()
        cur = R._rjson(state_file()) or {}
        if cur.get("pid") == os.getpid():
            try:
                os.remove(state_file())
            except OSError:
                pass
    return 0


# ----------------------------------------------------------------------------- client side (isim_config)
def _health(port, timeout=1.0):
    """-> dict (our service) | 'other' (something else answers) | None (nothing listens)."""
    try:
        with _OPENER.open(f"http://127.0.0.1:{port}/health", timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
        return d if isinstance(d, dict) and d.get("service") == SERVICE else "other"
    except urllib.error.HTTPError:
        return "other"
    except (urllib.error.URLError, OSError, ValueError):
        return None


def _shutdown(rec):
    try:
        rq = urllib.request.Request(f"http://127.0.0.1:{rec['port']}/shutdown",
                                    data=json.dumps({"secret": rec.get("secret") or ""}).encode(),
                                    headers={"Content-Type": "application/json"}, method="POST")
        _OPENER.open(rq, timeout=2).close()
    except (urllib.error.URLError, OSError, KeyError):
        return
    for _ in range(30):
        if _health(rec["port"], 0.3) is None:
            return
        time.sleep(0.1)


def _start(port):
    from ...core.config import ROOT, machine
    from ... import aedt_env
    flags = 0x00000008 | 0x00000200 if os.name == "nt" else 0          # DETACHED_PROCESS | NEW_PROCESS_GROUP
    subprocess.Popen([machine()["python"], "-u", "-m", "aedt_copilot", "config-serve", f"--port={port}"], cwd=ROOT,
                     env=aedt_env.child_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    for _ in range(50):
        h = _health(port, 0.3)
        if isinstance(h, dict):
            return h
        time.sleep(0.1)
    return None


def ensure(log=print):
    """Port of a running service of this tool version (started when needed); None when unavailable."""
    if os.environ.get("AEDT_COPILOT_CONFIG_SERVICE") == "0":
        return None
    rec = R._rjson(state_file()) or {}
    if rec.get("port"):
        h = _health(rec["port"])
        if isinstance(h, dict):
            if _same(h):
                return int(rec["port"])
            log(f"[config] save service {h.get('version')} ({h.get('registry')}) -> restart")
            _shutdown(rec)
    try:
        from ...core.config import machine
        base = int(machine().get("config_port") or DEFAULT_PORT)
    except (ValueError, TypeError):
        base = DEFAULT_PORT
    for p in range(base, base + PORT_TRIES):
        h = _health(p)
        if _same(h):
            return p
        if h is not None:                                               # other program / other version on it
            continue
        if isinstance(_start(p), dict):
            log(f"[config] save service started on 127.0.0.1:{p}")
            return p
    log("[config] save service not available: Save falls back to the browser (038)")
    return None
