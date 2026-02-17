"""Project Pipeline — orchestrates a full project lifecycle.

Runs a multi-phase pipeline that feels like managing an IT team:
  1. Planning   — BA leads discussion, creates user stories
  2. Setup      — Senior architects, repo + scaffolding created
  3. Build      — Coders implement on branches, create PRs
  4. Quality    — QA writes tests, creates Excel test plan, runs tests
  5. Review     — Reviewer reviews PRs, posts feedback
  6. Delivery   — Senior produces final summary, localhost instructions

Usage::

    from core.pipeline import ProjectPipeline
    pipeline = ProjectPipeline(orchestrator)
    pipeline.run("Build a task management API with auth")
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


# ── Data models ──────────────────────────────────────────────────────

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
    artifacts: Dict[str, str] = field(default_factory=dict)  # e.g. {"repo_url": "..."}
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0


@dataclass
class PipelineResult:
    """Output of the full project pipeline."""
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


# ── Pipeline ─────────────────────────────────────────────────────────

class ProjectPipeline:
    """Multi-phase project pipeline that coordinates the full AI team.

    Args:
        orchestrator: The ``Orchestrator`` instance (provides agents + tools).
        on_phase_start: Optional callback ``(phase_name) -> None``.
        on_step_done: Optional callback ``(phase_name, step_name, response) -> None``.
        on_phase_done: Optional callback ``(PhaseResult) -> None``.
    """

    def __init__(
        self,
        orchestrator: Any,  # core.orchestrator.Orchestrator (avoid circular import)
        *,
        on_phase_start: Optional[Callable[[str], None]] = None,
        on_step_done: Optional[Callable[[str, str, AgentResponse], None]] = None,
        on_phase_done: Optional[Callable[[PhaseResult], None]] = None,
    ):
        self.orch = orchestrator
        self.on_phase_start = on_phase_start
        self.on_step_done = on_step_done
        self.on_phase_done = on_phase_done

    # ── public entry point ───────────────────────────────────────────

    def run(
        self,
        requirement: str,
        project_name: str = "",
        repo_owner: str = "",
        skip_github: bool = False,
    ) -> PipelineResult:
        """Execute the full project pipeline.

        Args:
            requirement: The project description / feature request.
            project_name: Desired project/repo name (auto-generated if empty).
            repo_owner: GitHub owner (user or org) for repo creation.
            skip_github: If ``True``, skip GitHub operations (offline mode).
        """
        result = PipelineResult(project_name=project_name or "project")

        # Shared context that accumulates across phases
        ctx: Dict[str, str] = {
            "requirement": requirement,
            "project_name": project_name,
            "repo_owner": repo_owner,
        }

        has_github = (
            not skip_github
            and self.orch.github_configured
        )
        ctx["has_github"] = str(has_github)

        phases = [
            ("planning", self._phase_planning),
            ("setup", self._phase_setup),
            ("build", self._phase_build),
            ("quality", self._phase_quality),
            ("review", self._phase_review),
            ("delivery", self._phase_delivery),
        ]

        t0 = time.time()
        for phase_name, phase_fn in phases:
            if self.on_phase_start:
                self.on_phase_start(phase_name)

            try:
                phase_result = phase_fn(ctx, has_github)
            except Exception as exc:
                logger.error(f"Phase {phase_name} failed: {exc}", exc_info=True)
                phase_result = PhaseResult(
                    name=phase_name,
                    status=PhaseStatus.FAILED,
                    errors=[str(exc)],
                )

            result.phases[phase_name] = phase_result

            if self.on_phase_done:
                self.on_phase_done(phase_result)

            # Feed phase outputs into shared context for later phases
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

    # ── helper: ask an agent inside a phase ──────────────────────────

    def _ask(
        self,
        phase_name: str,
        step_name: str,
        role: Role,
        prompt: str,
    ) -> AgentResponse:
        """Ask an agent and fire the on_step_done callback."""
        logger.info(f"[{phase_name}] {step_name}: asking {role.value}")
        response = self.orch.ask(role, prompt)
        if self.on_step_done:
            self.on_step_done(phase_name, step_name, response)
        return response

    # ── Phase 1: Planning ────────────────────────────────────────────

    def _phase_planning(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """BA analyses requirements, team discusses, BA finalises stories."""
        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}

        # 1a — BA creates user stories + acceptance criteria
        ba_prompt = f"""You are starting a new project. Analyse the following requirement and produce:

