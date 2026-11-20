"""038: board data of one channel for the config page (READ-ONLY: layout snapshot, live EDB session read-only).

extents  FINAL cut region (AEDT expanded extent + end GND rule 022) for every type x factor 0.02..0.20 (snapshot
         preview, extents cached with the snapshot) - same function as the cut (cutter.cut_extent)
layers   copper of every signal layer in the view (snapshot region, else live) -> SVG paths per net class
ends     pads of the 2 end components (signal, GND kept by the cleanup rules, others), end measurements of
         interface_sim.ends on the source board -> choices (unusual cases, connector handling)
"""
import copy
import math
import time

from ...core.errors import CopilotInputError
from . import model as M

MM = 1e-3
TOL = 0.01                                      # mm, simplify of the picture copper
LABELS = {"gnd_plate_vias": "GND plate under the body + vias", "gnd_existing_copper": "Use existing GND copper",
          "gnd_keep_pad": "Keep the exposed GND pad", "keep_component": "Keep the component as is",
          "stop_interface": "Stop this channel", "smd_rebuild": "Rebuild as SMD (pins at pad, GND plate)",
          "no_solder_ball": "No solder ball"}
RULE_LABELS = {"no_gnd_pin": "End without GND pin", "connector_end": "Connector end",
               "no_gnd_near_signal": "Signal pins without GND pin nearby", "non_round_pad_bga": "BGA pads not round",
               "unknown_type": "End type not recognised", "pad_size_mismatch": "Signal pad sizes differ"}


def _series(content):
    return sorted((content.get("series") or {}).keys())


# ----------------------------------------------------------------------------- extents
def extents(req, content, P, log=print, version=None):
    """{type: {"0.02": [[x, y] mm], ...}} + timings. Snapshot first, live board as fallback."""
    from ...core.edb import aedb_path, edb_session
    from ...cut_board import cutter
    nets, ends = list(content["nets"]), [content["comp_a"], content["comp_b"]]
    comps = ends + [r for r in _series(content) if r not in ends]
    out, t0 = {}, time.perf_counter()
    quiet = (lambda *a, **k: None)
    Q = copy.deepcopy(P)                       # the extent cache reads the type from this dict: change it in place

    def run(edb, ext):
        for typ in M.CUT_TYPES:
            Q["cutout"]["extent_type"] = typ
            out[typ] = {}
            for f in M.FACTORS:
                Q["cutout"]["expansion"] = float(f)
                pts, _ = cutter.cut_extent(edb, Q, nets, ends, quiet, strict=False, extent=ext)
                out[typ][f] = [[round(x, 4), round(y, 4)] for x, y in pts]
            log(f"  extents {typ}: {round(time.perf_counter() - t0, 1)} s")
    src = "snapshot"
    try:
        from ... import layout_snapshot as LS
        from ...layout_snapshot import preview as SP
        with SP.open_for_preview(aedb_path(req["board"]), req.get("cell") or "", Q, nets, comps, version, quiet) as \
                (sedb, ext, _):
            run(sedb, ext)
    except Exception as ex:                                               # SnapshotFallback / Missing / other
        if type(ex).__name__ not in ("SnapshotFallback", "SnapshotMissing"):
            raise
        log(f"  snapshot not used for extents ({ex}); board read live")
        src = "live"
        out.clear()
        with edb_session(req["board"], req.get("cell") or None, True, version) as edb:
            run(edb, None)
    return out, {"source": src, "seconds": round(time.perf_counter() - t0, 1)}


# ----------------------------------------------------------------------------- layers
def _pad_shape(pdef, layer, x, y, rot):
    from shapely import affinity
    from shapely.geometry import Point, box
    d = (pdef or {}).get("pads", {}).get(layer)
    if not d:
        return None
    kind, prm = str(d[0]).lower(), d[1]
    kind = {"1": "circle", "2": "square", "3": "rect", "4": "oval", "5": "oval"}.get(kind, kind)
    try:
        if "circle" in kind and prm:
            return Point(x, y).buffer(prm[0] / 2, 4)
        if ("rect" in kind or "square" in kind) and prm:
            w, h = prm[0], (prm[1] if len(prm) > 1 else prm[0])
            g = box(x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            return affinity.rotate(g, rot, origin=(x, y)) if rot else g
        if ("oval" in kind or "obround" in kind) and prm:
            w, h = prm[0], (prm[1] if len(prm) > 1 else prm[0])
            r = min(w, h) / 2
            g = box(x - w / 2 + r, y - h / 2 + r, x + w / 2 - r, y + h / 2 - r).buffer(r, 3)
            return affinity.rotate(g, rot, origin=(x, y)) if rot else g
    except Exception:
        return None
    return None


def _to_path(g):
    s = []
    for p in ([g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))):
        if p.geom_type != "Polygon" or p.is_empty:
            continue
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)[:-1]
            if len(c) >= 3:
                s.append("M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in c) + "Z")
    return "".join(s)


def view_box(ext):
    """Picture box = bounding box of the largest region (bounding box type, factor 0.20) + 1 mm."""
    pts = (ext.get("bounding_box") or {}).get(M.FACTORS[-1]) or [p for t in ext.values() for v in t.values() for p in v]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1]


