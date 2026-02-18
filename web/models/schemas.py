"""Pydantic request/response models for the CLAI web API."""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ChatRequest(BaseModel):
    """Web request model (pipeline-only in current API behavior)."""
    type: str  # "pipeline"
    stage: Optional[str] = None
    workflow: Optional[str] = None
    context: Dict[str, str] = Field(default_factory=dict)
    requirement: Optional[str] = None
    project_name: Optional[str] = None
    workspace_dir: Optional[str] = None
    selected_files: List[str] = Field(default_factory=list)
    use_github: bool = False
    selected_phases: Optional[List[str]] = None


class SessionResponse(BaseModel):
    session_id: str


class WorkflowListResponse(BaseModel):
    workflows: List[str]
    stages: List[str]
    stage_details: Dict[str, Dict[str, str]]
