"""Check 'pair_skew' (feature 030, luật 1): chiều dài từng thành viên cặp vi sai / bộ 3 CPHY (trace + thân via, qua linh
kiện nối tiếp, như check routing).
037 (người dùng 2026-11-15): skew cho phép tuỳ spec từng interface, người dùng tự biết -> CHỈ BÁO CHIỀU DÀI: không
ngưỡng, không OK / NOT OK, không khuyến nghị (không bao giờ sinh item). Bảng P / N nằm trong khung cặp của báo cáo."""
from . import _rules as X

NAME = "pair_skew"
ORDER = 50
TITLE, RULE = X.meta(NAME)
DATA_ONLY = True                    # 037: không sinh finding -> không cần REPORT


def run(cc):
    data = []
    for grp in cc.groups["intra"]:
        L = grp.get("lengths") or {}
        if len(L) < 2:
            continue
        data.append({"group": list(L),
                     "lengths_mm": {n: round(float(v["total_mm"]), 4) for n, v in L.items()},
                     "by_layer": {n: {k: round(float(x), 4) for k, x in (v.get("by_layer") or {}).items()}
                                  for n, v in L.items()}})
    return {"items": [], "data": {"groups": data}}
