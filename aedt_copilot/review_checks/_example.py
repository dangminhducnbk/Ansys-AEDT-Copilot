"""MẪU check review - KHÔNG được nạp (tên bắt đầu '_'). 031: một luật = steering review_rules/<id>.md (copy
review_rules/_template.md) + file code này đổi tên thành review_checks/<id>.py (NAME = id).

Trong luật thật (xem sov.py): TITLE, RULE = X.meta(NAME); REPORT = X.report(NAME, _describe, _layers);
câu Why / Fix lấy bằng X.text(NAME, "why" / "fix", biến thể, **giá trị) - chữ nằm trong steering (một nguồn).
File mẫu này giữ chữ tại chỗ vì không có steering đi kèm (để test hợp đồng 028 chạy độc lập).
Đơn vị trong finding: mét. status: "NOT OK" khi vượt ngưỡng của luật, "OK" khi chỉ là dữ liệu (036: không có mức).
Hợp đồng: specs/031-review-rule-files/contracts/review-rules.md, specs/028-check-report-text/contracts/check-report.md.
"""
from . import _text as T

NAME = "example_wide_trace"            # duy nhất trong registry
ORDER = 90                             # thứ tự chạy / hiển thị
TITLE = "Example: trace wider than a limit"
RULE = "Wide trace NOT OK when width > 0.3 mm (example)"
LIMIT_MM = 0.3                         # luật thật: đặt ngưỡng ở template (review.<key>) và đọc từ cc.ctx.R


def run(cc):
    """cc = review_checks._context.ChannelCtx: cc.trace (nets...), cc.collected (paths, polys, vias, pins),
    cc.copper, cc.via_rows, cc.ctx.B (Board: planes, ref_layers), cc.ctx.R (template review.*)."""
    paths = cc.collected[0]
    items = []
    for p in paths:
        if p["w"] > LIMIT_MM * T.MM:
            x, y = p["pts"][0]
            items.append({"check": "Wide trace", "status": "NOT OK", "net": p["net"], "layer": p["layer"],
                          "ref": "", "x": x, "y": y, "value": f"width {p['w'] / T.MM:.3f} mm",
                          "bbox": (x, y, x, y)})
    return {"items": items, "data": {}}


def _describe(f, P, c=None):
    """-> (rows [(nhãn, chữ)], why, fix). Giá trị đặt cạnh ngưỡng, lời thường, tiếng Anh."""
    w = T.num(f.get("value"), r"width ([0-9.]+) mm")
    rows = [("At", T.xy(f)), ("Trace", str(f.get("layer") or "")),
            ("Width", f"{w:.3f} mm — limit ≤ {LIMIT_MM:.3f} mm ✗" if w is not None else str(f.get("value")))]
    return rows, "a wider trace lowers the impedance of this segment (reflection).", "neck the trace to the rule width."


def _layers(f, ref_layers, metal):
    """-> (lớp tín hiệu, lớp plane) vẽ trong ảnh; None = không biết (ảnh chỉ lớp issue + ghi chú)."""
    return {f.get("layer")}, set(ref_layers(f.get("layer")))


REPORT = {
    "Wide trace": {"section": "routing", "title": "Trace wider than the rule", "limit_key": None,
                   "describe": _describe, "layers": _layers},
}