def region(req, box, log=print, version=None):
    """extract_region of the box (snapshot, else live) -> region dict (edit_layout format)."""
    from ...core.edb import aedb_path, edb_session
    from ...edit_layout.extract import extract_region
    quiet = (lambda *a, **k: None)
    try:
        from ...layout_snapshot import region as SR
        sedb, _ = SR.open_for_region(aedb_path(req["board"]), req.get("cell") or "", box, True, version, quiet)
        return extract_region(sedb, box, log=quiet), "snapshot"
    except Exception as ex:
        if type(ex).__name__ not in ("SnapshotFallback", "SnapshotMissing"):
            raise
        log(f"  snapshot not used for the layers ({ex}); board read live")
    with edb_session(req["board"], req.get("cell") or None, True, version) as edb:
        return extract_region(edb, box, log=quiet), "live"


def layers(D, nets, refs, rot, box):
    """region dict -> {box, order, routed, layers{layer: {sig, gnd, oth}}} (SVG paths, mm)."""
    from shapely.geometry import Polygon, box as sbox
    from shapely.ops import unary_union
    view = sbox(*box)
    order = list(D["signal_layers"])
    acc = {ln: {"sig": [], "gnd": [], "oth": []} for ln in order}
    routed = set()
    for p in D["prims"]:
        if "poly" not in p or p.get("is_void") or p.get("layer") not in acc:
            continue
        try:
            g = Polygon(p["poly"]).buffer(0)
            for v in p.get("voids") or []:
                if len(v) >= 3:
                    g = g.difference(Polygon(v).buffer(0))
            g = g.intersection(view)
            if g.is_empty:
                continue
        except Exception:
            continue
        cls = "sig" if p.get("net") in nets else "gnd" if p.get("net") in refs else "oth"
        if cls == "sig":
            routed.add(p["layer"])
        acc[p["layer"]][cls].append(g)
    for pid, pdef, net, x, y, sl, el, comp, is_pin in D["instances"]:
        if not net:
            continue
        cls = "sig" if net in nets else "gnd" if net in refs else "oth"
        try:
            a, b = order.index(sl), order.index(el)
        except ValueError:
            continue
        for ln in order[min(a, b):max(a, b) + 1]:
            g = _pad_shape(D["pdefs"].get(pdef), ln, x, y, rot.get(comp, 0.0) if is_pin else 0.0)
            if g is not None:
                acc[ln][cls].append(g)
    out = {ln: {c: _to_path(unary_union(gs).simplify(TOL)) if gs else "" for c, gs in d.items()} for ln, d in acc.items()}
    return {"box": [round(v, 3) for v in box], "order": order, "routed": [ln for ln in order if ln in routed],
            "layers": out}


# ----------------------------------------------------------------------------- ends
def _pad(p, MMx=MM):
    (x0, y0), (x1, y1) = p.bounding_box
    return {"pin": str(p.pin_number), "net": p.net_name, "x": round(p.position[0] / MMx, 4),
            "y": round(p.position[1] / MMx, 4), "box": [round(v / MMx, 4) for v in (x0, y0, x1, y1)]}


def choices_of(rd, end, th):
    """Choice field of one end (FR-034): unusual rules + connector default -> {rule, label, options, default}."""
    rules = [u for u in end.get("unusual") or []]
    dh = end.get("default_handling")
    if not rules and not dh:
        return None
    opts = []
    for u in rules:
        opts += [o for o in u.get("options") or [] if o != "other" and o not in opts]
    if dh:
        opts += [o for o in dh["options"] if o not in opts]
    rule = rules[0]["rule"] if rules else dh["rule"]
    if dh and not rules:
        default = dh["value"]
    elif rule == "no_gnd_pin":
        default = "gnd_plate_vias" if "gnd_plate_vias" in opts else opts[0]
    else:
        default = dh["value"] if dh and dh["value"] in opts else opts[0]
    label = "; ".join(RULE_LABELS.get(u["rule"], u["rule"]) + (f" ({u['detail']})" if u.get("detail") else "")
                      for u in rules) or RULE_LABELS["connector_end"]
    return {"rule": rule, "label": label, "options": opts, "default": default,
            "option_labels": {o: LABELS.get(o, o) for o in opts}}


