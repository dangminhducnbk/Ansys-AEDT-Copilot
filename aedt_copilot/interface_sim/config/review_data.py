"""045 review page data (contract: specs/045-review-resolve-page/contracts/review-page.md). Pure (no EDB).

report_rows       rows / section intros / topology of the review report HTML the tool wrote (033 / 043 structure)
channel_review    review data of one channel for the page (NOT OK points, report rows, stackup)
validate_resolutions / unresolved / carry_over   resolutions saved in the page state (cfg-state.review)
"""
import html as H
import math
import re

from ...core.errors import CopilotInputError

# check title -> family (marker colour, same colours as the 043 frames)
FAM = {"Loss of reference": "ref", "Near plane edge": "ref", "Signal over void (SOV)": "ref",
       "Reference to another net": "ref", "Trace over via clearance": "ref",
       "Via stub": "via", "Nearest GND via": "via", "Reference plane change at a via": "via",
       "Serpentine": "rt", "Pair members split apart": "rt", "Coupling": "rt", "Trace stub": "ts",
       "Width vs stackup": "stk"}
OUTER = ("top layer", "bottom layer")


def _tab_text(text, tab):
    m = re.search(r"<div class='tabp' data-t='%d'>(.*?)(?=<div class='tabp' data-t=|<script)" % tab, text, re.S)
    return m.group(1) if m else (text if "<div class='tabp'" not in text else "")


def report_rows(text, tab=1):
    """-> (rows {point id: [{rid, sec, desc, pic}]}, sections {title: intro html}, topo html)."""
    if text is None:
        return {}, {}, ""
    if not isinstance(text, str):
        raise CopilotInputError("text", "review report HTML text", type(text).__name__)
    if not isinstance(tab, int) or isinstance(tab, bool) or tab < 1:
        raise CopilotInputError("tab", "channel tab number >= 1", tab)
    t = _tab_text(text, tab)
    rows, secs, topo = {}, {}, ""
    i = t.find("<h3>Signal routing per pair</h3>")                    # 033 topology boxes, kept as they are
    if i >= 0:
        j = t.find("<p class='lead'>", i)
        topo = t[i:j if j > i else len(t)].replace('class="xs"', 'class="xs2"')
    for part in re.split(r"<h2 id='[^']+'>", t)[1:]:
        hm = re.match(r"(.*?)</h2>", part, re.S)
        if not hm:
            continue
        sec = hm.group(1)
        im = re.search(r"<div class='intro'>(.*?)</div>(?=<h3|<p class='lead'|<table|<div class='leg2'|$)", part, re.S)
        if im:
            secs[sec] = re.sub(r"^<div>This section checks:</div>", "", im.group(1))
        for rm in re.finditer(r"<tr id='t\d+-r-([^']+)'>(.*?)</tr>(?=<tr id=|</tbody>)", part, re.S):
            rid, body = rm.group(1), rm.group(2)
            tds = re.match(r"<td>.*?</td><td>.*?</td><td>(.*?)</td><td class='pic'>(.*)</td>$", body, re.S)
            if not tds:
                continue
            desc = tds.group(1).replace("class='iss'", "class='iss2'")
            pic = tds.group(2).replace("class='loc'", "class='loc2'")
            for pid in dict.fromkeys(re.findall(r"point #([\d.]+)", desc)):
                rows.setdefault(pid, []).append({"rid": rid, "sec": sec, "desc": desc, "pic": pic})
    return rows, secs, topo


def _strip(h):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()


def _issue_rec(rows, check):
    """Issue / Recommendation sentences of the report row(s) of this check (title 'check <name>; point #...')."""
    for r in rows:
        for blk in re.findall(r"<div class='iss2'[^>]*title='([^']*)'[^>]*>(.*?)</div></div>", r["desc"], re.S) or []:
            title, body = blk
            if f"check {check};" not in H.unescape(title) + ";":
                continue
            iss = re.search(r"<b>Issue:</b>(.*?)</div>", body, re.S)
            rec = re.search(r"<b>Recommendation:</b>(.*?)(?:</div>|$)", body, re.S)
            return _strip(iss.group(1)) if iss else "", _strip(rec.group(1)) if rec else ""
    return "", ""


