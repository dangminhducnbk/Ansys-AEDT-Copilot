"""Interface simulation (feature 003, guide interface_sim): code đo + thao tác, agent quyết định cùng người dùng.

Quy trình (mỗi request = 1 workspace AEDT của người dùng):
  0  schematic PDF + BOM -> schematic.md (agent đọc PDF, code đọc BOM, lưu 1 lần, dùng lại khi nguồn không đổi)
  1  content  : trace net / linh kiện trên board (+ so với schematic) -> người dùng chốt (GATE A)
  2  cut      : copy board -> cutter.cut_stage (nặng) ; ends: đo 2 đầu, trường hợp lạ ; settings: bảng thông số
     apply    : người dùng đồng ý (GATE B) -> copy stage1 -> cutter.apply_stage + self_check
  3  merge    : người dùng duyệt (GATE C) -> thêm design vào workspace (backup trước)
  4  run      : chỉ khi người dùng yêu cầu (GATE D) -> copy sang thư mục simulation trên server, giải lần lượt

Thư mục: <workspace dir>/Ansys AEDT Copilot/interface_sim/<request_id>/ (xem request.py).
Contract: specs/003-interface-simulation/contracts/.
"""
