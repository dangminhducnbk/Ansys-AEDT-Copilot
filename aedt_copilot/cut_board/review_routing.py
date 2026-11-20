"""Mục 'Signal routing per pair' của báo cáo layout review (feature 033): chỉ để xem (không OK / NOT OK).

Mỗi cặp / bộ 3 (net đầu của mỗi chuỗi net qua linh kiện nối tiếp, ghép theo đuôi tên) một khung thu gọn:
  - hình nhìn từ trên: chỉ trace của các thành viên, màu theo lớp đi dây (P đậm / N nhạt), linh kiện 2 đầu (khung thân
    thật + pad thật) và linh kiện nối tiếp (pad thật), refdes không chồng nhau, đúng tỉ lệ, zoom khoá / mở;
  - mặt cắt ngang (topology) của thành viên đầu từ chân đầu tới chân cuối: lớp, chiều dài từng đoạn, via (stub,
    backdrill), linh kiện nối tiếp; thành viên khác topology vẽ thêm;
  - bảng chiều dài: tổng + từng lớp (= chiều dài trace của review).
Thuần (không EDB): dữ liệu là ch["routing"] do review._review_edb thu trong lượt đo. Mét; HTML tiếng Anh.
"""
import html as H
import math
import re

from . import naming
from . import review_units as U

MM = 1e-3
TOL_VIA, TOL_PIN = 0.15 * MM, 0.30 * MM
LAYER_COLORS = ("#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b", "#17becf", "#e377c2")
STUB = "#ff1493"


def side(layer):
    """2.11.1 (R3): lớp đặt linh kiện -> 'Top' / 'Bottom' (tên lớp ngoài) hoặc tên lớp."""
    n = str(layer or "").strip()
    if n.lower().startswith("top"):
        return "Top"
    if n.lower().startswith("bottom") or n.lower().startswith("bot"):
        return "Bottom"
    return n


_PKG = re.compile(r"(?<![\d.])(0201|0402|0603|0805|1206|1210|2512)(?!\d)")
_UNIT = {"capacitor": "F", "inductor": "H", "resistor": "Ω"}
_PREF = ((1e-12, "p"), (1e-9, "n"), (1e-6, "u"), (1e-3, "m"), (1.0, ""), (1e3, "k"), (1e6, "M"))


def fmt_value(v, ctype=""):
    """045: giá trị linh kiện -> nhãn ('2.2e-07' + Capacitor -> '220nF'; chữ sẵn ('220nF') giữ nguyên; rỗng -> '')."""
    s = str(v if v is not None else "").strip()
    if not s:
        return ""
    try:
        x = float(s)
    except ValueError:
        return s
    if x == 0:
        return "0" + _UNIT.get(str(ctype).lower(), "")
    k, p = next(((k, p) for k, p in reversed(_PREF) if abs(x) >= k * 0.9999), _PREF[0])
    n = x / k
    txt = (f"{n:.3g}").rstrip("0").rstrip(".") if "." in f"{n:.3g}" else f"{n:.3g}"
    return f"{txt}{p}{_UNIT.get(str(ctype).lower(), '')}"


def package_of(part):
    """045: mã cỡ chân (0201 ... 2512) đầu tiên trong tên part; không có -> ''."""
    m = _PKG.search(str(part or ""))
    return m.group(1) if m else ""


def series_text(info):
    """045: '<value> - <package>' của một linh kiện nối tiếp (info = rt['series_info'][rd])."""
    if not isinstance(info, dict):
        return ""
    return " - ".join(x for x in (fmt_value(info.get("value"), info.get("type")), package_of(info.get("part"))) if x)


def ref_label(rt, comp):
    """'U14 (Top)': refdes + lớp đặt (không có lớp -> chỉ refdes)."""
    lay = side((rt.get("comp_layer") or {}).get(comp))
    return f"{comp} ({lay})" if lay else comp


def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


# ----------------------------------------------------------------------------- cặp / bộ 3
def groups(chains):
    """-> [[thành viên]] (cặp / bộ 3 theo tên net đầu của chuỗi; net lẻ = nhóm 1), chain_of {net: [net chuỗi]}."""
    first = [nets[0] for nets in chains.values() if nets]
    chain_of = {n: nets for nets in chains.values() for n in nets}
    gs = [list(g) for g in naming.review_groups(first)]                    # 034: chung luật ghép với các check
    used = {n for g in gs for n in g}
    gs += [[n] for n in first if n not in used]
    return gs, chain_of


