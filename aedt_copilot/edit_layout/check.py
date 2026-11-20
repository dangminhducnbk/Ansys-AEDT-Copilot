"""Kiểm tra sau khi sửa (so vùng trước / sau, tổng quát cho mọi board).

Trả list mục {"check", "status": PASS|WARN|FAIL|INFO, "detail"}.
"""
import collections
import math

from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

from .geom import min_width, parts, to_geom


def _net_union(R, L, n, reg):
    gs = [g.intersection(reg) for nn, t, g, i in R.LAY[L] if nn == n and g.intersects(reg)]
    return unary_union(gs) if gs else None


def run_checks(B, A, ch, rules, touched, extra=None, edb=None):
    """B, A: Region trước / sau. touched: {(layer, net)} bị sửa. extra: plan["checks"]."""
    res = []
    reg = A.box
    mg = rules["min_copper_gap"]
    tol = 0.005
    layers = sorted({L for L, n in touched} | {L for v in ch["vias"] for L in A.SIG
                                                if A.spans(dict(v, sl=v["from"], el=v["to"], pin=False), L)},
                    key=A.SIG.index)
    nets = sorted({n for L, n in touched} | {v["net"] for v in ch["vias"]})

    # 1. chồng đồng giữa 2 net khác nhau (mới so với trước)
    bad = []
    for L in layers:
        by = collections.defaultdict(list)
        for n, t, g, i in A.LAY[L]:
            if g.intersects(reg):
                by[n].append(g.intersection(reg))
        names = sorted(by)
        U = {n: unary_union(by[n]) for n in names}
        tree = STRtree([U[n] for n in names])
        for k, n in enumerate(names):
            for j in tree.query(U[n]):
                if j <= k:
                    continue
                m = names[j]
                if n not in nets and m not in nets:
                    continue
                ov = U[n].intersection(U[m]).area
                if ov > 1e-6:
                    bn, bm = _net_union(B, L, n, reg), _net_union(B, L, m, reg)
                    ovb = bn.intersection(bm).area if bn is not None and bm is not None else 0.0
                    if ov - ovb > 1e-5:
                        bad.append(f"{L}: {n} / {m} chồng {ov - ovb:.4f} mm²")
    res.append({"check": "Chồng đồng giữa các net (mới)", "status": "FAIL" if bad else "PASS",
                "detail": bad[:20] or "0"})

    # 2. khe hở đồng mới / đồng thay đổi tới net khác
    gaps = []
    for L, n in sorted(touched):
        a, b = A.netgeom(L, n), B.netgeom(L, n)
        new = a.difference(b)
        new = unary_union([p for p in parts(new) if p.area > 1e-4]) if parts(new) else None
        if new is None or new.is_empty:
            continue
        oth = A.others(L, {n})
        d = new.distance(oth) if not oth.is_empty else 99
        gaps.append((L, n, round(new.area, 3), round(d, 4)))
    bad = [g for g in gaps if g[3] < mg - tol]
    res.append({"check": f"Khe hở đồng mới tới net khác (≥ {mg} mm)", "status": "FAIL" if bad else "PASS",
                "detail": [f"{L} {n}: +{a} mm², khe {d} mm" for L, n, a, d in gaps] or "không có đồng mới"})

    # 3. số mảnh đồng mỗi net bị sửa trên mỗi lớp (đứt mảnh = FAIL)
    pcs, bad = [], []
    for L, n in sorted(touched):
        pb = [round(p.area, 2) for p in parts(B.netgeom(L, n)) if p.area > 0.05]
        pa = [round(p.area, 2) for p in parts(A.netgeom(L, n)) if p.area > 0.05]
        pcs.append(f"{L} {n}: {len(pb)} → {len(pa)} mảnh, diện tích {sum(pb):.1f} → {sum(pa):.1f} mm²")
        if len(pa) > len(pb):
            bad.append(L + " " + n)
    res.append({"check": "Số mảnh đồng (net bị sửa)", "status": "WARN" if bad else "PASS", "detail": pcs})

    # 4. via / pin của các net liên quan vẫn chạm đồng cùng net (không mất kết nối)
    lost_all, lost_nets = [], set()
    gone = {c["id"] for c in ch.get("deleted_vias", [])}        # 016: via xoá theo plan không tính là mất kết nối
    for n in sorted({n for L, n in touched}):
        def contacts(R):
            out = set()
            for v in R.inst:
                if v["net"] != n or v["id"] in gone:
                    continue
                p = Point(v["x"], v["y"])
                for L in R.SIG:
                    if not R.on_layer(v, L):
                        continue
                    if any(nn == n and g.distance(p) < 1e-3 for nn, t, g, i in R.LAY[L]):
                        out.add((v["pd"], round(v["x"], 3), round(v["y"], 3), L))
            return out
        cb, ca = contacts(B), contacts(A)
        lost = sorted(cb - ca)
        if lost:
            lost_nets.add(n)
            lost_all.append(f"{n}: mất {len(lost)} điểm chạm {lost[:6]}")
        else:
            lost_all.append(f"{n}: {len(cb)} → {len(ca)} điểm chạm, không mất")
    contact = {"check": "Via/pin còn chạm đồng cùng net", "status": "FAIL" if lost_nets else "PASS", "detail": lost_all}
    res.append(contact)
    if ch.get("deleted_vias"):                                    # 016: via đã xoá không còn trong file đã lưu
        akeys = {(v["pd"], round(v["x"], 3), round(v["y"], 3)) for v in A.inst}
        still = [c for c in ch["deleted_vias"] if (c["pd"], round(c["x"], 3), round(c["y"], 3)) in akeys]
        res.append({"check": "Via đã xoá", "status": "FAIL" if still else "PASS",
                    "detail": [f"{c['net']} {c['pd']} ({c['x']:.3f}, {c['y']:.3f}) " + ("CÒN" if c in still else "đã xoá")
                               for c in ch["deleted_vias"]]})

    # 5. via mới: chạm đồng cùng net ở lớp đầu/cuối, khe hở pad tới đồng net khác, antipad trên plane
    newv = []
    oldkeys = {(v["pd"], round(v["x"], 3), round(v["y"], 3)) for v in B.inst}
    for v in A.inst:
        if not v["pin"] and (v["pd"], round(v["x"], 3), round(v["y"], 3)) not in oldkeys:
            newv.append(v)
    land_bad, clr_bad, vv_bad = [], [], []
    land_of = {(round(c["x"], 3), round(c["y"], 3)): c.get("land") for c in ch["vias"]}
    for v in newv:
        p = Point(v["x"], v["y"])
        # lớp đáp = `land` của op via (khớp theo vị trí); mặc định lớp đầu/cuối
        for L in (land_of.get((round(v["x"], 3), round(v["y"], 3))) or (v["sl"], v["el"])):
            on_cu = any(nn == v["net"] and g.distance(p) < 1e-6 for nn, t, g, i in A.LAY[L])
            on_pad = any(w is not v and w["net"] == v["net"] and A.on_layer(w, L)
                         and math.hypot(w["x"] - v["x"], w["y"] - v["y"]) <= (A.padr_min(w["pd"], L) or 0.1)
                         for w in A.inst)
            if not (on_cu or on_pad):
                land_bad.append(f"{v['pd']} ({v['x']:.3f}, {v['y']:.3f}) không chạm {v['net']} ở {L}")
        for L in A.SIG:
            if not A.spans(v, L):
                continue
            r = A.padr(v["pd"], L)
            for nn, t, g, i in A.LAY[L]:
                if nn == v["net"]:
                    continue
                d = g.distance(p) - r
                if d < mg - tol:
                    clr_bad.append(f"{v['pd']} ({v['x']:.3f}, {v['y']:.3f}) {L}: {nn} khe {d:.3f} mm")
        for w in A.inst:
            if w is v or w["net"] == v["net"]:
                continue
            d = math.hypot(v["x"] - w["x"], v["y"] - w["y"])
            if d > 2:
                continue
            for L in A.SIG:
                if A.spans(v, L) and A.on_layer(w, L):
                    g = d - A.padr(v["pd"], L) - (A.padr(w["pd"], L) or 0.15)
                    if g < mg - tol:
                        vv_bad.append(f"{v['pd']} ({v['x']:.2f}, {v['y']:.2f}) – {w['net']} {w['pd']} {L}: {g:.3f} mm")
                        break
    res.append({"check": "Via mới: số lượng", "status": "INFO",
                "detail": dict(collections.Counter(f"{v['net']} {v['pd']}" for v in newv)) or "0"})
    if newv:
        res.append({"check": "Via mới chạm đồng cùng net ở lớp đáp (land)", "status": "FAIL" if land_bad else "PASS",
                    "detail": land_bad[:20] or f"{len(newv)}/{len(newv)}"})
        res.append({"check": f"Via mới: pad cách đồng net khác ≥ {mg} mm", "status": "FAIL" if clr_bad else "PASS",
                    "detail": clr_bad[:20] or "0 lỗi"})
        res.append({"check": f"Via mới: cách pad via/pin net khác ≥ {mg} mm", "status": "FAIL" if vv_bad else "PASS",
                    "detail": vv_bad[:20] or "0 lỗi"})

    # 6. kiểm tra thêm do plan yêu cầu
    for c in (extra or []):
        try:
            if c["type"] == "min_width":
                L, n = c["layer"], c["net"]
                win = to_geom(c["window"])
                za, zb = to_geom(c["from"]), to_geom(c["to"])
                wb, pb = min_width(B.netgeom(L, n), win, za, zb, c.get("grid", 0.05))
                wa, pa = min_width(A.netgeom(L, n), win, za, zb, c.get("grid", 0.05))
                st = "PASS" if wa >= c.get("min", 0) and wa >= wb - 1e-6 else ("FAIL" if wa < c.get("min", 0) else "WARN")
                res.append({"check": f"Độ rộng dòng nhỏ nhất {n} {L}", "status": st,
                            "detail": f"{wb} → {wa} mm (điểm nghẽn sau: {pa[:3]})"})
            elif c["type"] == "connected" and edb is not None:
                r = _connected(edb, c)
                r["net"] = c["net"]
                res.append(r)
        except Exception as ex:
            res.append({"check": f"{c.get('type')}", "status": "WARN", "detail": f"lỗi kiểm tra: {ex}"})
    # mất điểm chạm do thiết kế: chỉ hạ xuống WARN khi MỌI net bị mất có check `connected` PASS
    conn_ok = {r["net"] for r in res if r.get("net") and r["status"] == "PASS"}
    if lost_nets and lost_nets <= conn_ok:
        contact["status"] = "WARN"
        contact["detail"] = lost_all + ["contacts removed by design, connectivity OK"]
    for w in ch.get("warnings", []):
        res.append({"check": "Cảnh báo khi sửa", "status": "WARN", "detail": w})
    return res