1. **Project Overview** — one paragraph summary
2. **User Stories** — numbered list, each with:
   - Title
   - As a / I want / So that
   - Acceptance Criteria (Given/When/Then)
   - Priority (P0/P1/P2)
   - Estimated complexity (S/M/L/XL)
3. **Non-Functional Requirements** — performance, security, scalability
4. **Open Questions** — anything that needs clarification

{"Use the `create_repository` tool to create a GitHub repo named " + repr(ctx.get("project_name", "")) + " if a name was provided, then use `create_issue` to create a GitHub issue for EACH user story with labels." if has_github else "List all stories in structured format."}

Requirement:
{ctx['requirement']}"""

        resp = self._ask("planning", "ba_stories", Role.BA, ba_prompt)
        outputs["ba_stories"] = resp

        # 1b — Team roundtable discussion
        discussion = self.orch.consult_team_discussion(
            f"Project requirement:\n{ctx['requirement']}\n\nBA's analysis:\n{resp.content[:2000]}",
            roles=[Role.QA, Role.SENIOR_DEV, Role.CODER, Role.CODER_2],
        )
        for role, dresp in discussion.items():
            key = f"discuss_{role.value}"
            outputs[key] = dresp

        return PhaseResult(
            name="planning",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            duration=time.time() - t0,
        )

    # ── Phase 2: Setup ───────────────────────────────────────────────

    def _phase_setup(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """Senior Dev designs architecture and creates project scaffolding."""
        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}

        prior_ba = ctx.get("ba_stories", "")[:3000]
        prior_discussion = "\n".join(
            f"[{k}]: {v[:600]}" for k, v in ctx.items() if k.startswith("discuss_")
        )

        # 2a — Senior Dev: architecture document
        arch_prompt = f"""Based on the BA's analysis and team discussion, design the full project architecture.

**Deliverables (use your file tools to CREATE these files)**:
1. Write `architecture.md` — system design, components, data model, API routes, tech stack
2. Write `project_structure.md` — directory layout, file responsibilities
3. Create the initial directory structure using `create_directory` and `write_file`:
   - Source directories, config files, README.md, .gitignore, requirements.txt / package.json
   - Include placeholder files so the structure is visible

{"4. Use `create_branch` to create a `develop` branch on the repo if GitHub tools are available." if has_github else ""}

Project name: {ctx.get('project_name', 'project')}

BA Analysis:
{prior_ba}

Team Discussion:
{prior_discussion}"""

        resp = self._ask("setup", "senior_architecture", Role.SENIOR_DEV, arch_prompt)
        outputs["senior_architecture"] = resp

        return PhaseResult(
            name="setup",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            duration=time.time() - t0,
        )

    # ── Phase 3: Build ───────────────────────────────────────────────

    def _phase_build(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """Coders implement features, create branches + PRs."""
        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}

        prior_arch = ctx.get("senior_architecture", "")[:3000]
        prior_ba = ctx.get("ba_stories", "")[:2000]

        # 3a — Primary Coder: implement core features
        coder_prompt = f"""Implement the project based on the architecture and user stories below.

**Your tasks**:
1. Use `read_file` and `get_tree` to see what the Senior Dev already created
2. Use `write_file` to create ALL source code files — models, routes/handlers, services, utilities, config
3. Write COMPLETE, WORKING code — not pseudocode or placeholders
4. Include proper imports, error handling, logging
5. Add docstrings and type hints
{"6. Use `create_branch` to create a feature branch (e.g. `feature/core-implementation`), then use `push_files` or `create_or_update_file` to push your code, and `create_pull_request` to open a PR to `develop`" if has_github else ""}

Architecture:
{prior_arch}

User Stories:
{prior_ba}"""

        resp = self._ask("build", "coder_implementation", Role.CODER, coder_prompt)
        outputs["coder_implementation"] = resp

        # 3b — Secondary Coder: implement remaining features / complementary work
        coder2_prompt = f"""You are the secondary coder. The primary coder has already started implementation.

**Your tasks**:
1. Use `get_tree` and `read_file` to see what exists already
2. Implement any REMAINING features, utilities, middleware, or config that the primary coder missed
3. Add any missing error handling, validation, or edge case coverage
4. Create helper scripts (e.g. `run.sh`, `Makefile`, startup scripts)
5. Write COMPLETE, WORKING code using `write_file`
{"6. Create a branch (e.g. `feature/secondary-implementation`), push code, and open a PR to `develop`" if has_github else ""}

What the primary coder built:
{resp.content[:2500]}

