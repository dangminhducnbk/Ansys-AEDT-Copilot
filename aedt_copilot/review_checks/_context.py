"""Ngữ cảnh đo dùng chung, tính lười (feature 011): board index, trace channel, primitive của net, cửa sổ, chỉ mục
đồng GND (chỉ khi check 'reference' cần), via rows (dùng chung cho 'vias' và 'routing').

Mọi hàm đo là của cut_board/review.py (không đổi) -> số liệu giống hệt review_layout.
"""
from ..cut_board import config, inspect_board
from ..cut_board import review as RV

MM = RV.MM


class Ctx:
    def __init__(self, edb, log=None, board=None):
        d = config.defaults()
        self.board = board                                     # 030: .aedb (bảng stackup của board)
        self.edb, self.R, self.refs = edb, d["review"], d["cutout"]["reference_nets"]
        self.step = float(self.R["sample_step_mm"]) * MM
        self.log = log or (lambda *a: None)
        self._B = None
        PD = edb.core.Geometry.PointData
        self.pt = lambda x, y: PD(edb.edb_value(x), edb.edb_value(y))

    @property
    def B(self):
        if self._B is None:
            self._B = RV.Board(self.edb, self.refs, self.R)
        return self._B


class ChannelCtx:
    """Một channel: các phần tính một lần, khi check đầu tiên cần."""

    def __init__(self, ctx, spec):
        self.ctx, self.spec = ctx, spec
        self._cache = {}

    def _get(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    @property
    def trace(self):
        c, s = self.ctx, self.spec
        return self._get("trace", lambda: inspect_board.trace_channel(c.edb, s["comp_a"], s["comp_b"], s["patterns"],
                                                                      c.refs))

    @property
    def collected(self):
        return self._get("collected", lambda: RV._collect(self.ctx.edb, self.ctx.B, self.trace["nets"]))

    @property
    def window(self):
        def f():
            paths, _, vias, pins = self.collected
            allp = [q for p in paths for q in p["pts"]] + [(v["x"], v["y"]) for v in vias + pins]
            xs, ys = [p[0] for p in allp], [p[1] for p in allp]
            return (min(xs) - 1 * MM, min(ys) - 1 * MM, max(xs) + 1 * MM, max(ys) + 1 * MM)
        return self._get("window", f)

    @property
    def copper(self):
        """(cu, oc) như review.review(): cửa sổ + lề ảnh zoom + 2 mm."""
        def f():
            win, R = self.window, self.ctx.R
            g = float(R["zoom_margin_mm"]) * MM + 2 * MM
            cu = RV.Copper(self.ctx.edb, self.ctx.B.ref_prims, (win[0] - g, win[1] - g, win[2] + g, win[3] + g))
            oc = RV.Copper(self.ctx.edb, self.ctx.B.other_prims(cu.window, self.trace["nets"]), cu.window)
            return cu, oc
        return self._get("copper", f)

    @property
    def via_rows(self):
        def f():
            paths, polys, vias, pins = self.collected
            stacks = RV._stacks(vias, float(self.ctx.R["stack_merge_mm"]) * MM)
            return RV.via_rows(self.ctx.B, stacks, paths, polys, pins, self.ctx.pt, self.ctx.R)
        return self._get("via_rows", f)

    @property
    def groups(self):
        """030: cặp / bộ 3 + chuỗi net + chiều dài (như check routing). -> {chains, groups, chain_len, intra}."""
        def f():
            from ..cut_board import naming
            c, t = self.ctx, self.trace
            rows, _ = self.via_rows
            pg = set(c.edb.nets.power.keys()) | set(c.refs)
            chains = RV._chains(t["nets"], t["series"], t["start_nets"], pg)
            groups = naming.review_groups(t["start_nets"])                  # 034: tên 'X_P*' cũng ghép cặp
            chain_len, intra, inter, widths = RV.lengths(chains, self.collected[0], rows, groups)
            return {"chains": chains, "groups": groups, "chain_len": chain_len, "intra": intra}
        return self._get("groups", f)

    def built(self):
        return sorted(self._cache)
