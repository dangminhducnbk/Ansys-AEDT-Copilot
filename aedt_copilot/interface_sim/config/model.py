"""038 page state <-> settings of the existing steps (PURE: no EDB / AEDT, no file).

State of one channel (data-model.md):
  folder, cut{template key: text}, nets{net: bool}, diffs{item: board|schematic|drop}, content_note,
  cm{refdes: {die_type, die_orientation, die_height_mm, ball_shape, ball_ratio, ball_height_mm, ball_material,
              port_location, port_pct (041 slider 0-100 %, None for BGA)}},
  setup{mode, freq_ghz, freq_linked, max_passes, max_delta_s, multi[{f, unit, ds}], multi_passes, refine_pct, basis,
        via_mesh_3d, via_sides, delta_zo},
  sweep{type, q3d_dc, rows[{dist, start, end, value}], max_solutions, error_pct, passivity, passivity_tol, causality},
  extents{dielectric_type, dielectric_pad, airbox_type, airbox_pad, z_pos, z_sync, z_neg},
  choices{refdes: option}
Values are the codes the existing code uses (conformal, conforming, mixed, linear_step, flip_chip, ...); the page shows
labels. Frequencies are text with a unit (GHz / MHz / kHz / Hz; a plain number = GHz).
"""
import hashlib
import json
import math
import re

from ...core.errors import CopilotInputError

CUT_TYPES = ("conformal", "convex_hull", "bounding_box")
FACTORS = tuple(f"{0.02 + 0.01 * i:.2f}" for i in range(19))          # slider 0.02 .. 0.20
MODEL_TYPES = ("bounding_box", "conforming", "convex_hull")
BASIS = ("zero", "first", "second", "mixed")
DISTS = ("linear_step", "linear_count", "log_scale")
SWEEP_TYPES = ("interpolation", "discrete")
DIE_TYPES = ("none", "flip_chip", "wire_bond")
ORIENTS = ("chip_down", "chip_up")
SHAPES = ("cylinder", "spheroid", "none")
PORTS = ("end", "centre")
DIFF_CHOICES = ("board", "schematic", "drop")
NAME_BAD = '<>:"/\\|?*; '
STRUCT_PREFIX = ("cutout.",)
STRUCT_KEYS = ("series.keep",)
ADV_PREFIX = ("cutout.", "cleanup.", "series.")                        # rows of the "Advanced" part of the cut frame
MAIN_CUT = ("cutout.extent_type", "cutout.expansion")
UNIT_GHZ = {"ghz": 1.0, "mhz": 1e-3, "khz": 1e-6, "hz": 1e-9}
FRAMES = {"folder": "Channel folder", "cut": "Auto Generate Extent", "content": "Content", "cm": "Component Model",
          "setup": "Analysis Setup", "sweep": "Analysis Setup", "extents": "Set HFSS Model Extents",
          "choices": "Content"}


# ----------------------------------------------------------------------------- small helpers
def ghz(text):
    """'50GHz' / '500 MHz' / '5' -> GHz (float). Empty / wrong -> None."""
    m = re.fullmatch(r"\s*([0-9]*\.?[0-9]+(?:[eE][+-]?\d+)?)\s*(GHz|MHz|kHz|Hz)?\s*", str(text if text is not None else ""),
                     re.I)
    if not m:
        return None
    return float(m.group(1)) * UNIT_GHZ[(m.group(2) or "GHz").lower()]


def num(text):
    try:
        v = float(str(text).strip())
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _int(text):
    v = num(text)
    return int(v) if v is not None and float(v).is_integer() else None


