"""Sửa layout theo plan JSON: 1 lần mở EDB (bản COPY), chạy hết op, lưu, đọc lại vùng, kiểm tra, ảnh, changes.md.

    region(board, box)        đọc một vùng (chỉ đọc) -> tóm tắt + ảnh từng lớp, để Claude lập plan
    edit(plan)                áp plan vào bản copy của board, trả kết quả + check + đường dẫn

Board gốc KHÔNG bao giờ được mở để ghi: edit() copy .aedb sang thư mục kết quả rồi mới mở bản copy.
"""
import datetime
import json
import os
import shutil
import time

import math

from ..core import config
from ..core.edb import aedb_path, edb_session
from ..core.errors import CopilotInputError
from ..core.unique import claim_dir
from . import check as CK
from . import extract as EX
from . import render
from .geom import Region, to_geom
from .ops import OPS, Editor, op_bbox

TEMPLATE = config.template_path("layout_edit")


def defaults():
    return {r["key"]: float(r["default"]) for r in config.template_rows(TEMPLATE)}


def _work_dir(aedb):
    return os.path.join(os.path.dirname(aedb), "Ansys AEDT Copilot", "layout_edit")


def _session(path, cell="", readonly=False):
    """Phiên EDB (core.edb) với bản AEDT của config.yaml; luôn đóng khi ra khỏi khối."""
    return edb_session(path, cell or None, readonly, config.machine()["aedt_version"])


def _box(name, v):
    """'x0,y0,x1,y1' hoặc list 4 số (mm) -> [x0, y0, x1, y1] float; x0 < x1, y0 < y1."""
    try:
        b = [float(x) for x in (v.split(",") if isinstance(v, str) else v)]
    except (TypeError, ValueError):
        raise CopilotInputError(name, "4 numbers x0,y0,x1,y1 (mm)", v) from None
    if len(b) != 4 or not all(math.isfinite(x) for x in b) or b[0] >= b[2] or b[1] >= b[3]:
        raise CopilotInputError(name, "4 numbers x0,y0,x1,y1 (mm) with x0 < x1 and y0 < y1", v)
    return b


class _Log:
    def __init__(self, fn):
        self.t0 = time.time()
        self.fn = fn or (lambda s: None)
        self.times = {}

    def __call__(self, *a):
        self.fn(f"[{time.time() - self.t0:7.1f}s] " + " ".join(str(x) for x in a))

    def mark(self, name, t):
        self.times[name] = round(time.time() - t, 1)


# ============================================================================ region
def region(board, bbox, layers=None, nets=None, cell="", images=True, log=None):
    aedb = aedb_path(board)
    bbox = _box("bbox", bbox)
    log = _Log(log)
    t = time.time()
    D, source = _read_snapshot(aedb, cell, bbox, layers or None, (), log, build=True)
    if D is None:
        with _session(aedb, cell, readonly=True) as edb:
            D = EX.extract_region(edb, bbox, layers or None, log=log)
    log.mark("read", t)
    R = Region(D)
    want_nets = set(nets or [])
    summary = {}
    for L in R.SIG:
        items = R.LAY.get(L, [])
        if not items:
            continue
        polys = sorted([(i, n, round(g.intersection(R.box).area, 2)) for n, t_, g, i in items if t_ != "path"],
                       key=lambda x: -x[2])
        traces = {}
        for n, t_, g, i in items:
            if t_ == "path":
                traces.setdefault(n, 0)
                traces[n] += 1
        vias = {}
        for v in R.inst:
            if R.on_layer(v, L) and not v["pin"]:
                vias[f"{v['net']} {v['pd']}"] = vias.get(f"{v['net']} {v['pd']}", 0) + 1
        summary[L] = {"polygons_in_box (id, net, mm2)": [p for p in polys if p[2] > 0.05][:25],
                      "traces_per_net": dict(sorted(traces.items(), key=lambda kv: -kv[1])[:15]),
                      "vias_per_net_padstack": dict(sorted(vias.items(), key=lambda kv: -kv[1])[:15])}
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = claim_dir(os.path.join(_work_dir(aedb), "_region", stamp))   # 024: _2 khi trùng giây
    with open(os.path.join(out_dir, "region.json"), "w", encoding="utf-8") as f:
        json.dump(D, f)
    imgs = []
    if images:
        hi = list(want_nets) if want_nets else None
        for L in [l for l in R.SIG if l in summary]:
            if layers and L not in layers:
                continue
            if hi is None:
                area = {}
                for n, t_, g, i in R.LAY[L]:
                    area[n] = area.get(n, 0) + g.intersection(R.box).area
                nets_l = [n for n, a in sorted(area.items(), key=lambda kv: -kv[1]) if a > 0.5][:6]
            else:
                nets_l = [n for n in hi]
            imgs.append(render.draw_layer(R, L, nets_l, bbox, os.path.join(out_dir, f"{L}.png"), f"{L}  (region)",
                                          px=int(defaults()["image_px"])))
    pdefs = {k: {"hole": v.get("hole"), "pad_mm": {l: p[1] for l, p in v["pads"].items() if isinstance(p, list)}}
             for k, v in D["pdefs"].items()}
    return {"aedb": aedb, "box": bbox, "signal_layers": R.SIG, "layers": summary, "padstacks": pdefs,
            "components": D["comps"], "vias": via_list(R, want_nets),
            "region_json": os.path.join(out_dir, "region.json"), "images": imgs, "seconds": log.times,
            "source": source}


