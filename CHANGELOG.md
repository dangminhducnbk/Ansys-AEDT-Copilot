# Changelog

## 5.7.0 (2026-11-19) — Repo public cho team + kiểm tra trước commit / push + hướng dẫn cài cho AI IDE (046)
**Cần chạy lại `setup.bat`** (đăng ký MCP cho Claude Code). Repo mới (public):
`https://github.com/dangminhducnbk/Ansys-AEDT-Copilot` — ai đã clone repo private cũ: clone lại repo này.
- `INSTALL.md` (tiếng Anh, viết cho AI IDE): kiểm tra điều kiện, `setup.bat`, đăng ký MCP từng client, kiểm tra,
  cập nhật, gỡ, lỗi hay gặp. `AGENTS.md`, `.github/copilot-instructions.md`, `CLAUDE.md` trỏ tới nó.
- `tools/register_claude.py --client desktop|code|all`, `--print` (cấu hình cho client MCP khác), `--remove`;
  `setup.bat` đăng ký Claude Code + Claude desktop (app đang chạy -> chỉ cảnh báo, không dừng).
- `tools/public_guard.py` + `.githooks/` (máy chủ repo): mỗi commit / push kiểm tra tên khách hàng, IP nội bộ,
  đường dẫn máy, file chỉ để trên máy, file nhị phân chưa duyệt, e-mail tác giả. Danh sách che chỉ nằm trên máy.
- Repo không còn chứa test (`tests/`), mock trong `specs/`, ghi chú riêng (`CLAUDE.local.md`). Tên board / net của
  khách hàng trong tài liệu, comment, spec đã thay bằng tên trung tính. Chức năng tool không đổi.

## 5.6.0 (2026-11-17) — Một trang cho mỗi request: review layout (resolve điểm NOT OK) + settings (045)
Không cần chạy lại `setup.bat`. Mở chat mới để Claude đọc guide / mô tả tool mới.
- Request mới (5.6.0): `isim_layout_review` ghi luôn TRANG DUY NHẤT `<request>/config.html` (toàn màn hình), trả M0p
  (bảng review + link), KHÔNG còn câu hỏi Q0. Mỗi channel 2 tab:
  - **Review layout**: hình vùng cut (đồng từng lớp như trang config, lớp / stackup có độ dày + điện môi), một marker
    cho mỗi điểm NOT OK (điểm gần nhau gộp, bấm để zoom), rê chuột xem tóm tắt; bấm = chi tiết y như dòng report cũ
    (section + mã REF-01..., Issue / Recommendation, hình có số đo), mặt cắt stackup tại điểm, nút "Print issue to
    image" (PNG: Issue / Layout version / Issue description, Overview khoanh điểm + mũi tên, Zoom in), Resolve (ghi
    chú tuỳ chọn) / Unresolve; "Resolve all NOT OK" cho mọi channel (xác nhận 1 lần); "Topology per pair" = khung
    routing của report; double-click hình = toàn vùng; đơn vị mil / µm / mm.
  - **Settings**: trang config 5.5.0 nguyên vẹn; khoá tới khi resolve hết điểm của channel.
  - Save (link của tool hoặc trình duyệt) chỉ mở khi resolve hết điểm mọi channel; lưu settings + resolution.
- `isim_config_check` / `isim_go` từ chối khi còn điểm chưa resolve, hoặc trang dựng từ review cũ (review đo lại ->
  trang mới, resolution cũ trùng check + net + vị trí được tick sẵn, phải Save lại). Q2 thêm dòng "N điểm NOT OK đã
  được người dùng resolve"; `_work/resolutions.json` ghi lại từng điểm.
- `isim_review_answer` chỉ dùng cho request 5.2–5.5 (có Q0); request cũ chạy như trước.
- Topology per pair (report review + trang): linh kiện nối tiếp của chính cặp đó vẽ thân hình chữ nhật (không vẽ của
  cặp khác); mặt cắt ghi "<refdes>" / "<giá trị> - <package>" (vd. "C951" / "220nF - 0402", giá trị từ netlist hoặc
  board) ở hàng nhãn dưới hình.
- Dữ liệu trang config có thêm stackup board (đọc trong phiên EDB sẵn có); trang config cũ: chạy lại để có.

## 5.5.0 (2026-11-17) — Trang config: trace mọi pad trong top view + 3D, thanh trượt port (044)
Không cần chạy lại `setup.bat`, không cần khởi động lại Claude. Trang config đã tạo trước bản này: chạy lại
`isim_config` để có trace lớp trong.
- Trace: ngoài trace trên lớp đặt linh kiện (5.3.0), trang config lấy thêm trace ở LỚP TRONG đi ra từ via nằm trong pad
  tín hiệu (via-in-pad, chân xuyên lỗ), nối tiếp các đoạn path cùng net / lớp đến hết khung hình (vd. J25 BOARDA:
  Layer 14). Top view: lớp đặt linh kiện nét liền, lớp trong nét đứt mỗi lớp một màu, chú thích "Trace <lớp> (via in
  pad)". 3D: trace lớp đặt linh kiện trên mặt board, trace lớp trong trên một mặt phẳng dưới board (tượng trưng, không
  đúng độ sâu), đoạn thẳng đứng ở via.
- Thanh trượt vị trí port: phần màu chạy theo con trỏ (lúc mở trang, khi kéo, khi bấm nút nhanh).

## 5.4.1 (2026-11-17) — Ảnh review: mỗi loại lỗi một kiểu khung (043)
Không cần chạy lại `setup.bat`, không cần khởi động lại Claude.
- Ảnh tham chiếu (một panel mỗi lớp GND) của một điểm có nhiều lỗi trước đây vẽ các khung hồng nét đứt giống hệt nhau
  (vd. PCIE_HSA2HSB_L1_N: Loss of reference + Near plane edge -> trông như "khoanh 2 lần"). Nay mỗi loại lỗi một màu +
  kiểu nét: Loss of reference hồng nét đứt (như cũ), Near plane edge cam chấm, SOV tím gạch-chấm, Ref to other net nâu
  gạch dài, Trace over via clearance xanh gạch ngắn (luật khác: danh sách dự phòng). Khung loại thứ 2, 3… vẽ lệch ra
  ngoài một chút để không chồng lên nhau. Chú thích dưới ảnh ghi từng loại "<lỗi> (<kiểu> frame)". Số điểm / số lỗi
  không đổi.

## 5.4.0 (2026-11-16) — File gộp = bản copy board gốc + các channel, kiểm stackup (042)
Không cần chạy lại `setup.bat`. Mở chat mới để Claude đọc guide mới.
- `isim_go`: project gộp `<request>/<request_id>.aedt` nay là BẢN COPY project board của người dùng (`.aedt` + `.aedb`;
  board chỉ có `.aedb` -> copy `.aedb`), thêm mỗi channel thành 1 design mới. Design của board giữ nguyên; file gốc chỉ
  được đọc (bỏ qua `.lock`, `edb.def.tmp`, `edb.def+`, `edb.def.bak`, `stride/`). Thư mục request nặng thêm bằng board.
- Lỗi 5.0.0–5.3.0: gộp vào project RỖNG làm linh kiện nối tiếp RLC (vd. tụ 0 Ω C951 / C958 / C959 / C1015 của
  PCIE_U14_J25) mất pin -> AEDT Validation Check treo. Gộp vào bản copy board giữ đủ pin (Validation 32 s). Request
  cũ có linh kiện nối tiếp: chạy lại `isim_go`; project gộp cũ được chuyển vào `_work/history/` (không xoá).
- Stackup: đọc stackup board lúc cut; self-check mục "stackup = board" (thứ tự lớp, tên, loại, độ dày ± 0.01 µm, vật
  liệu, vật liệu lấp, εr / tanδ / độ dẫn). Sau khi gộp, đọc lại từng design: linh kiện / pin = design channel,
  stackup = board; khác -> channel "merge error" + từng dòng khác. M3: cột "Stackup = board", dòng "Board copy".
- `isim_merge` / `design_merge` (gộp vào project người dùng chọn): cũng đọc lại design sau khi gộp (pin, stackup so với
  channel).

## 5.3.0 (2026-11-16) — Thanh trượt vị trí port + trace trên trang config (041, mở rộng)
Không cần chạy lại `setup.bat`. Mở chat mới để Claude đọc guide mới.
- Trang config, tab Solder Ball Properties: mục "Port location" thành thanh trượt 0–100 % (một giá trị cho mọi pad
  tín hiệu của đầu): 0 % = sát đầu pad phía thân, 50 % = tâm pad (vị trí pin), 100 % = sát đầu pad phía ngoài. Port
  tròn Ø = bề rộng pad, tâm đi từ W/2 đến L − W/2 (pad 10 × 2 mm: 1 → 9 mm). Nút nhanh Body-side end / Pad centre /
  Outer end; dòng khoảng cách tâm port theo từng cỡ pad (mm + mil). Pad vuông / tròn: không trượt, giữ tâm.
- Hình top view của đầu linh kiện vẽ thêm trace nối vào pad (lớp đặt linh kiện) để thấy trace tới từ hướng nào.
- Hướng luôn theo thân linh kiện khi đã chọn (cả pad có trace). Giá trị 5.2.0 đã lưu: `end` = 0 %, `centre` = 50 %.
  Pad có trace đi VÀO phía thân (hiếm) với `end`: port nay ở đầu phía thân đúng như tên (5.2.0: đầu đối diện trace).
- Self-check "<refdes> port location (<pct> %)": đọc lại từng pin tín hiệu, so với vị trí yêu cầu (± 1 µm).
  `metrics.port_location` thêm `pct` + `targets` (pin, vị trí, khoảng cách từ đầu pad phía thân).
- Không có lựa chọn riêng cho đầu (tool bước, request cũ): như cũ.

## 5.2.0 (2026-11-16) — Review trước config (039) + vị trí port đúng lựa chọn (041)
Không cần chạy lại `setup.bat`. Cần khởi động lại Claude / mở chat mới (2 tool mới, guide, prompt đổi).
- 039: sau `isim_trace`, `isim_layout_review` đo review mọi channel -> M0 (bảng Channel / file review / số điểm
  NOT OK) + Q0 "Review layout ổn, chuyển sang bước config không? / Is the layout review OK, go on to config?".
  `isim_review_answer` (cờ `user_answered_review` + lời người dùng): "không" -> request DỪNG (M0x), config / check /
  go bị từ chối; "đồng ý" -> lưu lời đồng ý gắn với các review đã gửi rồi ghi trang config (M1). Một câu trả lời cho
  mọi channel. Review đổi (board đổi / đo lại) trước config -> phải review lại. Q2 ghi "review updated" khi review đo
  lại do nội dung đổi trong trang config. Request tạo trước 5.2.0: như cũ (không Q0). 60 tool.
- 041 (bug J25, báo cáo test 2026-11-16): `port_location = end` bị bỏ qua với pad có via-in-pad / không có trace
  trên lớp pad. Nay "end" dời MỌI pin tín hiệu về đầu pad phía thân (pad không có trace: theo trục dài, về tâm thân);
  "centre" = tâm pad (vị trí pin, via không phải port). Pad không xác định được đầu (vuông / tròn / nằm trên trục
  thân) -> giữ tâm + cảnh báo. `result.json` `metrics.port_location` từng đầu (yêu cầu, số pin dời, pin không dời
  + lý do); self-check thêm mục "<refdes> port location" (đọc lại vị trí pin so với tâm pad gốc). Trang config: vị
  trí port xem trước do tool tính (cùng hàm với lúc dựng), nhãn "Pad centre (pin position)", mặc định "centre" cho
  đầu có via-in-pad (= kết quả trước đây). Không có lựa chọn riêng cho đầu (tool bước / request cũ): như cũ.
