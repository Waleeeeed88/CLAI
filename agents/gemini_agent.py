"""Gemini agent - Google API."""
from typing import List
import google.generativeai as genai

from .base import BaseAgent, AgentResponse, Message, MessageRole
from config import get_settings


class GeminiAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._chat_session = None
    
    @property
    def provider_name(self) -> str:
        return "google"
    
    def _initialize_client(self) -> None:
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key.get_secret_value())
        
        self._client = genai.GenerativeModel(
            model_name=self.model,
            generation_config=genai.GenerationConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature,
            ),
            system_instruction=self.system_prompt if self.system_prompt else None,
        )
    
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        gemini_history = [
            {
                "role": "user" if msg.role == MessageRole.USER else "model",
                "parts": [msg.content]
            }
            for msg in messages[:-1]
        ]
        
        chat = self._client.start_chat(history=gemini_history)
        last_message = messages[-1].content if messages else ""
        response = chat.send_message(last_message)
        
        usage = {}
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = {
                "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0),
            }
        
        return AgentResponse(
            content=response.text,
            model=self.model,
            provider=self.provider_name,
            usage=usage,
            finish_reason="stop",
            raw_response=response,
        )
