"""MCP Filesystem - re-export from core for backwards compatibility."""
from core.filesystem import FileSystemTools, FileInfo, OperationResult, get_filesystem

__all__ = ["FileSystemTools", "FileInfo", "OperationResult", "get_filesystem"]