MAX_END_TRACES = 400


PAD_TOL_MM = 0.02


def _in_box(p, box, tol=PAD_TOL_MM):
    return box[0] - tol <= p[0] <= box[2] + tol and box[1] - tol <= p[1] <= box[3] + tol


def end_traces(paths, layer, frame_mm, pad_boxes=None):
    """041 (FR-008): signal paths on the end's placement layer with a point inside frame_mm (x0, y0, x1, y1) ->
    [{net, w_mm, pts [[x, y] mm], layer, inner}]; arc markers (|v| > 1e100) dropped; at most MAX_END_TRACES.
    044: paths on OTHER layers whose first or last point lies in a signal pad box (mm; via in pad / through-hole pin)
    are kept too, inner = true, via = that end point."""
    x0, y0, x1, y1 = frame_mm
    inside = lambda pts: any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts)     # noqa: E731
    rows = []
    for pth in paths:
        inner = pth.layer_name != layer
        if inner and not pad_boxes:
            continue
        try:
            pts = [(float(a) / MM, float(b) / MM) for a, b in (tuple(q[:2]) for q in pth.center_line)
                   if abs(float(a)) < 1e100 and abs(float(b)) < 1e100]
            w = float(pth.width) / MM
        except Exception:
            continue
        if len(pts) >= 2:
            rows.append((pth.net_name, pth.layer_name, inner, w, pts))
    keep, via_of = [], {}
    for i, (net, lay, inner, w, pts) in enumerate(rows):
        if not inside(pts):
            continue
        if not inner:
            keep.append(i)
            continue
        via = next((q for q in (pts[0], pts[-1]) if any(_in_box(q, b) for b in pad_boxes)), None)
        if via is not None:
            keep.append(i)
            via_of[i] = via
    # 044: an inner trace is usually several path pieces -> follow pieces of the same net / layer joined end to end
    ends = lambda pts: (pts[0], pts[-1])                                            # noqa: E731
    near = lambda a, b: abs(a[0] - b[0]) <= PAD_TOL_MM and abs(a[1] - b[1]) <= PAD_TOL_MM   # noqa: E731
    todo = [i for i in keep if rows[i][2]]
    while todo and len(keep) < MAX_END_TRACES:
        i = todo.pop()
        net, lay, _, _, pts = rows[i]
        for j, (n2, l2, inner2, _, p2) in enumerate(rows):
            if j in keep or not inner2 or n2 != net or l2 != lay or not inside(p2):
                continue
            if any(near(a, b) for a in ends(pts) for b in ends(p2)):
                keep.append(j)
                todo.append(j)
    out = []
    for i in keep[:MAX_END_TRACES]:
        net, lay, inner, w, pts = rows[i]
        t = {"net": net, "w_mm": round(w, 4), "pts": [[round(x, 4), round(y, 4)] for x, y in pts],
             "layer": lay, "inner": inner}
        if i in via_of:
            t["via"] = [round(via_of[i][0], 4), round(via_of[i][1], 4)]
        out.append(t)
    return out


def stackup_rows(edb):
    """045: board stackup for the review page (layer panel + cross-section): [{name, type, material, thickness_um}]."""
    from ...cut_board import stackup_check
    return [{"name": r["name"], "type": "dielectric" if r["type"].lower() == "dielectric" else "signal",
             "material": r["material"], "thickness_um": r["thickness_um"]} for r in stackup_check.read(edb)["layers"]]


