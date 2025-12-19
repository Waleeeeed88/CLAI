"""
Base Role Configuration

Defines the structure for role configurations and system prompts.
"""
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum


@dataclass
class RoleConfig:
    """
    Configuration for a team role.
    
    Attributes:
        name: Human-readable role name
        description: What this role does
        system_prompt: The system prompt that defines behavior
        max_tokens: Default max tokens for this role
        temperature: Default temperature for this role
        capabilities: List of things this role can do
    """
    name: str
    description: str
    system_prompt: str
    max_tokens: int = 4096
    temperature: float = 0.7
    capabilities: tuple = ()


# Import role configs (will be populated by role modules)
_ROLE_CONFIGS: Dict[str, RoleConfig] = {}


def register_role(role_key: str, config: RoleConfig) -> None:
    """Register a role configuration."""
    _ROLE_CONFIGS[role_key] = config


def get_role_config(role) -> RoleConfig:
    """
    Get the configuration for a role.
    
    Args:
        role: Role enum or string key
        
    Returns:
        RoleConfig for the role
        
    Raises:
        ValueError: If role is not found
    """
    # Handle enum
    if hasattr(role, 'value'):
        role_key = role.value
    else:
        role_key = str(role)
    
    # Lazy load configs
    if not _ROLE_CONFIGS:
        from . import senior_dev, coder, coder_2, qa, ba, reviewer
    
    config = _ROLE_CONFIGS.get(role_key)
    if not config:
        raise ValueError(f"Unknown role: {role_key}")
    
    return config


def list_roles() -> Dict[str, RoleConfig]:
    """Get all registered roles."""
    if not _ROLE_CONFIGS:
        from . import senior_dev, coder, qa, ba, reviewer
    return _ROLE_CONFIGS.copy()
