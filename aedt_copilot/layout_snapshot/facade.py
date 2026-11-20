"""SnapEdb: đối tượng CHỈ ĐỌC trả lời đúng các thuộc tính PyEDB mà code review đọc (feature 023).

cut_board/review.py (Board, Copper, _collect, check_reference, trace_stubs, via_rows), inspect_board.trace_channel và
review_checks chạy KHÔNG đổi trên đối tượng này -> cùng đầu vào, cùng thứ tự, cùng làm tròn -> cùng kết quả.

Dữ liệu (data-model.md): index (cả board) + window (hình học trong cửa sổ). Thứ gì không có trong snapshot ->
SnapshotMissing (BaseException: `except Exception` trong code đo không nuốt được) -> review chạy live + cảnh báo.

Thêm check mới cho developer: viết hàm đo trên các thuộc tính ở đây (nets / components / primitive / PointInPolygon) và
thử offline bằng snapshot giả (tests/unit/_snapshot_fixture.py), không cần PyEDB.
"""
from array import array

import shapely

from . import SnapshotMissing

BIGY = 1e300                     # điểm đánh dấu cung của EDB (Y = DBL_MAX, X = chiều cao cung)
BBOX_PAD = 1e-9                  # bbox index làm tròn 9 số: nới 1 nm -> lọc bbox của extract_region là tập cha


def pyedb_points(raw, arc_segments=6):
    """029: như PyEDB Primitive.points(arc_segments) (pyedb 0.85 _get_points_for_plot + orient_polygon) trên điểm gốc
    PolygonData.Points đã lưu -> cùng số thực với live. Không điểm -> [] (như PyEDB)."""
    from pyedb.generic.geometry_operators import GeometryOperators
    from pyedb.misc.utilities import compute_arc_points
    x, y = [], []
    n = len(raw)
    for i, (px, py) in enumerate(raw):
        if not py > BIGY:
            x.append(px)
            y.append(py)
        else:
            p1 = [raw[i - 1][0], raw[i - 1][1]]
            p2 = [raw[i + 1][0], raw[i + 1][1]] if i + 1 < n else [raw[0][0], raw[0][1]]
            xa, ya = compute_arc_points(p1, p2, px, arc_segments)
            x.extend(xa)
            y.extend(ya)
    if not x:
        return []
    return GeometryOperators.orient_polygon(x, y, clockwise=True)


class _Val:
    """edb_value(...) giả: ToDouble() + float()."""

    def __init__(self, v):
        self.v = v

    def ToDouble(self):
        return float(self.v)

    def __float__(self):
        return float(self.v)


def _f(v):
    return float(v)


class _Geometry:
    @staticmethod
    def PointData(x, y):
        return (_f(x), _f(y))


class _Core:
    Geometry = _Geometry


class _Cell:
    def __init__(self, name):
        self.name = name

    def GetName(self):
        return self.name


class _PD:
    """polygon_data.core giả: PointInPolygon trên polygon dây cung (shapely, đã prepare)."""

    def __init__(self, snap, ref):
        self._snap, self._ref, self._g = snap, ref, None

    def geom(self):
        if self._g is None:
            off, n = self._ref
            g = shapely.from_wkb(self._snap.geom[off:off + n])
            shapely.prepare(g)
            self._g = g
        return self._g

    def PointInPolygon(self, pt):
        return bool(shapely.intersects_xy(self.geom(), pt[0], pt[1]))


class _PDHolder:
    def __init__(self, core):
        self.core = core

    @property
    def points(self):
        """027: đường bao ngoài (m) như PyEDB polygon_data.points (cung tròn = dây cung <= arc_tol_um)."""
        g = self.core.geom()
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda q: q.area)
        return [[float(x), float(y)] for x, y in list(g.exterior.coords)[:-1]]


class _Void:
    def __init__(self, snap, row):
        vid, bbox, off, n = row[:4]
        self.id, self.bbox = vid, bbox
        self.polygon_data = _PDHolder(_PD(snap, (off, n)))
        self.is_void = True
        self._snap, self._r = snap, row[4:6]

    def points(self, arc_segments=6):
        if len(self._r) != 2:
            raise SnapshotMissing(f"original points of void {self.id} not in the snapshot (schema < 2)")
        return pyedb_points(self._snap.raw(self._r), arc_segments)


class _Pt:
    def __init__(self, x, y):
        self.X, self.Y = _Val(x), _Val(y)


