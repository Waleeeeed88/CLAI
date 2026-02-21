"""Simple project pipeline with three phases.

Flow:
1. planning        - define stories, tasks, and issue backlog
2. implementation  - build code and test assets (including Excel test plan)
3. github_mcp      - sync issues to GitHub MCP or produce local fallback files
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from agents import AgentResponse
from agents.factory import Role

logger = logging.getLogger(__name__)

MAX_REQUIREMENT_CHARS = 9000
MAX_SELECTED_FILES_CHARS = 1800
MAX_PLANNING_SUMMARY_CHARS = 1600
MAX_IMPL_SUMMARY_CHARS = 1300
MAX_GITHUB_PLAN_SUMMARY_CHARS = 1200


class PhaseStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """Output of a single pipeline phase."""

    name: str
    status: PhaseStatus
    outputs: Dict[str, AgentResponse] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0


@dataclass
class PipelineResult:
    """Output of the full pipeline."""

    project_name: str
    phases: Dict[str, PhaseResult] = field(default_factory=dict)
    total_duration: float = 0.0
    status: PhaseStatus = PhaseStatus.PENDING

    @property
    def all_outputs(self) -> Dict[str, AgentResponse]:
        merged: Dict[str, AgentResponse] = {}
        for phase in self.phases.values():
            merged.update(phase.outputs)
        return merged

    @property
    def all_artifacts(self) -> Dict[str, str]:
        merged: Dict[str, str] = {}
        for phase in self.phases.values():
            merged.update(phase.artifacts)
        return merged


class ProjectPipeline:
    """Simple multi-phase pipeline with planning, implementation, and GitHub sync."""

    ALL_PHASES = ["planning", "implementation", "github_mcp"]
    PHASE_DESCRIPTIONS: Dict[str, str] = {
        "planning": "Plan scope and produce issue backlog.",
        "implementation": "Build code and QA artifacts (including Excel test plan).",
        "github_mcp": "Sync issues via GitHub MCP or create local fallback issue files.",
    }

    def __init__(
        self,
        orchestrator: Any,
        *,
        on_phase_start: Optional[Callable[[str], None]] = None,
        on_step_done: Optional[Callable[[str, str, AgentResponse], None]] = None,
        on_phase_done: Optional[Callable[[PhaseResult], None]] = None,
    ):
        self.orch = orchestrator
        self.on_phase_start = on_phase_start
        self.on_step_done = on_step_done
        self.on_phase_done = on_phase_done

    @staticmethod
    def _clip(text: str, max_chars: int) -> str:
        if not text:
            return ""
        if len(text) <= max_chars:
            return text
        suffix = "\n...[truncated]"
        if max_chars <= len(suffix):
            return text[:max_chars]
        return f"{text[: max_chars - len(suffix)].rstrip()}{suffix}"

    def run(
        self,
        requirement: str,
        project_name: str = "",
        repo_owner: str = "",
        skip_github: bool = False,
        selected_phases: Optional[List[str]] = None,
        selected_files: Optional[List[str]] = None,
    ) -> PipelineResult:
        """Execute the three-phase pipeline."""

        result = PipelineResult(project_name=project_name or "project")
        requirement = self._clip(requirement or "", MAX_REQUIREMENT_CHARS)
        ctx: Dict[str, str] = {
            "requirement": requirement,
            "project_name": project_name or "project",
            "repo_owner": repo_owner,
        }
        if selected_files:
            cleaned = [p.strip() for p in selected_files if p and p.strip()]
            if cleaned:
                selected_blob = "\n".join(f"- {p}" for p in cleaned)
                ctx["selected_files"] = self._clip(selected_blob, MAX_SELECTED_FILES_CHARS)

        has_github = (not skip_github) and self.orch.github_available
        ctx["has_github"] = str(has_github)
        ctx["issue_tracking_mode"] = "github_mcp" if has_github else "local_txt"

        all_phases = [
            ("planning", self._phase_planning),
            ("implementation", self._phase_implementation),
            ("github_mcp", self._phase_github_mcp),
        ]
        if selected_phases is None:
            phases = all_phases
        else:
            selected_set = set(selected_phases)
            phases = [(name, fn) for name, fn in all_phases if name in selected_set]
            if not phases:
                result.status = PhaseStatus.FAILED
                result.total_duration = 0.0
                result.phases["selection"] = PhaseResult(
                    name="selection",
                    status=PhaseStatus.FAILED,
                    errors=["No valid phases selected. Choose at least one phase."],
                )
                return result

        t0 = time.time()
        for phase_name, phase_fn in phases:
            if self.on_phase_start:
                self.on_phase_start(phase_name)

            try:
                phase_result = phase_fn(ctx, has_github)
            except Exception as exc:
                logger.error("Phase %s failed: %s", phase_name, exc, exc_info=True)
                phase_result = PhaseResult(
                    name=phase_name,
                    status=PhaseStatus.FAILED,
                    errors=[str(exc)],
                )

            result.phases[phase_name] = phase_result

            if self.on_phase_done:
                self.on_phase_done(phase_result)

            for step_key, resp in phase_result.outputs.items():
                ctx[step_key] = resp.content
            for art_key, art_val in phase_result.artifacts.items():
                ctx[art_key] = art_val

            if phase_result.status == PhaseStatus.FAILED:
                result.status = PhaseStatus.FAILED
                break

        result.total_duration = time.time() - t0
        if result.status != PhaseStatus.FAILED:
            result.status = PhaseStatus.COMPLETED
        return result

    def _ask(
        self,
        phase_name: str,
        step_name: str,
        role: Role,
        prompt: str,
    ) -> AgentResponse:
        """Ask one role for one step and emit callback."""

        logger.info("[%s] %s: asking %s", phase_name, step_name, role.value)
        response = self.orch.ask(role, prompt)
        if self.on_step_done:
            self.on_step_done(phase_name, step_name, response)
        return response

    def _phase_planning(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """Create plan and issue backlog."""

        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}
        selected_files = ctx.get("selected_files", "none provided")
        issue_mode = "GitHub MCP issues" if has_github else "local text files"

        planning_prompt = f"""You are the planning lead for project "{ctx.get('project_name', 'project')}".

