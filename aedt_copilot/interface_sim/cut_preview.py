"""Xem trước vùng cut ở GATE A (feature 022, contract: specs/022-cut-keeps-end-gnd/contracts/cut-preview.md).

Mở board gốc CHỈ ĐỌC (như isim_trace), tính vùng cutout bằng ĐÚNG hàm cắt dùng (cutter.cut_extent: hệ số nền + luật
GND ở 2 đầu + hệ số tay từng đầu) -> bảng từng đầu + ảnh vùng cut + ảnh zoom từng đầu mở rộng. Chỉ ghi vào thư mục
interface của request (preview/, preview.json); board không bị ghi gì.
"""
import json
import os
import time

from ..core.errors import CopilotInputError
from . import report, request as R

BEFORE_CUT = ("started", "content_agreed")
AFTER_CUT_REASON = "already cut: change the cut settings = Gate A again (isim_confirm_content) + re-cut"


def snapshot_on(P=None):
    """027: template snapshot.use_for_preview (job) -> preview đọc board từ layout snapshot."""
    from ..cut_board import config
    v = (config.defaults().get("snapshot") or {}).get("use_for_preview", True)
    return bool(v)


def _content(st):
    return st.get("content") or st.get("proposal")


def settings_key(P, end_factors, nets):
    """Khoá so sánh preview <-> cut: thông số cutout + series.keep + hệ số tay + net (JSON chuẩn). Thuần."""
    cut = {k: v for k, v in sorted((P.get("cutout") or {}).items()) if k != "mode"}
    return json.dumps({"cutout": cut, "series_keep": (P.get("series") or {}).get("keep"),
                       "end_factors": {k: float(v) for k, v in sorted((end_factors or {}).items())},
                       "nets": sorted(nets)}, sort_keys=True, default=str)


def structural_for(c, structural=None):
    """structural đã lưu (hoặc mặc định) + giá trị form. Khoá lạ -> lỗi nêu tên khoá."""
    from .content import STRUCTURAL_KEYS, STRUCTURAL_PREFIX, structural_defaults
    s = dict(c.get("structural") or structural_defaults())
    for k, v in (structural or {}).items():
        if not (str(k).startswith(STRUCTURAL_PREFIX) or k in STRUCTURAL_KEYS) or k not in structural_defaults():
            raise CopilotInputError("structural", "cutout.* / series.keep template keys (cut settings)", k)
        s[k] = v
    return s


def inputs(c, name, structural=None, end_factors=None):
    """-> (P, ch, nets, ends, end_factors sạch, errors[]). Không mở EDB."""
    from ..cut_board import cutter, end_gnd as EG
    from .cut import channel, params_for
    s = structural_for(c, structural)
    P, errs = params_for(dict(c, structural=s))
    errors = list(errs)                                               # chỉ có structural: lỗi = lỗi cut settings
    ef_in = (c.get("end_factors") or {}) if end_factors is None else end_factors
    ef, ef_err = EG.validate_end_factors(ef_in, [c["comp_a"], c["comp_b"]])
    errors += ef_err
    ch = channel(name, c)
    nets = ends = None
    if not errors:
        nets, ends, _, _ = cutter.channel_sets(ch, P)
    return P, ch, nets, ends, ef, errors, s


def rows(eg):
    """Bảng từng đầu (US4). Thuần."""
    out = []
    for rd, e in (eg.get("ends") or {}).items():
        base_ok = "yes" if e.get("result") == "met" else ("n/a" if e.get("result") == "no_gnd_pin_on_board" else "no")
        if e.get("result") == "manual":
            base_ok = "yes" if e.get("base_inside") else "no"
        fac = e.get("factor")
        out.append({"refdes": rd, "gnd_pins_on_board": e.get("gnd_pins_on_board"),
                    "gnd_inside_at_base": base_ok, "result": e.get("result"),
                    "factor_used": fac, "manual": e.get("result") == "manual",
                    "added_mm2": e.get("added_mm2") or 0.0,
                    "gnd_gained": [p["pin"] for p in e.get("gnd_pins_gained") or []] or
                                  ([e["gnd_pin_inside"]] if e.get("gnd_pin_inside") else []),
                    "other_nets": e.get("other_nets") or [], "error": e.get("error")})
    return out