# ----------------------------------------------------------------------------- đi dây
def _via_at(vrows, pt):
    v = min(vrows, key=lambda r: _d((r["x"], r["y"]), pt), default=None)
    return v if v and _d((v["x"], v["y"]), pt) <= TOL_VIA else None


def _rng(v):
    r = v.get("range")
    if isinstance(r, str):
        a = r.split(" → ")
        return a[0], a[-1]
    return (r[0], r[-1]) if r else (None, None)


EXACT = 2e-6                                          # 037: đầu path trùng khít (dữ liệu board liền tới ~1 µm)


def _goes_on(grid, used, cur, target):
    """037: còn path chưa dùng nối khít tại cur mà đầu kia gần target hơn cur (trace chưa tới chân)."""
    cx, cy = math.floor(cur[0] / TOL_PIN), math.floor(cur[1] / TOL_PIN)
    here = _d(cur, target)
    for gx in (cx - 1, cx, cx + 1):
        for gy in (cy - 1, cy, cy + 1):
            for i, end, other in grid.get((gx, gy), ()):
                if i not in used and _d(end, cur) <= EXACT and _d(other, target) < here - EXACT:
                    return True
    return False


def walk(nets, comp_a, comp_b, paths, vrows, pins):
    """-> [bước] theo thứ tự từ chân comp_a tới chân comp_b: pin / seg / via / comp. Nối đầu path trong 0.3 mm; đổi
    lớp = via trong 0.15 mm; gặp chân linh kiện nối tiếp thì nhảy sang chân kia; chân xuyên lỗ = via giả."""
    nets = set(nets)
    ps = [p for p in paths if p["net"] in nets]
    pn = [q for q in pins if q["net"] in nets]
    vr = [v for v in vrows if v["net"] in nets]
    start = next((q for q in pn if q.get("comp") == comp_a), None)
    if not start:
        return []
    steps = [{"kind": "pin", "comp": comp_a, "layer": start["range"][0]}]
    cur, layer, used, seen = (start["x"], start["y"]), start["range"][0], set(), {comp_a}
    grid = {}                                         # 037: ô lưới cạnh TOL_PIN -> (i, đầu, đầu kia)
    for i, p in enumerate(ps):
        for end, other in ((p["pts"][0], p["pts"][-1]), (p["pts"][-1], p["pts"][0])):
            grid.setdefault((math.floor(end[0] / TOL_PIN), math.floor(end[1] / TOL_PIN)), []).append((i, end, other))
    for _ in range(max(500, 2 * len(ps) + 10)):
        nxt, best = None, TOL_PIN                     # 037: đầu GẦN NHẤT trong mọi path chưa dùng (không lấy đầu tiên
        cx, cy = math.floor(cur[0] / TOL_PIN), math.floor(cur[1] / TOL_PIN)   # trong 0.3 mm: chuỗi đoạn thẳng + cung
        for gx in (cx - 1, cx, cx + 1):                                        # ngắn bị bỏ cung rồi đi ngược)
            for gy in (cy - 1, cy, cy + 1):
                for i, end, other in grid.get((gx, gy), ()):
                    if i in used:
                        continue
                    dd = _d(end, cur)
                    if dd < best or (dd == best and nxt is None):
                        nxt, best = (i, ps[i], other), dd
        if not nxt:
            break
        i, p, other = nxt
        used.add(i)
        if p["layer"] != layer:
            v = _via_at(vr, cur)
            if v:
                steps.append({"kind": "via", "from": layer, "to": p["layer"], "v": v})
            layer = p["layer"]
        if steps[-1]["kind"] == "seg" and steps[-1]["layer"] == layer:
            steps[-1]["len"] += p["len"]
        else:
            steps.append({"kind": "seg", "layer": layer, "len": p["len"]})
        cur = other
        near = [(_d((q["x"], q["y"]), cur), k) for k, q in enumerate(pn) if q.get("comp") not in seen]
        near = [t for t in near if t[0] <= TOL_PIN]
        pin = pn[min(near)[1]] if near else None                         # 037: chân gần nhất
        if pin and _goes_on(grid, used, cur, (pin["x"], pin["y"])):
            pin = None                                 # 037: trace còn đoạn nối tiếp tiến gần chân hơn -> đi tiếp
        if pin:
            pl = pin["range"][0]
            if pl != layer:
                v = _via_at(vr, cur) or _via_at(vr, (pin["x"], pin["y"]))   # 037: via trong pad ở tâm chân
                if v:
                    steps.append({"kind": "via", "from": layer, "to": pl, "v": v})
                elif len(pin["range"]) > 1 and layer in pin["range"]:      # chân xuyên lỗ: thân = via giả
                    r = pin["range"]
                    steps.append({"kind": "via", "from": layer, "to": pl,
                                  "v": {"kind": "through-hole pin", "range": f"{r[0]} → {r[-1]}", "has_bd": False,
                                        "stub_mm": 0.0, "pin": True}})
            comp = pin["comp"]
            seen.add(comp)
            if comp == comp_b:
                steps.append({"kind": "pin", "comp": comp, "layer": pl})
                break
            steps.append({"kind": "comp", "comp": comp, "layer": pl})
            o = next((q for q in pins if q.get("comp") == comp and q is not pin and q["net"] in nets), None)
            if not o:
                break
            cur, layer = (o["x"], o["y"]), o["range"][0]
    return steps


