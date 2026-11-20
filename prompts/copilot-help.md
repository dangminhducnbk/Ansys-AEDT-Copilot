---
description: Giới thiệu Ansys AEDT Copilot cho người mới: làm được gì, các bước, ví dụ.
---
Gọi `about()`, `list_workflows()`, `list_tools()` và `get_guide("catalog")`. Giới thiệu ngắn gọn bằng ngôn ngữ người dùng ($ARGUMENTS):
1. Công cụ làm gì: danh mục tool (mỗi tool có mức an toàn) và workflow (mỗi quy trình là một workflow).
2. Bảng workflow (tên, dùng khi nào, điểm dừng người dùng duyệt) và bảng tool theo nhóm.
3. Quy trình cắt / mô phỏng interface (interface simulation, prompt interface-sim): thống nhất nội dung → cắt trên
   bản copy → kiểm tra đầu → chốt settings → apply → gộp vào workspace → chạy (khi yêu cầu); mở kết quả trong AEDT
   bằng finish_in_aedt khi người dùng muốn. Từ 1.0.0 không còn luồng Excel.
4. Ví dụ câu lệnh đầu tiên: interface-sim với `C:\...\simulation.aedt U14-U26:CPHY_B02DEVA_*`, hoặc
   "cắt U14-U26 net CPHY_* rồi đặt sweep 0-10 GHz" (workflow cut-sweep-merge).
5. Workflow cá nhân: lưu được trong `%USERPROFILE%\.aedt_copilot\workflows`.
6. Yêu cầu: Windows, Ansys AEDT 2026 R1 (2025 R2 dự phòng), đã chạy setup.bat. Phiên bản hiện tại.
Không chạy tool nào khác.
