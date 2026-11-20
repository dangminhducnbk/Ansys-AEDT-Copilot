"""Đọc điểm đường bao của primitive EDB (contract: core-geometry.md). Chuyển nguyên văn từ cut_board/geometry.py."""


def prim_points(p):
    """Danh sách điểm (m) của đường bao primitive (polygon/rectangle...). Lùi về bbox nếu không đọc được."""
    for getter in (
        lambda: p.polygon_data.points,
        lambda: [list(q) for q in zip(*p.points())],
        lambda: [[q.X.ToDouble(), q.Y.ToDouble()] for q in p.polygon_data._edb_object.Points],
    ):
        try:
            pts = getter()
            pts = [(float(a), float(b)) for a, b in pts if abs(float(b)) < 1e3]
            if len(pts) >= 3:
                return pts
        except Exception:
            pass
    b = p.bbox
    return [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]
