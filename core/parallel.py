"""Parallel agent execution — fan-out/fan-in for concurrent agent calls.

Enables multiple agents to work simultaneously (e.g., Coder + Coder 2
during implementation), collecting results when all complete.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from agents import AgentResponse
from agents.factory import Role

logger = logging.getLogger(__name__)

# Shared pool — kept small to avoid overwhelming API rate limits
_parallel_pool = ThreadPoolExecutor(max_workers=3)


@dataclass
class ParallelTask:
    """A single agent task to run in parallel."""

    role: Role
    prompt: str
    label: str = ""  # human-readable step name


@dataclass
class ParallelResult:
    """Result from a parallel fan-out."""

    responses: Dict[Role, AgentResponse]
    errors: Dict[Role, str]

    @property
    def all_succeeded(self) -> bool:
        return len(self.errors) == 0

    def merged_content(self, separator: str = "\n\n---\n\n") -> str:
        """Merge all successful response contents."""
        parts = []
        for role, resp in self.responses.items():
            parts.append(f"### {role.value}\n{resp.content}")
        return separator.join(parts)


def parallel_ask(
    orchestrator: Any,
    tasks: List[ParallelTask],
    on_start: Optional[Callable[[Role, str], None]] = None,
    on_done: Optional[Callable[[Role, AgentResponse], None]] = None,
    on_error: Optional[Callable[[Role, Exception], None]] = None,
) -> ParallelResult:
    """Fan-out multiple agent calls, fan-in results.

    Each task runs in its own thread via the orchestrator's ask() method.
    Agent instances are per-role, so there are no shared-state conflicts.

    Args:
        orchestrator: The Orchestrator instance.
        tasks: List of ParallelTask to execute concurrently.
        on_start: Optional callback fired when each task starts.
        on_done: Optional callback fired when each task completes.
        on_error: Optional callback fired if a task fails.

    Returns:
        ParallelResult with responses and any errors.
    """
    responses: Dict[Role, AgentResponse] = {}
    errors: Dict[Role, str] = {}

    def _run_task(task: ParallelTask) -> Tuple[Role, AgentResponse]:
        if on_start:
            on_start(task.role, task.label)
        resp = orchestrator.ask(task.role, task.prompt)
        return task.role, resp

    futures = {
        _parallel_pool.submit(_run_task, task): task for task in tasks
    }

    for future in as_completed(futures):
        task = futures[future]
        try:
            role, resp = future.result()
            responses[role] = resp
            if on_done:
                on_done(role, resp)
        except Exception as exc:
            logger.error("Parallel task failed for %s: %s", task.role.value, exc)
            errors[task.role] = str(exc)
            if on_error:
                on_error(task.role, exc)

    return ParallelResult(responses=responses, errors=errors)
