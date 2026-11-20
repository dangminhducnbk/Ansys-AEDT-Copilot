---
description: Interface simulation (quy trình cố định 5.0.0; từ 5.6.0 một trang review + settings cho mỗi request): trace -> review layout + trang duy nhất (resolve điểm NOT OK, rồi settings) -> kiểm tra + vùng cut + review -> một lời đồng ý -> cut + dựng design + gộp vào project mới của request. Cut lại "như lần trước". Không dùng Excel.
---
Gọi `get_guide("interface_sim")` rồi làm theo mục 0 (QUY TRÌNH CỐ ĐỊNH), CHỈ dùng tool của MCP server `aedt_copilot`.

Yêu cầu: $ARGUMENTS

Bước 0: cần workspace .aedt (board), các interface (2 đầu + net), (tuỳ chọn) netlist / schematic / BOM / stackup. Thiếu thì hỏi đúng điều thiếu.
Quy trình (request 5.6.0+): isim_start -> isim_trace (mỗi channel) -> isim_layout_review (M0p: link trang review + settings, không có câu hỏi) -> người dùng resolve hết điểm NOT OK, Save + "xong" / "done" -> isim_config_check (M2 hoặc Q2) -> "đồng ý" / "yes" -> isim_go(user_approved_cut=true, user_words) (M3).
Request 5.2–5.5: isim_layout_review (M0 + Q0) -> "không" / "no": isim_review_answer(accepted=false) = DỪNG (M0x) | "đồng ý" / "yes": isim_review_answer(user_answered_review=true, accepted=true, user_words) (M1) -> như trên từ "xong".
Mỗi bước: DÁN NGUYÊN VĂN answer_md của tool (tiếng Việt + tiếng Anh), không thêm câu nào. Chỉ có các câu hỏi Q1 (đã config xong chưa?), Q2 (đồng ý cut không?) và Q0 (chỉ request cũ). Không hỏi chạy simulation.
Review chỉ OK / NOT OK theo ngưỡng: không đánh giá lỗi thay người dùng, không resolve điểm thay người dùng.
Cut lại "như lần trước" / "settings cũ" / request id / đường dẫn user_settings.json: Phase R của guide (isim_previous -> isim_start -> isim_recut), không gõ lại giá trị cũ, chỉ báo khác biệt.
Request tạo trước 5.0.0 hoặc người dùng yêu cầu từng bước: dùng các tool bước (GATE A-D) theo phần còn lại của guide.
