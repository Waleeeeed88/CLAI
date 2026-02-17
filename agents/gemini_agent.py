"""Gemini agent - Google API with tool-calling support."""
from typing import Any, Dict, List
import google.generativeai as genai
from google.protobuf.struct_pb2 import Struct

from .base import BaseAgent, AgentResponse, Message, MessageRole, ToolCall
from config import get_settings


class GeminiAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chat_session = None

    @property
    def provider_name(self) -> str:
        return "google"

    def _initialize_client(self) -> None:
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key.get_secret_value())

        model_kwargs: Dict[str, Any] = {
            "model_name": self.model,
            "generation_config": genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            ),
            "system_instruction": self.system_prompt if self.system_prompt else None,
        }

        # Inject tool declarations if available
        if self.tool_registry and len(self.tool_registry) > 0:
            func_decls = self.tool_registry.to_gemini_format()
            model_kwargs["tools"] = [
                genai.protos.Tool(
                    function_declarations=[
                        genai.protos.FunctionDeclaration(**fd) for fd in func_decls
                    ]
                )
            ]

        self._client = genai.GenerativeModel(**model_kwargs)

    # ── message conversion ───────────────────────────────────────────

    def _to_gemini_history(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert internal Messages to Gemini chat history format.

        Handles plain text, function_call parts, and function_response parts.
        """
        history: List[Dict[str, Any]] = []
        for msg in messages[:-1]:
            # Assistant message with tool calls
            if msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                parts = []
                if msg.content:
                    parts.append(msg.content)
                for tc in msg.tool_calls:
                    parts.append(
                        genai.protos.Part(
                            function_call=genai.protos.FunctionCall(
                                name=tc.name,
                                args=self._dict_to_struct(tc.arguments),
                            )
                        )
                    )
                history.append({"role": "model", "parts": parts})
                continue

            # Tool result message
            if msg.role == MessageRole.TOOL and msg.tool_result:
                fr_part = genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=msg.metadata.get("tool_name", "tool"),
                        response=self._dict_to_struct(
                            {"result": msg.tool_result.content}
                        ),
                    )
                )
                # Merge consecutive tool results into one user entry
                # (Gemini requires strict user/model alternation)
                if (
                    history
                    and history[-1]["role"] == "user"
                    and history[-1]["parts"]
                    and not isinstance(history[-1]["parts"][0], str)
                ):
                    history[-1]["parts"].append(fr_part)
                else:
                    history.append({"role": "user", "parts": [fr_part]})
                continue

            # Plain text
            role = "user" if msg.role == MessageRole.USER else "model"
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            history.append({"role": role, "parts": [content]})
        return history

    @staticmethod
    def _dict_to_struct(d: Dict[str, Any]) -> Struct:
        s = Struct()
        s.update(d)
        return s

    # ── override tool message building ───────────────────────────────

    def _append_tool_messages(self, messages, assistant_response, tool_results):
        """Override to inject tool_name metadata for Gemini FunctionResponse."""
        assistant_msg = Message(
            role=MessageRole.ASSISTANT,
            content=assistant_response.content or "",
            tool_calls=assistant_response.tool_calls_made,
            metadata={"raw_response": assistant_response.raw_response},
        )
        messages.append(assistant_msg)

        # Map tool_call_id → tool_name from the assistant's calls
        id_to_name = {
            tc.id: tc.name for tc in (assistant_response.tool_calls_made or [])
        }

        for tr in tool_results:
            messages.append(
                Message(
                    role=MessageRole.TOOL,
                    content=tr.content,
                    tool_result=tr,
                    metadata={"tool_name": id_to_name.get(tr.tool_call_id, "tool")},
                )
            )
        return messages

    # ── request ──────────────────────────────────────────────────────

    def _send_request(self, messages: List[Message]) -> AgentResponse:
        gemini_history = self._to_gemini_history(messages)
        last_content = messages[-1].content if messages else ""

        # Handle the case where the last message is a tool result
        if messages and messages[-1].role == MessageRole.TOOL:
            # Rebuild: history is everything except the trailing tool-result
            # messages, and the "send" payload is the tool results
            tool_result_parts = []
            idx = len(messages) - 1
            while idx >= 0 and messages[idx].role == MessageRole.TOOL:
                msg = messages[idx]
                if msg.tool_result:
                    tool_name = msg.metadata.get("tool_name", "tool")
                    tool_result_parts.insert(
                        0,
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response=self._dict_to_struct(
                                    {"result": msg.tool_result.content}
                                ),
                            )
                        ),
                    )
                idx -= 1
            # Rebuild history: everything up to (and including) the assistant
            # message before the trailing tool results.  We append a dummy
            # entry so _to_gemini_history (which skips the last element)
            # processes all messages up to idx.
            gemini_history = self._to_gemini_history(
                messages[: idx + 1] + [messages[-1]]
            )
            last_content = tool_result_parts
        else:
            if isinstance(last_content, str):
                last_content = last_content
            else:
                last_content = str(last_content)

        # Re-initialize client if tool_registry was changed since last init
        if self._client is None:
            self._initialize_client()

        chat = self._client.start_chat(history=gemini_history)
        response = chat.send_message(last_content)

        # Check for function_call parts
        tool_calls: List[ToolCall] = []
        has_function_calls = False
        text_parts: List[str] = []

        for part in response.parts:
            if hasattr(part, "function_call") and part.function_call.name:
                has_function_calls = True
                args = dict(part.function_call.args) if part.function_call.args else {}
                tool_calls.append(ToolCall(
                    id=f"gemini_{part.function_call.name}_{id(part)}",
                    name=part.function_call.name,
                    arguments=args,
                ))
            elif hasattr(part, "text") and part.text:
                text_parts.append(part.text)

        content = "".join(text_parts)

        usage: Dict[str, int] = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
            }

        finish_reason = "function_call" if has_function_calls else "stop"

        return AgentResponse(
            content=content,
            model=self.model,
            provider=self.provider_name,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=response,
            tool_calls_made=tool_calls,
        )