class _BBox:
    def __init__(self, x0, y0, x1, y1):
        self.Item1, self.Item2 = _Pt(x0, y0), _Pt(x1, y1)


class _PrimCore:
    """p.core.GetPolygonData().GetBBox() giả (extract_region lọc nhanh): bbox index nới 1 nm."""

    def __init__(self, prim):
        self._p = prim

    def GetPolygonData(self):
        return self

    def GetBBox(self):
        b = self._p._bbox
        if b is None:
            raise AttributeError(f"primitive {self._p.id} has no polygon data")
        return _BBox(b[0] - BBOX_PAD, b[1] - BBOX_PAD, b[2] + BBOX_PAD, b[3] + BBOX_PAD)


class _Prim:
    def __init__(self, snap, row):
        pid, kind, layer, net, is_void, bbox = row
        self._snap, self.id, self.kind, self.layer_name, self.net_name = snap, pid, kind, layer, net
        self.is_void, self._bbox = bool(is_void), bbox

    @property
    def bbox(self):
        if self._bbox is None:
            raise AttributeError(f"primitive {self.id} has no polygon data (as in PyEDB)")
        return self._bbox

    def _g(self):
        g = self._snap.geoms.get(str(self.id))
        if g is None:
            raise SnapshotMissing(f"geometry of primitive {self.id} ({self.layer_name}, {self.net_name}) "
                                  "is outside the snapshot window")
        return g

    @property
    def polygon_data(self):
        return _PDHolder(self._snap.pd(self.id, self._g()["o"]))

    @property
    def voids(self):
        return [_Void(self._snap, r) for r in self._g().get("v", [])]

    @property
    def type(self):
        """029: như PyEDB Primitive.type (GetPrimitiveType().ToString().lower())."""
        return str(self.kind).lower()

    @property
    def core(self):
        return _PrimCore(self)

    def points(self, arc_segments=6):
        """029: như PyEDB points(arc_segments) từ điểm gốc (cung đổi y hệt live)."""
        r = self._g().get("r")
        if r is None:
            raise SnapshotMissing(f"original points of primitive {self.id} not in the snapshot (schema < 2)")
        return pyedb_points(self._snap.raw(r), arc_segments)

    def area(self):
        """Diện tích chỉ dùng cho luật lớp plane: primitive lớn nhất của (net, lớp) -> diện tích thật (toàn board);
        primitive khác -> 0 (Board chỉ lấy max nên kết quả như đọc từng primitive)."""
        a = self._snap.plane_max.get((self.net_name, self.layer_name))
        return a[0] if a and a[1] == self.id else 0.0

    def _path(self):
        p = self._snap.paths.get(str(self.id))
        if p is None:
            raise SnapshotMissing(f"path {self.id} ({self.layer_name}, {self.net_name}) is outside the snapshot window")
        return p

    @property
    def center_line(self):
        return [list(q) for q in self._path()["c"]]

    @property
    def width(self):
        return self._path()["w"]

    @property
    def length(self):
        return self._path()["l"]


class Path(_Prim):                 # tên lớp = tên PyEDB mà review.py kiểm tra ("Path")
    pass


class Polygon(_Prim):
    pass


class _Inst:
    def __init__(self, snap, row):
        iid, net, pdef, x, y, start, stop, is_pin, comp, name = row
        self._snap, self.id, self.net_name, self.padstack_definition = snap, iid, net, pdef
        self.position = [x, y]
        self.start_layer, self.stop_layer, self.is_pin = start, stop, bool(is_pin)
        self.component_name, self.name = comp or "", name
        self.pin_number = name                                    # 027: như PyEDB (tên pin)

    @property
    def layer_range_names(self):
        """Như PyEDB: các lớp signal từ start tới stop (theo thứ tự stackup)."""
        out, started = [], False
        for ln in self._snap.metal:
            if started:
                out.append(ln)
                if ln in (self.stop_layer, self.start_layer):
                    break
            elif ln in (self.start_layer, self.stop_layer):
                started = True
                out.append(ln)
                if self.start_layer == self.stop_layer:
                    break
        return out

    @property
    def backdrill_parameters(self):
        bd = self._snap.backdrill.get(str(self.id))
        if bd is None:
            raise SnapshotMissing(f"backdrill of via {self.id} ({self.net_name}) not in the snapshot window")
        return bd

    @property
    def bounding_box(self):
        b = self._snap.pin_bbox.get(str(self.id))
        if b is None:
            if self._snap.lenient:
                raise ValueError(f"pin box {self.id} not in snapshot (index-only pass)")
            raise SnapshotMissing(f"box of pin {self.component_name}.{self.name} ({self.net_name}) not in the snapshot")
        return b

    @property
    def component(self):
        return self._snap.components.instances.get(self.component_name) if self.component_name else None