def _use_snapshot():
    from ..layout_snapshot.api import _defaults
    return _defaults()["use_region"]


def _read_snapshot(aedb, cell, bbox, layers, extra_pdefs, log, build):
    """029: vùng đọc từ layout snapshot (extract_region không đổi trên SnapEdb) -> (D, source); không dùng được ->
    (None, source live + warning). build=False (layout_edit before): chỉ dùng cửa sổ đã có."""
    from ..layout_snapshot import SnapshotFallback, SnapshotMissing
    from ..layout_snapshot.region import open_for_region
    if not _use_snapshot():
        return None, {"kind": "live"}
    try:
        snap, src = open_for_region(aedb, cell, bbox, build=build, version=config.machine()["aedt_version"], log=log)
        t = time.time()
        D = EX.extract_region(snap, bbox, layers, extra_pdefs=extra_pdefs, log=log)
        src["extract_s"] = round(time.time() - t, 2)
        return D, src
    except SnapshotFallback as ex:
        why = ex.reason + (f" (ids {ex.ids[:20]})" if ex.ids else "")
    except SnapshotMissing as ex:
        why = f"snapshot data missing: {ex}"
    except (OSError, ValueError, RuntimeError, TimeoutError) as ex:
        why = f"snapshot error: {str(ex)[:300]}"
    log("[snapshot] live read:", why)
    return None, {"kind": "live", "warning": why}


VIA_LIST_MAX = 200


def via_list(R, nets=None, limit=VIA_LIST_MAX):
    """016: via (không phải pin) trong vùng: id cho op delete. nets -> chỉ các net đó. Quá limit -> cắt + ghi chú."""
    vs = sorted((v for v in R.inst if not v["pin"] and (not nets or v["net"] in nets)),
                key=lambda v: (v["net"], v["x"], v["y"]))
    rows = [[v["id"], v["net"], v["pd"], round(v["x"], 3), round(v["y"], 3), v["sl"], v["el"]] for v in vs[:limit]]
    out = {"columns": ["id", "net", "padstack", "x_mm", "y_mm", "from", "to"], "rows": rows, "total": len(vs)}
    if len(vs) > limit:
        out["note"] = f"first {limit} of {len(vs)}: pass nets= or a smaller box (all in region.json instances)"
    return out


# ============================================================================ edit
def _load_plan(plan):
    """dict / chuỗi JSON / đường dẫn file JSON -> dict plan đã kiểm tra board, ops, region (trước khi copy)."""
    if not isinstance(plan, dict):
        s = str(plan).strip()
        try:
            if s.startswith("{"):
                plan = json.loads(s)
            else:
                with open(s.strip('"'), encoding="utf-8") as f:
                    plan = json.load(f)
        except (OSError, ValueError) as ex:
            raise CopilotInputError("plan", "plan object, JSON text or JSON file", f"{s[:200]} ({ex})") from ex
    if not isinstance(plan, dict):
        raise CopilotInputError("plan", "JSON object", plan)
    if "board" not in plan:
        raise CopilotInputError("board", "board path in plan")
    ops = plan.get("ops")
    if not isinstance(ops, list) or not ops or not all(isinstance(o, dict) for o in ops):
        raise CopilotInputError("ops", "non-empty list of op objects", ops)
    for o in ops:
        if o.get("op") not in OPS:
            raise CopilotInputError("op", "one of " + ", ".join(OPS), o.get("op"))
    if plan.get("region"):
        _box("region", plan["region"])
    return plan


