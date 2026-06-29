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


class RoleConfig(BaseModel):
    provider: str
    model: str


class TeamPreset(BaseModel):
    id: str
    label: str
    description: str
    roles: Dict[str, RoleConfig]


class ToolConfig(BaseModel):
    filesystem: bool = True
    scratchpad: bool = True
    enterprise_data: bool = True
    qa_tools: bool = True
    github_mcp: bool = False


class CostSavingConfig(BaseModel):
    enabled: bool = False
    max_output_tokens: int = 1600
    history_messages: int = 8
    history_char_limit: int = 2000


class ModelConfigResponse(BaseModel):
    roles: Dict[str, RoleConfig]
    providers: List[str]
    presets: List[TeamPreset] = Field(default_factory=list)
    active_preset: Optional[str] = None
    tools: ToolConfig = Field(default_factory=ToolConfig)
    cost_saving: CostSavingConfig = Field(default_factory=CostSavingConfig)
    warnings: List[str] = Field(default_factory=list)


class ModelConfigRequest(BaseModel):
    overrides: Dict[str, RoleConfig] = Field(default_factory=dict)
    team_preset: Optional[str] = None
    tools: Optional[ToolConfig] = None
    cost_saving: Optional[CostSavingConfig] = None