def signature(steps):
    """Topology = thứ tự lớp / via / linh kiện (không tính chiều dài) để so các thành viên."""
    out = []
    for s in steps:
        if s["kind"] == "seg":
            out.append(("seg", s["layer"]))
        elif s["kind"] == "via":
            out.append(("via", s["from"], s["to"], bool(s["v"].get("has_bd")), round(s["v"].get("stub_mm") or 0, 2)))
        else:
            out.append((s["kind"],))
    return tuple(out)


def _stub(s, metal):
    """Bước via có phần thừa: via thường = stub đo được (stub_mm); chân xuyên lỗ = thân dài hơn đoạn vào -> ra."""
    v = s["v"]
    if not v.get("pin"):
        return (v.get("stub_mm") or 0) > 1e-6
    idx = {L: i for i, L in enumerate(metal)}
    a, b = _rng(v)
    ends = [idx.get(x) for x in (a, b, s["from"], s["to"])]
    if None in ends:
        return False
    return min(ends[0], ends[1]) < min(ends[2], ends[3]) or max(ends[0], ends[1]) > max(ends[2], ends[3])


def via_counts(steps, metal=()):
    """-> (via, đã backdrill, có stub); chân xuyên lỗ không tính là via nhưng tính stub (thấy trong mặt cắt)."""
    vias = [s for s in steps if s["kind"] == "via"]
    nv = sum(1 for s in vias if not s["v"].get("pin"))
    bd = sum(1 for s in vias if s["v"].get("has_bd"))
    st = sum(1 for s in vias if _stub(s, metal))
    return nv, bd, st


def short_layer(n):
    """'Top Layer' -> 'Top', 'Bottom Layer' -> 'Bottom', 'Layer 3' / 'Layer 2 - GND' -> 'L3' / 'L2'."""
    n = str(n or "")
    lo = n.lower()
    if lo.startswith("top"):
        return "Top"
    if lo.startswith("bottom") or lo.startswith("bot"):
        return "Bottom"
    m = re.match(r"\s*layer\s*(\d+)", lo)
    return f"L{m.group(1)}" if m else n


def via_label(v, metal=()):
    """2.11.1 (R4 / R5): nhãn via trong mặt cắt -> [dòng]: loại (Through / Blind a–b / Buried a–b / Micro a–b /
    Stacked xN a–b), 'backdrilled' nếu khoan, kích thước '<pad>D<hole>' mil (từ via rows: padstack của board)."""
    if v.get("pin"):
        return ["TH pin"]
    a, b = _rng(v)
    span = f"{short_layer(a)}–{short_layer(b)}"
    kind = str(v.get("kind") or "")
    idx = {L: i for i, L in enumerate(metal)}
    adjacent = a in idx and b in idx and abs(idx[a] - idx[b]) == 1
    if kind.startswith("Stacked"):
        n = re.search(r"x(\d+)", kind)
        t = f"Stacked x{n.group(1)} {span}" if n else f"Stacked {span}"
    elif kind.startswith("Through"):
        t = "Through"
    elif adjacent:
        t = f"Micro {span}"
    elif kind.startswith("Blind"):
        t = f"Blind {span}"
    elif kind.startswith("Buried"):
        t = f"Buried {span}"
    else:
        t = kind or "Via"
    out = [t]
    if v.get("has_bd"):
        out.append("backdrilled")
    sizes = [x.split(" (")[0].strip() for x in str(v.get("size") or "").split(" + ")]
    sizes = list(dict.fromkeys(x for x in sizes if x and x != "size ?"))
    if sizes:
        out.append("/".join(sizes))
    return out