def channel_review(doc, report_text, stackup=None, layer_order=None, tab=1):
    """review.json (one channel) + its report -> ReviewData (data-model.md)."""
    if not isinstance(doc, dict) or not doc.get("channels"):
        raise CopilotInputError("review", "review.json with one channel", type(doc).__name__)
    if not doc.get("measured_at"):
        raise CopilotInputError("review.measured_at", "measured review", None)
    ch = doc["channels"][0]
    order = list(layer_order or [])
    rows, secs, topo = report_rows(report_text, tab)
    items = [i for i in ch.get("items") or [] if i.get("status") == "NOT OK"]
    pts = []
    for p in ch.get("points") or []:
        if p.get("status") != "NOT OK":
            continue
        rep = rows.get(str(p["id"]), [])
        its = []
        for it in (i for i in items if str(i.get("point")) == str(p["id"])):
            lay = str(it.get("layer") or "")
            inv = [lay] if lay in order else []
            inv += [x.strip() for x in str(it.get("ref") or "").split(",") if x.strip()]
            inv += list(it.get("used_layers") or [])
            if " → " in lay:
                inv += lay.split(" → ")
            iss, rec = _issue_rec(rep, it.get("check", ""))
            its.append({"id": it.get("id"), "check": it.get("check", ""), "fam": FAM.get(it.get("check"), "rt"),
                        "value": str(it.get("value") or ""), "net": it.get("net", ""), "layer": lay,
                        "ref": str(it.get("ref") or ""), "used": list(it.get("used_layers") or []),
                        "issue": iss or str(it.get("value") or ""), "rec": rec, "inv": list(dict.fromkeys(inv))})
        act = next((x for i in its for x in ([i["layer"]] + i["used"][::-1])
                    if x in order and x.lower() not in OUTER), None) or (its[0]["inv"][0] if its and its[0]["inv"]
                                                                        else None)
        pts.append({"id": str(p["id"]), "net": p.get("net", ""), "x": float(p.get("x_mm") or 0.0),
                    "y": float(p.get("y_mm") or 0.0), "items": its, "act": act, "rep": rep,
                    "inv": list(dict.fromkeys(x for i in its for x in i["inv"]))})
    return {"measured_at": doc["measured_at"], "review_html": doc.get("html") or "", "points": pts,
            "sections": secs, "topo": topo, "stackup": list(stackup or [])}


# ----------------------------------------------------------------------------- resolutions (cfg-state.review)
_RES_KEYS = {"check": str, "net": str, "time": str, "note": str}


def validate_resolutions(state_review, data_review):
    """Shape of cfg-state.review vs the page data. -> [error text] ([] = ok)."""
    if state_review is None:
        return []
    if not isinstance(state_review, dict):
        return ["review: object {channel: {measured_at, resolved}} expected"]
    errs = []
    for n, r in state_review.items():
        if n not in (data_review or {}):
            errs.append(f"review: unknown channel {n}")
            continue
        if not isinstance(r, dict) or not isinstance(r.get("resolved", {}), dict):
            errs.append(f"review.{n}: {{measured_at, resolved{{}}}} expected")
            continue
        ids = {p["id"] for p in data_review[n].get("points") or []}
        for pid, x in r.get("resolved", {}).items():
            if pid not in ids:
                errs.append(f"review.{n}: point {pid} is not a NOT OK point of the page")
            elif not isinstance(x, dict) or any(k in x and not isinstance(x[k], t) for k, t in _RES_KEYS.items()):
                errs.append(f"review.{n}.{pid}: resolution {{check, net, time, note}} expected")
    return errs


def unresolved(state, data):
    """-> {channel: [point id]} of points not resolved for the CURRENT review of the page data."""
    out = {}
    rv = (data or {}).get("review") or {}
    sr = (state or {}).get("review") or {}
    for n, d in rv.items():
        s = sr.get(n) or {}
        same = s.get("measured_at") == d.get("measured_at")
        res = (s.get("resolved") or {}) if same else {}
        left = [p["id"] for p in d.get("points") or [] if p["id"] not in res]
        if left:
            out[n] = left
    return out


def carry_over(old_review, data_review, tol_mm=0.01):
    """Resolutions of the page state kept for the current reviews: same measurement -> kept; older measurement ->
    matching check + net + location (<= tol_mm) carried with carried=true. -> (new state review, carried count)."""
    out, carried = {}, 0
    for n, d in (data_review or {}).items():
        old = (old_review or {}).get(n) or {}
        res = old.get("resolved") or {}
        if old.get("measured_at") == d.get("measured_at"):
            out[n] = {"measured_at": d["measured_at"], "resolved": dict(res)}
            continue
        new = {}
        for p in d.get("points") or []:
            checks = "+".join(i["check"] for i in p["items"])
            for x in res.values():
                if (isinstance(x, dict) and x.get("check") == checks and x.get("net") == p["net"]
                        and math.hypot(float(x.get("x", 1e9)) - p["x"], float(x.get("y", 1e9)) - p["y"]) <= tol_mm):
                    new[p["id"]] = dict(x, carried=True)
                    carried += 1
                    break
        out[n] = {"measured_at": d["measured_at"], "resolved": new}
    return out, carried
