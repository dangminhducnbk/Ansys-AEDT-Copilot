"""Module 'PI-DC report': current density + via current check of a solved SIwave DC-IR project.

common.py        đọc .siw (net nguồn, lớp kim loại, tên DC sim), thư mục kết quả, thông số pidc.*
export.py        chép project sang thư mục chạy, tạo filter + script IronPython, chạy SIwave (cần GPU), chạy lại job lỗi
colorbar_ocr.py  đọc nhãn thang màu bằng template glyph (data/siwave_colorbar_glyphs.npz) + tự kiểm
post.py          current density (P90 theo vùng) + via current (.vcd/.vias, IPC) -> board_summary.json
report.py        HTML tiếng Anh + ảnh PNG riêng trong pidc_report_files/
Quy tắc: guides/review_pidc.md.
"""
from .. import __version__  # noqa: F401