- Constitution Nguyên tắc I: quy trình cố định nay có thêm lời đồng ý Q0 (khoá trong code) — chủ repo cập nhật câu
  chữ nếu cần.

## 5.1.0 (2026-11-16) — Save của config.html ghi đè thẳng file, không chọn đường dẫn (feature 040)
Không cần chạy lại `setup.bat`. Cần khởi động lại Claude / mở chat mới (guide đổi; MCP server nạp code mới).
- `isim_config` bật dịch vụ lưu cục bộ (chỉ 127.0.0.1, cổng 17880, bận thì +1..+9; `config.yaml` `config_port`
  tuỳ chọn), tự tắt sau 8 h không dùng; kết quả thêm `config_url`; M1 = link + đường dẫn file (VI + EN).
- Trang mở từ link: Save gửi settings, tool dựng lại và ghi đè `<request>/config.html` (file tạm + replace). Đường
  dẫn do tool lấy từ request, không lấy từ trang; link có mã riêng mỗi request; chỉ nhận JSON; trang chỉ đọc / trang
  cũ hơn file trên đĩa / tên folder sai -> từ chối. Bấm Save hai lần liên tiếp chỉ gửi một lần.
- Tool không chạy -> trang báo "Cannot reach the tool" và lưu kiểu 038 (hộp chọn file / Downloads).
- CLI nội bộ `config-serve`. Không thêm MCP tool.

## 5.0.0 (2026-11-16) — MAJOR: quy trình cut cố định, trang config HTML, một lời đồng ý, thư mục theo channel (feature 038)
Không cần chạy lại `setup.bat`. Cần khởi động lại Claude / mở chat mới (3 tool mới, guide, prompt đổi).
- Quy trình cố định cho MỌI lần cut (guide `interface_sim` mục 0): `isim_start` -> `isim_trace` -> `isim_config`
  (M1) -> người dùng sửa trang, Save, trả lời "xong" / "done" -> `isim_config_check` (M2 lỗi, hoặc Q2 kèm vùng cut +
  file review mọi channel) -> "đồng ý" / "yes" -> `isim_go` (cut + đo 2 đầu + dựng design + gộp, M3). Chỉ 2 câu hỏi
  (Q1 đã config xong chưa?, Q2 đồng ý cut không?), mọi câu tiếng Việt + tiếng Anh, do tool viết sẵn (dán nguyên văn).
  Không hỏi chạy simulation.
- Trang `config.html` (theo mock đã duyệt): Content (2 đầu, nhóm vi sai, linh kiện nối tiếp, khác biệt schematic,
  trường hợp lạ ở 2 đầu, ghi chú), Auto Generate Extent (kiểu + hệ số 0.02-0.20, bảng net, hình layout thật từng
  lớp + vùng cut CUỐI tính sẵn bằng AEDT cho mọi bước, bảng lớp, zoom, Advanced), Component Model (mỗi đầu: Top view +
  3D, die, solder ball theo tỉ lệ pad, port giữa pad / cuối pad), Analysis Setup (Single / Multi-Frequencies, refine,
  basis, via 3D, ΔZo; sweep nhiều dải Linear Step / Count / Log, Interpolating / Discrete, Q3D DC), Set HFSS Model
  Extents (dielectric + airbox, Sync, hình top + 3D), ô bắt buộc "Channel folder". Save: Chrome / Edge ghi đè file
  (chọn file config.html lần đầu), trình duyệt khác tải về (tool tìm trong Downloads).
- Thư mục request mới: `<board>_<thời gian>/` = project gộp `<request>.aedt` + `.aedb` (project MỚI, workspace của
  người dùng không bị ghi), `config.html`, `request.md`, mỗi channel một thư mục (tên do người dùng nhập) gồm
  `<tên>.aedb`, `<tên>.aedt`, `review.html`, `config.html` (bản ghi chỉ đọc), `_work/` (file nội bộ). Request cũ đọc
  như trước.
- Template thêm hàng (mặc định = như cũ): `setup.solution_mode`, `setup.multi_freqs`, `setup.multi_max_passes`,
  `setup.via_mesh_3d`, `setup.via_num_sides`, `sweep.use_q3d_dc`, `sweep.ranges`, `airbox.z_sync`,
  `airbox.dielectric_horizontal`, `component.*` (die, vị trí port, `component.model` mỗi đầu).
- Tool bước cũ (GATE A-D) giữ nguyên cho request cũ / khi người dùng yêu cầu từng bước.
- Constitution 2.1.0 (chủ repo đồng ý 2026-11-16): Nguyên tắc I = quy trình cố định có một lời đồng ý (`isim_go`,
  cờ `user_approved_cut` + lời người dùng, gắn với config đã check); tool thủ công / phục hồi giữ gate A-D.

## 4.1.0 (2026-11-15) — sửa review sau lần test 4.0.0 (feature 037)
Không cần chạy lại `setup.bat`. Cần khởi động lại Claude / mở chat mới (guide, luật review đổi).
- Mặt cắt trong khung cặp ("Signal routing per pair") đi tới đúng chân cuối: ở chỗ dây gãy khúc dày (đoạn thẳng xen
  cung ngắn) lấy đầu đoạn GẦN NHẤT thay vì đầu đầu tiên trong 0.3 mm; không dừng ở chân khi trace còn đoạn đi tiếp vào
  tâm pad (trước đây mất via blind trong pad J25). Chỉ là hình vẽ: chiều dài / via stub không đổi.
- Pair gap: chỗ tách cặp có điểm giữa nằm trong thân linh kiện BGA ở đầu kênh là breakout cố ý, không còn NOT OK.
  Key mới `review.bga_breakout_margin_mm` (mặc định 0); số chỗ bỏ qua ghi ở dữ liệu `skipped_in_bga`.
- Pair skew: chỉ báo chiều dài P / N (skew cho phép tuỳ spec từng interface, người dùng tự biết): không ngưỡng, không
  OK / NOT OK, không khuyến nghị. Bỏ key `review.pair_skew_mm`. Bảng chiều dài trong khung cặp: Total = trace + via,
  thêm cột Vias.
- Bản ghi review 4.0.0 không dùng lại (schema 5: đo lại 1 lần). Kết quả cut không đổi.

## 4.0.0 (2026-11-15) — MAJOR: review chỉ OK / NOT OK, câu trả lời do tool viết, netlist schematic (feature 036)
Không cần chạy lại `setup.bat`. Cần khởi động lại Claude / mở chat mới (tool, guide, prompt, luật review đổi).
- BỎ HẲN mức HIGH / MEDIUM / INFO: mỗi luật review chỉ cho OK / NOT OK theo ngưỡng (trước là INFO -> nay OK, chỉ là
  dữ liệu, không liệt kê). Kết quả tool / bản ghi review / lời đồng ý ở GATE A ghi số điểm NOT OK (+ theo từng check).
  Claude không đánh giá, xếp hạng hay hạ mức lỗi; người dùng chịu trách nhiệm 100 %. Report HTML không đổi nội dung
  (vốn đã OK / NOT OK), chỉ đổi thứ tự số điểm trong chú thích rê chuột.
- Câu trả lời cho một channel do TOOL viết sẵn (`answer_md` trong kết quả `isim_cut_preview` / `isim_review`): tiêu đề
  vùng cut (kích thước, diện tích), mỗi đầu 1 dòng, file review, câu hỏi của tool (nếu có), câu cuối "Đọc review rồi
  xác nhận cut <channel>?". Claude gửi ảnh + file review rồi dán nguyên văn, không thêm câu nào.
- NETLIST schematic: `isim_start(netlist=<file>)` nhận netlist Altium (Protel 2.0) hoặc Allegro / Telesis (nhận theo
  nội dung, không theo đuôi file). Code đọc kết nối + giá trị linh kiện (BOARDA: 9 339 linh kiện, 4 084 net, ~1 s);
  có netlist thì Claude không đọc PDF để lấy kết nối. Netlist của board khác bị từ chối khi trace.
- So board với schematic THEO CHÂN: off-page / block đổi tên net không còn là khác biệt (chỉ ghi `renamed`), chân PDF
  không đọc được = "chỉ có trên board" (không hỏi), đảo chân 1 / 2 của tụ / điện trở không còn báo, giá trị so theo số
  (0.22uF = 220nF). Chỉ khác biệt thật (chân nối sang net khác, net thiếu, giá trị khác) mới được hỏi.
- Linh kiện nối tiếp (tụ AC...) vẫn mặc định 0 Ω, không hỏi, không nhắc trong câu trả lời (ghi ở self-check).
- Luật review (steering `review_rules/*.md`): trường `severity` đổi thành `not ok when`; module luật dùng `RULE` thay
  `SEVERITY_RULE` (luật cá nhân cũ vẫn chạy). Bản ghi review 3.0.0 không dùng lại (schema 4: đo lại 1 lần).
  Kết quả cut không đổi.

## 3.0.0 (2026-11-14) — MAJOR: người dùng đọc review rồi tự quyết định cut; quy trình ngắn, chuẩn (feature 035)
Không cần chạy lại `setup.bat`. Cần khởi động lại Claude / mở chat mới (tool, guide, prompt đổi).
- Yêu cầu một channel -> Claude chỉ trả 3 phần: ảnh VÙNG CUT CUỐI (phần tăng thêm ở đầu đã gộp, 1 đường viền xanh;
  mỗi đầu 1 dòng: factor, GND giữ được), FILE REVIEW HTML (luôn được tạo), và 1 câu hỏi "Đọc review rồi xác nhận cut?".
  Không còn bảng nội dung / danh sách lỗi trong chat trừ khi hỏi.
- Một lần "đồng ý" = GATE A: xác nhận nội dung + vùng cut + review. Tool ghi lời đồng ý (giờ, file report, số HIGH /
  MEDIUM / INFO, preview) vào `user_settings.json`. GATE A bị từ chối khi chưa có review / report / preview; cut bị từ
  chối khi chưa có lời đồng ý. Board lưu lại / đổi net -> phải review và đồng ý lại.
- BỎ gate theo mức lỗi: không còn STOP / CONTINUE (chat, report HTML, cột trạng thái). HIGH / MEDIUM chỉ là thông
  tin; quyết định 100 % của người dùng.
- BỎ tool `isim_review_decide`, `isim_review_override`, `design_review_decide` (và lệnh CLI `review-decide`, cờ
  `user_approved_review_override`). Request cũ: override / quyết định cũ chỉ hiện làm lịch sử, không thay lời đồng ý.
- Sau khi cut: bước settings LUÔN là bảng nhập (form `isim_settings_form`, mỗi interface một tab, sweep để trống);
  không hỏi từng giá trị. Kết quả `isim_cut` / `isim_check_ends` có trường `next` chỉ tới form.
- Ảnh chi tiết cũ (vùng nền + phần thêm + net khác) vẫn có: `cut_detail.png` + ảnh zoom từng đầu (khi hỏi về factor).
- Bản ghi review 2.12.0 không được dùng lại (schema 3; đo lại 1 lần, vài giây trên snapshot). Kết quả cut không đổi.

