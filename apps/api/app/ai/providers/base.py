"""Base AI provider abstractions and data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolCallSpec:
    """Specification of a tool call requested by the model."""

    name: str
    arguments: Dict[str, Any]
    call_id: str = ""


@dataclass
class ToolResultSpec:
    """Result of an executed tool call returned to the model."""

    call_id: str
    name: str
    result: Dict[str, Any]


@dataclass
class LLMMessage:
    """Message representation in the AI provider abstraction."""

    role: str  # "system", "user", "assistant", "tool"
    content: str = ""
    tool_calls: Optional[List[ToolCallSpec]] = None
    tool_results: Optional[List[ToolResultSpec]] = None


@dataclass
class ToolDefinition:
    """JSON-schema definition for an analytical tool exposed to the model."""

    name: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class LLMUsage:
    """Token usage metadata for an AI request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    """Response returned by an AI provider."""

    message: str = ""
    tool_calls: List[ToolCallSpec] = field(default_factory=list)
    finish_reason: str = "stop"  # "stop", "tool_calls", "length", "error"
    usage: LLMUsage = field(default_factory=LLMUsage)
    raw_response: Optional[Dict[str, Any]] = None


class AIProviderError(Exception):
    """Base exception for AI provider errors."""

    pass


class AIProviderTimeoutError(AIProviderError):
    """Raised when an AI provider call times out."""

    pass


class AIProviderAuthError(AIProviderError):
    """Raised when an AI provider authentication fails."""

    pass


class AIProviderRateLimitError(AIProviderError):
    """Raised when an AI provider rate limit is hit."""

    pass


class LLMProvider(ABC):
    """Abstract base class for all AI LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM, optionally calling registered tools."""
        pass
