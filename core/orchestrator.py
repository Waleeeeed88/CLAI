"""Orchestrator - coordinates multi-agent workflows and stages."""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging

from agents import AgentFactory, AgentResponse, BaseAgent
from agents.factory import Role
from config import get_settings
from .workflows import WorkflowStatus, WorkflowStep, WorkflowResult
from .filesystem import FileSystemTools, get_filesystem
from .tool_registry import ToolRegistry
from .filesystem_tools import build_filesystem_registry

logger = logging.getLogger(__name__)

# Roles that receive filesystem tools
_FS_TOOL_ROLES = {Role.SENIOR_DEV, Role.CODER, Role.CODER_2, Role.QA, Role.BA, Role.REVIEWER}


class Orchestrator:
    def __init__(self, verbose: bool = False, workspace_root: Optional[str] = None):
        self.verbose = verbose
        self._agents: Dict[Role, BaseAgent] = {}
        self._workflows: Dict[str, List[WorkflowStep]] = {}
        self._stages: Dict[str, Dict[str, str]] = {}
        self._extra_registries: Dict[Role, ToolRegistry] = {}

        settings = get_settings()
        self._mcp_enabled = settings.mcp_enabled
        self._fs: Optional[FileSystemTools] = None
        self._fs_registry: Optional[ToolRegistry] = None
        if self._mcp_enabled:
            if workspace_root:
                self._fs = FileSystemTools(workspace_root=workspace_root)
            else:
                self._fs = get_filesystem()
            self._fs_registry = build_filesystem_registry(self._fs)

        # GitHub MCP client (lazy — connected on first use)
        self._github_client: Optional[Any] = None
        self._github_registries: Dict[str, ToolRegistry] = {}
        self._github_mcp_initialized = False
        self._github_settings: Optional[Any] = None

        # Excel & test runner tools
        self._excel_registry: Optional[ToolRegistry] = None
        self._test_runner_registry: Optional[ToolRegistry] = None
        self._init_extra_tools(settings)

        self._register_default_workflows()
        self._register_default_stages()

    def _init_extra_tools(self, settings) -> None:
        """Initialize Excel, test runner, and GitHub MCP tools."""
        # Excel test plan tool (always available if openpyxl is installed)
        try:
            from .excel_tools import build_excel_registry
            self._excel_registry = build_excel_registry(settings.workspace_path)
        except Exception as e:
            logger.debug(f"Excel tools not available: {e}")

        # Test runner tool
        try:
            from .test_runner import build_test_runner_registry
            self._test_runner_registry = build_test_runner_registry(settings.workspace_path)
        except Exception as e:
            logger.debug(f"Test runner not available: {e}")

        # GitHub MCP — store settings for lazy init (connected on first use)
        if settings.github_mcp_enabled and settings.github_token:
            self._github_settings = settings

    def _ensure_github_mcp(self) -> bool:
        """Lazily connect to the GitHub MCP server on first use.

        Returns True if GitHub tools are available, False otherwise.
        """
        if self._github_registries:
            return True

        settings = self._github_settings
        if settings is None:
            self._github_mcp_initialized = False
            return False

        try:
            self._init_github_mcp(settings)
            self._github_mcp_initialized = True
            return True
        except Exception as e:
            logger.warning(f"GitHub MCP initialization failed: {e}")
            self._github_mcp_initialized = False
            self._github_registries.clear()
            if self._github_client is not None:
                try:
                    self._github_client.disconnect_sync()
                except Exception:
                    pass
            self._github_client = None
            return False

    def _init_github_mcp(self, settings) -> None:
        """Launch the GitHub MCP server and build per-role registries."""
        from .mcp_client import MCPClient
        from .mcp_bridge import build_github_registry_for_role

        token = settings.github_token.get_secret_value()
        self._github_client = MCPClient(
            command=settings.github_mcp_command,
            args=settings.github_mcp_args_list,
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": token},
            server_name="github",
        )
        self._github_client.connect_sync()

        # Build scoped registries for each role
        for role_name in ("ba", "reviewer", "coder", "coder_2", "senior_dev", "qa"):
            self._github_registries[role_name] = build_github_registry_for_role(
                self._github_client, role_name
            )
        logger.info("GitHub MCP tools loaded for all roles")
    
    @property
    def github_available(self) -> bool:
        """Check if GitHub MCP is configured (and connect lazily if needed)."""
        return self._ensure_github_mcp()

    @property
    def github_configured(self) -> bool:
        """Check if GitHub MCP is configured (without connecting)."""
        return self._github_settings is not None

    @property
    def filesystem(self) -> Optional[FileSystemTools]:
        return self._fs

    def write_file(self, path: str, content: str) -> bool:
        if not self._fs:
            return False
        result = self._fs.write_file(path, content)
        return result.success

    def read_file(self, path: str) -> Optional[str]:
        if not self._fs:
            return None
        result = self._fs.read_file(path)
        return result.data if result.success else None

    # ── tool registry helpers ────────────────────────────────────────

    def register_tools_for_role(self, role: Role, registry: ToolRegistry) -> None:
        """Register additional tools for a specific role.

        These will be merged with the default tools (filesystem, etc.)
        when the agent for that role is created.
        """
        self._extra_registries[role] = registry
        # Invalidate cached agent so it gets rebuilt with new tools
        self._agents.pop(role, None)

    def _build_tool_registry(self, role: Role) -> Optional[ToolRegistry]:
        """Build the combined ToolRegistry for *role*."""
        registry = ToolRegistry()

        # Filesystem tools for eligible roles
        if self._fs_registry and role in _FS_TOOL_ROLES:
            registry.merge(self._fs_registry)

        # GitHub MCP tools (scoped per role, lazy-init on first use)
        if self._github_settings and not self._github_mcp_initialized:
            self._ensure_github_mcp()
        github_reg = self._github_registries.get(role.value)
        if github_reg:
            registry.merge(github_reg)

        # Excel test plan tool for QA
        if self._excel_registry and role in (Role.QA,):
            registry.merge(self._excel_registry)

        # Test runner for QA and coders
        if self._test_runner_registry and role in (Role.QA, Role.CODER, Role.CODER_2):
            registry.merge(self._test_runner_registry)

        # Extra tools registered externally
        extra = self._extra_registries.get(role)
        if extra:
            registry.merge(extra)

        return registry if registry else None

    def _get_agent(self, role: Role) -> BaseAgent:
        if role not in self._agents:
            tool_registry = self._build_tool_registry(role)
            self._agents[role] = AgentFactory.create_by_role(
                role, tool_registry=tool_registry
            )
        return self._agents[role]

    def _ask_with_limits(
        self,
        role: Role,
        prompt: str,
        max_tokens: int,
        temperature: Optional[float] = None,
    ) -> AgentResponse:
        """Use a short-lived agent instance for budgeted stage turns."""
        agent = AgentFactory.create_by_role(
            role=role,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if self.verbose:
            print(f"[{role.value}] Stage turn...")
        return agent.chat(prompt, include_history=False)
    
    def ask(self, role: Role, prompt: str, include_history: bool = False) -> AgentResponse:
        agent = self._get_agent(role)
        if self.verbose:
            print(f"[{role.value}] Processing...")
        response = agent.chat(prompt, include_history=include_history)
        if self.verbose:
            print(f"[{role.value}] Done ({response.total_tokens} tokens)")
        return response
    
    def consult_team(self, prompt: str, roles: Optional[List[Role]] = None) -> Dict[Role, AgentResponse]:
        if roles is None:
            roles = [Role.BA, Role.QA, Role.SENIOR_DEV, Role.CODER, Role.CODER_2, Role.REVIEWER]
        results = {}
        for role in roles:
            if self.verbose:
                print(f"Consulting {role.value}...")
            results[role] = self.ask(role, prompt)
        return results

    def consult_team_discussion(
        self,
        prompt: str,
        roles: Optional[List[Role]] = None,
        max_chars_per_turn: int = 1000,
        max_tokens_per_turn: int = 700,
    ) -> Dict[Role, AgentResponse]:
        """Run a BA-first roundtable where each role can react to previous roles."""
        if roles is None:
            roles = [Role.BA, Role.QA, Role.SENIOR_DEV, Role.CODER, Role.CODER_2]

        results: Dict[Role, AgentResponse] = {}
        turns: List[Tuple[Role, AgentResponse]] = []
        roster = ", ".join([role.value for role in roles])

        for role in roles:
            if self.verbose:
                print(f"Roundtable: {role.value}...")

            prior_discussion = self._build_turn_context(turns, max_chars_per_turn=max_chars_per_turn)
            turn_prompt = f"""Team roundtable discussion.
Topic:
{prompt}

Team roster:
{roster}

Prior discussion:
{prior_discussion}

Your response rules:
- Keep it under 170 words.
- Use headings: Position, Reply to Team, Next Action.
- If prior discussion exists, explicitly reply to at least one prior role.
- Focus on planning/coordination quality.
"""
            response = self._ask_with_limits(
                role=role,
                prompt=turn_prompt,
                max_tokens=max_tokens_per_turn,
                temperature=0.5,
            )
            results[role] = response
            turns.append((role, response))

        return results
    
    def register_workflow(self, name: str, steps: List[WorkflowStep]) -> None:
        self._workflows[name] = steps

    def register_stage(self, name: str, description: str, status: str = "placeholder") -> None:
        self._stages[name] = {"description": description, "status": status}
    
    def run_workflow(self, workflow_name: str, context: Dict[str, str]) -> WorkflowResult:
        if workflow_name not in self._workflows:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=0,
                errors=[f"Unknown workflow: {workflow_name}"],
            )
        
        steps = self._workflows[workflow_name]
        outputs: Dict[str, AgentResponse] = {}
        start_time = datetime.now()
        
        if self.verbose:
            print(f"Starting workflow: {workflow_name} ({len(steps)} steps)")
        
        for i, step in enumerate(steps):
            step_name = f"step_{i}_{step.role.value}"
            try:
                prompt = step.instruction
                for key, value in context.items():
                    prompt = prompt.replace(f"{{{key}}}", value)
                
                if step.depends_on:
                    dep_context = "\n\n---\nPrevious outputs:\n"
                    for dep in step.depends_on:
                        if dep in outputs:
                            dep_context += f"\n[{dep}]:\n{outputs[dep].content}\n"
                    prompt += dep_context
                    prompt += (
                        "\n\n---\nCoordination rules:\n"
                        "- Explicitly reference at least one depended step.\n"
                        "- State how your output aligns or disagrees with prior roles.\n"
                        "- Keep response actionable and concise.\n"
                    )
                
                if step.transform:
                    prompt = step.transform({"prompt": prompt, **context})
                
                if self.verbose:
                    print(f"  Step {i+1}/{len(steps)}: {step.role.value}")
                
                response = self.ask(step.role, prompt)
                outputs[step_name] = response
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                return WorkflowResult(
                    status=WorkflowStatus.FAILED,
                    steps_completed=i,
                    outputs=outputs,
                    errors=[f"Step {step_name} failed: {str(e)}"],
                    duration=duration,
                )
        
        duration = (datetime.now() - start_time).total_seconds()
        if self.verbose:
            print(f"Completed in {duration:.2f}s")
        
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            steps_completed=len(steps),
            outputs=outputs,
            duration=duration,
        )

    def run_stage(self, stage_name: str, context: Dict[str, str]) -> WorkflowResult:
        if stage_name not in self._stages:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=0,
                errors=[f"Unknown stage: {stage_name}"],
            )

        if stage_name == "planning_discussion":
            return self._run_planning_discussion_stage(context)
        elif stage_name == "architecture_alignment":
            return self._run_architecture_alignment_stage(context)
        elif stage_name == "implementation_breakdown":
            return self._run_implementation_breakdown_stage(context)
        elif stage_name == "verification_hardening":
            return self._run_verification_hardening_stage(context)
        elif stage_name == "release_handoff":
            return self._run_release_handoff_stage(context)

        return self._run_placeholder_stage(stage_name)
    
    def clear_context(self, role: Optional[Role] = None) -> None:
        if role:
            if role in self._agents:
                self._agents[role].clear_history()
        else:
            for agent in self._agents.values():
                agent.clear_history()
    
    def list_workflows(self) -> List[str]:
        return list(self._workflows.keys())

    def list_stages(self) -> List[str]:
        return list(self._stages.keys())

    def get_stages(self) -> Dict[str, Dict[str, str]]:
        return {name: details.copy() for name, details in self._stages.items()}

    def _build_turn_context(
        self,
        turns: List[Tuple[Role, AgentResponse]],
        max_chars_per_turn: int = 900,
    ) -> str:
        if not turns:
            return "No prior discussion yet."

        sections: List[str] = []
        for role, response in turns:
            snippet = response.content.strip()
            if len(snippet) > max_chars_per_turn:
                snippet = f"{snippet[:max_chars_per_turn].rstrip()}..."
            sections.append(f"[{role.value}]\n{snippet}")
        return "\n\n".join(sections)

    def _run_planning_discussion_stage(self, context: Dict[str, str]) -> WorkflowResult:
        topic = (
            context.get("requirement")
            or context.get("project_description")
            or context.get("topic")
            or context.get("prompt")
            or ""
        ).strip()
        if not topic:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=0,
                errors=["Missing stage context. Provide a requirement or topic."],
            )

        start_time = datetime.now()
        outputs: Dict[str, AgentResponse] = {}
        turns: List[Tuple[Role, AgentResponse]] = []

        turn_plan: List[Tuple[Role, str, int]] = [
            (
                Role.BA,
                "Lead with user stories, acceptance criteria, constraints, and open questions.",
                700,
            ),
            (
                Role.QA,
                "Create a concise test strategy and challenge weak assumptions from BA.",
                650,
            ),
            (
                Role.SENIOR_DEV,
                "Propose architecture direction and sequencing while addressing BA and QA feedback.",
                700,
            ),
            (
                Role.CODER,
                "Break implementation into thin, deliverable slices and call out dependencies.",
                700,
            ),
            (
                Role.CODER_2,
                "Offer an alternative implementation path and integration cautions.",
                650,
            ),
        ]

        try:
            for i, (role, instruction, token_budget) in enumerate(turn_plan):
                prior_discussion = self._build_turn_context(turns)
                turn_prompt = f"""You are in stage: planning_discussion.
Topic:
{topic}

Team roster and responsibilities:
- ba: requirements clarity, user stories, acceptance criteria.
- qa: test strategy, risks, quality gates.
- senior_dev: architecture, sequencing, technical tradeoffs.
- coder: implementation slices and delivery details.
- coder_2: alternative approach and integration cautions.

Prior discussion:
{prior_discussion}

Your turn objective:
{instruction}

Rules:
- Keep it under 180 words.
- Use exactly these headings: Position, Feedback to Team, Concrete Output.
- If prior discussion exists, directly respond to at least one earlier role.
- No code. Planning content only.
"""
                response = self._ask_with_limits(
                    role=role,
                    prompt=turn_prompt,
                    max_tokens=token_budget,
                    temperature=0.5,
                )
                outputs[f"step_{i}_{role.value}"] = response
                turns.append((role, response))

            synthesis_prompt = f"""You are finalizing stage: planning_discussion.
Topic:
{topic}

Full team discussion:
{self._build_turn_context(turns, max_chars_per_turn=1200)}

Provide a compact alignment summary with these headings only:
1) Agreed Plan
2) QA Gate Criteria
3) Engineering Sequencing
4) Open Risks

Rules:
- Keep total response under 220 words.
- No code.
"""
            final_response = self._ask_with_limits(
                role=Role.SENIOR_DEV,
                prompt=synthesis_prompt,
                max_tokens=750,
                temperature=0.4,
            )
            outputs["step_5_senior_dev"] = final_response

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=len(outputs),
                outputs=outputs,
                errors=[f"planning_discussion failed: {str(e)}"],
                duration=duration,
            )

        duration = (datetime.now() - start_time).total_seconds()
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            steps_completed=len(outputs),
            outputs=outputs,
            duration=duration,
        )

    def _run_architecture_alignment_stage(self, context: Dict[str, str]) -> WorkflowResult:
        topic = (
            context.get("requirement")
            or context.get("project_description")
            or context.get("topic")
            or context.get("prompt")
            or ""
        ).strip()
        if not topic:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=0,
                errors=["Missing stage context. Provide a requirement or topic."],
            )

        start_time = datetime.now()
        outputs: Dict[str, AgentResponse] = {}
        turns: List[Tuple[Role, AgentResponse]] = []

        turn_plan: List[Tuple[Role, str, int]] = [
            (
                Role.SENIOR_DEV,
                "Propose and justify the architecture: key components, data flow, tech stack, and main tradeoffs.",
                750,
            ),
            (
                Role.CODER,
                "Assess implementation feasibility, delivery risk, and dependency concerns from a developer's perspective.",
                700,
            ),
            (
                Role.CODER_2,
                "Offer alternative architectural approaches and flag integration or cross-cutting concerns.",
                650,
            ),
            (
                Role.QA,
                "Review the architecture for testability, observability gaps, and risk surface.",
                650,
            ),
            (
                Role.REVIEWER,
                "Evaluate code quality standards, anti-patterns, and long-term maintainability of the proposed design.",
                650,
            ),
        ]

        try:
            for i, (role, instruction, token_budget) in enumerate(turn_plan):
                prior_discussion = self._build_turn_context(turns)
                turn_prompt = f"""You are in stage: architecture_alignment.
Topic / Requirement:
{topic}

Team roster and responsibilities:
- senior_dev: architecture decisions, component design, tech-stack selection.
- coder: implementation feasibility, delivery risk, dependency management.
- coder_2: alternative approaches, integration concerns, cross-cutting patterns.
- qa: testability, observability, quality gates, risk surface.
- reviewer: code quality standards, anti-patterns, maintainability.

Prior discussion:
{prior_discussion}

Your turn objective:
{instruction}

Rules:
- Keep it under 180 words.
- Use exactly these headings: Architecture Position, Feedback to Prior Roles, Concrete Decision.
- If prior discussion exists, directly reference at least one earlier role.
- No implementation code. Architecture planning only.
"""
                response = self._ask_with_limits(
                    role=role,
                    prompt=turn_prompt,
                    max_tokens=token_budget,
                    temperature=0.5,
                )
                outputs[f"step_{i}_{role.value}"] = response
                turns.append((role, response))

            synthesis_prompt = f"""You are finalizing stage: architecture_alignment.
Topic:
{topic}

Full team discussion:
{self._build_turn_context(turns, max_chars_per_turn=1200)}

Provide a compact architectural alignment summary with these headings only:
1) Agreed Architecture
2) Key Technical Decisions
3) Risk Register
4) Definition of Done

Rules:
- Keep total response under 220 words.
- No code.
"""
            final_response = self._ask_with_limits(
                role=Role.SENIOR_DEV,
                prompt=synthesis_prompt,
                max_tokens=780,
                temperature=0.4,
            )
            outputs[f"step_{len(turn_plan)}_senior_dev"] = final_response

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=len(outputs),
                outputs=outputs,
                errors=[f"architecture_alignment failed: {str(e)}"],
                duration=duration,
            )

        duration = (datetime.now() - start_time).total_seconds()
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            steps_completed=len(outputs),
            outputs=outputs,
            duration=duration,
        )

    def _run_implementation_breakdown_stage(self, context: Dict[str, str]) -> WorkflowResult:
        topic = (
            context.get("requirement")
            or context.get("project_description")
            or context.get("topic")
            or context.get("prompt")
            or ""
        ).strip()
        if not topic:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=0,
                errors=["Missing stage context. Provide a requirement or topic."],
            )

        start_time = datetime.now()
        outputs: Dict[str, AgentResponse] = {}
        turns: List[Tuple[Role, AgentResponse]] = []

        turn_plan: List[Tuple[Role, str, int]] = [
            (
                Role.BA,
                "Break the requirement into discrete user stories and tasks with clear acceptance criteria and priority ordering.",
                700,
            ),
            (
                Role.SENIOR_DEV,
                "Size the tasks, establish sequencing and dependencies, and propose a sprint plan.",
                750,
            ),
            (
                Role.CODER,
                "Commit to specific delivery slices, call out implementation blockers, and clarify ownership.",
                700,
            ),
            (
                Role.CODER_2,
                "Identify parallel workstreams, alternative task groupings, and integration checkpoints.",
                650,
            ),
            (
                Role.QA,
                "Define test tasks tied to each delivery slice and specify quality gates per milestone.",
                650,
            ),
        ]

        try:
            for i, (role, instruction, token_budget) in enumerate(turn_plan):
                prior_discussion = self._build_turn_context(turns)
                turn_prompt = f"""You are in stage: implementation_breakdown.
Requirement:
{topic}

Team roster and responsibilities:
- ba: task clarity, acceptance criteria per task, priority ordering.
- senior_dev: task sizing, sequencing, dependencies, sprint planning.
- coder: delivery slices, blocker identification, task commitment.
- coder_2: parallel workstreams, alternative task groupings, integration checkpoints.
- qa: test tasks per delivery slice, quality gates per milestone.

Prior discussion:
{prior_discussion}

Your turn objective:
{instruction}

Rules:
- Keep it under 180 words.
- Use exactly these headings: Task Breakdown, Sequencing/Dependencies, Ownership.
- If prior discussion exists, directly reference at least one earlier role.
- No code. Task planning only.
"""
                response = self._ask_with_limits(
                    role=role,
                    prompt=turn_prompt,
                    max_tokens=token_budget,
                    temperature=0.5,
                )
                outputs[f"step_{i}_{role.value}"] = response
                turns.append((role, response))

            synthesis_prompt = f"""You are finalizing stage: implementation_breakdown.
Requirement:
{topic}

Full team discussion:
{self._build_turn_context(turns, max_chars_per_turn=1200)}

Provide a compact task breakdown summary with these headings only:
1) Sprint 1 Deliverables
2) Task Ownership Matrix
3) Dependencies & Blockers
4) Milestone Criteria

Rules:
- Keep total response under 220 words.
- No code.
"""
            final_response = self._ask_with_limits(
                role=Role.BA,
                prompt=synthesis_prompt,
                max_tokens=780,
                temperature=0.4,
            )
            outputs[f"step_{len(turn_plan)}_ba"] = final_response

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=len(outputs),
                outputs=outputs,
                errors=[f"implementation_breakdown failed: {str(e)}"],
                duration=duration,
            )

        duration = (datetime.now() - start_time).total_seconds()
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            steps_completed=len(outputs),
            outputs=outputs,
            duration=duration,
        )

    def _run_verification_hardening_stage(self, context: Dict[str, str]) -> WorkflowResult:
        topic = (
            context.get("requirement")
            or context.get("project_description")
            or context.get("topic")
            or context.get("prompt")
            or ""
        ).strip()
        if not topic:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=0,
                errors=["Missing stage context. Provide a feature or system to verify."],
            )

        start_time = datetime.now()
        outputs: Dict[str, AgentResponse] = {}
        turns: List[Tuple[Role, AgentResponse]] = []

        turn_plan: List[Tuple[Role, str, int]] = [
            (
                Role.QA,
                "Define a comprehensive test strategy: test pyramid, edge cases, regression approach, and risk areas.",
                750,
            ),
            (
                Role.SENIOR_DEV,
                "Identify performance benchmarks, security review points, and observability requirements.",
                700,
            ),
            (
                Role.CODER,
                "Specify unit test coverage targets and assess testability of the current implementation.",
                650,
            ),
            (
                Role.CODER_2,
                "Propose integration test patterns, contract testing strategy, and test data management.",
                650,
            ),
            (
                Role.REVIEWER,
                "Define code quality gates, release criteria, and the definition of 'shippable'.",
                700,
            ),
        ]

        try:
            for i, (role, instruction, token_budget) in enumerate(turn_plan):
                prior_discussion = self._build_turn_context(turns)
                turn_prompt = f"""You are in stage: verification_hardening.
Feature / System under review:
{topic}

Team roster and responsibilities:
- qa: test strategy, test pyramid, edge cases, regression approach.
- senior_dev: performance benchmarks, security review, observability.
- coder: unit test coverage targets, testability of implementation.
- coder_2: integration test patterns, contract testing, test data strategy.
- reviewer: code quality gates, release criteria, definition of shippable.

Prior discussion:
{prior_discussion}

Your turn objective:
{instruction}

Rules:
- Keep it under 180 words.
- Use exactly these headings: Testing Strategy, Risk Coverage, Quality Gate.
- If prior discussion exists, directly reference at least one earlier role.
- No implementation code. Verification planning only.
"""
                response = self._ask_with_limits(
                    role=role,
                    prompt=turn_prompt,
                    max_tokens=token_budget,
                    temperature=0.5,
                )
                outputs[f"step_{i}_{role.value}"] = response
                turns.append((role, response))

            synthesis_prompt = f"""You are finalizing stage: verification_hardening.
Feature / System:
{topic}

Full team discussion:
{self._build_turn_context(turns, max_chars_per_turn=1200)}

Provide a compact verification summary with these headings only:
1) Test Coverage Plan
2) Quality Gates
3) Edge Cases & Risk Areas
4) Release Readiness Criteria

Rules:
- Keep total response under 220 words.
- No code.
"""
            final_response = self._ask_with_limits(
                role=Role.QA,
                prompt=synthesis_prompt,
                max_tokens=780,
                temperature=0.4,
            )
            outputs[f"step_{len(turn_plan)}_qa"] = final_response

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=len(outputs),
                outputs=outputs,
                errors=[f"verification_hardening failed: {str(e)}"],
                duration=duration,
            )

        duration = (datetime.now() - start_time).total_seconds()
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            steps_completed=len(outputs),
            outputs=outputs,
            duration=duration,
        )

    def _run_release_handoff_stage(self, context: Dict[str, str]) -> WorkflowResult:
        topic = (
            context.get("requirement")
            or context.get("project_description")
            or context.get("topic")
            or context.get("prompt")
            or ""
        ).strip()
        if not topic:
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=0,
                errors=["Missing stage context. Provide a release scope or description."],
            )

        start_time = datetime.now()
        outputs: Dict[str, AgentResponse] = {}
        turns: List[Tuple[Role, AgentResponse]] = []

        turn_plan: List[Tuple[Role, str, int]] = [
            (
                Role.SENIOR_DEV,
                "Present the release plan: go/no-go criteria, technical checklist, rollback strategy, and monitoring approach.",
                750,
            ),
            (
                Role.REVIEWER,
                "Provide code freeze sign-off status, final review summary, and known technical debt.",
                650,
            ),
            (
                Role.QA,
                "Report final test results, outstanding defects, and regression status sign-off.",
                700,
            ),
            (
                Role.BA,
                "Confirm stakeholder acceptance, user communication plan, and business sign-off criteria.",
                650,
            ),
            (
                Role.CODER,
                "Detail the deployment runbook, environment setup steps, and post-deploy verification checklist.",
                700,
            ),
        ]

        try:
            for i, (role, instruction, token_budget) in enumerate(turn_plan):
                prior_discussion = self._build_turn_context(turns)
                turn_prompt = f"""You are in stage: release_handoff.
Release scope:
{topic}

Team roster and responsibilities:
- senior_dev: release plan, go/no-go criteria, rollback strategy, monitoring.
- reviewer: code freeze sign-off, final review status, known technical debt.
- qa: final test results sign-off, outstanding defects, regression status.
- ba: stakeholder acceptance, user communication plan, business sign-off.
- coder: deployment runbook, environment setup, post-deploy verification steps.

Prior discussion:
{prior_discussion}

Your turn objective:
{instruction}

Rules:
- Keep it under 180 words.
- Use exactly these headings: Release Position, Checklist Items, Sign-off Criteria.
- If prior discussion exists, directly reference at least one earlier role.
- No code. Release planning only.
"""
                response = self._ask_with_limits(
                    role=role,
                    prompt=turn_prompt,
                    max_tokens=token_budget,
                    temperature=0.5,
                )
                outputs[f"step_{i}_{role.value}"] = response
                turns.append((role, response))

            synthesis_prompt = f"""You are finalizing stage: release_handoff.
Release scope:
{topic}

Full team discussion:
{self._build_turn_context(turns, max_chars_per_turn=1200)}

Provide a compact release summary with these headings only:
1) Go / No-Go Decision
2) Release Checklist
3) Rollback Plan
4) Post-Release Monitoring

Rules:
- Keep total response under 220 words.
- No code.
"""
            final_response = self._ask_with_limits(
                role=Role.SENIOR_DEV,
                prompt=synthesis_prompt,
                max_tokens=800,
                temperature=0.4,
            )
            outputs[f"step_{len(turn_plan)}_senior_dev"] = final_response

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return WorkflowResult(
                status=WorkflowStatus.FAILED,
                steps_completed=len(outputs),
                outputs=outputs,
                errors=[f"release_handoff failed: {str(e)}"],
                duration=duration,
            )

        duration = (datetime.now() - start_time).total_seconds()
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            steps_completed=len(outputs),
            outputs=outputs,
            duration=duration,
        )

    def _run_placeholder_stage(self, stage_name: str) -> WorkflowResult:
        details = self._stages.get(stage_name, {})
        description = details.get("description", "Placeholder stage")
        response = AgentResponse(
            content=(
                f"Stage '{stage_name}' is currently a placeholder.\n\n"
                f"Purpose: {description}\n\n"
                "Implementation status: not active yet."
            ),
            model="stage-placeholder",
            provider="system",
            usage={"total_tokens": 0},
            finish_reason="stop",
        )
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            steps_completed=1,
            outputs={"step_0_placeholder": response},
            duration=0.0,
        )
    
    def _register_default_workflows(self) -> None:
        self.register_workflow("feature", [
            WorkflowStep(Role.BA, "Analyze this feature request and create user stories. If GitHub tools are available, create issues for each story:\n\n{requirement}"),
            WorkflowStep(Role.QA, "Create test plan and edge-case strategy. If create_test_plan_excel is available, generate an Excel test plan document.", depends_on=["step_0_ba"]),
            WorkflowStep(Role.SENIOR_DEV, "Design architecture and delivery approach.", depends_on=["step_0_ba", "step_1_qa"]),
            WorkflowStep(Role.CODER, "Implement the feature according to plan. Use write_file to create actual source files in the workspace.", depends_on=["step_0_ba", "step_1_qa", "step_2_senior_dev"]),
            WorkflowStep(Role.CODER_2, "Propose alternative implementation/refinement and integration checks. Use write_file if making changes.", depends_on=["step_3_coder"]),
        ])

        self.register_workflow("review", [
            WorkflowStep(Role.REVIEWER, "Review this code:\n\n{code}"),
            WorkflowStep(Role.SENIOR_DEV, "Suggest refactoring improvements.", depends_on=["step_0_reviewer"]),
        ])

        self.register_workflow("bugfix", [
            WorkflowStep(Role.QA, "Analyze this bug:\n\n{bug_description}\n\nCode:\n{code}"),
            WorkflowStep(Role.SENIOR_DEV, "Plan the fix approach.", depends_on=["step_0_qa"]),
            WorkflowStep(Role.CODER, "Implement the fix. Use write_file to apply changes to actual files.", depends_on=["step_0_qa", "step_1_senior_dev"]),
        ])

        self.register_workflow("architecture", [
            WorkflowStep(Role.BA, "List business requirements for:\n\n{project_description}"),
            WorkflowStep(Role.SENIOR_DEV, "Design comprehensive architecture.", depends_on=["step_0_ba"]),
            WorkflowStep(Role.QA, "Review for issues and scalability.", depends_on=["step_1_senior_dev"]),
        ])

        # ── New GitHub-integrated workflows ──────────────────────────

        self.register_workflow("project_setup", [
            WorkflowStep(
                Role.BA,
                "Analyze this project and create a GitHub repository with issues for each user story. "
                "Use create_repository to set up the repo, then create_issue for each story with labels and acceptance criteria:\n\n{requirement}",
            ),
            WorkflowStep(
                Role.SENIOR_DEV,
                "Read the issues created by the BA and design the architecture. "
                "Write architecture documentation to the workspace.",
                depends_on=["step_0_ba"],
            ),
            WorkflowStep(
                Role.CODER,
                "Implement the initial project scaffolding based on the architecture. "
                "Use write_file to create all necessary files.",
                depends_on=["step_0_ba", "step_1_senior_dev"],
            ),
        ])

        self.register_workflow("pr_review", [
            WorkflowStep(
                Role.REVIEWER,
                "Review the pull request. If GitHub PR tools are available, fetch the PR details "
                "and post your review directly. Otherwise review the provided code:\n\n{pr_info}",
            ),
        ])

        self.register_workflow("full_feature", [
            WorkflowStep(
                Role.BA,
                "Analyze requirements and create GitHub issues for each user story:\n\n{requirement}",
            ),
            WorkflowStep(
                Role.SENIOR_DEV,
                "Design architecture based on the requirements.",
                depends_on=["step_0_ba"],
            ),
            WorkflowStep(
                Role.CODER,
                "Implement the feature. Use write_file to create source files.",
                depends_on=["step_0_ba", "step_1_senior_dev"],
            ),
            WorkflowStep(
                Role.QA,
                "Write test files and create an Excel test plan. Run tests if run_tests is available.",
                depends_on=["step_2_coder"],
            ),
            WorkflowStep(
                Role.REVIEWER,
                "Review the implementation for quality, correctness, and best practices.",
                depends_on=["step_2_coder", "step_3_qa"],
            ),
        ])

        self.register_workflow("test_and_verify", [
            WorkflowStep(
                Role.QA,
                "Read the implementation files and write comprehensive tests. "
                "Use write_file to create test files and run_tests to execute them:\n\n{code_path}",
            ),
        ])

    def _register_default_stages(self) -> None:
        self.register_stage(
            "planning_discussion",
            "Cross-role planning conversation: BA -> QA -> Senior -> Coders with final alignment.",
            status="active",
        )
        self.register_stage(
            "architecture_alignment",
            "Validate architecture decisions and tradeoffs before implementation.",
            status="active",
        )
        self.register_stage(
            "implementation_breakdown",
            "Convert plan into concrete tasks, ownership, and sequencing.",
            status="active",
        )
        self.register_stage(
            "verification_hardening",
            "Consolidate testing, edge cases, and quality gates before release.",
            status="active",
        )
        self.register_stage(
            "release_handoff",
            "Prepare final release checklist, rollout plan, and rollback strategy.",
            status="active",
        )
