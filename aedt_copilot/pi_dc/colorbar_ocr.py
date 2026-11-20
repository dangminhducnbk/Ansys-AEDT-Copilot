"""Đọc nhãn thang màu ảnh DC report SIwave không cần OCR engine (khớp template glyph).

Bố cục tỉ lệ theo chiều cao ảnh H (S = H/1000): nhãn x 104..400 S, tâm nhãn đo từ ảnh (15 dòng chữ),
crop +-16 S, ink gray < 110. Template riêng cho mỗi chiều cao ảnh: data/siwave_colorbar_glyphs_h<H>.npz
(h1000 = mặc định SIwave). Thiếu template cho H -> calibrate_from_pairs() từ cặp ảnh cùng job ở 1000 px và H px.
Tự kiểm: đủ 15 nhãn và tuyến tính trong 0.5 %; sai -> không dùng ảnh (PENDING).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
DATA = Path(__file__).with_name("data")
LBL_X0, LBL_X1 = 104, 400
Y0, Y1, NLAB = 20, 972, 15
HALF = 16
INK = 110
GAP_STOP = 6
GW, GH = 14, 22


def label_y(k: int) -> int:
    return int(round(Y0 + k * (Y1 - Y0) / 14))


def _gray(img) -> np.ndarray:
    im = img if isinstance(img, Image.Image) else Image.open(img)
    return np.asarray(im.convert("L")).astype(np.int16)


def label_rows(gray: np.ndarray, S: float) -> list[int] | None:
    """Tâm 15 dòng nhãn đo từ ảnh."""
    rows = np.nonzero((gray[:, int(LBL_X0 * S):int(LBL_X1 * S)] < INK).any(axis=1))[0]
    if len(rows) == 0:
        return None
    runs, s, p = [], rows[0], rows[0]
    for r in rows[1:]:
        if r > p + max(1, int(S)):
            runs.append((s, p))
            s = r
        p = r
    runs.append((s, p))
    runs = [r for r in runs if r[1] - r[0] >= 4 * S]
    return [int((a + b) // 2) for a, b in runs] if len(runs) == NLAB else None


def segment(gray: np.ndarray, y: int, S: float = 1.0) -> list[np.ndarray]:
    """Glyph (GH x GW, 0..1) của dòng nhãn tâm y, trái -> phải, dừng ở khoảng trắng trước đơn vị."""
    h = int(round(HALF * S))
    crop = gray[max(0, y - h): y + h + 1, int(LBL_X0 * S):int(LBL_X1 * S)] < INK
    cols = crop.any(axis=0)
    glyphs, x, n, last_end = [], 0, crop.shape[1], None
    gap = GAP_STOP * S
    while x < n:
        if not cols[x]:
            x += 1
            continue
        if last_end is not None and x - last_end > gap:
            break
        s = x
        while x < n and cols[x]:
            x += 1
        g = crop[:, s:x].astype(np.uint8) * 255          # giữ nguyên chiều cao -> giữ vị trí dọc ('.' khác '-')
        glyphs.append(np.asarray(Image.fromarray(g).resize((GW, GH), Image.BILINEAR), dtype=np.float32) / 255.0)
        last_end = x
    return glyphs


def _rows(gray, S):
    if S == 1:                                   # template h1000 hiệu chuẩn ở vị trí cố định
        return [label_y(k) for k in range(NLAB)]
    return label_rows(gray, S)                   # template khác: tâm dòng đo từ ảnh (cả lúc hiệu chuẩn)


def npz_for(height: int) -> Path:
    return DATA / f"siwave_colorbar_glyphs_h{height}.npz"


class Reader:
    def __init__(self, npz):
        d = np.load(npz)
        self.chars = [str(c) for c in d["chars"]]
        self.tpl = d["templates"].reshape(len(self.chars), -1)

    def text(self, gray, y, S=1.0) -> str:
        gl = segment(gray, y, S)
        if not gl:
            return ""
        G = np.stack([g.ravel() for g in gl])
        d = ((G[:, None, :] - self.tpl[None, :, :]) ** 2).sum(axis=2)
        return "".join(self.chars[i] for i in d.argmin(axis=1))

    def read_colorbar(self, img) -> dict:
        """-> {vmax, vmin, labels, texts, ok, err}. ok = 15 nhãn đọc được và tuyến tính trong 0.5 %."""
        gray = _gray(img)
        S = gray.shape[0] / 1000.0
        ys = _rows(gray, S)
        res = {"texts": [], "labels": [], "ok": False, "err": None, "vmax": None, "vmin": None}
        if not ys:
            res["err"] = "label rows"
            return res
        texts = [self.text(gray, y, S) for y in ys]
        vals = [float(t) if re.fullmatch(r"[+-]?\d+(\.\d+)?(E[+-]\d+)?", t) else None for t in texts]
        res.update(texts=texts, labels=vals)
        if any(v is None for v in vals):
            res["err"] = "parse"
            return res
        vmax, vmin = vals[0], vals[-1]
        res.update(vmax=vmax, vmin=vmin)
        span = vmax - vmin
        if span <= 0:
            res["ok"] = span == 0
            res["err"] = None if span == 0 else "span"
            return res
        dev = max(abs(v - (vmax - k * span / 14)) / span for k, v in enumerate(vals))
        res["max_dev"] = dev
        res["ok"] = dev <= 0.005
        if not res["ok"]:
            res["err"] = "linear %.4f" % dev
        return res


_readers: dict[int, Reader] = {}


def reader_for(height: int) -> Reader:
    if height not in _readers:
        p = npz_for(height)
        if not p.exists():
            raise RuntimeError(f"Chưa có template glyph cho ảnh cao {height} px ({p.name}). "
                               f"Chạy calibrate_from_pairs với cặp ảnh 1000 px / {height} px.")
        _readers[height] = Reader(p)
    return _readers[height]


def read(img) -> dict:
    im = img if isinstance(img, Image.Image) else Image.open(img)
    h = im.size[1]
    leg = im.crop((0, 0, int(420 * h / 1000), h))                 # chỉ vùng thang màu (nhanh)
    return reader_for(h).read_colorbar(leg)


def calibrate_from_pairs(pairs: list[tuple[str, str]], height: int) -> dict:
    """pairs = [(ảnh 1000 px, cùng ảnh ở `height` px)]. Nhãn đọc ở 1000 px (template h1000) -> template mới."""
    r1 = reader_for(1000)
    acc: dict[str, list[np.ndarray]] = {}
    used = skipped = 0
    for p1, ph in pairs:
        a = r1.read_colorbar(p1)
        if not a["ok"]:
            skipped += 1
            continue
        im = Image.open(ph)
        S = im.size[1] / 1000.0
        gray = _gray(im.crop((0, 0, int(420 * S), im.size[1])))
        ys = label_rows(gray, S)
        if not ys:
            skipped += 1
            continue
        for y, t in zip(ys, a["texts"]):
            gl = segment(gray, y, S)
            if len(gl) != len(t):
                skipped += 1
                continue
            used += 1
            for ch, g in zip(t, gl):
                acc.setdefault(ch, []).append(g)
    chars = sorted(acc)
    np.savez(npz_for(height), chars=np.array(chars), templates=np.stack([np.mean(acc[c], axis=0) for c in chars]))
    return {"height": height, "chars": "".join(chars), "labels_used": used, "skipped": skipped}
