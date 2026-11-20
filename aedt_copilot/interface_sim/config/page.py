"""038 config page: build the HTML (assets inlined, data + state as JSON blocks) and parse a saved page (contract:
specs/038-cut-config-html/contracts/config-flow.md). Pure (reads only the package assets)."""
import json
import os
import re

from ...core.errors import CopilotInputError

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
_STATE_RE = re.compile(r'<script type="application/json" id="cfg-state">(.*?)</script>', re.S)
_DATA_RE = re.compile(r'<script type="application/json" id="cfg-data">(.*?)</script>', re.S)
_META_RE = re.compile(r'<meta name="aedt-copilot-request" content="([^"]*)">')


def _asset(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return f.read()


def _json_block(obj):
    """JSON safe inside <script>: no '</' can close the block."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def build(data, state, readonly=False):
    """-> full HTML text. data / state: data-model.md (data['request_id'] required; state['channels'] = data's)."""
    if not isinstance(data, dict) or not data.get("request_id") or not isinstance(data.get("channels"), dict):
        raise CopilotInputError("data", "page data {request_id, channels{...}}", type(data).__name__)
    if not isinstance(state, dict) or set((state.get("channels") or {})) != set(data["channels"]):
        raise CopilotInputError("state", "page state with the same channels as the data",
                                sorted((state or {}).get("channels") or {}))
    rid = str(data["request_id"])
    if '"' in rid or "<" in rid:
        raise CopilotInputError("request_id", "id without quotes / <", rid)
    d = dict(data, readonly=bool(readonly))
    if data.get("review") is not None and not readonly:                 # 045: review + settings on one page
        return _build_review(d, state, rid)
    parts = {"CSS": _asset("page.css"), "JS": _asset("page.js"), "DATA": _json_block(d), "STATE": _json_block(state),
             "REQUEST_ID": rid, "BODY_CLASS": "ro" if readonly else ""}
    # one pass over the template only: text inside the data never gets replaced
    return re.sub(r"__(CSS|JS|DATA|STATE|REQUEST_ID|BODY_CLASS)__", lambda m: parts[m.group(1)], _asset("page.html"))


def config_template(rid):
    """045: the 038 config page with its data / state tokens left in (__DATA__ / __STATE__), escaped for a
    <script type="text/plain"> block: '</script' -> '</scr@@ipt', 'id="cfg-' -> 'id="cfg@@-' (the page's own blocks stay
    the first cfg-data / cfg-state of the file). review.js reverses both before using it as the Settings frame."""
    parts = {"CSS": _asset("page.css"), "JS": _asset("page.js"), "REQUEST_ID": rid, "BODY_CLASS": ""}
    t = re.sub(r"__(CSS|JS|REQUEST_ID|BODY_CLASS)__", lambda m: parts[m.group(1)], _asset("page.html"))
    if "</scr@@ipt" in t or 'id="cfg@@-' in t:
        raise CopilotInputError("assets", "config page without the escape markers", "marker found")
    return re.sub(r"</script", "</scr@@ipt", t, flags=re.I).replace('id="cfg-', 'id="cfg@@-')


def _build_review(d, state, rid):
    rv = d.get("review")
    if not isinstance(rv, dict) or set(rv) != set(d["channels"]):
        raise CopilotInputError("data.review", "review data for every channel of the page",
                                sorted(rv) if isinstance(rv, dict) else type(rv).__name__)
    d = dict(d, kind="review")
    parts = {"CSS": _asset("page.css"), "RCSS": _asset("review.css"), "RJS": _asset("review.js"),
             "DATA": _json_block(d), "STATE": _json_block(state), "REQUEST_ID": rid, "CFGPAGE": config_template(rid)}
    return re.sub(r"__(CSS|RCSS|RJS|DATA|STATE|REQUEST_ID|CFGPAGE)__", lambda m: parts[m.group(1)], _asset("review.html"))


def parse(text):
    """Saved page text -> (request_id, state, data). Missing / broken blocks -> CopilotInputError."""
    m, s, d = _META_RE.search(text or ""), _STATE_RE.search(text or ""), _DATA_RE.search(text or "")
    if not (m and s and d):
        raise CopilotInputError("page", "config page written by isim_config (request meta + data + state blocks)",
                                "blocks missing")
    try:
        return m.group(1), json.loads(s.group(1)), json.loads(d.group(1))
    except ValueError as ex:
        raise CopilotInputError("page", "valid JSON state / data", str(ex)[:120]) from ex


def read_file(path):
    with open(path, encoding="utf-8") as f:
        return parse(f.read())
