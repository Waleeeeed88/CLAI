"""Agent factory - creates agents by provider or role."""
from typing import Dict, Type, Optional
from enum import Enum

from .base import BaseAgent
from .claude_agent import ClaudeAgent
from .gpt_agent import GPTAgent
from .gemini_agent import GeminiAgent
from config import get_settings


class Provider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class Role(Enum):
    SENIOR_DEV = "senior_dev"
    CODER = "coder"
    CODER_2 = "coder_2"
    QA = "qa"
    BA = "ba"
    REVIEWER = "reviewer"


PROVIDER_AGENTS: Dict[Provider, Type[BaseAgent]] = {
    Provider.ANTHROPIC: ClaudeAgent,
    Provider.OPENAI: GPTAgent,
    Provider.GOOGLE: GeminiAgent,
}

ROLE_PROVIDERS: Dict[Role, Provider] = {
    Role.SENIOR_DEV: Provider.ANTHROPIC,
    Role.CODER: Provider.ANTHROPIC,
    Role.CODER_2: Provider.GOOGLE,
    Role.QA: Provider.GOOGLE,
    Role.BA: Provider.OPENAI,
    Role.REVIEWER: Provider.ANTHROPIC,
}


class AgentFactory:
    @staticmethod
    def create_by_provider(
        provider: Provider,
        model: str,
        system_prompt: str = "",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> BaseAgent:
        settings = get_settings()
        agent_class = PROVIDER_AGENTS.get(provider)
        if not agent_class:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return agent_class(
            model=model,
            system_prompt=system_prompt,
            max_tokens=max_tokens or settings.default_max_tokens,
            temperature=temperature if temperature is not None else settings.default_temperature,
        )
    
    @staticmethod
    def create_by_role(
        role: Role,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> BaseAgent:
        from roles import get_role_config
        
        settings = get_settings()
        role_config = get_role_config(role)
        provider = ROLE_PROVIDERS.get(role)
        if not provider:
            raise ValueError(f"Unsupported role: {role}")
        
        model_map = {
            Role.SENIOR_DEV: settings.senior_dev_model,
            Role.CODER: settings.coder_model,
            Role.CODER_2: settings.coder_model_2,
            Role.QA: settings.qa_model,
            Role.BA: settings.ba_model,
            Role.REVIEWER: settings.reviewer_model,
        }
        
        model = model_map.get(role)
        if not model:
            raise ValueError(f"No model for role: {role}")
        
        return AgentFactory.create_by_provider(
            provider=provider,
            model=model,
            system_prompt=system_prompt or role_config.system_prompt,
            max_tokens=max_tokens or role_config.max_tokens,
            temperature=temperature if temperature is not None else role_config.temperature,
        )
