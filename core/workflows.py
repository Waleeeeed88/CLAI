"""Workflow data models."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from agents import AgentResponse
from agents.factory import Role


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowStep:
    role: Role
    instruction: str
    depends_on: List[str] = field(default_factory=list)
    transform: Optional[Callable[[Dict[str, str]], str]] = None


@dataclass
class WorkflowResult:
    status: WorkflowStatus
    steps_completed: int
    outputs: Dict[str, AgentResponse] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0
    
    @property
    def final_output(self) -> Optional[str]:
        if self.outputs:
            last_key = list(self.outputs.keys())[-1]
            return self.outputs[last_key].content
        return None
