"""Bước 1: thống nhất nội dung interface (net, nhóm vi sai, linh kiện 2 đầu, linh kiện nối tiếp) - contract isim-content.md.

trace(): đọc board CHỈ ĐỌC -> đề xuất + dữ kiện board (board_facts) + khác biệt so với schematic.md.
confirm(): kiểm tra nội dung người dùng chốt với board_facts đã lưu (không mở lại EDB) -> content_agreed.
"""
import difflib
import fnmatch
import itertools
import json
import os
import re

from ..core.errors import CopilotInputError
from . import report, request as R
from . import schematic as SCH

STRUCTURAL_PREFIX = ("cutout.",)
STRUCTURAL_KEYS = ("series.keep",)


def _template_rows():
    from ..cut_board import config
    return config.template_rows()


def structural_defaults():
    """Thông số cut_stage dùng (cutout.*, series.keep): mặc định template, chốt cùng nội dung (đổi sau = cắt lại)."""
    return {r["key"]: r["default"] for r in _template_rows()
            if r["scope"] == "channel" and (r["key"].startswith(STRUCTURAL_PREFIX) or r["key"] in STRUCTURAL_KEYS)}


def _closest(name, pool, n=5):
    m = difflib.get_close_matches(name, pool, n=n, cutoff=0.5)
    if not m:
        u = name.upper()
        m = [x for x in pool if u in x.upper()][:n]
    return m


# ----------------------------------------------------------------------------- board (EDB)
def _comp_value(c):
    for a in ("value", "res_value", "cap_value", "ind_value"):
        try:
            v = getattr(c, a)
            if v not in (None, "", 0):
                return str(v)
        except Exception:
            pass
    return ""


def _facts(edb, comps, nets, refs):
    """Dữ kiện board cho các linh kiện / net liên quan (JSON được)."""
    inst = edb.components.instances
    out = {"components": {}, "nets": {}}
    nets = set(nets)
    for rd in comps:
        c = inst[rd]
        pins = {}
        gnd = 0
        for pn, p in c.pins.items():
            if p.net_name in nets:
                pins[str(p.pin_number or pn)] = p.net_name
            elif p.net_name in refs:
                gnd += 1
        out["components"][rd] = {"part": c.partname, "type": c.type, "numpins": c.numpins,
                                 "value": _comp_value(c), "signal_pins": pins, "gnd_pins": gnd}
    for n in nets:
        out["nets"][n] = sorted([rd, pn] for rd in comps for pn, net in out["components"][rd]["signal_pins"].items()
                                if net == n)
    return out


def _expand_nets(patterns, netlist):
    out, missing = [], []
    for p in patterns:
        hit = [n for n in netlist if fnmatch.fnmatchcase(n, p) or n == p]
        if hit:
            out += hit
        else:
            missing.append(p)
    return sorted(set(out)), missing


