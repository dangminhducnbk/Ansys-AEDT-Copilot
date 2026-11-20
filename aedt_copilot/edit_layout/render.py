"""Ảnh trước / sau cho từng lớp bị sửa (PIL, không cần matplotlib)."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely import contains_xy
from shapely.geometry import box

PALETTE = [(214, 39, 40), (31, 119, 180), (44, 160, 44), (148, 103, 189), (255, 127, 14), (23, 190, 207),
           (140, 86, 75), (227, 119, 194)]
OTHER = (205, 205, 205)
BG = (255, 255, 255)


def _font(size):
    for f in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default()


GND_COLOR = (31, 119, 180)


def net_colors(nets):
    """GND/VSS luôn xanh dương; net khác lấy palette còn lại (không bao giờ tô GND màu đỏ)."""
    rest = [c for c in PALETTE if c != GND_COLOR]
    col, k = {}, 0
    for n in nets:
        if "GND" in n.upper() or "VSS" in n.upper():
            col[n] = GND_COLOR
        else:
            col[n] = rest[k % len(rest)]
            k += 1
    return col


def draw_layer(R, L, nets, view, path, title, new_vias=(), px=900):
    """view = (x0, y0, x1, y1) mm. nets: net tô màu (theo thứ tự PALETTE)."""
    x0, y0, x1, y1 = view
    w = px
    h = max(200, int(px * (y1 - y0) / max(x1 - x0, 1e-6)))
    sx = (x1 - x0) / w
    xs = x0 + (np.arange(w) + 0.5) * sx
    ys = y1 - (np.arange(h) + 0.5) * (y1 - y0) / h
    X, Y = np.meshgrid(xs, ys)
    img = np.full((h, w, 3), BG, dtype=np.uint8)
    win = box(*view)
    col = net_colors(nets)
    for n, t, g, i in R.LAY[L]:
        if n in col or not g.intersects(win):
            continue
        img[contains_xy(g, X, Y)] = OTHER
    for n in nets:
        g = R.netgeom(L, n)
        if g.is_empty or not g.intersects(win):
            continue
        img[contains_xy(g, X, Y)] = col[n]
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)

    def P(x, y):
        return (x - x0) / sx, (y1 - y) / ((y1 - y0) / h)

    for v in R.inst:
        if not R.on_layer(v, L) or not (x0 <= v["x"] <= x1 and y0 <= v["y"] <= y1):
            continue
        r = max(2, (R.padr(v["pd"], L) or 0.12) / sx)
        cx, cy = P(v["x"], v["y"])
        fill = col.get(v["net"], (120, 120, 120))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=(0, 0, 0))
    for x, y in new_vias:
        if x0 <= x <= x1 and y0 <= y <= y1:
            cx, cy = P(x, y)
            d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], outline=(255, 215, 0), width=3)
    f = _font(16)
    d.rectangle([0, 0, w, 24], fill=(255, 255, 255))
    d.text((6, 3), title, fill=(0, 0, 0), font=f)
    # chú thích màu
    yy = 28
    for n, c in col.items():
        d.rectangle([6, yy, 20, yy + 12], fill=c, outline=(0, 0, 0))
        d.text((26, yy - 2), n, fill=(0, 0, 0), font=_font(13))
        yy += 16
    # thước 1 mm
    bar = 1.0 / sx
    d.line([w - 20 - bar, h - 16, w - 20, h - 16], fill=(0, 0, 0), width=3)
    d.text((w - 20 - bar, h - 34), "1 mm", fill=(0, 0, 0), font=_font(13))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return path