class _Comp:
    def __init__(self, snap, rd, d):
        self._snap, self.refdes, self.name = snap, rd, rd
        self.type, self.partname, self.part_name = d["type"], d["part"], d["part"]
        self.numpins, self.placement_layer = d["numpins"], d.get("layer")
        self._pins = d["pins"]
        self._bb = d.get("bbox")

    @property
    def bounding_box(self):
        """029: như PyEDB (m, round 6) - đọc lúc build; không đọc được -> lỗi (layout_region bỏ linh kiện như live)."""
        if self._bb is None:
            raise ValueError(f"component box {self.refdes} not readable at build")
        return list(self._bb)

    @property
    def pins(self):
        return {self._snap.inst(i).name: self._snap.inst(i) for i in self._pins}


class _Net:
    def __init__(self, snap, name):
        self._snap, self.name = snap, name

    @property
    def primitives(self):
        return [self._snap.prim(i) for i in self._snap.net_prims.get(self.name, [])]

    @property
    def padstack_instances(self):
        return [self._snap.inst(i) for i in self._snap.net_insts.get(self.name, [])]

    @property
    def components(self):
        out = {}
        for p in self.padstack_instances:
            c = p.component
            if c and c.refdes not in out:
                out[c.refdes] = c
        return out


class _Nets:
    def __init__(self, snap):
        self.nets = {n: _Net(snap, n) for n in snap.index["nets"]}
        self.power = {n: self.nets[n] for n in snap.index["power_nets"] if n in self.nets}

    @property
    def netlist(self):
        return list(self.nets)


class _Layer:
    type = "signal"                # index chỉ lưu lớp signal (như stackup.signal_layers)

    def __init__(self, name, lower, thick):
        self.name, self.lower_elevation, self.thickness = name, lower, thick


class _Stackup:
    def __init__(self, layers):
        self.layers = {n: _Layer(n, lo, th) for n, lo, th in layers}
        self.signal_layers = dict(self.layers)


class _Components:
    def __init__(self, snap):
        self.instances = {rd: _Comp(snap, rd, d) for rd, d in snap.index["comps"].items()}


class _PadParam:
    def __init__(self, vals):
        self._v = vals

    @property
    def parameters_values(self):
        if self._v is None:
            raise ValueError("pad parameters not readable at build")
        return self._v


class _Def:
    def __init__(self, d):
        self._d = d

    @property
    def hole_diameter(self):
        if "hole_diameter" not in self._d:
            raise ValueError("hole_diameter not readable at build")
        return self._d["hole_diameter"]

    @property
    def hole_properties(self):
        if "hole_props0" not in self._d:
            raise ValueError("hole_properties not readable at build")
        return [self._d["hole_props0"]]

    @property
    def pad_by_layer(self):
        if self._d.get("pads") is None:
            raise ValueError("pad_by_layer not readable at build")
        return {l: _PadParam(v) for l, v in self._d["pads"].items()}


class _RPad:
    """029: pad / antipad của bảng padstack gốc: [geometry_type hoặc shape (chuỗi), tham số số gốc]."""

    def __init__(self, row):
        self._s, self._v = row[0], row[1]

    @property
    def geometry_type(self):
        return self._s

    @property
    def shape(self):
        return self._s

    @property
    def parameters_values(self):
        return list(self._v)


class _RDef:
    """029: definition cho extract.pad_table (layout_region): dữ liệu = pad_table(scale=1) lúc build."""

    def __init__(self, d):
        self._d = d

    @property
    def pad_by_layer(self):
        pads = self._d.get("pads") or {}
        if "err" in pads:
            raise RuntimeError(pads["err"])
        return {l: _RPad(r) for l, r in pads.items()}

    @property
    def antipad_by_layer(self):
        return {l: _RPad(r) for l, r in (self._d.get("antipads") or {}).items()}

    @property
    def hole_properties(self):
        if self._d.get("hole") is None:
            raise ValueError("hole not readable at build")
        return [self._d["hole"]]