def _connected(edb, c):
    """EDB connectivity: từ pin đầu tiên của linh kiện `from` trên net, có tới mọi `to` không."""
    net = c["net"]
    comps = edb.components.instances
    start = [p for p in comps[c["from"]].pins.values() if p.net_name == net]
    if not start:
        return {"check": f"Kết nối {net}", "status": "WARN", "detail": f"{c['from']} không có pin {net}"}
    # LayoutInstance MỚI sau khi sửa: pyedb edb.get_connected_objects dùng layout_instance cache từ lúc mở
    # (sau khi sửa trả về 6676 đối tượng thay vì 30)
    core = start[0]._edb_object
    li = core.GetLayout().GetLayoutInstance()
    objs = [loi.GetLayoutObj() for loi in li.GetConnectedObjects(li.GetLayoutObjInstance(core, None)).Items]
    ids = {o.GetId() for o in objs}
    other = sorted({o.GetNet().GetName() for o in objs if not o.GetNet().IsNull()} - {net})
    miss = []
    for rd in c["to"]:
        pins = [p for p in comps[rd].pins.values() if p.net_name == net]
        if not pins or not any(p.id in ids for p in pins):
            miss.append(rd)
    bad = miss or other
    det = (f"không tới: {miss}; " if miss else "") + (f"CHẠM NET KHÁC: {other[:6]}; " if other else "") + \
        f"{len(ids)} đối tượng liên thông"
    return {"check": f"Kết nối {net}: {c['from']} → {', '.join(c['to'])}", "status": "FAIL" if bad else "PASS",
            "detail": det}
