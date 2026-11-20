"""Bước 2b: đo 2 đầu interface trên thiết kế stage1 (chỉ đọc) + đánh dấu trường hợp lạ (contract: isim-ends.md).

Code chỉ đo và đánh dấu; cách xử lý do người dùng chọn (handling) trong số thao tác đang có.
"""
import fnmatch
import math
import os

from . import report, request as R

OPTIONS = {
    "no_gnd_near_signal": ["smd_rebuild", "keep_component", "stop_interface"],
    "non_round_pad_bga": ["no_solder_ball", "keep_component", "stop_interface"],
    "connector_end": ["keep_component", "smd_rebuild", "no_solder_ball", "stop_interface"],
    "unknown_type": ["keep_component", "smd_rebuild", "stop_interface"],
    "pad_size_mismatch": ["keep_component", "no_solder_ball", "stop_interface"],
    # 015: đầu SMD / connector không có pin GND -> options theo từng trường hợp (gnd_decision.options_for)
    "no_gnd_pin": ["gnd_plate_vias", "gnd_existing_copper", "gnd_keep_pad", "keep_component", "stop_interface",
                   "other"],                                         # 019: gnd_keep_pad
}
OLD_CUT_REASON = "cut before 0.15.0: cut again (isim_cut) to get this option"


def keep_pad_for(s1, rd):
    """019: mục keep_pad cho đầu rd từ stage1 (pad GND ngoài vùng cutout đo lúc cắt trên board gốc)."""
    from ..cut_board import gnd_decision as GD
    if "gnd_pads_outside" not in (s1 or {}):
        return {"offered": False, "reason": OLD_CUT_REASON}
    return GD.keep_pad_entry((s1["gnd_pads_outside"] or {}).get(rd), s1.get("extent_pts_mm"))


def thresholds(P):
    s = P.get("interface_sim", {})
    ch = str(s.get("connector_handling") or "smd_rebuild").strip()
    return {"connector_patterns": s.get("connector_patterns") or ["J*", "CN*", "CON*"],
            "connector_handling": ch if ch in OPTIONS["connector_end"] else "smd_rebuild",
            "round_pad_aspect_max": float(s.get("round_pad_aspect_max") or 1.1),
            "pad_size_tol_pct": float(s.get("pad_size_tol_pct") or 10),
            "gnd_near_smd_mm": float(s.get("gnd_near_smd_mm") or 1.0),
            "gnd_near_bga_mm": float(P.get("cleanup", {}).get("bga_gnd_pin_keep_dist_mm") or 1.6)}


def is_connector(refdes, part, patterns):
    return any(fnmatch.fnmatchcase(refdes.upper(), p.upper()) or fnmatch.fnmatchcase((part or "").upper(), p.upper())
               for p in patterns)


def classify_unusual(end, th):
    """end: dict đo được (data-model End check). Trả [{rule, detail, values, options}]. Thuần."""
    out = []
    sig = end.get("signal_pins") or []

    def add(rule, detail, values):
        out.append({"rule": rule, "detail": detail, "values": values, "options": list(OPTIONS[rule])})
    if end.get("type") == "unknown":
        add("unknown_type", "end type not recognised", {"part": end.get("part")})
    lonely = [p["pin"] for p in sig if not p.get("gnd_near")]
    if end.get("no_gnd"):                                            # 015: thay no_gnd_near_signal, người dùng chọn
        f = end["no_gnd"]
        out.append({"rule": "no_gnd_pin", "detail": f"no GND pin; {f['n_vias']} GND via(s) in body, "
                                                    f"{f['n_copper_vias']} on GND copper",
                    "values": f, "options": list(f["options"]), "omitted": list(f["omitted"])})
    elif lonely:
        add("no_gnd_near_signal", f"{len(lonely)} signal pin(s) without GND pin within "
                                  f"{end.get('gnd_radius_mm')} mm", {"pins": lonely[:20]})
    if end.get("type") == "bga":
        bad = [(p["pin"], p["pad"]["w_mm"], p["pad"]["h_mm"]) for p in sig if p.get("pad") and
               min(p["pad"]["w_mm"], p["pad"]["h_mm"]) > 0 and
               max(p["pad"]["w_mm"], p["pad"]["h_mm"]) / min(p["pad"]["w_mm"], p["pad"]["h_mm"]) >
               th["round_pad_aspect_max"]]
        if bad:
            add("non_round_pad_bga", f"{len(bad)} BGA signal pad(s) not round (aspect > {th['round_pad_aspect_max']})",
                {"pads": bad[:20]})
    sizes = [min(p["pad"]["w_mm"], p["pad"]["h_mm"]) for p in sig if p.get("pad")]
    if len(sizes) >= 2 and min(sizes) > 0 and (max(sizes) - min(sizes)) / min(sizes) * 100 > th["pad_size_tol_pct"]:
        add("pad_size_mismatch", f"signal pad short side {min(sizes)}-{max(sizes)} mm "
                                 f"(> {th['pad_size_tol_pct']} %)", {"min_mm": min(sizes), "max_mm": max(sizes)})
    return out


