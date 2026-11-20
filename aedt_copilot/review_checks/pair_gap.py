"""Check 'pair_gap' (feature 030, luật 2): thành viên cặp / bộ 3 tách xa nhau. Khe mép-mép tới thành viên gần nhất
> khe danh định x review.pair_gap_ratio trên đoạn >= review.pair_gap_min_len_mm -> NOT OK. Khe danh định = bảng
stackup của lớp (nếu có) hoặc trung vị đo được; bỏ qua vùng neck-down quanh pad / via.
033: chỗ tách nằm trong một serpentine (bù chiều dài) của cùng cặp không phải lỗi -> bỏ (trước khi gộp đoạn).
037: chỗ tách có điểm giữa trong thân đầu BGA (+ review.bga_breakout_margin_mm) = breakout cố ý -> bỏ, đếm skipped_in_bga."""
from . import _si as S
from . import _stackup
from . import _rules as X
from . import _serp as SP
from . import _text as T

NAME = "pair_gap"
ORDER = 60
TITLE, RULE = X.meta(NAME)
MM = S.MM


def nominal(table, layer, width_m, median_m):
    """Khe danh định (m): cặp trong bảng stackup có độ rộng gần nhất, không có -> trung vị đo được."""
    e = _stackup.expected(table, layer, True)
    if e and e[1]:
        best = min(e[1], key=lambda p: abs(p["width_mm"] * MM - width_m))
        return best["gap_mm"] * MM, "stackup"
    return median_m, "median"


def bga_boxes(cc, margin_m):
    """037: khung thân (m, + lề) của các đầu kênh loại BGA (end_types của trace, như isim_trace); khung không đọc
    được -> bỏ qua linh kiện đó (đoạn tách vẫn được xét)."""
    t = cc.trace
    out = {}
    for rd, typ in (t.get("end_types") or {}).items():
        if typ != "bga":
            continue
        try:
            x0, y0, x1, y1 = [float(v) for v in cc.ctx.edb.components.instances[rd].bounding_box]
        except Exception:                                    # SnapshotMissing không xảy ra: bbox thân có trong index
            continue
        out[rd] = (min(x0, x1) - margin_m, min(y0, y1) - margin_m, max(x0, x1) + margin_m, max(y0, y1) + margin_m)
    return out


def in_box(boxes, x, y):
    return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for b in boxes.values())


def run(cc):
    R, step = cc.ctx.R, cc.ctx.step
    ratio, minlen = float(R["pair_gap_ratio"]), float(R["pair_gap_min_len_mm"]) * MM
    table = _stackup.load(cc.ctx.board)
    items, data = [], []
    serps = SP.found(cc)
    bgas = bga_boxes(cc, float(R.get("bga_breakout_margin_mm") or 0) * MM)
    skipped, in_bga = 0, 0
    for e in S.pair_gaps(cc):
        some = next(iter(e["res"].values()))[0][0]
        nom, src = nominal(table, e["layer"], some["w"], e["nominal_median_m"])
        lim = nom * ratio
        data.append({"group": e["group"], "layer": e["layer"], "nominal_gap_mm": round(nom / MM, 4), "source": src})
        found = []
        for m in e["members"][:1]:                                       # cặp: một phía là đủ
            for p, smp, gap, skip in e["res"].get(m, []):
                flags = [(not s) and g > lim for g, s in zip(gap, skip)]
                for i0, i1 in S.runs(flags):
                    if (i1 - i0 + 1) * step < minlen - 1e-12:
                        continue
                    a, b = smp[i0], smp[i1]
                    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
                    if any(p["net"] in sp["nets"] and SP.inside(sp, mx, my) for sp in serps):
                        skipped += 1                                         # 033: serpentine của cùng cặp
                        continue
                    if in_box(bgas, mx, my):
                        in_bga += 1                                          # 037: breakout cố ý trong thân BGA
                        continue
                    gmax = float(max(gap[i0:i1 + 1]))
                    gtxt = f"{gmax / MM:.3f} mm" if gmax < 1 else "no partner trace nearby"
                    found.append(S.finding("Pair gap", "NOT OK", p["net"], e["layer"], smp, i0, i1, step,
                                           f"gap up to {gtxt} vs nominal {nom / MM:.3f} mm ({src}) over "
                                           f"{(i1 - i0 + 1) * step / MM:.3f} mm",
                                           gap_max_mm=gmax / MM, nominal_mm=nom / MM, nominal_src=src,
                                           group=e["group"]))
        for f in S.merge(found, lambda f: (f["net"], f["layer"])):
            f["gap_max_mm"] = max(x["gap_max_mm"] for x in found if x["net"] == f["net"])
            gm = f["gap_max_mm"]
            f["value"] = (f"gap up to {f'{gm:.3f} mm' if gm < 1000 else 'no partner trace nearby'} vs nominal {nom / MM:.3f} mm ({src}) on "
                          f"{f['runs']} stretch(es), {f['total_mm']:.3f} mm in total (longest {f['len_mm']:.3f} mm)")
            items.append(f)
    return {"items": items, "data": {"layers": data, "skipped_in_serpentine": skipped, "skipped_in_bga": in_bga,
                                     "bga_bodies": sorted(bgas)}}


def _describe(f, P, c=None):
    ratio = float(P["pair_gap_ratio"])
    nom, g = f.get("nominal_mm"), f.get("gap_max_mm")
    rows = [("Trace", f"{f.get('layer')}{T.trace_seg(f)}"), ("Pair / trio", " / ".join(f.get("group") or [])),
            ("Gap", (f"up to {g:.3f} mm — limit ≤ {nom * ratio:.3f} mm ({ratio:g} × nominal {nom:.3f} mm, "
                     f"{f.get('nominal_src')}) ✗") if g is not None and g < 1000 and nom else str(f.get("value"))),
            T.length_row(f), ("Stretches", f"{f.get('runs', 1)}, {f.get('total_mm', 0):.3f} mm in total")]
    return rows, X.text(NAME, "why"), X.text(NAME, "fix")


def _layers(f, ref_layers, metal):
    return {f.get("layer")}, set(ref_layers(f.get("layer")))


REPORT = X.report(NAME, _describe, _layers)