## 2.12.0 (2026-11-14) — layout review nhận đúng cặp vi sai có tên net kết thúc bằng `*` (feature 034)
Không cần chạy lại `setup.bat`, không cần khởi động lại Claude (chỉ đổi code Python). Kết quả review thay đổi trên
board có tên net kiểu `X_P*` / `X_N*` (phía tụ AC, vd SERLINK).
- Trước: cặp mà net phía linh kiện đầu có `*` bị coi là 2 trace single-ended -> so với độ rộng SE (báo sai "Width vs
  stackup") và bị bỏ qua ở pair skew / pair gap / coupling / gap vs stackup.
- Sau: bỏ `*` cuối khi ghép cặp; mọi check theo cặp và routing view dùng chung 1 danh sách cặp. SERLINK (bản copy
  test1, có bảng stackup FAB): U14_U15 nhận 4/4 cặp (trước 2/4), "Width vs stackup" 8 -> 0 (MEDIUM 16 -> 8);
  U14_J8 nhận 2/2 cặp (trước 0/2), skew 0.024 / 0.011 mm (OK), không thêm lỗi; U14_U227 không đổi.
- PCIe (test1): thêm 2 HIGH pair skew THẬT trước đây bị bỏ sót (PCIE_HSA2HSB_L0 0.917 mm, L1 1.244 mm > 0.127);
  channel vốn đã STOP. Cắt không đổi.
- Gate A (đề xuất nội dung interface) và cắt không đổi.
- Bản ghi review cũ (2.11.x) không được dùng lại nữa (đo lại 1 lần, vài giây trên snapshot).

## 2.11.4 (2026-11-14) — sửa theo góp ý user: ảnh review sắc nét (feature 033, R12, demo đã duyệt)
Không cần chạy lại `setup.bat`, không cần khởi động lại Claude (chỉ đổi code Python).
- Ảnh có đồng plane trong báo cáo review (panel tham chiếu SOV / loss of reference / ref to other net / via clearance
  / plane edge, ảnh zoom) vẽ đồng bằng vector: đường bao và lỗ void thật của đồng GND (cung = dây cung mịn), cắt theo
  khung ảnh; đồng net khác cũng vậy. Không còn mép bậc thang, phóng to vẫn sắc; file HTML nhỏ hơn (SERLINK 650 → 413 KB).
- Số lỗi / số đo không đổi (chỉ đổi cách vẽ). Không đọc được hình đồng thì ảnh vẽ lưới như cũ.

## 2.11.3 (2026-11-14) — sửa theo góp ý user cho báo cáo review 2.11.2 (feature 033, R11)
Không cần chạy lại `setup.bat`, không cần khởi động lại Claude (chỉ đổi code Python).
- Ảnh serpentine, khung Detail A: chữ "W = …" không còn chồng lên "c = …" (SERLINK: 6 / 10 ảnh bị chồng). Mỗi giá trị
  W / A / G / c tìm chỗ trống cạnh chính kích thước của nó (W: phía bên kia mũi tên hoặc cao hơn); bề rộng chữ đậm ước
  lượng đúng hơn. Kiểm tra trên trình duyệt: 10 ảnh x 3 đơn vị, 0 chỗ chồng, 0 chữ ra ngoài khung.
- Số đo không đổi: SERLINK (bản copy test1) U14_U15 16 MEDIUM / 37 INFO, U14_J8 6 / 15, U14_U227 4 / 9.

## 2.11.2 (2026-11-13) — góp ý user cho báo cáo review 2.11.1 (feature 033, R6–R10, demo đã duyệt)
Không cần chạy lại `setup.bat`, không cần khởi động lại Claude (chỉ đổi code Python).
- Ảnh serpentine theo kiểu bản vẽ cơ khí: ảnh tổng của cặp chỉ khoanh bướu được đo bằng vòng tròn gạch "A" (không
  số); khung "Detail A (xN)" phóng to bướu đó và ghi kích thước: đường gióng vuông góc cạnh đo, đường kích thước mũi
  tên 2 đầu, giá trị kèm đơn vị; W hẹp thì mũi tên ngoài chỉ vào; A và G đo mép–mép (số không đổi); c = chiều dài
  cạnh vát 45° theo đường tâm, ghi song song cạnh vát; đường tâm dây gạch–chấm.
- Nút đổi đơn vị mil / µm / mm ở đầu report (mặc định mil, trình duyệt nhớ lựa chọn): đổi MỌI độ dài (ảnh
  serpentine, mặt cắt, bảng chiều dài, Location, câu Issue / Recommendation). Không đổi: diện tích mm², góc, %,
  tên via `<pad>D<hole>` (mil). Không có JS: hiện mil.
- Số đo không đổi: SERLINK (bản copy test1) số lỗi và A / G / W giống 2.11.1.
- Chi tiết: `specs/033-review-report-redesign/verify-changes.md` (mục 2.11.2).

## 2.11.1 (2026-11-12) — sửa theo góp ý user cho báo cáo review 2.11.0 (feature 033, R1–R5)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (steering luật `serpentine` đổi).
- Ảnh serpentine: mũi tên đo mảnh, đầu mũi tên nhỏ (≤ 1/3 mũi tên), nhãn A / G / c / W có viền trắng và không chồng
  nhau; G chọn cặp đoạn xa mũi tên A; c có đường gióng tới 2 đầu cạnh vát. Đầu mũi tên chỉ đúng điểm đo.
- Đo serpentine: chỗ 2 dây tách để vào chân / via (fan-out) không còn bị tính là bướu. SERLINK_DEVA2DEVB_L0_P
  (Layer 5): 3 bướu, A 0.571 mm → 2 bướu, A 0.425 mm (vẫn NOT OK). Số serpentine không đổi (SERLINK 10, PCIe 2).
- Khung đi dây từng cặp: refdes linh kiện 2 đầu và linh kiện nối tiếp kèm lớp đặt, vd. "U14 (Top)", "J8 (Bottom)".
- Mặt cắt ngang: mỗi via có nhãn loại (Through / Blind / Buried / Micro / Stacked, kèm "backdrilled" nếu khoan)
  và kích thước `<pad>D<hole>` mil (vd. "Blind Top–L5 18D6"); chân connector xuyên lỗ ghi "TH pin"; có dòng chú thích.
- Chi tiết: `specs/033-review-report-redesign/verify-changes.md` (mục 2.11.1).

## 2.11.0 (2026-11-12) — báo cáo layout review mới: tab mỗi connection, OK / NOT OK, đi dây từng cặp, luật serpentine (feature 033)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide `review_measure` và steering các luật đổi; luật mới
`serpentine`, bỏ luật `via_count`).
- Báo cáo HTML ngắn: header 3 dòng (Layout version, Review gate verdict, Review date), mỗi connection một tab (đo một
  lần). Chỉ còn OK (xanh) / NOT OK (đỏ); không còn HIGH / MEDIUM / INFO, không còn "Reference data", thanh link,
  dòng Overall. Summary: Routing, Reference, Trace stub, Via, Stackup. Mỗi mục: danh sách check (lấy từ file luật),
  bảng chỉ các dòng NOT OK với 2 dòng Issue / Recommendation (lấy từ file luật).
- Ảnh: chỗ lỗi = khung / vòng hồng nét đứt, bỏ chú thích màu, thêm dòng Location (X, Y mm).
- 2.1 Routing: mỗi cặp / bộ 3 một khung thu gọn: hình nhìn từ trên (P đậm / N nhạt, màu theo lớp, linh kiện đầu và
  linh kiện nối tiếp với pad thật, zoom khoá / mở), mặt cắt từ chân đầu đến chân cuối (via, stub, backdrill), bảng
  chiều dài theo lớp.
- Luật mới `serpentine` (mục Routing, MEDIUM): G ≥ 3H, A ≤ 3W, không góc 90°, cạnh vát 45° ≥ 1.5W (dung sai 5 %);
  ngưỡng `review.serp_*` trong template. `pair_gap` bỏ chỗ tách nằm trong serpentine của cùng cặp. Bỏ luật
  `via_count` (số via xem ở mặt cắt) và hàng template `review.via_count_max`.
- Gate review (025) và kết quả JSON giữ nguyên mức HIGH / MEDIUM / INFO.
- Kết quả thay đổi có chủ đích: SERLINK Serpentine 10, Pair gap 3 → 1, Via count 12 → 0; PCIe MEDIUM 16 → 14
  (−4 via count, +2 serpentine); board1 không đổi. Chi tiết: `specs/033-review-report-redesign/verify-changes.md`.

## 2.10.0 (2026-11-11) — review tham chiếu chính xác hơn, ảnh mỗi lớp plane một khung (feature 032)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (luật mới `via_clearance`, steering `sov` / `loss_of_reference` /
`plane_edge` đổi).
- Trace đi trong void clearance (antipad) của via KHÔNG còn bị báo mất tham chiếu: via cùng net (trace vào chính via
  của nó) → không báo; via net khác → INFO "Trace over via clearance" (luật mới `via_clearance`, không chặn cut). Khe
  thật trên plane vẫn HIGH / MEDIUM như cũ; void quanh lỗ không có net (lỗ cơ khí) vẫn là khe thật.
- Một đoạn = một lỗi: không còn "Loss of reference" + "SOV" lớp trên + "SOV" lớp dưới cho cùng một đoạn; "Near plane
  edge" cũng gộp các lớp plane vào một lỗi.
- Ảnh lỗi tham chiếu: mỗi lớp plane một khung đặt cạnh nhau (tên lớp, màu riêng), đoạn thiếu tham chiếu tô viền cam
  dọc theo đoạn, via của clearance khoanh vòng, khung nhìn rộng hơn.
- Kết quả thay đổi có chủ đích: test1 SERLINK U14_J8 12 HIGH → 0; PCIe 21 / 57 / 25 → 5 / 16 / 45 (LoR 19 → 3);
  danh sách từng điểm: `specs/032-review-reference-accuracy/verify-changes.md`.

## 2.9.0 (2026-11-11) — mỗi luật review một file (feature 031)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tool mới `review_rules`, guide `review_measure` rút gọn).
- Mỗi luật layout review có file hướng dẫn riêng `review_rules/<id>.md` (luật kiểm tra gì, ngưỡng dùng, mức, vì sao,
  cách sửa, cách trao đổi) và, nếu luật đo, file code riêng `aedt_copilot/review_checks/<id>.py`. Sửa một luật = sửa
  file của nó. Câu Why / Fix, tiêu đề, mục báo cáo lấy từ file hướng dẫn (một nguồn).
- `reference` tách thành `sov`, `ref_other_net`, `loss_of_reference`; `vias` thành `ref_plane_change`, `via_stub`,
  `nearest_gnd_via` (đo chung một lần, số liệu và tốc độ như cũ). `checks="reference"` / `"vias"` vẫn dùng được.
- Tool mới `review_rules`: liệt kê luật, đọc hướng dẫn của một luật, bật / tắt code của luật CÁ NHÂN (thư mục
  `~/.aedt_copilot/review_rules` hoặc biến `AEDT_COPILOT_REVIEW_RULES`; trùng id với luật team → dùng luật team; code
  cá nhân chỉ chạy khi người dùng bật). Luật không có code: Claude tự đánh giá khi được hỏi, không chặn cut.
- Guide `review_measure` chỉ còn quy trình + bảng luật tự sinh. Kết quả review và báo cáo HTML giống hệt 2.8.0
  (board1, test1). Review cũ của 2.8.0 sẽ được đo lại một lần (danh sách luật đổi).

## 2.8.0 (2026-11-11) — layout_region đọc layout snapshot (feature 029)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide `layout_edit` đổi).
- `layout_region` đọc board từ layout snapshot: kết quả GIỐNG HỆT đọc live (id, toạ độ từng số, `region.json`, ảnh
  PNG từng byte). Lần đầu trên một board dựng snapshot CẢ BOARD (mở board chỉ đọc một lần), các box sau không mở board:
  B04 đọc vùng 19–43 s → 1,8–2,9 s (dựng lần đầu 24–28 s, 36 MB); board1 85–88 s → 3,9–4,3 s (dựng 130 s, 237 MB).
