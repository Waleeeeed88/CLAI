"""Shared agent scratchpad — structured inter-agent memory.

Provides a key-value store that agents read/write via tool calls,
replacing the lossy text-clipping approach with structured context.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional

from core.tool_registry import ToolParameter, ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class ScratchpadEntry:
    """A single entry in the scratchpad."""

    key: str
    value: Any
    author: str  # role that wrote it, e.g. "senior_dev"
    category: str  # decision | artifact | blocker | status
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "author": self.author,
            "category": self.category,
            "timestamp": self.timestamp,
        }


class Scratchpad:
    """Thread-safe shared memory for inter-agent communication."""

    VALID_CATEGORIES = ("decision", "artifact", "blocker", "status")

    def __init__(self, on_write: Optional[Callable[[ScratchpadEntry], None]] = None):
        self._entries: Dict[str, ScratchpadEntry] = {}
        self._lock = threading.Lock()
        self._on_write = on_write

    def write(self, key: str, value: Any, author: str, category: str) -> ScratchpadEntry:
        """Write or overwrite an entry. Returns the entry."""
        if category not in self.VALID_CATEGORIES:
            category = "status"
        entry = ScratchpadEntry(
            key=key, value=value, author=author, category=category,
        )
        with self._lock:
            self._entries[key] = entry
        if self._on_write:
            self._on_write(entry)
        return entry

    def read(self, key: str) -> Optional[ScratchpadEntry]:
        with self._lock:
            return self._entries.get(key)

    def read_by_category(self, category: str) -> List[ScratchpadEntry]:
        with self._lock:
            return [e for e in self._entries.values() if e.category == category]

    def read_all(self) -> Dict[str, ScratchpadEntry]:
        with self._lock:
            return dict(self._entries)

    def summarize(self, max_chars: int = 2000) -> str:
        """Format all entries as a readable summary for prompt injection."""
        with self._lock:
            entries = list(self._entries.values())

        if not entries:
            return "(scratchpad is empty)"

        # Group by category
        by_cat: Dict[str, List[ScratchpadEntry]] = {}
        for e in entries:
            by_cat.setdefault(e.category, []).append(e)

        lines: List[str] = ["## Shared Scratchpad"]
        for cat in ("decision", "artifact", "blocker", "status"):
            items = by_cat.get(cat)
            if not items:
                continue
            lines.append(f"\n### {cat.upper()}S")
            for e in items:
                val = e.value if isinstance(e.value, str) else json.dumps(e.value, default=str)
                lines.append(f"- **{e.key}** ({e.author}): {val}")

        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[: max_chars - 15].rstrip() + "\n...[truncated]"
        return text

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {k: e.to_dict() for k, e in self._entries.items()}


def build_scratchpad_registry(scratchpad: Scratchpad, role_name: str) -> ToolRegistry:
    """Build a ToolRegistry with scratchpad read/write/list tools.

    Each tool call is bound to the given ``role_name`` as the author.
    """
    registry = ToolRegistry()

    def _write(key: str, value: str, category: str = "status") -> str:
        entry = scratchpad.write(key=key, value=value, author=role_name, category=category)
        return f"Written to scratchpad: {entry.key} [{entry.category}]"

    registry.register(
        name="scratchpad_write",
        description=(
            "Write a structured entry to the shared team scratchpad. "
            "Use this to record decisions, artifacts, blockers, or status updates "
            "that other team members should see."
        ),
        parameters=[
            ToolParameter("key", "string", "Unique key for this entry (e.g. 'auth_decision', 'api_schema')", required=True),
            ToolParameter("value", "string", "The content to store", required=True),
            ToolParameter(
                "category", "string",
                "Entry category: decision, artifact, blocker, or status",
                required=True,
                enum=list(Scratchpad.VALID_CATEGORIES),
            ),
        ],
        handler=_write,
    )

    def _read(key: str) -> str:
        entry = scratchpad.read(key)
        if entry is None:
            return f"No entry found for key: {key}"
        val = entry.value if isinstance(entry.value, str) else json.dumps(entry.value, default=str)
        return f"[{entry.category}] {entry.key} (by {entry.author}):\n{val}"

    registry.register(
        name="scratchpad_read",
        description="Read a specific entry from the shared team scratchpad by key.",
        parameters=[
            ToolParameter("key", "string", "The key to read", required=True),
        ],
        handler=_read,
    )

    def _list(category: str = "") -> str:
        if category:
            entries = scratchpad.read_by_category(category)
        else:
            entries = list(scratchpad.read_all().values())
        if not entries:
            return "No entries found." if category else "Scratchpad is empty."
        lines = []
        for e in entries:
            val = e.value if isinstance(e.value, str) else json.dumps(e.value, default=str)
            preview = val[:200] if len(val) > 200 else val
            lines.append(f"- [{e.category}] {e.key} ({e.author}): {preview}")
        return "\n".join(lines)

    registry.register(
        name="scratchpad_list",
        description=(
            "List entries in the shared team scratchpad. "
            "Optionally filter by category (decision, artifact, blocker, status)."
        ),
        parameters=[
            ToolParameter(
                "category", "string",
                "Filter by category (optional). Leave empty to list all.",
                required=False,
                enum=list(Scratchpad.VALID_CATEGORIES),
            ),
        ],
        handler=_list,
    )

    return registry