# ----------------------------------------------------------------------------- mặt cắt
def cross_svg(steps, metal, gnd_layers=(), names=None, info=None):
    """Mặt cắt: hàng = lớp (Top trên cùng), cột = các bước theo thứ tự (không theo tỉ lệ chiều dài).
    names: {refdes: nhãn hiện} (2.11.1: 'U14 (Top)'). info (045): {refdes: '220nF - 0402'} -> 2 dòng nhãn dưới hình
    (refdes đậm + giá trị - cỡ) ở cột của linh kiện, cùng hàng nhãn via (không đè lên hình)."""
    names, info = names or {}, info or {}
    rowh, left, colw = 20, 130, 100
    y = {L: 18 + i * rowh for i, L in enumerate(metal)}
    W = left + colw * max(1, len(steps)) + 30
    band = 44 if any(st["kind"] == "via" or (st["kind"] == "comp" and info.get(st["comp"])) for st in steps) else 0
    # 2.11.1: dải nhãn via (loại / backdrill / cỡ); 045: + nhãn giá trị linh kiện nối tiếp
    Hh = 18 + rowh * len(metal) + band
    gl = set(gnd_layers)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}" '
         f'font-family="Segoe UI,Arial" font-size="11" class="xs">']
    for L in metal:
        g = L in gl or "GND" in L.upper()
        o.append(f'<rect x="{left}" y="{y[L] - 3}" width="{W - left - 10}" height="6" '
                 f'fill="{"#cfdcf2" if g else "#efefef"}"/>'
                 f'<text x="{left - 6}" y="{y[L] + 4}" text-anchor="end" fill="#000">{H.escape(L)}</text>')
    cxs = [left + 40 + i * colw for i in range(len(steps))]
    for i, s in enumerate(steps):                            # 1) dây: đoạn trace nối phần tử trước -> sau
        if s["kind"] == "seg":
            yy = y.get(s["layer"], 18)
            xa, xb = cxs[max(i - 1, 0)], cxs[min(i + 1, len(steps) - 1)]
            o.append(f'<line x1="{xa}" y1="{yy}" x2="{xb}" y2="{yy}" stroke="#d62728" stroke-width="4"/>'
                     f'<rect x="{cxs[i] - 36}" y="{yy - 17}" width="72" height="12" fill="#fff" opacity="0.9"/>'
                     f'<text x="{cxs[i]}" y="{yy - 7}" text-anchor="middle" fill="#000"{U.attrs(s["len"])}>'
                     f'{U.fmt(s["len"])}</text>')
        elif i and steps[i - 1]["kind"] != "seg":            # via sát pad (không có đoạn trace): nối ở lớp của pad
            L = s["layer"] if s["kind"] in ("pin", "comp") else steps[i - 1].get("layer")
            if L:
                yy = y.get(L, 18)
                o.append(f'<line x1="{cxs[i - 1]}" y1="{yy}" x2="{cxs[i]}" y2="{yy}" stroke="#d62728" '
                         f'stroke-width="4"/>')
    for i, s in enumerate(steps):                            # 2) via, chân linh kiện vẽ đè lên dây
        cx = cxs[i]
        if s["kind"] in ("pin", "comp"):
            yy = y.get(s["layer"], 18)
            nm = names.get(s["comp"], s["comp"])
            bw = max(60, min(colw - 6, 7 * len(nm) + 10))
            o.append(f'<rect x="{cx - bw / 2:g}" y="{yy - 9}" width="{bw:g}" height="18" fill="#fff" stroke="#000"/>'
                     f'<text x="{cx}" y="{yy + 4}" text-anchor="middle" fill="#000" font-weight="bold">'
                     f'{H.escape(nm)}</text>')
            if s["kind"] == "comp" and info.get(s["comp"]):          # 045: '<refdes>' / '<value> - <package>'
                yb0 = 18 + rowh * len(metal) - 4
                o.append(f'<text x="{cx}" y="{yb0 + 12}" text-anchor="middle" font-size="10" fill="#000" '
                         f'font-weight="bold">{H.escape(s["comp"])}</text>'
                         f'<text x="{cx}" y="{yb0 + 24}" text-anchor="middle" font-size="10" fill="#000">'
                         f'{H.escape(info[s["comp"]])}</text>')
        elif s["kind"] == "via":
            v = s["v"]
            a, b = _rng(v)
            ya, yb = y.get(a, 18), y.get(b, 18)
            yf, yt = y.get(s["from"], ya), y.get(s["to"], yb)
            top, bot = min(ya, yb), max(ya, yb)
            u0, u1 = min(yf, yt), max(yf, yt)
            o.append(f'<rect x="{cx - 4}" y="{u0}" width="8" height="{max(u1 - u0, 2)}" fill="#000"/>')
            bd = bool(v.get("has_bd"))
            for t0, t1 in ((u1, bot), (top, u0)):
                if t1 > t0:                                  # phần via thừa: stub (hồng) / đã backdrill (nét đứt)
                    dash = ' stroke-dasharray="3 2"' if bd else ""
                    o.append(f'<rect x="{cx - 4}" y="{t0}" width="8" height="{t1 - t0}" '
                             f'fill="{"none" if bd else STUB}" stroke="{STUB}"{dash}/>')
            yb0 = 18 + rowh * len(metal) - 4                  # nhãn via dưới cùng, thẳng cột via
            for k, line in enumerate(via_label(v, metal)):
                o.append(f'<text x="{cx}" y="{yb0 + 12 * (k + 1)}" text-anchor="middle" font-size="10" fill="#000"'
                         f'{" font-weight=\"bold\"" if k == 0 else ""}>{H.escape(line)}</text>')
    o.append("</svg>")
    return "".join(o)


