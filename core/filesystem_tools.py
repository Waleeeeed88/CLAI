"""Filesystem tools — wraps FileSystemTools methods as ToolRegistry entries.

Provides a ready-to-use ToolRegistry that agents can call to read/write
files, list directories, search, etc. inside the sandboxed workspace.
"""
from __future__ import annotations

import json
from typing import List, Optional

from core.tool_registry import ToolParameter, ToolRegistry
from core.filesystem import FileSystemTools, get_filesystem


def build_filesystem_registry(
    fs: Optional[FileSystemTools] = None,
) -> ToolRegistry:
    """Build a ToolRegistry with all filesystem operations.

    Args:
        fs: An existing FileSystemTools instance. If *None*, the global
            singleton is used via ``get_filesystem()``.
    """
    if fs is None:
        fs = get_filesystem()

    registry = ToolRegistry()

    # ── read_file ────────────────────────────────────────────────────

    def _read_file(file_path: str) -> str:
        result = fs.read_file(file_path)
        if not result.success:
            return f"Error: {result.message}"
        return result.data or ""

    registry.register(
        name="read_file",
        description="Read the contents of a file in the workspace.",
        parameters=[
            ToolParameter("file_path", "string", "Relative path to the file", required=True),
        ],
        handler=_read_file,
    )

    # ── write_file ───────────────────────────────────────────────────

    def _write_file(file_path: str, content: str) -> str:
        result = fs.write_file(file_path, content)
        return result.message

    registry.register(
        name="write_file",
        description="Write content to a file in the workspace. Creates parent directories automatically.",
        parameters=[
            ToolParameter("file_path", "string", "Relative path to the file", required=True),
            ToolParameter("content", "string", "Full file content to write", required=True),
        ],
        handler=_write_file,
    )

    # ── append_file ──────────────────────────────────────────────────

    def _append_file(file_path: str, content: str) -> str:
        result = fs.append_file(file_path, content)
        return result.message

    registry.register(
        name="append_file",
        description="Append content to an existing file in the workspace.",
        parameters=[
            ToolParameter("file_path", "string", "Relative path to the file", required=True),
            ToolParameter("content", "string", "Content to append", required=True),
        ],
        handler=_append_file,
    )

    # ── delete_file ──────────────────────────────────────────────────

    def _delete_file(file_path: str) -> str:
        result = fs.delete_file(file_path)
        return result.message

    registry.register(
        name="delete_file",
        description="Delete a file from the workspace.",
        parameters=[
            ToolParameter("file_path", "string", "Relative path to the file", required=True),
        ],
        handler=_delete_file,
    )

    # ── list_directory ───────────────────────────────────────────────

    def _list_directory(dir_path: str = ".") -> str:
        entries = fs.list_directory(dir_path)
        if not entries:
            return "Directory is empty or does not exist."
        return "\n".join(str(e) for e in entries)

    registry.register(
        name="list_directory",
        description="List files and subdirectories in a workspace directory.",
        parameters=[
            ToolParameter("dir_path", "string", "Relative directory path (default: root)", required=False),
        ],
        handler=_list_directory,
    )

    # ── create_directory ─────────────────────────────────────────────

    def _create_directory(dir_path: str) -> str:
        result = fs.create_directory(dir_path)
        return result.message

    registry.register(
        name="create_directory",
        description="Create a directory (and parents) in the workspace.",
        parameters=[
            ToolParameter("dir_path", "string", "Relative directory path to create", required=True),
        ],
        handler=_create_directory,
    )

    # ── get_tree ─────────────────────────────────────────────────────

    def _get_tree(dir_path: str = ".", max_depth: int = 3) -> str:
        return fs.get_tree(dir_path, max_depth)

    registry.register(
        name="get_tree",
        description="Get a tree view of the workspace directory structure.",
        parameters=[
            ToolParameter("dir_path", "string", "Root directory (default: workspace root)", required=False),
            ToolParameter("max_depth", "integer", "Maximum depth to display (default: 3)", required=False),
        ],
        handler=_get_tree,
    )

    # ── search_files ─────────────────────────────────────────────────

    def _search_files(pattern: str, dir_path: str = ".") -> str:
        matches = fs.search_files(pattern, dir_path)
        if not matches:
            return "No files matched the pattern."
        return "\n".join(matches)

    registry.register(
        name="search_files",
        description="Search for files matching a glob pattern in the workspace.",
        parameters=[
            ToolParameter("pattern", "string", "Glob pattern, e.g. '*.py'", required=True),
            ToolParameter("dir_path", "string", "Directory to search in (default: root)", required=False),
        ],
        handler=_search_files,
    )

    # ── grep ─────────────────────────────────────────────────────────

    def _grep(search_term: str, dir_path: str = ".", file_pattern: str = "*") -> str:
        matches = fs.grep(search_term, dir_path, file_pattern)
        if not matches:
            return "No matches found."
        return "\n".join(matches[:50])  # cap output to 50 matches

    registry.register(
        name="grep",
        description="Search for text within files in the workspace. Returns matching lines with file:line:content format.",
        parameters=[
            ToolParameter("search_term", "string", "Text to search for (case-insensitive)", required=True),
            ToolParameter("dir_path", "string", "Directory to search in (default: root)", required=False),
            ToolParameter("file_pattern", "string", "File glob filter, e.g. '*.py' (default: all files)", required=False),
        ],
        handler=_grep,
    )

    return registry
