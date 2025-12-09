"""
LLM service module.

Provides AI-powered explanations for vulnerabilities and security concepts.
Implements a fallback chain: Ollama (local) -> Hosted API -> Static knowledge base.
"""

from .service import LLMService, get_llm_service
from .models import (
    ExplanationRequest,
    ExplanationResponse,
    ExplanationType,
    LLMProvider,
)

__all__ = [
    "LLMService",
    "get_llm_service",
    "ExplanationRequest",
    "ExplanationResponse",
    "ExplanationType",
    "LLMProvider",
]
