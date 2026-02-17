"""Claude agent - Anthropic API with tool-calling support."""
from typing import Any, Dict, List
import anthropic

from .base import BaseAgent, AgentResponse, Message, MessageRole, ToolCall
from config import get_settings


class ClaudeAgent(BaseAgent):
    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _initialize_client(self) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key.get_secret_value()
        )

    # ── message conversion ───────────────────────────────────────────

    def _to_anthropic_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal Messages to Anthropic's format.

        Handles plain text, assistant tool_use, and tool_result messages.
        """
        out: List[Dict[str, Any]] = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                continue

            # Assistant message with tool calls
            if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                content_blocks: List[Dict[str, Any]] = []
                if msg.content:
                    content_blocks.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                out.append({"role": "assistant", "content": content_blocks})
                continue

            # Tool result message
            if msg.role == MessageRole.TOOL and msg.tool_result:
                out.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_result.tool_call_id,
                        "content": msg.tool_result.content,
                        **({"is_error": True} if msg.tool_result.is_error else {}),
                    }],
                })
                continue

            # Plain text message
            out.append({
                "role": msg.role.value,
                "content": msg.content if isinstance(msg.content, str) else str(msg.content),
            })
        return out

    # ── request ──────────────────────────────────────────────────────

    def _send_request(self, messages: List[Message]) -> AgentResponse:
        anthropic_messages = self._to_anthropic_messages(messages)

        request_params: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": anthropic_messages,
        }

        if not self.model.endswith("-thinking"):
            request_params["temperature"] = self.temperature

        if self.system_prompt:
            request_params["system"] = self.system_prompt

        # Inject tool schemas if available
        if self.tool_registry and len(self.tool_registry) > 0:
            request_params["tools"] = self.tool_registry.to_anthropic_format()

        response = self._client.messages.create(**request_params)

        # Extract text content
        content = "".join(
            block.text for block in response.content if block.type == "text"
        )

        # Extract tool-call blocks
        tool_calls = [
            ToolCall(
                id=block.id,
                name=block.name,
                arguments=dict(block.input) if block.input else {},
            )
            for block in response.content
            if block.type == "tool_use"
        ]

        return AgentResponse(
            content=content,
            model=response.model,
            provider=self.provider_name,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,  # "tool_use" when tools requested
            raw_response=response,
            tool_calls_made=tool_calls,
        )
