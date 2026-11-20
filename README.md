# Ansys AEDT Copilot

Tự động cắt channel tín hiệu từ board Ansys AEDT/EDB thành design HFSS 3D Layout riêng (port, setup,
sweep, airbox, solder ball, dọn GND) để mô phỏng nhanh. Có review layout (HTML) trước khi cắt.
Dùng qua Claude Code / Claude desktop (MCP server `aedt_copilot`) hoặc dòng lệnh.

## Cài đặt (mỗi máy, 1 lần)

Yêu cầu: Windows, Ansys AEDT 2026 R1 (không có thì dùng 2025 R2), Python 3.10–3.12, git, Claude desktop.
`setup.bat` tự chọn bản AEDT (`ANSYSEM_ROOT261`, rồi `ANSYSEM_ROOT252`) và ghi vào `config.yaml`.

Lưu ý AEDT 2026 R1:
- File do 2026 R1 lưu (kết quả cắt, bản copy của layout edit, project sau merge/finish) **không mở được bằng 2025 R2**.
- Không tô được màu net bằng script (lỗi của AEDT 2026 R1): merge/finish báo warning "thiếu màu", design vẫn dùng
  được bình thường. Muốn có màu thì đổi tay trong AEDT.

Cách nhanh nhất: clone rồi bảo AI IDE (Claude Code, ...) "cài repo này" — nó đọc [INSTALL.md](INSTALL.md) và làm
từng bước. Làm tay:

```bat
git clone https://github.com/dangminhducnbk/Ansys-AEDT-Copilot.git D:\tools\Ansys-AEDT-Copilot
cd /d D:\tools\Ansys-AEDT-Copilot
setup.bat
```

Thư mục clone **không được có dấu cách**. `setup.bat` tạo `.venv`, cài thư viện, đặt `AEDT_COPILOT_HOME` và **tự đăng
ký MCP server `aedt_copilot`** cho Claude Code (mở session mới) và Claude desktop (thoát hẳn app, cả icon khay hệ
thống, rồi mở lại). Client MCP khác: `.venv\Scripts\python tools\register_claude.py --print`.
Đã clone repo private cũ trước đây: clone lại repo public này.
Không cần plugin (bản ≤ 0.1.x dùng plugin `ansys-aedt-copilot`: hãy gỡ nó).

Cập nhật: `git pull` → khởi động lại Claude. Chạy lại `setup.bat` khi CHANGELOG ghi "Cần chạy setup.bat"
(requirements đổi) hoặc khi đổi chỗ thư mục repo.

## Dùng với Claude

Trong chat mới, bấm **"+" → aedt_copilot** để chọn prompt, hoặc nói thẳng (vd "cắt board X channel U14-U26:CPHY_*").

| Prompt | Việc |
|---|---|
| `copilot-help` | Giới thiệu cho người mới |
| `interface-sim` | Cắt / mô phỏng interface: thống nhất nội dung → cắt (bản copy) → kiểm tra đầu → chốt settings → apply → gộp → chạy |
| `design-tools` | Một thao tác trên design bất kỳ (setup, sweep, airbox, port, solder ball, ...) |
| `catalog` | Danh mục tool + workflow (quy trình) |
| `pidc-report` | Báo cáo PI-DC |

Các bước cần người dùng duyệt (gate A–D của interface simulation, đầu không pin GND, sửa tại chỗ, merge) được khoá trong
server: Claude không thể bỏ qua. Từ 1.0.0 không còn luồng Excel (job Excel cũ: checkout tag `v0.15.0` để làm xong).

## PI-DC report (từ 0.3.0, tách riêng khỏi cắt board)

