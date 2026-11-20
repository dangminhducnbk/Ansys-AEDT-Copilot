"""Bước 2c: áp settings đã thống nhất (cutter.apply_stage) trên bản copy của stage1 + tự kiểm tra (contract isim-cut.md)."""
import datetime as dt
import math
import os
import shutil

from ..core.errors import CopilotInputError
from ..core.units import MM
from ..core.unique import claim_dir, move_aside
from . import request as R
from . import settings as S
from .cut import FileLog, channel


def gnd_decisions(ng, handling, notes=None):
    """015: {refdes: {option, rect_mm | n_copper_vias, image, note, decided_at}} cho đầu no_gnd_pin. Thuần."""
    out = {}
    for rd, u in (ng or {}).items():
        f, h = u.get("values") or {}, (handling or {}).get(rd)
        d = {"option": h, "image": f.get("image"), "note": (notes or {}).get(rd) or "", "decided_at": R._now()}
        if h == "gnd_plate_vias":
            d["rect_mm"] = f.get("rect_mm")
        elif h == "gnd_existing_copper":
            d["n_copper_vias"] = f.get("n_copper_vias")
        elif h == "gnd_keep_pad":                                       # 019
            kp = f.get("keep_pad") or {}
            d["pads"] = [{"pin": p["pin"], "size_mm": p["size_mm"]} for p in kp.get("pads") or []]
            d["margin_mm"] = kp.get("margin_mm")
        out[rd] = d
    return out


def run(request_id, name, values, handling=None, version=None, gnd_notes=None):
    from ..core.config import machine
    from ..core.edb import open_edb
    from ..cut_board import cutter
    req = R.load(request_id)
    rid = req["request_id"]
    chk = S.validate_for(rid, name, values, handling)
    if not chk["valid"]:
        raise CopilotInputError("settings", "valid settings (see errors)", chk["errors"])
    handling = dict(chk.get("handling") or handling or {})          # 012: mặc định connector + lần trước + kỹ sư
    ng = S.no_gnd_ends(rid, name)
    if gnd_notes is not None and (not isinstance(gnd_notes, dict) or set(gnd_notes) - set(ng)):
        raise CopilotInputError("gnd_notes", "{refdes of a no_gnd_pin end: text} among " + str(sorted(ng)), gnd_notes)
    gdec = gnd_decisions(ng, handling, gnd_notes)
    stop = [rd for rd, h in handling.items() if h == "stop_interface"]
    st = R.get_state(rid, name)
    if stop:
        R.fail(rid, name, f"stopped by engineer at {stop}")
        return {"name": name, "stopped": stop}
    P = chk["P"]
    version = version or machine()["aedt_version"]
    with R.busy(rid, name) as d:
        fl = FileLog(os.path.join(d, "apply.log"))
        log = fl.log
        try:
            s1j = R._rjson(os.path.join(d, "stage1.json"))
            fin = os.path.join(d, "final")
            if os.path.exists(fin):
                move_aside(fin, fin + "_old_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S"))
            dst = os.path.join(fin, name + ".aedb")
            ch = channel(name, st["content"])
            kp = sorted(rd for rd, h in handling.items() if h == "gnd_keep_pad")
            if kp:                                   # 019: cắt lại từ bản copy board, vùng cutout ∪ (pad GND + lề)
                s1j = recut_keep_pads(req, d, ch, P, version, log, dst, kp)
            else:
                with log.step("copy_stage1"):
                    shutil.copytree(s1j["aedb"], dst, ignore=shutil.ignore_patterns("*.lock"))
            s1 = cutter.stage1_from_json(s1j)
            with log.step("open"):
                edb = open_edb(dst, s1j.get("cell") or name, False, version)
            try:
                metrics = cutter.apply_stage(edb, s1, ch, P, log, handling=handling)
                out = edb.edbpath
            finally:
                try:
                    edb.close()
                except Exception as ex:
                    log("  edb.close lỗi:", ex)
            warnings = cutter.check(metrics, dict(ch, nets=s1["nets"]), P)
            sc = self_check(out, P, ch, s1, metrics, version, st.get("board_facts"))
            result = {"aedb": out, "metrics": metrics, "warnings": warnings, "self_check": sc, "times": log.times}
            R.wjson(os.path.join(d, "result.json"), result)
            saved = S.save(rid, name, chk.get("values", values), handling, chk["rows"], P,   # 009: arc step tường minh
                           gnd_decisions=gdec)
            values = saved["values"]
            result["user_settings"] = saved["user_settings"]
            R.set_state(rid, name, "applied", settings={"values": values, "handling": handling,
                                                        "gnd_decisions": gdec},
                        result={k: result[k] for k in ("aedb", "warnings", "self_check")})
            R.advance(rid, name, "applied")
            return {"name": name, "step": "applied", **result, "log": os.path.join(d, "apply.log")}
        except BaseException as ex:
            R.fail(rid, name, f"apply: {type(ex).__name__}: {ex}")
            raise
        finally:
            fl.close()


