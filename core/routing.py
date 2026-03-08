"""Smart routing — provider fallback chains for resilient agent execution.

When a primary provider fails (rate limit, outage, error), automatically
retries with an alternative provider from a configurable fallback chain.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from agents import AgentFactory, AgentResponse, BaseAgent
from agents.factory import Provider, Role

logger = logging.getLogger(__name__)


@dataclass
class FallbackChain:
    """Ordered list of (provider, model) pairs to try for a role."""

    primary: Tuple[Provider, str]
    fallbacks: List[Tuple[Provider, str]] = field(default_factory=list)

    @property
    def all_options(self) -> List[Tuple[Provider, str]]:
        return [self.primary] + self.fallbacks


# Default fallback chains — each role has a primary (from ROLE_PROVIDERS)
# and cross-provider fallbacks for resilience.
DEFAULT_FALLBACKS: Dict[Role, List[Tuple[Provider, str]]] = {
    Role.SENIOR_DEV: [
        (Provider.GOOGLE, "gemini-3.1-pro-preview"),
        (Provider.OPENAI, "gpt-5.2-2025-12-11"),
    ],
    Role.CODER: [
        (Provider.GOOGLE, "gemini-3.1-pro-preview"),
        (Provider.OPENAI, "gpt-5.2-2025-12-11"),
    ],
    Role.CODER_2: [
        (Provider.ANTHROPIC, "claude-sonnet-4-5-20250929"),
        (Provider.OPENAI, "gpt-5.2-2025-12-11"),
    ],
    Role.CODER_3: [
        (Provider.GOOGLE, "gemini-3.1-pro-preview"),
        (Provider.ANTHROPIC, "claude-sonnet-4-5-20250929"),
    ],
    Role.QA: [
        (Provider.OPENAI, "gpt-4.1-2025-04-14"),
        (Provider.ANTHROPIC, "claude-sonnet-4-5-20250929"),
    ],
    Role.BA: [
        (Provider.ANTHROPIC, "claude-sonnet-4-5-20250929"),
        (Provider.GOOGLE, "gemini-3.1-pro-preview"),
    ],
    Role.REVIEWER: [
        (Provider.GOOGLE, "gemini-3.1-pro-preview"),
        (Provider.OPENAI, "gpt-5.2-2025-12-11"),
    ],
}


@dataclass
class FallbackEvent:
    """Emitted when a fallback occurs."""

    role: str
    from_provider: str
    from_model: str
    to_provider: str
    to_model: str
    reason: str
    attempt: int


def _is_retriable_error(exc: Exception) -> bool:
    """Check if an exception should trigger a fallback attempt."""
    msg = str(exc).lower()
    name = type(exc).__name__.lower()
    return (
        "rate_limit" in msg
        or "rate limit" in msg
        or "429" in msg
        or "ratelimiterror" in name
        or "server_error" in msg
        or "500" in msg
        or "502" in msg
        or "503" in msg
        or "overloaded" in msg
    )


def ask_with_fallback(
    role: Role,
    prompt: str,
    system_prompt: str,
    tool_registry: Any = None,
    max_tokens: int = 8192,
    temperature: float = 0.7,
    on_fallback: Optional[Callable[[FallbackEvent], None]] = None,
) -> AgentResponse:
    """Try the primary provider, fall back to alternatives on retriable errors.

    Args:
        role: The role to create an agent for.
        prompt: The user/pipeline prompt.
        system_prompt: System prompt for the agent.
        tool_registry: Optional tool registry.
        max_tokens: Max tokens for the response.
        temperature: Sampling temperature.
        on_fallback: Callback fired when a fallback occurs.

    Returns:
        AgentResponse from whichever provider succeeded.

    Raises:
        The last exception if all providers fail.
    """
    primary_provider, primary_model = AgentFactory.get_role_runtime_config(role)
    fallbacks = DEFAULT_FALLBACKS.get(role, [])

    all_options = [(primary_provider, primary_model)] + fallbacks
    last_exc: Optional[Exception] = None

    for attempt, (provider, model) in enumerate(all_options):
        try:
            agent = AgentFactory.create_by_provider(
                provider=provider,
                model=model,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                tool_registry=tool_registry,
            )
            response = agent.chat(prompt, include_history=False)
            return response

        except Exception as exc:
            last_exc = exc

            if not _is_retriable_error(exc):
                raise

            logger.warning(
                "Provider %s/%s failed for %s (attempt %d): %s",
                provider.value, model, role.value, attempt + 1, exc,
            )

            # Emit fallback event if there's a next option
            if attempt < len(all_options) - 1:
                next_provider, next_model = all_options[attempt + 1]
                if on_fallback:
                    on_fallback(FallbackEvent(
                        role=role.value,
                        from_provider=provider.value,
                        from_model=model,
                        to_provider=next_provider.value,
                        to_model=next_model,
                        reason=str(exc)[:200],
                        attempt=attempt + 1,
                    ))

                # Brief delay before fallback
                time.sleep(1)

    # All options exhausted
    raise last_exc  # type: ignore[misc]
