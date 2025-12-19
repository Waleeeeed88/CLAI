"""
CLAI Configuration Settings

Uses Pydantic Settings for environment variable management with validation.
Supports .env files and system environment variables.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    API keys are stored as SecretStr to prevent accidental logging.
    Model configurations allow runtime customization.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # =========================
    # API Keys (Required)
    # =========================
    anthropic_api_key: SecretStr = Field(
        ...,
        description="Anthropic API key for Claude models"
    )
    openai_api_key: SecretStr = Field(
        ...,
        description="OpenAI API key for GPT models"
    )
    google_api_key: SecretStr = Field(
        ...,
        description="Google API key for Gemini models"
    )
    
    # =========================
    # Model Configurations (BOOSTED)
    # =========================
    # Senior Dev - Claude Opus 4 (Best reasoning, architecture, complex problems)
    senior_dev_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model for Senior Developer role"
    )
    
    # Coder - Claude Sonnet 4.5 (Fast, excellent code generation)
    coder_model: str = Field(
        default="claude-sonnet-4-5-20250514",
        description="Primary model for Coder role (Claude)"
    )
    
    # Coder 2 - Gemini (Secondary/fallback for large context)
    coder_model_2: str = Field(
        default="gemini-2.0-flash",
        description="Secondary model for Coder role (Gemini)"
    )
    
    # QA - GPT-4o (Thorough testing, edge case detection)
    qa_model: str = Field(
        default="gpt-4o",
        description="Model for QA role"
    )
    
    # BA - Gemini 1.5 Pro (Best analysis, massive context window)
    ba_model: str = Field(
        default="gemini-1.5-pro",
        description="Model for Business Analyst role"
    )
    
    # Code Reviewer - Claude Opus 4 (Thorough reviews need the best)
    reviewer_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model for Code Reviewer role"
    )
    
    # =========================
    # General Settings (BOOSTED)
    # =========================
    default_max_tokens: int = Field(
        default=8192,
        description="Default max tokens for responses"
    )
    
    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for responses"
    )
    
    verbose: bool = Field(
        default=True,
        description="Enable verbose output"
    )
    
    log_level: str = Field(
        default="DEBUG",
        description="Logging level"
    )
    
    # =========================
    # MCP Filesystem Settings
    # =========================
    mcp_enabled: bool = Field(
        default=True,
        description="Enable MCP filesystem tools"
    )
    
    mcp_workspace_root: str = Field(
        default="./workspace",
        description="Root directory for MCP file operations"
    )
    
    @property
    def workspace_path(self) -> Path:
        """Get the absolute workspace path, creating it if needed."""
        path = Path(self.mcp_workspace_root).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are loaded once and reused.
    """
    return Settings()