def _copy_aedb(src, dst):
    def ign(d, names):
        return [n for n in names if n.endswith((".bak", ".tmp", "+", ".lock")) or n == "edb.def+"]
    shutil.copytree(src, dst, ignore=ign)


def edit(plan, log=None):
    P = _load_plan(plan)
    src = aedb_path(P["board"])
    if not P.get("region") and all(op_bbox(o) is None for o in P["ops"]):   # 016: vd. plan chỉ có delete
        raise CopilotInputError("region", "region [x0, y0, x1, y1] mm (plan has no op with a position, e.g. only delete)")
    log = _Log(log)
    name = P.get("name") or "edit"
    for ch in '<>:"/\\|?* ':
        name = name.replace(ch, "_")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.abspath(P.get("out_dir") or os.path.join(_work_dir(src), f"{name}_{stamp}"))
    dst = os.path.join(out_dir, os.path.splitext(os.path.basename(src))[0] + f"_{name}.aedb")
    if os.path.abspath(dst).lower() == src.lower() or (P.get("out_dir") and os.path.exists(dst)):
        raise RuntimeError(f"Thư mục kết quả đã có / trùng board gốc: {dst}")
    rules = defaults()
    rules.update(P.get("rules") or {})
    if P.get("out_dir"):
        os.makedirs(out_dir, exist_ok=True)
    else:                                                # 024: thư mục mới nguyên tử, _2 khi trùng giây
        out_dir = claim_dir(out_dir)
        dst = os.path.join(out_dir, os.path.basename(dst))
    t = time.time()
    _copy_aedb(src, dst)
    log.mark("copy", t)
    log("copy ->", dst)
    with open(os.path.join(out_dir, "plan.json"), "w", encoding="utf-8") as f:
        json.dump(P, f, ensure_ascii=False, indent=1)

    ops = P["ops"]                                       # đã kiểm tra trong _load_plan (trước khi copy)
    if P.get("region"):
        bbox = _box("region", P["region"])
    else:
        bbs = [b for b in (op_bbox(o) for o in ops) if b]
        m = rules["region_margin"]
        bbox = [min(b[0] for b in bbs) - m, min(b[1] for b in bbs) - m, max(b[2] for b in bbs) + m, max(b[3] for b in bbs) + m]
    results, err = [], None
    extra_pd = [o["padstack"] for o in ops if o["op"] == "via"]
    t = time.time()
    # 029: bản copy vừa chép từ src -> vùng "before" = snapshot của src nếu đã có cửa sổ chứa vùng (không build ở đây)
    BD, before_source = _read_snapshot(src, P.get("cell", ""), bbox, None, extra_pd, log, build=False)
    t_snap = time.time() - t
    with _session(dst, P.get("cell", "")) as edb:
        t = time.time()
        if BD is None:
            BD = EX.extract_region(edb, bbox, extra_pdefs=extra_pd, log=log)
        B = Region(BD)
        log.times["read_before"] = round(t_snap + time.time() - t, 1)
        E = Editor(edb, B, rules, log)
        t = time.time()
        for k, o in enumerate(ops):
            t1 = time.time()
            try:
                r = OPS[o["op"]](E, o)
                results.append({"#": k + 1, "op": o["op"], "ok": True, "result": r, "seconds": round(time.time() - t1, 1)})
                log(f"op {k + 1} {o['op']} OK ({time.time() - t1:.1f} s)")
            except Exception as ex:
                err = f"op {k + 1} ({o['op']}): {ex}"
                results.append({"#": k + 1, "op": o["op"], "ok": False, "error": str(ex)})
                log("LỖI", err)
                break
        cleanup = E.cleanup_merged() if not err else {}
        log.mark("edit", t)
        if not err:
            t = time.time()
            edb.save()
            log.mark("save", t)
    if not err:
        # kiểm tra trên FILE ĐÃ LƯU (mở lại, chỉ đọc): trong phiên sửa, connectivity EDB (LayoutInstance) không thấy
        # void vừa thêm -> via mới "chạm" GND/plane khác (B04 neck: 6676 đối tượng thay vì 30)
        t = time.time()
        with _session(dst, P.get("cell", ""), readonly=True) as edb:
            log.mark("reopen", t)
            t = time.time()
            A = Region(EX.extract_region(edb, bbox, extra_pdefs=extra_pd, log=log))
            log.mark("read_after", t)
            t = time.time()
            touched = {(c["layer"], c["net"]) for key in ("created", "deleted", "voids", "traces") for c in E.ch[key]}
            touched |= {(L, c["net"]) for c in E.ch.get("deleted_vias", []) for L in (c["from"], c["to"])  # 016
                        if L in B.SIG}
            checks = CK.run_checks(B, A, E.ch, rules, touched, P.get("checks"), edb)
            log.mark("check", t)
    if err:
        shutil.rmtree(dst, ignore_errors=True)
        with open(os.path.join(out_dir, "error.json"), "w", encoding="utf-8") as f:
            json.dump({"error": err, "ops": results}, f, ensure_ascii=False, indent=1, default=str)
        return {"ok": False, "error": err, "ops": results, "out_dir": out_dir,
                "note": "Không lưu gì; bản copy đã xoá. Sửa plan rồi chạy lại."}
    # ảnh trước / sau
    t = time.time()
    imgs = []
    newv = [(v["x"], v["y"]) for v in E.ch["vias"]]
    layers = sorted({L for L, n in touched}, key=A.SIG.index)
    for L in layers:
        nets_l = sorted({n for LL, n in touched if LL == L})
        nets_l += [n for n in sorted({v["net"] for v in E.ch["vias"]}) if n not in nets_l]
        view = P.get("view") or bbox
        for tag, R in (("before", B), ("after", A)):
            imgs.append(render.draw_layer(R, L, nets_l, view, os.path.join(out_dir, "img", f"{L}_{tag}.png"),
                                          f"{L}  {tag}", new_vias=newv if tag == "after" else (),
                                          px=int(rules["image_px"])))
    log.mark("images", t)
    ch = {k: v for k, v in E.ch.items() if not k.startswith("_")}
    ch["cleanup_merged_voids"] = cleanup
    out = {"ok": True, "aedb": dst, "source": src, "out_dir": out_dir, "region": bbox, "ops": results,
           "checks": checks, "summary": {s: sum(c["status"] == s for c in checks) for s in ("PASS", "WARN", "FAIL")},
           "images": imgs, "seconds": log.times, "total_s": round(time.time() - log.t0, 1),
           "before_source": before_source}
    with open(os.path.join(out_dir, "changes.json"), "w", encoding="utf-8") as f:
        json.dump(ch, f, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(out_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    out["changes_md"] = write_md(P, out, ch)
    return out


def write_md(P, out, ch):
    L = [f"# Layout edit: {P.get('name', 'edit')}", "",
         f"- Board gốc (không sửa): `{out['source']}`",
         f"- Kết quả: `{out['aedb']}`",
         f"- Thời gian máy chạy: {out['total_s']} s ({', '.join(f'{k} {v}s' for k, v in out['seconds'].items())})",
         f"- Kiểm tra: PASS {out['summary']['PASS']}, WARN {out['summary']['WARN']}, FAIL {out['summary']['FAIL']}", ""]
    if P.get("purpose"):
        L += ["## Mục đích", "", P["purpose"], ""]
    L += ["## Thay đổi", "", "| # | Op | Kết quả |", "|---|---|---|"]
    for r in out["ops"]:
        res = r.get("result", {})
        brief = {k: v for k, v in res.items() if k not in ("points", "pieces", "polygons", "cleared_pours", "ids")}
        L.append(f"| {r['#']} | {r['op']} | {json.dumps(brief, ensure_ascii=False)} |")
    L += ["", "## Kiểm tra", "", "| Mục | Kết quả | Chi tiết |", "|---|---|---|"]
    for c in out["checks"]:
        d = c["detail"]
        d = "; ".join(map(str, d)) if isinstance(d, list) else (json.dumps(d, ensure_ascii=False) if isinstance(d, dict) else str(d))
        L.append(f"| {c['check']} | {c['status']} | {d[:600]} |")
    L += ["", "## Ảnh", ""] + [f"- `{p}`" for p in out["images"]]
    L += ["", f"Chi tiết: `{os.path.join(out['out_dir'], 'changes.json')}`, `result.json`, `plan.json`."]
    p = os.path.join(out["out_dir"], "changes.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    return p
