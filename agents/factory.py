"""
Agent Factory

Factory pattern implementation for creating agents.
Supports creating agents by provider or by role.
"""
from typing import Dict, Type, Optional
from enum import Enum

from .base import BaseAgent
from .claude_agent import ClaudeAgent
from .gpt_agent import GPTAgent
from .gemini_agent import GeminiAgent
from config import get_settings


class Provider(Enum):
    """Supported AI providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class Role(Enum):
    """Team roles with their default configurations."""
    SENIOR_DEV = "senior_dev"
    CODER = "coder"
    CODER_2 = "coder_2"  # Secondary coder using Gemini
    QA = "qa"
    BA = "ba"
    REVIEWER = "reviewer"


# Mapping of providers to agent classes
PROVIDER_AGENTS: Dict[Provider, Type[BaseAgent]] = {
    Provider.ANTHROPIC: ClaudeAgent,
    Provider.OPENAI: GPTAgent,
    Provider.GOOGLE: GeminiAgent,
}

# Mapping of roles to providers
ROLE_PROVIDERS: Dict[Role, Provider] = {
    Role.SENIOR_DEV: Provider.ANTHROPIC,
    Role.CODER: Provider.ANTHROPIC,  # Using Claude Sonnet 4.5 for coding
    Role.CODER_2: Provider.GOOGLE,   # Secondary coder using Gemini
    Role.QA: Provider.OPENAI,
    Role.BA: Provider.GOOGLE,
    Role.REVIEWER: Provider.ANTHROPIC,
}


class AgentFactory:
    """
    Factory for creating AI agents.
    
    Supports two creation patterns:
    1. By provider: Create a specific provider's agent with custom config
    2. By role: Create a pre-configured agent for a team role
    
    Example:
        # Create by provider
        agent = AgentFactory.create_by_provider(
            Provider.ANTHROPIC,
            model="claude-sonnet-4-20250514"
        )
        
        # Create by role
        senior_dev = AgentFactory.create_by_role(Role.SENIOR_DEV)
    """
    
    @staticmethod
    def create_by_provider(
        provider: Provider,
        model: str,
        system_prompt: str = "",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> BaseAgent:
        """
        Create an agent by provider type.
        
        Args:
            provider: The AI provider (anthropic, openai, google)
            model: The model identifier
            system_prompt: Optional system prompt
            max_tokens: Max tokens (uses default if not specified)
            temperature: Temperature (uses default if not specified)
            
        Returns:
            Configured BaseAgent instance
            
        Raises:
            ValueError: If provider is not supported
        """
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
        """
        Create an agent for a specific team role.
        
        Uses pre-configured models and default system prompts for each role.
        
        Args:
            role: The team role
            system_prompt: Override the default system prompt
            max_tokens: Override max tokens
            temperature: Override temperature
            
        Returns:
            Configured BaseAgent for the role
            
        Raises:
            ValueError: If role is not supported
        """
        from roles import get_role_config
        
        settings = get_settings()
        role_config = get_role_config(role)
        provider = ROLE_PROVIDERS.get(role)
        
        if not provider:
            raise ValueError(f"Unsupported role: {role}")
        
        # Get model from settings based on role
        model_map = {
            Role.SENIOR_DEV: settings.senior_dev_model,
            Role.CODER: settings.coder_model,
            Role.CODER_2: settings.coder_model_2,  # Secondary Gemini coder
            Role.QA: settings.qa_model,
            Role.BA: settings.ba_model,
            Role.REVIEWER: settings.reviewer_model,
        }
        
        model = model_map.get(role)
        if not model:
            raise ValueError(f"No model configured for role: {role}")
        
        return AgentFactory.create_by_provider(
            provider=provider,
            model=model,
            system_prompt=system_prompt or role_config.system_prompt,
            max_tokens=max_tokens or role_config.max_tokens,
            temperature=temperature if temperature is not None else role_config.temperature,
        )