# ----------------------------------------------------------------------------- nhìn từ trên
def _tint(hexc, t):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(round(v + (255 - v) * t) for v in (r, g, b))


def _pad_svg(q):
    """Pad thật: khung pin (bounding box) -> chữ nhật; không có -> tròn theo cỡ pad của padstack."""
    bb = q.get("bbox")
    if bb:
        return (f'<rect x="{bb[0] / MM:.4f}" y="{-bb[3] / MM:.4f}" width="{(bb[2] - bb[0]) / MM:.4f}" '
                f'height="{(bb[3] - bb[1]) / MM:.4f}" fill="#9a9a9a" stroke="#555" stroke-width="0.5" '
                f'vector-effect="non-scaling-stroke"/>')
    r = (q.get("pad") or 0.4 * MM) / 2
    return (f'<circle cx="{q["x"] / MM:.4f}" cy="{-q["y"] / MM:.4f}" r="{r / MM:.4f}" fill="#9a9a9a" stroke="#555" '
            f'stroke-width="0.5" vector-effect="non-scaling-stroke"/>')


def _pad_half(q):
    bb = q.get("bbox")
    if bb:
        return max(bb[2] - bb[0], bb[3] - bb[1]) / 2 / MM
    return (q.get("pad") or 0.4 * MM) / 2 / MM


def _labels(labels, fs):
    """Refdes không chồng nhau: linh kiện sát nhau xét chung; đặt dọc -> chữ dọc hai bên; nằm ngang -> trên / dưới."""
    out, gs = [], []
    for l_ in labels:
        cx, cy = (l_[1] + l_[3]) / 2, (l_[2] + l_[4]) / 2
        gg = next((gg for gg in gs if gg[0][5] == l_[5] and
                   any(math.hypot(cx - (o[1] + o[3]) / 2, cy - (o[2] + o[4]) / 2) < fs * 4 for o in gg)), None)
        (gg.append(l_) if gg else gs.append([l_]))
    for gg in gs:
        if all(o[5] for o in gg):
            gg.sort(key=lambda o: o[1])
            for i, (comp, bx0, by0, bx1, by1, _) in enumerate(gg):
                cy_ = -(by0 + by1) / 2
                if i == 0 or len(gg) == 1:
                    pos = (f'x="{bx0:.4f}" y="{cy_:.4f}" dy="-0.35em" text-anchor="middle" '
                           f'transform="rotate(-90 {bx0:.4f} {cy_:.4f})"')
                elif i == len(gg) - 1:
                    pos = (f'x="{bx1:.4f}" y="{cy_:.4f}" dy="1.05em" text-anchor="middle" '
                           f'transform="rotate(-90 {bx1:.4f} {cy_:.4f})"')
                else:
                    xm = (bx0 + bx1) / 2
                    pos = (f'x="{xm:.4f}" y="{-by0:.4f}" dy="0.35em" dx="0.3em" text-anchor="start" '
                           f'transform="rotate(-90 {xm:.4f} {-by0:.4f})"')
                out.append(f'<text {pos} font-size="{fs:.4f}" data-fs="{fs:.4f}" fill="#000" font-weight="bold">'
                           f'{H.escape(comp)}</text>')
            continue
        gg.sort(key=lambda o: -o[4])
        for i, (comp, bx0, by0, bx1, by1, _) in enumerate(gg):
            if i == 0:
                pos = f'x="{(bx0 + bx1) / 2:.4f}" y="{-by1:.4f}" dy="-0.35em" text-anchor="middle"'
            elif i == len(gg) - 1:
                pos = f'x="{(bx0 + bx1) / 2:.4f}" y="{-by0:.4f}" dy="1.05em" text-anchor="middle"'
            else:
                pos = f'x="{bx1:.4f}" y="{-(by0 + by1) / 2:.4f}" dx="0.3em" dy="0.35em" text-anchor="start"'
            out.append(f'<text {pos} font-size="{fs:.4f}" data-fs="{fs:.4f}" fill="#000" font-weight="bold">'
                       f'{H.escape(comp)}</text>')
    return out


