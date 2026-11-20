"""Cây lệnh CLI (dùng được không cần Claude).

  python -m aedt_copilot inspect  --board <.aedt|.aedb>
  python -m aedt_copilot finish   --aedb <kết quả.aedb|.aedt> [--port <gRPC>]
  (1.0.0: luồng Excel review / propose / cut / status / report / merge / run-job / worker đã bỏ)
  PI-DC (làm trực tiếp trên thư mục có .siw đã giải; report trong <dir>/Ansys AEDT Copilot/):
  python -m aedt_copilot pidc        --dir <thư mục> [--sim "DC IR Sim 1"] [--skills current_density,via_current] [--skip-export]
  python -m aedt_copilot pidc-export --dir <thư mục> [--sim ...] [--voltage-only]
  python -m aedt_copilot pidc-skill  --dir <thư mục> --name current_density|via_current|voltage_distribution|power_tree
                                     [--sim ...] [--pt-voltage 3] [--pt-current 100]
  python -m aedt_copilot pidc-report --dir <thư mục> [--sim ...]
  Sửa layout (improvement, làm trên bản copy; guide layout_edit):
  python -m aedt_copilot layout-region --board <.aedb> --box x0,y0,x1,y1 [--layers L1,L2] [--nets N1,N2]
  python -m aedt_copilot layout-edit   --plan <plan.json | chuỗi JSON>
  Interface simulation (guide interface_sim):
  python -m aedt_copilot isim --op=<start|trace|confirm|cut|ends|validate|apply|status|merge|run|...> --args=<json>
  Công cụ lẻ trên design bất kỳ (guide design_tools; mặc định làm trên bản copy):
  python -m aedt_copilot design --op=<read|setup|sweep|airbox|ports|solder_ball|trace|end_check|check|cutout|cleanup|merge>
         --args=<json> | --args-file=<path>
  Review đo từng check (guide review_measure, chỉ đọc):
  python -m aedt_copilot review-measure --board=<.aedb> --channels="U14-U26:CPHY_*" [--checks=vias,routing] [--html]
         [--snapshot=auto|off]
  Layout snapshot (023: board đọc một lần ra file, review chạy trên đó; chỉ ghi thư mục Ansys AEDT Copilot/snapshots):
  python -m aedt_copilot snapshot --op=<build|status|list> --args=<json> | --args-file=<path>
  Danh mục (tool + workflow, guide catalog):
  python -m aedt_copilot catalog --op=<tools|workflows|get|save> --args=<json>
  Dịch vụ lưu config.html (040, nội bộ: isim_config tự bật; chỉ 127.0.0.1):
  python -m aedt_copilot config-serve [--port=17880]

Lệnh mới: thêm parser ở đây + 1 hàm xử lý trong commands.py (COMMANDS). Không sửa __main__.py.
"""
import argparse


def build_parser():
    ap = argparse.ArgumentParser(prog="aedt_copilot")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("inspect"); p.add_argument("--board", required=True); p.add_argument("--cell")
    p = sub.add_parser("finish"); p.add_argument("--aedb", required=True); p.add_argument("--port"); p.add_argument("--design")
    for name in ("pidc", "pidc-export", "pidc-skill", "pidc-report"):
        p = sub.add_parser(name); p.add_argument("--dir", required=True); p.add_argument("--sim", default="")
        if name == "pidc":
            p.add_argument("--skills", default=""); p.add_argument("--skip-export", action="store_true")
        if name == "pidc-skill":
            p.add_argument("--name", required=True)
            p.add_argument("--pt-voltage", type=float)              # power_tree: ngưỡng điện áp (% hoặc V)
            p.add_argument("--pt-current", type=float)              # power_tree: ngưỡng dòng (A)
        if name == "pidc-export":
            p.add_argument("--voltage-only", action="store_true")    # chỉ bổ sung ảnh VLT của ALL_POWER
    p = sub.add_parser("layout-region"); p.add_argument("--board", required=True); p.add_argument("--box", required=True)
    p.add_argument("--layers", default=""); p.add_argument("--nets", default=""); p.add_argument("--cell", default="")
    p = sub.add_parser("layout-edit"); p.add_argument("--plan", required=True)
    p = sub.add_parser("isim"); p.add_argument("--op", required=True)            # interface simulation (feature 003)
    p.add_argument("--args", default=""); p.add_argument("--args-file", default="")
    p = sub.add_parser("design"); p.add_argument("--op", required=True)          # công cụ lẻ (feature 007)
    p.add_argument("--args", default=""); p.add_argument("--args-file", default="")
    p = sub.add_parser("review-measure"); p.add_argument("--board", required=True)   # review đo (feature 011)
    p.add_argument("--channels", required=True); p.add_argument("--checks", default=""); p.add_argument("--cell", default="")
    p.add_argument("--html", action="store_true"); p.add_argument("--snapshot", default="auto")   # 023
    p = sub.add_parser("review-rules"); p.add_argument("--op", required=True)    # 031: luật review (steering)
    p.add_argument("--args", default=""); p.add_argument("--args-file", default="")
    p = sub.add_parser("stackup-table"); p.add_argument("--op", required=True)   # 030: bảng stackup (luật 6)
    p.add_argument("--args", default=""); p.add_argument("--args-file", default="")
    p = sub.add_parser("snapshot"); p.add_argument("--op", required=True)        # layout snapshot (023)
    p.add_argument("--args", default=""); p.add_argument("--args-file", default="")
    p = sub.add_parser("catalog"); p.add_argument("--op", required=True)         # danh mục (008, tên 2.0.0)
    p.add_argument("--args", default=""); p.add_argument("--args-file", default="")
    p = sub.add_parser("config-serve"); p.add_argument("--port", type=int, default=17880)   # 040: Save của config.html
    return ap
