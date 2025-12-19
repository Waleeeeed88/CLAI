"""Role definitions for the AI team."""
from .base import RoleConfig, get_role_config
from .senior_dev import SENIOR_DEV_CONFIG
from .coder import CODER_CONFIG
from .coder_2 import CODER_2_CONFIG
from .qa import QA_CONFIG
from .ba import BA_CONFIG
from .reviewer import REVIEWER_CONFIG

__all__ = [
    "RoleConfig",
    "get_role_config",
    "SENIOR_DEV_CONFIG",
    "CODER_CONFIG",
    "CODER_2_CONFIG",
    "QA_CONFIG",
    "BA_CONFIG",
    "REVIEWER_CONFIG",
]
