---
description: Danh mục - chọn workflow (quy trình) hoặc ghép các tool cho một yêu cầu bất kỳ; lưu workflow cá nhân.
---
Gọi `get_guide("catalog")` rồi làm theo, CHỈ dùng tool của MCP server `aedt_copilot`.

Yêu cầu: $ARGUMENTS

Đọc `list_workflows` + `list_tools` trước. Có workflow hợp → `get_workflow` và làm theo (điểm dừng chờ người
dùng đồng ý). Không có → đề xuất chuỗi tool, chờ đồng ý. Lưu workflow cá nhân (`save_workflow`) chỉ khi người dùng
yêu cầu.