def recut_keep_pads(req, d, ch, P, version, log, dst, keep_pads):
    """019: cắt lại interface từ <iface>/_src (board copy) với vùng cutout mở rộng giữ pad GND của keep_pads.
    -> stage1 JSON (ghi stage1_keep_pad.json). Board của người dùng không bao giờ được mở."""
    from .cut import copy_source, cut_design
    with log.step("copy_source"):
        src, copied = copy_source(req["board"], d)
        log(f"  source copy {src} ({'copied' if copied else 'reused'})")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    s1j = cut_design(src, dst, ch, P, req.get("cell") or "", version, log, keep_pads=set(keep_pads))
    R.wjson(os.path.join(d, "stage1_keep_pad.json"), s1j)
    return s1j


GEOMETRY_KEYS = ("ports", "components", "gnd_vias", "gnd_by_layer")


def geometry_diff(old, new):
    """Thuần: so metrics hình học (port, linh kiện, GND via, GND theo lớp) -> {key: (cũ, mới)} khi khác."""
    import re

    def norm(m):
        m = dict(m or {})
        comps = {}
        for rd, c in (m.get("components") or {}).items():
            c = dict(c)
            c["part"] = re.sub(r"_cut(_\d+)?$", "_cut", c.get("part") or "")
            # bbox thân linh kiện đo trong phiên apply khác với đo sau khi mở lại file (EDB tính lại) -> không so;
            # vẫn so số pin, GND pin, vùng pin (pins_extent_mm)
            c.pop("bbox_mm", None)
            comps[rd] = c
        m["components"] = comps
        return m
    o, n = norm(old), norm(new)
    return {k: (o.get(k), n.get(k)) for k in GEOMETRY_KEYS if o.get(k) != n.get(k)}


def reapply(request_id, name, values, version=None):
    """006: đổi CHỈ setup / sweep / airbox của thiết kế đã apply. Backup final/<name>_old_<time>.aedb trước (không
    xoá), ghi lại setup, lưu, tự kiểm tra, so hình học với lần apply trước. Interface đã merge -> về 'applied'."""
    from ..core.config import machine
    from ..core.edb import open_edb
    from ..cut_board import config, cutter
    req = R.load(request_id)
    rid = req["request_id"]
    chk = S.validate_reapply(rid, name, values)
    if not chk["valid"]:
        raise CopilotInputError("settings", "valid re-apply settings (see errors)", chk["errors"])
    st = R.get_state(rid, name)
    P_new = chk["P"]
    P_old, _ = config.build_params(S.agreed_values(st, rid, name))
    handling = chk["handling"]
    version = version or machine()["aedt_version"]
    with R.busy(rid, name) as d:
        fl = FileLog(os.path.join(d, "reapply.log"))
        log = fl.log
        try:
            prev = R._rjson(os.path.join(d, "result.json")) or {}
            cur = prev.get("aedb") or os.path.join(d, "final", name + ".aedb")
            tag = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            with log.step("backup"):                                      # 024: thư mục nguyên tử, _2 khi trùng
                backup = claim_dir(os.path.join(os.path.dirname(cur), f"{name}_old_{tag}.aedb"))
                shutil.copytree(cur, backup, ignore=shutil.ignore_patterns("*.lock"), dirs_exist_ok=True)
            s1j = R._rjson(os.path.join(d, "stage1.json")) or {}
            ch = channel(name, st["content"])
            s1 = cutter.stage1_from_json(s1j)
            with log.step("open"):
                edb = open_edb(cur, s1j.get("cell") or name, False, version)
            try:
                with log.step("reapply_sim"):
                    cutter.reapply_sim(edb, P_old, P_new, log)
                with log.step("save"):
                    edb.save()
                metrics = cutter.collect_metrics(edb, P_new, s1["nets"], s1["ends"])
                metrics["arc_step_deg"] = cutter.read_arc_step(edb, P_new["setup"]["name"])
            finally:
                try:
                    edb.close()
                except Exception as ex:
                    log("  edb.close lỗi:", ex)
            metrics["max_pin_shift_mm"] = (prev.get("metrics") or {}).get("max_pin_shift_mm")   # hình học không đổi
            gdiff = geometry_diff(prev.get("metrics"), metrics)
            warnings = cutter.check(metrics, dict(ch, nets=s1["nets"]), P_new)
            sc = self_check(cur, P_new, ch, s1, metrics, version, st.get("board_facts"))
            result = {"aedb": cur, "metrics": metrics, "warnings": warnings, "self_check": sc, "times": log.times,
                      "reapplied_at": R._now(), "backup": backup}
            R.wjson(os.path.join(d, "result.json"), result)
            saved = S.save(rid, name, dict(chk["values"]), handling, chk["rows"], P_new)
            new_values = saved["values"]
            st = R.get_state(rid, name)
            changes = {"settings": {"values": new_values, "handling": handling},
                       "result": {k: result[k] for k in ("aedb", "warnings", "self_check")},
                       "result_history": (st.get("result_history") or []) + [st.get("result")],
                       "reapplied": (st.get("reapplied") or []) + [{"time": result["reapplied_at"],
                                                                     "values": new_values, "backup": backup,
                                                                     "self_check_ok": sc["ok"]}]}
            if st["step"] == "merged":                                    # merge lại = design mới (_v2)
                changes.update(step="applied", merged=None,
                               merged_before=(st.get("merged_before") or []) + [st.get("merged")])
            R.set_state(rid, name, "re-applied (setup / sweep / airbox)", failed=False, error=None, **changes)
            return {"name": name, "step": "applied", **result, "geometry_same": not gdiff,
                    "geometry_diff": gdiff, "user_settings": saved["user_settings"],
                    "log": os.path.join(d, "reapply.log")}
        except BaseException as ex:
            R.fail(rid, name, f"reapply: {type(ex).__name__}: {ex}")
            raise
        finally:
            fl.close()


