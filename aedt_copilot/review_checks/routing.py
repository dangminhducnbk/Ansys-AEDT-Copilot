"""Check 'routing': chiều dài theo chuỗi net / lớp, độ rộng, lệch trong cặp / bộ 3 và giữa nhóm (review.lengths)."""
from ..cut_board import naming
from ..cut_board import review as RV
from . import _rules as X

NAME = "routing"
ORDER = 40
TITLE, RULE = X.meta(NAME)
DATA_ONLY = True                    # 028: không sinh finding -> không cần REPORT


def run(cc):
    c, t = cc.ctx, cc.trace
    paths = cc.collected[0]
    rows, _ = cc.via_rows
    pg = set(c.edb.nets.power.keys()) | set(c.refs)
    chains = RV._chains(t["nets"], t["series"], t["start_nets"], pg)
    groups = naming.review_groups(t["start_nets"])                          # 034: tên 'X_P*' cũng ghép cặp
    chain_len, intra, inter, widths = RV.lengths(chains, paths, rows, groups)
    for g in intra:
        g["layers"] = {n: list(v) for n, v in g["layers"].items()}
    return {"items": [], "data": {"chains": chain_len, "intra": intra, "inter": inter,
                                  "widths_mm": {k: list(v) for k, v in widths.items()}}}
