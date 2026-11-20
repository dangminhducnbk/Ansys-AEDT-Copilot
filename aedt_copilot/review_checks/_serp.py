"""Serpentine (bù chiều dài) trong cặp vi sai (feature 033): nhận ra serpentine (bướu lặp lại so với dây kia) và đo theo
luật: G (khe mép-mép giữa 2 đoạn song song liền kề của chính serpentine) >= review.serp_gap_factor x H, A (biên độ,
tâm đường gốc -> tâm đỉnh) <= review.serp_amp_factor x W, không góc 90°, cạnh vát 45° c >= review.serp_chamfer_factor
x W (dung sai review.serp_chamfer_tol). Đơn vị m. Module riêng ('_') -> registry không nạp như một check.

Dùng chung cho luật serpentine (finding) và luật pair_gap (bỏ chỗ tách nằm trong serpentine của cùng cặp).
"""
import html as H
import math

MM = 1e-3
MIL = 0.0254 * MM


class Params:
    """Ngưỡng + hằng số nhận dạng từ template (review.serp_*)."""

    def __init__(self, R):
        g = lambda k, d: float(R.get(k, d))
        self.gap_factor, self.amp_factor = g("serp_gap_factor", 3), g("serp_amp_factor", 3)
        self.chamfer_factor, self.chamfer_tol = g("serp_chamfer_factor", 1.5), g("serp_chamfer_tol", 0.05)
        self.rise, self.bump_max = g("serp_rise_factor", 1.5), g("serp_bump_max_mm", 2) * MM
        self.spacing, self.ratio = g("serp_bump_spacing_mm", 2) * MM, g("serp_bump_ratio", 1.43)
        self.min_bumps, self.excl = int(g("serp_min_bumps", 2)), g("serp_excl_mm", 1) * MM
        self.step = g("serp_step_mm", 0.01) * MM


# ----------------------------------------------------------------------------- hình học
def _seg_pts(pts, step):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        out += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    return out + [tuple(pts[-1])]


def _t(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    L2 = ax * ax + ay * ay
    return 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L2))


def _d_seg(p, a, b):
    t = _t(p, a, b)
    return math.hypot(p[0] - a[0] - t * (b[0] - a[0]), p[1] - a[1] - t * (b[1] - a[1]))