def signal_paths(nets, series=None):
    """012: số đường tín hiệu giữa 2 đầu = số nhóm net nối nhau qua linh kiện nối tiếp 2 net. Thuần."""
    parent = {n: n for n in nets}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n
    for v in (series or {}).values():
        ns = [n for n in (v.get("nets") or []) if n in parent]
        for a, b in zip(ns, ns[1:]):
            parent[find(a)] = find(b)
    return len({find(n) for n in parent})


def series_report(edb, ch, P, facts=None):
    """012: mọi linh kiện nối tiếp của content -> [{refdes, type, part, value, nets, model, r_ohm, ok}].
    type / part / value từ board_facts (board gốc, trước khi nối tắt); r_ohm đọc lại trên EDB đã lưu."""
    r_model = float(P["series"]["model_r_ohm"])
    comps = (facts or {}).get("components") or {}
    out = []
    for rd, v in sorted((ch.get("series") or {}).items()):
        f = comps.get(rd) or {}
        row = {"refdes": rd, "type": f.get("type") or v.get("type"), "part": f.get("part") or v.get("part"),
               "value": f.get("value"), "nets": list(v.get("nets") or []),
               "model": f"short (R = {r_model:g} ohm)" if P["series"]["keep"] else "not kept", "r_ohm": None,
               "ok": False}
        c = edb.components.instances.get(rd)
        if c is None:
            row["model"] = "missing in design"
        else:
            try:
                row["r_ohm"] = float(str(c.res_value).lower().replace("ohm", "").strip())
            except Exception:
                row["r_ohm"] = None
            row["ok"] = row["r_ohm"] is not None and abs(row["r_ohm"] - r_model) < 1e-9
        out.append(row)
    return out


MOVED_M = 1e-6                          # 041: a signal pin farther than 1 µm from its source pad centre = moved


