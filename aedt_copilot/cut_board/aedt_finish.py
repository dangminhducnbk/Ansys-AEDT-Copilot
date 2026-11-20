"""Mở kết quả trong AEDT: bật Highlight mọi net, net tín hiệu đỏ, GND xanh, zoom fit, lưu.
Cú pháp lấy từ script AEDT người dùng ghi lại (Tools > Record Script): "Hi:=" và Color = ["R:=",r,"G:=",g,"B:=",b].
Lưu ý: AEDT KHÔNG báo lỗi khi sai cú pháp (vd "Hl:=" hay "(255 0 0)") - chỉ là không có tác dụng."""
import os

from . import config


def finish(aedb_or_aedt, port=None, design=None):
    from ansys.aedt.core import Hfss3dLayout
    m = config.machine()
    d = config.defaults()["display"]
    refs = set(config.defaults()["cutout"]["reference_nets"])
    kw = dict(project=aedb_or_aedt, version=m["aedt_version"], new_desktop=False, non_graphical=False)
    if design:
        kw["design"] = design
    port = port or m.get("aedt_grpc_port")
    if port:
        kw["port"] = int(port)
    h = Hfss3dLayout(**kw)
    try:
        warns = []
        nets = apply_display(h, d, refs, warnings=warns)
        h.save_project()
        return {"project": h.project_name, "design": h.design_name, "aedt": h.project_file, "nets": nets,
                "ports": len(h.port_list), "setups": h.setup_names, "warnings": warns}
    finally:
        h.release_desktop(close_projects=False, close_desktop=False)   # pyaedt 1.9: close_desktop (không còn close_on_exit)


def apply_display(h, d=None, refs=None, warnings=None):
    """Highlight mọi net, tín hiệu đỏ, GND xanh, zoom fit. Trả số net.
    AEDT 2026 R1: SetNetColor lỗi khi gọi bằng script (gRPC, và cả script người dùng record chạy lại bằng
    RunScript - test 2026-11-04); chỉ thao tác tay trong GUI là được. -> warnings: list nhận cảnh báo,
    không dừng merge/finish (design vẫn đủ port/setup, chỉ thiếu màu). Không dùng RunScript: nó không báo lỗi."""
    d = d or config.defaults()["display"]
    refs = refs or set(config.defaults()["cutout"]["reference_nets"])
    oe = h.oeditor
    nets = list(oe.GetNets())
    hi, col = ["NAME:Args"], ["NAME:Args"]
    for n in nets:
        r, g, b = d["gnd_rgb"] if n in refs else d["signal_rgb"]
        hi += ["Name:=", n, "Hi:=", bool(d["highlight"])]
        col += ["Name:=", n, "Color:=", ["R:=", int(r), "G:=", int(g), "B:=", int(b)]]
    oe.HighlightNet(hi)
    try:
        oe.SetNetColor(col)
    except Exception as ex:
        if warnings is None:
            raise
        warnings.append(f"Không tô được màu net (SetNetColor: {ex}) - design vẫn dùng được, chỉ thiếu màu")
    oe.ZoomToFit()
    return len(nets)
