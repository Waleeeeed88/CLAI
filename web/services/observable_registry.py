"""ObservableToolRegistry — wraps ToolRegistry to fire callbacks on tool calls."""
from typing import Any, Callable, Dict
from core.tool_registry import ToolRegistry


class ObservableToolRegistry(ToolRegistry):
    """Shares the inner registry's tool dict and fires on_call/on_result on execute()."""

    def __init__(
        self,
        inner: ToolRegistry,
        on_call: Callable[[str, Dict[str, Any]], None],
        on_result: Callable[[str, str, bool], None],
    ):
        super().__init__()
        # Share the backing store — no copy overhead
        self._tools = inner._tools
        self._on_call = on_call
        self._on_result = on_result

    def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        self._on_call(name, arguments)
        try:
            result = super().execute(name, arguments)
        except Exception as exc:
            error_msg = f"Tool error: {type(exc).__name__}: {exc}"
            self._on_result(name, error_msg, False)
            raise
        self._on_result(name, result, True)
        return result
