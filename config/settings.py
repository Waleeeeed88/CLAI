"""CLAI Configuration - API keys and model settings."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    anthropic_api_key: SecretStr = Field(...)
    openai_api_key: SecretStr = Field(...)
    google_api_key: SecretStr = Field(...)

    # Kimi (Moonshot AI) — optional, only needed if you route a role to Kimi
    kimi_api_key: Optional[SecretStr] = Field(default=None)

    # GitHub MCP integration
    github_token: Optional[SecretStr] = Field(default=None)
    github_mcp_enabled: bool = Field(default=False)
    github_mcp_command: str = Field(default="npx")
    github_mcp_args: str = Field(default="-y @modelcontextprotocol/server-github")

    senior_dev_model: str = "claude-opus-4-5-20251101"
    coder_model: str = "claude-sonnet-4-5-20250929"
    coder_model_2: str = "gemini-3.1-pro-preview"
    coder_model_3: str = "kimi-k2-thinking"
    qa_model: str = "gemini-3-flash-preview"
    ba_model: str = "gpt-5.2-2025-12-11"
    reviewer_model: str = "claude-sonnet-4-5-20250929"

    # Optional JSON overrides for arbitrary role routing/model choices.
    # Example:
    # ROLE_MODEL_OVERRIDES='{"qa":"gpt-5.2-2025-12-11","coder":"gpt-5.2-2025-12-11"}'
    # ROLE_PROVIDER_OVERRIDES='{"qa":"openai","ba":"google"}'
    role_model_overrides: Dict[str, str] = Field(default_factory=dict)
    role_provider_overrides: Dict[str, str] = Field(default_factory=dict)
    
    default_max_tokens: int = 8192
    default_temperature: float = 0.7
    verbose: bool = True
    log_level: str = "DEBUG"

    # Input-shaping and retry safeguards for Anthropic requests.
    anthropic_retry_attempts: int = 3
    anthropic_retry_base_delay_seconds: float = 8.0
    anthropic_message_char_limit: int = 8000
    anthropic_tool_result_char_limit: int = 2500
    anthropic_total_input_char_budget: int = 24000
    anthropic_total_input_char_budget_retry: int = 12000
    
    mcp_enabled: bool = True
    mcp_workspace_root: str = "./workspace"

    @field_validator("role_model_overrides", "role_provider_overrides", mode="before")
    @classmethod
    def _coerce_override_map(cls, value):
        if value is None:
            return {}
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return {}
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON overrides: {exc}") from exc
            if not isinstance(parsed, dict):
                raise ValueError("Override values must be a JSON object")
            value = parsed

        if not isinstance(value, dict):
            raise ValueError("Override values must be a mapping")

        normalized: Dict[str, str] = {}
        for key, mapped_value in value.items():
            role_key = str(key).strip().lower()
            if not role_key:
                continue
            model_or_provider = str(mapped_value).strip()
            if model_or_provider:
                normalized[role_key] = model_or_provider
        return normalized

    def resolve_role_model(self, role_key: str, default: str) -> str:
        return self.role_model_overrides.get(role_key.lower(), default)

    def resolve_role_provider(self, role_key: str, default: str) -> str:
        return self.role_provider_overrides.get(role_key.lower(), default)
    
    @property
    def workspace_path(self) -> Path:
        path = Path(self.mcp_workspace_root).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def github_mcp_args_list(self) -> List[str]:
        """Parse space-separated MCP args string into a list."""
        return self.github_mcp_args.split() if self.github_mcp_args else []


OVERRIDES_FILE = Path(__file__).parent / "overrides.json"


def _load_overrides() -> Dict[str, Dict[str, str]]:
    """Load role overrides from the local JSON file (if it exists)."""
    if not OVERRIDES_FILE.exists():
        return {}
    try:
        data = json.loads(OVERRIDES_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # Merge file-based overrides on top of env-based overrides
    file_overrides = _load_overrides()
    for role_key, cfg in file_overrides.items():
        if not isinstance(cfg, dict):
            continue
        role_key = role_key.lower()
        if "model" in cfg and cfg["model"]:
            settings.role_model_overrides[role_key] = cfg["model"]
        if "provider" in cfg and cfg["provider"]:
            settings.role_provider_overrides[role_key] = cfg["provider"]
    return settings


def clear_settings_cache() -> None:
    """Clear the cached settings so the next call reloads from .env + overrides.json."""
    get_settings.cache_clear()