def top_svg(rt, g, chain_of, px=900):
    """Hình nhìn từ trên của nhóm g -> (svg, chú thích html)."""
    mem = {n: i for i, m in enumerate(g) for n in chain_of.get(m, [m])}
    nets = set(mem)
    ps = [p for p in rt["paths"] if p["net"] in nets]
    keep = set(rt.get("comps") or [])
    comps = {}
    for q in rt["pins"]:
        if q["net"] in nets and q.get("comp") and (not keep or q["comp"] in keep):
            comps.setdefault(q["comp"], []).append(q)
    xs = [q[0] for p in ps for q in p["pts"]] + [q["x"] for qs in comps.values() for q in qs]
    ys = [q[1] for p in ps for q in p["pts"]] + [q["y"] for qs in comps.values() for q in qs]
    if not xs:
        return "", ""
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = 0.07 * max(x1 - x0, y1 - y0, 1e-3)
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    w, h = (x1 - x0) / MM, (y1 - y0) / MM
    H_ = max(120, min(700, px * h / w)) if w else 300
    W_ = px if (w and px * h / w <= 700) else (700 * w / h if h else px)
    metal = rt["metal"]
    lays = [L for L in metal if any(p["layer"] == L for p in ps)]
    col = {L: LAYER_COLORS[i % len(LAYER_COLORS)] for i, L in enumerate(lays)}
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_:.0f}" height="{H_:.0f}" '
         f'viewBox="{x0 / MM:.4f} {-y1 / MM:.4f} {w:.4f} {h:.4f}" class="tv" '
         f'style="background:#fff;border:1px solid #ccc">']
    for p in ps:
        d = " ".join(f"{x / MM:.4f},{-y / MM:.4f}" for x, y in p["pts"])
        k = min(mem[p["net"]], 2)                              # P / A đậm, N / B nhạt hơn, C nhạt nhất (cùng màu lớp)
        s.append(f'<polyline points="{d}" fill="none" stroke="{_tint(col[p["layer"]], (0, 0.45, 0.65)[k])}" '
                 f'stroke-width="1.2" vector-effect="non-scaling-stroke" stroke-linecap="round" '
                 f'stroke-linejoin="round"/>')
    fs = max(w, h) / 75                                        # cỡ nhãn giữ trên màn hình khi zoom (JS)
    labels = []
    ends = (rt.get("comp_a"), rt.get("comp_b"))
    for comp in comps:                                         # 045: thân linh kiện nối tiếp của cặp (dưới trace)
        bb = (rt.get("comp_bb") or {}).get(comp)
        if comp not in ends and comp in (rt.get("series_info") or {}) and bb:
            s.insert(1, f'<rect x="{bb[0] / MM:.4f}" y="{-bb[3] / MM:.4f}" width="{(bb[2] - bb[0]) / MM:.4f}" '
                        f'height="{(bb[3] - bb[1]) / MM:.4f}" fill="#f5deb3" fill-opacity=".55" stroke="#000" '
                        f'stroke-width="1" vector-effect="non-scaling-stroke" class="sbody"/>')
    for comp, qs in comps.items():
        bb = (rt.get("comp_bb") or {}).get(comp)
        if comp in ends and bb and (bb[2] - bb[0]) < 0.06 and (bb[3] - bb[1]) < 0.06:   # khung thân thật
            s.append(f'<rect x="{bb[0] / MM:.4f}" y="{-bb[3] / MM:.4f}" width="{(bb[2] - bb[0]) / MM:.4f}" '
                     f'height="{(bb[3] - bb[1]) / MM:.4f}" fill="none" stroke="#000" stroke-width="0.8" '
                     f'vector-effect="non-scaling-stroke"/>')
        for q in qs:
            s.append(_pad_svg(q))
        xs_, ys_ = [q["x"] / MM for q in qs], [q["y"] / MM for q in qs]
        pr = max(_pad_half(q) for q in qs)
        vert = (comp not in ends and len(qs) > 1 and (max(ys_) - min(ys_)) > (max(xs_) - min(xs_)))
        labels.append([ref_label(rt, comp), min(xs_) - pr, min(ys_) - pr, max(xs_) + pr, max(ys_) + pr, vert])
    s += _labels(labels, fs)
    s.append("</svg>")
    leg = "".join(f"<span class='lg'><i style='background:{col[L]}'></i>{H.escape(L)}</span>" for L in lays)
    sty = ("dark", "light", "lightest")
    leg += "".join(f"<span class='lg'>{H.escape(_suffix(m))}: {sty[min(i, 2)]} shade</span>"
                   for i, m in enumerate(g) if len(g) > 1)
    leg += f"<span>Box: {U.span(w * MM)} × {U.span(h * MM)}</span>"
    return "".join(s), leg


