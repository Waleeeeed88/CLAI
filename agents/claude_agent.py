"""Claude agent - Anthropic API with tool-calling support."""
from typing import Any, Dict, List
import time
import anthropic

from .base import BaseAgent, AgentResponse, Message, MessageRole, ToolCall, DEFAULT_REQUEST_TIMEOUT
from config import get_settings


class ClaudeAgent(BaseAgent):
    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _initialize_client(self) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key.get_secret_value(),
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )

    @staticmethod
    def _truncate_text(text: str, max_chars: int) -> str:
        if max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text
        suffix = "\n...[truncated to reduce input tokens]"
        if max_chars <= len(suffix):
            return text[:max_chars]
        return f"{text[: max_chars - len(suffix)].rstrip()}{suffix}"

    @staticmethod
    def _is_rate_limit_error(exc: Exception) -> bool:
        msg = str(exc).lower()
        return (
            "rate_limit" in msg
            or "rate limit" in msg
            or "429" in msg
            or type(exc).__name__.lower() == "ratelimiterror"
        )

    def _compact_tool_input(self, value: Any, max_chars: int) -> Any:
        if isinstance(value, str):
            return self._truncate_text(value, max_chars)
        if isinstance(value, list):
            return [self._compact_tool_input(v, max_chars) for v in value]
        if isinstance(value, dict):
            return {k: self._compact_tool_input(v, max_chars) for k, v in value.items()}
        return value

    def _compact_anthropic_messages(
        self, messages: List[Dict[str, Any]], *, aggressive: bool = False
    ) -> List[Dict[str, Any]]:
        settings = get_settings()
        text_limit = settings.anthropic_message_char_limit
        tool_limit = settings.anthropic_tool_result_char_limit
        budget = settings.anthropic_total_input_char_budget
        if aggressive:
            text_limit = max(800, text_limit // 2)
            tool_limit = max(500, tool_limit // 2)
            budget = settings.anthropic_total_input_char_budget_retry

        compact_rev: List[Dict[str, Any]] = []
        used_chars = 0

        for msg in reversed(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            out: Dict[str, Any] = {"role": role}

            if isinstance(content, str):
                clipped = self._truncate_text(content, text_limit)
                remaining = max(0, budget - used_chars)
                clipped = self._truncate_text(clipped, remaining) if remaining < len(clipped) else clipped
                used_chars += len(clipped)
                out["content"] = clipped
            elif isinstance(content, list):
                blocks_rev: List[Dict[str, Any]] = []
                for block in reversed(content):
                    if used_chars >= budget:
                        break
                    b = dict(block)
                    btype = b.get("type")

                    if btype == "text":
                        text = self._truncate_text(str(b.get("text", "")), text_limit)
                        remaining = max(0, budget - used_chars)
                        text = self._truncate_text(text, remaining) if remaining < len(text) else text
                        used_chars += len(text)
                        b["text"] = text
                    elif btype == "tool_result":
                        tcontent = self._truncate_text(str(b.get("content", "")), tool_limit)
                        remaining = max(0, budget - used_chars)
                        tcontent = self._truncate_text(tcontent, remaining) if remaining < len(tcontent) else tcontent
                        used_chars += len(tcontent)
                        b["content"] = tcontent
                    elif btype == "tool_use" and "input" in b:
                        b["input"] = self._compact_tool_input(b["input"], tool_limit)

                    blocks_rev.append(b)

                out["content"] = list(reversed(blocks_rev))
            else:
                text = self._truncate_text(str(content), text_limit)
                remaining = max(0, budget - used_chars)
                text = self._truncate_text(text, remaining) if remaining < len(text) else text
                used_chars += len(text)
                out["content"] = text

            compact_rev.append(out)
            if used_chars >= budget:
                break

        return list(reversed(compact_rev))

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
        settings = get_settings()
        anthropic_messages = self._compact_anthropic_messages(
            self._to_anthropic_messages(messages),
            aggressive=False,
        )

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

        response = None
        retry_attempts = max(1, settings.anthropic_retry_attempts)
        for attempt in range(retry_attempts):
            try:
                response = self._client.messages.create(**request_params)
                break
            except Exception as exc:
                if not self._is_rate_limit_error(exc) or attempt >= (retry_attempts - 1):
                    raise

                delay = settings.anthropic_retry_base_delay_seconds * (2 ** attempt)
                request_params["messages"] = self._compact_anthropic_messages(
                    request_params["messages"],
                    aggressive=True,
                )
                time.sleep(delay)

        if response is None:
            raise RuntimeError("Anthropic request failed after retries.")

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
