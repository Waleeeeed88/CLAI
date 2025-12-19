"""
Gemini Agent Implementation

Wrapper for Google's Gemini models.
Handles API communication and response parsing.
"""
from typing import List
import google.generativeai as genai

from .base import BaseAgent, AgentResponse, Message, MessageRole
from config import get_settings


class GeminiAgent(BaseAgent):
    """
    Agent implementation for Google Gemini models.
    
    Supports Gemini Pro, Gemini 2.0 Flash, Gemini 3 Pro, and other variants.
    Uses the official Google Generative AI Python SDK.
    
    MCP Integration: This agent excels at analyzing large requirements
    documents with its massive context window (2M+ tokens).
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chat_session = None
    
    @property
    def provider_name(self) -> str:
        return "google"
    
    def _initialize_client(self) -> None:
        """Initialize the Google GenAI client with API key."""
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key.get_secret_value())
        
        # Create generation config
        generation_config = genai.GenerationConfig(
            max_output_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        
        # Create the model
        self._client = genai.GenerativeModel(
            model_name=self.model,
            generation_config=generation_config,
            system_instruction=self.system_prompt if self.system_prompt else None,
        )
    
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        """
        Send request to Gemini API.
        
        Args:
            messages: List of messages to send
            
        Returns:
            AgentResponse with Gemini's response
        """
        # Convert messages to Gemini format
        # Gemini uses 'user' and 'model' roles
        gemini_history = []
        
        for msg in messages[:-1]:  # All but last message go to history
            role = "user" if msg.role == MessageRole.USER else "model"
            gemini_history.append({
                "role": role,
                "parts": [msg.content]
            })
        
        # Start chat with history
        chat = self._client.start_chat(history=gemini_history)
        
        # Send the last message
        last_message = messages[-1].content if messages else ""
        response = chat.send_message(last_message)
        
        # Extract content
        content = response.text
        
        # Build usage dict (Gemini provides token counts differently)
        usage = {}
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = {
                "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0),
            }
        
        # Build standardized response
        return AgentResponse(
            content=content,
            model=self.model,
            provider=self.provider_name,
            usage=usage,
            finish_reason="stop",
            raw_response=response,
        )
