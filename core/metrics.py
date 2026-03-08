"""Metrics — token usage, cost estimation, and latency tracking.

Aggregates per-agent metrics across a pipeline or workflow run,
with cost estimation based on published model pricing.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Cost per 1K tokens (input, output) in USD — approximate published rates
COST_TABLE: Dict[str, tuple] = {
    # Anthropic
    "claude-opus-4-5-20251101":    (0.015, 0.075),
    "claude-sonnet-4-5-20250929":  (0.003, 0.015),
    # OpenAI
    "gpt-5.2-2025-12-11":         (0.005, 0.015),
    "gpt-4.1-2025-04-14":         (0.002, 0.008),
    "o3-mini":                     (0.001, 0.004),
    # Google
    "gemini-3.1-pro-preview":      (0.00125, 0.005),
    "gemini-3-flash-preview":      (0.000075, 0.0003),
    "gemini-2.5-pro-preview-05-06":(0.00125, 0.005),
    # Kimi / Moonshot
    "kimi-k2-0520":                (0.002, 0.008),
    "moonshot-v1-128k":            (0.008, 0.008),
    "moonshot-v1-32k":             (0.002, 0.002),
}

# Fallback for unknown models
_DEFAULT_COST = (0.003, 0.015)


@dataclass
class AgentMetrics:
    """Metrics for a single agent turn."""

    role: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    tool_calls_count: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class RunSummary:
    """Aggregated metrics for a full run."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    agent_count: int = 0
    agent_breakdown: List[AgentMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_latency_ms": round(self.total_latency_ms, 1),
            "agent_count": self.agent_count,
            "agents": [
                {
                    "role": a.role,
                    "provider": a.provider,
                    "model": a.model,
                    "input_tokens": a.input_tokens,
                    "output_tokens": a.output_tokens,
                    "total_tokens": a.total_tokens,
                    "latency_ms": round(a.latency_ms, 1),
                    "tool_calls": a.tool_calls_count,
                    "cost_usd": round(a.estimated_cost_usd, 6),
                }
                for a in self.agent_breakdown
            ],
        }


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD based on model and token counts."""
    input_rate, output_rate = COST_TABLE.get(model, _DEFAULT_COST)
    return (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)


class RunMetrics:
    """Thread-safe metrics collector for a single pipeline/workflow run."""

    def __init__(self) -> None:
        self._turns: List[AgentMetrics] = []
        self._lock = threading.Lock()

    def record_agent_turn(
        self,
        role: str,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
        tool_calls_count: int = 0,
    ) -> AgentMetrics:
        """Record metrics for one agent turn."""
        # If only total_tokens given, split estimate 60/40 input/output
        if total_tokens and not input_tokens and not output_tokens:
            input_tokens = int(total_tokens * 0.6)
            output_tokens = total_tokens - input_tokens

        cost = _estimate_cost(model, input_tokens, output_tokens)

        metrics = AgentMetrics(
            role=role,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens or (input_tokens + output_tokens),
            latency_ms=latency_ms,
            tool_calls_count=tool_calls_count,
            estimated_cost_usd=cost,
        )

        with self._lock:
            self._turns.append(metrics)

        return metrics

    def get_summary(self) -> RunSummary:
        """Aggregate all recorded turns into a summary."""
        with self._lock:
            turns = list(self._turns)

        summary = RunSummary(agent_count=len(turns))
        for t in turns:
            summary.total_input_tokens += t.input_tokens
            summary.total_output_tokens += t.output_tokens
            summary.total_tokens += t.total_tokens
            summary.total_cost_usd += t.estimated_cost_usd
            summary.total_latency_ms += t.latency_ms
            summary.agent_breakdown.append(t)

        return summary

    def to_dict(self) -> Dict[str, Any]:
        return self.get_summary().to_dict()