def port_location_mismatches(rd, comp, nets, stage1, metrics):
    """041: the user's per-end port location vs the pins read back from the saved design (distance to the source pad
    centre, same net). Only for an explicit choice on a rebuilt end."""
    pl = (metrics.get("port_location") or {}).get(rd) or {}
    if pl.get("explicit") and "targets" in pl:                          # 041 slider: every pin at its target (± 1 µm)
        news = [(p.net_name, tuple(p.position)) for p in comp.pins.values() if p.net_name in nets]
        off = []
        for t in pl["targets"]:
            q = (t["at_mm"][0] * MM, t["at_mm"][1] * MM)
            d = min((math.hypot(q[0] - x[0], q[1] - x[1]) for n2, x in news if n2 == t["net"]), default=None)
            if d is None or d > MOVED_M:
                off.append(f"{t['pin']}" + (f" {d / MM * 1000:.1f} µm off" if d is not None else " missing"))
        off += [f"{x['pin']}: {x['reason']}" for x in pl.get("not_moved") or []]
        if not off:
            return []
        n = len(pl["targets"]) + len(pl.get("not_moved") or [])
        return [{"item": f"{rd} port location ({pl.get('pct'):g} %)",
                 "expected": f"{n} signal pins at {pl.get('pct'):g} % of the pad", "got": "; ".join(off)}]
    req = pl.get("requested")
    if not pl.get("explicit") or req not in ("end", "centre") or "pins" not in pl:
        return []
    news = [(p.net_name, tuple(p.position)) for p in comp.pins.values() if p.net_name in nets]
    olds = [(net, o) for (r, net), v in stage1["sig_pos0"].items() if r == rd for o in v]
    moved = 0
    for net, o in olds:
        d = min((math.hypot(o[0] - q[0], o[1] - q[1]) for n2, q in news if n2 == net), default=None)
        if d is not None and d > MOVED_M:
            moved += 1
    exp = len(olds) if req == "end" else 0
    if moved == exp:
        return []
    why = "; ".join(f"{x['pin']}: {x['reason']}" for x in pl.get("not_moved") or [])
    return [{"item": f"{rd} port location ({req})", "expected": f"{exp} of {len(olds)} signal pins at the pad end",
             "got": f"{moved}" + (f" ({why})" if why else "")}]


def stackup_item(edb, stage1):
    """042: stackup of the saved design vs the board read at the cut -> {ok, diffs, note?}."""
    from ..cut_board import stackup_check as SC
    ref = stage1.get("board_stackup")
    if not ref:
        return {"ok": None, "diffs": [], "note": "no board stackup recorded (cut before 5.4.0)"}
    try:
        diffs = SC.compare(ref, SC.read(edb))
    except Exception as ex:
        diffs = [f"stackup unreadable: {type(ex).__name__}: {ex}"]
    return {"ok": not diffs, "diffs": diffs}


def self_check(aedb, P, ch, stage1, metrics, version, facts=None):
    """Mở lại CHỈ ĐỌC: số port, pin dời, setup / sweep có đúng tên, linh kiện đầu còn đủ pin tín hiệu."""
    from ..core.edb import edb_session
    mm = []
    nets = set(stage1["nets"])
    with edb_session(aedb, ch["name"], True, version) as edb:
        sig = 0
        for rd in stage1["ends"]:
            c = edb.components.instances.get(rd)
            if c is None:
                mm.append({"item": f"component {rd}", "expected": "present", "got": None})
                continue
            n = sum(1 for p in c.pins.values() if p.net_name in nets)
            exp = sum(1 for (r, _), v in stage1["sig_pos0"].items() if r == rd for _ in v)
            sig += n
            if n < exp:
                mm.append({"item": f"{rd} signal pins", "expected": exp, "got": n})
            mm += port_location_mismatches(rd, c, nets, stage1, metrics)   # 041
            gpc = next((g for g in metrics.get("gnd_pin_cleanup") or [] if g.get("refdes") == rd), None)
            if gpc:                                                     # 021: số pin GND sau dọn, đầu còn GND
                refs = set(P["cutout"]["reference_nets"])
                ng = sum(1 for p in c.pins.values() if p.net_name in refs)
                if ng != gpc["gnd_pins_after"] or (n and not ng):
                    mm.append({"item": f"{rd} GND pins after cleanup", "expected": gpc["gnd_pins_after"], "got": ng})
        ports = len(edb.ports)
        if ports != sig:
            mm.append({"item": "ports", "expected": sig, "got": ports})
        paths = signal_paths(ch["nets"], ch.get("series"))
        if ports != 2 * paths:
            mm.append({"item": "ports vs 2 x signal paths", "expected": 2 * paths, "got": ports})
        series = series_report(edb, ch, P, facts) if ch.get("series") else []
        if P["series"]["keep"]:
            bad = [r["refdes"] for r in series if not r["ok"]]
            if bad:
                mm.append({"item": "series parts shorted", "expected": f"R = {P['series']['model_r_ohm']} ohm",
                           "got": bad})
        setups = dict(edb.setups) if hasattr(edb, "setups") else {}
        sname, wname = P["setup"]["name"], P["sweep"]["name"]
        if sname not in setups:
            mm.append({"item": "setup", "expected": sname, "got": sorted(setups)})
        else:
            try:
                sw = list(setups[sname].sweeps)
                if wname not in sw:
                    mm.append({"item": "sweep", "expected": wname, "got": sw})
                else:
                    mm += setup_mismatches(read_setup(setups[sname], wname), P)
            except Exception as ex:
                mm.append({"item": "sweep", "expected": wname, "got": f"unreadable: {ex}"})
        try:
            mm += airbox_mismatches(read_airbox(edb), P)                   # airbox.* (đọc lại từ EDB đã lưu)
        except Exception as ex:
            mm.append({"item": "airbox", "expected": "readable", "got": f"unreadable: {ex}"})
        stk = stackup_item(edb, stage1)                                    # 042: stackup = board
        mm += [{"item": "stackup = board", "expected": "board stackup", "got": d} for d in stk.get("diffs") or []]
    if (metrics.get("max_pin_shift_mm") or 0) > 1.0:
        mm.append({"item": "max_pin_shift_mm", "expected": "<= 1", "got": metrics["max_pin_shift_mm"]})
    return {"ok": not mm, "mismatches": mm, "ports": ports, "signal_pins": sig, "signal_paths": paths,
            "expected_ports_2x_paths": 2 * paths, "series": series, "stackup": stk,
            "gnd_reference": metrics.get("gnd_reference") or {},                # 015: tham chiếu GND từng đầu
            "gnd_pin_cleanup": metrics.get("gnd_pin_cleanup") or []}            # 021: pin GND trước -> sau


