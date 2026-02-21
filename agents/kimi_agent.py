"""Kimi agent - Moonshot AI (OpenAI-compatible API)."""
from openai import OpenAI

from .gpt_agent import GPTAgent
from .base import DEFAULT_REQUEST_TIMEOUT
from config import get_settings


class KimiAgent(GPTAgent):
    @property
    def provider_name(self) -> str:
        return "kimi"

    def _initialize_client(self) -> None:
        settings = get_settings()
        key = settings.kimi_api_key
        if not key:
            raise RuntimeError(
                "KIMI_API_KEY is not set. Add it to your .env file."
            )
        self._client = OpenAI(
            api_key=key.get_secret_value(),
            base_url="https://api.moonshot.cn/v1",
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