def table_md(name, rws, area, size, image, zooms, errors):
    lines = [f"## Cut preview {name}", "", f"Extent {area} mm2, {size[0]} x {size[1]} mm. Image: {image}"]
    for rd, z in (zooms or {}).items():
        lines.append(f"Zoom {rd}: {z}")
    lines += ["", report.table(["Refdes", "GND pins on board", "GND inside at base", "Factor used", "Added mm2",
                                "GND pin / pad gained", "Other nets in added area (not kept)", "Error"],
                               [[r["refdes"], r["gnd_pins_on_board"], r["gnd_inside_at_base"],
                                 "-" if r["factor_used"] is None else
                                 f"{r['factor_used']} ({'manual' if r['manual'] else 'auto'})",
                                 r["added_mm2"], ", ".join(r["gnd_gained"]) or "-",
                                 ", ".join(r["other_nets"][:12]) + (" ..." if len(r["other_nets"]) > 12 else "") or "-",
                                 r["error"] or ""] for r in rws])]
    if errors:
        lines += ["", "**Errors (Gate A / cut refused until fixed or cleared):**"] + [f"- {e}" for e in errors]
    return "\n".join(lines)


def preview(request_id, name, structural=None, end_factors=None, version=None):
    from ..core.config import machine
    from ..core.edb import edb_session
    from ..core import geometry as G
    from ..cut_board import cutter, end_gnd as EG
    req = R.load(request_id)
    rid = req["request_id"]
    st = R.get_state(rid, name)
    if st["step"] not in BEFORE_CUT:
        raise CopilotInputError("step", AFTER_CUT_REASON, st["step"])
    c = _content(st)
    if not c:
        raise CopilotInputError("name", "interface traced first (isim_trace)", name)
    P, ch, nets, ends, ef, errors, s = inputs(c, name, structural, end_factors)
    if errors:
        return {"name": name, "ok": False, "validation": True, "errors": errors,
                "table_md": "Cut settings invalid:\n" + "\n".join(f"- {e}" for e in errors)}
    d = R.iface_dir(rid, name)
    out = os.path.join(d, "preview")
    lines = []
    lg = lambda *a: lines.append(" ".join(map(str, a)))
    series = sorted(ch.get("series") or {})
    pts = eg = sc = None
    source = {"kind": "live"}
    t0 = time.perf_counter()
    if snapshot_on(P):                                                  # 027: board đọc từ layout snapshot
        from .. import layout_snapshot as LS
        from ..core.edb import aedb_path
        from ..layout_snapshot import preview as SP
        try:
            with SP.open_for_preview(aedb_path(req["board"]), req.get("cell") or "", P, nets,
                                     list(ends) + [r for r in series if r not in ends],
                                     version or machine()["aedt_version"], lg) as (sedb, ext, source):
                pts, eg = cutter.cut_extent(sedb, P, nets, ends, lg, end_factors=ef, strict=False, extent=ext)
                sc = EG.scene(sedb, P, nets, ends, series, eg, pts)
        except (LS.SnapshotFallback, LS.SnapshotMissing) as ex:
            ids = getattr(ex, "ids", [])
            source = {"kind": "live", "warning": f"layout snapshot not used ({ex}); board read live" +
                      (f"; ids {ids[:20]}" if ids else "")}
            pts = eg = sc = None
            lines.clear()
    if sc is None:
        with edb_session(req["board"], req.get("cell") or None, True, version or machine()["aedt_version"]) as edb:
            pts, eg = cutter.cut_extent(edb, P, nets, ends, lg, end_factors=ef, strict=False)
            sc = EG.scene(edb, P, nets, ends, series, eg, pts)
    source["seconds"] = round(time.perf_counter() - t0, 2)
    source.pop("extent_cache", None) if not isinstance(source.get("extent_cache"), dict) else None
    os.makedirs(out, exist_ok=True)
    image = EG.render_scene(EG.final_scene(sc), os.path.join(out, "cut_region.png"),          # 035: vùng cut CUỐI
                            title=f"{name} - final cut region")
    detail = EG.render_scene(sc, os.path.join(out, "cut_detail.png"), title=f"{name} - detail")  # nền + phần thêm
    zooms = {}
    for rd, e in eg["ends"].items():
        if e.get("result") in ("enlarged", "manual") and e.get("region_mm"):
            r = e["region_mm"]
            zooms[rd] = EG.render_scene(sc, os.path.join(out, f"end_{rd}.png"),
                                        view=[r[0] - 1, r[1] - 1, r[2] + 1, r[3] + 1], title=f"{name} · {rd}")
    x0, y0, x1, y1 = G.bbox_of(pts)
    area = round(G.poly_area(pts), 3)
    size = [round(x1 - x0, 2), round(y1 - y0, 2)]
    rws = rows(eg)
    errs = list(eg.get("errors") or [])
    doc = {"key": settings_key(P, ef, nets), "structural": s, "end_factors": ef, "nets": nets,
           "extent_pts_mm": [list(p) for p in pts], "extent_area_mm2": area, "extent_size_mm": size,
           "end_gnd": {k: v for k, v in eg.items() if k != "base_pts_mm"}, "rows": rws, "errors": errs,
           "image": image, "detail": detail, "zooms": zooms, "time": R._now(), "log": lines, "source": source}
    R.wjson(os.path.join(d, "preview.json"), doc)
    from . import answer
    out = {"name": name, "ok": not errs, "errors": errs, "rows": rws, "image": image, "detail": detail, "zooms": zooms,
           "extent_area_mm2": area, "extent_size_mm": size, "structural": s, "end_factors": ef,
           "ends_lines": ends_lines(rws),
           "table_md": table_md(name, rws, area, size, image, zooms, errs), "preview_json": os.path.join(d, "preview.json"),
           "source": source}
    return answer.attach(out, rid, name)                               # 036: câu trả lời chuẩn (dán nguyên văn)


