"""CLAI Configuration - API keys and model settings."""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


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
    
    senior_dev_model: str = "claude-opus-4-5-20251101"
    coder_model: str = "claude-sonnet-4-5-20250929"
    coder_model_2: str = "gemini-3-pro-preview"
    qa_model: str = "gemini-3-flash-preview"
    ba_model: str = "gpt-5.2-2025-12-11"
    reviewer_model: str = "claude-sonnet-4-5-20250929"
    
    default_max_tokens: int = 8192
    default_temperature: float = 0.7
    verbose: bool = True
    log_level: str = "DEBUG"
    
    mcp_enabled: bool = True
    mcp_workspace_root: str = "./workspace"
    
    @property
    def workspace_path(self) -> Path:
        path = Path(self.mcp_workspace_root).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
