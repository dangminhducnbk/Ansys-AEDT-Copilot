"""Các thao tác sửa layout trên EDB đang mở (đơn vị mm trong plan).

Viết lại tổng quát từ các script tối ưu B04 (ASM_1P1V stitch / U200 neck, 2026-10-31..11-01). Mọi lệnh tạo/xoá
gọi thẳng API .NET của EDB với cache (net, lớp, padstack): pyedb `padstacks.place` và `modeler.create_circle`
dựng lại danh sách padstack / tìm lại cả layout ở mỗi lần gọi (~6 s / via trên B04).

Mỗi op là dict {"op": ..., ...}; xem guides/layout_edit.md.
"""
import math

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from shapely.prepared import prep

from ..core.units import MM
from .geom import parts, polys_only, ring_list, to_geom


class Editor:
    def __init__(self, edb, R, rules, log=print):
        from pyedb.dotnet.database.general import convert_py_list_to_net_list
        self.NL = convert_py_list_to_net_list
        self.edb, self.R, self.rules, self.log = edb, R, rules, log
        self.api = edb._edb
        self.layout = edb.active_layout
        self._nets, self._layers, self._pdefs = {}, {}, None
        self._prims = None
        self._made = {}                     # id -> primitive .NET tạo bởi new_polygon
        self.ch ={"ops": [], "deleted": [], "created": [], "voids": [], "vias": [], "traces": [], "warnings": []}
        self.merged = []                    # id polygon đã gộp -> dọn void vụn cuối cùng
        self.new_vias = []                  # (x, y, pd, net, sl, el)
        self.live = {}                      # id -> (layer, net, geom) cho polygon mới tạo
        self.gone = set()                   # id đã xoá
        self.gone_vias = set()              # 016: id via (padstack instance) đã xoá
        self.over = {}                      # id (polygon cũ) -> hình mới sau khi khoét void (không sửa Region trước)

    # ------------------------------------------------------------------ cache / tiện ích .NET
    def v(self, x):
        return self.edb.edb_value(x)

    def net(self, name):
        if name not in self._nets:
            self._nets[name] = self.edb.nets.find_or_create_net(name)._edb_object
        return self._nets[name]

    def layer(self, name):
        if name not in self._layers:
            self._layers[name] = self.edb.stackup.signal_layers[name]._edb_layer
        return self._layers[name]

    def pdef(self, name):
        if self._pdefs is None:
            self._pdefs = dict(self.edb.padstacks.definitions)
        if name not in self._pdefs:
            raise RuntimeError(f"Không có padstack '{name}'")
        return self._pdefs[name].edb_padstack

    def prims(self, refresh=False):
        if self._prims is None or refresh:
            if refresh:
                self.edb.layout.clear_cache()      # cache pyedb chỉ làm mới khi số lượng đổi
            self._prims = {p.id: p for p in self.edb.layout.primitives}
        return self._prims

    def core(self, pid):
        if pid in self._made:               # polygon tạo trong phiên này (pyedb không liệt kê lại)
            return self._made[pid]
        p = self.prims().get(pid)
        if p is None:
            self.prims(refresh=True)
            p = self._prims.get(pid)
        if p is None:
            raise RuntimeError(f"Không tìm thấy primitive id {pid}")
        return getattr(p, "core", None) or p._edb_object

    def pdata(self, ring):
        """Vòng [[x, y]...] mm (có thể khép kín) -> PolygonData."""
        pts = [list(c) for c in ring]
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts = pts[:-1]
        shape = self.edb.modeler.Shape("polygon", points=[[x * MM, y * MM] for x, y in pts])
        pd = self.edb.modeler.shape_to_polygon_data(shape)
        return getattr(pd, "core", pd)

    def pdata_poly(self, poly):
        pd = self.pdata(list(poly.exterior.coords))
        for r in poly.interiors:
            pd.AddHole(self.pdata(list(r.coords)))
        return pd

    def new_polygon(self, layer, net, pdata):
        prim = self.api.Cell.Primitive.Polygon.Create(self.layout, layer, self.net(net), pdata)
        if prim.IsNull():
            raise RuntimeError(f"Tạo polygon lỗi ({layer}, {net})")
        self._made[prim.GetId()] = prim
        return prim

    def add_void(self, host_core, layer, net, geom=None, circle=None, why=""):
        if circle is not None:
            x, y, r = circle
            vp = self.api.Cell.Primitive.Circle.Create(self.layout, layer, self.net(net), self.v(x * MM), self.v(y * MM),
                                                       self.v(r * MM))
        else:
            vp = self.api.Cell.Primitive.Polygon.Create(self.layout, layer, self.net(net), self.pdata_poly(geom))
        if vp.IsNull() or not host_core.AddVoid(vp):
            raise RuntimeError(f"AddVoid lỗi ({layer}, {net}) {why}")
        self.ch["voids"].append({"host": host_core.GetId(), "layer": layer, "net": net, "why": why})

    # ------------------------------------------------------------------ hình học hiện tại (trước + đã sửa)
    def geom_of(self, pid):
        if pid in self.live:
            return self.live[pid][2]
        return self.over.get(pid, self.R.BYID[pid][3])

    def _items(self, L):
        """(net, type, geom, id) hiện tại trên lớp L: vùng đọc ban đầu (trừ id đã xoá, thay hình đã khoét)."""
        return [(n, t, self.over.get(i, g), i) for n, t, g, i in self.R.LAY[L] if i not in self.gone]

    def polygons(self, L, net, near=None):
        out = [(i, g) for n, t, g, i in self._items(L)
               if n == net and t != "path" and (near is None or g.intersects(near))]
        out += [(i, g) for i, (l, n, g) in self.live.items() if l == L and n == net and (near is None or g.intersects(near))]
        return out

    def copper(self, L, net):
        gs = [g for i, g in self.polygons(L, net)] + [g for nn, t, g, i in self._items(L) if nn == net and t == "path"]
        gs += [g for (l, n, g) in self.ch.get("_trace_geoms", []) if l == L and n == net]
        return unary_union(gs) if gs else Polygon()

    def others(self, L, excl):
        gs = [g for nn, t, g, i in self._items(L) if nn not in excl]
        gs += [g for i, (l, n, g) in self.live.items() if l == L and n not in excl]
        gs += [g for (l, n, g) in self.ch.get("_trace_geoms", []) if l == L and n not in excl]
        return unary_union(gs) if gs else Polygon()

    def via_r(self, v, L):
        """Bán kính clearance trên plane cho via/pin net khác (giống quy ước board B04)."""
        pr = self.R.padr(v["pd"], L) or (0.15 if v["pin"] else 0.0)
        return max(pr + self.rules["via_plane_clearance"], self.rules["antipad_min_r"]) if pr else 0.0

    def all_vias(self):
        out = [v for v in self.R.inst if v["id"] not in self.gone_vias]
        for x, y, pd, net, sl, el in self.new_vias:
            out.append(dict(id=None, pd=pd, net=net, x=x, y=y, sl=sl, el=el, comp="", pin=False))
        return out

    # ------------------------------------------------------------------ gộp polygon cùng net
    def merge_into(self, L, net, new_cores, why):
        """Gộp polygon mới với polygon cùng net chạm vào nó (Unite outline, gắn lại void, xoá cũ)."""
        new_geoms = [g for c, g in new_cores]
        touch = [(i, g) for i, g in self.polygons(L, net) if any(g.distance(n) < 1e-6 for n in new_geoms)]
        if not touch:
            for c, g in new_cores:
                self.live[c.GetId()] = (L, net, g)
                self.ch["created"].append({"id": c.GetId(), "layer": L, "net": net, "why": why, "merged": False})
            return [c.GetId() for c, g in new_cores]
        old_cores = [self.core(i) for i, g in touch]
        cores = old_cores + [c for c, g in new_cores]
        pd0 = old_cores[0].GetPolygonData()
        united = [u for u in pd0.Unite(self.NL([c.GetPolygonData() for c in cores])) if not u.IsNull()]
        united = [u for u in united if u.Area() / MM / MM > self.rules["min_piece_mm2"]]
        ids = []
        geom_all = unary_union([g for i, g in touch] + new_geoms)
        for u in united:
            m = self.new_polygon(L, net, u)
            nv = 0
            for c in cores:
                for vd in _voids(c):
                    vp = self.api.Cell.Primitive.Polygon.Create(self.layout, L, self.net(net), vd.GetPolygonData())
                    if m.AddVoid(vp):
                        nv += 1
            mid = m.GetId()
            g = geom_all if len(united) == 1 else polys_only(geom_all.intersection(_bbox_poly(u)))
            self.live[mid] = (L, net, g)
            self.merged.append(mid)
            ids.append(mid)
            self.ch["created"].append({"id": mid, "layer": L, "net": net, "why": why, "merged_from": [i for i, _ in touch],
                                       "voids_reattached": nv})
        for i, g in touch:
            self._delete(i, L, net, "gộp vào polygon mới")
        for c, g in new_cores:
            c.Delete()
        return ids

    def _delete(self, pid, L, net, why):
        self.core(pid).Delete()
        self.gone.add(pid)
        self.live.pop(pid, None)
        self.ch["deleted"].append({"id": pid, "layer": L, "net": net, "why": why})

    # ------------------------------------------------------------------ OPS
    def op_add_copper(self, o):
        """Thêm đồng cho net trên lớp: vùng `shape`, tự trừ đồng net khác + khe hở, trừ clearance via net khác,
        gộp vào polygon cùng net chạm vào. clip=false: dùng nguyên shape (đã tính sẵn khe hở)."""
        L, net = o["layer"], o["net"]
        gap = o.get("gap", self.rules["plane_gap"])
        g = to_geom(o["shape"])
        if o.get("keep_out"):
            g = g.difference(unary_union([to_geom(k) for k in o["keep_out"]]))
        if o.get("clip", True):
            g = g.difference(self.others(L, {net}).buffer(gap))
            g = g.difference(self.R_via_voids(L, net, g))
        g = unary_union([p for p in parts(g) if p.area > o.get("min_piece", self.rules["min_piece_mm2"])])
        if g.is_empty:
            raise RuntimeError(f"add_copper {L} {net}: vùng còn lại rỗng sau khi trừ khe hở")
        new = [(self.new_polygon(L, net, self.pdata_poly(p)), p) for p in parts(g)]
        ids = self.merge_into(L, net, new, o.get("why", "add_copper")) if o.get("merge", True) else \
            [self._register(c, L, net, p, o) for c, p in new]
        return {"layer": L, "net": net, "added_mm2": round(g.area, 3), "pieces": len(parts(g)), "ids": ids}

    def _shrink(self, i, L, net, cut):
        """Cập nhật hình polygon i sau khi khoét void `cut`."""
        if i in self.live:
            self.live[i] = (L, net, polys_only(self.live[i][2].difference(cut)))
        else:
            self.over[i] = polys_only(self.geom_of(i).difference(cut))

    def _register(self, c, L, net, g, o):
        self.live[c.GetId()] = (L, net, g)
        self.ch["created"].append({"id": c.GetId(), "layer": L, "net": net, "why": o.get("why", o["op"])})
        return c.GetId()

    def R_via_voids(self, L, net, region):
        vs = []
        for v in self.all_vias():
            if v["net"] == net or not self.R.on_layer(v, L):
                continue
            r = self.via_r(v, L)
            p = Point(v["x"], v["y"])
            if r and region.distance(p) < r:
                vs.append(p.buffer(r, 32))
        return unary_union(vs) if vs else Polygon()

    def op_carve(self, o):
        """Lấy đồng từ net `from_net` cho net `net` trong vùng `shape` (cùng lớp): khoét void ở from_net
        (vùng + gap), thêm đồng cho net (vùng - đồng net khác - via net khác), gộp vào polygon net."""
        L, net, src = o["layer"], o["net"], o["from_net"]
        gap = o.get("gap", self.rules["plane_gap"])
        C = to_geom(o["shape"])
        if o.get("keep_out"):
            C = C.difference(unary_union([to_geom(k) for k in o["keep_out"]]))
        src_polys = self.polygons(L, src, near=C)
        if not src_polys:
            raise RuntimeError(f"carve: không có polygon {src} trên {L} trong vùng")
        holes = [Polygon(r) for i, g in src_polys for pg in parts(g) for r in pg.interiors if Polygon(r).intersects(C)]
        carve = C.difference(unary_union(holes)) if holes else C
        carve = carve.difference(self.others(L, {net, src}).buffer(gap))
        carve = unary_union([p for p in parts(carve) if p.area > o.get("min_piece", 0.5)])
        if carve.is_empty:
            raise RuntimeError("carve: vùng khoét rỗng")
        lost = [v for v in self.all_vias() if v["net"] == src and self.R.on_layer(v, L)
                and carve.buffer(gap).distance(Point(v["x"], v["y"])) < self.R.padr(v["pd"], L)]
        if lost and not o.get("allow_cut_vias"):
            raise RuntimeError(f"carve: vùng khoét chạm {len(lost)} via/pin của {src}: "
                               f"{[(v['pd'], round(v['x'], 2), round(v['y'], 2)) for v in lost[:8]]}")
        cut = Polygon(carve.buffer(gap, join_style=2, mitre_limit=3).exterior) if carve.geom_type == "Polygon" else \
            unary_union([Polygon(p.exterior) for p in parts(carve.buffer(gap, join_style=2, mitre_limit=3))])
        for i, g in src_polys:
            if g.intersects(cut):
                for pc in parts(cut.intersection(Polygon(_outer(g)).buffer(0.05, join_style=2))):
                    self.add_void(self.core(i), L, src, geom=Polygon(pc.exterior), why=f"carve cho {net}")
                self._shrink(i, L, src, cut)
        gain = carve.difference(self.R_via_voids(L, net, carve))
        gain = unary_union([p for p in parts(gain) if p.area > self.rules["min_piece_mm2"]])
        new = [(self.new_polygon(L, net, self.pdata_poly(p)), p) for p in parts(gain)]
        ids = self.merge_into(L, net, new, o.get("why", f"carve từ {src}"))
        return {"layer": L, "net": net, "from_net": src, "carve_mm2": round(carve.area, 3),
                "gain_mm2": round(gain.area, 3), "ids": ids}

    def op_remove_copper(self, o):
        """Bỏ đồng của `net` trên `layer` trong vùng `shape` (cắt outline, không chỉ thêm void)."""
        L, net = o["layer"], o["net"]
        rect = to_geom(o["shape"])
        res = []
        for i, g in self.polygons(L, net, near=rect):
            c = self.core(i)
            sub = [self.pdata_poly(rect)]
            keep = []
            for vd in _voids(c):
                vg = _pd_bbox_poly(vd.GetPolygonData())
                if vg.intersects(rect):
                    if not vg.within(rect):
                        sub.append(vd.GetPolygonData())
                else:
                    keep.append(vd)
            pd0 = c.GetPolygonData()
            outs = [u for u in pd0.Subtract(self.NL([pd0]), self.NL(sub)) if not u.IsNull()]
            outs = [u for u in outs if u.Area() / MM / MM > self.rules["min_piece_mm2"]]
            newg = polys_only(g.difference(rect))
            ids = []
            for u in outs:
                m = self.new_polygon(L, net, u)
                ub = _bbox_poly(u)
                for vd in keep:
                    if _pd_bbox_poly(vd.GetPolygonData()).intersects(ub):
                        vp = self.api.Cell.Primitive.Polygon.Create(self.layout, L, self.net(net), vd.GetPolygonData())
                        m.AddVoid(vp)
                self.live[m.GetId()] = (L, net, polys_only(newg.intersection(ub)) if len(outs) > 1 else newg)
                self.ch["created"].append({"id": m.GetId(), "layer": L, "net": net, "why": o.get("why", "remove_copper")})
                ids.append(m.GetId())
            self._delete(i, L, net, "remove_copper (thay bằng polygon đã cắt)")
            res.append({"old": i, "new": ids, "removed_mm2": round(g.area - newg.area, 3)})
        if not res:
            raise RuntimeError(f"remove_copper: không có polygon {net} trên {L} trong vùng")
        return {"layer": L, "net": net, "polygons": res}

    def op_void(self, o):
        """Khoét void (shape) vào polygon của net trên lớp (vd antipad, sửa SOV ngược, kênh đi dây)."""
        L, net = o["layer"], o["net"]
        g = to_geom(o["shape"])
        n = 0
        for i, pg in self.polygons(L, net, near=g):
            self.add_void(self.core(i), L, net, geom=g, why=o.get("why", "void"))
            self._shrink(i, L, net, g)
            n += 1
        if not n:
            raise RuntimeError(f"void: không có polygon {net} trên {L} giao với shape")
        return {"layer": L, "net": net, "polygons": n, "area_mm2": round(g.area, 3)}

    def op_trace(self, o):
        """Vẽ trace. pieces=[{"points":[[x,y]...], "width": mm}] hoặc points + width.
        clear_pours=gap (mm): khoét kênh trong pour net khác dọc trace (trace/2 + gap)."""
        L, net = o["layer"], o["net"]
        pieces = o.get("pieces") or [{"points": o["points"], "width": o["width"]}]
        out = []
        cu = []
        for pc in pieces:
            w = pc["width"]
            tr = self.edb.modeler.create_trace([[x * MM, y * MM] for x, y in pc["points"]], layer_name=L, width=w * MM,
                                               net_name=net, start_cap_style=o.get("cap", "Round"),
                                               end_cap_style=o.get("cap", "Round"), corner_style=o.get("corner", "Round"))
            if not tr:
                raise RuntimeError("create_trace lỗi")
            g = LineString(pc["points"]).buffer(w / 2, cap_style=1)
            cu.append(g)
            self.ch.setdefault("_trace_geoms", []).append((L, net, g))
            out.append({"id": tr.id, "width": w, "length": round(LineString(pc["points"]).length, 3)})
            self.ch["traces"].append({"id": tr.id, "layer": L, "net": net, "width_mm": w,
                                      "length_mm": round(LineString(pc["points"]).length, 3)})
        CU = unary_union(cu)
        cleared = []
        gap = o.get("clear_pours")
        if gap:
            chan = unary_union([LineString(pc["points"]).buffer(pc.get("channel_width", pc["width"]) / 2 + gap, cap_style=1)
                                for pc in pieces])
            for nn in sorted({n for n, t, g, i in self.R.LAY[L] if n != net and t != "path"}):
                for i, g in self.polygons(L, nn, near=chan):
                    cutg = chan.intersection(Polygon(_outer(g)).buffer(0.02, join_style=2))
                    for pc in parts(cutg):
                        self.add_void(self.core(i), L, nn, geom=Polygon(pc.exterior), why=f"kênh cho trace {net}")
                        self._shrink(i, L, nn, Polygon(pc.exterior))
                    cleared.append({"polygon": i, "net": nn, "removed_mm2": round(chan.intersection(g).area, 3)})
        # vật cản cứng: trace net khác, pad via/pin net khác; polygon net khác chỉ khi không khoét kênh
        hard = [g for nn, t, g, i in self._items(L) if nn != net and (t == "path" or not gap)]
        hard += [g for i, (l, n, g) in self.live.items() if l == L and n != net and not gap]
        hard += [g for (l, n, g) in self.ch["_trace_geoms"] if l == L and n != net]
        vias = self.R_via_pads(L, net, CU)
        if not vias.is_empty:
            hard.append(vias)
        H = unary_union(hard) if hard else Polygon()
        gmin = round(CU.distance(H), 4) if not H.is_empty else None
        if gmin is not None and gmin < self.rules["min_copper_gap"] - 1e-4:
            self.ch["warnings"].append(f"trace {net} {L}: khe hở nhỏ nhất {gmin} mm < {self.rules['min_copper_gap']}")
        return {"layer": L, "net": net, "pieces": out, "cleared_pours": cleared, "min_gap_to_other_copper": gmin}

    def R_via_pads(self, L, net, near):
        gs = []
        for v in self.all_vias():
            if v["net"] == net or not self.R.on_layer(v, L):
                continue
            r = self.R.padr(v["pd"], L) or (0.25 if v["pin"] else 0.15)
            p = Point(v["x"], v["y"])
            if near.distance(p) < r + 1.0:
                gs.append(p.buffer(r, 32))
        return unary_union(gs) if gs else Polygon()

    def op_via(self, o):
        """Đặt via (một hay nhiều điểm). Mỗi điểm được kiểm tra: nằm trên đồng cùng net ở lớp `land`
        (mặc định from/to), cách đồng net khác ≥ pad + min_copper_gap ở mọi lớp xuyên qua (trừ plane được khoét),
        cách via khác ≥ via_pitch. Không đạt -> dời trong bán kính `search` (mm), không được thì bỏ.
        Tự khoét antipad (pad + antipad_margin) ở polygon net khác trên mọi lớp via xuyên qua."""
        net, pdn, sl, el = o["net"], o["padstack"], o["from"], o["to"]
        R = self.R
        pdef = self.pdef(pdn)
        if pdn not in R.PD:
            from .extract import pad_table
            R.PD.update(pad_table(self.edb, [pdn]))
        a, b = sorted([R.idx(sl), R.idx(el)])
        span = R.SIG[a:b + 1]
        land = o.get("land") or [sl, el]
        pitch = o.get("pitch", self.rules["via_pitch"])                    # tới via/pin net khác
        pitch_same = o.get("pitch_same", self.rules["via_pitch_same"])     # tới via/pin cùng net + via mới
        search = o.get("search", self.rules["via_search"])
        mg = self.rules["min_copper_gap"]
        am = o.get("antipad_margin", self.rules["antipad_margin"])
        lm = o.get("land_margin", self.rules["land_margin"])
        # lớp được phép khoét (polygon net khác): mặc định mọi lớp xuyên qua
        void_layers = set(o.get("void_layers") or span)
        # chỉ xét hình học quanh các điểm (cắt trước, prepare 1 lần / op -> nhanh)
        win = box(*unary_union([Point(p).buffer(search + 2.0) for p in o["points"]]).bounds)
        all_v = self.all_vias()
        own_poly, own_in, own_small = {}, {}, {}
        for L in land:
            pr = R.padr(pdn, L)
            poly = unary_union([g.intersection(win) for i, g in self.polygons(L, net, near=win)] or [Polygon()])
            small = [g.intersection(win) for nn, t, g, i in self._items(L) if nn == net and t == "path" and g.intersects(win)]
            small += [g.intersection(win) for (l, n, g) in self.ch.get("_trace_geoms", []) if l == L and n == net and g.intersects(win)]
            small += [Point(v["x"], v["y"]).buffer(R.padr_min(v["pd"], L) or 0.1, 16) for v in all_v
                      if v["net"] == net and R.on_layer(v, L) and win.contains(Point(v["x"], v["y"]))]
            own_poly[L] = prep(poly)
            own_in[L] = prep(poly.buffer(-(pr + lm))) if not poly.is_empty else None
            own_small[L] = prep(unary_union(small)) if small else None
        hardL, hard_buf = {}, {}
        for L in span:
            hard = [g.intersection(win) for nn, t, g, i in self._items(L)
                    if nn != net and (t == "path" or L not in void_layers) and g.intersects(win)]
            hard += [g.intersection(win) for (l, n, g) in self.ch.get("_trace_geoms", []) if l == L and n != net and g.intersects(win)]
            hardL[L] = unary_union(hard) if hard else Polygon()
            pr = R.padr(pdn, L)
            hard_buf[L] = prep(hardL[L].buffer(pr + mg)) if pr and not hardL[L].is_empty else None

        near_all = [v for v in all_v if any(R.on_layer(v, L) for L in span)
                    and any(math.hypot(v["x"] - x, v["y"] - y) < search + max(pitch, pitch_same) + 0.5
                            for x, y in o["points"])]
        KO = unary_union([to_geom(k) for k in o["keep_out"]]) if o.get("keep_out") else None

        def land_ok(L, p):
            """Tâm trong polygon cùng net -> pad + land_margin phải nằm trọn trong polygon (đáp lên plane).
            Ngoài polygon -> chấp nhận nếu tâm nằm trên trace / pad pin-via cùng net (đầu trace, pad SMD)."""
            if own_poly[L].contains(p):
                return own_in[L] is not None and own_in[L].contains(p)
            return own_small[L] is not None and own_small[L].intersects(p)

        def why_bad(x, y, placed, first=False):
            p = Point(x, y)
            why = []
            if KO is not None and KO.distance(p) < (R.padr(pdn, sl) or 0.1):
                why.append("trong vùng keep_out")
                if not first:
                    return why
            for L in land:
                if not land_ok(L, p):
                    why.append(f"không đáp được lên đồng {net} ở {L}")
                    if not first:
                        return why
            for L in span:
                if hard_buf[L] is not None and hard_buf[L].intersects(p):
                    d = hardL[L].distance(p) - R.padr(pdn, L)
                    if d < mg:
                        why.append(f"gần đồng net khác ở {L} ({d:.3f} mm)")
                        if not first:
                            return why
            for v in near_all:
                d = math.hypot(v["x"] - x, v["y"] - y)
                lim = pitch_same if v["net"] == net else pitch
                if d < lim:
                    why.append(f"cách via/pin {v['net']} {d:.2f} mm < {lim}")
                    break
            for q in placed:
                if math.hypot(q[0] - x, q[1] - y) < pitch_same:
                    why.append("gần via mới khác")
                    break
            return why

        st = o.get("search_step", self.rules["via_search_step"])
        k = int(round(search / st))
        cand = sorted(((math.hypot(i * st, j * st), i, j) for i in range(-k, k + 1) for j in range(-k, k + 1)
                       if 0 < math.hypot(i * st, j * st) <= search + 1e-9))
        placed, report = [], []
        for x, y in o["points"]:
            why = why_bad(x, y, placed, first=True)
            if not why:
                placed.append((x, y)); report.append({"target": [x, y], "status": "ok", "xy": [x, y]}); continue
            best = None
            for d, i, j in cand:
                q = (round(x + i * st, 4), round(y + j * st, 4))
                if not why_bad(*q, placed):
                    best = (d, q)
                    break
            if best:
                placed.append(best[1])
                report.append({"target": [x, y], "status": f"moved {best[0]:.2f} mm", "xy": list(best[1]), "why": why})
            else:
                report.append({"target": [x, y], "status": "dropped", "why": why})
        fl, tl = self.layer(sl), self.layer(el)
        nvoid = 0
        for x, y in placed:
            pt = self.api.Geometry.PointData(self.v(x * MM), self.v(y * MM))
            inst = self.api.Cell.Primitive.PadstackInstance.Create(self.layout, self.net(net), "", pdef, pt, self.v(0.0),
                                                                    fl, tl, None, None)
            if inst.IsNull():
                raise RuntimeError(f"Đặt via lỗi tại {x}, {y}")
            self.new_vias.append((x, y, pdn, net, sl, el))
            for L in span:
                if L not in void_layers:
                    continue
                r = (R.padr(pdn, L) or 0.0) + am
                r = max(r, o.get("antipad_min_r", 0.0))
                c = Point(x, y).buffer(r, 32)
                for nn in sorted({n for n, t, g, i in R.LAY[L] if n != net and t != "path"} |
                                 {n for (l, n, g) in self.live.values() if l == L and n != net}):
                    for i, g in self.polygons(L, nn, near=c):
                        self.add_void(self.core(i), L, nn, circle=(x, y, r), why=f"antipad via {net} {x:.3f},{y:.3f}")
                        self._shrink(i, L, nn, c)
                        nvoid += 1
            self.ch["vias"].append({"pd": pdn, "x": x, "y": y, "from": sl, "to": el, "net": net, "land": list(land)})
        return {"net": net, "padstack": pdn, "placed": len(placed), "dropped": sum(r["status"] == "dropped" for r in report),
                "antipads": nvoid, "points": report}

    def op_delete(self, o):
        """ids = primitive id hoặc (016) id via / padstack instance (như layout_region liệt kê). Pin linh kiện -> lỗi."""
        n, nv, why = 0, 0, o.get("why", "delete")
        vias = {v["id"]: v for v in self.R.inst}
        for pid in o["ids"]:
            if pid in self.R.BYID or pid in self.live or pid in self._made:
                L, net = (self.R.BYID.get(pid) or self.live.get(pid) or ("?", "?"))[:2]
                self._delete(pid, L, net, why)
            elif pid in vias:
                self._delete_via(vias[pid], why)
                nv += 1
            else:                                   # ngoài vùng đọc: primitive (như cũ), không có -> via
                try:
                    self._delete(pid, "?", "?", why)
                except RuntimeError:
                    v = self._via_outside(pid)
                    if v is None:
                        raise RuntimeError(f"Không tìm thấy primitive / via id {pid}") from None
                    self._delete_via(v, why)
                    nv += 1
            n += 1
        return {"deleted": n, "vias": nv}

    def _via_inst(self, pid):
        inst = self.edb.padstacks.instances.get(pid)
        if inst is None:
            raise RuntimeError(f"Không tìm thấy via id {pid}")
        return inst

    def _via_outside(self, pid):
        inst = self.edb.padstacks.instances.get(pid)
        if inst is None:
            return None
        comp = ""
        if inst.is_pin:
            try:
                comp = inst.component.refdes
            except Exception:
                comp = ""
        return dict(id=pid, pd=inst.padstack_definition, net=inst.net_name, x=inst.position[0] / MM,
                    y=inst.position[1] / MM, sl=inst.start_layer, el=inst.stop_layer, comp=comp, pin=bool(inst.is_pin))

    def _delete_via(self, v, why):
        if v["pin"]:
            raise RuntimeError(f"id {v['id']} là pin của {v['comp'] or 'linh kiện'} (net {v['net']}): không xoá pin")
        inst = self._via_inst(v["id"])
        obj = getattr(inst, "_edb_object", None) or inst._edb_padstackinstance
        obj.Delete()
        self.gone_vias.add(v["id"])
        self.ch.setdefault("deleted_vias", []).append({"id": v["id"], "pd": v["pd"], "net": v["net"], "x": v["x"],
                                                       "y": v["y"], "from": v["sl"], "to": v["el"], "why": why})

    # ------------------------------------------------------------------ dọn void vụn sau khi gộp
    def cleanup_merged(self):
        """Void vụn do Unite (diện tích < sliver_mm2, không có via bên trong), void trùng, void suy biến."""
        out = {}
        if not self.merged:
            return out
        vias = [(v["x"], v["y"]) for v in self.all_vias()]
        for mid in self.merged:
            if mid in self.gone:
                continue
            c = self.core(mid)
            seen, dele = set(), {"sliver": 0, "duplicate": 0, "degenerate": 0}
            vs = _voids(c)
            for vd in vs:
                pd = vd.GetPolygonData()
                area = pd.Area() / MM / MM
                bb = _pd_bbox_poly(pd)
                if len(list(pd.Points)) < 2:
                    vd.Delete(); dele["degenerate"] += 1; continue
                x0, y0, x1, y1 = bb.bounds
                hasv = any(x0 - 1e-3 <= x <= x1 + 1e-3 and y0 - 1e-3 <= y <= y1 + 1e-3 for x, y in vias)
                if area < self.rules["sliver_mm2"] and not hasv:
                    vd.Delete(); dele["sliver"] += 1; continue
                key = (round(area, 6), round((x0 + x1) / 2, 4), round((y0 + y1) / 2, 4))
                if key in seen:
                    vd.Delete(); dele["duplicate"] += 1; continue
                seen.add(key)
            out[mid] = {"voids_before": len(vs), "deleted": dele}
        return out