def _proj(p, a, b):
    t = _t(p, a, b)
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def _runs(flags):
    out, i = [], 0
    while i < len(flags):
        if flags[i]:
            j = i
            while j + 1 < len(flags) and flags[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def _ang(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def _turn(a, b, c):
    t = abs(_ang(b, c) - _ang(a, b)) % 360
    return min(t, 360 - t)


def _near_dist(sm, segs):
    """Khoảng cách tâm-tâm từ mỗi mẫu tới dây kia (STRtree khi có shapely; nếu không thì vét cạn)."""
    try:
        import numpy as np
        import shapely
        from shapely.geometry import LineString
        geoms = [LineString([a, b]) for a, b in segs if a != b]
        tree = shapely.STRtree(geoms)
        (_, _), dist = tree.query_nearest(shapely.points(np.asarray(sm, dtype=float)), return_distance=True,
                                         all_matches=False)
        return [float(x) for x in dist]
    except Exception:
        return [min(_d_seg(q, a, b) for a, b in segs) for q in sm]


def find(path, other_paths, H_m, excl=(), P=None):
    """path: một primitive của một thành viên; other_paths: primitive của thành viên kia cùng lớp.
    -> [serpentine {net, layer, W, H, A, G, base, x0..y1, peak, peak_n, gpair, c90, chams, short, violations}]."""
    P = P or Params({})
    pts, W = [tuple(q) for q in path["pts"]], float(path["w"])
    segs = [(tuple(a), tuple(b)) for p in other_paths for a, b in zip(p["pts"], p["pts"][1:])]
    if len(pts) < 6 or not segs:
        return []
    sm = _seg_pts(pts, P.step)
    near = _near_dist(sm, segs)
    if not near:
        return []
    srt = sorted(near)
    base = srt[len(srt) // 4]                                   # khe tâm-tâm danh định (đoạn đi sát nhau)
    if base > 1.0 * MM:
        return []
    ex = list(excl)
    exc = [any(math.hypot(q[0] - e[0], q[1] - e[1]) < P.excl for e in ex) for q in sm]
    thr = base + P.rise * W
    away = [d > thr for d in near]                              # xa dây kia (chưa trừ vùng pin / via)
    far = [a and not x for a, x in zip(away, exc)]              # bỏ vùng thoát pad / via
    last = len(sm) - 1

    def fan_out(i, j):
        """2.11.1 (R2): 2 dây tách để vào chân / via (fan-out), không phải bướu: đoạn xa chạm vùng loại trừ quanh pin /
        via VÀ từ đó tới đầu path dây không quay lại sát dây kia. Bướu thật gần via thì có quay lại -> vẫn là bướu.
        (2.11.0: A đo chỗ tách P / N này, vd. SERLINK_DEVA2DEVB_L0_P A 0.571 mm.)"""
        left = i > 0 and exc[i - 1] and all(away[:i])
        right = j < last and exc[j + 1] and all(away[j + 1:])
        return left or right
    bumps = [(i, j) for i, j in _runs(far) if (j - i) * P.step < P.bump_max and not fan_out(i, j)]
    amp = lambda b: max(near[b[0]:b[1] + 1]) - base
    groups, cur = [], []
    for b in bumps:                                             # bướu lặp lại: gần nhau và cao gần bằng nhau
        if cur and ((b[0] - cur[-1][1]) * P.step > P.spacing or
                    not 1 / P.ratio <= amp(b) / max(amp(cur[-1]), 1e-12) <= P.ratio):
            groups.append(cur)
            cur = []
        cur.append(b)
    if cur:
        groups.append(cur)
    tol = 1 - P.chamfer_tol
    out = []
    for g in groups:
        if len(g) < P.min_bumps:
            continue
        i0, i1 = g[0][0], g[-1][1]
        reg = sm[i0:i1 + 1]
        mx = max(near[i0:i1 + 1])
        A = mx - base                                           # tâm đường gốc -> tâm đỉnh
        top = [k for k in range(i0, i1 + 1) if near[k] >= mx - 0.002 * MM]
        run = [top[0]] if top else [i0]                         # đoạn đỉnh liền của bướu đầu tiên
        for k in top[1:]:
            if k != run[-1] + 1:
                break
            run.append(k)
        ia = run[len(run) // 2]                                 # giữa đỉnh bướu đầu -> mũi tên A không đè G
        x0, x1 = min(q[0] for q in reg) - W, max(q[0] for q in reg) + W
        y0, y1 = min(q[1] for q in reg) - W, max(q[1] for q in reg) + W
        ids = [k for k, q in enumerate(pts) if x0 <= q[0] <= x1 and y0 <= q[1] <= y1]
        if len(ids) < 3:
            continue
        k0, k1 = max(ids[0] - 1, 0), min(ids[-1] + 1, len(pts) - 1)
        sub = pts[k0:k1 + 1]
        ss = list(zip(sub, sub[1:]))
        G, gpair, gpairs, cands = None, None, [], []                        # G: đoạn song song, không liền kề, chồng hình chiếu
        for i in range(len(ss)):
            for j in range(i + 2, len(ss)):
                a, b = ss[i], ss[j]
                if min(math.dist(*a), math.dist(*b)) < 0.5 * W:
                    continue                                    # bỏ dây cung ngắn (cung tròn)
                da, db = _ang(*a) % 180, _ang(*b) % 180
                if min(abs(da - db), 180 - abs(da - db)) > 5:
                    continue
                ux, uy = b[1][0] - b[0][0], b[1][1] - b[0][1]
                L = math.hypot(ux, uy)
                if L == 0:
                    continue
                ux, uy = ux / L, uy / L
                pa = sorted(((q[0] - b[0][0]) * ux + (q[1] - b[0][1]) * uy) for q in a)
                if pa[1] <= 1e-9 or pa[0] >= L - 1e-9:
                    continue
                d = min(_d_seg(a[0], *b), _d_seg(a[1], *b), _d_seg(b[0], *a), _d_seg(b[1], *a)) - W
                if d > 0:
                    cands.append((d, (a, b)))
        pk_ = sm[ia]
        nb = min(((_proj(pk_, a, b), a, b) for a, b in segs), key=lambda t: math.dist(t[0], pk_))[0]
        if cands:
            G = min(d for d, _ in cands)
            du = math.dist(pk_, nb) or 1                        # mũi tên A: tâm đường gốc -> tâm đỉnh
            a_base = (nb[0] + (pk_[0] - nb[0]) / du * base, nb[1] + (pk_[1] - nb[1]) / du * base)

            def mid(ab):
                return (sum(q[0] for sg in ab for q in sg) / 4, sum(q[1] for sg in ab for q in sg) / 4)
            # 2.11.1 (R1): cặp đoạn G (cùng G đo được, sai khác <= 0.1 µm) xa mũi tên A nhất -> không chồng nhau
            gpair = max((ab for d, ab in cands if d <= G + 1e-7), key=lambda ab: _d_seg(mid(ab), pk_, a_base))
            gpairs = [ab for d, ab in cands if d <= G + 1e-7]          # 2.11.2: ảnh Detail chọn cặp gần bướu đo
        c90, short, chams = [], [], []
        for k in range(1, len(sub) - 1):
            if 80 <= _turn(sub[k - 1], sub[k], sub[k + 1]) <= 100:
                c90.append(sub[k])
        bseg = min(segs, key=lambda ab: _d_seg(sm[i0], *ab))    # hướng đi của cặp (dây kia, gần đầu vùng)
        bang = _ang(*bseg) % 180
        for k in range(1, len(sub) - 2):                       # cạnh vát: nghiêng ~45° so với hướng đi của cặp
            t0, t1 = _turn(sub[k - 1], sub[k], sub[k + 1]), _turn(sub[k], sub[k + 1], sub[k + 2])
            rel = abs(_ang(sub[k], sub[k + 1]) % 180 - bang)
            rel = min(rel, 180 - rel)
            if 35 <= t0 <= 55 and 35 <= t1 <= 55 and 35 <= rel <= 55:
                L = math.dist(sub[k], sub[k + 1])
                chams.append((sub[k], sub[k + 1], L))
                if L < P.chamfer_factor * W * tol:
                    short.append((sub[k], sub[k + 1], L))
        viol = []
        if G is not None and G < P.gap_factor * H_m:
            viol.append(("G", f"gap between bends {G / MM:.3f} mm < {P.gap_factor:g}H {P.gap_factor * H_m / MM:.3f} mm"))
        if A > P.amp_factor * W:
            viol.append(("A", f"bump height {A / MM:.3f} mm > {P.amp_factor:g}W {P.amp_factor * W / MM:.3f} mm"))
        if c90:
            viol.append(("C", f"{len(c90)} corner(s) of 90°"))
        if short:
            viol.append(("S", f"45° chamfer {min(s[2] for s in short) / MM:.3f} mm < {P.chamfer_factor:g}W "
                              f"{P.chamfer_factor * W / MM:.3f} mm"))
        out.append({"net": path["net"], "layer": path["layer"], "W": W, "H": H_m, "A": A, "G": G, "base": base,
                    "n_bumps": len(g), "x0": x0, "y0": y0, "x1": x1, "y1": y1, "peak": pk_, "peak_n": nb,
                    "gpair": gpair, "gpairs": gpairs, "c90": c90, "chams": chams, "short": short, "violations": viol,
                    "limits": {"gap": P.gap_factor, "amp": P.amp_factor, "chamfer": P.chamfer_factor,
                               "tol": P.chamfer_tol}})
    return out


# ----------------------------------------------------------------------------- dữ liệu channel
def pairs(chains):
    """Cặp vi sai theo net đầu của mỗi chuỗi net (nhận cả cặp đặt tên chiều ngược) -> [[P, N]], P trước."""
    from ..cut_board import naming
    out = []
    for g in naming.review_groups([nets[0] for nets in chains.values() if nets]):      # 034: chung luật ghép
        if len(g) == 2:
            out.append(sorted(g, key=lambda n: (not n.rstrip("*").upper().endswith(("_P", "_DP", "+", "P")), n)))
    return out


def height(B, layer):
    """H: khoảng điện môi từ lớp trace tới lớp plane tham chiếu gần nhất (stackup); None nếu không có."""
    if layer not in getattr(B, "elev", {}):
        return None
    lo, hi = B.elev[layer]
    ds = []
    for pl in B.ref_layers(layer):
        plo, phi = B.elev[pl]
        ds.append(lo - phi if plo < lo else plo - hi)
    ds = [d for d in ds if d > 0]
    return min(ds) if ds else None


def detect(paths, chains, pins_vias, B, R):
    """-> [serpentine] của mọi cặp trong channel (cả 2 chiều), mỗi serpentine có 'group' (2 thành viên) và 'nets'
    (net của 2 chuỗi)."""
    P = Params(R)
    chain_of = {n: nets for nets in chains.values() for n in nets}
    out = []
    for g in pairs(chains):
        nets = set(chain_of.get(g[0], [g[0]])) | set(chain_of.get(g[1], [g[1]]))
        ex = [(q["x"], q["y"]) for q in pins_vias if q.get("net") in nets]
        for a, b in ((g[0], g[1]), (g[1], g[0])):
            na, nb = set(chain_of.get(a, [a])), set(chain_of.get(b, [b]))
            for pth in paths:
                if pth["net"] not in na:
                    continue
                oth = [q for q in paths if q["net"] in nb and q["layer"] == pth["layer"]]
                Hm = height(B, pth["layer"]) or 0.1 * MM
                for sp in find(pth, oth, Hm, ex, P):
                    sp["group"], sp["nets"] = list(g), sorted(nets)
                    out.append(sp)
    return out


def found(cc):
    """Serpentine của channel (tính một lần, dùng chung cho luật serpentine và pair_gap)."""
    def f():
        paths, _, vias, pins = cc.collected
        return detect(paths, cc.groups["chains"], vias + pins, cc.ctx.B, cc.ctx.R)
    return cc._get("serpentines", f)


def inside(sp, x, y, margin=0.5 * MM):
    return sp["x0"] - margin <= x <= sp["x1"] + margin and sp["y0"] - margin <= y <= sp["y1"] + margin


# ----------------------------------------------------------------------------- ảnh
def v_txt(m):
    return f"{m / MM:.3f} mm ({m / MIL:.1f} mil)"


def compare_rows(s):
    """[(chữ, đạt)] so sánh số đo với ngưỡng (dưới ảnh)."""
    lim = s.get("limits") or {"gap": 3, "amp": 3, "chamfer": 1.5, "tol": 0.05}
    W, A, G, Hh = s["W"], s["A"], s["G"], s["H"]
    rows = [(f"A = {v_txt(A)} must be ≤ {lim['amp']:g}W = {v_txt(lim['amp'] * W)}", A <= lim["amp"] * W)]
    if G is not None:
        rows.append((f"G = {v_txt(G)} must be ≥ {lim['gap']:g}H = {v_txt(lim['gap'] * Hh)}", G >= lim["gap"] * Hh))
    if s["chams"]:
        c_ = min(t[2] for t in s["chams"])
        rows.append((f"c (45° chamfer) = {v_txt(c_)} must be ≥ {lim['chamfer']:g}W = {v_txt(lim['chamfer'] * W)} "
                     f"(−{lim['tol'] * 100:g} %)", c_ >= lim["chamfer"] * W * (1 - lim["tol"])))
    if s["c90"]:
        rows.append((f"{len(s['c90'])} corner(s) of 90°: not allowed", False))
    return rows


# ----------------------------------------------------------------------------- ảnh (2.11.2: kiểu bản vẽ cơ khí)
C_MEMBER, C_OTHER = "#378ADD", "#85B7EB"          # thành viên có serpentine / dây còn lại (theo demo user duyệt)


def _add(a, b, k=1.0):
    return a[0] + b[0] * k, a[1] + b[1] * k


def _bump(s, paths):
    """Bướu được đo (chứa đỉnh A) theo hệ trục u (dây kia -> đỉnh) / t (dọc cặp), gốc tại tâm đỉnh.
    -> {u, t, tau0, tau1 (chân bướu), ta, tb (đỉnh), gap_lo, gap_hi (tới bướu bên cạnh)}."""
    pk_, nb = s["peak"], s["peak_n"]
    d_ = math.dist(pk_, nb) or 1
    u = ((pk_[0] - nb[0]) / d_, (pk_[1] - nb[1]) / d_)
    t = (-u[1], u[0])
    W, A, base = s["W"], s["A"], s["base"]
    box = (s["x0"] - W, s["y0"] - W, s["x1"] + W, s["y1"] + W)
    out = {"u": u, "t": t, "tau0": -2 * W, "tau1": 2 * W, "ta": -W, "tb": W, "gap_lo": math.inf, "gap_hi": math.inf}
    cands = []
    for p in paths:
        if p["net"] == s["net"] and p["layer"] == s["layer"] and len(p["pts"]) > 1:
            q = _seg_pts([tuple(x) for x in p["pts"]], max(W / 4, 1e-6))
            cands.append([x for x in q if box[0] <= x[0] <= box[2] and box[1] <= x[1] <= box[3]])
    sm = max(cands, key=len, default=[])
    if not sm:
        return out
    h = [(q[0] - nb[0]) * u[0] + (q[1] - nb[1]) * u[1] for q in sm]
    tau = [(q[0] - pk_[0]) * t[0] + (q[1] - pk_[1]) * t[1] for q in sm]
    k0 = min(range(len(sm)), key=lambda k: math.dist(sm[k], pk_))

    def grow(lim):
        i = j = k0
        while i > 0 and h[i - 1] > lim:
            i -= 1
        while j < len(sm) - 1 and h[j + 1] > lim:
            j += 1
        return i, j
    i, j = grow(base + 0.05 * A)
    a_, b_ = grow(base + 0.9 * A)
    out.update(tau0=min(tau[i:j + 1]), tau1=max(tau[i:j + 1]), ta=min(tau[a_:b_ + 1]), tb=max(tau[a_:b_ + 1]))
    others = [tau[k] for k in range(len(sm)) if (k < i or k > j) and h[k] > base + 0.5 * A]
    out["gap_hi"] = min((x - out["tau1"] for x in others if x > out["tau1"]), default=math.inf)
    out["gap_lo"] = min((out["tau0"] - x for x in others if x < out["tau0"]), default=math.inf)
    return out


class _Pen:
    """Vẽ: toạ độ thế giới (m) -> SVG (mm, y lật). fsz = cỡ chữ (đơn vị SVG)."""

    def __init__(self, fsz):
        self.fsz, self.sw = fsz, fsz / 16
        self.o = []

    @staticmethod
    def p(q):
        return q[0] / MM, -q[1] / MM

    def line(self, a, b, w=None, extra=""):
        (ax, ay), (bx, by) = self.p(a), self.p(b)
        self.o.append(f'<line x1="{ax:.4f}" y1="{ay:.4f}" x2="{bx:.4f}" y2="{by:.4f}" stroke="#000" '
                      f'stroke-width="{(w or self.sw):.4f}"{extra}/>')

    def head(self, tip, frm):
        """Đầu mũi tên đặc, đỉnh ở tip, hướng frm -> tip."""
        (tx, ty), (fx, fy) = self.p(tip), self.p(frm)
        L = math.hypot(tx - fx, ty - fy) or 1
        dx, dy = (tx - fx) / L, (ty - fy) / L
        hl = self.fsz * 0.45
        hw = hl * 0.3
        qx, qy = tx - dx * hl, ty - dy * hl
        self.o.append(f'<path d="M{tx:.4f},{ty:.4f} L{qx - dy * hw:.4f},{qy + dx * hw:.4f} '
                      f'L{qx + dy * hw:.4f},{qy - dx * hw:.4f} z" fill="#000"/>')

    def text(self, q, txt, anchor="middle", bold=False, length=None, prefix=""):
        """Chữ có viền trắng; length (m) -> độ dài đổi đơn vị được (data-m)."""
        from ..cut_board import review_units as U
        x, y = self.p(q)
        el = (f'<text x="{x:.4f}" y="{y + self.fsz * 0.35:.4f}" font-size="{self.fsz:.4f}" text-anchor="{anchor}" '
              f'fill="#000" stroke="#fff" stroke-width="{self.fsz * 0.22:.4f}" paint-order="stroke"'
              + (' font-weight="bold"' if bold else ""))
        if length is not None:
            el += U.attrs(length, prefix) + f">{H.escape(prefix + U.fmt(length))}</text>"
        else:
            el += f">{H.escape(txt)}</text>"
        self.o.append(el)


def _anchor(n):
    """Hướng đặt nhãn (thế giới) -> text-anchor (x màn hình = x thế giới)."""
    return "start" if n[0] > 0.35 else "end" if n[0] < -0.35 else "middle"


def _tips(pen, p0, p1):
    return ",".join(f"{v:.5f}" for v in (*pen.p(p0), *pen.p(p1)))


def _lab_pos(p0, p1, nrm, lab_off, inline_end, fs_w, n_chars):
    """Vị trí + text-anchor của giá trị kích thước. Đường kích thước nằm ngang trên màn hình mà chữ dài hơn đường ->
    chữ nối tiếp sau đầu p1 (phía ngoài); còn lại -> cạnh trung điểm, phía nrm."""
    L = math.dist(p0, p1) or 1e-12
    e = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    if inline_end and abs(e[0]) > 0.7 and 0.55 * fs_w * n_chars > 0.8 * L:
        return _add(p1, e, 0.35 * fs_w), _anchor(e)
    mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
    return _add(mid, nrm, lab_off), _anchor(nrm)


def _lab_box(q, anchor, n_chars, fs_w):
    """2 góc khung chữ (thế giới) để khung ảnh chứa đủ nhãn và để nhãn không chồng nhau (R11: chữ đậm ~0.62 cỡ chữ /
    ký tự; 0.55 hẹp quá -> W / c chồng nhau)."""
    w = 0.62 * fs_w * n_chars
    x0 = q[0] - (0 if anchor == "start" else w if anchor == "end" else w / 2)
    return [(x0, q[1] - 0.5 * fs_w), (x0 + w, q[1] + 0.6 * fs_w)]


def _dim(pen, key, p0, p1, value, exts, lab, outside=None):
    """Kích thước kiểu ISO 129: đường gióng (exts), đường kích thước p0 -> p1, mũi tên 2 đầu chạm đường gióng / mép;
    hẹp -> mũi tên ngoài chỉ vào; giá trị + đơn vị tại lab (vị trí, anchor)."""
    fs_w = pen.fsz * MM
    L = math.dist(p0, p1) or 1e-12
    e = ((p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L)
    pen.o.append(f'<g class="dim" data-dim="{key}" data-tips="{_tips(pen, p0, p1)}">')
    for a, b in exts:
        pen.line(a, b, pen.sw * 0.7, ' class="ext"')
    if outside is None:
        outside = L < 2.6 * 0.45 * fs_w
    if outside:
        t0, t1 = _add(p0, e, -1.6 * fs_w), _add(p1, e, 1.6 * fs_w)
        pen.line(t0, p0)
        pen.line(p0, p1)
        pen.line(t1, p1)
        pen.head(p0, t0)
        pen.head(p1, t1)
    else:
        pen.line(p0, p1)
        pen.head(p0, p1)
        pen.head(p1, p0)
    pen.text(lab[0], "", lab[1], True, length=value, prefix=f"{key} = ")
    pen.o.append("</g>")


def _traces(pen, s, paths, win):
    """Dây thật trong khung (thành viên serpentine đậm, dây kia nhạt) + đường tâm gạch-chấm của dây serpentine."""
    x0, y0, x1, y1 = win

    def hit(pts):                                     # đoạn nào chạm khung (đầu mút có thể ở ngoài)
        return any(min(a[0], b[0]) <= x1 and max(a[0], b[0]) >= x0 and min(a[1], b[1]) <= y1 and max(a[1], b[1]) >= y0
                   for a, b in zip(pts, pts[1:]))
    inside_ = [p for p in paths if p["layer"] == s["layer"] and hit(p["pts"])]
    for p in inside_:
        d = " ".join(f"{a / MM:.4f},{-b / MM:.4f}" for a, b in p["pts"])
        col = C_MEMBER if p["net"] == s["net"] else C_OTHER
        pen.o.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="{p["w"] / MM:.4f}" '
                     f'stroke-linejoin="round" stroke-linecap="butt"/>')
    f_ = pen.fsz
    for p in inside_:
        if p["net"] == s["net"]:
            d = " ".join(f"{a / MM:.4f},{-b / MM:.4f}" for a, b in p["pts"])
            pen.o.append(f'<polyline class="cl" points="{d}" fill="none" stroke="#000" '
                         f'stroke-width="{pen.sw * 0.6:.4f}" stroke-dasharray="{f_ * 0.8:.4f} {f_ * 0.2:.4f} '
                         f'{f_ * 0.08:.4f} {f_ * 0.2:.4f}"/>')


def _hit(b1, b2, pad):
    """2 khung chữ (thế giới) chạm nhau (kể cả khoảng đệm pad)."""
    return not (b1[1][0] + pad <= b2[0][0] or b2[1][0] + pad <= b1[0][0]
                or b1[1][1] + pad <= b2[0][1] or b2[1][1] + pad <= b1[0][1])


def _unclash(w_lab, dims, pk_, u, t_s, W, fs_w, nch):
    """R11: giá trị W / A / G / c không chồng nhau. Lần lượt từng nhãn (A, G, c, W): giữ chỗ mặc định nếu trống, không
    thì thử chỗ khác cạnh chính kích thước đó (W: phía bên kia mũi tên / cao hơn; A / G / c: lùi ra xa theo hướng đặt)."""
    pad = 0.15 * fs_w
    placed = []

    def free(lab):
        b = _lab_box(lab[0], lab[1], nch, fs_w)
        return not any(_hit(b, o, pad) for o in placed), b

    out = []
    for d in dims:
        key, p0, p1, val, exts, (q, anc) = d
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        L = math.dist(q, mid)
        e = ((q[0] - mid[0]) / L, (q[1] - mid[1]) / L) if L > 1e-12 else (0.0, 1.0)
        cands = [(q, anc)] + [(_add(q, e, k * fs_w), anc) for k in (0.8, 1.6, 2.4, 3.2)]
        lab = next((c for c in cands if free(c)[0]), cands[0])
        placed.append(free(lab)[1])
        out.append((key, p0, p1, val, exts, lab))
    w_cands = [w_lab]
    if abs(u[0]) > 0.35:                                     # W ngang: lệch sang 2 bên đuôi mũi tên
        base = _add(pk_, u, W / 2 + 1.9 * fs_w)
        w_cands += [(_add(base, t_s, s_ * fs_w), _anchor(u)) for s_ in (1.2, -1.2, 2.4, -2.4)]
    else:                                                    # W dọc: phía bên kia đuôi mũi tên, rồi cao hơn
        top = _add(pk_, u, W / 2 + 1.3 * fs_w)
        w_cands += [(_add(top, t_s, 0.3 * fs_w), _anchor(t_s))]
        w_cands += [(_add(_add(top, u, k * fs_w), t_s, s_ * 0.3 * fs_w), _anchor((s_ * t_s[0], s_ * t_s[1])))
                    for k in (1.0, 2.0) for s_ in (-1, 1)]
        w_cands += [(_add(pk_, u, W / 2 + 2.3 * fs_w), "middle")]
    w = next((c for c in w_cands if free(c)[0]), w_cands[0])
    return w, out


def _detail_layout(s, bp, fs_w):
    """Bố cục khung Detail với cỡ chữ fs_w (m): -> (dims, w_dim, điểm phải chứa)."""
    W, A, base = s["W"], s["A"], s["base"]
    pk_, nb = s["peak"], s["peak_n"]
    u, t = bp["u"], bp["t"]
    sg = 1 if bp["gap_hi"] >= bp["gap_lo"] else -1          # phía đặt kích thước A: xa bướu bên cạnh
    t_s = (t[0] * sg, t[1] * sg)
    foot = bp["tau1"] if sg > 0 else -bp["tau0"]
    top_end = bp["tb"] if sg > 0 else -bp["ta"]
    gap = bp["gap_hi"] if sg > 0 else bp["gap_lo"]
    eg, ov = 0.1 * W + 0.15 * fs_w, 0.5 * fs_w
    nch = 13                                                 # 'A = 1234.5 mil'

    def at_top(tau):                                         # mép ngoài đỉnh bướu
        return _add(_add(pk_, u, W / 2), t_s, tau)

    def at_base(tau):                                        # mép cùng phía của đường gốc
        return _add(_add(nb, u, base + W / 2), t_s, tau)
    tau_d = foot + min(max(1.5 * W, 1.6 * fs_w), 0.5 * gap)
    a0, a1 = at_base(tau_d), at_top(tau_d)
    ext_a = [(at_top(top_end + eg), at_top(tau_d + ov)), (at_base(foot + min(W, 0.25 * gap)), at_base(tau_d + ov))]
    pts = [a0, a1, at_base(tau_d + ov), at_top(tau_d + ov)]
    dims = []
    lab = _lab_pos(a0, a1, t_s, 0.6 * fs_w, True, fs_w, nch)
    dims.append(("A", a0, a1, A, ext_a, lab))
    # G: khe mép-mép giữa 2 đoạn song song (cặp gần bướu này nhất)
    gps = s.get("gpairs") or ([s["gpair"]] if s.get("gpair") else [])
    if gps and s.get("G") is not None:
        def mid(ab):
            return (sum(q[0] for sg_ in ab for q in sg_) / 4, sum(q[1] for sg_ in ab for q in sg_) / 4)
        a, b = min(gps, key=lambda ab: math.dist(mid(ab), _add(pk_, u, -A / 2)))
        Lb = math.dist(*b) or 1
        ub = ((b[1][0] - b[0][0]) / Lb, (b[1][1] - b[0][1]) / Lb)
        pr = sorted(((q[0] - b[0][0]) * ub[0] + (q[1] - b[0][1]) * ub[1]) for q in a)
        lo, hi = max(pr[0], 0), min(pr[1], Lb)
        qb = _add(b[0], ub, (lo + hi) / 2)
        qa = _proj(qb, *a)
        dg = math.dist(qa, qb) or 1
        g = ((qb[0] - qa[0]) / dg, (qb[1] - qa[1]) / dg)
        g0, g1 = _add(qa, g, W / 2), _add(qb, g, -W / 2)
        nrm = (-u[0], -u[1]) if abs(ub[0] * u[0] + ub[1] * u[1]) > 0.7 else ub
        lab = _lab_pos(g0, g1, nrm, 0.8 * fs_w, False, fs_w, nch)
        dims.append(("G", g0, g1, s["G"], (), lab))
        pts += [g0, g1]
    # c: cạnh vát 45° (dài theo đường tâm), kích thước song song cạnh vát, ra phía ngoài bướu; ưu tiên cạnh vát phía
    # ngược kích thước A, gần đỉnh (tránh chồng A / G)
    if s.get("chams"):
        cand = s["short"] or s["chams"]

        def score(c_):
            mc_ = ((c_[0][0] + c_[1][0]) / 2, (c_[0][1] + c_[1][1]) / 2)
            tau_ = (mc_[0] - pk_[0]) * t_s[0] + (mc_[1] - pk_[1]) * t_s[1]
            h_ = (mc_[0] - pk_[0]) * u[0] + (mc_[1] - pk_[1]) * u[1]
            return (tau_ > 0, math.dist(mc_, pk_) - 0.5 * h_)
        a, b, Lc = min(cand, key=score)
        e = ((b[0] - a[0]) / (Lc or 1), (b[1] - a[1]) / (Lc or 1))
        n = (-e[1], e[0])
        cen = _add(pk_, u, -A / 2)
        mc = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if (mc[0] - cen[0]) * n[0] + (mc[1] - cen[1]) * n[1] < 0:
            n = (-n[0], -n[1])
        off = W / 2 + max(1.0 * W, 1.0 * fs_w)
        c0, c1 = _add(a, n, off), _add(b, n, off)
        ext_c = [(_add(a, n, W / 2 + eg), _add(a, n, off + ov)), (_add(b, n, W / 2 + eg), _add(b, n, off + ov))]
        lab = _lab_pos(c0, c1, n, 0.7 * fs_w, False, fs_w, nch)
        dims.append(("c", c0, c1, Lc, ext_c, lab))
        pts += [c0, c1, _add(c0, n, ov), _add(c1, n, ov)]
    # W: mũi tên ngoài chỉ vào, trên đỉnh bướu
    w_hi, w_lo = _add(pk_, u, W / 2), _add(pk_, u, -W / 2)
    if abs(u[0]) > 0.35:                                     # chữ W nối sau đuôi mũi tên ngoài
        w_lab = (_add(pk_, u, W / 2 + 1.9 * fs_w), _anchor(u))
    else:                                                    # chữ W cạnh đuôi mũi tên
        w_lab = (_add(_add(pk_, u, W / 2 + 1.3 * fs_w), t_s, -0.3 * fs_w), _anchor((-t_s[0], -t_s[1])))
    pts += [_add(pk_, u, W / 2 + 1.7 * fs_w), _add(pk_, u, -W / 2 - 1.7 * fs_w)]
    w_lab, dims = _unclash(w_lab, dims, pk_, u, t_s, W, fs_w, nch)
    for key, p0, p1, val, exts, (q, anc) in dims + [("W", w_lo, w_hi, W, (), w_lab)]:
        pts += _lab_box(q, anc, nch, fs_w)
    for tau in (bp["tau0"] - W, bp["tau1"] + W):             # bướu + đường gốc + dây kia
        pts += [_add(_add(nb, u, -W), t, tau), _add(_add(pk_, u, W), t, tau)]
    return dims, (w_lo, w_hi, w_lab), pts


def _detail(s, paths, bp, px):
    """Khung 'Detail A': một bướu phóng to + kích thước W / A / G / c; cỡ chữ ~11 px. -> (pen, win, w, h) (mm)."""
    W = s["W"]
    fs_w = max(bp["tau1"] - bp["tau0"] + 4 * W, s["A"] + s["base"] + 3 * W) / 14
    for _ in range(4):                                        # cỡ chữ theo bề rộng khung (khung phụ thuộc cỡ chữ)
        dims, wd, pts = _detail_layout(s, bp, fs_w)
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        mg = 0.6 * fs_w
        win = (min(xs) - mg, min(ys) - mg, max(xs) + mg, max(ys) + mg + 1.4 * fs_w)   # + dòng tiêu đề
        want = (win[2] - win[0]) * 11.0 / px
        if abs(want - fs_w) <= 0.03 * fs_w:
            break
        fs_w = want
    pen = _Pen(fs_w / MM)
    _traces(pen, s, paths, win)
    for key, p0, p1, val, exts, lab in dims:
        _dim(pen, key, p0, p1, val, exts, lab)
    w_lo, w_hi, (q, anc) = wd
    u = bp["u"]
    pen.o.append(f'<g class="dim" data-dim="W" data-tips="{_tips(pen, w_lo, w_hi)}">')
    for tip, d_ in ((w_hi, u), (w_lo, (-u[0], -u[1]))):
        tail = _add(tip, d_, 1.6 * fs_w)
        pen.line(tail, tip)
        pen.head(tip, tail)
    pen.text(q, "", anc, True, length=W, prefix="W = ")
    pen.o.append("</g>")
    return pen, win, (win[2] - win[0]) / MM, (win[3] - win[1]) / MM


def svg(s, paths, px=380):
    """2.11.2 (R6–R9): ảnh tổng của cặp (vòng tròn gạch 'A' quanh bướu được đo, không số) + khung 'Detail A (xN)'
    phóng to bướu đó, kích thước kiểu bản vẽ cơ khí: đường gióng ⟂ cạnh đo, đường kích thước mũi tên 2 đầu, giá trị +
    đơn vị (đổi mil / µm / mm), W mũi tên ngoài chỉ vào, A / G mép-mép, c song song cạnh vát, đường tâm gạch-chấm.
    -> html (2 svg + dòng W / H + các dòng so sánh)."""
    from ..cut_board import review_units as U
    x0, y0, x1, y1 = s["x0"], s["y0"], s["x1"], s["y1"]
    side = max(x1 - x0 + 0.8 * MM, y1 - y0 + 0.8 * MM, 3.0 * MM)     # ảnh tổng: cặp + ngữ cảnh (>= 3 mm)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0, x1, y0, y1 = cx - side / 2, cx + side / 2, cy - side / 2, cy + side / 2
    S = side / MM
    bp = _bump(s, paths)
    pen = _Pen(S / 30)
    pen.o.append(f'<svg xmlns="http://www.w3.org/2000/svg" class="serp-ov" viewBox="{x0 / MM:.4f} {-y1 / MM:.4f} '
                 f'{S:.4f} {S:.4f}" width="{px}" height="{px}" style="background:#fff;border:1px solid #ccc">')
    _traces(pen, s, paths, (x0, y0, x1, y1))
    W, A, u, t = s["W"], s["A"], bp["u"], bp["t"]
    cen = _add(_add(s["peak"], u, -A / 2), t, (bp["tau0"] + bp["tau1"]) / 2)
    r = max((bp["tau1"] - bp["tau0"]) / 2, A / 2) + 1.5 * W
    ccx, ccy = pen.p(cen)
    pen.o.append(f'<circle class="det" cx="{ccx:.4f}" cy="{ccy:.4f}" r="{r / MM:.4f}" fill="none" stroke="#000" '
                 f'stroke-width="{pen.sw * 1.2:.4f}" stroke-dasharray="{pen.fsz * 0.4:.4f} {pen.fsz * 0.3:.4f}"/>')
    pen.text(_add(cen, u, r + 0.9 * pen.fsz * MM), "A", bold=True)
    pen.o.append(f'<rect x="{x0 / MM + S * 0.02:.4f}" y="{-y1 / MM + S * 0.02:.4f}" width="{S * 0.6:.4f}" '
                 f'height="{pen.fsz * 1.5:.4f}" fill="#fff" opacity="0.9"/><text x="{x0 / MM + S * 0.03:.4f}" '
                 f'y="{-y1 / MM + S * 0.02 + pen.fsz * 1.1:.4f}" font-size="{pen.fsz:.4f}" font-weight="bold" '
                 f'fill="#000">{H.escape(s["layer"])} – {H.escape(s["net"].rstrip("*"))}</text>')
    L = 0.5 if S > 1.5 else 0.2
    bx, by = x0 / MM + S * 0.05, -y0 / MM - S * 0.05
    pen.o.append(f'<line class="scale" x1="{bx:.4f}" y1="{by:.4f}" x2="{bx + L:.4f}" y2="{by:.4f}" stroke="#000" '
                 f'stroke-width="{S / 80:.4f}"/><text x="{bx:.4f}" y="{by - S / 50:.4f}" font-size="{S / 25:.4f}" '
                 f'fill="#000"{U.attrs(L * MM)}>{U.fmt(L * MM)}</text></svg>')
    dpen, win, w_, h_ = _detail(s, paths, bp, px)
    N = S / w_
    mag = f"{N:.0f}" if N >= 2 else f"{N:.1f}"
    hpx = px * h_ / w_
    f_ = dpen.fsz
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" class="serp-det" viewBox="{win[0] / MM:.4f} {-win[3] / MM:.4f} '
            f'{w_:.4f} {h_:.4f}" width="{px}" height="{hpx:.0f}" style="background:#fff;margin-top:4px">'
            f'<rect x="{win[0] / MM + f_ * 0.1:.4f}" y="{-win[3] / MM + f_ * 0.1:.4f}" width="{w_ - f_ * 0.2:.4f}" '
            f'height="{h_ - f_ * 0.2:.4f}" fill="none" stroke="#000" stroke-width="{dpen.sw:.4f}" '
            f'stroke-dasharray="{f_ * 0.6:.4f} {f_ * 0.4:.4f}"/>')
    title = (f'<text x="{win[2] / MM - f_ * 0.4:.4f}" y="{-win[3] / MM + f_ * 1.2:.4f}" font-size="{f_:.4f}" '
             f'font-weight="bold" text-anchor="end" fill="#000" stroke="#fff" stroke-width="{f_ * 0.25:.4f}" '
             f'paint-order="stroke">Detail A (x{mag})</text>')
    ok, nok = "<b class='okk'>OK</b>", "<b class='nok'>NOT OK</b>"
    lines = "".join(f"<div>{U.wrap(H.escape(t_))} → {ok if good else nok}</div>" for t_, good in compare_rows(s))
    return ("".join(pen.o) + head + "".join(dpen.o) + title + "</svg>"
            + f"<div class='meas'><div>W = {U.span(W)}, H = {U.span(s['H'])}</div>{lines}</div>")
