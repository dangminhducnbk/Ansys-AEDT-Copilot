"""MCP server 'aedt_copilot' - cắt channel tín hiệu từ board Ansys AEDT/EDB.

Server chỉ điều phối: mọi việc nặng chạy bằng tiến trình con `python -m aedt_copilot ...`
(dùng Python có pyedb .NET trong config.yaml). Tool nào chạy quá ~45 s thì trả task_id để gọi task_result sau.

Từ 0.2.0 không còn plugin: hướng dẫn quy trình nằm ở guides/*.md (tool get_guide), lệnh mẫu ở prompts/*.md
(MCP prompts), các gate được khoá trong tool (user_approved_*). Đăng ký với Claude desktop: tools/register_claude.py.

014 (Principle VIII): server chỉ lấy tham số, kiểm tra gate và gọi API package. Chạy CLI / file tham số:
aedt_copilot.cli.tasks; guide / prompt / about: aedt_copilot.cli.docs. Mọi lần chạy CLI đi qua _cli (test patch tên này).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mcp.server.fastmcp import FastMCP                          # noqa: E402
from aedt_copilot import __version__                          # noqa: E402
from aedt_copilot.cut_board import config                     # noqa: E402
from aedt_copilot import aedt_env                             # noqa: E402  (không import pyedb)
# Import sớm (trước mcp.run): import openpyxl/numpy lần đầu bên trong tool khi server stdio đang chạy
# bị treo trên Windows (nạp DLL numpy). 1.0.0: luồng Excel đã bỏ, vẫn import sớm openpyxl (BOM của isim).
import openpyxl                                               # noqa: E402,F401
from aedt_copilot.cli import docs as D, tasks as T            # noqa: E402
from aedt_copilot.cli.io import input_error                   # noqa: E402


def _guides():
    return D.guides()


INSTRUCTIONS = f"""Ansys AEDT Copilot (aedt_copilot) v{__version__}: cut signal channels / interfaces from a full Ansys
AEDT/EDB board into simulation-ready HFSS 3D Layout designs, review layouts, edit layouts, PI-DC reports.
To CUT / SIMULATE an interface: INTERFACE SIMULATION (below) - call get_guide("interface_sim") first. The old channel
Excel flow was removed in 1.0.0.
Gates are enforced: pass user_approved_* / user_* = true only after the user's explicit go in this conversation.
Separate feature: PI-DC report of a SOLVED SIwave DC-IR project (current density per
power net x layer, via current). For any PI-DC request call get_guide("pidc_workflow") first and follow it
(pidc_export -> pidc_current_density -> pidc_via_current -> pidc_voltage_distribution -> pidc_report).
It does not use the interface-simulation guides or gates.
Separate feature: LAYOUT EDIT (improvement of an EDB: carve/extend planes, remove copper, voids, traces, stitch vias).
For any request to change layout copper/vias call get_guide("layout_edit") first, then layout_region -> plan ->
layout_edit (one call applies all ops on a COPY, checks, images, changes.md). Never write ad-hoc pyedb scripts for it.
Separate process: INTERFACE SIMULATION, FIXED PROCESS since 5.0.0 (guide section 0): isim_start -> isim_trace ->
isim_layout_review -> since 5.6.0 (045): ONE page per request (config.html: per channel tab Review layout with the NOT
OK points to Resolve + tab Settings), answer M0p, no Q0 -> user resolves every point, saves + "xong"/"done" ->
isim_config_check (M2 or Q2; refused while a point is unresolved) -> "đồng ý"/"yes" -> isim_go(user_approved_cut)
(cut + build + merge into a NEW project of the request folder, M3). Requests of 5.2-5.5: M0 + Q0 -> isim_review_answer
(no: STOP M0x | yes: config.html, M1). Paste every answer_md verbatim; only questions Q0 (old requests) / Q1 / Q2.
For it call get_guide("interface_sim") first. Step tools with gates A-D
(user_confirmed_content, user_agreed_settings, user_approved_merge, user_requested_run) stay for older requests /
single steps on request.
Separate tools: ATOMIC DESIGN TOOLS design_* (one operation on ANY .aedb: setup, sweep, airbox, ports, solder ball;
copy by default) -> get_guide("design_tools") first.
TOOL CATALOG: every tool has a safety level + gate, every process is a workflow (team or personal). For any request
that is not clearly one process, and for "what can you do": list_workflows + list_tools first;
get_guide("catalog"). Tools trace / cutout / cleanup / end_check / check / merge compose new processes.
REVIEW AS DATA: design_review (any board / design, one check or all) / isim_review (MANDATORY step right after
isim_trace; always writes the HTML report: send it to the user, who reads it and decides. Each check is only OK /
NOT OK against its threshold - no severity levels; never judge findings for the user) -> get_guide("review_measure"). HTML report for a standalone review: design_review(html=true).
Reviews run on a cached LAYOUT SNAPSHOT (board read once, results identical, re-run in seconds); build it in the
background with layout_snapshot(op="build", board, nets) as soon as the nets are known (after isim_trace).
Open a cut / merged design in AEDT with nets highlighted (signal red, GND blue): finish_in_aedt (on request, AEDT GUI;
ask the user first).
Re-cut "like last time" / "như lần trước" / old settings: isim_previous -> isim_start -> isim_recut (never re-type
old values; show only differences).
Use only this server's tools for this work (not pyaedt-mcp, not ad-hoc Python). Reply in the user's language.
Guides available: {", ".join(_guides())}. New user / "what can you do" -> call about()."""

mcp = FastMCP("aedt_copilot", instructions=INSTRUCTIONS)
# 010 (Principle X): mọi tool đăng ký qua tool() - thiếu mục danh mục / mức an toàn / cờ đồng ý / contract -> server
# không khởi động (CatalogRegistrationError nêu tên tool). Tool mới: thêm mục vào aedt_copilot/catalog/tools.py.
from aedt_copilot.catalog.registration import make_tool          # noqa: E402
tool = make_tool(mcp)
WAIT_S = 45


def _cli(args, wait=WAIT_S):
    """Chạy CLI ở tiến trình con; quá `wait` giây thì trả task_id."""
    return T.run(args, wait)


def _result(tid):
    return T.result(tid)


@tool()
def inspect_board(board: str, cell: str = "") -> dict:
    """Đọc tổng quan một board AEDT/EDB (.aedt hoặc .aedb): các design, lớp, số net, linh kiện lớn.
    Dùng trước khi đề xuất channel cần cắt. Chỉ đọc, không sửa board."""
    return _cli(["inspect", f"--board={board}"] + ([f"--cell={cell}"] if cell else []))




def _refuse(msg):
    return {"refused": True, "reason": msg}


@tool()
def get_guide(topic: str = "") -> dict:
    """Hướng dẫn quy trình / kỹ thuật cho Claude (thay cho skill). topic trống = danh sách guide.
    Cắt / mô phỏng interface: get_guide("interface_sim"); việc khác: get_guide("catalog")."""
    return D.guide(topic)


@tool()
def about() -> dict:
    """Công cụ này làm được gì: phiên bản, các bước, prompt (lệnh mẫu), guide. Dùng khi người dùng mới hỏi."""
    return D.about()












@tool()
def finish_in_aedt(aedb: str, port: int = 0) -> dict:
    """Mở một channel ĐÃ CẮT trong AEDT, bật highlight, tô màu (tín hiệu đỏ, GND xanh), zoom fit, lưu.
    aedb: đường dẫn .aedb/.aedt kết quả (isim_status / kết quả design_* / interface sim). port: gRPC của AEDT đang mở (0 = tự tìm)."""
    return _cli(["finish", f"--aedb={aedb}"] + ([f"--port={port}"] if port else []))




# ----------------------------------------------------------------------------- Layout edit (guide layout_edit)
@tool()
def layout_region(board: str, box: str, layers: str = "", nets: str = "") -> dict:
    """Sửa layout bước 1 (get_guide('layout_edit')): ĐỌC một vùng của board (.aedb), không sửa gì.
    box: 'x0,y0,x1,y1' mm. layers / nets: lọc, cách nhau dấu phẩy (trống = tất cả).
    Trả mỗi lớp: polygon (id, net, diện tích trong vùng), trace theo net, via theo net/padstack; padstack (pad mm theo lớp);
    linh kiện; ảnh PNG từng lớp; region.json (hình học đầy đủ, mm). Dùng để lập plan cho layout_edit."""
    # --key=value: giá trị bắt đầu bằng '-' (vd box '-3.3,-8.4,...') argparse không coi là option
    return _cli(["layout-region", f"--board={board}", f"--box={box.strip()}"] +
                ([f"--layers={layers}"] if layers else []) + ([f"--nets={nets}"] if nets else []))


@tool()
def layout_edit(plan: str) -> dict:
    """Sửa layout bước 2 (get_guide('layout_edit')): áp plan JSON (đường dẫn file hoặc chuỗi JSON) lên BẢN COPY của board.
    1 lần mở EDB: đọc vùng -> chạy mọi op (add_copper, carve, remove_copper, void, trace, via, delete) -> dọn void vụn ->
    lưu -> đọc lại -> kiểm tra (chồng đồng, khe hở, mảnh đồng, via/pin mất kết nối, via mới, + checks trong plan) ->
    ảnh trước/sau -> changes.md. Op lỗi: không lưu gì, xoá bản copy, trả lỗi. Board gốc không bao giờ bị sửa.
    Thường 1-3 phút: có thể trả {pending, task_id} -> task_result."""
    if plan.strip().startswith("{"):
        plan = T.args_file("plan", plan)
    return _cli(["layout-edit", f"--plan={plan}"])


# ----------------------------------------------------------------------------- Công cụ lẻ (guide design_tools, 007)
def _design(op, board, cell="", values=None, targets=None, in_place=False, user_approved_in_place=False):
    if in_place and not user_approved_in_place:
        return _refuse("SỬA TẠI CHỖ: trình bày thao tác + file sẽ bị sửa (có backup), chờ người dùng đồng ý rõ ràng, "
                       "rồi gọi lại với user_approved_in_place=true. Hoặc bỏ in_place để làm trên bản copy.")
    path = T.args_file(f"design_{op}", {"board": board, "cell": cell, "values": values or {},
                                        "targets": targets or {}, "in_place": bool(in_place)})
    return _cli(["design", f"--op={op}", f"--args-file={path}"])


def _design_values(values):
    if values in (None, ""):
        return {}, None
    if isinstance(values, dict):
        return values, None
    try:
        v = json.loads(values)
    except ValueError as ex:
        return None, _refuse(f"values: cần JSON hợp lệ ({ex})")
    if not isinstance(v, dict):
        return None, _refuse("values: cần JSON object {key: value}")
    return v, None


@tool()
def design_read(board: str, cell: str = "") -> dict:
    """CÔNG CỤ LẺ (get_guide('design_tools')): đọc (CHỈ ĐỌC) setup / sweep, airbox, port, solder ball của một .aedb
    bất kỳ. Dùng trước một thao tác để báo giá trị cũ."""
    return _design("read", board, cell)


@tool()
def design_setup(board: str, values: str, setup_name: str = "", cell: str = "", in_place: bool = False,
                 user_approved_in_place: bool = False) -> dict:
    """CÔNG CỤ LẺ: tạo / thay HFSS setup (adaptive freq, passes, delta S, arc step ...) + sweep của một .aedb.
    values: JSON {setup.*: v, sweep.start_ghz, sweep.stop_ghz, sweep.step_ghz (bắt buộc), ...}; còn lại = mặc định
    template. Mặc định làm trên BẢN COPY (đường dẫn trong report). in_place: sửa file đã cho sau backup - cần
    user_approved_in_place=true sau khi người dùng đồng ý rõ ràng."""
    v, bad = _design_values(values)
    return bad or _design("setup", board, cell, v, {"setup_name": setup_name}, in_place, user_approved_in_place)


@tool()
def design_sweep(board: str, values: str, setup_name: str = "", cell: str = "", in_place: bool = False,
                 user_approved_in_place: bool = False) -> dict:
    """CÔNG CỤ LẺ: thay sweep của một setup có sẵn (start / stop / step GHz, type, interpolation ...).
    values: JSON {sweep.*: v}. setup_name trống = setup duy nhất / setup mặc định. Copy mặc định; in_place cần cờ."""
    v, bad = _design_values(values)
    return bad or _design("sweep", board, cell, v, {"setup_name": setup_name}, in_place, user_approved_in_place)


@tool()
def design_airbox(board: str, values: str = "", cell: str = "", in_place: bool = False,
                  user_approved_in_place: bool = False) -> dict:
    """CÔNG CỤ LẺ: đặt airbox (extent, dielectric extent, padding ngang / +Z / -Z, Z theo stackup, open region,
    operating freq). values: JSON {airbox.*: v}, trống = mặc định template. Copy mặc định; in_place cần cờ."""
    v, bad = _design_values(values)
    return bad or _design("airbox", board, cell, v, {}, in_place, user_approved_in_place)


@tool()
def design_ports(board: str, refdes: str, nets: str = "", replace: bool = False, cell: str = "",
                 in_place: bool = False, user_approved_in_place: bool = False) -> dict:
    """CÔNG CỤ LẺ: tạo coax port cho pin của linh kiện (refdes cách nhau dấu phẩy) trên các net (trống = mọi net
    không phải GND/reference), tên <refdes>.<pin>.<net>. Port đã có -> bỏ qua; replace=true -> xoá rồi tạo lại.
    Copy mặc định; in_place cần cờ."""
    return _design("ports", board, cell, {}, {"refdes": refdes, "nets": nets, "replace": bool(replace)},
                   in_place, user_approved_in_place)


@tool()
def design_solder_ball(board: str, refdes: str, values: str = "", cell: str = "", in_place: bool = False,
                       user_approved_in_place: bool = False) -> dict:
    """CÔNG CỤ LẺ: đặt solder ball cho linh kiện (refdes cách nhau dấu phẩy) theo luật nhóm (đường kính = tỉ lệ x
    cạnh ngắn pad tín hiệu, chiều cao mm) hoặc values JSON {solder_ball.*: v}. Copy mặc định; in_place cần cờ."""
    v, bad = _design_values(values)
    return bad or _design("solder_ball", board, cell, v, {"refdes": refdes}, in_place, user_approved_in_place)


@tool()
def design_trace(board: str, refdes: str, nets: str = "", cell: str = "") -> dict:
    """TOOL (get_guide('catalog')): dò channel (CHỈ ĐỌC) trên board / design bất kỳ: net, nhóm vi sai, R/C/L nối
    tiếp, loại đầu, pin tín hiệu 2 đầu. refdes: 2 linh kiện (cách nhau dấu phẩy), hoặc 1 + nets. nets: tên / mẫu *."""
    return _design("trace", board, cell, {}, {"refdes": refdes, "nets": nets})


@tool()
def design_cutout(board: str, comp_a: str, comp_b: str, nets: str, series: str = "", name: str = "",
                  values: str = "", cell: str = "") -> dict:
    """TOOL: cắt 1 channel từ BẢN COPY của board thành design MỚI <thư mục board>/Ansys AEDT Copilot/design_tools/
    <name>_cutout_<giờ>/<name>.aedb (+ stage1.json). Board đã cho không bị sửa. nets: tên / mẫu (bắt buộc).
    series: refdes R/C/L nối tiếp giữ lại. name trống = <prefix>_<a>_<b>. values: JSON {cutout.*, series.*}.
    ~5 phút với board lớn: thường trả {pending, task_id} -> task_result."""
    v, bad = _design_values(values)
    return bad or _design("cutout", board, cell, v, {"comp_a": comp_a, "comp_b": comp_b, "nets": nets,
                                                      "series": series, "name": name})


@tool()
def design_cleanup(board: str, ends: str, nets: str = "", values: str = "", cell: str = "", in_place: bool = False,
                   user_approved_in_place: bool = False) -> dict:
    """TOOL: dọn GND của design đã cắt (mảnh vụn lớp plane, shield xa tín hiệu, pin GND BGA xa, via GND xa).
    ends: refdes 2 đầu. nets / bga / diện tích: từ stage1.json cạnh design (design_cutout), không có thì tự tính.
    values: JSON {cleanup.*}. Copy mặc định; in_place cần user_approved_in_place=true sau khi người dùng đồng ý."""
    v, bad = _design_values(values)
    return bad or _design("cleanup", board, cell, v, {"ends": ends, "nets": nets}, in_place, user_approved_in_place)


@tool()
def design_end_check(board: str, refdes: str, nets: str = "", cell: str = "") -> dict:
    """TOOL: đo các đầu (CHỈ ĐỌC): loại, pad, GND gần pin tín hiệu, solder ball, via-in-pad, trường hợp lạ +
    options. refdes cách nhau dấu phẩy; nets trống = net không phải reference / nguồn. Trả ends + ends_md."""
    return _design("end_check", board, cell, {}, {"refdes": refdes, "nets": nets})


@tool()
def design_check(board: str, ends: str, nets: str = "", values: str = "", setup_name: str = "", cell: str = "") -> dict:
    """TOOL: tự kiểm tra design (CHỈ ĐỌC): đầu còn, port = pin tín hiệu trên các đầu, setup / sweep, airbox đúng
    giá trị mong đợi (template + values JSON; sweep.start/stop/step: cả 3 hoặc không - không có thì không so).
    Trả {ok, mismatches, ports, signal_pins}."""
    v, bad = _design_values(values)
    return bad or _design("check", board, cell, v, {"ends": ends, "nets": nets, "setup_name": setup_name})


@tool()
def design_merge(workspace: str, designs: str, port: int = 0, user_approved_merge: bool = False) -> dict:
    """TOOL (mức WORKSPACE): gộp design .aedb vào workspace .aedt (backup trước, mỗi design 1 design mới, trùng tên
    -> _v2, không ghi đè). designs: JSON {tên: .aedb} hoặc đường dẫn .aedb cách nhau dấu phẩy (tên = tên file).
    port: gRPC của AEDT đang mở workspace (0 = workspace phải đóng). user_approved_merge: true CHỈ khi người dùng đã
    đồng ý gộp rõ ràng. Thường trả task_id."""
    if not user_approved_merge:
        return _refuse("MERGE: trình bày workspace + danh sách design sẽ gộp, chờ người dùng đồng ý rõ ràng, rồi gọi "
                       "lại với user_approved_merge=true.")
    d, bad = _json_arg("designs", designs) if designs.strip().startswith("{") else (designs, None)
    if bad:
        return bad
    if os.path.exists(workspace + ".lock") and not port:
        return _refuse("Workspace đang mở/khoá trong AEDT: hỏi người dùng đóng project hoặc cho port của phiên AEDT đó. "
                       "Không xoá file .lock.")
    path = T.args_file("design_merge", {"workspace": workspace, "designs": d, "port": port or None})
    return _cli(["design", "--op=merge", f"--args-file={path}"])


@tool()
def design_review(board: str, channels: str, checks: str = "", cell: str = "", html: bool = False,
                  snapshot: str = "auto") -> dict:
    """TOOL (get_guide('review_measure')): ĐO review layout (CHỈ ĐỌC) trên board / design bất kỳ, từng check hoặc tất
    cả: reference (SOV, ref to other net, loss of ref), trace_stubs, vias (stub, via GND gần nhất, đổi lớp plane),
    routing (chiều dài / lớp, độ rộng, skew). channels: 'U14-U26:CPHY_*; U21-J25:...'. checks: cách nhau dấu phẩy
    (trống = tất cả). Trả số liệu, mỗi item status OK / NOT OK theo ngưỡng (036: không có mức nặng nhẹ) + summary_md.
    html=true -> thêm báo cáo HTML có ảnh (báo cáo layout review). Vài phút: có thể trả task_id.
    snapshot: 'auto' (mặc định: đo trên layout snapshot, tự dựng / dùng lại, kết quả như live) | 'off' (đọc EDB live).
    025: kết quả lưu thành bản ghi cạnh board (review_file, <board>/Ansys AEDT Copilot/reviews/) với số điểm NOT OK
    từng channel (+ theo check) + findings_md (không kết luận); interface simulation dùng lại khi còn hợp lệ."""
    if snapshot not in ("auto", "off"):
        return _refuse(f"snapshot: expected auto / off, got {snapshot!r}")
    return _cli(["review-measure", f"--board={board}", f"--channels={channels}"] +
                ([f"--checks={checks}"] if checks else []) + ([f"--cell={cell}"] if cell else []) +
                (["--html"] if html else []) + ([f"--snapshot={snapshot}"] if snapshot != "auto" else []))


@tool()
def review_rules(op: str = "list", rule_id: str = "", user_approved_personal_code: bool = False) -> dict:
    """TOOL (031, get_guide('review_measure')): luật layout review, MỖI LUẬT một file steering (định nghĩa, ngưỡng, mức,
    why / fix, cách trao đổi) + một file code nếu luật đo. op: list (mọi luật: team + cá nhân, shadowed khi trùng id,
    has_code, enabled) | get (đọc steering của MỘT luật theo rule_id - đọc khi diễn giải phát hiện của luật đó) |
    enable / disable (luật CÁ NHÂN có code; enable cần user_approved_personal_code=true sau khi người dùng nói rõ cho chạy
    code đó). Luật team ở repo review_rules/; luật cá nhân ở AEDT_COPILOT_REVIEW_RULES hoặc ~/.aedt_copilot/review_rules."""
    if op not in ("list", "get", "enable", "disable"):
        return _refuse(f"op: expected list / get / enable / disable, got {op!r}")
    if op != "list" and not rule_id.strip():
        return _refuse("rule_id: expected a rule id (review_rules op=list)")
    if op == "enable" and not user_approved_personal_code:
        return _refuse("user_approved_personal_code: enable a personal rule's code only after the user said to run it "
                       "in this conversation")
    path = T.args_file("review_rules", {"rule_id": rule_id})
    return _cli(["review-rules", f"--op={op}", f"--args-file={path}"])


@tool()
def review_stackup_table(board: str, op: str = "get", table: str = "", source_file: str = "", cell: str = "",
                         user_confirmed_table: bool = False) -> dict:
    """TOOL (030, get_guide('review_measure')): bảng width / gap theo lớp từ stackup của nhà máy cho luật review 6
    (stackup_width). Lưu ở <thư mục board>/Ansys AEDT Copilot/stackup/<board>.json, KHÔNG ghi vào board.
    op: get (bảng hiện có) | template (lớp tín hiệu của board, bảng trống) | save. Quy trình: người dùng đưa file stackup
    (PDF / Excel) -> bạn đọc ra bảng {layers: {<lớp>: {se_width_mm, pairs: [{name, width_mm, gap_mm}]}}} (mm), cho
    người dùng xem, người dùng xác nhận -> save với user_confirmed_table=true (bảng cũ được giữ lại tên _old_<giờ>).
    table: JSON; source_file: đường dẫn file stackup gốc."""
    if op not in ("get", "template", "save"):
        return _refuse(f"op: expected get / template / save, got {op!r}")
    args = {"board": board, "cell": cell}
    if op == "save":
        if not user_confirmed_table:
            return _refuse("user_confirmed_table: save the stackup table only after the user confirmed it in this "
                           "conversation (show the table first)")
        t, bad = _json_arg("table", table)
        if bad:
            return bad
        args.update(table=t, source_file=source_file)
    path = T.args_file("review_stackup_table", args)
    return _cli(["stackup-table", f"--op={op}", f"--args-file={path}"])


@tool()
def layout_snapshot(op: str, board: str, cell: str = "", nets: str = "", scope: str = "window",
                    margin_mm: float = 0) -> dict:
    """TOOL (get_guide('review_measure')): LAYOUT SNAPSHOT - đọc board MỘT lần ra file để review chạy lại trong vài giây.
    CHỈ ĐỌC board; chỉ ghi <thư mục board>/Ansys AEDT Copilot/snapshots/. op: build | status | list.
    build: nets (tên / mẫu, cách nhau dấu phẩy) -> cửa sổ = bbox các net + margin_mm (0 = mặc định template);
    scope='board' = cả board (lâu hơn). Dùng lại snapshot còn hợp lệ; board đổi (edb.def) -> dựng lại.
    status: valid / stale / missing / too_small. list: các snapshot của board. Build có thể trả task_id (chạy nền)."""
    if op not in ("build", "status", "list"):
        return _refuse(f"op: expected build / status / list, got {op!r}")
    if scope not in ("window", "board"):
        return _refuse(f"scope: expected window / board, got {scope!r}")
    if op == "build" and scope == "window" and not nets.strip():
        return _refuse("nets: expected at least one net / pattern (or scope='board')")
    if margin_mm is None or margin_mm < 0:
        return _refuse(f"margin_mm: expected >= 0, got {margin_mm!r}")
    args = {"board": board}
    if op != "list":
        args.update(cell=cell, nets=nets, scope=scope, margin_mm=margin_mm)
    path = T.args_file("layout_snapshot", args)
    return _cli(["snapshot", f"--op={op}", f"--args-file={path}"])


# ----------------------------------------------------------------------------- Danh mục (guide catalog, 008 / 020)
def _catalog(op, **args):
    from aedt_copilot.core.errors import CopilotInputError
    from aedt_copilot.catalog import api
    try:
        return api.call(op, args)
    except CopilotInputError as ex:
        return input_error(ex)


@tool()
def list_tools(group: str = "", kind: str = "", safety: str = "") -> dict:
    """DANH MỤC (get_guide('catalog')): mọi tool, nhóm, kind (tool | process), mức an toàn
    (read | copy | original | workspace | remote) + cờ đồng ý, đầu vào -> đầu ra. Lọc tuỳ chọn. Trả table_md."""
    return _catalog("tools", group=group, kind=kind, safety=safety)


@tool()
def list_workflows() -> dict:
    """DANH MỤC: danh sách workflow (quy trình) của nhóm (repo workflows/) và cá nhân (thư mục riêng; thư mục cũ
    trước 2.0.0 vẫn đọc), nguồn, số bước, điểm dừng, trạng thái (ok / broken / error / shadowed). Trùng tên giữa nhóm
    và cá nhân -> 2 dòng: hỏi người dùng chọn."""
    return _catalog("workflows")


@tool()
def get_workflow(name: str, source: str = "") -> dict:
    """DANH MỤC: đọc 1 workflow (bước, tool, điểm dừng, thân bài). source: team | personal (bắt buộc khi trùng tên)."""
    return _catalog("get", name=name, source=source)


@tool()
def save_workflow(name: str, markdown: str, overwrite: bool = False) -> dict:
    """DANH MỤC: lưu workflow vào thư mục CÁ NHÂN (không bao giờ thư mục nhóm) - CHỈ khi người dùng yêu cầu lưu.
    markdown: front matter YAML (name = name, title, description, inputs, steps[{tool, note, checkpoint}]) + thân bài.
    Đã có file cùng tên -> từ chối, trừ khi overwrite=true (người dùng đồng ý ghi đè)."""
    return _catalog("save", name=name, markdown=markdown, overwrite=bool(overwrite))


# ----------------------------------------------------------------------------- PI-DC (guide pidc_workflow)
def _pidc(cmd, folder, sim_name, *extra):
    return _cli([cmd, f"--dir={folder}"] + ([f"--sim={sim_name}"] if sim_name else []) + list(extra))


@tool()
def pidc_export(folder: str, sim_name: str = "") -> dict:
    """PI-DC bước 1 (get_guide('pidc_workflow')): xuất ảnh DC report 6x của project SIwave ĐÃ GIẢI DC-IR.
    folder: thư mục chứa .siw + .siwaveresults. Làm TRỰC TIẾP trên thư mục đó, không copy, KHÔNG save project.
    Output: <folder>/Ansys AEDT Copilot/raw/. Mở SIwave qua explorer.exe (cần desktop có GPU). sim_name: trống = sim DC duy nhất.
    Chạy ~15-25 phút: trả {pending, task_id} -> task_result. Kết quả: missing_jobs, image_size."""
    return _pidc("pidc-export", folder, sim_name)


@tool()
def pidc_current_density(folder: str, sim_name: str = "") -> dict:
    """PI-DC skill current density (get_guide('pidc_current_density')): J trung bình ô 0.5 mm, J_avg_max mỗi net x lớp,
    vùng nổi bật, ảnh images/CD_*.png. Cần pidc_export trước. Vài phút: có thể trả task_id."""
    return _pidc("pidc-skill", folder, sim_name, "--name=current_density")


@tool()
def pidc_via_current(folder: str, sim_name: str = "") -> dict:
    """PI-DC skill via current (get_guide('pidc_via_current')): dòng mỗi via nguồn (đoạn xấu nhất) vs I_cap IPC,
    3 ảnh images/VIA_*.png khoanh via FAIL/WARN + top-N. Cần pidc_export trước."""
    return _pidc("pidc-skill", folder, sim_name, "--name=via_current")


@tool()
def pidc_voltage_distribution(folder: str, sim_name: str = "") -> dict:
    """PI-DC skill voltage distribution (get_guide('pidc_voltage_distribution')): 1 ảnh images/VLT_ALL_POWER.png - mọi rail
    nguồn, mọi lớp chồng lên nhau, khoanh Vmin mỗi tải + điện áp VRM; bảng mỗi rail. Chỉ thông tin. Cần pidc_export trước."""
    return _pidc("pidc-skill", folder, sim_name, "--name=voltage_distribution")


@tool()
def pidc_power_tree(folder: str, sim_name: str = "", voltage: float = 0, current: float = 0) -> dict:
    """PI-DC skill power tree (get_guide('pidc_power_tree')): SIwave Export DC Power Tree -> images/POWER_TREE.png +
    bảng Pass/Fail mỗi tải. Mặc định (template pidc.pt_*): Include Yes, Current 100 A, Percentage 3 %, aggregate pins ON,
    power loss list OFF. voltage / current: CHỈ khi người dùng yêu cầu đổi (0 = mặc định). Tự mở SIwave (~1-2 phút)."""
    extra = ([f"--pt-voltage={voltage}"] if voltage else []) + ([f"--pt-current={current}"] if current else [])
    return _pidc("pidc-skill", folder, sim_name, "--name=power_tree", *extra)


@tool()
def pidc_report(folder: str, sim_name: str = "") -> dict:
    """PI-DC bước cuối: gộp kết quả các skill -> <folder>/Ansys AEDT Copilot/PIDC_report_<time>.html + report.md +
    summary.json + csv (ảnh trong images/, dùng được cho PowerPoint). Trả html, verdicts, suspect_points."""
    return _pidc("pidc-report", folder, sim_name)


# ----------------------------------------------------------------------------- Interface simulation (guide interface_sim)
def _isim(op, wait=WAIT_S, **args):
    """Chạy `python -m aedt_copilot isim --op=<op>` (tiến trình con); tham số ghi ra file JSON (tránh giới hạn dòng lệnh)."""
    path = T.args_file(f"isim_{op}", args)
    return _cli(["isim", f"--op={op}", f"--args-file={path}"], wait)


def _json_arg(name, text, default=None):
    """Tham số JSON dạng chuỗi -> dict. Lỗi -> (None, refusal)."""
    if text in (None, ""):
        return default, None
    if isinstance(text, (dict, list)):
        return text, None
    try:
        return json.loads(text), None
    except ValueError as ex:
        return None, _refuse(f"{name}: cần JSON hợp lệ ({ex})")


def _isim_state(request_id, name):
    from aedt_copilot.interface_sim import request as R
    try:
        req = R.load(request_id)
        return req, R.get_state(req["request_id"], name), None
    except ValueError as ex:
        return None, None, _refuse(str(ex))


@tool()
def isim_start(workspace: str, board: str = "", cell: str = "", stackup: str = "", schematic: str = "",
               bom: str = "", interfaces: str = "", netlist: str = "") -> dict:
    """INTERFACE SIMULATION bước 0 (get_guide('interface_sim') TRƯỚC). Tạo request cho workspace AEDT của người dùng.
    workspace: .aedt chính (người dùng chuẩn bị). board: .aedb (trống = của workspace). stackup: file stackup rời (tuỳ chọn).
    schematic: PDF, nhiều file cách nhau ';'. bom: .xlsx/.csv. interfaces: tên dự kiến cách nhau ';' (tuỳ chọn).
    netlist (036, tuỳ chọn, NÊN có): netlist xuất từ công cụ schematic (Protel 2.0 của Altium / Allegro Telesis; nhận
    theo nội dung) -> code đọc kết nối + giá trị linh kiện, KHÔNG cần đọc PDF để lấy kết nối.
    Trả request_id, folder, netlist (tóm tắt), schematic_status (+ schematic_template khi không có netlist và chưa có
    schematic.md dùng được)."""
    return _isim("start", workspace=workspace, board=board, cell=cell, stackup=stackup, schematic=schematic,
                 bom=bom, interfaces=interfaces, **({"netlist": netlist} if netlist else {}))


@tool()
def isim_bom(request_id: str = "", bom: str = "") -> dict:
    """Bước 0: đọc BOM (.xlsx/.csv) bằng code -> bom.json (map cột, mở rộng R1-R4). Trống = BOM trong request."""
    return _isim("bom", request_id=request_id, path=bom)


@tool()
def isim_schematic_status(request_id: str = "") -> dict:
    """Bước 0: schematic.md đã có / còn đúng với file nguồn (tên, size, thời gian)? reuse_from = bản của request trước.
    036: request có netlist -> source 'netlist', up_to_date true (không cần schematic.md)."""
    return _isim("schematic_status", request_id=request_id)


@tool()
def isim_save_schematic(request_id: str, markdown: str) -> dict:
    """Bước 0: lưu schematic.md do agent viết theo schematic_template (mục Sources, Components, Nets bắt buộc,
    tiêu đề bảng đúng mẫu). Trả số linh kiện / net, mục không đọc được, khác biệt BOM."""
    return _isim("save_schematic", request_id=request_id, markdown=markdown)


@tool()
def isim_trace(request_id: str, name: str = "", refdes: str = "", nets: str = "") -> dict:
    """Bước 1: đọc board (CHỈ ĐỌC) -> đề xuất nội dung interface: net, nhóm vi sai/CPHY, linh kiện 2 đầu, R/C/L nối tiếp,
    loại đầu, khác biệt với schematic.md, thông số cắt (cutout.*). refdes / nets: cách nhau dấu phẩy (net nhận mẫu *).
    name trống = tên tự sinh. Trình bày content_md cho người dùng, sửa đến khi người dùng chốt."""
    return _isim("trace", request_id=request_id, name=name, refdes=refdes, nets=nets)


@tool()
def isim_previous(name: str, workspace: str = "") -> dict:
    """CUT LẠI (004) bước 0: người dùng nói "cut lại X như lần trước" / "settings cũ". Liệt kê các lần chạy cũ của
    interface `name` cho cùng workspace (trống = workspace của request mới nhất), mới nhất trước: request id, ngày,
    bước cuối, sweep. Chỉ đọc. Cho người dùng chọn, rồi isim_start (request MỚI) -> isim_recut."""
    return _isim("previous", name=name, workspace=workspace)


@tool()
def isim_recut(request_id: str, name: str, source: str, nets: str = "") -> dict:
    """CUT LẠI (004) bước 1: request_id = request MỚI (isim_start). source = request id cũ, thư mục request cũ, hoặc
    đường dẫn user_settings.json (kể cả copy từ máy khác). Trace lại trên board hiện tại (CHỈ ĐỌC) với 2 đầu + net cũ;
    trả recut_diffs (CHỈ khác biệt), proposal = nội dung cũ, old_values, old_handling, content_md.
    Không khác biệt -> vẫn chờ người dùng "đồng ý" rồi isim_confirm_content (GATE A). Mỗi khác biệt cần resolution
    (content.recut_diffs[{item, ref, resolution}]). nets: mẫu net khác (cách nhau dấu phẩy), trống = như lần trước."""
    n = [x.strip() for x in nets.split(",") if x.strip()] or None
    return _isim("recut", request_id=request_id, name=name, source_ref=source, nets=n)


@tool()
def isim_confirm_content(request_id: str, name: str, content: str, user_confirmed_content: bool = False,
                         user_words: str = "") -> dict:
    """Bước 1 - GATE A = lời đồng ý DUY NHẤT (035): người dùng đã xem vùng cut dự tính (isim_cut_preview) + đọc file
    review HTML (isim_review) và đồng ý cut. content: JSON {comp_a, comp_b, nets[], diff_groups[[]],
    series{refdes: {nets[]}}, schematic_diffs[{item, resolution}], structural{cutout.*: v}, end_factors{}}.
    user_confirmed_content: true CHỈ khi người dùng đã nói rõ đồng ý cut interface này trong cuộc trò chuyện này, SAU khi
    đã nhận report + vùng cut. user_words: lời người dùng (ghi lại). Từ chối khi review thiếu / cũ / không có report,
    hoặc chưa có preview cùng thông số. Số điểm NOT OK không chặn. Ghi user_settings.json (review.approval).
    Cut lại (004): content.recut_diffs[{item, ref, resolution}] cho MỌI khác biệt."""
    if not user_confirmed_content:
        return _refuse("GATE A: gửi vùng cut dự tính + file review HTML, hỏi người dùng đọc review và xác nhận cut, rồi "
                       "gọi lại với user_confirmed_content=true.")
    c, bad = _json_arg("content", content)
    if bad:
        return bad
    req, st, bad = _isim_state(request_id, name)
    if bad:
        return bad
    bad = _review_refusal(req, st, name, c)                            # 035: review + report bắt buộc
    kw = {"user_words": user_words} if user_words.strip() else {}
    return bad or _isim("confirm", request_id=req["request_id"], name=name, content=c, **kw)


def _review_refusal(req, st, name, content=None, for_cut=False):
    """025 / 035 (Principle I): GATE A từ chối khi review layout thiếu / cũ / chưa có report HTML; cut từ chối khi kỹ
    sư chưa đồng ý (GATE A sau khi đọc report). Số điểm NOT OK không chặn. Interface đã qua GATE A mà nội dung
    không đổi -> không kiểm tra (request cũ vẫn apply / merge)."""
    from aedt_copilot.interface_sim import review as RVW
    c = content if isinstance(content, dict) else None
    if c is not None and not (c.get("comp_a") and c.get("comp_b") and isinstance(c.get("nets"), list)):
        return None                                                    # nội dung sai: package báo lỗi đầu vào
    old = st.get("content") or {}
    if c is not None and st["step"] != "started" and old and \
            sorted([str(c["comp_a"]), str(c["comp_b"])]) == sorted([old.get("comp_a"), old.get("comp_b")]) and \
            sorted(set(c["nets"])) == sorted(set(old.get("nets") or [])):
        return None
    try:
        g = RVW.gate_status(req["request_id"], name, c)
    except ValueError as ex:
        return _refuse(str(ex))
    if g["ok"] and for_cut and g["status"] != "approved":
        return _refuse(f"{name}: người dùng chưa đồng ý cut sau khi đọc review: gửi vùng cut dự tính + file review, hỏi, "
                       "rồi isim_confirm_content (GATE A).") | {"review_gate": g}
    return None if g["ok"] else _refuse(g["message"]) | {"review_gate": g}


@tool()
def isim_cut_form(request_id: str = "") -> dict:
    """FORM CUT SETTINGS ở GATE A (022): một tab / interface; mỗi tab = các dòng template cutout.* + series.keep
    (key, label, unit, type, choices, default cho "Set default", value, copy=true) + một ô "end factor" cho MỖI đầu
    (cutout.end_factor.<refdes>, trống = tự động, per_end=true, copy=false: "Copy to all tabs" KHÔNG copy ô này);
    preview gần nhất (ảnh, bảng). Tab khoá sau khi cắt. CHỈ ĐỌC. Client vẽ được widget -> vẽ form (guide
    interface_sim); không -> trình bày table_md. Submit = dữ liệu nhập: isim_cut_preview từng tab; GATE A vẫn cần
    người dùng đồng ý rõ ràng rồi isim_confirm_content (content.structural + content.end_factors)."""
    return _isim("cut_form", request_id=request_id)


@tool()
def isim_cut_preview(request_id: str, name: str, values: str = "", end_factors: str = "") -> dict:
    """XEM TRƯỚC VÙNG CUT trước khi cắt (022, GATE A): mở board gốc CHỈ ĐỌC, tính vùng cutout bằng đúng hàm cắt dùng
    (hệ số nền + luật GND 2 đầu + hệ số tay) -> bảng từng đầu (pin GND trên board, GND nằm trọn ở hệ số nền, hệ số
    dùng, mm2 thêm, pin GND giữ được, net khác trong phần thêm) + ảnh vùng cut + ảnh zoom từng đầu mở rộng. values:
    JSON {cutout.* / series.keep: giá trị} của form (trống = đã lưu); end_factors: JSON {refdes: hệ số | ""} (trống =
    tự động). Ghi ảnh / preview.json trong thư mục interface, KHÔNG ghi gì vào board. Đổi giá trị -> gọi lại. Lỗi hệ số
    tay -> sửa / xoá trước GATE A. Thường trả task_id (~1 phút).
    036: khi review đã có report -> answer_md (câu trả lời 3 phần, DÁN NGUYÊN VĂN, không thêm câu nào) + answer_image."""
    v, bad = _json_arg("values", values, None)
    e, bad2 = _json_arg("end_factors", end_factors, None)
    if bad or bad2:
        return bad or bad2
    return _isim("cut_preview", request_id=request_id, name=name, structural=v, end_factors=e)


@tool()
def isim_cut(request_id: str, name: str) -> dict:
    """Bước 2a: cắt interface trên BẢN COPY của board (copy vào thư mục interface, ~5 phút). Cần nội dung đã chốt.
    Thường trả {pending, task_id} -> task_result. Có thể chạy song song nhiều interface (mỗi interface 1 sub-agent)."""
    req, st, bad = _isim_state(request_id, name)
    if bad:
        return bad
    if st["step"] != "content_agreed":
        return _refuse(f"Cần nội dung đã chốt (GATE A); bước hiện tại: {st['step']}.")
    bad = _review_refusal(req, st, name, for_cut=True)                 # 035: chưa có lời đồng ý -> không cut
    return bad or _isim("cut", request_id=req["request_id"], name=name)


@tool()
def isim_check_ends(request_id: str, name: str) -> dict:
    """Bước 2b: đo 2 đầu interface trên bản đã cắt (chỉ đọc): loại đầu, pad, GND gần pin tín hiệu, solder ball, via-in-pad,
    trường hợp lạ (unusual + options). Trả ends_md + settings_md (bảng thông số đề xuất) để trao đổi với người dùng.
    Cut lại (004): thêm handling_compare / handling_md (kept / not_needed / needs_choice), values + handling điền sẵn
    từ lần trước (dùng cho isim_validate_settings / isim_apply), dropped."""
    return _isim("ends", request_id=request_id, name=name)


@tool()
def isim_validate_settings(request_id: str, name: str, values: str, handling: str = "") -> dict:
    """Bước 2: kiểm tra bảng thông số (cùng luật với Excel cũ). values: JSON {key: value} (bắt buộc sweep.start_ghz,
    stop_ghz, step_ghz). handling: JSON {refdes: option} cho đầu có unusual. Trả valid, errors, table_md.
    Interface đã apply / merge: luật re-apply (006) - nhóm cut khoá."""
    v, bad = _json_arg("values", values, {})
    h, bad2 = _json_arg("handling", handling, {})
    if bad or bad2:
        return bad or bad2
    return _isim("validate", request_id=request_id, name=name, values=v, handling=h)


@tool()
def isim_settings_form(request_id: str = "") -> dict:
    """FORM SETTINGS ĐẦY ĐỦ (005, GATE B): một tab / interface của request; mỗi tab = MỌI thông số scope channel của
    template (key, label, unit, type, choices, default = mặc định nhóm cho nút "Set default", value đề xuất, group,
    mandatory, locked + lý do), unusual {refdes: options}, handling điền sẵn. Tab chưa tới bước ends_checked bị khoá.
    CHỈ ĐỌC. Client vẽ được widget -> vẽ form theo guide interface_sim (tabs, Set default, Copy to all tabs); không
    -> trình bày table_md (bảng đầy đủ theo nhóm)."""
    return _isim("form", request_id=request_id)


@tool()
def isim_validate_form(request_id: str, entries: str) -> dict:
    """Kiểm tra form đã submit (005): entries JSON {interface: {values: {key: value}, handling: {refdes: option}}}.
    Từng interface kiểm tra riêng (luật như isim_validate_settings), lỗi tab này không chặn tab khác. KHÔNG apply:
    trình bày table_md từng interface, chờ người dùng "đồng ý" rồi isim_apply từng interface (GATE B)."""
    e, bad = _json_arg("entries", entries)
    if bad:
        return bad
    return _isim("validate_form", request_id=request_id, entries=e)


@tool()
def isim_apply(request_id: str, name: str, values: str, handling: str = "", user_agreed_settings: bool = False,
               gnd_notes: str = "", user_approved_gnd: bool = False) -> dict:
    """Bước 2c - GATE B: áp thông số ĐÃ THỐNG NHẤT (copy bản cắt -> port, dọn GND, solder ball, setup/sweep, airbox,
    tự kiểm tra). user_agreed_settings: true CHỈ khi người dùng đã đồng ý bảng thông số. Thường trả task_id.
    Giá trị đã chốt ghi vào user_settings.json của request (đường dẫn trong kết quả).
    Đã apply / merge (006): RE-APPLY chỉ setup / sweep / airbox (nhóm cut khoá: đổi = cut lại); backup
    final/<name>_old_<time>.aedb; GATE B lại; interface đã merge -> về applied, merge lại = design mới.
    015 - đầu không pin GND (isim_check_ends trả gnd_questions + ảnh): handling[refdes] = lựa chọn CỦA NGƯỜI DÙNG
    (gnd_plate_vias / gnd_existing_copper / keep_component / stop_interface; 'other' -> agent map về 1 option).
    gnd_notes JSON {refdes: lời người dùng}; user_approved_gnd: true CHỈ khi người dùng đã trả lời câu hỏi đó."""
    if not user_agreed_settings:
        return _refuse("GATE B: trình bày bảng thông số, chờ người dùng đồng ý, rồi gọi lại với user_agreed_settings=true.")
    v, bad = _json_arg("values", values, {})
    h, bad2 = _json_arg("handling", handling, {})
    n, bad3 = _json_arg("gnd_notes", gnd_notes, None)
    if bad or bad2 or bad3:
        return bad or bad2 or bad3
    from aedt_copilot.interface_sim import settings as S
    op, kw, bad = S.apply_route(request_id, name, v, h, user_approved_gnd)   # 006 re-apply; 015 cờ GND
    if not bad and op == "apply" and n:
        kw["gnd_notes"] = n
    return bad or _isim(op, **kw)


@tool()
def isim_review(request_id: str, name: str, checks: str = "", html: bool = False, snapshot: str = "auto",
                reuse: bool = True, nets: str = "") -> dict:
    """Bước BẮT BUỘC ngay sau isim_trace, TRƯỚC preview / GATE A (025 / 035; get_guide('review_measure')): đo review
    layout của interface (2 đầu + net của đề xuất, hoặc nội dung đã chốt) trên board của request, CHỈ ĐỌC. Lưu
    <interface>/review.json + bản ghi cạnh board (Ansys AEDT Copilot/reviews/) + LUÔN ghi báo cáo HTML (`html` = đường
    dẫn): GỬI file này cho người dùng đọc. Dùng lại bản ghi còn hợp lệ (board không đổi, cùng 2 đầu / net / đủ check /
    cùng ngưỡng; reuse=false = đo lại) -> reused_from. Trả số điểm NOT OK (+ theo check; chỉ là số liệu, KHÔNG chặn /
    KHÔNG cho phép cut) + gate (report ready / approved / out of date ...) + answer_md khi đã có preview (036: dán
    nguyên văn). Người dùng đọc report rồi quyết định ở GATE A.
    nets: danh sách net (dấu phẩy) khi nội dung sắp chốt khác đề xuất. checks=một phần -> review_partial.json (không thay
    review bắt buộc; html=true mới có báo cáo). snapshot: 'auto' (layout snapshot) | 'off' (live). Có thể trả task_id."""
    if snapshot not in ("auto", "off"):
        return _refuse(f"snapshot: expected auto / off, got {snapshot!r}")
    kw = {} if snapshot == "auto" else {"snapshot": snapshot}
    if not reuse:
        kw["reuse"] = False
    n = [x.strip() for x in nets.split(",") if x.strip()]
    if n:
        kw["nets"] = n
    return _isim("review", request_id=request_id, name=name, checks=checks or None, html=bool(html), **kw)


@tool()
def isim_status(request_id: str = "") -> dict:
    """Bảng trạng thái mọi interface của request (bước, lỗi, unusual, cảnh báo, design đã gộp). Trống = request mới nhất."""
    return _isim("status", request_id=request_id)


@tool()
def isim_merge(request_id: str = "", names: str = "", port: int = 0, user_approved_merge: bool = False) -> dict:
    """Bước 3 - GATE C: gộp các interface đã apply vào workspace chính (backup trước, mỗi interface 1 design mới,
    trùng tên -> _v2; không sửa design có sẵn). names: cách nhau dấu phẩy (trống = tất cả đã apply).
    port: gRPC của AEDT đang mở workspace (0 = workspace phải đóng). Thường trả task_id."""
    if not user_approved_merge:
        return _refuse("GATE C: trình bày isim_status, chờ người dùng duyệt gộp, rồi gọi lại với user_approved_merge=true.")
    from aedt_copilot.interface_sim import merge as M
    try:
        req, ready, missing = M.plan(request_id, names)
    except ValueError as ex:
        return _refuse(str(ex))
    if not ready:
        return _refuse("Chưa có interface nào ở bước 'applied'.") | {"missing": missing}
    if names == "" and missing:
        return _refuse("Còn interface chưa xong - hỏi người dùng: gộp các interface đã xong (truyền names) hay chờ.") | {
            "ready": ready, "missing": missing}
    if os.path.exists(req["workspace"] + ".lock") and not port:
        return _refuse("Workspace đang mở/khoá trong AEDT: hỏi người dùng đóng project hoặc cho port của phiên AEDT đó. "
                       "Không xoá file .lock.")
    return _isim("merge", request_id=req["request_id"], names=",".join(ready), port=port or None)


@tool()
def isim_run(request_id: str = "", server: str = "", port: int = 17878, sim_dir: str = "", sim_dir_server: str = "",
             designs: str = "", mode: str = "service", aedt_port: int = 50000, client_port: int = 18050,
             user_requested_run: bool = False) -> dict:
    """Bước 4 - GATE D (chỉ khi người dùng YÊU CẦU chạy): đưa workspace lên server, giải lần lượt từng design.
    mode 'service' (mặc định): server chạy PyAEDT service manager (port, mặc định 17878); tool mở AEDT không giao diện
    trên server (aedt_port 50000-50010, client_port 18000-18100 - trong firewall), đóng AEDT đó khi xong.
    sim_dir: thư mục simulation đã share, nhìn từ máy này (copy trực tiếp). Trống -> upload qua phiên RPyC vào
    sim_dir_server (đường dẫn TRÊN server). Mỗi lần chạy 1 thư mục con mới <request>_<time>, không ghi đè.
    mode 'grpc': AEDT người dùng đã mở (ansysedt.exe -grpcsrv <port>), cần sim_dir.
    designs: cách nhau dấu phẩy (trống = mọi design đã gộp). Chạy nền: theo dõi bằng isim_run_status."""
    if not user_requested_run:
        return _refuse("GATE D: chỉ chạy simulation khi người dùng yêu cầu rõ, rồi gọi lại với user_requested_run=true.")
    if not server:
        return _refuse("Hỏi người dùng: server (tên / IP máy chạy simulation).")
    if not sim_dir and not sim_dir_server:
        return _refuse("Hỏi người dùng: thư mục simulation trên server (sim_dir_server) và nó có share sang máy này "
                       "không (sim_dir).")
    if mode == "grpc" and not sim_dir:
        return _refuse("mode grpc cần sim_dir (thư mục share nhìn từ máy này).")
    return _isim("run", request_id=request_id, server=server, port=port, sim_dir=sim_dir,
                 sim_dir_server=sim_dir_server, designs=designs, mode=mode, aedt_port=aedt_port,
                 client_port=client_port)


@tool()
def isim_run_status(request_id: str = "", run_id: str = "") -> dict:
    """Tiến độ chạy simulation remote: từng design (queued/running/done/failed), thời gian, lỗi solver, đường dẫn kết quả."""
    return _isim("run_status", request_id=request_id, run_id=run_id)


@tool()
def isim_layout_review(request_id: str = "") -> dict:
    """039 BƯỚC 2-3 của quy trình cố định (get_guide('interface_sim')): sau isim_trace của MỌI channel, TRƯỚC config.
    Review layout mọi channel (board CHỈ ĐỌC, luôn có file HTML). Request 5.6.0+ (045): ghi luôn TRANG DUY NHẤT của
    request (config.html: mỗi channel tab Review layout - điểm NOT OK để Resolve - và tab Settings) -> answer_md = M0p
    (bảng review + link trang), KHÔNG có Q0: người dùng Resolve hết, Save, nói 'xong' -> isim_config_check. Request
    5.2-5.5: answer_md = M0 + Q0 'Review layout ổn, chuyển sang bước config không?'. DÁN NGUYÊN VĂN; KHÔNG tự trả lời,
    không nhận xét review thay người dùng. Request tạo trước 5.2.0: bị từ chối (dùng isim_config). Có thể trả task_id."""
    return _isim("layout_review", request_id=request_id)


@tool()
def isim_review_answer(request_id: str = "", accepted: bool = False, user_answered_review: bool = False,
                       user_words: str = "") -> dict:
    """039 BƯỚC 4: người dùng trả lời Q0 (isim_layout_review) trong cuộc trò chuyện này. accepted=false ('không' /
    'no') -> request DỪNG, answer_md = M0x. accepted=true ('đồng ý' / 'ok' / 'yes') -> lưu lời đồng ý (gắn với các
    review đã gửi) rồi ghi config.html -> answer_md = M1. DÁN NGUYÊN VĂN. Từ chối khi review đã đổi sau Q0
    (isim_layout_review lại). user_words: lời người dùng. Câu trả lời khác (thảo luận) -> KHÔNG gọi tool này.
    Request 5.6.0+ (045) không có Q0: tool này bị từ chối."""
    if not user_answered_review:
        return _refuse("Q0: gửi M0 + Q0 (isim_layout_review), chờ người dùng trả lời 'đồng ý' / 'không', rồi gọi lại "
                       "với user_answered_review=true, accepted và user_words.")
    if not user_words.strip():
        return _refuse("user_words: ghi lại câu trả lời của người dùng cho Q0.")
    return _isim("review_answer", request_id=request_id, accepted=bool(accepted), user_words=user_words)


@tool()
def isim_config(request_id: str = "") -> dict:
    """038 BƯỚC 3 của quy trình cố định (get_guide('interface_sim')): sau isim_trace của MỌI channel. Request 5.2.0+
    (039): chỉ sau lời đồng ý Q0 (isim_review_answer đã tự gọi bước này); gọi lại khi cần ghi lại trang. Review layout
    (khi chưa có / đã cũ), đọc board CHỈ ĐỌC (vùng cut 3 kiểu x 19 bước, đồng từng lớp, pad 2 đầu, trường hợp lạ),
    ghi <request>/config.html (một tab / channel). Trả answer_md = M1: DÁN NGUYÊN VĂN, không thêm câu nào.
    Thường trả task_id (vài phút lần đầu)."""
    return _isim("config", request_id=request_id)


@tool()
def isim_config_check(request_id: str = "") -> dict:
    """038 BƯỚC 5: người dùng nói 'xong' / 'done'. Đọc file config người dùng đã Save (thư mục request, hoặc thư mục
    Downloads), kiểm tra. Lỗi -> answer_md = M2 (bảng lỗi). Chưa Save -> M1 + Q1. Hợp lệ -> đặt thư mục channel,
    vùng cut dự tính (preview với thông số đã chọn) + file review của mọi channel -> answer_md = Q2. DÁN NGUYÊN VĂN.
    Thường trả task_id."""
    return _isim("config_check", request_id=request_id)


@tool()
def isim_go(request_id: str = "", user_approved_cut: bool = False, user_words: str = "") -> dict:
    """038 BƯỚC 7-8 - lời đồng ý DUY NHẤT: người dùng trả lời 'đồng ý' / 'yes' cho Q2 (isim_config_check) trong cuộc
    trò chuyện này. Mỗi channel: chốt nội dung + cut trên bản copy + đo 2 đầu + dựng design (port, solder ball, setup,
    sweep, airbox) theo config; gộp vào PROJECT MỚI <request>/<request_id>.aedt (không ghi file nào của người dùng);
    thư mục channel = <tên>.aedb / .aedt, review.html, config.html. Từ chối khi config đổi sau Q2.
    user_words: lời người dùng. Trả answer_md = M3: DÁN NGUYÊN VĂN. Thường trả task_id (vài phút / channel)."""
    if not user_approved_cut:
        return _refuse("Q2: gửi vùng cut + file review (isim_config_check), chờ người dùng trả lời 'đồng ý' / 'yes', rồi "
                       "gọi lại với user_approved_cut=true và user_words.")
    if not user_words.strip():
        return _refuse("user_words: ghi lại lời đồng ý của người dùng.")
    return _isim("go", request_id=request_id, user_words=user_words)


@tool()
def task_result(task_id: str) -> dict:
    """Lấy kết quả của tool trước đó đã trả {pending: true, task_id}."""
    return _result(task_id)


@tool()
def show_defaults() -> dict:
    """Thông số mặc định của nhóm (templates/autocut_template.csv) và phiên bản công cụ."""
    return {"version": __version__, "defaults": config.defaults(), "machine": config.machine(), "aedt": aedt_env.info()}


# ----------------------------------------------------------------------------- prompts (lệnh mẫu)
def _prompt_files():
    return D.prompt_files()


def _register_prompts():
    for name, desc in _prompt_files().items():
        mcp.prompt(name=name, description=desc)(_make_prompt(D.prompt_path(name)))


def _make_prompt(path):
    def fn(arguments: str = "") -> str:
        return D.prompt_text(path, arguments)              # đọc lại mỗi lần: sửa file có hiệu lực ngay
    return fn


_register_prompts()

if __name__ == "__main__":
    mcp.run()
