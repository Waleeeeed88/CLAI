"""GPT agent - OpenAI API with tool-calling support."""
import json
from typing import Any, Dict, List
from openai import OpenAI

from .base import BaseAgent, AgentResponse, Message, MessageRole, ToolCall, DEFAULT_REQUEST_TIMEOUT
from config import get_settings


class GPTAgent(BaseAgent):
    @property
    def provider_name(self) -> str:
        return "openai"

    def _initialize_client(self) -> None:
        settings = get_settings()
        self._client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )

    # ── message conversion ───────────────────────────────────────────

    def _to_openai_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal Messages to OpenAI's chat format."""
        out: List[Dict[str, Any]] = []

        if self.system_prompt:
            out.append({"role": "system", "content": self.system_prompt})

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                continue

            # Assistant message with tool calls
            if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                m: Dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, default=str),
                        },
                    }
                    for tc in msg.tool_calls
                ]
                out.append(m)
                continue

            # Tool result message
            if msg.role == MessageRole.TOOL and msg.tool_result:
                out.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_result.tool_call_id,
                    "content": msg.tool_result.content,
                })
                continue

            # Plain text
            if msg.role != MessageRole.SYSTEM:
                out.append({
                    "role": msg.role.value,
                    "content": msg.content if isinstance(msg.content, str) else str(msg.content),
                })
        return out

    # ── request ──────────────────────────────────────────────────────

    def _send_request(self, messages: List[Message]) -> AgentResponse:
        openai_messages = self._to_openai_messages(messages)

        request_params: Dict[str, Any] = {
            "model": self.model,
            "max_completion_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": openai_messages,
        }

        # Inject tool schemas if available
        if self.tool_registry and len(self.tool_registry) > 0:
            request_params["tools"] = self.tool_registry.to_openai_format()

        response = self._retry_request(
            lambda: self._client.chat.completions.create(**request_params)
        )

        choice = response.choices[0]
        content = choice.message.content or ""

        # Extract tool calls
        tool_calls: List[ToolCall] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, TypeError):
                    args = {"raw": tc.function.arguments}
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                ))

        usage: Dict[str, int] = {}
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        finish_reason = choice.finish_reason

        return AgentResponse(
            content=content,
            model=response.model,
            provider=self.provider_name,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=response,
            tool_calls_made=tool_calls,
        )