- `layout_edit` lấy vùng "trước" từ snapshot của board nguồn khi đã có (không dựng trong lúc sửa): B04 stitch / neck
  read_before 28,4 → 4,7 s / 16,1 → 2,6 s; `result.json` / `changes.json` giống hệt 2.6.1. Đọc "sau" + kiểm tra vẫn live.
- Kết quả có `source` / `before_source` (snapshot dùng lại / dựng mới, hoặc live + lý do). Board đang mở trong AEDT:
  snapshot hợp lệ vẫn dùng; cần dựng → đọc live + ghi chú (không đụng `.lock`).
- Định dạng snapshot schema 2 (lưu điểm gốc EDB kể cả cung, bảng padstack, khung linh kiện): snapshot cũ tự dựng lại
  một lần khi dùng. Dòng template mới `snapshot.use_for_region` (mặc định true; false = đọc live như trước).

## 2.7.0 (2026-11-11) — 6 luật review mới + bảng stackup (feature 030)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tool mới `review_stackup_table`, guide `review_measure`).
- Mọi review (kể cả review bắt buộc trước khi cut) chạy thêm 6 luật, mỗi luật một file trong `review_checks/`:
  1 lệch chiều dài trong cặp / bộ 3 > 0.127 mm (5 mil) = **HIGH** (dừng ở review gate); 2 cặp vi sai tách xa (khe >
  1.5 × khe danh định, ≥ 0.5 mm); 3 chạy song song với net khác gần hơn 3 × bề rộng trên ≥ 2.5 mm; 4 trace gần mép
  plane / void tham chiếu (< 3 × chiều dày điện môi, tối thiểu 0.2 mm; bỏ qua antipad ≤ 2 mm); 5 > 2 via mỗi net hoặc
  cặp / bộ 3 khác số via; 6 bề rộng trace và khe cặp so với bảng stackup (lệch > ±0.01 mm). Luật 2–6 = MEDIUM / INFO.
- Ngưỡng = 11 dòng template `review.*` mới (sửa trong `templates/autocut_template.csv`).
- Bảng stackup: người dùng đưa file stackup của nhà máy (PDF / Excel), Claude đọc ra bảng width / gap theo lớp, người
  dùng xác nhận, tool mới `review_stackup_table` lưu ở `<thư mục board>/Ansys AEDT Copilot/stackup/`. Chưa có bảng →
  INFO "No stackup table". Không tính trở kháng.
- Báo cáo HTML có mục mới "Stackup" (và "Crosstalk" khi có lỗi ghép). Kết quả 4 check cũ không đổi (số thứ tự điểm có
  thể dịch vì có thêm phát hiện). test1 PCIe: thêm 2 HIGH lệch chiều dài (cặp RX 2.6 / 2.9 mm).

## 2.6.1 (2026-11-10) — thêm luật review = thêm MỘT file (feature 028)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide `review_measure` thêm mục cho developer).
- Chữ báo cáo của từng luật (tiêu đề, các dòng có nhãn, Why / Fix, ngưỡng, lớp vẽ trong ảnh, mục báo cáo) chuyển vào
  chính file luật trong `aedt_copilot/review_checks/` (`REPORT`). Báo cáo HTML của 4 luật hiện có giống hệt 2.6.0.
- Luật mới: copy `review_checks/_example.py` (mẫu, không được nạp) thành `<luật>.py` → `design_review` /
  `isim_review` đo nó và báo cáo HTML hiện nó với dòng / Why / Fix / ảnh riêng, không sửa file nào khác. Luật không
  khai báo `REPORT` → khối chung (vị trí, lớp, giá trị đo).

## 2.6.0 (2026-11-10) — báo cáo review và cut preview đọc layout snapshot; báo cáo HTML dễ đọc hơn
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide `interface_sim` / `review_measure`, about() đổi).

### 027 — layout snapshot phase 2
- Báo cáo HTML layout review (`design_review(html=true)`, `isim_review(html=true)`) dựng từ layout snapshot, không
  đọc board lần hai: board1 2 channel 94,6 s → 2,7 s. Số liệu / id / mức giống hệt bản đọc live. Header ghi
  "Board data: snapshot | live" (live + cảnh báo khi phải lùi về đọc trực tiếp).
- Cut preview (`isim_cut_preview`, GATE A) đọc board từ snapshot: pin GND 2 đầu, linh kiện, net khác, ảnh. Vùng cắt
  (extent) vẫn là của AEDT, lưu cache theo net / thông số / hệ số → preview luôn đúng bằng vùng cắt thật. Hệ số chưa
  gặp lần nào → mở board một lần rồi lưu. board1: preview lặp lại 1,4–1,7 s (đọc live 89–265 s).
- Dòng template mới `snapshot.use_for_preview` (mặc định true; false = đọc live như trước). `layout_region` vẫn đọc
  live (để feature sau).

### 026 (sửa) — báo cáo HTML dễ đọc
- Mô tả mỗi issue thành các dòng có nhãn: tiêu đề + mức, Net (channel), vị trí, lớp, giá trị đo cạnh ngưỡng (✗ / ✓),
  **Why** (vì sao nguy hiểm) và **Fix** (cách sửa). Tên khoá nội bộ / id điểm chỉ còn trong hover.
- Chú thích dưới ảnh xuống dòng gọn trong ô ảnh ("Top Layer – signal", "Layer 2 - GND – GND (ref)", GND via,
  signal via, issue), không còn tràn chữ ra ngoài khung.

## 2.5.1 (2026-11-10) — sửa khoá file trên Windows (feature 024, T015)
Không cần chạy lại `setup.bat`, không cần khởi động lại Claude.
- Sửa: khoá file (`core/unique.file_lock`, dùng khi nhiều request / tiến trình ghi registry cùng lúc) đôi khi báo
  `PermissionError` trên Windows khi file khoá của tiến trình trước đang được xoá. Nay coi là "đang bận" và chờ; bị từ
  chối liên tục > 2 s mới báo lỗi quyền. Test `test_threaded_requests` 50/50 lần PASS.

## 2.5.0 (2026-11-10) — mẫu báo cáo layout review (feature 026)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide `review_measure`, about() đổi).
- Báo cáo HTML layout review (`design_review(html=true)`, `isim_review(html=true)`) theo cấu trúc cố định, giống nhau
  cho mọi board: header (board, design, ngày, version, **kết luận review gate 025** từng channel: STOP / CONTINUE /
  OVERRIDDEN) → **Summary** → mục chi tiết theo hạng mục → Reference data (thu gọn).
- Summary đầu trang: mỗi mục (Reference, Trace stub, Via, Routing; check mới = mục mới) một dòng: số issue HIGH /
  MEDIUM / INFO theo từng channel, mức nặng nhất, đánh giá nguy hiểm ("Dangerous — stop" / "Review needed" /
  "Information" / "OK — no issue"), link tới mục và tới từng dòng.
- Mỗi hạng mục một bảng 3 cột **Index / Description / Picture**, chỉ HIGH + MEDIUM (INFO đếm ở Summary, liệt kê ở
  Reference data). Index `REF-01`, `VIA-01`...; mô tả: channel, net, lớp, toạ độ, giá trị đo so với ngưỡng, lý do mức.
  Điểm có issue ở 2 hạng mục → một dòng ở mỗi bảng.
- Ảnh zoom đúng chỗ lỗi, **chỉ vẽ lớp liên quan** (trace: lớp trace + plane tham chiếu; đổi plane tại via: lớp trước /
  sau + plane hai phía; via: lớp via nối + plane), chú thích tên lớp dưới ảnh. Bỏ kiểu vẽ lớp khác nét đứt.
- Báo cáo chỉ là cách xem dữ liệu review: số liệu / id / mức không đổi (`tests/review_check.py` PASS). Thời gian tạo
  báo cáo board1 +3 %.

## 2.4.0 (2026-11-10) — review layout bắt buộc trước khi cắt (feature 025)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (2 tool mới, guide `interface_sim` / `review_measure`, workflow đổi).
- Interface simulation: `isim_review` là bước BẮT BUỘC ngay sau `isim_trace` (trước preview / GATE A), trên đề xuất
  hoặc nội dung đã chốt. Kết luận từng interface: **STOP** khi có điểm HIGH (mức cuối cùng) hoặc review không đầy đủ
  (check lỗi / không trace được), còn lại **CONTINUE**. MEDIUM / INFO chỉ báo.
- Khoá trong code (server + package): `isim_confirm_content` (GATE A) và `isim_cut` từ chối khi chưa review, review cũ
  (2 đầu / net khác, board đã lưu lại, ngưỡng đổi) hoặc STOP chưa có quyết định. Interface khác vẫn tiếp tục.
- Quyết định của kỹ sư: từng điểm (`isim_review_decide`, đổi mức phải có lý do) hoặc cả interface "vẫn cut"
  (tool mới `isim_review_override`, cờ `user_approved_review_override` + lý do, ghi `user_settings.json`). Gắn với
  đúng lần review; review mới / cut lại cần quyết định lại (`isim_recut` chỉ hiện `previous_review`).
- Mọi review đầy đủ lưu bản ghi cạnh board: `<thư mục board>/Ansys AEDT Copilot/reviews/<board>/review_<giờ>.json`
  (không ghi đè). `design_review` trả `review_file` + verdict từng channel; tool mới `design_review_decide` ghi quyết
  định vào bản ghi. Interface simulation dùng lại bản ghi khi board không đổi, cùng 2 đầu / net / đủ 4 check / cùng
  ngưỡng (`reused_from`), mang theo quyết định từng điểm, không mang override.
- `isim_status` thêm cột Review. Request cũ đã qua GATE A vẫn apply / re-apply / merge / chạy như trước; chỉ GATE A
  mới hoặc cut mới cần review. Số liệu đo của mọi check không đổi.

## 2.3.0 (2026-11-10) — connector / SMD chỉ giữ pin GND gần pin tín hiệu; tên theo giờ không bao giờ trùng
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide `interface_sim`, about() đổi). Feature 021 + 024.

### 021 — dọn pin GND ở đầu SMD / via-in-pad / connector
- Đầu được dựng lại (SMD / via-in-pad / connector) chỉ giữ pin GND riêng nằm trong
  `cleanup.smd_gnd_pin_keep_dist_mm` (mặc định 1.6 mm, giống luật BGA, sửa ở GATE B) quanh pin tín hiệu; khoảng cách
  đo tới MÉP pad GND (0 khi chồng lên). test1 PCIe: J25 64 → 32 pin GND; board1 CPHY_U21_J25: J25 84 → 30.
- Không bao giờ xoá: pin GND gần nhất của mỗi pin tín hiệu, pin / pad GND của luật 022, pad giữ theo 019, via tấm GND
  và đồng có sẵn (015).
- Đầu chỉ có MỘT pin / pad GND riêng (đường hồi thật của chip): luôn giữ, không cảnh báo, báo cáo ghi
  "<refdes>: GND duy nhất pin <n>, đã giữ". Nhiều pin GND mà pin gần nhất vẫn xa → cảnh báo như cũ.
- Báo cáo apply / self-check: pin GND trước → sau từng đầu. `design_cleanup` dùng cùng luật. Cắt lại "như lần
  trước" một request cũ: áp luật mới (hiện là thay đổi mặc định trong bảng khác biệt).

