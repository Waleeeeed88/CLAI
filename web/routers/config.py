"""Config router - read and update role, team, and tool assignments."""
import json

from fastapi import APIRouter, HTTPException

from agents.factory import AgentFactory, Provider, Role
from config import OVERRIDES_FILE, clear_settings_cache, get_settings
from config.settings import OVERRIDES_META_KEY, OVERRIDES_TOOLS_KEY
from config.team_profiles import TEAM_PRESETS
from ..models.schemas import (
    ModelConfigRequest,
    ModelConfigResponse,
    RoleConfig,
    TeamPreset,
    ToolConfig,
)

router = APIRouter()


def _get_current_config() -> dict[str, RoleConfig]:
    """Build the current role -> provider + model mapping."""
    result: dict[str, RoleConfig] = {}
    for role in Role:
        provider, model = AgentFactory.get_role_runtime_config(role)
        result[role.value] = RoleConfig(provider=provider.value, model=model)
    return result


def _load_override_file() -> dict:
    if not OVERRIDES_FILE.exists():
        return {}
    try:
        data = json.loads(OVERRIDES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_override_file(data: dict) -> None:
    try:
        OVERRIDES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save config: {exc}") from exc


def _team_presets() -> list[TeamPreset]:
    return [
        TeamPreset(
            id=preset_id,
            label=str(preset["label"]),
            description=str(preset["description"]),
            roles={
                role: RoleConfig(provider=cfg["provider"], model=cfg["model"])
                for role, cfg in preset["roles"].items()
            },
        )
        for preset_id, preset in TEAM_PRESETS.items()
    ]


def _tool_config_from_settings() -> ToolConfig:
    settings = get_settings()
    return ToolConfig(
        filesystem=settings.mcp_enabled,
        scratchpad=settings.scratchpad_enabled,
        enterprise_data=settings.enterprise_data_enabled,
        qa_tools=settings.qa_tools_enabled,
        github_mcp=settings.github_mcp_enabled,
    )


def _tool_config_to_overrides(tools: ToolConfig) -> dict[str, bool]:
    return {
        "mcp_enabled": tools.filesystem,
        "scratchpad_enabled": tools.scratchpad,
        "enterprise_data_enabled": tools.enterprise_data,
        "qa_tools_enabled": tools.qa_tools,
        "github_mcp_enabled": tools.github_mcp,
    }


def _active_preset_for(roles: dict[str, RoleConfig]) -> str | None:
    for preset_id, preset in TEAM_PRESETS.items():
        preset_roles = preset["roles"]
        if all(
            role in roles
            and roles[role].provider == cfg["provider"]
            and roles[role].model == cfg["model"]
            for role, cfg in preset_roles.items()
        ):
            return preset_id
    return None


def _validate_role_config(role_key: str, cfg: RoleConfig) -> None:
    valid_roles = {role.value for role in Role}
    valid_providers = {provider.value for provider in Provider}
    if role_key not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Unknown role: {role_key}")
    if cfg.provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Invalid provider for {role_key}: {cfg.provider}")
    if not cfg.model.strip():
        raise HTTPException(status_code=400, detail=f"Model is required for {role_key}")


def _onboarding_warnings(roles: dict[str, RoleConfig], tools: ToolConfig) -> list[str]:
    settings = get_settings()
    key_status = {
        "anthropic": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "google": settings.google_api_key,
        "kimi": settings.kimi_api_key,
        "openrouter": settings.openrouter_api_key,
    }
    warnings: list[str] = []
    for provider in sorted({cfg.provider for cfg in roles.values()}):
        key = key_status.get(provider)
        if key is None or not key.get_secret_value():
            warnings.append(f"{provider} is selected but its API key is not configured.")
    if tools.github_mcp and not settings.github_token:
        warnings.append("GitHub MCP is enabled but GITHUB_TOKEN is not configured.")
    if not tools.filesystem:
        warnings.append("Filesystem tools are disabled; agents cannot read or write workspace files.")
    if not tools.enterprise_data:
        warnings.append("Enterprise data tools are disabled; retrieval, memory, audit, and cost tools are unavailable.")
    return warnings


def _response() -> ModelConfigResponse:
    roles = _get_current_config()
    tools = _tool_config_from_settings()
    return ModelConfigResponse(
        roles=roles,
        providers=[p.value for p in Provider],
        presets=_team_presets(),
        active_preset=_active_preset_for(roles),
        tools=tools,
        warnings=_onboarding_warnings(roles, tools),
    )


@router.get("/config/models", response_model=ModelConfigResponse)
async def get_model_config():
    return _response()


@router.post("/config/models", response_model=ModelConfigResponse)
async def update_model_config(req: ModelConfigRequest):
    existing = _load_override_file()

    if req.team_preset:
        preset = TEAM_PRESETS.get(req.team_preset)
        if not preset:
            raise HTTPException(status_code=400, detail=f"Unknown team preset: {req.team_preset}")
        for role_key, cfg in preset["roles"].items():
            existing[role_key] = {"provider": cfg["provider"], "model": cfg["model"]}
        existing[OVERRIDES_META_KEY] = {"team_preset": req.team_preset}

    for role_key, cfg in req.overrides.items():
        role_key = role_key.lower()
        _validate_role_config(role_key, cfg)
        existing[role_key] = {"provider": cfg.provider, "model": cfg.model}
        existing[OVERRIDES_META_KEY] = {"team_preset": None}

    if req.tools is not None:
        existing[OVERRIDES_TOOLS_KEY] = _tool_config_to_overrides(req.tools)

    _write_override_file(existing)
    clear_settings_cache()
    return _response()