def ends_data(req, content, P, comps, log=print, version=None, want_stackup=False):
    """Live read-only session: pads of both ends, choices, rotation of the components in the view
    (+ 045: board stackup when want_stackup -> 4th value)."""
    from ...core.edb import edb_session
    from ...cut_board import cutter
    from .. import ends as EN
    nets, refs = set(content["nets"]), set(P["cutout"]["reference_nets"])
    th = EN.thresholds(P)
    out, choices, rot, paths, stk = {}, {}, {}, None, []
    with edb_session(req["board"], req.get("cell") or None, True, version) as edb:
        if want_stackup:
            try:
                stk = stackup_rows(edb)
            except Exception as ex:                                       # picture only: missing stackup = no panel rows
                log(f"  stackup: {type(ex).__name__}: {ex}")
        for rd in comps:
            try:
                rot[rd] = math.degrees(float(edb.components.instances[rd].rotation))
            except Exception:
                rot[rd] = 0.0
        for rd in (content["comp_a"], content["comp_b"]):
            c = edb.components.instances.get(rd)
            if c is None:
                raise CopilotInputError("comp", "end component on the board", rd)
            pins = list(c.pins.values())
            sig = [p for p in pins if p.net_name in nets]
            gnd = [p for p in pins if p.net_name in refs]
            bga = cutter.is_bga_or_th(c, nets)
            if bga:
                dist = float(P["cleanup"]["bga_gnd_pin_keep_dist_mm"]) * MM
                keep = [g for g in gnd if any(math.hypot(g.position[0] - s.position[0], g.position[1] - s.position[1])
                                              <= dist for s in sig)]
            else:
                keep, _, _ = cutter.prune_own_gnd_pins(P, rd, sig, gnd)
            kept = {id(p) for p in keep}
            other = [p for p in pins if p.net_name not in nets and id(p) not in kept]
            x0, y0, x1, y1 = [v / MM for v in (min(p.position[0] for p in sig + keep),
                                               min(p.position[1] for p in sig + keep),
                                               max(p.position[0] for p in sig + keep),
                                               max(p.position[1] for p in sig + keep))] if sig else (0, 0, 0, 0)
            m = max(x1 - x0, y1 - y0) * .2 + 1.0
            near = [p for p in other if x0 - m <= p.position[0] / MM <= x1 + m and y0 - m <= p.position[1] / MM <= y1 + m]
            spads = [_pad(p) for p in sig]
            no_exit = False
            if not bga:                                                   # 041: the build's pad-end position per pin
                if paths is None:
                    paths = [x for x in edb.layout.paths if x.net_name in nets]
                body = cutter.comp_bbox(c)
                for p, d in zip(sig, spads):
                    pos, how = cutter.port_end(edb, p, c.placement_layer, body, paths)
                    d["port_end"] = [round(v / MM, 4) for v in pos] if pos is not None else None
                    no_exit = no_exit or how != "trace"
                    span, why = cutter.port_span(p, body)                # 041 slider: port travel (body side first)
                    d["port_span"] = [[round(v / MM, 5) for v in q] for q in span] if span else None
                    d["port_how"] = how if span else why
            fr = (x0 - m, y0 - m, x1 + m, y1 + m)
            if paths is None:
                paths = [x for x in edb.layout.paths if x.net_name in nets]
            trs = end_traces(paths, c.placement_layer, fr, [d["box"] for d in spads])   # 044: + inner layers
            out[rd] = {"part": c.partname, "type": str(c.type), "refdes": rd, "layer": c.placement_layer,
                       "bga": bool(bga), "pins_total": len(pins), "pins_cut": len(sig) + len(keep),
                       "no_trace_exit": no_exit, "traces": trs,
                       "signal": spads, "gnd": [_pad(p) for p in keep],
                       "other": [_pad(p) for p in near[:600]]}
            try:
                e = EN._measure(edb, rd, nets, refs, bga, th, P=P)
                ch = choices_of(rd, e, th)
                if ch:
                    choices[rd] = ch
            except Exception as ex:                                       # measurement is advisory for the page
                log(f"  end check {rd} on the board: {type(ex).__name__}: {ex}")
    return (out, choices, rot, stk) if want_stackup else (out, choices, rot)


# ----------------------------------------------------------------------------- one channel
def channel_data(req, content, P, review_html=None, log=print, version=None):
    """Page data of one channel. content = traced / proposed content {comp_a, comp_b, nets, diff_groups, series,
    schematic_diffs}."""
    for k in ("comp_a", "comp_b", "nets"):
        if not content.get(k):
            raise CopilotInputError(f"content.{k}", "traced content (isim_trace)", content.get(k))
    t0 = time.perf_counter()
    refs = list(P["cutout"]["reference_nets"])
    ext, et = extents(req, content, P, log, version)
    box = view_box(ext)
    D, lsrc = region(req, box, log, version)
    comps = sorted(D.get("comps") or {})
    ends, choices, rot, stk = ends_data(req, content, P, comps, log, version, want_stackup=True)
    lay = layers(D, set(content["nets"]), set(refs), rot, box)
    cb = [{"refdes": rd, "box": [round(v, 3) for v in (c.get("bbox") or [0, 0, 0, 0])],
           "end": rd in (content["comp_a"], content["comp_b"])} for rd, c in (D.get("comps") or {}).items()]
    return {"content": {k: content.get(k) for k in ("comp_a", "comp_b", "nets", "diff_groups", "series",
                                                    "schematic_diffs")},
            "ref_nets": refs, "extents": ext, "layers": lay, "comps": [c for c in cb if c["end"]], "ends": ends,
            "choices": choices, "review_html": review_html, "stackup": stk,
            "times": {"extents": et, "layers_source": lsrc, "total_s": round(time.perf_counter() - t0, 1)}}