### 024 — tên / thư mục theo giờ không trùng
- **Sửa lỗi**: 2 request interface simulation bắt đầu cùng 1 giây nhận cùng id và ghi chung thư mục (2026-11-10:
  số liệu review PCIe bị trộn). Nay thư mục được tạo nguyên tử (`core/unique.py`: `claim_dir`, `claim_file`,
  `move_aside`, `file_lock`); trùng giây → `<time>_2`, `_3`. Không trùng → tên giữ nguyên như cũ (request cũ,
  `isim_previous`, re-cut không đổi). Danh sách request ghi dưới khoá file (chạy song song không mất mục).
- Áp dụng cho: bản copy / backup / thư mục cutout / merge của design tools, đổi tên `*_old_<time>` (reset, cut,
  apply, `_src`), backup re-apply, `_backup/<time>` của merge, HTML `layout_review_<time>.html`, thư mục
  `_region/<time>` và `<name>_<time>` của layout edit. Bản `_old_` cũ không bao giờ bị ghi đè.
- `about()`: thêm dòng Gate A cut form + cut preview (`isim_cut_form`, `isim_cut_preview`, luật GND đầu) và
  `layout_snapshot`.
- Dọn mã: bỏ `design_tools._common._free` (chỉ kiểm tra tồn tại, không nguyên tử) — thay bằng `claim_dir`.

## 2.2.0 (2026-11-10) — layout snapshot: review chạy lại trong vài giây
Không cần chạy lại `setup.bat`. Khởi động lại Claude (1 tool mới, guide đổi). Feature 023 (phase 1).

- **Layout snapshot** (`aedt_copilot/layout_snapshot/`): board được đọc MỘT lần ra file dưới
  `<thư mục board>/Ansys AEDT Copilot/snapshots/` (không ghi gì vào `.aedb`): chỉ mục board (stackup, net, linh kiện,
  mọi via/pin, metadata mọi primitive, diện tích GND lớn nhất mỗi lớp toàn board) + hình học cửa sổ (WKB, cung tròn
  thành dây cung ≤ 1 µm). Khoá theo `edb.def` (kích thước + mtime): board đổi → dựng lại, không bao giờ dùng bản cũ.
- **Review trên snapshot** (`design_review`, `isim_review`, CLI `review-measure`): mặc định (`review.use_snapshot` =
  true). Code đo `cut_board/review.py` giữ nguyên, chạy trên một đối tượng giả PyEDB chỉ đọc → kết quả giống hệt
  live (board1 + test1 so với golden trước thay đổi). Kết quả có `source` (snapshot / live). Primitive không chuyển
  được / board đang mở trong AEDT khi cần dựng → chạy live + cảnh báo nêu id. `snapshot="off"` = live như cũ.
  HTML (`html=true`) vẫn vẽ từ board live.
- **Tool mới `layout_snapshot`** (op build / status / list, mức an toàn read) + CLI `snapshot --op=...`; guide
  `interface_sim` bảo dựng snapshot nền ngay sau `isim_trace`; guide `review_measure` mục 2b.
- Template thêm `review.use_snapshot` (true), `snapshot.window_margin_mm` (5), `snapshot.arc_tol_um` (1).
- MCP server 54 tool.

## 2.1.2 (2026-11-10) — ảnh xem trước: net khác gạch chéo
Không cần chạy lại `setup.bat`. Feature 022 (bản vá). Vùng cut, kết quả cắt và bảng preview không đổi.

- Net khác trong phần thêm (vd plane nguồn) vẽ bằng viền xám đậm + gạch chéo xám, KHÔNG tô kín: phần "Added" vẫn
  xanh lá bên dưới (2.1.1 tô xám bán trong suốt làm phần thêm thành xám xanh). Ô chú thích "Other net" cùng kiểu
  gạch chéo.

## 2.1.1 (2026-11-10) — ảnh xem trước vùng cut ít chữ hơn
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide `interface_sim` đổi). Feature 022 (bản vá). Vùng cut,
kết quả cắt và bảng preview không đổi.

- `cut_region.png` / `end_<refdes>.png`: tiêu đề một dòng (`<interface> · W × H mm`, zoom `<interface> · <refdes>`);
  chú thích bằng ô màu ở chân ảnh cạnh thước (Signal, Base cut, Added, End region, GND pin, GND via, Other net — chỉ
  mục có trong ảnh); nhãn vùng đầu `<refdes> <hệ số>`; net khác trong phần thêm tô xám vừa (không còn số / tên trên
  ảnh — tên net và mm² thêm xem trong bảng preview).
- Khung linh kiện lớn hơn vùng vẽ (vd J25) được cắt theo mép ảnh, nhãn vẫn hiện; ảnh vẫn khớp theo vùng cut.

## 2.1.0 (2026-11-10) — cut giữ pin GND của 2 đầu; form cut + xem trước ở GATE A
Không cần chạy lại `setup.bat`. Khởi động lại Claude (2 tool mới, guide / prompt đổi). Feature 022.

- **Luật GND ở 2 đầu khi cắt** (`cut_board/end_gnd.py`, dùng cho `isim_cut` và `design_cutout`): trước khi cắt, tool
  phát hiện pin GND / exposed pad của mỗi đầu (IC / connector) trên board gốc. Cả interface cắt với hệ số của kỹ sư
  (`cutout.expansion`). Đầu có pin GND mà không pin nào nằm trọn trong vùng cut → CHỈ vùng đầu (khung pin + 1 mm)
  được mở rộng, hệ số +0.02 mỗi lần, không có mức tối đa, tới khi giữ được một pin GND / pad. Phần còn lại của vùng
  cut giữ nguyên. Via GND trong pad được giữ khi dọn GND. Phủ hết vùng đầu mà vẫn không có → lỗi hình học, không cắt.
  Đầu không có pin GND trên board → câu hỏi GND (015) như cũ; đầu có pin GND không bao giờ tới câu hỏi đó.
- Template thêm `cutout.end_expansion_step` (0.02) và `cutout.end_region_margin_mm` (1.0) — chốt ở GATE A, khoá sau
  cut.
- `isim_check_ends` / `design_end_check`: bảng "End GND rule" (pin GND trên board, hệ số nền → hệ số dùng, mm² thêm,
  pin GND giữ được, net khác trong phần thêm) + ảnh. Cut lại lần chạy trước 2.1.0: khác biệt `cut_method_changed` ở
  GATE A và `end_gnd_compare` sau cut.
- **GATE A mới**: `isim_cut_form` (form cut settings, một tab / interface, ô "end factor" cho từng đầu, "Copy to all
  tabs" không copy ô này) và `isim_cut_preview` (CHỈ ĐỌC board: bảng từng đầu + ảnh vùng cut + ảnh zoom đầu mở rộng;
  cùng hàm với cut nên vùng preview = vùng cut, `isim_cut` trả `preview_check`). Đổi giá trị → preview lại.
- **Hệ số tay từng đầu** (`content.end_factors`): dùng đúng giá trị (không tăng dần), phải còn pin GND nằm trọn, nếu
  không → lỗi và GATE A bị từ chối; lưu trong `user_settings.json`, cut lại dùng lại.
- MCP server 53 tool (+`isim_cut_form`, `isim_cut_preview`, đều mức an toàn read).

**Tham chiếu hồi quy board1 đổi CÓ CHỦ Ý** (`tests/reference/CPHY_U14_U26.json`): U26 giữ exposed pad (pin 65) nhờ
vùng đầu hệ số 0.06 → 0.16 (+59 mm²), không còn câu hỏi GND / tấm GND. U26 = 12 pin tín hiệu + pin 65; plane GND
901–923 mm² (trước 845–865); 126 via GND (trước 101, +25 via trong pad); vẫn 24 port, lệch pin 0.21 mm, self-check OK.
CPHY_U21_J25: U21 cũng giữ pin 65 (18 port). test1 PCIE_U14_J25 không đổi (2 đầu `met`, 16 port).

## 2.0.0 (2026-11-09) — BREAKING: đổi tên (bỏ ẩn dụ "kitchen")
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tên tool, guide, prompt đổi). Feature 020. Kết quả cắt / mô
phỏng / PI-DC / layout edit không đổi.

**Tên cũ → tên mới**

