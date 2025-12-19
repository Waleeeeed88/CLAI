"""
Orchestrator Module

Coordinates multi-agent workflows and manages task routing.
Implements the Mediator pattern for agent communication.

MCP Integration: Provides filesystem tools to all agents for
reading/writing code files and managing project repositories.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from datetime import datetime

from agents import AgentFactory, AgentResponse, BaseAgent
from agents.factory import Role
from mcp_filesystem import get_filesystem, FileSystemTools
from config import get_settings


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.
    
    Attributes:
        role: The role to execute this step
        instruction: What to tell the agent
        depends_on: Previous step outputs to include
        transform: Optional function to transform input
    """
    role: Role
    instruction: str
    depends_on: List[str] = field(default_factory=list)
    transform: Optional[Callable[[Dict[str, str]], str]] = None


@dataclass
class WorkflowResult:
    """
    Result of a workflow execution.
    
    Attributes:
        status: Workflow completion status
        steps_completed: Number of steps completed
        outputs: Dict of step_name -> response
        errors: Any errors encountered
        duration: Total execution time
    """
    status: WorkflowStatus
    steps_completed: int
    outputs: Dict[str, AgentResponse] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    
    @property
    def final_output(self) -> Optional[str]:
        """Get the last step's output."""
        if self.outputs:
            last_key = list(self.outputs.keys())[-1]
            return self.outputs[last_key].content
        return None


