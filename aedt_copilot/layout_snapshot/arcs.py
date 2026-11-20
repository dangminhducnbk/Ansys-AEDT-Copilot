"""Điểm EDB (có điểm đánh dấu cung tròn) -> dãy điểm dây cung (pure, feature 023).

Mã hoá EDB: điểm có Y > 1e300 là đánh dấu cung; X = chiều cao cung giữa điểm trước và điểm sau.
Dấu pháp tuyến = -1 (đã so với ArcData.GetMidPoint trên board1, spike 023).
"""
import math

from ..core.errors import CopilotInputError

BIGY = 1e300


def is_marker(p):
    return p[1] > BIGY


def arc_points(a, b, h, tol):
    """Cung từ a tới b, chiều cao h -> [a, ..., b] với sai số dây cung <= tol."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    c = math.hypot(dx, dy)
    if c == 0 or h == 0:
        return [a, b]
    nx, ny = -dy / c, dx / c                                   # pháp tuyến (dấu -1 so với trái)
    r = (c * c / 4 + h * h) / (2 * abs(h))
    mx, my = (a[0] + b[0]) / 2 + nx * h, (a[1] + b[1]) / 2 + ny * h          # điểm giữa cung
    s = h / abs(h)
    ox, oy = mx - nx * s * r, my - ny * s * r                  # tâm
    a0 = math.atan2(a[1] - oy, a[0] - ox)
    a1 = math.atan2(b[1] - oy, b[0] - ox)
    am = math.atan2(my - oy, mx - ox)
    two = 2 * math.pi
    ccw = (a1 - a0) % two
    sweep = ccw if (am - a0) % two <= ccw else -(two - ccw)
    step = 2 * math.acos(max(-1.0, 1 - tol / r)) if r > tol else math.pi / 2
    n = max(1, int(math.ceil(abs(sweep) / step)))
    pts = [(ox + r * math.cos(a0 + sweep * k / n), oy + r * math.sin(a0 + sweep * k / n)) for k in range(1, n)]
    return [a] + pts + [b]


def to_coords(raw, tol_m):
    """raw: [(x, y)] của PolygonData.Points (vòng kín, có điểm đánh dấu cung) -> [(x, y)] không còn cung."""
    if not isinstance(tol_m, (int, float)) or tol_m <= 0:
        raise CopilotInputError("tol_m", "> 0 (m)", tol_m)
    pts = [(float(x), float(y)) for x, y in raw]
    n = len(pts)
    out = []
    for i, p in enumerate(pts):
        if is_marker(p):
            continue
        out.append(p)
        if n > 1 and is_marker(pts[(i + 1) % n]):
            j = (i + 2) % n
            while is_marker(pts[j]) and j != i:                 # phòng 2 đánh dấu liền nhau
                j = (j + 1) % n
            out += arc_points(p, pts[j], pts[(i + 1) % n][0], tol_m)[1:-1]
    return out