# ----------------------------------------------------------------------------- đọc lại setup / sweep (FR-013)
_UNIT = {"hz": 1e-9, "khz": 1e-6, "mhz": 1e-3, "ghz": 1.0, "thz": 1e3}


def ghz(text):
    """'10GHz' / '0.1 GHz' / '500MHz' / 10 -> GHz (float)."""
    t = str(text).strip().replace(" ", "").lower()
    for u in sorted(_UNIT, key=len, reverse=True):
        if t.endswith(u):
            return float(t[:-len(u)]) * _UNIT[u]
    return float(t)


def _deg(text):
    from ..cut_board.cutter import deg
    return deg(text)


def _read(fn):
    try:
        return fn()
    except Exception as ex:                                       # không đọc được -> báo, không dừng
        return f"unreadable: {type(ex).__name__}"


def read_setup(st, sweep_name):
    """Setup PyEDB (.NET) -> dict giá trị thuần (đơn vị GHz). Mỗi mục đọc riêng, lỗi -> 'unreadable: ...'."""
    a = st.adaptive_settings
    afd = lambda: a.adaptive_frequency_data_list[0]
    sw = st.sweeps[sweep_name]

    def lin():
        f = sw.frequency_string
        f = f[0] if isinstance(f, (list, tuple)) and len(f) == 1 else f
        kind, start, stop, step = str(f).split()
        if kind.upper() != "LIN":
            raise ValueError(f)
        return ghz(start), ghz(stop), ghz(step)
    freqs = _read(lin)
    get = (lambda i: freqs[i]) if isinstance(freqs, tuple) else (lambda i: freqs)
    return {
        "setup.adaptive_freq": _read(lambda: ghz(afd().adaptive_frequency)),
        "setup.max_passes": _read(lambda: int(afd().max_passes)),
        "setup.max_delta_s": _read(lambda: float(afd().max_delta)),
        "setup.max_refine_per_pass": _read(lambda: int(a.max_refine_per_pass)),
        "setup.min_passes": _read(lambda: int(a.min_passes)),
        "setup.min_converged_passes": _read(lambda: int(a.min_converged_passes)),
        "setup.basis_order": _read(lambda: str(st.hfss_solver_settings.order_basis).lower()),
        "setup.max_delta_zo": _read(lambda: float(st.hfss_port_settings.max_delta_z0)),
        "setup.arc_step_deg": _read(lambda: _deg(st.curve_approx_settings.arc_angle)),
        "sweep.type": _read(lambda: str(sw.type).lower()),
        "sweep.start_ghz": get(0), "sweep.stop_ghz": get(1), "sweep.step_ghz": get(2),
        "sweep.max_solutions": _read(lambda: int(sw.max_solutions)),
        "sweep.error_tolerance_pct": _read(lambda: float(sw.relative_s_error) * 100),
        "sweep.enforce_causality": _read(lambda: bool(sw.enforce_causality)),
        "sweep.enforce_passivity": _read(lambda: bool(sw.enforce_passivity)),
        "sweep.passivity_tolerance": _read(lambda: float(sw.passivity_tolerance)),
    }


