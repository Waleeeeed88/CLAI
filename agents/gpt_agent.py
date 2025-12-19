"""
GPT Agent Implementation

Wrapper for OpenAI's GPT models (GPT-4o, Codex).
Handles API communication and response parsing.
"""
from typing import List
from openai import OpenAI

from .base import BaseAgent, AgentResponse, Message, MessageRole
from config import get_settings


class GPTAgent(BaseAgent):
    """
    Agent implementation for OpenAI GPT models.
    
    Supports GPT-4o, GPT-4-turbo, and other OpenAI models.
    Uses the official OpenAI Python SDK.
    """
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client with API key."""
        settings = get_settings()
        self._client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value()
        )
    
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        """
        Send request to OpenAI API.
        
        Args:
            messages: List of messages to send
            
        Returns:
            AgentResponse with GPT's response
        """
        # Convert messages to OpenAI format
        openai_messages = []
        
        # Add system prompt first if present
        if self.system_prompt:
            openai_messages.append({
                "role": "system",
                "content": self.system_prompt
            })
        
        # Add conversation messages
        for msg in messages:
            if msg.role != MessageRole.SYSTEM:
                openai_messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        # Make API call
        # Use max_completion_tokens for newer models (o1, o3, gpt-5.x)
        response = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=openai_messages,
        )
        
        # Extract content
        choice = response.choices[0]
        content = choice.message.content or ""
        
        # Build usage dict
        usage = {}
        if response.usage:
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        # Build standardized response
        return AgentResponse(
            content=content,
            model=response.model,
            provider=self.provider_name,
            usage=usage,
            finish_reason=choice.finish_reason,
            raw_response=response,
        )