def _suffix(m):
    for sfx in ("_DP", "_DN", "_P", "_N", "_A", "_B", "_C", "+", "-"):
        if m.upper().endswith(sfx):
            return sfx.lstrip("_")
    return m[-1:] if m[-1:] in "PN" else m


# ----------------------------------------------------------------------------- bảng chiều dài
def lengths(rt, g, chain_of):
    """-> [(thành viên, {lớp: m})] chiều dài trace theo lớp (mọi net của chuỗi)."""
    out = []
    for m in g:
        nets = set(chain_of.get(m, [m]))
        lay = {}
        for p in rt["paths"]:
            if p["net"] in nets:
                lay[p["layer"]] = lay.get(p["layer"], 0.0) + p["len"]
        out.append((m, lay))
    return out


def via_len(rt, m, chain_of):
    """037: chiều dài thân via (m) của chuỗi net (như review.lengths: barrel_mm của via rows)."""
    nets = set(chain_of.get(m, [m]))
    return sum(float(v.get("barrel_mm") or 0) for v in rt.get("vias") or [] if v.get("net") in nets) * MM


def len_table(rt, g, chain_of):
    """Bảng chiều dài P / N (037: = dữ liệu pair_skew, không trạng thái): Total = trace + thân via, từng lớp, Vias."""
    rows = lengths(rt, g, chain_of)
    metal = rt["metal"]
    lays = sorted({L for _, lay in rows for L in lay}, key=lambda L: metal.index(L) if L in metal else 99)
    un = U.unit_name()                                        # 2.11.2 (R10): đơn vị đổi được
    h = (f"<table class='topo'><tr><th>Net</th><th>Total, trace + via ({un})</th>"
         + "".join(f"<th>{H.escape(L)} ({un})</th>" for L in lays) + f"<th>Vias ({un})</th></tr>")
    for m, lay in rows:
        v = via_len(rt, m, chain_of)
        h += (f"<tr><td class='l'>{H.escape(m)}</td><td>{U.num(sum(lay.values()) + v)}</td>"
              + "".join(f"<td>{U.num(lay[L])}</td>" if L in lay else "<td>–</td>" for L in lays)
              + f"<td>{U.num(v)}</td></tr>")
    return h + "</table>"


def _cross(rt, g, chain_of):
    walks = [(n, walk(chain_of.get(n, [n]), rt["comp_a"], rt["comp_b"], rt["paths"], rt["vias"], rt["pins"]))
             for n in g]
    sig0 = signature(walks[0][1])
    names = {c: ref_label(rt, c) for c in rt.get("comps") or []}
    info = {rd: series_text(x) for rd, x in (rt.get("series_info") or {}).items()}
    o = []
    for i, (n, st) in enumerate(walks):
        if i and signature(st) == sig0:
            continue
        nv, bd, stub = via_counts(st, rt["metal"])
        same = ""
        if i == 0 and len(g) > 1:
            same_as = [m for (m, w) in walks[1:] if signature(w) == sig0]
            if same_as:
                same = " (same for " + ", ".join(same_as) + ")"
        elif i:
            same = f" (topology differs from {walks[0][0]})"
        note = "" if any(x["kind"] == "pin" and x["comp"] == rt["comp_b"] for x in st) else \
            " · <b>Note:</b> path not traced to the last pin"
        o.append(f"<div class='xsh'><b>Cross-section {H.escape(n)}</b>{H.escape(same)}: <b>Vias:</b> {nv} · "
                 f"<b>Backdrilled:</b> {bd} · <b>With stub:</b> {stub}{note}</div>"
                 f"<div class='ovx'>{cross_svg(st, rt['metal'], rt.get('gnd_layers') or (), names, info)}</div>")
    return "".join(o)