def expected_setup(P):
    """Giá trị setup / sweep mong đợi từ P (cùng quy ước cutter.apply_setup)."""
    s, w = P["setup"], P["sweep"]
    af = str(s["adaptive_freq"]).strip().lower()
    return {
        "setup.adaptive_freq": float(w["stop_ghz"]) if af in ("auto", "max", "") else ghz(s["adaptive_freq"]),
        "setup.max_passes": int(s["max_passes"]), "setup.max_delta_s": float(s["max_delta_s"]),
        "setup.max_refine_per_pass": int(s["max_refine_per_pass"]), "setup.min_passes": int(s["min_passes"]),
        "setup.min_converged_passes": int(s["min_converged_passes"]),
        "setup.basis_order": str(s["basis_order"]).lower(), "setup.max_delta_zo": float(s["max_delta_zo"]),
        **({"setup.arc_step_deg": float(s["arc_step_deg"])} if s.get("arc_step_deg") is not None else {}),
        "sweep.type": "discrete" if str(w["type"]).lower() == "discrete" else "interpolation",
        "sweep.start_ghz": float(w["start_ghz"]), "sweep.stop_ghz": float(w["stop_ghz"]),
        "sweep.step_ghz": float(w["step_ghz"]), "sweep.max_solutions": int(w["max_solutions"]),
        "sweep.error_tolerance_pct": float(w["error_tolerance_pct"]),
        "sweep.enforce_causality": bool(w["enforce_causality"]), "sweep.enforce_passivity": bool(w["enforce_passivity"]),
        "sweep.passivity_tolerance": float(w["passivity_tolerance"]),
    }


def _same(exp, got):
    if got is None or any(isinstance(x, (bool, str)) for x in (exp, got)):
        return exp == got
    return abs(float(exp) - float(got)) <= 1e-9 * max(1.0, abs(float(exp)))


def setup_mismatches(read, P):
    """Thuần: so dict đọc lại với P -> [{item, expected, got}]. Sweep discrete: max_solutions / error / passivity
    không áp dụng nên bỏ qua."""
    exp = expected_setup(P)
    skip = set()
    if exp["sweep.type"] == "discrete":
        skip = {"sweep.max_solutions", "sweep.error_tolerance_pct", "sweep.enforce_passivity",
                "sweep.passivity_tolerance", "sweep.enforce_causality"}
    return [{"item": k, "expected": v, "got": read.get(k)} for k, v in exp.items()
            if k not in skip and not _same(v, read.get(k))]


# ----------------------------------------------------------------------------- đọc lại airbox
def read_airbox(edb):
    """hfss_extent_info -> dict airbox.* (operating_freq theo GHz). Mỗi mục đọc riêng, lỗi -> 'unreadable: ...'."""
    h = edb.hfss.hfss_extent_info
    return {
        "airbox.extent_type": _read(lambda: str(h.extent_type).lower()),
        "airbox.dielectric_extent_type": _read(lambda: str(h.dielectric_extent_type).lower()),
        "airbox.horizontal": _read(lambda: float(h.air_box_horizontal_extent)),
        "airbox.positive_z": _read(lambda: float(h.air_box_positive_vertical_extent)),
        "airbox.negative_z": _read(lambda: float(h.air_box_negative_vertical_extent)),
        "airbox.z_from_stackup": _read(lambda: not bool(h.use_xy_data_extent_for_vertical_expansion)),
        "airbox.open_region": _read(lambda: str(h.open_region_type).lower()),
        "airbox.operating_freq": _read(lambda: float(h.operating_freq) / 1e9),
    }


def expected_airbox(P):
    a = P["airbox"]
    return {
        "airbox.extent_type": str(a["extent_type"]).lower(),
        "airbox.dielectric_extent_type": str(a["dielectric_extent_type"]).lower(),
        "airbox.horizontal": float(a["horizontal"]), "airbox.positive_z": float(a["positive_z"]),
        "airbox.negative_z": float(a["negative_z"]), "airbox.z_from_stackup": bool(a["z_from_stackup"]),
        "airbox.open_region": str(a["open_region"]).lower(), "airbox.operating_freq": ghz(a["operating_freq"]),
    }


def airbox_mismatches(read, P):
    """Thuần: so airbox đọc lại với P -> [{item, expected, got}]."""
    return [{"item": k, "expected": v, "got": read.get(k)} for k, v in expected_airbox(P).items()
            if not _same(v, read.get(k))]