class _DefMap(dict):
    def __missing__(self, name):
        raise SnapshotMissing(f"padstack definition {name} not in the snapshot")


class _Defs:
    def __init__(self, defs, snap=None):
        self.definitions = _DefMap({n: _Def(d) for n, d in defs.items()})
        self._snap = snap

    @property
    def instances(self):
        """027: {id: via / pin} mọi padstack instance của board (như PyEDB padstacks.instances)."""
        return {r[0]: self._snap.inst(r[0]) for r in self._snap.index["insts"]}


class _Modeler:
    def __init__(self, snap):
        self._snap = snap

    @property
    def primitives_by_layer(self):
        by = {}
        for row in self._snap.index["prims"]:
            by.setdefault(row[2], []).append(self._snap.prim(row[0]))
        return by

    @property
    def primitives(self):
        return [self._snap.prim(r[0]) for r in self._snap.index["prims"]]

    def clear_cache(self):
        """029: như PyEDB layout.clear_cache (snapshot không có cache cần xoá)."""
        return None


class SnapEdb:
    """index: dict của index.json. window: (window.json dict, geom bytes) hoặc None (chỉ index).
    lenient=True: bbox pin thiếu -> ValueError (lượt dò channel chỉ để biết net, chưa có cửa sổ).
    region=True (029, layout_region): padstacks.definitions = bảng padstack gốc (extract.pad_table chạy không đổi)."""

    def __init__(self, index, window=None, lenient=False, extra_pin_bbox=None, region=False):
        self.index, self.lenient = index, lenient
        w, g = window if window else ({}, b"")
        self.win, self.geom = w, g
        self.window = tuple(w["window"]) if w.get("window") else None
        self.geoms, self.paths = w.get("geoms", {}), w.get("paths", {})
        self.backdrill, self.pin_bbox = w.get("backdrill", {}), w.get("pin_bbox", {})
        if extra_pin_bbox:                                        # 027: khung mọi pin của linh kiện đầu (gồm GND)
            self.pin_bbox = dict(self.pin_bbox, **{str(k): v for k, v in extra_pin_bbox.items()})
        self.metal = [l[0] for l in index["layers"]]
        self._prims = {r[0]: r for r in index["prims"]}
        self._insts = {r[0]: r for r in index["insts"]}
        self._pcache, self._icache, self._pdcache = {}, {}, {}
        self.net_prims, self.net_insts = {}, {}
        for r in index["prims"]:
            self.net_prims.setdefault(r[3], []).append(r[0])
        for r in index["insts"]:
            self.net_insts.setdefault(r[1], []).append(r[0])
        self.plane_max = {(n, l): (v[0], v[1]) for n, d in index.get("plane_area", {}).items() for l, v in d.items()}
        self.stackup = _Stackup(index["layers"])
        self.nets = _Nets(self)
        self.components = _Components(self)
        self.padstacks = _Defs(index.get("pad_defs", {}), self)
        if region:
            if "pad_table" not in index:
                raise SnapshotMissing("padstack table not in the snapshot (schema < 2)")
            self.padstacks.definitions = {n: _RDef(d) for n, d in index["pad_table"].items()}
        self.modeler = _Modeler(self)
        self.layout = self.modeler
        self.active_cell = _Cell(index.get("cell_name") or index["key"]["cell"])
        self.core = _Core()

    # ---- PyEDB-like helpers
    @staticmethod
    def edb_value(v):
        return _Val(v)

    def close(self):
        return True

    # ---- objects (cached, so identity is stable inside one review)
    def prim(self, pid):
        p = self._pcache.get(pid)
        if p is None:
            row = self._prims[pid]
            p = (Path if row[1] == "Path" else Polygon)(self, row)
            self._pcache[pid] = p
        return p

    def inst(self, iid):
        v = self._icache.get(iid)
        if v is None:
            v = _Inst(self, self._insts[iid])
            self._icache[iid] = v
        return v

    def raw(self, ref):
        """029: điểm gốc [(x, y)] (m, có điểm đánh dấu cung) từ bản ghi float64 trong geom.wkb."""
        off, n = ref
        a = array("d")
        a.frombytes(self.geom[off:off + n])
        return [(a[k], a[k + 1]) for k in range(0, len(a), 2)]

    def pd(self, pid, ref):
        d = self._pdcache.get(pid)
        if d is None:
            d = _PD(self, ref)
            self._pdcache[pid] = d
        return d
