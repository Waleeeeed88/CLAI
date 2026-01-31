"""Orchestrator - coordinates multi-agent workflows."""
from typing import Dict, List, Optional
from datetime import datetime

from agents import AgentFactory, AgentResponse, BaseAgent
from agents.factory import Role
from config import get_settings
from .workflows import WorkflowStatus, WorkflowStep, WorkflowResult
from .filesystem import FileSystemTools, get_filesystem


class Orchestrator:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._agents: Dict[Role, BaseAgent] = {}
        self._workflows: Dict[str, List[WorkflowStep]] = {}
        
        settings = get_settings()
        self._mcp_enabled = settings.mcp_enabled
        self._fs: Optional[FileSystemTools] = None
        if self._mcp_enabled:
            self._fs = get_filesystem()
        
        self._register_default_workflows()
    
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
    
    def _get_agent(self, role: Role) -> BaseAgent:
        if role not in self._agents:
            self._agents[role] = AgentFactory.create_by_role(role)
        return self._agents[role]
    
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
            roles = list(Role)
        results = {}
        for role in roles:
            if self.verbose:
                print(f"Consulting {role.value}...")
            results[role] = self.ask(role, prompt)
        return results
    
    def register_workflow(self, name: str, steps: List[WorkflowStep]) -> None:
        self._workflows[name] = steps
    
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
    
    def clear_context(self, role: Optional[Role] = None) -> None:
        if role:
            if role in self._agents:
                self._agents[role].clear_history()
        else:
            for agent in self._agents.values():
                agent.clear_history()
    
    def list_workflows(self) -> List[str]:
        return list(self._workflows.keys())
    
    def _register_default_workflows(self) -> None:
        self.register_workflow("feature", [
            WorkflowStep(Role.BA, "Analyze this feature request and create user stories:\n\n{requirement}"),
            WorkflowStep(Role.SENIOR_DEV, "Design the architecture for implementation.", depends_on=["step_0_ba"]),
            WorkflowStep(Role.CODER, "Implement the feature.", depends_on=["step_0_ba", "step_1_senior_dev"]),
            WorkflowStep(Role.QA, "Review for bugs and edge cases.", depends_on=["step_2_coder"]),
        ])
        
        self.register_workflow("review", [
            WorkflowStep(Role.REVIEWER, "Review this code:\n\n{code}"),
            WorkflowStep(Role.SENIOR_DEV, "Suggest refactoring improvements.", depends_on=["step_0_reviewer"]),
        ])
        
        self.register_workflow("bugfix", [
            WorkflowStep(Role.QA, "Analyze this bug:\n\n{bug_description}\n\nCode:\n{code}"),
            WorkflowStep(Role.SENIOR_DEV, "Plan the fix approach.", depends_on=["step_0_qa"]),
            WorkflowStep(Role.CODER, "Implement the fix.", depends_on=["step_0_qa", "step_1_senior_dev"]),
        ])
        
        self.register_workflow("architecture", [
            WorkflowStep(Role.BA, "List business requirements for:\n\n{project_description}"),
            WorkflowStep(Role.SENIOR_DEV, "Design comprehensive architecture.", depends_on=["step_0_ba"]),
            WorkflowStep(Role.QA, "Review for issues and scalability.", depends_on=["step_1_senior_dev"]),
        ])
