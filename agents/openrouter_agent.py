"""OpenRouter agent - OpenAI-compatible API."""
from typing import Dict

from openai import OpenAI

from .base import DEFAULT_REQUEST_TIMEOUT
from .gpt_agent import GPTAgent
from config import get_settings


class OpenRouterAgent(GPTAgent):
    @property
    def provider_name(self) -> str:
        return "openrouter"

    def _initialize_client(self) -> None:
        settings = get_settings()
        key = settings.openrouter_api_key
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your .env file.")

        headers: Dict[str, str] = {"X-Title": settings.openrouter_app_name}
        if settings.openrouter_site_url:
            headers["HTTP-Referer"] = settings.openrouter_site_url

        self._client = OpenAI(
            api_key=key.get_secret_value(),
            base_url=settings.openrouter_base_url,
            default_headers=headers,
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