def _voids(core):
    """Void (primitive .NET) của một polygon."""
    try:
        return list(core.Voids)
    except Exception:
        return list(core.GetVoids())


def _outer(g):
    """Outline ngoài lớn nhất của geometry."""
    ps = parts(g)
    return max(ps, key=lambda p: p.area).exterior if ps else Polygon().exterior


def _pd_bbox_poly(pd):
    bb = pd.GetBBox()
    a, b = bb.Item1, bb.Item2
    return box(a.X.ToDouble() / MM, a.Y.ToDouble() / MM, b.X.ToDouble() / MM, b.Y.ToDouble() / MM)


def _bbox_poly(pd):
    return _pd_bbox_poly(pd)


OPS = {"add_copper": Editor.op_add_copper, "carve": Editor.op_carve, "remove_copper": Editor.op_remove_copper,
       "void": Editor.op_void, "trace": Editor.op_trace, "via": Editor.op_via, "delete": Editor.op_delete}


def op_bbox(o):
    """bbox (mm) của một op để chọn vùng đọc."""
    gs = []
    for k in ("shape", "keep_out"):
        if k in o:
            vals = o[k] if k == "keep_out" else [o[k]]
            gs += [to_geom(v) for v in vals]
    for pc in o.get("pieces") or []:
        gs.append(LineString(pc["points"]).buffer(pc.get("width", 0.2)))
    if o.get("points") and o["op"] == "trace":
        gs.append(LineString(o["points"]).buffer(o.get("width", 0.2)))
    if o.get("points") and o["op"] == "via":
        gs += [Point(p).buffer(o.get("search", 1.0) + 1.0) for p in o["points"]]
    if not gs:
        return None
    return unary_union(gs).bounds
