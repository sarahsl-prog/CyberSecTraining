"""
LLM service data models.

Defines request/response types for the LLM explanation service.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ExplanationType(str, Enum):
    """Types of explanations the LLM can provide."""

    VULNERABILITY = "vulnerability"  # Explain a specific vulnerability
    REMEDIATION = "remediation"      # Explain how to fix a vulnerability
    CONCEPT = "concept"              # Explain a security concept
    SERVICE = "service"              # Explain a network service
    RISK = "risk"                    # Explain potential risks


class LLMProvider(str, Enum):
    """Available LLM providers."""

    OLLAMA = "ollama"        # Local Ollama instance
    HOSTED = "hosted"        # Hosted API (e.g., Anthropic, OpenAI)
    STATIC = "static"        # Static knowledge base fallback


class ExplanationRequest(BaseModel):
    """
    Request for an LLM explanation.

    Attributes:
        explanation_type: The type of explanation requested
        topic: The specific topic to explain (e.g., vulnerability type, service name)
        context: Optional additional context for better explanation
        difficulty_level: Target audience difficulty level (beginner, intermediate, advanced)
    """

    explanation_type: ExplanationType = Field(
        description="Type of explanation requested"
    )
    topic: str = Field(
        min_length=1,
        max_length=500,
        description="The topic to explain"
    )
    context: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Additional context for the explanation"
    )
    difficulty_level: str = Field(
        default="beginner",
        pattern="^(beginner|intermediate|advanced)$",
        description="Target difficulty level"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "explanation_type": "vulnerability",
                    "topic": "default_credentials",
                    "context": "Found on a router at 192.168.1.1",
                    "difficulty_level": "beginner"
                }
            ]
        }
    }


class ExplanationResponse(BaseModel):
    """
    Response containing an LLM-generated explanation.

    Attributes:
        explanation: The generated explanation text
        provider: Which provider generated the explanation
        topic: The topic that was explained
        cached: Whether the response came from cache
        difficulty_level: The difficulty level of the explanation
        related_topics: Suggested related topics to explore
    """

    explanation: str = Field(
        description="The generated explanation text"
    )
    provider: LLMProvider = Field(
        description="Which LLM provider generated this explanation"
    )
    topic: str = Field(
        description="The topic that was explained"
    )
    cached: bool = Field(
        default=False,
        description="Whether this response was served from cache"
    )
    difficulty_level: str = Field(
        default="beginner",
        description="The difficulty level of the explanation"
    )
    related_topics: list[str] = Field(
        default_factory=list,
        description="Suggested related topics to explore"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "explanation": "Default credentials are...",
                    "provider": "ollama",
                    "topic": "default_credentials",
                    "cached": False,
                    "difficulty_level": "beginner",
                    "related_topics": ["password_security", "authentication"]
                }
            ]
        }
    }


class LLMHealthStatus(BaseModel):
    """
    Health status of LLM providers.

    Attributes:
        ollama_available: Whether Ollama is available
        hosted_available: Whether hosted API is available
        active_provider: Currently active provider
        cache_size: Number of cached explanations
    """

    ollama_available: bool = Field(
        default=False,
        description="Whether local Ollama instance is available"
    )
    hosted_available: bool = Field(
        default=False,
        description="Whether hosted LLM API is available"
    )
    active_provider: LLMProvider = Field(
        description="Currently active LLM provider"
    )
    cache_size: int = Field(
        default=0,
        description="Number of explanations in cache"
    )
