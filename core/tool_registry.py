"""Provider-agnostic tool registry.

Stores tool definitions and their callable handlers, converts to
provider-specific formats (Anthropic / OpenAI / Gemini).
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """A single parameter in a tool's input schema."""

    name: str
    type: str  # JSON Schema type: string, number, integer, boolean, array, object
    description: str = ""
    required: bool = False
    enum: Optional[List[str]] = None
    default: Optional[Any] = None
    items: Optional[Dict[str, Any]] = None  # JSON Schema items for array types


@dataclass
class ToolDefinition:
    """Provider-agnostic tool definition."""

    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    handler: Optional[Callable[..., Any]] = None

    # ── JSON Schema helpers ──────────────────────────────────────────

    def _build_json_schema(self) -> Dict[str, Any]:
        """Build a JSON Schema 'object' for the parameters."""
        properties: Dict[str, Any] = {}
        required: List[str] = []
        for p in self.parameters:
            prop: Dict[str, Any] = {"type": p.type}
            if p.description:
                prop["description"] = p.description
            if p.enum is not None:
                prop["enum"] = p.enum
            if p.type == "array":
                prop["items"] = p.items if p.items else {"type": "string"}
            properties[p.name] = prop
            if p.required:
                required.append(p.name)

        schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required
        return schema

    # ── Provider-specific conversions ────────────────────────────────

    def to_anthropic(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self._build_json_schema(),
        }

    def to_openai(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._build_json_schema(),
            },
        }

    @staticmethod
    def _convert_schema_for_gemini(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON Schema string types to Gemini protobuf Type enums.

        Gemini's FunctionDeclaration expects ``Type`` enum values
        (``Type.OBJECT``, ``Type.STRING``, etc.) not the JSON Schema
        string literals ``"object"``, ``"string"``, etc.
        """
        import google.generativeai as genai

        _TYPE_MAP = {
            "object": genai.protos.Type.OBJECT,
            "string": genai.protos.Type.STRING,
            "number": genai.protos.Type.NUMBER,
            "integer": genai.protos.Type.INTEGER,
            "boolean": genai.protos.Type.BOOLEAN,
            "array": genai.protos.Type.ARRAY,
        }
        converted: Dict[str, Any] = {}
        for key, value in schema.items():
            if key == "type" and isinstance(value, str):
                converted[key] = _TYPE_MAP.get(value, value)
            elif key == "properties" and isinstance(value, dict):
                converted[key] = {
                    k: ToolDefinition._convert_schema_for_gemini(v)
                    for k, v in value.items()
                }
            elif key == "items" and isinstance(value, dict):
                converted[key] = ToolDefinition._convert_schema_for_gemini(value)
            else:
                converted[key] = value
        return converted

    def to_gemini(self) -> Dict[str, Any]:
        """Return a dict usable as a Gemini FunctionDeclaration."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._convert_schema_for_gemini(self._build_json_schema()),
        }


class ToolRegistry:
    """Container for tool definitions paired with handler functions.

    Usage::

        registry = ToolRegistry()
        registry.register(
            name="read_file",
            description="Read a file from the workspace.",
            parameters=[
                ToolParameter("file_path", "string", "Relative path", required=True),
            ],
            handler=lambda file_path: fs.read_file(file_path).data,
        )
        result = registry.execute("read_file", {"file_path": "README.md"})
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    # ── Registration ─────────────────────────────────────────────────

    def register(
        self,
        name: str,
        description: str,
        parameters: Optional[List[ToolParameter]] = None,
        handler: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters or [],
            handler=handler,
        )

    def register_definition(self, tool_def: ToolDefinition) -> None:
        self._tools[tool_def.name] = tool_def

    def merge(self, other: "ToolRegistry") -> None:
        """Merge another registry's tools into this one."""
        self._tools.update(other._tools)

    # ── Execution ────────────────────────────────────────────────────

    def execute(self, name: str, arguments: Dict[str, Any]) -> str:
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        if not tool.handler:
            raise ValueError(f"Tool '{name}' has no handler registered")
        result = tool.handler(**arguments)
        # Normalise result to string for the model
        if isinstance(result, str):
            return result
        return json.dumps(result, default=str, indent=2)

    # ── Listing ──────────────────────────────────────────────────────

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_definition(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def __len__(self) -> int:
        return len(self._tools)

    def __bool__(self) -> bool:
        return bool(self._tools)

    # ── Provider-specific bulk conversion ────────────────────────────

    def to_anthropic_format(self) -> List[Dict[str, Any]]:
        return [t.to_anthropic() for t in self._tools.values()]

    def to_openai_format(self) -> List[Dict[str, Any]]:
        return [t.to_openai() for t in self._tools.values()]

    def to_gemini_format(self) -> List[Dict[str, Any]]:
        return [t.to_gemini() for t in self._tools.values()]