Requirement:
{ctx.get('requirement', '')}

Selected files from the user (optional context):
{selected_files}

Produce a practical planning package with these actions:
1. Use write_file to create planning/plan.md with:
   - scope summary
   - user stories with acceptance criteria
   - implementation slices
   - risks and assumptions
2. Use write_file to create planning/issues.txt with issue backlog in this format:
   ISSUE-001 | title | priority | owner | acceptance criteria
3. Use write_file to create planning/implementation_tasks.txt with clear build tasks.
4. Mention that issue tracking mode is: {issue_mode}

Rules:
- Keep outputs execution-oriented and concise.
- Do not skip file creation.
"""
        plan_resp = self._ask("planning", "ba_planning_package", Role.BA, planning_prompt)
        outputs["ba_planning_package"] = plan_resp

        return PhaseResult(
            name="planning",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            artifacts={"issue_tracking_mode": ctx["issue_tracking_mode"]},
            duration=time.time() - t0,
        )

    def _phase_implementation(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """Implement code and QA artifacts."""

        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}
        planning_summary = self._clip(
            ctx.get("ba_planning_package", ""),
            MAX_PLANNING_SUMMARY_CHARS,
        )

        implementation_prompt = f"""You are implementing project "{ctx.get('project_name', 'project')}".

Planning summary:
{planning_summary}

Requirement:
{ctx.get('requirement', '')}