class Orchestrator:
    """
    Orchestrates multi-agent workflows.
    
    Implements the Mediator pattern to coordinate between different
    AI agents without them knowing about each other.
    
    MCP Integration:
        - Provides filesystem tools to agents for file operations
        - Agents can read/write code files in the workspace
        - Project structure is maintained in MCP_WORKSPACE_ROOT
    
    Example:
        orchestrator = Orchestrator()
        
        # Single agent query
        response = orchestrator.ask(Role.SENIOR_DEV, "Design a REST API")
        
        # Multi-agent workflow
        result = orchestrator.run_workflow("feature_development", {
            "requirement": "User authentication system"
        })
        
        # File operations via MCP
        orchestrator.write_file("project/main.py", code_content)
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the orchestrator.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self._agents: Dict[Role, BaseAgent] = {}
        self._workflows: Dict[str, List[WorkflowStep]] = {}
        
        # Initialize MCP filesystem tools if enabled
        settings = get_settings()
        self._mcp_enabled = settings.mcp_enabled
        self._fs: Optional[FileSystemTools] = None
        if self._mcp_enabled:
            self._fs = get_filesystem()
        
        # Register built-in workflows
        self._register_default_workflows()
    
    @property
    def filesystem(self) -> Optional[FileSystemTools]:
        """Get the MCP filesystem tools instance."""
        return self._fs
    
    def write_file(self, path: str, content: str) -> bool:
        """
        Write content to a file via MCP.
        
        Args:
            path: Relative path within workspace
            content: File content to write
            
        Returns:
            True if successful, False otherwise
        """
        if not self._fs:
            return False
        result = self._fs.write_file(path, content)
        return result.success
    
    def read_file(self, path: str) -> Optional[str]:
        """
        Read file content via MCP.
        
        Args:
            path: Relative path within workspace
            
        Returns:
            File content or None if failed
        """
        if not self._fs:
            return None
        result = self._fs.read_file(path)
        return result.data if result.success else None
    
    def _get_agent(self, role: Role) -> BaseAgent:
        """
        Get or create an agent for a role.
        
        Uses lazy initialization to only create agents when needed.
        """
        if role not in self._agents:
            self._agents[role] = AgentFactory.create_by_role(role)
        return self._agents[role]
    
    def ask(
        self,
        role: Role,
        prompt: str,
        include_history: bool = False,
    ) -> AgentResponse:
        """
        Ask a single agent a question.
        
        Args:
            role: Which team role to ask
            prompt: The question or task
            include_history: Include conversation history
            
        Returns:
            AgentResponse from the agent
        """
        agent = self._get_agent(role)
        
        if self.verbose:
            print(f"[{role.value}] Processing request...")
        
        response = agent.chat(prompt, include_history=include_history)
        
        if self.verbose:
            print(f"[{role.value}] Completed ({response.total_tokens} tokens)")
        
        return response
    
    def consult_team(
        self,
        prompt: str,
        roles: Optional[List[Role]] = None,
    ) -> Dict[Role, AgentResponse]:
        """
        Ask multiple agents the same question.
        
        Useful for getting different perspectives on a problem.
        
        Args:
            prompt: The question or task
            roles: Which roles to consult (default: all)
            
        Returns:
            Dict mapping each role to their response
        """
        if roles is None:
            roles = list(Role)
        
        results = {}
        for role in roles:
            if self.verbose:
                print(f"Consulting {role.value}...")
            results[role] = self.ask(role, prompt)
        
        return results
    
    def register_workflow(
        self,
        name: str,
        steps: List[WorkflowStep],
    ) -> None:
        """
        Register a custom workflow.
        
        Args:
            name: Unique workflow identifier
            steps: List of workflow steps
        """
        self._workflows[name] = steps
    
    def run_workflow(
        self,
        workflow_name: str,
        context: Dict[str, str],
    ) -> WorkflowResult:
        """
        Execute a registered workflow.
        
        Args:
            workflow_name: Name of the workflow to run
            context: Initial context variables
            
        Returns:
            WorkflowResult with all outputs
        """
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
            print(f"Starting workflow: {workflow_name}")
            print(f"Steps: {len(steps)}")
        
        for i, step in enumerate(steps):
            step_name = f"step_{i}_{step.role.value}"
            
            try:
                # Build prompt with dependencies
                prompt = step.instruction
                
                # Replace context variables
                for key, value in context.items():
                    prompt = prompt.replace(f"{{{key}}}", value)
                
                # Add outputs from dependent steps
                if step.depends_on:
                    dep_context = "\n\n---\nPrevious outputs:\n"
                    for dep in step.depends_on:
                        if dep in outputs:
                            dep_context += f"\n[{dep}]:\n{outputs[dep].content}\n"
                    prompt += dep_context
                
                # Apply transform if provided
                if step.transform:
                    prompt = step.transform({"prompt": prompt, **context})
                
                if self.verbose:
                    print(f"  Step {i+1}/{len(steps)}: {step.role.value}")
                
                # Execute step
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
            print(f"Workflow completed in {duration:.2f}s")
        
        return WorkflowResult(
            status=WorkflowStatus.COMPLETED,
            steps_completed=len(steps),
            outputs=outputs,
            duration=duration,
        )
    
    def clear_context(self, role: Optional[Role] = None) -> None:
        """
        Clear conversation history for agents.
        
        Args:
            role: Specific role to clear, or None for all
        """
        if role:
            if role in self._agents:
                self._agents[role].clear_history()
        else:
            for agent in self._agents.values():
                agent.clear_history()
    
    def list_workflows(self) -> List[str]:
        """Get list of registered workflow names."""
        return list(self._workflows.keys())
    
    def _register_default_workflows(self) -> None:
        """Register built-in workflows."""
        
        # Feature Development Workflow
        # BA -> Senior Dev -> Coder -> QA
        self.register_workflow("feature", [
            WorkflowStep(
                role=Role.BA,
                instruction="Analyze this feature request and create user stories with acceptance criteria:\n\n{requirement}",
            ),
            WorkflowStep(
                role=Role.SENIOR_DEV,
                instruction="Based on the requirements below, design the architecture and create a technical plan for implementation.",
                depends_on=["step_0_ba"],
            ),
            WorkflowStep(
                role=Role.CODER,
                instruction="Implement the feature based on the architecture and requirements provided.",
                depends_on=["step_0_ba", "step_1_senior_dev"],
            ),
            WorkflowStep(
                role=Role.QA,
                instruction="Review the implementation for bugs, edge cases, and suggest test cases.",
                depends_on=["step_2_coder"],
            ),
        ])
        
        # Code Review Workflow
        # Reviewer -> Senior Dev (if issues found)
        self.register_workflow("review", [
            WorkflowStep(
                role=Role.REVIEWER,
                instruction="Review this code for issues, bugs, and improvements:\n\n{code}",
            ),
            WorkflowStep(
                role=Role.SENIOR_DEV,
                instruction="Based on the review feedback, suggest how to refactor and improve this code.",
                depends_on=["step_0_reviewer"],
            ),
        ])
        
        # Bug Fix Workflow
        # QA (analyze) -> Senior Dev (plan) -> Coder (fix)
        self.register_workflow("bugfix", [
            WorkflowStep(
                role=Role.QA,
                instruction="Analyze this bug report and identify the root cause:\n\n{bug_description}\n\nCode:\n{code}",
            ),
            WorkflowStep(
                role=Role.SENIOR_DEV,
                instruction="Based on the QA analysis, plan the fix approach.",
                depends_on=["step_0_qa"],
            ),
            WorkflowStep(
                role=Role.CODER,
                instruction="Implement the bug fix based on the analysis and plan.",
                depends_on=["step_0_qa", "step_1_senior_dev"],
            ),
        ])
        
        # Architecture Review Workflow
        self.register_workflow("architecture", [
            WorkflowStep(
                role=Role.BA,
                instruction="List the business requirements and constraints for:\n\n{project_description}",
            ),
            WorkflowStep(
                role=Role.SENIOR_DEV,
                instruction="Design a comprehensive architecture considering the business requirements.",
                depends_on=["step_0_ba"],
            ),
            WorkflowStep(
                role=Role.QA,
                instruction="Review the architecture for potential issues, scalability concerns, and security gaps.",
                depends_on=["step_1_senior_dev"],
            ),
        ])
