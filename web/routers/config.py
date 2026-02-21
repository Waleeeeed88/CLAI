"""Config router — read and update role-model assignments."""
import json
from fastapi import APIRouter

from agents.factory import AgentFactory, Provider, Role
from config import get_settings, clear_settings_cache, OVERRIDES_FILE
from ..models.schemas import ModelConfigResponse, ModelConfigRequest, RoleConfig

router = APIRouter()


def _get_current_config() -> dict[str, RoleConfig]:
    """Build the current role → provider + model mapping."""
    result: dict[str, RoleConfig] = {}
    for role in Role:
        provider, model = AgentFactory.get_role_runtime_config(role)
        result[role.value] = RoleConfig(provider=provider.value, model=model)
    return result


@router.get("/config/models", response_model=ModelConfigResponse)
async def get_model_config():
    return ModelConfigResponse(
        roles=_get_current_config(),
        providers=[p.value for p in Provider],
    )


@router.post("/config/models", response_model=ModelConfigResponse)
async def update_model_config(req: ModelConfigRequest):
    # Load existing overrides file (if any)
    existing: dict = {}
    if OVERRIDES_FILE.exists():
        try:
            existing = json.loads(OVERRIDES_FILE.read_text(encoding="utf-8"))
        except Exception:
            existing = {}

    # Merge new overrides
    for role_key, cfg in req.overrides.items():
        role_key = role_key.lower()
        existing[role_key] = {"provider": cfg.provider, "model": cfg.model}

    # Write to file
    OVERRIDES_FILE.write_text(
        json.dumps(existing, indent=2),
        encoding="utf-8",
    )

    # Clear the settings cache so next pipeline run picks up changes
    clear_settings_cache()

    return ModelConfigResponse(
        roles=_get_current_config(),
        providers=[p.value for p in Provider],
    )