Architecture:
{prior_arch}"""

        resp2 = self._ask("build", "coder2_implementation", Role.CODER_2, coder2_prompt)
        outputs["coder2_implementation"] = resp2

        return PhaseResult(
            name="build",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            duration=time.time() - t0,
        )

    # ── Phase 4: Quality ─────────────────────────────────────────────

    def _phase_quality(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """QA writes tests, creates Excel test plan, runs tests."""
        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}

        prior_ba = ctx.get("ba_stories", "")[:1500]
        prior_coder = ctx.get("coder_implementation", "")[:2000]
        prior_coder2 = ctx.get("coder2_implementation", "")[:1500]

        qa_prompt = f"""You are the QA engineer. The coders have implemented the project. Your job:

1. **Read the code** — use `get_tree` to see what was built, then `read_file` on key files
2. **Write test files** — use `write_file` to create comprehensive test files:
   - Unit tests for each module
   - Integration tests for API endpoints / key flows
   - Edge case tests for boundary conditions
3. **Create Excel test plan** — use `create_test_plan_excel` with:
   - test_plan_name: a descriptive name
   - test_cases: list of dicts with keys: id, title, description, steps, expected_result, priority, status
   - Cover ALL user stories from the BA
4. **Run tests** — if `run_tests` is available, execute: pytest tests/ -v
{"5. If any tests fail, create GitHub issues for the failures using `create_issue`" if has_github else ""}

User Stories:
{prior_ba}

Coder 1 Output:
{prior_coder}

Coder 2 Output:
{prior_coder2}"""

        resp = self._ask("quality", "qa_testing", Role.QA, qa_prompt)
        outputs["qa_testing"] = resp

        return PhaseResult(
            name="quality",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            duration=time.time() - t0,
        )

    # ── Phase 5: Review ──────────────────────────────────────────────

    def _phase_review(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """Reviewer reviews code and PRs."""
        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}

        prior_coder = ctx.get("coder_implementation", "")[:2000]
        prior_qa = ctx.get("qa_testing", "")[:1500]

        reviewer_prompt = f"""You are the Code Reviewer. The project has been implemented and tested.

**Your tasks**:
1. Use `get_tree` and `read_file` to examine the actual code files
2. Review for:
   - Code quality, readability, maintainability
   - Security issues (injection, auth, validation)
   - Error handling completeness
   - Architecture adherence
   - Test coverage assessment
3. Produce a structured review:
   - **Overall Grade**: A/B/C/D/F
   - **Must Fix**: Critical issues
   - **Should Fix**: Important improvements
   - **Consider**: Nice-to-have suggestions
   - **What's Good**: Positive observations
{"4. If GitHub PR tools are available, use `list_pull_requests` to find open PRs, then `get_pull_request` to review them, and `create_pull_request_review` to post your review" if has_github else ""}

Implementation Summary:
{prior_coder}

QA Results:
{prior_qa}"""

        resp = self._ask("review", "reviewer_feedback", Role.REVIEWER, reviewer_prompt)
        outputs["reviewer_feedback"] = resp

        return PhaseResult(
            name="review",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            duration=time.time() - t0,
        )

    # ── Phase 6: Delivery ────────────────────────────────────────────

    def _phase_delivery(self, ctx: Dict[str, str], has_github: bool) -> PhaseResult:
        """Senior Dev produces final summary and run instructions."""
        t0 = time.time()
        outputs: Dict[str, AgentResponse] = {}

        prior_arch = ctx.get("senior_architecture", "")[:1500]
        prior_review = ctx.get("reviewer_feedback", "")[:1500]
        prior_qa = ctx.get("qa_testing", "")[:1000]

        delivery_prompt = f"""You are the Senior Dev wrapping up the project. Produce a **Delivery Summary**:

1. **Project Status** — what was built, current state
2. **Architecture Recap** — key design decisions made
3. **How to Run Locally**:
   - Step-by-step instructions to get it running on localhost
   - Required environment variables
   - Install commands
   - Start command
   - Expected output / test URL
4. **GitHub Status** — repo URL, branches, open PRs, issues
5. **Test Results** — summary from QA
6. **Review Notes** — key findings from code review
7. **Next Steps** — what should be done next

Also use `write_file` to create a `DELIVERY.md` file with this information.

Architecture:
{prior_arch}

Code Review:
{prior_review}

QA Results:
{prior_qa}"""

        resp = self._ask("delivery", "senior_delivery", Role.SENIOR_DEV, delivery_prompt)
        outputs["senior_delivery"] = resp

        return PhaseResult(
            name="delivery",
            status=PhaseStatus.COMPLETED,
            outputs=outputs,
            duration=time.time() - t0,
        )