def default_handling(end, th):
    """012: đầu connector -> cách xử lý mặc định của team (template), không hỏi; kỹ sư đổi được ở Gate B. Thuần."""
    if not end.get("connector"):
        return None
    return {"rule": "connector_end", "value": th.get("connector_handling") or "smd_rebuild",
            "options": list(OPTIONS["connector_end"]), "source": "team default"}


def _measure(edb, rd, nets, refs, bga, th, P=None, body=None, image_dir=None, keep_pad=None):
    """P (015): có P -> đầu không phải BGA / TH, 0 pin GND -> đo + ảnh (image_dir) cho câu hỏi no_gnd_pin.
    keep_pad (019): keep_pad_for(stage1, rd) -> lựa chọn gnd_keep_pad (có / bỏ kèm lý do)."""
    from ..cut_board import inspect_board as IB
    c = edb.components.instances[rd]
    typ = "bga" if bga and "BGA" in (c.partname or "").upper() else IB.end_type(edb, c, set(nets))
    if bga and typ not in ("bga", "through_hole"):
        typ = "bga" if not any(p.start_layer != p.stop_layer for p in c.pins.values() if p.net_name in nets) \
            else "through_hole"
    radius = th["gnd_near_bga_mm"] if typ == "bga" else th["gnd_near_smd_mm"]
    gnd = [(str(p.pin_number or pn), p.position) for pn, p in c.pins.items() if p.net_name in refs]
    sig = []
    for pn, p in c.pins.items():
        if p.net_name not in nets:
            continue
        x, y = p.position
        pad = None
        try:
            (x0, y0), (x1, y1) = p.bounding_box                 # chỉ pin tín hiệu (chậm trên BGA lớn)
            pad = {"w_mm": round((x1 - x0) * 1e3, 3), "h_mm": round((y1 - y0) * 1e3, 3)}
            ar = max(pad["w_mm"], pad["h_mm"]) / max(min(pad["w_mm"], pad["h_mm"]), 1e-9)
            pad["shape"] = "round/square" if ar <= th["round_pad_aspect_max"] else "rect/oval"
        except Exception:
            pass
        near = sorted((round(math.hypot(x - gx, y - gy) * 1e3, 3), g) for g, (gx, gy) in gnd
                      if math.hypot(x - gx, y - gy) * 1e3 <= radius)
        sig.append({"pin": str(p.pin_number or pn), "net": p.net_name, "x_mm": round(x * 1e3, 3),
                    "y_mm": round(y * 1e3, 3), "pad": pad,
                    "gnd_near": [{"pin": g, "dist_mm": dd} for dd, g in near[:4]]})
    sb = None
    for a in ("solder_ball_diameter", "solder_ball_height"):
        try:
            v = getattr(c, a)
            if v:
                sb = sb or {}
                sb[a] = v
        except Exception:
            pass
    end = {"refdes": rd, "part": c.partname, "type": typ, "pins": c.numpins, "gnd_pins": len(gnd),
           "signal_pins": sig, "gnd_radius_mm": radius, "solder_ball": sb,
           "via_in_pad": typ == "smd_via_in_pad",
           "connector": is_connector(rd, c.partname, th["connector_patterns"])}
    if P is not None and not gnd and typ not in ("bga", "through_hole") and sig:
        end["no_gnd"] = no_gnd_finding(edb, P, rd, nets, body, image_dir, keep_pad)
    end["unusual"] = classify_unusual(end, th)
    dh = default_handling(end, th)
    if dh:
        end["default_handling"] = dh
    return end


def no_gnd_finding(edb, P, rd, nets, body=None, image_dir=None, keep_pad=None):
    """015: dữ liệu + ảnh cho câu hỏi đầu không pin GND (cùng tính toán với apply)."""
    from ..cut_board import gnd_decision as GD
    return GD.question(edb, P, rd, nets, body, os.path.join(image_dir, f"gnd_{rd}.png") if image_dir else None,
                       keep_pad=keep_pad)


