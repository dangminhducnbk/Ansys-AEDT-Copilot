"""Dọn pin GND của đầu SMD / via-in-pad / connector (feature 021, contract:
specs/021-smd-gnd-pin-cleanup/contracts/gnd-pin-cleanup.md). Thuần (không EDB).

Giữ pin GND của chính linh kiện nằm trong cleanup.smd_gnd_pin_keep_dist_mm của ít nhất 1 pin tín hiệu, cộng pin GND
gần nhất của MỖI pin tín hiệu (kể cả xa hơn -> cảnh báo), cộng pin được bảo vệ (pin / pad GND của luật 022, pad giữ
lại 019). Khoảng cách = tâm pin tín hiệu -> MÉP pad GND (khung pad, 0 khi chồng lên) (sửa 2026-11-10: exposed pad
6.3 mm sát pin tín hiệu không còn bị coi là xa); luật BGA vẫn tâm - tâm.
"""
import math

MM = 1e-3


def dist(x, y, g):
    """Điểm (x, y) -> pin GND g: (x, y) tâm hoặc (x0, y0, x1, y1) khung pad (0 khi điểm nằm trong). Thuần."""
    if len(g) == 4:
        x0, y0, x1, y1 = min(g[0], g[2]), min(g[1], g[3]), max(g[0], g[2]), max(g[1], g[3])
        return math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1))
    return math.hypot(g[0] - x, g[1] - y)


def select(sig_xy, gnd, keep_m, protect=()):
    """sig_xy [(x, y)] (m), gnd {tên: (x, y) | khung pad} -> {keep, removed, nearest {i: tên}, far [i], no_signal}."""
    names = sorted(gnd)
    if not sig_xy or not names:
        return {"keep": names, "removed": [], "nearest": {}, "far": [], "no_signal": not sig_xy}
    keep = {n for n in protect if n in gnd}
    nearest, far = {}, []
    for i, (x, y) in enumerate(sig_xy):
        ds = sorted((dist(x, y, gnd[n]), n) for n in names)
        keep |= {n for d, n in ds if d <= keep_m + 1e-12}
        nearest[i] = ds[0][1]
        keep.add(ds[0][1])
        if ds[0][0] > keep_m + 1e-12:
            far.append(i)
    return {"keep": sorted(keep), "removed": sorted(set(names) - keep), "nearest": nearest, "far": far,
            "no_signal": False}


def report(rd, before, sel, keep_mm, sig_names=None):
    """-> {refdes, gnd_pins_before, gnd_pins_after, removed, keep_dist_mm, warnings, info}.
    Đúng 1 pin GND riêng (luật 2026-11-10): pin đó là đường hồi của chip -> không cảnh báo xa, chỉ dòng info."""
    w, info = [], []
    if sel.get("no_signal"):
        w.append(f"{rd}: no signal pin to measure from - no GND pin removed")
    if before == 1 and sel.get("keep"):
        info.append(f"{rd}: GND duy nhất pin {sel['keep'][0]}, đã giữ")
    else:
        for i in sel.get("far") or []:
            sp = (sig_names or {}).get(i, f"#{i}")
            w.append(f"{rd}: signal pin {sp} has no GND pin within {keep_mm} mm - nearest GND pin "
                     f"{sel['nearest'][i]} kept")
    return {"refdes": rd, "gnd_pins_before": before, "gnd_pins_after": len(sel["keep"]),
            "removed": sel["removed"][:50], "keep_dist_mm": keep_mm, "warnings": w, "info": info}


def protected_names(stage1, rd):
    """Pin GND không bao giờ xoá: 022 (pin nằm trọn / pin giành được), 019 (pad giữ lại)."""
    out = set()
    e = (((stage1 or {}).get("end_gnd") or {}).get("ends") or {}).get(rd) or {}
    if e.get("gnd_pin_inside"):
        out.add(str(e["gnd_pin_inside"]))
    out |= {str(p["pin"]) for p in e.get("gnd_pins_gained") or [] if p.get("pin") is not None}
    out |= {str(p) for p in ((stage1 or {}).get("kept_pads") or {}).get(rd) or []}
    return out


def keep_m(P):
    """Khoảng giữ (m) từ P['cleanup'] (mặc định 1.6 mm như hàng BGA)."""
    v = (P.get("cleanup") or {}).get("smd_gnd_pin_keep_dist_mm")
    return float(1.6 if v is None else v) * MM
