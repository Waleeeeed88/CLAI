"""
Claude Agent Implementation

Wrapper for Anthropic's Claude models (Opus, Sonnet).
Handles API communication and response parsing.
"""
from typing import List
import anthropic

from .base import BaseAgent, AgentResponse, Message, MessageRole
from config import get_settings


class ClaudeAgent(BaseAgent):
    """
    Agent implementation for Anthropic Claude models.
    
    Supports Claude Opus 4.5, Sonnet 4.5, and other Claude variants.
    Uses the official Anthropic Python SDK.
    
    MCP Integration: This agent can be used within MCP workflows
    for complex architecture decisions and code review tasks.
    """
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    def _initialize_client(self) -> None:
        """Initialize the Anthropic client with API key."""
        settings = get_settings()
        self._client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key.get_secret_value()
        )
    
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        """
        Send request to Claude API.
        
        Args:
            messages: List of messages to send
            
        Returns:
            AgentResponse with Claude's response
        """
        # Convert messages to Anthropic format
        # Claude uses system prompt separately
        anthropic_messages = [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
            if msg.role != MessageRole.SYSTEM
        ]
        
        # Build request parameters
        # Note: Anthropic API uses 'max_tokens' (not max_completion_tokens)
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": anthropic_messages,
        }
        
        # Add temperature if not using extended thinking models
        # Extended thinking models (claude-*-thinking) don't support temperature
        if not self.model.endswith("-thinking"):
            request_params["temperature"] = self.temperature
        
        # Add system prompt if present
        if self.system_prompt:
            request_params["system"] = self.system_prompt
        
        # Make API call
        response = self._client.messages.create(**request_params)
        
        # Extract content (Claude returns list of content blocks)
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text
        
        # Build standardized response
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
