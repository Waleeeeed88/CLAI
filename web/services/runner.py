"""Runner — bridges the synchronous orchestrator to the async SSE layer.

Design:
  - Creates a fresh Orchestrator per request (stateless per run).
  - Monkey-patches _build_tool_registry to wrap every ToolRegistry in an
    ObservableToolRegistry so tool call/result events are emitted in real time.
  - Monkey-patches _ask_with_limits and ask to emit agent_start/agent_done.
  - All work runs in a ThreadPoolExecutor thread; events flow via EventBus.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, Tuple

from agents.factory import Role
from core.orchestrator import Orchestrator
from core.tool_registry import ToolRegistry
from .event_bus import EventBus
from .observable_registry import ObservableToolRegistry

_executor = ThreadPoolExecutor(max_workers=4)


def _format_runtime_error(exc: Exception) -> str:
    text = str(exc)
    lower = text.lower()
    if "rate_limit" in lower or "rate limit" in lower or " 429" in lower or "429 " in lower:
        return (
            "Provider rate limit hit (429). The run used too much request context too quickly. "
            "Try again after a short wait, or reduce selected files/context size."
        )
    return f"{type(exc).__name__}: {exc}"


def _make_tool_callbacks(
    bus: EventBus, role: Role
) -> Tuple[Callable, Callable]:
    """Create on_call / on_result closures bound to a specific role."""

    def on_call(name: str, args: Dict[str, Any]) -> None:
        bus.put({
            "type": "tool_call",
            "agent": role.value,
            "tool": name,
            "args": {k: str(v)[:200] for k, v in args.items()},
        })

    def on_result(name: str, result: str, success: bool = True) -> None:
        bus.put({
            "type": "tool_result",
            "agent": role.value,
            "tool": name,
            "preview": result[:300] if result else "",
            "success": success,
        })

    return on_call, on_result


def _instrument_orchestrator(orch: Orchestrator, bus: EventBus, context_label: str) -> None:
    """Wrap tool registries and agent calls to emit SSE events."""

    # --- Patch _build_tool_registry so every built registry is observable ---
    _orig_build = orch._build_tool_registry

    def _patched_build(role: Role) -> Optional[ToolRegistry]:
        inner = _orig_build(role)
        if inner is None:
            return None
        on_call, on_result = _make_tool_callbacks(bus, role)
        return ObservableToolRegistry(inner, on_call=on_call, on_result=on_result)

    orch._build_tool_registry = _patched_build

    # Invalidate any cached agents so they rebuild with observable registries
    orch._agents.clear()

    # --- Patch _ask_with_limits (used by stages) ---
    _orig_ask_limits = orch._ask_with_limits

    def _instrumented_ask_limits(
        role: Role, prompt: str, max_tokens: int, temperature=None
    ):
        bus.put({
            "type": "agent_start",
            "agent": role.value,
            "context": context_label,
        })
        try:
            resp = _orig_ask_limits(role, prompt, max_tokens, temperature)
        except Exception as exc:
            bus.put({
                "type": "agent_done",
                "agent": role.value,
                "content": f"[error] {_format_runtime_error(exc)}",
                "tokens": 0,
                "model": "unknown",
            })
            raise
        bus.put({
            "type": "agent_done",
            "agent": role.value,
            "content": resp.content,
            "tokens": resp.total_tokens,
            "model": resp.model,
        })
        return resp

    orch._ask_with_limits = _instrumented_ask_limits

    # --- Patch ask (used by workflows) ---
    _orig_ask = orch.ask

    def _instrumented_ask(role: Role, prompt: str, include_history: bool = False):
        bus.put({
            "type": "agent_start",
            "agent": role.value,
            "context": context_label,
        })
        try:
            resp = _orig_ask(role, prompt, include_history)
        except Exception as exc:
            bus.put({
                "type": "agent_done",
                "agent": role.value,
                "content": f"[error] {_format_runtime_error(exc)}",
                "tokens": 0,
                "model": "unknown",
            })
            raise
        bus.put({
            "type": "agent_done",
            "agent": role.value,
            "content": resp.content,
            "tokens": resp.total_tokens,
            "model": resp.model,
        })
        return resp

    orch.ask = _instrumented_ask

    # --- Patch consult_team_discussion (used by some workflows) ---
    _orig_discuss = getattr(orch, "consult_team_discussion", None)
    if _orig_discuss:
        def _instrumented_discuss(prompt, roles=None, **kwargs):
            bus.put({
                "type": "phase_start",
                "phase": f"{context_label} · roundtable",
            })
            result = _orig_discuss(prompt, roles=roles, **kwargs)
            bus.put({
                "type": "phase_done",
                "phase": f"{context_label} · roundtable",
                "status": "completed",
            })
            return result
        orch.consult_team_discussion = _instrumented_discuss


def run_stage_async(
    stage_name: str, context: Dict[str, str], bus: EventBus,
    workspace_dir: Optional[str] = None,
) -> None:
    """Submit a stage run to the thread pool. Returns immediately."""

    def _run():
        try:
            bus.put({"type": "phase_start", "phase": stage_name})
            orch = Orchestrator(verbose=False, workspace_root=workspace_dir)
            _instrument_orchestrator(orch, bus, stage_name)
            result = orch.run_stage(stage_name, context)
            bus.put({
                "type": "phase_done",
                "phase": stage_name,
                "status": result.status.value,
                "duration": result.duration,
            })
            bus.put({
                "type": "stage_complete",
                "stage": stage_name,
                "status": result.status.value,
                "steps": result.steps_completed,
                "duration": result.duration,
            })
        except Exception as e:
            bus.put({"type": "error", "message": _format_runtime_error(e)})
        finally:
            bus.close()

    _executor.submit(_run)


def run_workflow_async(
    workflow_name: str, context: Dict[str, str], bus: EventBus,
    workspace_dir: Optional[str] = None,
) -> None:
    """Submit a workflow run to the thread pool. Returns immediately."""

    def _run():
        try:
            bus.put({"type": "phase_start", "phase": workflow_name})
            orch = Orchestrator(verbose=False, workspace_root=workspace_dir)
            _instrument_orchestrator(orch, bus, workflow_name)
            result = orch.run_workflow(workflow_name, context)
            bus.put({
                "type": "phase_done",
                "phase": workflow_name,
                "status": result.status.value,
                "duration": result.duration,
            })
            bus.put({
                "type": "workflow_complete",
                "workflow": workflow_name,
                "status": result.status.value,
                "steps": result.steps_completed,
                "duration": result.duration,
            })
        except Exception as e:
            bus.put({"type": "error", "message": _format_runtime_error(e)})
        finally:
            bus.close()

    _executor.submit(_run)


def run_pipeline_async(
    requirement: str, project_name: str, bus: EventBus,
    workspace_dir: Optional[str] = None,
    use_github: bool = False,
    selected_phases: Optional[List[str]] = None,
    selected_files: Optional[List[str]] = None,
) -> None:
    """Submit a full project pipeline to the thread pool. Returns immediately."""

    def _run():
        try:
            from core.pipeline import ProjectPipeline, PhaseResult

            orch = Orchestrator(verbose=False, workspace_root=workspace_dir)
            _instrument_orchestrator(orch, bus, "pipeline")

            def on_phase_start(phase_name: str):
                bus.put({"type": "phase_start", "phase": phase_name})

            def on_phase_done(result: PhaseResult):
                bus.put({
                    "type": "phase_done",
                    "phase": result.name,
                    "status": result.status.value,
                    "duration": result.duration,
                })

            pipeline = ProjectPipeline(
                orch,
                on_phase_start=on_phase_start,
                on_phase_done=on_phase_done,
                cancel_check=lambda: bus.is_cancelled,
            )
            final = pipeline.run(
                requirement=requirement,
                project_name=project_name,
                skip_github=not use_github,
                selected_phases=selected_phases,
                selected_files=selected_files,
            )
            bus.put({
                "type": "pipeline_complete",
                "status": final.status.value,
            })
        except Exception as e:
            bus.put({"type": "error", "message": _format_runtime_error(e)})
        finally:
            bus.close()

    _executor.submit(_run)
