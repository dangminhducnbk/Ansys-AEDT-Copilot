"""Lịch sử mặc định của nhóm (feature 009, contract: defaults-history.md).

values đã chốt của một lần chạy chỉ giữ khoá người dùng nhập; mặc định template đọc lúc apply. Khi đổi mặc định
(vd arc step 10 -> 30 ở 0.11.1), cut lại / re-apply lần chạy cũ phải giữ giá trị lần đó dùng: tra theo tool_version
của lần chạy. Mặc định hiện tại vẫn chỉ nằm ở template (test: giá trị cuối = template).
"""
HISTORY = {
    "setup.arc_step_deg": [((0, 7, 0), 10), ((0, 11, 1), 30)],
    # 021: luật mới (trước đó giữ mọi pin GND của đầu SMD / connector). Lần chạy cũ: NOT_YET -> cut lại dùng luật mới,
    # dòng settings ghi nguồn "team default (new)" (Q3 B)
    "cleanup.smd_gnd_pin_keep_dist_mm": [((2, 3, 0), 1.6)],
}


class _NotYet:
    def __repr__(self):
        return "NOT_YET"


NOT_YET = _NotYet()


def ver(v):
    try:
        t = tuple(int(x) for x in str(v).split(".")[:3])
        return t + (0,) * (3 - len(t))
    except ValueError:
        return (0, 0, 0)                                               # "<0.7.0" (request 0.6.0), lỗi -> rất cũ


def default_at(key, tool_version):
    """Mặc định của key ở phiên bản đó; NOT_YET nếu key chưa có; None nếu key không có lịch sử."""
    h = HISTORY.get(key)
    if not h:
        return None
    v = ver(tool_version)
    val = NOT_YET
    for since, x in h:
        if v >= since:
            val = x
    return val


def fill(values, tool_version):
    """values + khoá lịch sử còn thiếu (mặc định thời tool_version). Khoá đã có không bao giờ đổi."""
    out = dict(values or {})
    for k in HISTORY:
        if k not in out:
            d = default_at(k, tool_version)
            if d is not None and d is not NOT_YET:
                out[k] = d
    return out


def effective(values, P):
    """values + khoá lịch sử còn thiếu, lấy từ P (giá trị thật đã dùng) -> lưu tường minh vào lần chạy."""
    out = dict(values or {})
    for k in HISTORY:
        sec, name = k.split(".", 1)
        if k not in out and (P.get(sec) or {}).get(name) is not None:
            out[k] = P[sec][name]
    return out
