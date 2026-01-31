"""GPT agent - OpenAI API."""
from typing import List
from openai import OpenAI

from .base import BaseAgent, AgentResponse, Message, MessageRole
from config import get_settings


class GPTAgent(BaseAgent):
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def _initialize_client(self) -> None:
        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key.get_secret_value())
    
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        openai_messages = []
        
        if self.system_prompt:
            openai_messages.append({"role": "system", "content": self.system_prompt})
        
        for msg in messages:
            if msg.role != MessageRole.SYSTEM:
                openai_messages.append({"role": msg.role.value, "content": msg.content})
        
        response = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=openai_messages,
        )
        
        choice = response.choices[0]
        content = choice.message.content or ""
        
        usage = {}
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return AgentResponse(
            content=content,
            model=response.model,
            provider=self.provider_name,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw_response=response,
        )
