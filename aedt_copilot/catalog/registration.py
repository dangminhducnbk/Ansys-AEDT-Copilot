"""Đường đăng ký tool chung (feature 010, contract: specs/020-rename-catalog-workflows/contracts/catalog.md, Principle X).

Mọi tool của server đăng ký qua `tool = make_tool(mcp)` rồi `@tool()`. Tool không có trong danh mục tool, thiếu
mức an toàn, mức có rủi ro mà thiếu cờ đồng ý (hoặc cờ không phải tham số), hay thiếu contract -> lỗi ngay lúc import
server = server không khởi động. Tên, docstring, tham số của tool không đổi (FastMCP nhận đúng hàm đó).
"""
import inspect

from . import tools as catalog


class CatalogRegistrationError(RuntimeError):
    pass


def problems(name, params):
    """-> danh sách lỗi đăng ký của tool `name` có tham số `params` (rỗng = hợp lệ)."""
    e = catalog.by_name().get(name)
    if e is None:
        return ["no catalog entry"]
    out = []
    if e.get("safety") not in catalog.SAFETY:
        out.append(f"safety '{e.get('safety')}' not one of " + ", ".join(catalog.SAFETY))
    if e.get("kind") not in catalog.KINDS:
        out.append(f"kind '{e.get('kind')}' not tool / process")
    if e.get("safety") in catalog.GATED and not e.get("gate"):
        out.append(f"safety '{e['safety']}' needs a gate flag")
    if e.get("gate") and e["gate"] not in params:
        out.append(f"gate '{e['gate']}' is not a parameter")
    if not e.get("contract"):
        out.append("no contract reference")
    return out


def make_tool(mcp):
    """-> tool(): decorator thay cho mcp.tool(), kiểm tra danh mục trước khi đăng ký."""
    def tool():
        def deco(fn):
            p = problems(fn.__name__, list(inspect.signature(fn).parameters))
            if p:
                raise CatalogRegistrationError(f"catalog: tool '{fn.__name__}': " + "; ".join(p) +
                                               " - add it to aedt_copilot/catalog/tools.py (Principle X)")
            out = mcp.tool()(fn)
            tool.registered.append(fn.__name__)
            return out
        return deco
    tool.registered = []
    return tool