def fmt(v):
    """Number -> short text (0.06 -> '0.06', 30 -> '30')."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return f"{v:g}"
    if isinstance(v, list):
        return ",".join(str(x) for x in v)
    return "" if v is None else str(v)


def adv_rows(rows):
    """Template rows of the cut frame (Advanced part): cutout.* (not the 2 main ones) + cleanup.* + series.*."""
    return [r for r in rows if r["scope"] == "channel" and r["key"].startswith(ADV_PREFIX) and r["key"] not in MAIN_CUT]


def check_folder(name, taken=()):
    """Channel folder name rule (= request.check_name): '' if valid, else the message."""
    n = str(name or "").strip()
    if not n:
        return "Required"
    if any(c in n for c in NAME_BAD) or not n.strip("."):
        return 'No space or < > : " / \\ | ? * ;'
    if n.lower() in {str(t).lower() for t in taken}:
        return "Already used by another channel"
    if n.lower() == "_work":
        return "Reserved name"
    return ""


# ----------------------------------------------------------------------------- defaults
def defaults(P, rows, data_channel):
    """Page state of one channel from the team defaults (P = config.defaults(), rows = template rows)."""
    c = data_channel.get("content") or {}
    sb, cmp_, s, w, a = P["solder_ball"], P["component"], P["setup"], P["sweep"], P["airbox"]
    ends = data_channel.get("ends") or {}
    cm = {rd: {"die_type": cmp_["die_type"], "die_orientation": cmp_["die_orientation"],
               "die_height_mm": fmt(cmp_["die_height_mm"]),
               "ball_shape": sb["shape"] if sb["enable"] else "none", "ball_ratio": fmt(sb["diameter_ratio"]),
               "ball_height_mm": fmt(sb["height_mm"]), "ball_material": sb["material"],
               # 041: via-in-pad / no-trace pads -> centre (what the build did before 041); the user may pick end
               "port_location": "centre" if e.get("bga") or e.get("no_trace_exit") else cmp_["port_location"],
               # 041 slider: 0 % = body side (old end), 50 % = centre; none for BGA (round pads)
               "port_pct": None if e.get("bga") else
               (50 if e.get("no_trace_exit") or cmp_["port_location"] == "centre" else 0)}
          for rd, e in ends.items()}
    return {
        "folder": "",
        "cut": {**{k: fmt(P[k.split(".")[0]][k.split(".", 1)[1]]) for k in MAIN_CUT},
                **{r["key"]: fmt(P[r["key"].split(".")[0]][r["key"].split(".", 1)[1]]) for r in adv_rows(rows)}},
        "nets": {n: True for n in c.get("nets") or []},
        "diffs": {d["item"]: "board" for d in c.get("schematic_diffs") or []},
        "content_note": "",
        "cm": cm,
        "setup": {"mode": s["solution_mode"], "freq_ghz": "", "freq_linked": True, "max_passes": fmt(s["max_passes"]),
                  "max_delta_s": fmt(s["max_delta_s"]), "multi": [], "multi_passes": fmt(s["multi_max_passes"]),
                  "refine_pct": fmt(s["max_refine_per_pass"]), "basis": s["basis_order"],
                  "via_mesh_3d": bool(s["via_mesh_3d"]), "via_sides": fmt(s["via_num_sides"]),
                  "delta_zo": fmt(s["max_delta_zo"])},
        "sweep": {"type": w["type"], "q3d_dc": bool(w["use_q3d_dc"]),
                  "rows": [{"dist": "linear_step", "start": "", "end": "", "value": ""}],   # mandatory, empty
                  "max_solutions": fmt(w["max_solutions"]), "error_pct": fmt(w["error_tolerance_pct"]),
                  "passivity": bool(w["enforce_passivity"]), "passivity_tol": fmt(w["passivity_tolerance"]),
                  "causality": bool(w["enforce_causality"])},
        "extents": {"dielectric_type": a["dielectric_extent_type"], "dielectric_pad": fmt(a["dielectric_horizontal"]),
                    "airbox_type": a["extent_type"], "airbox_pad": fmt(a["horizontal"]), "z_pos": fmt(a["positive_z"]),
                    "z_sync": bool(a["z_sync"]), "z_neg": fmt(a["negative_z"])},
        "choices": {rd: ch.get("default") for rd, ch in (data_channel.get("choices") or {}).items()},
    }


# ----------------------------------------------------------------------------- sweep rows
def row_points(r):
    """(points, error) of one sweep row (same rules as the page)."""
    s, e = ghz(r.get("start")), ghz(r.get("end"))
    if s is None or e is None:
        return None, "Start and End are required (e.g. 0GHz, 20GHz)"
    if not (e > s >= 0):
        return None, "Start must be >= 0 and below End"
    d = r.get("dist")
    if d == "linear_step":
        v = ghz(r.get("value"))
        if v is None or not (0 < v <= e - s):
            return None, "Step size: 0 < step <= End - Start"
        return int(math.floor((e - s) / v + 1e-9)) + 1, None
    if d == "linear_count":
        n = _int(r.get("value"))
        if n is None or n < 2:
            return None, "Count: whole number >= 2"
        return n, None
    if d == "log_scale":
        n = _int(r.get("value"))
        if s <= 0:
            return None, "Log Scale needs Start > 0"
        if n is None or n < 1:
            return None, "Samples per decade: whole number >= 1"
        return int(math.ceil(math.log10(e / s) * n - 1e-9)) + 1, None
    return None, f"Distribution: one of {', '.join(DISTS)}"


def sweep_end(rows):
    ends = [ghz(r.get("end")) for r in rows or []]
    ends = [e for e in ends if e is not None]
    return max(ends) if ends else None


# ----------------------------------------------------------------------------- validation
def _err(out, ch, frame, field, msg):
    out.append({"channel": ch, "frame": FRAMES.get(frame, frame), "field": field, "message": msg})


def _pos(out, ch, frame, field, text, lo=0.0, strict=True, integer=False, hi=None):
    v = _int(text) if integer else num(text)
    ok = v is not None and (v > lo if strict else v >= lo) and (hi is None or v <= hi)
    if not ok:
        rng = f"{'>' if strict else '>='} {lo:g}" + (f" and <= {hi:g}" if hi is not None else "")
        _err(out, ch, frame, field, f"{'whole number' if integer else 'number'} {rng} (got {text!r})")
    return v


def validate(state, data, P, rows, build_params=None):
    """-> [{channel, frame, field, message}] ([] = valid). Wrong document shape -> CopilotInputError."""
    if not isinstance(state, dict) or not isinstance(state.get("channels"), dict):
        raise CopilotInputError("state", "page state {channels: {name: {...}}}", type(state).__name__)
    chans = (data or {}).get("channels") or {}
    if set(state["channels"]) != set(chans):
        raise CopilotInputError("state.channels", "the channels of the request " + ", ".join(sorted(chans)),
                                sorted(state["channels"]))
    out = []
    folders = {}
    for name in chans:
        st, dc = state["channels"][name], chans[name]
        msg = check_folder(st.get("folder"), folders.values())
        if msg:
            _err(out, name, "folder", "Channel folder", msg)
        else:
            folders[name] = st["folder"].strip()
        out += validate_channel(name, st, dc, P, rows, build_params)
    return out


def validate_channel(name, st, dc, P, rows, build_params=None):
    out = []
    types = {r["key"]: r["type"] for r in rows}
    cut = st.get("cut") or {}
    if cut.get("cutout.extent_type") not in CUT_TYPES:
        _err(out, name, "cut", "Expansion type", f"one of {', '.join(CUT_TYPES)}")
    if cut.get("cutout.expansion") not in FACTORS:
        _err(out, name, "cut", "Expansion", f"0.02 .. 0.20 step 0.01 (got {cut.get('cutout.expansion')!r})")
    from ...core.config import coerce
    for k, v in cut.items():
        if k in MAIN_CUT:
            continue
        if k not in types or not k.startswith(ADV_PREFIX):
            _err(out, name, "cut", k, "not a setting of this frame")
            continue
        try:
            coerce(v, types[k])
        except ValueError as ex:
            _err(out, name, "cut", k, str(ex))
    c = dc.get("content") or {}
    nets = [n for n in c.get("nets") or [] if (st.get("nets") or {}).get(n, True)]
    if not nets:
        _err(out, name, "content", "Nets", "at least one signal net included")
    for d in c.get("schematic_diffs") or []:
        if (st.get("diffs") or {}).get(d["item"]) not in DIFF_CHOICES:
            _err(out, name, "content", d["item"], f"one of {', '.join(DIFF_CHOICES)}")
    for rd, ch in (dc.get("choices") or {}).items():
        if (st.get("choices") or {}).get(rd) not in (ch.get("options") or []):
            _err(out, name, "choices", rd, "one of " + ", ".join(ch.get("options") or []))
    for rd, e in (dc.get("ends") or {}).items():
        m = (st.get("cm") or {}).get(rd)
        if not isinstance(m, dict):
            _err(out, name, "cm", rd, "component model missing")
            continue
        if m.get("die_type") not in DIE_TYPES:
            _err(out, name, "cm", f"{rd} Die type", ", ".join(DIE_TYPES))
        if m.get("die_orientation") not in ORIENTS:
            _err(out, name, "cm", f"{rd} Orientation", ", ".join(ORIENTS))
        if m.get("die_type") == "wire_bond":
            _pos(out, name, "cm", f"{rd} Die height", m.get("die_height_mm"), strict=False)
        if m.get("ball_shape") not in SHAPES:
            _err(out, name, "cm", f"{rd} Shape", ", ".join(SHAPES))
        elif m["ball_shape"] != "none":
            _pos(out, name, "cm", f"{rd} Diameter", m.get("ball_ratio"), hi=1.0)
            _pos(out, name, "cm", f"{rd} Height", m.get("ball_height_mm"))
            if not str(m.get("ball_material") or "").strip():
                _err(out, name, "cm", f"{rd} Material", "required")
        if m.get("port_location") not in PORTS:
            _err(out, name, "cm", f"{rd} Port location", ", ".join(PORTS))
        elif e.get("bga") and m["port_location"] != "centre":
            _err(out, name, "cm", f"{rd} Port location", "round pads (BGA): port at the pad centre")
        if m.get("port_pct") not in (None, "") and not e.get("bga"):    # 041 slider
            _pos(out, name, "cm", f"{rd} Port position %", m.get("port_pct"), strict=False, hi=100.0)
    s = st.get("setup") or {}
    if s.get("mode") == "single":
        if not s.get("freq_linked"):
            f = ghz(s.get("freq_ghz"))
            if f is None or f <= 0:
                _err(out, name, "setup", "Frequency", f"frequency > 0 (got {s.get('freq_ghz')!r})")
        _pos(out, name, "setup", "Maximum Number of Passes", s.get("max_passes"), integer=True, hi=100)
        _pos(out, name, "setup", "Maximum Delta S", s.get("max_delta_s"))
    elif s.get("mode") == "multi":
        if not s.get("multi"):
            _err(out, name, "setup", "Multi-Frequencies", "at least one frequency")
        for i, m in enumerate(s.get("multi") or []):
            f = ghz(f"{m.get('f')}{m.get('unit') or 'GHz'}")
            if f is None or f <= 0:
                _err(out, name, "setup", f"Multi-Frequencies row {i + 1}", "frequency > 0")
            _pos(out, name, "setup", f"Multi-Frequencies row {i + 1} Max Delta S", m.get("ds"))
        _pos(out, name, "setup", "Maximum Number of Passes", s.get("multi_passes"), integer=True, hi=100)
    else:
        _err(out, name, "setup", "Solution Frequency", "single or multi")
    _pos(out, name, "setup", "Maximum Refinement Per Pass", s.get("refine_pct"), integer=True, hi=100)
    if s.get("basis") not in BASIS:
        _err(out, name, "setup", "Order of Basis Functions", ", ".join(BASIS))
    if s.get("via_mesh_3d"):
        _pos(out, name, "setup", "Number of sides for meshed vias", s.get("via_sides"), lo=3, strict=False,
             integer=True, hi=64)
    _pos(out, name, "setup", "Maximum Delta Zo", s.get("delta_zo"))
    w = st.get("sweep") or {}
    if w.get("type") not in SWEEP_TYPES:
        _err(out, name, "sweep", "Sweep Type", ", ".join(SWEEP_TYPES))
    if not w.get("rows"):
        _err(out, name, "sweep", "Frequency Sweeps", "at least one row")
    for i, r in enumerate(w.get("rows") or []):
        _, e = row_points(r)
        if e:
            _err(out, name, "sweep", f"Frequency Sweeps row {i + 1}", e)
    if w.get("type") == "interpolation":
        _pos(out, name, "sweep", "Max Solutions", w.get("max_solutions"), integer=True)
        _pos(out, name, "sweep", "Error Tolerance", w.get("error_pct"))
        if w.get("passivity"):
            _pos(out, name, "sweep", "Passivity Error Tolerance", w.get("passivity_tol"))
    x = st.get("extents") or {}
    for k, lab in (("dielectric_type", "Dielectric Type"), ("airbox_type", "Airbox Type")):
        if x.get(k) not in MODEL_TYPES:
            _err(out, name, "extents", lab, ", ".join(MODEL_TYPES))
    for k, lab in (("dielectric_pad", "Dielectric Horizontal Padding"), ("airbox_pad", "Airbox Horizontal Padding"),
                   ("z_pos", "Positive Padding")) + ((("z_neg", "Negative Padding"),) if not x.get("z_sync") else ()):
        _pos(out, name, "extents", lab, x.get(k), strict=False)
    if not out:                                                        # final check = rules of the existing steps
        try:
            s2 = to_settings(name, st, dc, P, rows)
        except CopilotInputError as ex:
            _err(out, name, "setup", ex.args[0] if ex.args else "settings", str(ex))
            return out
        if build_params is None:
            from ...cut_board.config import build_params
        _, errs = build_params({**s2["structural"], **s2["values"]})
        for e in errs:
            k = e.split(":")[0].split(" ")[0]
            _err(out, name, "cut" if k.startswith(ADV_PREFIX) else "setup", k, e)
    return out


# ----------------------------------------------------------------------------- mapping
def _ranges(rows):
    out = []
    for r in rows:
        d = r["dist"]
        v = ghz(r["value"]) if d == "linear_step" else _int(r["value"])
        out.append([d, ghz(r["start"]), ghz(r["end"]), v])
    return out


def to_settings(name, st, dc, P, rows):
    """-> {content, structural, values, handling, folder, note}. Pre: validate_channel(...) == []."""
    c = dict(dc.get("content") or {})
    if not c.get("comp_a"):
        raise CopilotInputError("content", f"traced content of {name}", c)
    keep = [n for n in c.get("nets") or [] if (st.get("nets") or {}).get(n, True)]
    groups = [[n for n in g if n in keep] for g in c.get("diff_groups") or []]
    series = {rd: v for rd, v in (c.get("series") or {}).items() if set(v.get("nets") or []) & set(keep)}
    diffs = [{"item": d["item"], "resolution": (st.get("diffs") or {}).get(d["item"], "board")}
             for d in c.get("schematic_diffs") or []]
    cut = st.get("cut") or {}
    structural = {k: v for k, v in cut.items() if k.startswith(STRUCT_PREFIX) or k in STRUCT_KEYS}
    content = {"comp_a": c["comp_a"], "comp_b": c["comp_b"], "nets": keep,
               "diff_groups": [g for g in groups if len(g) >= 2], "series": series, "schematic_diffs": diffs,
               "structural": structural}
    values = {k: v for k, v in cut.items() if k.startswith(ADV_PREFIX) and k not in structural}
    s, w, x = st["setup"], st["sweep"], st["extents"]
    rws = w["rows"]
    rg = _ranges(rws)
    start, stop = min(r[1] for r in rg), max(r[2] for r in rg)
    lin = [r[3] for r in rg if r[0] == "linear_step" and r[3]]
    step = min(lin) if lin else (stop - start) / 100.0
    values.update({
        "setup.solution_mode": s["mode"],
        "setup.adaptive_freq": "auto" if s.get("freq_linked") or s["mode"] != "single" else f"{ghz(s['freq_ghz']):g}",
        "setup.max_passes": s["max_passes"], "setup.max_delta_s": s["max_delta_s"],
        "setup.multi_freqs": json.dumps([[ghz(f"{m['f']}{m.get('unit') or 'GHz'}"), num(m["ds"])]
                                         for m in s.get("multi") or []]) if s["mode"] == "multi" else "",
        "setup.multi_max_passes": s.get("multi_passes") or "10",
        "setup.max_refine_per_pass": s["refine_pct"], "setup.basis_order": s["basis"],
        "setup.via_mesh_3d": "true" if s["via_mesh_3d"] else "false", "setup.via_num_sides": s["via_sides"],
        "setup.max_delta_zo": s["delta_zo"],
        "sweep.type": w["type"], "sweep.use_q3d_dc": "true" if w["q3d_dc"] else "false",
        "sweep.start_ghz": f"{start:g}", "sweep.stop_ghz": f"{stop:g}", "sweep.step_ghz": f"{step:g}",
        "sweep.ranges": json.dumps(rg),
        "sweep.max_solutions": w["max_solutions"], "sweep.error_tolerance_pct": w["error_pct"],
        "sweep.enforce_passivity": "true" if w["passivity"] else "false",
        "sweep.passivity_tolerance": w["passivity_tol"], "sweep.enforce_causality": "true" if w["causality"] else "false",
        "airbox.dielectric_extent_type": x["dielectric_type"], "airbox.dielectric_horizontal": x["dielectric_pad"],
        "airbox.extent_type": x["airbox_type"], "airbox.horizontal": x["airbox_pad"],
        "airbox.positive_z": x["z_pos"], "airbox.z_sync": "true" if x["z_sync"] else "false",
        "airbox.negative_z": x["z_pos"] if x["z_sync"] else x["z_neg"],
        "component.model": json.dumps({rd: dict(m) for rd, m in sorted((st.get("cm") or {}).items())}),
    })
    return {"content": content, "structural": structural, "values": {k: str(v) for k, v in values.items()},
            "handling": {rd: o for rd, o in (st.get("choices") or {}).items() if o},
            "folder": str(st.get("folder") or "").strip(), "note": str(st.get("content_note") or "")}


def settings_hash(settings):
    """sha1 of the canonical JSON of to_settings(...) (approval binding: Q2 -> go)."""
    return hashlib.sha1(json.dumps(settings, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