Do all of the following:
1. Use get_tree and read_file to inspect existing files.
2. Implement required source files with write_file.
3. Update or create README/run instructions if needed.
4. Use write_file to create implementation/implementation_summary.md listing what was built and what's pending.
{"5. If GitHub MCP tools are available, prepare branch and PR notes in implementation/github_notes.md." if has_github else ""}

Rules:
- Write real code and concrete files.
- Keep architecture aligned with planning artifacts.
"""
        impl_resp = self._ask(
            "implementation",
            "coder_implementation",
            Role.CODER,
            implementation_prompt,
        )
        outputs["coder_implementation"] = impl_resp

        qa_prompt = f"""You are QA for project "{ctx.get('project_name', 'project')}".

Implementation summary:
{self._clip(impl_resp.content, MAX_IMPL_SUMMARY_CHARS)}

Do all of the following:
1. Use write_file to create/update test files.
2. Use create_test_plan_excel to create quality/test_plan.xlsx.
   - file_path: quality/test_plan.xlsx
   - suite_name: "<project name> core test plan"
   - test_cases: JSON array with id, title, steps, expected_result, priority, status, category
3. Use write_file to create quality/issues_for_tracking.txt with defects/risks found.
4. If run_tests is available, run relevant tests and report outcomes in quality/test_results.md.

Rules:
- Ensure the Excel tool call is actually executed.
- Keep defects specific and actionable.
"""
        qa_resp = self._ask("implementation", "qa_quality_assets", Role.QA, qa_prompt)
        outputs["qa_quality_assets"] = qa_resp

        return PhaseResult(
            name="implementation",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            artifacts={"excel_test_plan": "quality/test_plan.xlsx"},
            duration=time.time() - t0,
        )

    def _phase_github_mcp(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """Sync issues to GitHub or generate local fallback tracking files."""

        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}
        project_name = ctx.get("project_name", "project")
        requirement = ctx.get("requirement", "")
        plan_summary = ctx.get("ba_planning_package", "")[:2200]
        plan_summary = self._clip(plan_summary, MAX_GITHUB_PLAN_SUMMARY_CHARS)
        repo_owner = ctx.get("repo_owner", "")

        if has_github:
            github_prompt = f"""GitHub MCP is enabled for this project.

Project:
- name: {project_name}
- owner: {repo_owner or "(not provided, choose sensible default if needed)"}

Requirement:
{requirement}

Planning summary:
{plan_summary}

Execute GitHub synchronization tasks using MCP tools:
1. Ensure repository exists for this project (create_repository if needed).
2. Create GitHub issues from planning/issues.txt content (or planning summary when needed).
3. Label issues by priority/area where possible.
4. Use write_file to create github/github_sync.md summarizing repo, issues, and next actions.

Rules:
- Actually call GitHub tools; do not just describe what you would do.
- If any GitHub action fails, record fallback instructions in github/github_sync.md.
"""
            gh_resp = self._ask("github_mcp", "ba_github_sync", Role.BA, github_prompt)
            outputs["ba_github_sync"] = gh_resp
            artifacts = {"issue_tracking_mode": "github_mcp"}
        else:
            fallback_prompt = f"""GitHub MCP is NOT available for this run.

Project: {project_name}
Requirement:
{requirement}

Planning summary:
{plan_summary}

Create local issue tracking artifacts using write_file:
1. github/issues_local.txt - issues in a machine-friendly line format.
2. github/issues_board.md - grouped by priority and status.
3. github/github_mcp_fallback.md - exact steps to sync these issues to GitHub later.

Rules:
- Do not use GitHub tools.
- Ensure files are complete and actionable for later migration to GitHub.
"""
            fallback_resp = self._ask(
                "github_mcp",
                "ba_local_issue_tracking",
                Role.BA,
                fallback_prompt,
            )
            outputs["ba_local_issue_tracking"] = fallback_resp
            artifacts = {"issue_tracking_mode": "local_txt"}

        return PhaseResult(
            name="github_mcp",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            artifacts=artifacts,
            duration=time.time() - t0,
        )