def pair_box(rt, g, chain_of):
    """Khung thu gọn của một cặp / bộ 3 (hoặc net lẻ)."""
    svg, leg = top_svg(rt, g, chain_of)
    return ("<details class='pbox'><summary><b>"
            f"{H.escape(rt['name'])}: {H.escape(' / '.join(g))}</b> ({H.escape(rt['comp_a'])} → "
            f"{H.escape(rt['comp_b'])})</summary>"
            f"<div class='leg2'>{leg}</div><div class='ovx'>{svg}</div>"
            + _cross(rt, g, chain_of) + len_table(rt, g, chain_of) + "</details>")


LEGEND = ("<div class='leg2'><span>Cross-section:</span><span class='lg'><i style='background:#d62728'></i>Trace</span>"
          "<span class='lg'><i class='v' style='background:#000'></i>Via</span>"
          f"<span class='lg'><i class='v' style='background:{STUB}'></i>Stub</span>"
          f"<span class='lg'><i class='v' style='background:none;border:1px dashed {STUB}'></i>Backdrilled</span></div>"
          "<div class='leg2'><span>Via labels: Through · Blind / Buried &lt;from&gt;–&lt;to&gt; · Micro (one "
          "dielectric) · Stacked xN · backdrilled · 18D8 = pad 18 mil, hole 8 mil · TH pin = through-hole connector "
          "pin (not counted as a via)</span></div>")


def section_html(rt):
    """HTML 'Signal routing per pair' của một channel (rt = ch['routing']); không có dữ liệu -> ''."""
    if not rt:
        return ""
    gs, chain_of = groups(rt["chains"])
    o = ["<h3>Signal routing per pair</h3><div>For information (no OK / NOT OK). Click a pair to expand it: top view "
         "(P / N, colour per layer), cross-section from the first pin to the last pin, vias and trace length. Zoom: "
         "click the button above a top view to unlock, then mouse wheel = zoom at the cursor, drag = move, "
         "double-click = reset.</div>", LEGEND]
    o += [pair_box(rt, g, chain_of) for g in gs]
    return "".join(o)


ZOOM_JS = """
document.querySelectorAll('svg.tv').forEach(sv=>{
 const v0=sv.getAttribute('viewBox').split(' ').map(Number);let v=v0.slice(),drag=null,lock=true;
 const bt=document.createElement('button');bt.type='button';bt.className='zb';
 const show=()=>{bt.textContent=lock?'Zoom locked (click to unlock)':'Zoom unlocked (click to lock)';
   bt.classList.toggle('on',!lock);sv.style.cursor=lock?'default':'crosshair';};
 bt.onclick=()=>{lock=!lock;show();};show();sv.parentElement.insertBefore(bt,sv);
 const set=()=>{sv.setAttribute('viewBox',v.join(' '));const k=v[2]/v0[2];
   sv.querySelectorAll('text[data-fs]').forEach(t=>t.setAttribute('font-size',t.dataset.fs*k));};
 const pt=e=>{const r=sv.getBoundingClientRect(),s=Math.max(v[2]/r.width,v[3]/r.height),
   ox=(r.width-v[2]/s)/2,oy=(r.height-v[3]/s)/2;return [v[0]+(e.clientX-r.left-ox)*s,v[1]+(e.clientY-r.top-oy)*s,s];};
 sv.addEventListener('wheel',e=>{if(lock)return;e.preventDefault();const [x,y]=pt(e),k=e.deltaY<0?0.8:1.25;
   v=[x-(x-v[0])*k,y-(y-v[1])*k,v[2]*k,v[3]*k];set();},{passive:false});
 sv.addEventListener('mousedown',e=>{if(lock)return;drag=[e.clientX,e.clientY,v.slice()];e.preventDefault();});
 window.addEventListener('mousemove',e=>{if(!drag)return;const s=pt(e)[2];
   v=[drag[2][0]-(e.clientX-drag[0])*s,drag[2][1]-(e.clientY-drag[1])*s,v[2],v[3]];set();});
 window.addEventListener('mouseup',()=>drag=null);
 sv.addEventListener('dblclick',()=>{if(lock)return;v=v0.slice();set();});});
"""
