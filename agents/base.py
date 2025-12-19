"""
Base Agent Abstract Class

Defines the interface that all AI provider agents must implement.
Uses the Template Method pattern for consistent behavior across providers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class MessageRole(Enum):
    """Standard message roles across all providers."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """
    Universal message format for all providers.
    
    Attributes:
        role: The role of the message sender
        content: The message content
        metadata: Optional metadata (timestamps, tokens, etc.)
    """
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to simple dict format."""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class AgentResponse:
    """
    Standardized response from any agent.
    
    Attributes:
        content: The generated text response
        model: The model that generated the response
        provider: The provider (anthropic, openai, google)
        usage: Token usage statistics
        finish_reason: Why the response ended
        raw_response: Original provider response (for debugging)
    """
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_tokens(self) -> int:
        """Get total tokens used."""
        return self.usage.get("total_tokens", 0)
    
    def __str__(self) -> str:
        return self.content


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.
    
    Implements the Template Method pattern where the overall flow
    is defined here, but specific steps are implemented by subclasses.
    
    Attributes:
        model: The model identifier
        system_prompt: The system/role prompt
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        conversation_history: Message history for context
    """
    
    def __init__(
        self,
        model: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.conversation_history: List[Message] = []
        self._client = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (anthropic, openai, google)."""
        pass
    
    @abstractmethod
    def _initialize_client(self) -> None:
        """Initialize the provider-specific client."""
        pass
    
    @abstractmethod
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        """
        Send request to the provider API.
        
        Args:
            messages: List of messages to send
            
        Returns:
            AgentResponse with the generated content
        """
        pass
    
    def chat(self, user_message: str, include_history: bool = True) -> AgentResponse:
        """
        Send a message and get a response.
        
        This is the main interface method that implements the template pattern.
        
        Args:
            user_message: The user's input
            include_history: Whether to include conversation history
            
        Returns:
            AgentResponse from the model
        """
        # Initialize client if needed
        if self._client is None:
            self._initialize_client()
        
        # Build message list
        messages = []
        
        # Add history if requested
        if include_history:
            messages.extend(self.conversation_history)
        
        # Add new user message
        user_msg = Message(role=MessageRole.USER, content=user_message)
        messages.append(user_msg)
        
        # Send request (implemented by subclass)
        response = self._send_request(messages)
        
        # Update conversation history
        self.conversation_history.append(user_msg)
        self.conversation_history.append(
            Message(role=MessageRole.ASSISTANT, content=response.content)
        )
        
        return response
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
    
    def set_system_prompt(self, prompt: str) -> None:
        """Update the system prompt."""
        self.system_prompt = prompt
    
    def get_context_length(self) -> int:
        """Get the current context length in messages."""
        return len(self.conversation_history)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model}, provider={self.provider_name})"
