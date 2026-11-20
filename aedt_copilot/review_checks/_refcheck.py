"""Phép đo tham chiếu dùng chung cho các luật sov / ref_other_net / loss_of_reference (031): MỘT lần
review.check_reference cho mỗi channel (cache trong ChannelCtx) -> mỗi luật lọc phần của mình. Số liệu, tốc độ như 011."""
from ..cut_board import review as RV


class NoPlaneLayer(Exception):
    pass


def findings(cc):
    c = cc.ctx
    if not c.B.planes:
        raise NoPlaneLayer("no plane layer")

    def f():
        paths, _, vias, pins = cc.collected
        cu, oc = cc.copper
        excl = [(v["x"], v["y"]) for v in vias + pins]
        return RV.check_reference(c.B, cu, paths, excl, c.R, c.step, oc)
    return cc._get("reference_findings", f)


def layers_trace(f, ref_layers, metal):
    if f["check"] == "Ref to other net":
        return {f.get("layer")}, {str(f.get("ref") or "").split(":")[0].strip()}
    return {f.get("layer")}, {r.strip() for r in str(f.get("ref") or "").split(",") if r.strip()}