Đầu vào: thư mục chứa `.siw` SIwave đã giải DC-IR + `.siwaveresults`. Làm **trực tiếp** trên thư mục đó (không copy,
không save project). Kết quả trong `<thư mục>\Ansys AEDT Copilot\`:
`PIDC_report_<time>.html`, `images\*.png` (kéo thẳng vào PowerPoint), `report.md`, `summary.json`, `*.csv`, `raw\` (ảnh SIwave 6x).

| Cách gọi | |
|---|---|
| Prompt `pidc-report` / nói "làm PI-DC report cho thư mục X" | Claude đọc guide `pidc_workflow` rồi chạy |
| `.venv\Scripts\python -m aedt_copilot pidc --dir "<thư mục>"` | Chạy cả quy trình không cần Claude (~35–45 phút) |
| `... pidc --dir "<thư mục>" --skip-export` | Làm lại phân tích + report từ `raw\` (không mở SIwave) |

- Guide: `pidc_workflow` (điều khiển) → skill `pidc_current_density`, `pidc_via_current`, `pidc_voltage_distribution`,
  `pidc_power_tree`. Tool MCP: `pidc_export`, `pidc_current_density`, `pidc_via_current`, `pidc_voltage_distribution`,
  `pidc_power_tree`, `pidc_report`.
- Power tree mặc định 100 A / 3 %; đổi: `... pidc-skill --dir "<thư mục>" --name power_tree --pt-voltage 5 --pt-current 2`.
- Thư mục đã export trước 0.3.1 (chưa có ảnh voltage): `... pidc-export --dir "<thư mục>" --voltage-only` (~2 phút).
- Thông số: `templates/pidc_template.csv` (giới hạn 150/100 A/mm², ô trung bình 0.5 mm, IPC via dT 35 °C, ảnh 6x...).
- SIwave được mở qua `explorer.exe` (cần desktop có GPU); ảnh nét nhờ biến môi trường `EXPORT_REPORT_IMAGE_WIDTH/HEIGHT`.

## Sửa layout / improvement (từ 0.4.0)

Nói với Claude: "trong board X, mở rộng plane ASM_1P1V L9 ở U200, thêm stitch via L5–L12…". Claude đọc guide
`layout_edit`, gọi `layout_region` (đọc vùng) rồi `layout_edit(plan)` một lần. Luôn làm trên **bản copy**:
`<thư mục board>\Ansys AEDT Copilot\layout_edit\<tên>_<time>\` (`.aedb` đã sửa, `changes.md`, `img\` trước/sau, `result.json`).

| Cách gọi | |
|---|---|
| `.venv\Scripts\python -m aedt_copilot layout-region --board "<.aedb>" --box x0,y0,x1,y1` | Đọc vùng + ảnh từng lớp |
| `.venv\Scripts\python -m aedt_copilot layout-edit --plan plan.json` | Áp plan (xem guide `layout_edit`) |

Thao tác: `add_copper`, `carve`, `remove_copper`, `void`, `trace`, `via`, `delete`. Thông số: `templates/layout_edit_template.csv`.

## Interface simulation (từ 0.6.0, không dùng Excel)

Prompt `interface-sim` (guide `interface_sim`). Claude đọc schematic PDF + BOM **một lần** → `schematic.md`; với mỗi
interface: thống nhất net / linh kiện (GATE A) → cắt trên **bản copy** board → kiểm tra 2 đầu (pad, GND, connector…)
→ bảng settings, người dùng đồng ý (GATE B) → apply + tự kiểm tra; sau cùng gộp vào workspace chính (GATE C, backup
trước) và chỉ khi người dùng yêu cầu: copy sang thư mục simulation trên server, giải lần lượt (GATE D).
File: `<thư mục workspace>\Ansys AEDT Copilot\interface_sim\<request>\` (`user_settings.json`, `schematic.md`,
`<interface>\content.md`, `ends.md`, `final\<interface>.aedb`, `merge.json`, `run_*.json`).

- **Giữ pin GND của 2 đầu + xem trước vùng cut** (từ 2.1.0): trước khi cắt, tool tìm pin GND / exposed pad
  của mỗi IC / connector đầu; đầu nào mất hết pin GND với hệ số cut thì CHỈ vùng đầu đó được mở rộng (+0.02 mỗi
  lần) tới khi giữ được một pin. Ở GATE A có form cut settings (một tab / interface, ô hệ số riêng cho từng đầu,
  trống = tự động) và ảnh xem trước vùng cut (đỏ: tín hiệu, xanh lá: phần thêm ở đầu, xanh dương: pin GND giữ được),
  tính lại mỗi khi anh đổi hệ số; board không bị ghi gì.
- **Cut lại "như lần trước"** (từ 0.7.0): nói "cut lại X như lần trước" (hoặc đưa request id / đường dẫn
  `user_settings.json`, kể cả file copy từ máy khác). Claude liệt kê các lần chạy cũ của interface cho workspace này,
  trace lại trên board hiện tại và **chỉ báo khác biệt**; settings và cách xử lý 2 đầu điền sẵn từ lần trước; vẫn qua
  GATE A / B / C. `user_settings.json` (một file / request) giữ mọi thứ đã chốt: nội dung, thông số cắt, xử lý 2 đầu,
  settings — giữ file này để cut lại sau.
- **Công cụ lẻ** (từ 0.10.0, prompt `design-tools`, guide `design_tools`): trên một `.aedb` bất kỳ — `design_read`,
  `design_setup`, `design_sweep`, `design_airbox`, `design_ports` (coax port `<refdes>.<pin>.<net>`),
  `design_solder_ball`. Mặc định làm trên bản copy `<tên>_<thao tác>_<giờ>.aedb`; sửa tại chỗ chỉ khi anh đồng ý (có
  backup). Mỗi thao tác đọc lại và ghi báo cáo `<kết quả>.design_tools.md` (cũ → mới, bỏ qua, đọc lại).
- **Danh mục tool + workflow** (từ 0.11.0; tên mới từ 2.0.0, prompt `catalog`, guide `catalog`): mỗi tool có
  mức an toàn (chỉ đọc / tạo bản copy / sửa file gốc / sửa workspace / chạy remote; 3 mức sau luôn cần anh đồng ý, khoá
  trong server). Mỗi quy trình là một **workflow** (file Markdown liệt kê các bước + điểm dừng chờ duyệt).
  Workflow nhóm: thư mục `workflows\` của repo (interface-sim, re-cut, re-apply, layout-review, pidc-report, layout-edit,
  design-tools, cut-sweep-merge). Workflow cá nhân: `%USERPROFILE%\.aedt_copilot\workflows\` (biến môi trường
  `AEDT_COPILOT_WORKFLOWS`; Claude lưu khi anh yêu cầu; trùng tên với workflow nhóm thì hiện cả hai, không ghi đè).
  File cá nhân lưu trước 2.0.0 ở thư mục cũ vẫn được đọc, không bị sửa / xoá. Hỏi "bạn làm được gì" → bảng workflow +
  tool (`list_workflows`, `list_tools`).
  Tool ghép được: `design_trace`, `design_end_check`, `design_check` (chỉ đọc), `design_cutout` (cắt 1 channel từ bản
  copy của board ra `<thư mục board>\Ansys AEDT Copilot\design_tools\`), `design_cleanup` (dọn GND), `design_merge`
  (gộp design vào workspace, backup trước, cần đồng ý).
  Từ 0.11.2 luật này khoá bằng code: tool nào thiếu trong danh mục (hoặc thiếu cờ đồng ý / contract) thì server không
  khởi động. Người phát triển thêm tool mới: dùng `@tool()` + thêm mục vào `aedt_copilot/catalog/tools.py` + contract.
- **Review layout dạng số liệu** (từ 0.12.0, guide `review_measure`): "review layout U14-U26 net CPHY_*" (hoặc một
  check: "via stub của net X") trên board hoặc design đã cắt → mỗi check chỉ OK / NOT OK theo ngưỡng (từ 4.0.0 không
  còn mức nặng nhẹ; Claude không đánh giá lỗi thay anh); HTML chỉ khi anh yêu cầu. Kết quả lưu thành bản ghi cạnh
  board (`Ansys AEDT Copilot\reviews\`) với số điểm NOT OK từng channel.
- **Review + đồng ý trước khi cắt** (025 / 3.0.0 / 4.0.0): trong interface simulation, review chạy ngay sau khi trace
  channel và luôn có file review HTML. Claude chỉ trả lời 3 phần do tool viết sẵn: ảnh vùng cut dự tính (mỗi đầu một
  dòng), file review, câu "Đọc review rồi xác nhận cut <channel>?". Anh đọc report và quyết định 100 %; lời đồng ý
  được ghi lại cùng review đó. Review độc lập trước đó của cùng board / channel được dùng lại nếu board chưa đổi.
- **Netlist schematic** (4.0.0): đưa netlist xuất từ Altium (Protel 2.0) hoặc Allegro vào `isim_start` → code đọc kết
  nối + giá trị linh kiện, so với board theo chân (off-page đổi tên, đảo chân tụ / điện trở không còn bị báo khác).
- **Sửa settings sau khi apply** (từ 0.9.0): chỉ nhóm simulation (setup, sweep, airbox, convergence, arc step) sửa
  được — Claude backup design cũ (`final\<interface>_old_<giờ>.aedb`), chỉ ghi lại setup / sweep / airbox, tự kiểm tra
  và so hình học với lần trước; vẫn cần "đồng ý" (GATE B). Nhóm cut (cutout, series, cleanup, port, solder ball, xử lý
  đầu) đã khoá: muốn đổi phải cut lại. Interface đã merge → merge lại thành design mới (`_v2`).
- **Form settings đầy đủ** (từ 0.8.0): ở GATE B Claude hiện một form, mỗi interface một tab, đủ mọi thông số của
  template theo nhóm (cutout / cleanup / series / port / solder ball / setup / sweep / airbox), dòng khoá (cutout.*,
  series.keep) chỉ xem; nút **Set default** (tab / mọi tab) đưa về mặc định của nhóm, **Copy to all tabs**. Submit chỉ là
  dữ liệu nhập: Claude hiện bảng kết quả, chờ "đồng ý" từng interface. Client không có widget → bảng đầy đủ trong chat.
- Arc step (Setup → Advanced Meshing → circle / arc approximation): mặc định **30 deg** từ 0.11.1 (trước đó 10;
  `setup.arc_step_deg` trong `templates/autocut_template.csv`); self-check đọc lại.
  Cut lại / sửa settings của lần chạy cũ giữ arc step của lần đó (bảng settings ghi chú mặc định mới).
  Max refinement per pass mặc định **10 %** (số nguyên 1..100).

- Chạy remote (mặc định): trên server chạy PyAEDT service manager (port 17878, như skill aedt-remote-pyaedt; firewall
  mở 17878, 18000-18100, 50000-50010). Cho Claude IP server + thư mục simulation trên server (và đường dẫn share nếu
  có; không share thì tool upload qua phiên RPyC). Tool tự mở AEDT không giao diện trên server và đóng khi xong.
  Cách khác: tự mở `ansysedt.exe -grpcsrv <port>` (mode `grpc`, cần thư mục share). Cần `rpyc` (chạy lại `setup.bat`).
- Ngưỡng kiểm tra 2 đầu: `interface_sim.*` trong `templates/autocut_template.csv`.
- Dòng lệnh: `.venv\Scripts\python -m aedt_copilot isim --op=<start|trace|confirm|cut|ends|validate|apply|status|merge|run> --args=<json>`.

## Version

`VERSION` + `CHANGELOG.md` + git tag `vX.Y.Z`. Version hiện trong report HTML và tool `about`.

## Dòng lệnh (không cần Claude)

```bat
.venv\Scripts\python -m aedt_copilot inspect --board D:\b\simulation.aedt
.venv\Scripts\python -m aedt_copilot review-measure --board D:\b\simulation.aedt --channels "U14-U26:CPHY_B02DEVA_*" --html
.venv\Scripts\python -m aedt_copilot isim --op=start --args="{\"workspace\": \"D:/b/simulation.aedt\"}"
.venv\Scripts\python -m aedt_copilot design --op=read --args="{\"board\": \"D:/b/x.aedb\"}"
```

## Cấu trúc

- `aedt_copilot/` — package Python. `aedt_copilot/cut_board/` = cắt board (pyedb, cut_stage / apply_stage), review layout, merge, tô màu AEDT.
  `aedt_copilot/pi_dc/` = PI-DC report (export SIwave, `skills/`, report)
- `templates/autocut_template.csv` — **thông số mặc định** cắt board (cột Default). `templates/pidc_template.csv` — PI-DC.
  Chỉ chủ repo sửa, dùng trình soạn thảo văn bản (không mở bằng Excel)
- `config.yaml` — cấu hình riêng từng máy (phiên bản AEDT, python, gRPC port)
- `mcp_server/server.py` — MCP server `aedt_copilot`
- `guides/` — hướng dẫn quy trình cho Claude (tool `get_guide`). Thêm/sửa file `.md` = có hiệu lực ở chat mới
- `prompts/` — lệnh mẫu (MCP prompts) hiện trong menu "+" của Claude
- `tools/register_claude.py` — đăng ký / gỡ server trong Claude desktop (`--remove`)
- `tests/` — số liệu tham chiếu & kiểm tra hồi quy

Kết quả mặc định: `<thư mục board>/autocut/<channel>.aedb` (+ `report_<job>.xlsx`, `_jobs/<job>/` log).
Board gốc không bị sửa.
