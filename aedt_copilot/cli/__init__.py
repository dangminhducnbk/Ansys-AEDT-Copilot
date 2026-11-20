"""Lớp vào (feature 014): CLI (parser, commands, main) + hỗ trợ cho MCP server (tasks = chạy CLI ở tiến trình con,
docs = guide / prompt / about). Chỉ lấy tham số và gọi API package (Principle VIII)."""
from .main import main

__all__ = ["main"]
