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
from core.parallel import parallel_ask, ParallelTask

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
        cancel_check: Optional[Callable[[], bool]] = None,
    ):
        self.orch = orchestrator
        self.on_phase_start = on_phase_start
        self.on_step_done = on_step_done
        self.on_phase_done = on_phase_done
        self._cancel_check = cancel_check

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

    def _check_cancelled(self) -> None:
        """Raise if the run has been cancelled."""
        if self._cancel_check and self._cancel_check():
            raise RuntimeError("Pipeline cancelled by user")

    def _scratchpad_context(self) -> str:
        """Return scratchpad summary if available, empty string otherwise."""
        scratchpad = getattr(self.orch, "_scratchpad", None)
        if scratchpad is None:
            return ""
        summary = scratchpad.summarize(max_chars=1200)
        if summary == "(scratchpad is empty)":
            return ""
        return f"\n\n{summary}\n"

    def _ask(
        self,
        phase_name: str,
        step_name: str,
        role: Role,
        prompt: str,
    ) -> AgentResponse:
        """Ask one role for one step and emit callback."""
        self._check_cancelled()

        # Inject scratchpad context so agents see shared state
        pad_ctx = self._scratchpad_context()
        if pad_ctx:
            prompt = f"{prompt}\n{pad_ctx}"

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
1. Use write_file to create planning/plan.markdown with:
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
        """Implement code and QA artifacts.

        Flow:
        1. BA       — break plan into implementation tasks + acceptance criteria
        2. Senior   — architecture design, sequencing, coordination
        3. QA       — upfront test strategy and quality gates
        4. Coder    — primary implementation
        5. Coder 2  — secondary/parallel implementation
        6. Reviewer  — code review
        7. BA + Senior — final sign-off review
        """

        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}
        project = ctx.get("project_name", "project")
        requirement = ctx.get("requirement", "")
        planning_summary = self._clip(
            ctx.get("ba_planning_package", ""),
            MAX_PLANNING_SUMMARY_CHARS,
        )

        # ── Step 1: BA — Implementation task breakdown ──────────────────
        ba_impl_prompt = f"""You are the Business Analyst for project "{project}".

Planning summary:
{planning_summary}

Requirement:
{requirement}

Break the plan into concrete implementation tasks:
1. Use write_file to create implementation/task_breakdown.markdown with:
   - Numbered implementation tasks (TASK-001, TASK-002, etc.)
   - Clear acceptance criteria per task
   - Priority ordering (P0 critical, P1 high, P2 normal)
   - Dependencies between tasks
   - Suggested owner role (coder, coder_2, coder_3, qa)
2. Use write_file to create implementation/acceptance_criteria.markdown with:
   - Definition of done per task
   - Business validation rules
   - User-facing expectations

Rules:
- Be specific and actionable — no vague tasks.
- Every task must have clear acceptance criteria.
- Order tasks by dependency then priority.
"""
        ba_resp = self._ask("implementation", "ba_task_breakdown", Role.BA, ba_impl_prompt)
        outputs["ba_task_breakdown"] = ba_resp

        ba_summary = self._clip(ba_resp.content, MAX_IMPL_SUMMARY_CHARS)

        # ── Step 2: Senior Dev — Architecture + coordination ────────────
        senior_prompt = f"""You are the Senior Developer / Architect for project "{project}".

Requirement:
{requirement}

BA task breakdown:
{ba_summary}

Design the implementation architecture and coordinate the build:
1. Use write_file to create implementation/architecture.markdown with:
   - System architecture (components, data flow, interfaces)
   - Technology decisions and rationale
   - File/module structure to implement
   - Sequencing: which tasks to build first and why
   - Integration points between components
2. Use write_file to create implementation/coding_guidelines.markdown with:
   - Coding standards for this project
   - Error handling patterns
   - Naming conventions
   - Critical constraints the coders must follow

Rules:
- Make architecture decisions concrete — specify exact files, modules, patterns.
- Address each task from the BA breakdown with technical direction.
- Flag any risks or blockers the coders should know about.
"""
        senior_resp = self._ask("implementation", "senior_architecture", Role.SENIOR_DEV, senior_prompt)
        outputs["senior_architecture"] = senior_resp

        arch_summary = self._clip(senior_resp.content, MAX_IMPL_SUMMARY_CHARS)

        # ── Step 3: QA — Upfront test strategy ──────────────────────────
        qa_strategy_prompt = f"""You are QA lead for project "{project}".

BA task breakdown:
{ba_summary}

Architecture design:
{arch_summary}

Define the test strategy BEFORE coding begins:
1. Use write_file to create quality/test_strategy.markdown with:
   - Test approach per task (unit, integration, e2e)
   - Critical test scenarios and edge cases
   - Quality gates that must pass before code is accepted
   - Risk areas needing extra coverage
2. Use write_file to create quality/test_cases_spec.markdown with:
   - Specific test case outlines (TC-001, TC-002, etc.)
   - Input/output expectations
   - Boundary conditions

Rules:
- Define quality gates the reviewer will use later.
- Be specific about what "passing" means for each task.
"""
        qa_strategy_resp = self._ask("implementation", "qa_test_strategy", Role.QA, qa_strategy_prompt)
        outputs["qa_test_strategy"] = qa_strategy_resp

        qa_summary = self._clip(qa_strategy_resp.content, MAX_IMPL_SUMMARY_CHARS)

        # ── Steps 4-5: Parallel Coder + Coder 2 implementation ─────────
        # Both coders run simultaneously with the same architecture/QA context.
        # They use the shared scratchpad to coordinate and avoid duplication.
        pad_ctx = self._scratchpad_context()

        coder_prompt = f"""You are the primary developer for project "{project}".

Requirement:
{requirement}

Architecture design:
{arch_summary}

QA test strategy (your code must satisfy these quality gates):
{qa_summary}
{pad_ctx}
Do all of the following:
1. Use scratchpad_write to record which modules/files you are implementing (key: "coder_modules", category: "status").
2. Use get_tree and read_file to inspect any existing files.
3. Implement the primary source files with write_file — follow the architecture design.
4. Write unit tests alongside your code.
5. Create or update README/run instructions if needed.
6. Use write_file to create implementation/coder_summary.markdown listing what you built.
{"7. If GitHub MCP tools are available, prepare branch and PR notes in implementation/github_notes.markdown." if has_github else ""}

Rules:
- Write real, complete, working code — not stubs or pseudocode.
- Follow the coding guidelines from the senior dev.
- Ensure your code is testable per the QA strategy.
- Address the BA's acceptance criteria for each task you implement.
- Use scratchpad_write to record key decisions and artifacts as you work.
"""

        coder2_prompt = f"""You are the secondary developer for project "{project}".

Requirement:
{requirement}

Architecture design:
{arch_summary}

QA test strategy:
{qa_summary}
{pad_ctx}
You are running IN PARALLEL with the primary coder. To avoid duplication:
1. Use scratchpad_list to check what the primary coder is working on.
2. Use scratchpad_write to record which modules/files you are implementing (key: "coder2_modules", category: "status").
3. Focus on complementary modules, supporting code, and integration layers.
4. Implement your assigned source files with write_file.
5. Add integration tests or additional unit tests.
6. Use write_file to create implementation/coder2_summary.markdown with what you built and any concerns.

Rules:
- Coordinate via scratchpad to avoid duplicating the primary coder's work.
- Focus on gaps, edge cases, and integration code.
- Write real code, not descriptions.
- Use scratchpad_write to record key decisions and artifacts as you work.
"""

        self._check_cancelled()
        logger.info("[implementation] Running Coder + Coder 2 in parallel")

        parallel_result = parallel_ask(
            self.orch,
            tasks=[
                ParallelTask(role=Role.CODER, prompt=coder_prompt, label="coder_implementation"),
                ParallelTask(role=Role.CODER_2, prompt=coder2_prompt, label="coder2_implementation"),
            ],
        )

        # Collect results — gracefully handle partial failures
        coder_resp = parallel_result.responses.get(Role.CODER)
        coder2_resp = parallel_result.responses.get(Role.CODER_2)

        if coder_resp:
            outputs["coder_implementation"] = coder_resp
            if self.on_step_done:
                self.on_step_done("implementation", "coder_implementation", coder_resp)
        if coder2_resp:
            outputs["coder2_implementation"] = coder2_resp
            if self.on_step_done:
                self.on_step_done("implementation", "coder2_implementation", coder2_resp)

        # Log errors but don't fail the pipeline if at least one coder succeeded
        for role, error in parallel_result.errors.items():
            logger.warning("Parallel coder %s failed: %s", role.value, error)

        if not coder_resp and not coder2_resp:
            raise RuntimeError(
                f"Both coders failed: {parallel_result.errors}"
            )

        coder_content = coder_resp.content if coder_resp else "(coder failed)"
        coder2_content = coder2_resp.content if coder2_resp else "(coder 2 failed)"
        combined_code_summary = coder_content + "\n\n" + coder2_content

        coder3_prompt = f"""You are the implementation finisher for project "{project}".

Requirement:
{requirement}

Architecture design:
{arch_summary}

QA test strategy:
{qa_summary}

Implementation summary from the first two coding passes:
{self._clip(combined_code_summary, MAX_IMPL_SUMMARY_CHARS)}
{pad_ctx}
You are working AFTER the primary and secondary coders. Your job is to improve the final result:
1. Use scratchpad_list to review prior coding ownership and open issues.
2. Use scratchpad_write to record what you are polishing (key: "coder3_modules", category: "status").
3. Use get_tree and read_file to inspect what was built.
4. Improve integration seams, UX details, error states, consistency, and final implementation rough edges with write_file.
5. Add or tighten tests if your changes need them.
6. Use write_file to create implementation/coder3_summary.markdown with what you improved and any unresolved risks.

Rules:
- Do not duplicate the main implementation work.
- Focus on high-leverage cleanup, polish, integration hardening, and UX improvements.
- Preserve the existing architecture unless you find a concrete issue.
- Use scratchpad_write to record key decisions and artifacts as you work.
"""
        coder3_resp = self._ask("implementation", "coder3_polish", Role.CODER_3, coder3_prompt)
        outputs["coder3_polish"] = coder3_resp

        coder3_content = coder3_resp.content if coder3_resp else "(coder 3 failed)"

        all_code_summary = self._clip(
            combined_code_summary + "\n\n" + coder3_content,
            MAX_IMPL_SUMMARY_CHARS,
        )

        # ── Step 6: Reviewer — Code review ──────────────────────────────
        reviewer_prompt = f"""You are the Code Reviewer for project "{project}".

Architecture design:
{arch_summary}

QA quality gates:
{qa_summary}

Implementation summary (all coding passes):
{all_code_summary}

Review the implementation:
1. Use read_file and get_tree to inspect what was built.
2. Use write_file to create review/code_review.markdown with:
   - Review verdict: APPROVED / CHANGES_REQUESTED / BLOCKED
   - Issues found (severity: critical, major, minor)
   - Architecture compliance check
   - Code quality assessment
   - Security concerns
   - Performance concerns
3. If critical issues are found, use write_file to document required fixes in review/required_fixes.markdown.

Rules:
- Be thorough but pragmatic — not every style preference is a blocker.
- Check against the QA quality gates and BA acceptance criteria.
- Focus on correctness, security, and maintainability.
"""
        reviewer_resp = self._ask("implementation", "reviewer_code_review", Role.REVIEWER, reviewer_prompt)
        outputs["reviewer_code_review"] = reviewer_resp

        review_summary = self._clip(reviewer_resp.content, MAX_IMPL_SUMMARY_CHARS)

        # ── Step 7: BA + Senior Dev — Final sign-off ────────────────────
        signoff_prompt = f"""You are conducting the final implementation sign-off for project "{project}".

Requirement:
{requirement}

Code review result:
{review_summary}

Implementation summary:
{all_code_summary}

Provide the final sign-off assessment:
1. Use write_file to create implementation/implementation_summary.markdown with:
   - Overall status: APPROVED / NEEDS_WORK
   - What was built (files, features, tests)
   - What's still pending or deferred
   - Acceptance criteria pass/fail per BA task
   - Architecture compliance per senior dev design
   - Key risks going forward
2. Use write_file to create quality/final_assessment.markdown with quality summary.

Rules:
- Be honest about gaps — don't rubber-stamp incomplete work.
- Reference specific acceptance criteria from the BA breakdown.
"""
        signoff_resp = self._ask("implementation", "senior_ba_signoff", Role.SENIOR_DEV, signoff_prompt)
        outputs["senior_ba_signoff"] = signoff_resp

        # ── Step 8: QA — Final test assets + Excel plan ─────────────────
        qa_final_prompt = f"""You are QA finalizing test assets for project "{project}".

Implementation summary:
{all_code_summary}

Review result:
{review_summary}

Do all of the following:
1. Use write_file to create/update test files based on what was actually built.
2. Use create_test_plan_excel to create quality/test_plan.xlsx.
   - file_path: quality/test_plan.xlsx
   - suite_name: "{project} core test plan"
   - test_cases: JSON array with id, title, steps, expected_result, priority, status, category
3. Use write_file to create quality/issues_for_tracking.txt with defects/risks found.
4. If run_tests is available, run relevant tests and report outcomes in quality/test_results.markdown.

Rules:
- Ensure the Excel tool call is actually executed.
- Keep defects specific and actionable.
- Reference the reviewer's findings in your test priorities.
"""
        qa_final_resp = self._ask("implementation", "qa_quality_assets", Role.QA, qa_final_prompt)
        outputs["qa_quality_assets"] = qa_final_resp

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
4. Use write_file to create github/github_sync.markdown summarizing repo, issues, and next actions.

Rules:
- Actually call GitHub tools; do not just describe what you would do.
- If any GitHub action fails, record fallback instructions in github/github_sync.markdown.
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
2. github/issues_board.markdown - grouped by priority and status.
3. github/github_mcp_fallback.markdown - exact steps to sync these issues to GitHub later.

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
