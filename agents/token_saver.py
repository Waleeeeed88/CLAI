"""Native token-saving policy for CLAI agents."""
from __future__ import annotations

from typing import Iterable, List

from .base import Message


TOKEN_SAVER_PROMPT = """## Cost Saver Mode
Use the Ponytail ladder before adding work: skip speculative scope, reuse local code, prefer stdlib, prefer native platform features, use installed dependencies, then write the smallest correct implementation.

Use Caveman brevity in replies: no pleasantries, filler, or decorative structure. Keep exact code, commands, paths, API names, and errors. Preserve safety, validation, security, accessibility, and explicit user requirements."""


def apply_cost_saver_prompt(system_prompt: str) -> str:
    """Append cost-saving behavior once."""
    if TOKEN_SAVER_PROMPT in system_prompt:
        return system_prompt
    if not system_prompt:
        return TOKEN_SAVER_PROMPT
    return f"{system_prompt.rstrip()}\n\n{TOKEN_SAVER_PROMPT}"


def apply_output_cap(max_tokens: int, cap: int) -> int:
    """Apply a conservative max-output cap while preserving invalid cap safety."""
    if cap <= 0:
        return max_tokens
    return min(max_tokens, cap)


def trim_history(messages: Iterable[Message], keep: int) -> List[Message]:
    """Keep the newest chat history messages, like LangGraph-style trim-before-call."""
    items = list(messages)
    if keep <= 0:
        return []
    if len(items) <= keep:
        return items
    return items[-keep:]


def compact_message_text(message: Message, max_chars: int) -> Message:
    """Return a shallow-compacted message for old history text."""
    if max_chars <= 0 or not isinstance(message.content, str) or len(message.content) <= max_chars:
        return message

    suffix = "\n...[trimmed by cost saver]"
    if max_chars <= len(suffix):
        content = message.content[:max_chars]
    else:
        content = f"{message.content[: max_chars - len(suffix)].rstrip()}{suffix}"

    return Message(
        role=message.role,
        content=content,
        metadata=dict(message.metadata),
        tool_calls=message.tool_calls,
        tool_result=message.tool_result,
    )


def compact_history(messages: Iterable[Message], keep: int, max_chars: int) -> List[Message]:
    return [compact_message_text(message, max_chars) for message in trim_history(messages, keep)]