def _board_trace(edb, refdes, nets, refs, missing_ok=False):
    """-> (proposal, candidates, end_types, warnings). Không sửa board.
    missing_ok (cut lại, 004): net / pattern không còn trên board -> bỏ qua, ghi vào warnings 'missing nets: ...'."""
    from ..cut_board import inspect_board as IB
    from ..cut_board.naming import group_diff
    inst = edb.components.instances
    netlist = list(edb.nets.netlist)
    for rd in refdes:
        if rd not in inst:
            raise CopilotInputError("refdes", "refdes on the board, closest: " + ", ".join(_closest(rd, list(inst))), rd)
    patterns = list(nets)
    if len(refdes) < 2 and not patterns:
        raise CopilotInputError("nets", "net names / patterns when fewer than 2 refdes are given", patterns)
    if patterns:
        found, missing = _expand_nets(patterns, netlist)
        if missing and missing_ok and (found or len(refdes) >= 2):
            patterns = [x for x in patterns if x not in missing]
            missing = []
        if missing:
            raise CopilotInputError("nets", "nets on the board, closest to " + missing[0] + ": " +
                                    ", ".join(_closest(missing[0], netlist)), missing)
    pg = set(edb.nets.power.keys()) | set(refs)
    warnings, candidates = [], []
    if len(refdes) >= 2:
        pairs = [tuple(refdes[:2])] if len(refdes) == 2 else list(itertools.combinations(refdes, 2))
    else:
        # chỉ net (hoặc 1 refdes + net): linh kiện trên các net, bỏ 2-pin R/C/L (nối tiếp)
        on = {}
        for n in found:
            for rd, c in IB._net_components(edb, n).items():
                ctype = (getattr(c, "type", "") or "").lower()
                if c.numpins == 2 and ctype in IB.SERIES_TYPES:
                    continue
                on[rd] = c.numpins
        ends = sorted(on, key=lambda r: (-on[r], r))
        if refdes:
            ends = [refdes[0]] + [r for r in ends if r != refdes[0]]
        candidates = [{"refdes": r, "pins": on.get(r, inst[r].numpins), "part": inst[r].partname} for r in ends]
        if len(ends) < 2:
            raise CopilotInputError("nets", "nets connecting at least 2 components", patterns)
        pairs = [tuple(ends[:2])] if len(ends) == 2 else list(itertools.combinations(ends, 2))
        if len(ends) > 2:
            warnings.append(f"{len(ends)} end candidates on these nets: {ends[:8]} - choose comp_a / comp_b")
    traces = []
    for a, b in pairs:
        t = IB.trace_channel(edb, a, b, patterns or None, refs)
        traces.append((a, b, t))
        if len(pairs) > 1:
            candidates.append({"pair": [a, b], "nets": len(t["nets"]), "series": sorted(t["series"])})
    a, b, t = max(traces, key=lambda x: len(x[2]["nets"]))
    if len(pairs) > 1:
        warnings.append(f"proposal uses the pair with most nets: {a}-{b}")
    warnings += t["warnings"]
    prop = {"comp_a": a, "comp_b": b, "nets": t["nets"], "diff_groups": group_diff(t["nets"]),
            "series": {rd: {"nets": [n for n in v["nets"] if n not in pg], "type": v["type"], "part": v["part"]}
                       for rd, v in t["series"].items()}}
    return prop, candidates, t["end_types"], warnings


def trace(request_id, name, refdes=(), nets=(), version=None, missing_ok=False):
    from ..core.edb import edb_session
    from ..cut_board import config, naming
    req = R.load(request_id)
    refdes = [r.strip() for r in (refdes.split(",") if isinstance(refdes, str) else refdes) if r and r.strip()]
    nets = [n.strip() for n in (nets.split(",") if isinstance(nets, str) else nets) if n and n.strip()]
    if not refdes and not nets:
        raise CopilotInputError("refdes / nets", "at least one refdes or net", "")
    refs = config.defaults()["cutout"]["reference_nets"]
    with edb_session(req["board"], req.get("cell") or None, True, version) as edb:
        prop, cands, end_types, warns = _board_trace(edb, refdes, nets, refs, missing_ok)
        netlist = list(edb.nets.netlist)
        missing_nets = [p for p in nets if not _expand_nets([p], netlist)[0]] if missing_ok else []
        comps = [prop["comp_a"], prop["comp_b"]] + sorted(prop["series"])
        facts = _facts(edb, comps, prop["nets"] + [n for s in prop["series"].values() for n in s["nets"]], refs)
        board_nets = sorted(edb.nets.netlist)
    name = name or naming.default_name(prop["comp_a"], prop["comp_b"], prop["nets"])
    others = [n for n in req["interfaces"] if n.lower() != name.lower()]
    R.check_name(name, others)
    sch = SCH.load_parsed(req["request_id"])
    if sch and sch.get("source") == "netlist":
        check_design(facts, sch)                                        # 036: netlist của board khác -> từ chối
    R.add_interface(req["request_id"], name)
    R.wjson(os.path.join(R.work_dir(req), "board_nets.json"), board_nets)
    cmp_ = compare(facts, sch, nets) if sch else {"diffs": [], "board_only": [], "renamed": []}
    diffs = cmp_["diffs"]
    info = {"source": (sch or {}).get("source"), "board_only": cmp_["board_only"], "renamed": cmp_["renamed"]}
    if not sch:
        warns.append("no schematic (netlist / schematic.md): content checked against the board only")
    st = R.new_state(req["request_id"], name)
    prop["structural"] = (st.get("content") or {}).get("structural") or structural_defaults()
    R.set_state(req["request_id"], name, "trace", proposal=prop, board_facts=facts, schematic_diffs=diffs,
                schematic_info=info, end_types=end_types, trace_args={"refdes": refdes, "nets": nets},
                candidates=cands)
    md = content_md(name, prop, facts, diffs, end_types, title="Proposal (not agreed)")
    return {"request_id": req["request_id"], "name": name, "step": st["step"], "proposal": prop,
            "candidates": cands, "end_types": end_types, "schematic_diffs": diffs, "schematic_info": info,
            "warnings": warns, "content_md": md, "missing_nets": missing_nets}


