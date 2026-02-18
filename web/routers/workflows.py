"""GET /api/workflows - simplified metadata for the web UI."""

from fastapi import APIRouter

from core.pipeline import ProjectPipeline
from ..models.schemas import WorkflowListResponse

router = APIRouter()


@router.get("/workflows", response_model=WorkflowListResponse)
def list_workflows():
    phase_names = list(ProjectPipeline.ALL_PHASES)
    details = {
        name: {
            "description": ProjectPipeline.PHASE_DESCRIPTIONS.get(name, ""),
            "status": "active",
        }
        for name in phase_names
    }
    return WorkflowListResponse(
        workflows=["simple_pipeline"],
        stages=phase_names,
        stage_details=details,
    )