| Cũ | Mới |
|---|---|
| MCP `kitchen_utensils` | `list_tools` (kết quả: khoá `tools` thay `utensils`) |
| MCP `kitchen_recipes` | `list_workflows` (khoá `workflows` thay `recipes`) |
| MCP `get_recipe` | `get_workflow` |
| MCP `save_recipe` | `save_workflow` |
| guide `kitchen`, prompt `kitchen` | guide `catalog`, prompt `catalog` |
| CLI `kitchen --op=utensils\|recipes\|get\|save` | CLI `catalog --op=tools\|workflows\|get\|save` |
| package `aedt_copilot/kitchen/` (catalog.py, recipes.py) | `aedt_copilot/catalog/` (tools.py, workflows.py) |
| kind `utensil` trong danh mục | kind `tool` |
| thư mục repo `recipes/` | `workflows/` |
| bước trong file workflow `- utensil: <tool>` | `- tool: <tool>` (khoá cũ vẫn đọc được) |
| workflow cá nhân `%USERPROFILE%\.aedt_copilot\recipes` (env `AEDT_COPILOT_RECIPES`) | `%USERPROFILE%\.aedt_copilot\workflows` (env `AEDT_COPILOT_WORKFLOWS`) |
| kết quả design tools `<thư mục board>\Ansys AEDT Copilot\kitchen\` | `...\Ansys AEDT Copilot\design_tools\` |
| plan template "Kitchen check" | "Tool catalog check" |

- Workflow cá nhân đã lưu ở thư mục cũ: vẫn được liệt kê và đọc (ghi chú "old folder"), không bị sửa / xoá. Lưu mới
  chỉ vào thư mục mới. Cùng tên ở cả hai → dùng bản ở thư mục mới, bản cũ hiện `shadowed`.
- Thư mục kết quả cũ `Ansys AEDT Copilot\kitchen\` trên máy không bị đụng tới; `design_cutout` lần đầu sau cập nhật
  copy board một lần nữa vào `design_tools\_src`.
- Constitution Principle X đổi tên "Tool catalog and workflows" (cùng luật; chủ repo sửa bằng `/speckit-constitution`,
  câu chữ theo `specs/020-rename-catalog-workflows/plan.md`).

## 1.0.0 (2026-11-09) — BREAKING: bỏ luồng Excel
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tool, prompt, guide đổi). Feature 017.

**Bỏ (danh sách đã được duyệt) → thay bằng**

| Đã bỏ | Dùng thay |
|---|---|
| `review_layout` (HTML) | `design_review(board, channels, html=true)` — cùng báo cáo HTML |
| `propose_channels`, `read_channels`, `start_cut_batch` | interface simulation: `isim_start` → `isim_trace` → `isim_confirm_content` → `isim_cut` → `isim_check_ends` → `isim_apply` (prompt `interface-sim`) |
| `job_status`, `get_report` | `isim_status`, `task_result`, kết quả `isim_apply` (`self_check`, `metrics`) |
| `merge_to_project` | `isim_merge` (hoặc `design_merge`) |
| prompt `cut-board`, `cut-run`, `cut-status`, `cut-report`, `cut-open`, `cut-rerun` | prompt `interface-sim` (mở kết quả trong AEDT: `finish_in_aedt`) |
| guide `workflow`, `setup_note`, `verify`, `review_layout` | nội dung chuyển vào guide `interface_sim` (ghi chú kỹ thuật + checklist kiểm tra) và `review_measure` (báo cáo HTML) |
| recipe `excel-cut` | recipe `interface-sim`, `cut-sweep-merge` |
| CLI `review`, `propose`, `cut`, `status`, `report`, `merge`, `run-job`, `worker` | CLI `isim --op=...`, `review-measure --html`, `design --op=...` |
| hàng template `run.channel_timeout_min`, `run.max_parallel` | — (chỉ chạy hàng loạt Excel dùng) |

- Giữ: `finish_in_aedt` (mở design đã cắt / đã gộp trong AEDT, tô màu net), `inspect_board`, mọi tool `isim_*`,
  `design_*`, `kitchen_*`, `pidc_*`, `layout_*`; các thư mục `autocut/` cũ trên máy không bị đụng tới.
- **Job Excel cũ đang dở**: không còn tool đọc. Muốn làm xong: `git checkout v0.15.0` (rồi quay lại `main`).
- `tests/regression.py` giờ chạy luồng interface simulation trên bản copy board1, cùng số liệu tham chiếu
  (`python tests/regression.py <bản copy>\simulation.aedt`).
- Constitution 2.0.0 (Principle I, III, V, IX bỏ phần Excel; chủ repo sửa bằng `/speckit-constitution`, câu chữ theo
  `specs/017-retire-excel-flow/plan.md` §5).

## 0.15.0 (2026-11-09)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide đổi). Feature 019.
- **Đầu không pin GND: lựa chọn mới `gnd_keep_pad`** (interface simulation). Khi linh kiện thật ra CÓ pin GND (vd.
  exposed pad) nhưng bị cutout cắt mất, câu hỏi 015 có thêm lựa chọn: mở rộng vùng cutout = vùng cũ ∪ (pad + 0.5 mm,
  hàng template mới `interface_sim.keep_pad_margin_mm`). Apply cắt lại từ bản copy board, pad thành pin GND, giữ via
  GND trong pad, không vẽ tấm GND. Chỉ đưa ra khi pad chạm vùng cutout; không có thì ghi lý do.
- Ảnh câu hỏi: pad GND (xanh lá), vùng cutout cũ (xám), vùng mở rộng (xanh lá), via trong pad; câu hỏi ghi kích thước
  pad, số via, các net khác nằm trong phần mở rộng (cutout không giữ các net đó).
- board1: U26 / U21 pin 65 (6.3 × 6.3 mm, 25 via) được đề xuất; chọn `gnd_keep_pad` cho U14_U26 → U26 có pin GND,
  không có tấm GND, 24 port, self-check OK. Lựa chọn 1 (tấm GND) và luồng Excel giữ nguyên như 0.14.0.
- `design_end_check` báo số liệu pad (khi có `stage1.json` cạnh design) nhưng không đưa thành lựa chọn (chỉ
  `isim_apply` thực hiện được).

## 0.14.1 (2026-11-09)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide đổi). Sửa lỗi PI-DC + sửa layout (feature 016).
- **Điện áp VRM đúng**: đọc bảng Voltage / Current Sources theo TÊN cột. Cột "Series R Voltage" là sụt áp trên R nguồn
  khi bằng I × R (V ra = Magnitude − cột); khác I × R (VRM remote sense, vd. B04 VCC_0P8V) thì chính là V ra. Trước
  đây boardb_19x19 ra V VRM ≈ 0 V và drop âm.
- **Đồng mảnh không còn im lặng NO_DATA**: trace RDL 20–40 µm được đo bằng ô 0.1 mm (`pidc.cd_narrow_window_mm`), chỉ
  trên pixel đồng; mảnh đồng < 0.002 mm² (`pidc.cd_tiny_area_mm2`) chỉ INFO. Không cặp nào được đánh giá → verdict
  NO_DATA (không bao giờ PASS). boardb_19x19: NO_DATA 505 → 76 (chỉ còn "không có dòng").
- `.siw` không có danh sách net nguồn / GND (hoặc chỉ GND) → dừng, báo rõ cách sửa trong SIwave.
- **Via: dT lấy từ mô phỏng**: dT = nhiệt độ DC sim (`GlobalTemperature` của run) − `pidc.via_base_temp_C` (25 °C).
  Bỏ hàng `pidc.via_dT_C`. Thiếu nhiệt độ hoặc dT ≤ 0 → dừng; ngoài 10..100 °C → cảnh báo. Report ghi T_sim, T_base,
  dT. B04 (60 °C → dT 35) không đổi; boardb_19x19 (90 °C → dT 65).
- `pidc.image_width` mặc định 10000 (SIwave giới hạn 10000), lớn hơn → cảnh báo.
- **layout_edit xoá được via**: `delete` nhận id via (padstack instance); `layout_region` trả danh sách via có id;
  pin linh kiện bị từ chối; kiểm tra "Via đã xoá". Plan chỉ có `delete` cần `region`.
- B04: kết quả PI-DC (current density, via, voltage) và 2 case layout_edit giống hệt bản trước.

## 0.14.0 (2026-11-09)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide + tham số tool đổi).
- **Đầu không có pin GND: người dùng quyết định** (feature 015). IC SMD / connector không có pin GND (vd. U26, U21
  QFN64 trên board1) không còn được tự vẽ tấm GND. End check dừng, gửi ẢNH vùng thân linh kiện (pad tín hiệu đỏ,
  via GND xanh, đồng GND có sẵn, hình chữ nhật đề xuất nét đứt kèm kích thước) và hỏi nhiều lựa chọn theo đúng trường
  hợp: 1 vẽ hình chữ nhật GND bao các via (cách cũ), 2 dùng đồng GND có sẵn (via trên đồng thành pin GND, chỉ khi có),
  3 giữ nguyên linh kiện, 4 dừng interface, 5 khác (người dùng ghi, agent map về 1 lựa chọn hoặc báo không có công cụ).
  Không có via GND: cũng dừng và hỏi (lựa chọn cần via bị bỏ, có lý do).
- Cờ mới `user_approved_gnd` trên `isim_apply` (+ `gnd_notes`) và `start_cut_batch` (+ `gnd_handling`): thiếu câu trả
  lời thì tool từ chối. Câu trả lời lưu trong `user_settings.json` (`gnd_decisions`); cut lại hiện ảnh + câu trả lời
  cũ và hỏi xác nhận lại (không tự dùng lại).
- Luồng Excel (giữ tối thiểu): `propose_channels` trả `gnd_questions` + ảnh + cảnh báo trong Excel; hỏi ở GATE 2.
  Format Excel không đổi; report Excel thêm cột "Tham chiếu GND". Lệnh CLI `cut --gnd-handling`.
- Self-check / metrics ghi tham chiếu GND từng đầu (`gnd_reference`). Chọn lựa chọn 1 cho kết quả giống hệt bản cũ.
- Phát hiện trên board1: U26 / U21 có pin GND (pin 65, exposed pad) nhưng nằm ngoài vùng cutout nên bị cắt mất;
  câu hỏi ghi chú điều này (luồng Excel).
## 0.13.2 (2026-11-09)
Không cần chạy lại `setup.bat`. Khởi động lại Claude để MCP server dùng code mới (tool, tham số, kết quả không đổi).
- Sắp xếp lại (feature 014): CLI chuyển vào `aedt_copilot/cli/` (mỗi lệnh 1 hàm xử lý; `__main__.py` chỉ gọi vào);
  MCP server chỉ lấy tham số, kiểm tra gate và gọi API package. Logic cũ trong server (kiểm tra Excel channel, dấu đã
  verify, điều kiện merge, chọn apply / re-apply, chạy CLI nền, guide / prompt / about) chuyển vào package.
- Tên tool, mô tả, tham số, thông báo từ chối, prompt, lệnh và cờ CLI giống hệt bản trước (so với golden chụp từ code
  cũ); regression board1 PASS.
## 0.13.1 (2026-11-08)
Không cần chạy lại `setup.bat`, không cần khởi động lại Claude. Kết quả không đổi.
- Sắp xếp lại (feature 013): PI-DC và sửa layout dùng lớp `core` chung. Skill PI-DC được tìm tự động (thêm skill =
  thêm 1 file), sửa layout mở board qua phiên EDB chung. Kết quả PI-DC (3 skill) và sửa layout (2 case B04) giống hệt
  bản trước.
- Đầu vào sai (board không có, box sai, op không hỗ trợ, tên skill sai) báo lỗi ngay, nêu rõ tham số; op sai được
  phát hiện TRƯỚC khi copy board.
## 0.13.0 (2026-11-08)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide đổi).
- **Đầu connector không còn dừng hỏi** (feature 012): end check đề xuất cách xử lý mặc định của team
  `smd_rebuild` (dòng template mới `interface_sim.connector_handling`): port trên pin tín hiệu của connector, tham
  chiếu là pin GND của chính connector (tấm GND chỉ khi không có pin GND, như cũ). Kỹ sư đổi được ở GATE B; lựa chọn
  lưu trong `user_settings.json`, cut lại dùng lại. Connector có vấn đề khác (vd. thiếu GND gần pin) vẫn hỏi.
- Self-check liệt kê mọi linh kiện nối tiếp (refdes, loại, part, giá trị) và mô hình đã dùng: **nối tắt** (R = 0 Ω,
  đọc lại trên design). Số port so với 2 × số đường tín hiệu (`expected_ports_2x_paths`, thay `expected_ports_2x_nets`):
  linh kiện nối tiếp không thêm đầu.
- Review: mỗi dòng bằng chứng của một điểm chỉ hiện một lần (bỏ dòng SOV trùng). Số mục / điểm / severity không đổi;
  mất tham chiếu vẫn HIGH.
- Guide: via stub đánh giá theo tốc độ interface (nêu lý do); báo kỹ sư tụ AC bị nối tắt.

## 0.12.0 (2026-11-07)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tool / guide mới).
- **Mới: review layout dạng số liệu** (feature 011, guide `review_measure`, công thức `layout-review`):
  `design_review(board, channels, checks)` đo từng check hoặc tất cả trên board / design bất kỳ — `reference` (SOV,
  ref sang net khác, mất tham chiếu), `trace_stubs`, `vias` (stub, via GND gần nhất, đổi lớp plane), `routing` (chiều
  dài theo lớp, độ rộng, skew cặp / bộ 3). Severity chỉ là gợi ý; agent tóm tắt điểm nghi vấn kèm số liệu trong chat,
  đổi severity phải nêu lý do; HTML (như `review_layout`) chỉ khi được yêu cầu.
- Interface simulation: bước tuỳ chọn sau GATE A — `isim_review` (đo nội dung đã chốt, `review.json`),
  `isim_review_decide` (chấp nhận / bỏ qua từng điểm, lưu trong `user_settings.json`). Bỏ qua = như trước.
- Mỗi check là một module (`aedt_copilot/review_checks/`): thêm check = thêm file. Code đo dùng lại nguyên hàm của
  `review_layout` → số liệu giống hệt. `review_layout`, HTML và gate của luồng Excel không đổi.
- Kiểm tra trên bản copy board1: số liệu đo giống hệt `review_layout` (U14_U26 24 mục; U21_J25 29 mục, 11 điểm nghi vấn);
  một check riêng chạy 0,34 lần thời gian tất cả check; bước review của interface simulation + lưu quyết định OK;
  regression luồng Excel và isim_check PASS.

## 0.11.2 (2026-11-07)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (server + guide đổi).
- **Khoá nguyên tắc "nhà bếp" bằng code** (feature 010, constitution 1.2.0 Principle X): mọi tool đăng ký qua một
  đường chung; tool thiếu mục danh mục, mức an toàn, cờ đồng ý hoặc contract → server không khởi động (báo tên tool).
  Test offline: mọi dụng cụ có cờ đều từ chối khi cờ false và không ghi file; mọi mục danh mục có contract; công thức
  nhóm không có dụng cụ lạ hay tool quy trình dùng sai chỗ (`misplaced`).
- `merge_to_project`: kiểm tra cờ `user_approved_verify` trước (trước đây kiểm tra job trước). Tên / đầu vào / kết quả
  tool không đổi.
- Spec Kit: plan có mục "Kitchen check"; converge chạy test danh mục.

## 0.11.1 (2026-11-07)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide đổi).
- **Arc step mặc định 30 deg** (trước 10; feature 009). Max refinement per pass giữ 10 % (AEDT đã hiện đúng), thêm
  kiểm tra số nguyên 1..100 trước khi ghi file; self-check đọc lại cả hai.
- Lần chạy cũ giữ giá trị của nó: cut lại "như lần trước" giữ arc step cũ (10) và liệt kê `default_changes`
  (mặc định nhóm nay 30); re-apply design cũ giữ arc step cũ. Từ bản này, mỗi lần apply ghi arc step tường minh vào
  `user_settings.json`; file của bản cũ được bổ sung giá trị cũ khi ghi lần đầu (chỉ thêm, không đổi gì khác).
- Kiểm tra trên bản copy board1: cut mới 2 interface PASS (đọc lại arc 30, max refine 10, reference OK); cut lại
  request 0.7.0 → giữ arc 10, `default_changes` = 1 dòng, metrics như lần trước, file cũ không đổi; công cụ lẻ PASS.

## 0.11.0 (2026-11-07)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tool / guide / prompt mới).
- **Mới: mô hình nhà bếp** (feature 008, guide `kitchen`, prompt `kitchen`): mỗi tool là một dụng cụ có mức an toàn
  (`read`, `copy`, `original`, `workspace`, `remote`); 3 mức sau cần cờ đồng ý, khoá trong server theo từng dụng cụ.
  `kitchen_utensils` (danh mục dụng cụ), `kitchen_recipes` / `get_recipe` (công thức), `save_recipe` (chỉ ghi thư mục
  cá nhân `%USERPROFILE%\.aedt_copilot\recipes`, env `AEDT_COPILOT_RECIPES`; không ghi đè nếu không có cờ).
- Công thức nhóm trong `recipes/`: excel-cut, interface-sim, re-cut, re-apply, pidc-report, layout-edit, design-tools
  (trỏ tới guide hiện có) + `cut-sweep-merge` (ví dụ ghép chỉ từ dụng cụ, không cần code).
- **Dụng cụ mới**: `design_trace`, `design_end_check`, `design_check` (chỉ đọc), `design_cutout` (cắt 1 channel từ
  bản copy của board ra `<thư mục board>/Ansys AEDT Copilot/kitchen/<tên>_cutout_<giờ>/`), `design_cleanup` (dọn GND,
  copy mặc định, in place cần cờ), `design_merge` (gộp design vào workspace, backup trước, cờ `user_approved_merge`).
- Tool, định dạng file và quy trình cũ không đổi.
- `design_check` / `design_end_check` nhận mẫu net (`CPHY_*`); check không có pin tín hiệu nào → không ok.
  Công thức `cut-sweep-merge` có thêm bước `design_airbox` (design vừa cắt mang airbox mặc định của PyEDB).
- Kiểm tra trên bản copy board1: trace U14-U26 (12 net) → cutout (307 s, design mới trong `kitchen/`) → end check →
  cleanup (từ stage1.json) → 24 port → setup → airbox → check OK (24 port = 24 pin tín hiệu) → merge vào workspace copy
  (design mới, có backup); board không đổi. Cut lại CPHY_U14_U26 như lần trước: PASS, metrics như lần trước.

## 0.10.0 (2026-11-06)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tool / guide / prompt mới).
- **Mới: công cụ lẻ trên design `.aedb` bất kỳ** (feature 007, guide `design_tools`, prompt `design-tools`):
  `design_read` (chỉ đọc), `design_setup`, `design_sweep`, `design_airbox`, `design_ports`, `design_solder_ball`.
  Mặc định làm trên bản copy `<tên>_<thao tác>_<giờ>.aedb` (file gốc không đổi); `in_place` sửa tại chỗ sau backup
  `<tên>_old_<giờ>.aedb`, cần cờ `user_approved_in_place`. Kiểm tra đầu vào trước khi đụng file, từ chối khi design
  đang mở (`.lock`). Mỗi thao tác: đọc lại giá trị, báo cáo cũ → mới / bỏ qua, file `<kết quả>.design_tools.md`.
- Nội bộ: `cutter.apply_sweep` và `cutter.create_ports` tách ra (cut cho kết quả như cũ).
- Gọi nối tiếp: bản copy giữ tên gốc `<tên>_<thao tác>_<giờ>.aedb` (không dài thêm), báo cáo cộng dồn các bước.
- Kiểm tra trên bản copy board1: cut luồng Excel giống hệt 0.7.0 (regression OK), cut lại OK; 5 thao tác nối tiếp
  (sweep, setup, airbox, port U26, solder ball U14): đọc lại đúng, chỉ đổi mục được nêu, file gốc không đổi.

## 0.9.0 (2026-11-06)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide / prompt / tool mới).
- **Mới: sửa settings simulation sau khi apply** (feature 006). Thông số chia 2 nhóm theo tiền tố khoá: **cut**
  (`cutout`, `series`, `cleanup`, `port`, `solder_ball` + xử lý đầu) khoá sau apply — đổi phải cut lại; **simulation**
  (`setup`, `sweep`, `airbox`) sửa được: `isim_apply` lần nữa (GATE B lại) → backup `final/<name>_old_<giờ>.aedb`
  (không xoá), chỉ ghi lại setup / sweep / arc step / airbox, self-check đọc lại, so hình học với lần trước
  (`geometry_same`). Interface đã merge → về `applied`; merge lại = design mới (`_v2`), design cũ giữ nguyên.
- `user_settings.json`: giá trị cũ giữ trong `history` của interface. Form (005): tab đã apply mở, nhóm cut chỉ xem.
- Guide: bỏ câu "re-apply mọi giá trị"; luật mới ở Phase 2 bước 8. Luồng Excel cũ không đổi.
- So hình học khi re-apply không so `bbox_mm` của linh kiện (EDB tính lại khi mở file); vẫn so pin, GND pin, vùng pin,
  port, GND via, mặt GND.
- Kiểm tra trên bản copy board1: đổi `cleanup.*` → bị từ chối; sweep stop 20 GHz + max passes 20 → backup, self-check
  OK, hình học giữ nguyên, `user_settings.json` có history.

## 0.8.0 (2026-11-06)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tool / guide / prompt mới).
- **Mới: form settings đầy đủ ở GATE B** (feature 005): tool `isim_settings_form` (mỗi interface của request một tab;
  mọi thông số scope channel của template, theo nhóm, có mặc định / lựa chọn / đơn vị / mô tả; dòng khoá chỉ xem;
  lựa chọn cho đầu "unusual") và `isim_validate_form` (kiểm tra mọi tab một lần, lỗi tab này không chặn tab khác).
  Guide: nút "Set default" (tab / mọi tab) về mặc định của nhóm, "Copy to all tabs"; submit chỉ là dữ liệu nhập,
  GATE B vẫn duyệt từng interface. Không có widget → bảng đầy đủ trong chat.
- Template: mô tả của `airbox.extent_type` / `airbox.dielectric_extent_type` liệt kê lựa chọn
  (`conforming | bounding_box | convex_hull`); khoá và giá trị không đổi.
- Kiểm tra trên bản copy board1: 2 interface (CPHY_U14_U26, CPHY_U21_J25) → form 2 tab × 52 thông số → validate cả 2
  → apply từng cái: self-check OK, U14_U26 metrics giống hệt cách nhập bằng chữ.

## 0.7.2 (2026-11-06)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide / prompt mới).
- Interface simulation: self-check sau apply đọc lại **toàn bộ airbox** từ EDB đã lưu (extent, dielectric extent,
  padding ngang / +Z / -Z, padding Z theo stackup, open region, operating freq) và so với settings đã chốt; lệch → báo.
  Luồng Excel cũ không có self-check này (không đổi).
- Guide `interface_sim`: form GATE B có nhóm airbox (dropdown loại extent, số padding, checkbox Z theo stackup,
  radiation / pml, operating freq), điền sẵn mặc định.
- Kiểm tra trên bản copy board1: cut lại CPHY_U14_U26 → self-check OK (cả airbox), metrics giống lần trước.

## 0.7.1 (2026-11-06)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (guide / prompt mới).
- Guide `interface_sim` + prompt `interface-sim`: ở GATE A (chọn 2 đầu, cách xử lý khác biệt board / schematic /
  cut lại) và GATE B (sweep start / stop / step, loại sweep, basis order, max passes, delta S, arc step, lựa chọn cho
  từng đầu "unusual"), nếu Claude hiển thị được widget thì dùng **form nhập điền sẵn** thay cho chỉ bảng markdown.
  Kết quả form chỉ là dữ liệu nhập: vẫn hiện bảng kết quả và chờ "đồng ý". Ô sweep bắt buộc để trống (không tự điền).
  Kiểm tra phía server và luồng Excel không đổi.

## 0.7.0 (2026-11-06)
Không cần chạy lại `setup.bat`. Khởi động lại Claude (tool / guide / prompt mới).
- **Mới: cut lại "như lần trước"** (feature 004): tool `isim_previous` (các lần chạy cũ của interface cho cùng
  workspace), `isim_recut` (trace lại trên board hiện tại với 2 đầu + net cũ, chỉ báo khác biệt, nội dung cũ điền
  sẵn; mỗi khác biệt cần người dùng quyết ở GATE A). `isim_check_ends` thêm `handling_compare`; bảng settings điền sẵn
  giá trị lần trước (Source `previous run <id>`). Đọc được cả request 0.6.0.
- **Một file `user_settings.json` / request** giữ mọi thứ đã chốt (nội dung, thông số cắt, xử lý 2 đầu, settings);
  thay `settings.json` / `settings.md` của từng interface (không còn ghi). Copy sang máy khác để cut lại được.
- **Arc step 10 deg** (`setup.arc_step_deg`, khoảng (0, 90]) cho mọi design cắt ra, cả luồng Excel cũ (dòng mới trong
  Settings của Excel) → **kết quả mesh thay đổi**; self-check + metrics đọc lại; reference regression thêm
  `arc_step_deg`.
- Kiểm tra trên bản copy board1 (AEDT 2026 R1): cut lại CPHY_U14_U26 từ request 0.6.0 → 0 khác biệt, metrics giống
  hệt, self-check OK; regression luồng Excel PASS; AEDT GUI hiện arc step 10 deg.

## 0.6.0 (2026-11-05)
**Cần chạy lại `setup.bat`** (thêm `rpyc==6.0.2`) rồi khởi động lại Claude (tool / guide / prompt mới).
- **Mới: interface simulation** (guide `interface_sim`, prompt `interface-sim`, 14 tool `isim_*`, CLI `isim`), không
  dùng Excel: schematic PDF + BOM đọc 1 lần → `schematic.md`; thống nhất nội dung interface (GATE A); cắt trên bản copy
  board; kiểm tra 2 đầu (loại đầu, pad, GND gần pin tín hiệu, connector → `unusual` + lựa chọn); bảng settings
  (cùng luật với Excel) → apply + tự kiểm tra (GATE B); gộp vào workspace chính (GATE C); chạy remote lần lượt trên
  server khi người dùng yêu cầu (GATE D) qua PyAEDT service manager (port 17878: tool mở AEDT không giao diện trên
  server, upload nếu thư mục không share) hoặc AEDT người dùng đã mở (`-grpcsrv`). Trạng thái lưu theo request, làm tiếp được ở chat mới.
- Cutter tách `cut_stage` (cutout) / `apply_stage` (port, dọn GND, solder ball, setup): đổi settings không phải cắt
  lại. `cut_channel` (luồng Excel cũ) giữ nguyên kết quả.
- `cut_board.merge.merge_designs` (gộp vào project bất kỳ); `merge_to_project` không đổi.
- Template thêm dòng `interface_sim.*` (scope job, không vào Excel). `config.yaml`: ví dụ `sim_servers` (chú thích).

## 0.5.1 (2026-11-05)
Không cần chạy lại `setup.bat`. Chỉ thay đổi nội bộ, kết quả không đổi.
- Package mới `aedt_copilot/core/` (feature 002): `errors` (`CopilotInputError`), `validate`, `config` (một bộ đọc
  template CSV theo tên cột cho cả 3 template), `edb` (`edb_session`), `geometry`, `units`, `registry`.
- `cut_board/config.py`, `cut_board/geometry.py` giữ đường dẫn cũ (re-export). `aedt_env`, `pi_dc`, `edit_layout`
  không còn import `cut_board`.
- Test offline mới `tests/unit/` (golden lấy từ code trước khi chuyển). Roadmap: `specs/ROADMAP.md`.

## 0.5.0 (2026-11-04)
**Cần chạy lại `setup.bat`** (chọn bản AEDT, ghi `config.yaml`) rồi khởi động lại Claude.
- **Chạy trên Ansys AEDT 2026 R1** (2025 R2 vẫn dùng được nếu máy không có 2026 R1). Module mới `aedt_copilot/aedt_env.py`
  tìm thư mục AEDT (config `aedt_root` → biến môi trường → registry → quét), lấy biến license từ môi trường Windows,
  dùng chung cho review / cut / layout edit / PI-DC. Không còn ghi cứng `2025.2`.
- `setup.bat`: ưu tiên `ANSYSEM_ROOT261`, rồi `ANSYSEM_ROOT252`; ghi `aedt_version` vào `config.yaml`
  (`tools/set_aedt_version.py`).
- MCP server: tiến trình con nhận đúng môi trường AEDT; tham số dạng `--key=value` (giá trị bắt đầu bằng `-` như toạ độ âm).
- AEDT 2026 R1 không cho tô màu net bằng script → merge / `finish_in_aedt` chỉ báo warning "thiếu màu"; design vẫn đủ
  port / setup / sweep. Sửa `finish_in_aedt` (lỗi tham số `release_desktop` với pyaedt 1.9).
- Kiểm tra trên 2026 R1 (bản copy): regression cut CPHY_U14_U26, layout edit B04 (stitch + neck), PI-DC VCC_0P8V
  (`pidc_check`) cho kết quả giống 2025 R2; merge + finish chạy được.
- Lưu ý: file do 2026 R1 lưu không mở được bằng 2025 R2.

## 0.4.0 (2026-11-03)
**Cần chạy lại `setup.bat`** (thêm shapely) rồi khởi động lại Claude.
- **Mới: sửa layout (improvement)** – module `aedt_copilot.edit_layout`, guide `layout_edit`, tool MCP `layout_region`,
  `layout_edit`, CLI `layout-region` / `layout-edit`. Tổng quát hoá từ các case tối ưu B04 (ASM_1P1V stitch, U200 neck):
  trước đây Claude viết script mới mỗi case (~70 phút cho 4 phút máy chạy).
  - `layout_region`: đọc một vùng (không cả board), tóm tắt polygon/trace/via + ảnh từng lớp.
  - `layout_edit(plan)`: 1 lần mở EDB trên BẢN COPY, op `add_copper`, `carve`, `remove_copper`, `void`, `trace`,
    `via`, `delete`; tự khoét antipad, tự dời/bỏ via vi phạm, gộp polygon + dọn void vụn; kiểm tra (chồng đồng, khe hở,
    mảnh đồng, mất kết nối via/pin, via mới, min_width, connected); ảnh trước/sau; `changes.md`.
  - Đặt via / khoét void gọi thẳng API .NET có cache: pyedb `padstacks.place` + `modeler.create_circle` mất ~6 s/via.
  - Mặc định: `templates/layout_edit_template.csv`. Test: `tests/layout_edit_b04.py`.

## 0.3.2 (2026-10-28)
Khởi động lại Claude (tool mới). Không cần chạy lại `setup.bat`.
- PI-DC skill mới **power_tree** (guide `pidc_power_tree`, tool `pidc_power_tree`): SIwave Export DC Power Tree bằng
  script → `images/POWER_TREE.png` + bảng Pass/Fail từng tải (vào Summary nếu Fail). Mặc định: Include Yes, 100 A,
  Percentage 3 %, gộp pin ON, danh sách power loss OFF (`pidc.pt_*`); đổi voltage/current theo yêu cầu
  (`--pt-voltage`, `--pt-current` / tham số tool).
- Voltage distribution: vòng khoanh + mũi tên màu đen viền trắng, nhãn chữ đen (nổi trên nền đỏ).

## 0.3.1 (2026-10-28)
Khởi động lại Claude (tool mới). Không cần chạy lại `setup.bat`.
- PI-DC skill mới **voltage_distribution** (guide `pidc_voltage_distribution`, tool `pidc_voltage_distribution`):
  1 ảnh `images/VLT_ALL_POWER.png` — mọi rail nguồn (không GND), mọi lớp chồng lên nhau (TOP trên cùng), 1 thang màu
  chung; khoanh Vmin từng tải (refdes.pin, rail, mV) và điện áp VRM. Bảng mỗi rail: VRM, Vmin tải, drop mV/%. Chỉ thông tin.
- Export: job ALL_POWER thêm `<voltage>1</voltage>`; `pidc-export --voltage-only` xuất bổ sung ảnh voltage cho thư mục cũ.
- Current density: pad linh kiện = node chân linh kiện của SIwave (dòng đổ vào 1 node) → chỉ INFO, không FAIL/WARN
  (`pidc.cd_pin_keepout_mm` = 0.25). Template glyph 6x hiệu chuẩn lại (338 ảnh, đọc được cả thang màu voltage).

## 0.3.0 (2026-10-28)
**Cần chạy lại `setup.bat`** (thêm numpy, scipy, pillow) rồi khởi động lại Claude.
- **Mới: PI-DC report** (tách riêng, không ảnh hưởng cắt board). Đầu vào: thư mục SIwave đã giải DC-IR; làm trực tiếp,
  không copy, không save. Output `<thư mục>\Ansys AEDT Copilot\`: HTML, `images\*.png` (dùng cho PowerPoint), `report.md`,
  `summary.json`, csv, `raw\` (ảnh SIwave 6x).
  - Guide `pidc_workflow` (điều khiển) + skill `pidc_current_density`, `pidc_via_current`; tool MCP `pidc_export`,
    `pidc_current_density`, `pidc_via_current`, `pidc_report`; prompt `pidc-report`; CLI `python -m aedt_copilot pidc --dir`.
  - Export: ảnh 6x (10000×6000) qua biến môi trường `EXPORT_REPORT_IMAGE_WIDTH/HEIGHT`; chờ report ghi xong (export bất
    đồng bộ); filter `via-current` cho ảnh via current chỉ net nguồn.
  - Current density: J trung bình ô 0.5×0.5 mm (chỉ đồng), kết luận theo J_avg_max (FAIL > giới hạn, WARN > 50 %),
    khoanh tối đa 3 vùng nổi bật/ảnh (≥ 50 % giới hạn hoặc ≥ 2× nền), đỉnh 1 điểm chỉ INFO.
  - Via current: đoạn xấu nhất, I_cap IPC (dT 35 °C, lỗ hoàn thiện), 3 ảnh khoanh via FAIL/WARN + top 5.
  - Thông số riêng `templates/pidc_template.csv`.

## 0.2.0 (2026-10-25)
**Cần chạy lại `setup.bat`**, gỡ plugin `ansys-aedt-copilot` / `ansys-aedt-auto-cut-board` trong Claude, khởi động lại Claude.
- **Bỏ plugin, chỉ còn MCP server.** `setup.bat` tự đăng ký `aedt_copilot` vào Claude desktop
  (`tools/register_claude.py`, đường dẫn tuyệt đối, có bản MSIX). Skill → `guides/*.md` (tool `get_guide`),
  lệnh `/cut-*` → MCP prompts trong `prompts/` (+ `copilot-help`), tool mới `about`.
  Sửa guide/prompt chỉ cần mở chat mới, không phải build/cài lại.
- Khoá gate trong server: `propose_channels` cần đã có layout review + `user_approved_review`;
  `start_cut_batch` cần `user_approved_excel` + Excel hợp lệ; `merge_to_project` cần job xong, đã `get_report`
  và `user_approved_verify`.
- Prompt `cut-board` giờ chạy review layout trước (GATE 1) rồi mới tạo Excel.
- **Đổi tên thành Ansys AEDT Copilot**: thư mục `ansys_aedt_copilot`, package `aedt_copilot` (module `aedt_copilot.cut_board`),
  MCP server `aedt_copilot`, biến môi trường `AEDT_COPILOT_HOME`. Người dùng: đổi tên thư mục, chạy `setup.bat`.
- Mới: `review_layout` (MCP) / `review` (CLI) — review layout trước khi cắt, báo cáo HTML tự chứa
  (SOV, loss of reference, reference change, via stub/backdrill, via GND gần nhất, chiều dài cặp/bộ 3).
  Ngưỡng ở `review.*` trong template.
- Chặn tên channel trùng / trống / có ký tự lạ (`read_channels`, `start_cut_batch`); `propose` tự thêm `_2`.
- Cắt lỗi hoặc quá giờ: tự xoá `.aedb` làm dở (chỉ khi chính lần cắt đó tạo ra).
- `tests/regression.py`: tham chiếu đổi tên `CPHY_U14_U26` (tên tự sinh); FAIL khi thiếu job/kết quả.
- Skill review-layout: báo cáo HTML (thay PDF), viết tiếng Anh, có mục Summary đầu trang.
- Báo cáo layout review v2: Summary dạng bảng (Signal via / Signal routing, chỉ tô đỏ chỗ bất thường), điểm bất thường
  gộp theo vị trí và theo loại lỗi, phần chi tiết thu gọn. Check mới: tham chiếu sang net khác (GND → net khác),
  trace stub (đầu hở / nhánh T), chiều dài và độ rộng trace theo layer, cặp/bộ 3 có đi cùng layer không.
  Đổi lớp plane GND → GND tại via chỉ còn HIGH (thiếu via GND) hoặc INFO.
- Sửa cắt: khung BGA ôm sát pin; pin giữ đúng vị trí khi dựng lại component (trước đó U14/J25 bị dời);
  tên part definition không trùng khi cắt lại sau merge; tự kiểm tra pin lệch > 1 mm và khung component.
- Skill workflow / setup-note / verify bổ sung các quy tắc trên.
- Solder ball: đường kính / chiều cao ghi kèm đơn vị mm (trước đó AEDT hiện 0.0002 không đơn vị).
- requirements: `ansys-aedt-core` không còn trên PyPI → `pyaedt==1.9.0` (cùng module `ansys.aedt.core`);
  ghim `mcp<2` (mcp 2.x bỏ `FastMCP`).

## 0.1.0
- Phiên bản đầu: đề xuất channel ra Excel, cắt hàng loạt (mỗi channel một tiến trình), báo cáo Excel,
  tô màu net trong AEDT. MCP server `ansys_aedt_auto_cut_board` + plugin `ansys-aedt-auto-cut-board`.