def ends_lines(rws):
    """035: một dòng mỗi đầu cho câu trả lời ngắn (factor, GND giữ được). Thuần."""
    out = []
    for r in rws:
        f = r.get("factor_used")
        fac = "-" if f is None else f"{f} ({'manual' if r.get('manual') else 'auto'})"
        if r.get("added_mm2"):
            fac += f", +{round(r['added_mm2'], 1)} mm2"
        g = ", ".join(r.get("gnd_gained") or [])
        out.append(f"{r['refdes']}: factor {fac}; GND kept: {g or 'none'}" + (f"; ERROR {r['error']}" if r.get("error")
                                                                                else ""))
    return out


def last(rid, name):
    """preview.json của interface hoặc None."""
    return R._rjson(os.path.join(R.iface_dir(rid, name), "preview.json"))


def errors_for(rid, name, key):
    """Lỗi của preview đã tính với CÙNG thông số (key) -> list; không có preview cùng thông số -> []."""
    p = last(rid, name)
    return list(p.get("errors") or []) if p and p.get("key") == key else []


def compare(rid, name, key, pts):
    """SC-005: extent của cut so với preview cùng thông số -> {compared, equal, area_diff_mm2}."""
    from ..core import geometry as G
    p = last(rid, name)
    if not p or p.get("key") != key:
        return {"compared": False, "reason": "no preview with the agreed cut settings"}
    try:
        from shapely.geometry import Polygon
        diff = Polygon(p["extent_pts_mm"]).buffer(0).symmetric_difference(Polygon(pts).buffer(0)).area
    except Exception:
        diff = abs(G.poly_area(p["extent_pts_mm"]) - G.poly_area(pts))
    return {"compared": True, "equal": diff < 1e-6, "area_diff_mm2": round(diff, 6)}
