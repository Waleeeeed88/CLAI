"""Model team presets for configurable agent routing."""
from __future__ import annotations

from typing import Dict


ROLE_KEYS = (
    "senior_dev",
    "coder",
    "coder_2",
    "coder_3",
    "qa",
    "ba",
    "reviewer",
)


TEAM_PRESETS: Dict[str, dict] = {
    "cheap": {
        "label": "Cheap Team",
        "description": "Lowest-cost routing for drafts, triage, and routine iterations.",
        "roles": {
            "senior_dev": {"provider": "openai", "model": "gpt-5.4-mini"},
            "coder": {"provider": "openai", "model": "gpt-5.4-mini"},
            "coder_2": {"provider": "google", "model": "gemini-3.5-flash"},
            "coder_3": {"provider": "kimi", "model": "kimi-k2-thinking"},
            "qa": {"provider": "google", "model": "gemini-3.5-flash"},
            "ba": {"provider": "openai", "model": "gpt-5.4-mini"},
            "reviewer": {"provider": "google", "model": "gemini-3.5-flash"},
        },
    },
    "optimal": {
        "label": "Optimal Team",
        "description": "Balanced default for serious product work without maxing every call.",
        "roles": {
            "senior_dev": {"provider": "anthropic", "model": "claude-opus-4-8"},
            "coder": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
            "coder_2": {"provider": "google", "model": "gemini-3.1-pro-preview"},
            "coder_3": {"provider": "kimi", "model": "kimi-k2-thinking"},
            "qa": {"provider": "google", "model": "gemini-3.5-flash"},
            "ba": {"provider": "openai", "model": "gpt-5.5"},
            "reviewer": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        },
    },
    "expensive": {
        "label": "Expensive Team",
        "description": "Premium routing for architecture, high-risk changes, and final review.",
        "roles": {
            "senior_dev": {"provider": "anthropic", "model": "claude-opus-4-8"},
            "coder": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
            "coder_2": {"provider": "google", "model": "gemini-3.1-pro-preview"},
            "coder_3": {"provider": "openrouter", "model": "~qwen/qwen3-coder-latest"},
            "qa": {"provider": "openai", "model": "gpt-5.5"},
            "ba": {"provider": "openai", "model": "gpt-5.5"},
            "reviewer": {"provider": "anthropic", "model": "claude-opus-4-8"},
        },
    },
}
