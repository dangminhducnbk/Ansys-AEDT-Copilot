"""Hình học 2D thuần (đơn vị mét), không phụ thuộc PyEDB (contract: core-geometry.md).

Chuyển nguyên văn từ cut_board/geometry.py (kết quả giống hệt). Không kiểm tra đầu vào mỗi lần gọi: hot path."""
import math


def point_seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _cross(ax, ay, bx, by, cx, cy):
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def seg_seg_dist(a, b):
    """a, b = (x0, y0, x1, y1)."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    d1, d2 = _cross(ax0, ay0, ax1, ay1, bx0, by0), _cross(ax0, ay0, ax1, ay1, bx1, by1)
    d3, d4 = _cross(bx0, by0, bx1, by1, ax0, ay0), _cross(bx0, by0, bx1, by1, ax1, ay1)
    if d1 * d2 < 0 and d3 * d4 < 0:
        return 0.0
    return min(point_seg_dist(ax0, ay0, *b), point_seg_dist(ax1, ay1, *b),
               point_seg_dist(bx0, by0, *a), point_seg_dist(bx1, by1, *a))


def point_in_poly(x, y, pts):
    inside = False
    n = len(pts)
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-30) + xi:
            inside = not inside
        j = i
    return inside


def poly_area(pts):
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2


def bbox_of(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def edges(pts):
    return [(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]) for i in range(len(pts))]
