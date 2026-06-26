import asyncio
import json

from agents.factory import Provider, Role
from config import clear_settings_cache
from config.settings import OVERRIDES_TOOLS_KEY
from config.team_profiles import TEAM_PRESETS
from core import Orchestrator
from web.models.schemas import ModelConfigRequest, ToolConfig
from web.routers import config as config_router


def _use_tmp_overrides(monkeypatch, tmp_path):
    path = tmp_path / "overrides.json"
    monkeypatch.setattr("config.settings.OVERRIDES_FILE", path)
    monkeypatch.setattr(config_router, "OVERRIDES_FILE", path)
    clear_settings_cache()
    return path


def test_team_preset_and_tool_config_persist(monkeypatch, tmp_path):
    overrides_path = _use_tmp_overrides(monkeypatch, tmp_path)

    response = asyncio.run(
        config_router.update_model_config(
            ModelConfigRequest(
                team_preset="cheap",
                tools=ToolConfig(
                    filesystem=True,
                    scratchpad=False,
                    enterprise_data=False,
                    qa_tools=False,
                    github_mcp=False,
                ),
            )
        )
    )

    assert response.active_preset == "cheap"
    assert response.roles["qa"].provider == "google"
    assert response.tools.scratchpad is False
    stored = json.loads(overrides_path.read_text(encoding="utf-8"))
    assert stored["__meta__"]["team_preset"] == "cheap"
    assert stored[OVERRIDES_TOOLS_KEY]["enterprise_data_enabled"] is False


def test_orchestrator_respects_tool_toggles(monkeypatch, tmp_path):
    overrides_path = _use_tmp_overrides(monkeypatch, tmp_path)
    overrides_path.write_text(
        json.dumps(
            {
                OVERRIDES_TOOLS_KEY: {
                    "mcp_enabled": False,
                    "scratchpad_enabled": False,
                    "enterprise_data_enabled": False,
                    "qa_tools_enabled": False,
                    "github_mcp_enabled": False,
                }
            }
        ),
        encoding="utf-8",
    )
    clear_settings_cache()

    registry = Orchestrator()._build_tool_registry(Role.QA)
    tool_names = set(registry.list_tools()) if registry else set()

    assert "read_file" not in tool_names
    assert "scratchpad_write" not in tool_names
    assert "semantic_search" not in tool_names
    assert "run_tests" not in tool_names


def test_string_tool_overrides_are_coerced(monkeypatch, tmp_path):
    overrides_path = _use_tmp_overrides(monkeypatch, tmp_path)
    overrides_path.write_text(
        json.dumps({OVERRIDES_TOOLS_KEY: {"enterprise_data_enabled": "false"}}),
        encoding="utf-8",
    )
    clear_settings_cache()

    response = asyncio.run(config_router.get_model_config())

    assert response.tools.enterprise_data is False


def test_team_presets_cover_every_role_and_use_valid_providers():
    role_keys = {role.value for role in Role}
    provider_keys = {provider.value for provider in Provider}

    assert set(TEAM_PRESETS) == {"cheap", "optimal", "expensive"}
    for preset in TEAM_PRESETS.values():
        assert set(preset["roles"]) == role_keys
        for role_config in preset["roles"].values():
            assert role_config["provider"] in provider_keys
            assert role_config["model"].strip()