# ----------------------------------------------------------------------------- schematic diff (thuần)
_PREFIX = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}


def si_value(v):
    """'220nF' / '0.22uF' / '2.2e-07' / '10k' / '0R' / '0 Ohm' -> số (đơn vị gốc); không hiểu -> None."""
    s = str(v or "").strip().replace(" ", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    m = re.fullmatch(r"(\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)([pnuµmkKMG]?)(?:F|H|Ohm|ohm|OHM|Ω|R|r)?", s)
    if not m:
        m = re.fullmatch(r"(\d+)([RrKkMm])(\d+)", s)                    # 4R7 / 2K2
        if not m:
            return None
        p = {"R": 1, "r": 1, "K": 1e3, "k": 1e3, "M": 1e6, "m": 1e6}[m.group(2)]
        return float(f"{m.group(1)}.{m.group(3)}") * p
    return float(m.group(1)) * _PREFIX.get(m.group(2), 1.0)


def check_design(facts, sch):
    """036: netlist phải là của board này: >= 50 % linh kiện của interface (2 đầu + nối tiếp) có trong netlist."""
    comps = list(facts["components"])
    found = [rd for rd in comps if rd in sch["components"]]
    if comps and len(found) * 2 < len(comps):
        raise CopilotInputError("netlist", "netlist of THIS board (the traced ends / series parts must be in it; "
                                           f"found {len(found)} of {len(comps)}: {', '.join(comps[:6])})",
                                sch.get("design") or "netlist.json")


def compare(board_facts, sch, patterns=()):
    """036: so board với schematic / netlist THEO CHÂN (refdes.pin), không theo tên net. Thuần.
    - linh kiện 2 chân: không xét số chân (đảo chân 1 / 2 không phải khác biệt);
    - chân không có trong schematic (PDF không đọc được, linh kiện không có) -> board_only (thông tin, không hỏi);
    - cùng chân nhưng tên net khác (off-page / block đổi tên) -> renamed (thông tin);
    - khác biệt thật (chân nối sang net khác, net schematic giữa 2 linh kiện không có trên board, giá trị nối tiếp
      khác) -> diffs [{item, kind, board, schematic, probable}].
    patterns: net pattern của trace; với netlist chỉ net schematic khớp pattern mới xét 'missing_on_board'."""
    snets = sch.get("nets", {})
    scomps = sch.get("components", {})
    fc = board_facts["components"]
    two = {rd for rd, c in fc.items() if c.get("numpins") == 2}

    def key(rd, pn):
        return (rd, "*") if rd in two else (rd, str(pn))

    spin = {}
    for n, v in snets.items():
        for rd, pn in v["pins"]:
            spin.setdefault(key(rd, pn), set()).add(n)
    diffs, board_only, renamed, matched = [], [], [], set()
    items = sorted(board_facts["nets"].items())
    # net có chân cụ thể (không phải linh kiện 2 chân) trước: chúng xác định net schematic; net chỉ có chân linh kiện
    # 2 chân (vd. đoạn tụ -> connector khi PDF thiếu chân connector) lấy net còn lại
    items.sort(key=lambda kv: not any(key(rd, pn)[1] != "*" and key(rd, pn) in spin for rd, pn in kv[1]))
    for n, bpins in items:
        B = {key(rd, pn) for rd, pn in bpins}
        known = {p for p in B if p in spin}
        unknown = sorted([rd, pn] for rd, pn in bpins if key(rd, pn) not in known)
        if unknown:
            board_only.append({"item": n, "pins": unknown})
        if not known:
            continue
        exact = [p for p in known if p[1] != "*"]
        if exact:
            S = set().union(*(spin[p] for p in exact))
        else:
            S = set.intersection(*(spin[p] for p in known)) - matched
            if len(S) != 1:                       # không xác định được (chỉ biết chân linh kiện 2 chân): thông tin
                if not unknown:
                    board_only.append({"item": n, "pins": sorted(list(x) for x in bpins)})
                continue
        bp = sorted(list(x) for x in bpins)
        if len(S) != 1:
            diffs.append({"item": n, "kind": "pin_mismatch", "board": bp,
                          "schematic": {s: sorted([rd, pn] for rd, pn in snets[s]["pins"] if rd in fc)
                                        for s in sorted(S)}, "probable": False})
            matched |= S
            continue
        s = next(iter(S))
        matched.add(s)
        SP = {key(rd, pn) for rd, pn in snets[s]["pins"] if rd in fc}
        if (known - SP) or (SP - B):
            diffs.append({"item": n, "kind": "pin_mismatch", "board": bp,
                          "schematic": sorted([rd, pn] for rd, pn in snets[s]["pins"] if rd in fc), "probable": False})
        elif s != n:
            renamed.append({"board": n, "schematic": s})
    for rd, c in sorted(fc.items()):
        s = scomps.get(rd) or next((v for k, v in scomps.items() if k.upper() == rd.upper()), None)
        if s is None:
            if not any(b["item"] == rd for b in board_only):
                board_only.append({"item": rd, "pins": []})
            continue
        if c.get("numpins") == 2:
            a, b = si_value(c.get("value")), si_value(s.get("value"))
            if a is not None and b is not None and abs(a - b) > 0.01 * max(abs(a), abs(b), 1e-30):
                diffs.append({"item": rd, "kind": "series_value", "board": c["value"], "schematic": s["value"],
                              "probable": False})
    # net schematic nối >= 2 linh kiện của interface nhưng không khớp net nào của board
    pats = [p for p in (patterns or []) if p]
    netlist = sch.get("source") == "netlist"
    if not netlist or pats:
        for n, v in sorted(snets.items()):
            if n in matched or (netlist and not any(fnmatch.fnmatchcase(n, p) or n == p for p in pats)):
                continue
            rds = {rd for rd, _ in v["pins"]} & set(fc)
            if len(rds) >= 2:
                diffs.append({"item": n, "kind": "missing_on_board", "board": None, "schematic": sorted(rds),
                              "probable": False})
    return {"diffs": diffs, "board_only": board_only, "renamed": renamed}


def diff(board_facts, sch, patterns=()):
    """board_facts (từ _facts) vs schematic / netlist -> khác biệt THẬT [{item, kind, board, schematic, probable}]."""
    return compare(board_facts, sch, patterns)["diffs"]


# ----------------------------------------------------------------------------- confirm
def validate_content(content, facts, board_nets, diffs, recut_diffs=None):
    """Kiểm tra nội dung người dùng chốt. Trả content đã chuẩn hoá. Lỗi -> CopilotInputError."""
    if not isinstance(content, dict):
        raise CopilotInputError("content", "JSON object {comp_a, comp_b, nets, diff_groups, series}", content)
    a, b = content.get("comp_a"), content.get("comp_b")
    for k, rd in (("comp_a", a), ("comp_b", b)):
        if rd not in facts["components"]:
            raise CopilotInputError(k, "end component from isim_trace (re-run isim_trace for another one)", rd)
    if a == b:
        raise CopilotInputError("comp_b", "a component different from comp_a", b)
    nets = content.get("nets") or []
    if not nets:
        raise CopilotInputError("nets", "at least one signal net", nets)
    bn = set(board_nets)
    bad = [n for n in nets if n not in bn]
    if bad:
        raise CopilotInputError("nets", "nets on the board", bad)
    for g in content.get("diff_groups") or []:
        if not set(g) <= set(nets):
            raise CopilotInputError("diff_groups", "groups made of the agreed nets", g)
    series = content.get("series") or {}
    for rd, v in series.items():
        c = facts["components"].get(rd)
        if not c:
            raise CopilotInputError("series", "series part from isim_trace", rd)
        if c.get("numpins") != 2:
            raise CopilotInputError("series", "2-pin part", rd)
    res = {d["item"]: d.get("resolution") for d in content.get("schematic_diffs") or []}
    open_ = [d["item"] for d in diffs if not (res.get(d["item"]) or d.get("resolution"))]
    if open_:
        raise CopilotInputError("schematic_diffs", "a resolution for every board / schematic difference", open_)
    rres = {(d.get("item"), str(d.get("ref"))): d.get("resolution") for d in content.get("recut_diffs") or []
            if isinstance(d, dict)}
    ropen = [f"{d['item']} {d['ref']}" for d in recut_diffs or []
             if not (rres.get((d["item"], str(d["ref"]))) or d.get("resolution"))]
    if ropen:
        raise CopilotInputError("recut_diffs", "a resolution for every change since the previous run", ropen)
    structural = dict(content.get("structural") or structural_defaults())
    from ..cut_board import config
    types = {r["key"]: r["type"] for r in _template_rows()}
    for k, v in structural.items():
        if k not in types or not (k.startswith(STRUCTURAL_PREFIX) or k in STRUCTURAL_KEYS):
            raise CopilotInputError("structural", "cutout.* / series.keep template keys", k)
        try:
            config.coerce(v, types[k])
        except ValueError as ex:
            raise CopilotInputError(k, types[k], v) from ex
    from ..cut_board import end_gnd as EG                               # 022 US5: hệ số tay từng đầu
    ef, ef_err = EG.validate_end_factors(content.get("end_factors"), [a, b])
    if ef_err:
        raise CopilotInputError("end_factors", "{refdes: factor > 0} for the ends (empty = automatic)", ef_err)
    return {"comp_a": a, "comp_b": b, "nets": sorted(nets), "diff_groups": content.get("diff_groups") or [],
            **({"end_factors": ef} if ef else {}),
            "series": {rd: {"nets": list(v.get("nets") or [])} for rd, v in series.items()},
            "schematic_diffs": [dict(d, resolution=res.get(d["item"]) or d.get("resolution")) for d in diffs],
            **({"recut_diffs": [dict(d, resolution=rres.get((d["item"], str(d["ref"]))) or d.get("resolution"))
                                for d in recut_diffs]} if recut_diffs is not None else {}),
            "structural": structural}


def confirm(request_id, name, content, user_words=""):
    """GATE A = lời đồng ý DUY NHẤT của kỹ sư (035): nội dung + vùng cut dự tính + review đã đọc."""
    req = R.load(request_id)
    st = R.get_state(req["request_id"], name)
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except ValueError as ex:
            raise CopilotInputError("content", "JSON object", content[:80]) from ex
    board_nets = R._rjson(os.path.join(R.work_dir(req), "board_nets.json"), []) or []
    c = validate_content(content, st.get("board_facts") or {"components": {}}, board_nets,
                         st.get("schematic_diffs") or [], st.get("recut_diffs"))
    from . import review as RVW
    if st["step"] != "started" and st.get("content") == c:              # 025: interface đã qua GATE A, không đổi
        if RVW.gate_status(req["request_id"], name, c)["status"] == "ready":   # 035: review mới (board đổi) -> duyệt lại
            pv = _preview_gate(req["request_id"], name, c)
            return {"name": name, "step": st["step"], "unchanged": True,
                    "approval": RVW.approve(req["request_id"], name, pv, user_words, c)}
        return {"name": name, "step": st["step"], "unchanged": True}
    RVW.require(req["request_id"], name, c)                             # 025/035: review hiện hành + report HTML
    pv = _preview_gate(req["request_id"], name, c)                      # 022/035: vùng cut dự tính, không lỗi
    if st["step"] != "started":
        keep = RVW._review_section(req["request_id"], name)
        R.advance(req["request_id"], name, "started", "content changed -> redo cut / settings")
        if keep:                                                        # review của nội dung mới giữ lại (replace đã cất mục cũ)
            from . import user_settings as U
            U.update(req["request_id"], name, review=keep)
    approval = RVW.approve(req["request_id"], name, pv, user_words, c)  # 035: lời đồng ý gắn với review này
    R.set_state(req["request_id"], name, "content agreed", content=c, content_agreed_at=R._now())
    st = R.advance(req["request_id"], name, "content_agreed")
    from . import user_settings as U
    U.update(req["request_id"], name, content={k: v for k, v in c.items() if k != "structural"},
             structural=c.get("structural") or {}, content_agreed_at=st["content_agreed_at"],
             recut_from=st.get("recut_from"), trace_args=st.get("trace_args"),
             board_facts=st.get("board_facts"))
    md = content_md(name, c, st.get("board_facts"), c["schematic_diffs"], st.get("end_types") or {},
                    title=f"Agreed {st['content_agreed_at']}")
    with open(os.path.join(R.iface_dir(req["request_id"], name), "content.md"), "w", encoding="utf-8") as f:
        f.write(md + "\n")
    return {"name": name, "step": st["step"], "content": c, "content_md": md, "approval": approval,
            "user_settings": U.path(req["request_id"])}


def _preview_gate(rid, name, c):
    """022 + 035: GATE A cần preview (isim_cut_preview = vùng cut dự tính kỹ sư đã xem) tính với CÙNG thông số và
    không lỗi (hệ số tay không giữ được pin GND...). -> đường dẫn preview.json."""
    from . import cut_preview as CP
    try:
        P, ch, nets, ends, ef, errs, _ = CP.inputs(c, name)
    except CopilotInputError:
        return None                                                     # nội dung sai: validate_content đã báo
    if errs:
        return None
    key = CP.settings_key(P, ef, nets)
    p = CP.last(rid, name)
    if not p or p.get("key") != key:
        raise CopilotInputError("preview", "isim_cut_preview with these cut settings first (the user approves the "
                                           "cut area he saw)", "no preview" if not p else "preview of other settings")
    bad = CP.errors_for(rid, name, key)
    if bad:
        raise CopilotInputError("end_factors", "cut settings whose preview has no error (fix or clear the end factor, "
                                               "then isim_cut_preview again)", bad)
    return os.path.join(R.iface_dir(rid, name), "preview.json")


# ----------------------------------------------------------------------------- markdown
def content_md(name, c, facts, diffs, end_types, title=""):
    facts = facts or {"components": {}, "nets": {}}
    lines = [f"# Interface {name}" + (f" - {title}" if title else ""), ""]
    if c.get("recut_diffs") is not None:                               # cut lại (004): thay đổi trước tiên
        rd_ = c["recut_diffs"]
        lines += ["## Changes since previous run",
                  report.table(["Item", "Ref", "Old", "New", "Resolution"],
                               [[d["item"], d["ref"], d.get("old"), d.get("new"), d.get("resolution") or "(open)"]
                                for d in rd_]) if rd_ else "No difference since the previous run.", ""]
    comp_rows = []
    for role, rd in (("end A", c.get("comp_a")), ("end B", c.get("comp_b"))):
        f = facts["components"].get(rd, {})
        comp_rows.append([role, rd, f.get("part"), end_types.get(rd), f.get("numpins"),
                          len(f.get("signal_pins", {})), f.get("gnd_pins")])
    for rd in sorted(c.get("series") or {}):
        f = facts["components"].get(rd, {})
        comp_rows.append(["series (0 ohm)", rd, f.get("part"), f.get("type"), f.get("numpins"),
                          len(f.get("signal_pins", {})), f.get("value")])
    lines += ["## Components", report.table(["Role", "Refdes", "Part", "Type", "Pins", "Signal pins", "GND pins / value"],
                                            comp_rows), ""]
    grp = {n: i + 1 for i, g in enumerate(c.get("diff_groups") or []) for n in g}
    lines += ["## Nets", report.table(["Net", "Group", "Pins on ends"],
                                      [[n, grp.get(n, ""), " ".join(".".join(p) for p in facts["nets"].get(n, []))]
                                       for n in c.get("nets") or []]), ""]
    if c.get("structural"):
        lines += ["## Cut settings (agreed with content; change = re-cut)",
                  report.table(["Key", "Value"], sorted(c["structural"].items()) +
                               [[f"cutout.end_factor.{rd}", f] for rd, f in sorted((c.get("end_factors") or {}).items())]),
                  ""]
    if diffs:
        lines += ["## Board vs schematic", report.table(
            ["Item", "Kind", "Board", "Schematic", "Probable", "Resolution"],
            [[d["item"], d["kind"], d["board"], d["schematic"], "yes" if d.get("probable") else "",
              d.get("resolution") or "(open)"] for d in diffs]), ""]
    return "\n".join(lines)
