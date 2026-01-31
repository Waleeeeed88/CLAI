"""Base agent classes."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role.value, "content": self.content}


@dataclass
class AgentResponse:
    content: str
    model: str
    provider: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)
    
    def __str__(self) -> str:
        return self.content


class BaseAgent(ABC):
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
        pass
    
    @abstractmethod
    def _initialize_client(self) -> None:
        pass
    
    @abstractmethod
    def _send_request(self, messages: List[Message]) -> AgentResponse:
        pass
    
    def chat(self, user_message: str, include_history: bool = True) -> AgentResponse:
        if self._client is None:
            self._initialize_client()
        
        messages = list(self.conversation_history) if include_history else []
        user_msg = Message(role=MessageRole.USER, content=user_message)
        messages.append(user_msg)
        
        response = self._send_request(messages)
        self.conversation_history.append(user_msg)
        self.conversation_history.append(
            Message(role=MessageRole.ASSISTANT, content=response.content)
        )
        return response
    
    def clear_history(self) -> None:
        self.conversation_history = []
    
    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
