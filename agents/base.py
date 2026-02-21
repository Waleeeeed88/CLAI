"""Base agent classes and tool-calling infrastructure."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

MAX_TOOL_CALL_ITERATIONS = 25
MAX_TOOL_RESULT_CHARS = 4000


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ToolCall:
    """Represents a tool invocation requested by the model."""
    id: str
    name: str
    arguments: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "arguments": self.arguments}


@dataclass
class ToolResult:
    """Represents the result of executing a tool."""
    tool_call_id: str
    content: str
    is_error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id,
            "content": self.content,
            "is_error": self.is_error,
        }


@dataclass
class Message:
    role: MessageRole
    content: Union[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_calls: Optional[List[ToolCall]] = None
    tool_result: Optional[ToolResult] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"role": self.role.value, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]
        if self.tool_result:
            d["tool_result"] = self.tool_result.to_dict()
        return d


@dataclass
class AgentResponse:
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls_made: List[ToolCall] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)

    def __str__(self) -> str:
        return self.content


class BaseAgent(ABC):
    def __init__(
        self,
        model: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tool_registry: Optional[Any] = None,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.tool_registry = tool_registry  # core.tool_registry.ToolRegistry
        self.conversation_history: List[Message] = []
        self._client = None
        self.max_tool_result_chars = MAX_TOOL_RESULT_CHARS

    @staticmethod
    def _truncate_text(text: str, max_chars: int) -> str:
        if max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text
        suffix = "\n...[truncated for token safety]"
        if max_chars <= len(suffix):
            return text[:max_chars]
        return f"{text[: max_chars - len(suffix)].rstrip()}{suffix}"

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    def _initialize_client(self) -> None:
        pass

    @abstractmethod
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        """Send a single request (no tool loop). Provider-specific."""
        pass

    def _execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call via the registry and return the result."""
        if not self.tool_registry:
            return ToolResult(
                tool_call_id=tool_call.id,
                content="Error: No tool registry available.",
                is_error=True,
            )
        try:
            result = self.tool_registry.execute(tool_call.name, tool_call.arguments)
            content = str(result)
            if len(content) > self.max_tool_result_chars:
                content = self._truncate_text(content, self.max_tool_result_chars)
            return ToolResult(tool_call_id=tool_call.id, content=content)
        except Exception as e:
            logger.error(f"Tool execution error ({tool_call.name}): {e}")
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error executing tool '{tool_call.name}': {e}",
                is_error=True,
            )

    def chat(self, user_message: str, include_history: bool = True) -> AgentResponse:
        if self._client is None:
            self._initialize_client()

        messages = list(self.conversation_history) if include_history else []
        user_msg = Message(role=MessageRole.USER, content=user_message)
        messages.append(user_msg)

        all_tool_calls: List[ToolCall] = []
        response = self._send_request(messages)

        # Tool-call loop: keep going while the model wants to call tools
        iterations = 0
        while (
            response.finish_reason in ("tool_use", "tool_calls", "function_call")
            and self.tool_registry
            and iterations < MAX_TOOL_CALL_ITERATIONS
        ):
            iterations += 1
            if not response.tool_calls_made:
                break

            all_tool_calls.extend(response.tool_calls_made)

            for tc in response.tool_calls_made:
                logger.info(f"Tool call: {tc.name}({json.dumps(tc.arguments, default=str)[:200]})")

            # Execute tools and build result messages
            tool_results = [self._execute_tool(tc) for tc in response.tool_calls_made]

            for tr in tool_results:
                logger.info(f"Tool result ({tr.tool_call_id}): {tr.content[:200]}")

            # Append assistant + tool result messages (provider-specific formatting
            # happens in _send_request, but we store the canonical form here)
            messages = self._append_tool_messages(messages, response, tool_results)
            response = self._send_request(messages)

        if iterations >= MAX_TOOL_CALL_ITERATIONS:
            logger.warning(f"Tool-call loop hit max iterations ({MAX_TOOL_CALL_ITERATIONS})")

        response.tool_calls_made = all_tool_calls

        # Update history with the final user/assistant pair
        self.conversation_history.append(user_msg)
        self.conversation_history.append(
            Message(role=MessageRole.ASSISTANT, content=response.content)
        )
        return response

    def _append_tool_messages(
        self,
        messages: List[Message],
        assistant_response: AgentResponse,
        tool_results: List[ToolResult],
    ) -> List[Message]:
        """Append assistant tool-call message and tool-result messages.

        Default implementation stores tool calls/results in Message metadata.
        Providers override this in their _send_request to read the right format.
        """
        # Assistant message that contained tool calls
        assistant_msg = Message(
            role=MessageRole.ASSISTANT,
            content=assistant_response.content or "",
            tool_calls=assistant_response.tool_calls_made,
            metadata={"raw_response": assistant_response.raw_response},
        )
        messages.append(assistant_msg)

        # One message per tool result
        for tr in tool_results:
            messages.append(
                Message(
                    role=MessageRole.TOOL,
                    content=tr.content,
                    tool_result=tr,
                )
            )
        return messages

    def clear_history(self) -> None:
        self.conversation_history = []

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