def check(request_id, name, version=None):
    from ..core.config import machine
    from ..core.edb import edb_session
    from .cut import params_for
    req = R.load(request_id)
    rid = req["request_id"]
    st = R.get_state(rid, name)
    R.require_step(st, "cut")
    s1 = R._rjson(os.path.join(R.iface_dir(rid, name), "stage1.json"))
    P, _ = params_for(st["content"])
    th = thresholds(P)
    refs = set(P["cutout"]["reference_nets"])
    with edb_session(s1["aedb"], s1.get("cell") or name, True, version or machine()["aedt_version"]) as edb:
        d = R.iface_dir(rid, name)
        ends = {rd: _measure(edb, rd, set(s1["nets"]), refs, rd in s1["bga_ends"], th, P=P,
                             body=(s1.get("bodies") or {}).get(rd), image_dir=d, keep_pad=keep_pad_for(s1, rd))
                for rd in s1["ends"]}
    from ..cut_board import end_gnd as EG                                   # 022: luật GND ở 2 đầu
    imgs = EG.images(s1, d)
    for rd, e in ends.items():
        e["end_gnd"] = dict(EG.end_entry(s1, rd), image=imgs.get(rd))
    data = {"ends": ends, "thresholds": th}
    R.wjson(os.path.join(d, "ends.json"), data)
    md = ends_md(name, ends)
    with open(os.path.join(d, "ends.md"), "w", encoding="utf-8") as f:
        f.write(md + "\n")
    R.set_state(rid, name, "ends checked", ends={"ends": {rd: {k: e.get(k) for k in ("type", "unusual",
                                                                                     "default_handling")}
                                                          for rd, e in ends.items()}})
    R.advance(rid, name, "ends_checked")
    from . import settings
    st = R.get_state(rid, name)
    prop = settings.proposal(st, ends)
    dflt = defaults_of(ends)
    out = {"name": name, "step": "ends_checked", "ends": ends, "ends_md": md, "settings_proposal": prop["rows"],
           "settings_md": prop["table_md"] + ("\n\n" + default_md(ends) if dflt else ""),
           "default_handling": dflt,
           "unusual": {rd: [u["rule"] for u in e["unusual"]] for rd, e in ends.items() if e["unusual"]},
           "end_gnd": {rd: e["end_gnd"] for rd, e in ends.items()}, "next": R.NEXT_SETTINGS}
    gq = gnd_questions(ends)
    if gq:                                                                 # 015: hỏi người dùng, không tự chọn
        out["gnd_questions"] = gq
    if st.get("recut_from"):                                               # cut lại (004)
        from . import recut
        hc = recut.compare_handling((st.get("recut_old") or {}).get("handling"), ends)
        out.update(handling_compare=hc, handling_md=recut.handling_md(hc), values=prop.get("values"),
                   dropped=prop.get("dropped"), default_changes=prop.get("default_changes") or [],
                   handling={r["refdes"]: r["old"] for r in hc if r["result"] == "kept"},
                   end_gnd_compare=recut.compare_end_gnd(recut.previous_stage1(st.get("recut_from")), s1))
    return out


def gnd_questions(ends):
    """015: {refdes: {image, question_md, options, omitted, rect_mm}} của đầu không pin GND. Thuần."""
    return {rd: {k: e["no_gnd"].get(k) for k in ("image", "question_md", "options", "omitted", "rect_mm",
                                                 "rect_size_mm", "n_vias", "n_copper_vias", "keep_pad")
                 if k in e["no_gnd"] or k != "keep_pad"}
            for rd, e in (ends or {}).items() if e.get("no_gnd")}


def defaults_of(ends):
    """{refdes: handling mặc định} của các đầu có default_handling (connector)."""
    return {rd: e["default_handling"]["value"] for rd, e in (ends or {}).items() if e.get("default_handling")}


def default_md(ends):
    rows = [[rd, e["default_handling"]["rule"], e["default_handling"]["value"], e["default_handling"]["source"],
             " / ".join(e["default_handling"]["options"])]
            for rd, e in sorted((ends or {}).items()) if e.get("default_handling")]
    return ("## End handling (team default - engineer may change at Gate B)\n" +
            report.table(["Refdes", "Rule", "Handling", "Source", "Options"], rows)) if rows else ""


def ends_md(name, ends):
    rows, un = [], []
    for rd, e in ends.items():
        pads = sorted({p["pad"]["shape"] + f" {p['pad']['w_mm']}x{p['pad']['h_mm']}" for p in e["signal_pins"]
                       if p.get("pad")})
        no_gnd = sum(1 for p in e["signal_pins"] if not p["gnd_near"])
        rows.append([rd, e["part"], e["type"], e["pins"], len(e["signal_pins"]), e["gnd_pins"],
                     f"{no_gnd} without GND <= {e['gnd_radius_mm']} mm", "; ".join(pads[:3]),
                     "yes" if e["solder_ball"] else "", "yes" if e["via_in_pad"] else "",
                     ", ".join(u["rule"] for u in e["unusual"])])
        for u in e["unusual"]:
            un.append([rd, u["rule"], u["detail"], " / ".join(u["options"])])
    md = [f"# Ends of {name}", "", report.table(
        ["Refdes", "Part", "Type", "Pins", "Signal", "GND", "GND near signal", "Signal pads (mm)", "Solder ball",
         "Via-in-pad", "Unusual"], rows), ""]
    if un:
        md += ["## Unusual - engineer chooses handling", report.table(["Refdes", "Rule", "Detail", "Options"], un), ""]
    q = [e["no_gnd"]["question_md"] for e in ends.values() if e.get("no_gnd")]
    if q:
        md += ["## GND decision needed - ask the user (multiple choice), never choose", ""] + [x + "\n" for x in q]
    eg = {rd: e["end_gnd"] for rd, e in ends.items() if e.get("end_gnd")}
    if eg:                                                                  # 022
        from ..cut_board import end_gnd as EG
        md += ["## End GND rule (cut extent) - show before Gate B", report.table(
            EG.HEADER, EG.md_rows(eg, {rd: e.get("image") for rd, e in eg.items()})), ""]
    if default_md(ends):
        md += [default_md(ends), ""]
    return "\n".join(md)
