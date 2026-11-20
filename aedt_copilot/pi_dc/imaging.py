"""Dùng chung cho các skill PI-DC: đọc ảnh SIwave (mọi độ phân giải), thang màu, J theo pixel, hiệu chuẩn mm,
ảnh kiểu báo cáo (thang màu bên trái, layout zoom vào giữa khung, khung đỏ / vòng tròn có nhãn).

Bố cục ảnh SIwave tỉ lệ theo chiều cao H (chuẩn 1000 px): S = H / 1000. Thang màu: cột x = 50 S,
nhãn x 104..400 S, tâm nhãn y_k = (20 + k 952/14) S; vùng board x >= 0.45 H (sau nhãn).
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import colorbar_ocr

Image.MAX_IMAGE_PIXELS = None
RED = (220, 0, 0)
CANVAS_H = 1400
CANVAS_AREA_W = int(CANVAS_H * 1.6)


def font(sz):
    for f in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def open_rgb(p) -> Image.Image:
    return Image.open(p).convert("RGB")


def scale(im: Image.Image) -> float:
    return im.size[1] / 1000.0


def bar_end(im: Image.Image) -> int:
    return int(0.45 * im.size[1])


def read_colorbar(im: Image.Image) -> dict:
    """OCR thang màu ở độ phân giải gốc (template theo chiều cao ảnh, xem colorbar_ocr)."""
    return colorbar_ocr.read(im)


def band_colors(im: Image.Image) -> np.ndarray:
    """14 màu dải, index 0 = dải CAO nhất (đỉnh thang màu)."""
    S = scale(im)
    a = np.asarray(im)
    return np.array([a[int((20 + (k + 0.5) * 952 / 14) * S), int(50 * S)] for k in range(14)], dtype=np.int32)


def copper_mask(a: np.ndarray, x0: int) -> np.ndarray:
    sub = a[:, x0:]
    return (sub.max(2).astype(np.int16) - sub.min(2)) > 60


def jmap(im: Image.Image, vmin: float, vmax: float):
    """-> (J [float32, NaN = không phải đồng có dòng], x0 offset). Mỗi pixel = giữa dải màu gần nhất (khoảng cách < 60)."""
    a = np.asarray(im)
    x0 = bar_end(im)
    m = copper_mask(a, x0)
    bands = band_colors(im)
    mids = vmax - (np.arange(14) + 0.5) * (vmax - vmin) / 14
    J = np.full(m.shape, np.nan, np.float32)
    ys, xs = np.nonzero(m)
    for i in range(0, len(ys), 1_000_000):
        px = a[ys[i:i + 1_000_000], xs[i:i + 1_000_000] + x0].astype(np.int32)
        d2 = ((px[:, None, :] - bands[None]) ** 2).sum(2)
        k = d2.argmin(1)
        ok = d2[np.arange(len(k)), k] < 3600
        J[ys[i:i + 1_000_000][ok], xs[i:i + 1_000_000][ok]] = mids[k[ok]]
    return J, x0


def colored_extent(im: Image.Image):
    a = np.asarray(im)
    x0 = bar_end(im)
    ys, xs = np.nonzero(copper_mask(a, x0))
    if len(xs) == 0:
        return None
    return xs.min() + x0, ys.min(), xs.max() + x0, ys.max()


class Calib:
    """mm <-> px cho mọi ảnh cùng cỡ của một lần export (SIwave vẽ cùng khung cho mọi lớp/job).
    Tham chiếu: vùng màu của ảnh ALL_NETS lớp plane (rộng nhất) = khung outline board."""

    def __init__(self, ref_png: Path, outline_file: Path):
        im = open_rgb(ref_png)
        self.size = im.size
        px0, py0, px1, py1 = colored_extent(im)
        pts = []
        for ln in open(outline_file, encoding="latin-1"):
            p = ln.split()
            try:
                pts.append((float(p[0]), float(p[1])))
            except (ValueError, IndexError):
                pass
        P = np.array(pts) * 1e3
        self.bx0, self.bx1, self.by0, self.by1 = P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()
        self.px0, self.py0, self.px1, self.py1 = px0, py0, px1, py1
        self.sx = (px1 - px0) / (self.bx1 - self.bx0)
        self.sy = (py1 - py0) / (self.by1 - self.by0)
        self.ppmm = (self.sx + self.sy) / 2

    def to_px(self, x, y, f=1.0):
        """mm -> px trên ảnh cỡ gốc nhân f (f = hệ số thu nhỏ khi phân tích)."""
        return (self.px0 + (x - self.bx0) * self.sx) * f, (self.py1 - (y - self.by0) * self.sy) * f

    def to_mm(self, X, Y, f=1.0):
        X, Y = X / f, Y / f
        return self.bx0 + (X - self.px0) / self.sx, self.by0 + (self.py1 - Y) / self.sy


def best_ref(ctx) -> Path:
    """Ảnh ALL_NETS CUR có vùng màu lớn nhất (lớp plane) để hiệu chuẩn."""
    best, area = None, -1
    for lay in ctx.metals:
        p = ctx.cur_png("ALL_NETS", "CUR", lay)
        if not p:
            continue
        im = open_rgb(p)
        im = im.reduce(8) if im.size[1] > 2000 else im
        e = colored_extent(im)
        if e and (e[2] - e[0]) * (e[3] - e[1]) > area:
            best, area = p, (e[2] - e[0]) * (e[3] - e[1])
    if best is None:
        raise RuntimeError("Không có ảnh ALL_NETS CUR để hiệu chuẩn")
    return best


# ------------------------------------------------------------------ report-style canvas
class Canvas:
    """Thang màu (gốc) bên trái + layout cắt theo `box` (px ảnh gốc) phóng vừa khung 2800x1400 (tỉ lệ 2:1)."""

    def __init__(self, im: Image.Image, box, thicken: bool = False):
        H = im.size[1]
        S = scale(im)
        a = np.asarray(im.crop((0, 0, bar_end(im), H)))
        cols = np.nonzero((a.min(2) < 110).any(0))[0]
        leg = im.crop((0, 0, int(cols.max()) + int(10 * S), H))
        self.leg = leg.resize((max(1, int(leg.width * CANVAS_H / H)), CANVAS_H), Image.LANCZOS)
        bw, bh = box[2] - box[0], box[3] - box[1]
        pad = Image.new("RGB", (bw, bh), "white")
        ix0, iy0, ix1, iy1 = max(0, box[0]), max(0, box[1]), min(im.size[0], box[2]), min(H, box[3])
        pad.paste(im.crop((ix0, iy0, ix1, iy1)), (ix0 - box[0], iy0 - box[1]))
        self.k = min(CANVAS_AREA_W / bw, (CANVAS_H - 20) / bh)
        if thicken and self.k < 0.7:                    # nét mảnh (marker via) -> làm dày trước khi thu nhỏ để không bị mờ
            from PIL import ImageFilter
            pad = pad.filter(ImageFilter.MinFilter(int(round(1 / self.k)) | 1))
        crop = pad.resize((max(1, int(bw * self.k)), max(1, int(bh * self.k))),
                          Image.LANCZOS if self.k < 1 else Image.NEAREST)
        self.box = box
        self.ox = self.leg.width + 30 + (CANVAS_AREA_W - crop.width) // 2
        self.oy = (CANVAS_H - crop.height) // 2
        self.img = Image.new("RGB", (self.leg.width + 30 + CANVAS_AREA_W, CANVAS_H), "white")
        self.img.paste(self.leg, (0, 0))
        self.img.paste(crop, (self.ox, self.oy))
        self.d = ImageDraw.Draw(self.img)
        self.labels = []

    def P(self, X, Y):
        return self.ox + (X - self.box[0]) * self.k, self.oy + (Y - self.box[1]) * self.k

    def _free(self, x, y, w, h):
        return not any(x < b[2] and x + w > b[0] and y < b[3] and y + h > b[1] for b in self.labels)

    def label(self, x, y, text, f, prefer_right=True, color=RED):
        w = self.d.textlength(text, font=f)
        h = f.size + 6
        cx = x if prefer_right else x - w
        cx = min(max(2, cx), self.img.width - w - 2)
        while not self._free(cx, y, w, h):
            y += h
        self.d.rectangle([cx - 3, y - 2, cx + w + 3, y + h - 2], fill="white",
                         outline=None if color == RED else color, width=1)
        self.d.text((cx, y), text, fill=color, font=f)
        self.labels.append((cx - 3, y - 2, cx + w + 3, y + h - 2))
        return cx, y

    def rect(self, bx, text):
        x0, y0 = self.P(bx[0], bx[1])
        x1, y1 = self.P(bx[2], bx[3])
        self.d.rectangle([x0, y0, x1, y1], outline=RED, width=4)
        f = font(26)
        w = self.d.textlength(text, font=f)
        self.label(x1 + 6 if x1 + 6 + w < self.img.width else x0 - 6 - w, y0, text, f)

    def rect_info(self, bx, text, col=(110, 110, 110)):
        """Khung xám nét đứt + nhãn xám (thông tin, không phải vi phạm)."""
        x0, y0 = self.P(bx[0], bx[1])
        x1, y1 = self.P(bx[2], bx[3])
        for (a, b), (c, d) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            L = max(1.0, math.hypot(c - a, d - b))
            for t in range(0, int(L), 16):
                t1 = min(L, t + 9)
                self.d.line([(a + (c - a) * t / L, b + (d - b) * t / L), (a + (c - a) * t1 / L, b + (d - b) * t1 / L)],
                            fill=col, width=3)
        f = font(22)
        w = self.d.textlength(text, font=f)
        cx = x1 + 6 if x1 + 6 + w < self.img.width else x0 - 6 - w
        cx = min(max(2, cx), self.img.width - w - 2)
        y = y1 + 4
        while not self._free(cx, y, w, f.size + 6):
            y += f.size + 6
        self.d.rectangle([cx - 3, y - 2, cx + w + 3, y + f.size + 4], fill="white")
        self.d.text((cx, y), text, fill=col, font=f)
        self.labels.append((cx - 3, y - 2, cx + w + 3, y + f.size + 4))

    def circles(self, pts, r=12, gap=30, color=RED, halo=False):
        """pts = [(X, Y, label)] px ảnh gốc. Cụm (cách nhau < 80 px trên khung) -> nhãn xếp cột cạnh cụm.
        color/halo: màu vòng + mũi tên (+ viền trắng) để nổi trên nền đỏ (ảnh voltage)."""
        f = font(22)
        Pp = [(*self.P(X, Y), lab) for X, Y, lab in pts]
        for x, y, _ in Pp:
            if halo:
                self.d.ellipse([x - r - 2, y - r - 2, x + r + 2, y + r + 2], outline="white", width=7)
            self.d.ellipse([x - r, y - r, x + r, y + r], outline=color, width=3)
        used, groups = set(), []
        for i in range(len(Pp)):
            if i in used:
                continue
            g, todo = [i], [i]
            used.add(i)
            while todo:
                j = todo.pop()
                for k in range(len(Pp)):
                    if k not in used and abs(Pp[k][0] - Pp[j][0]) < 80 and abs(Pp[k][1] - Pp[j][1]) < 80:
                        used.add(k); g.append(k); todo.append(k)
            groups.append([Pp[k] for k in g])
        for g in groups:
            tw = max(self.d.textlength(p[2], font=f) for p in g)
            right = max(p[0] for p in g) + r + 50
            cx = right if right + tw < self.img.width - 4 else min(p[0] for p in g) - r - 50 - tw
            ty = min(p[1] for p in g) - 12 - (len(g) - 1) * gap / 2
            for x, y, lab in sorted(g, key=lambda p: (p[1], p[0])):
                lx, ly = self.label(cx, ty, lab, f, color=color)
                seg = [(x + (r if lx > x else -r), y), (lx - 4 if lx > x else lx + tw + 4, ly + 12)]
                if halo:
                    self.d.line(seg, fill="white", width=6)
                self.d.line(seg, fill=color, width=2 if not halo else 3)
                ty = ly + gap

    def title(self, text):
        self.d.text((self.leg.width + 30, 2), text, fill=(90, 90, 90), font=font(18))

    def save(self, p):
        self.img.save(p, optimize=True)


def main_box(im: Image.Image, extra=()):
    """Khung chứa phần lớn structure: 0.5..99.5 % pixel màu + lề 4 %, gộp thêm các khung `extra`."""
    a = np.asarray(im)
    x0 = bar_end(im)
    ys, xs = np.nonzero(copper_mask(a, x0))
    if len(xs) < 20:
        return (x0, 0, im.size[0], im.size[1])
    xs = xs + x0
    lx, hx = np.percentile(xs, [0.5, 99.5]); ly, hy = np.percentile(ys, [0.5, 99.5])
    for e in extra:
        lx, ly, hx, hy = min(lx, e[0]), min(ly, e[1]), max(hx, e[2]), max(hy, e[3])
    mx, my = 0.04 * (hx - lx) + 8, 0.04 * (hy - ly) + 8
    return (int(max(x0, lx - mx)), int(max(0, ly - my)), int(min(im.size[0], math.ceil(hx + mx))),
            int(min(im.size[1], math.ceil(hy + my))))


def snap(im_arr: np.ndarray, X, Y, rad):
    """Dời vị trí via dự đoán về tâm marker màu gần nhất (o / x của SIwave) trong bán kính rad px."""
    from scipy import ndimage
    x0, y0 = int(max(0, X - rad)), int(max(0, Y - rad))
    sub = im_arr[y0:int(Y + rad) + 1, x0:int(X + rad) + 1]
    m = (sub.max(2).astype(np.int16) - sub.min(2)) > 60
    if not m.any():
        return X, Y
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    best, bd = (X, Y), 1e18
    for i in range(1, n + 1):
        yy, xx = np.nonzero(lab == i)
        cx, cy = xx.mean() + x0, yy.mean() + y0
        dd = (cx - X) ** 2 + (cy - Y) ** 2
        if dd < bd:
            best, bd = (cx, cy), dd
    return best
