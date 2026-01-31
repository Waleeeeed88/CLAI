"""Claude agent - Anthropic API."""
from typing import List
import anthropic

from .base import BaseAgent, AgentResponse, Message, MessageRole
from config import get_settings


class ClaudeAgent(BaseAgent):
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    def _initialize_client(self) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key.get_secret_value()
        )
    
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        anthropic_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages if msg.role != MessageRole.SYSTEM
        ]
        
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": anthropic_messages,
        }
        
        if not self.model.endswith("-thinking"):
            request_params["temperature"] = self.temperature
        
        if self.system_prompt:
            request_params["system"] = self.system_prompt
        
        response = self._client.messages.create(**request_params)
        
        content = "".join(
            block.text for block in response.content if block.type == "text"
        )
        
        return AgentResponse(
            content=content,
            model=response.model,
            provider=self.provider_name,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            raw_response=response,
        )
