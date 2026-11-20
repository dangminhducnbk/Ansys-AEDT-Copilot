---
description: Công cụ lẻ trên một design .aedb bất kỳ - tạo port, đặt setup / sweep / airbox, solder ball (mặc định trên bản copy).
---
Gọi `get_guide("design_tools")` rồi làm theo, CHỈ dùng tool `design_*` của MCP server `aedt_copilot`.

Yêu cầu: $ARGUMENTS

Cần: đường dẫn .aedb và thao tác (port / setup / sweep / airbox / solder ball). Thiếu thì hỏi. Đọc trước bằng
`design_read`. Mặc định làm trên bản copy; sửa tại chỗ chỉ khi người dùng yêu cầu VÀ đồng ý rõ ràng.
