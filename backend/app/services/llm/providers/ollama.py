"""
Ollama LLM provider.

Provides integration with local Ollama instance for privacy-focused
LLM interactions.
"""

from typing import Optional

import httpx

from app.config import settings
from app.core.logging import get_llm_logger
from app.services.llm.models import (
    ExplanationRequest,
    ExplanationResponse,
    LLMProvider,
)
from .base import BaseLLMProvider

logger = get_llm_logger()


class OllamaProvider(BaseLLMProvider):
    """
    Ollama provider for local LLM inference.

    Uses the Ollama API to generate explanations locally, ensuring
    privacy and offline capability.
    """

    # Default model to use - llama3.2 is a good balance of quality and speed
    DEFAULT_MODEL = "llama3.2"

    # Timeout for API requests (seconds)
    REQUEST_TIMEOUT = 60.0

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the Ollama provider.

        Args:
            base_url: Ollama API base URL (defaults to settings)
            model: Model to use for generation (defaults to llama3.2)
        """
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or self.DEFAULT_MODEL
        self._available: Optional[bool] = None

        logger.info(
            f"OllamaProvider initialized",
            extra={"base_url": self.base_url, "model": self.model}
        )

    @property
    def provider_type(self) -> LLMProvider:
        """Return the provider type."""
        return LLMProvider.OLLAMA

    async def is_available(self) -> bool:
        """
        Check if Ollama is running and has the required model.

        Returns:
            True if Ollama is available and model is loaded
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Check if Ollama is running
                response = await client.get(f"{self.base_url}/api/tags")

                if response.status_code != 200:
                    logger.warning("Ollama API returned non-200 status")
                    self._available = False
                    return False

                # Check if our model is available
                data = response.json()
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]

                if self.model.split(":")[0] not in models:
                    logger.info(
                        f"Model {self.model} not found in Ollama",
                        extra={"available_models": models}
                    )
                    # Model not available but Ollama is running
                    # We could try to pull the model here, but for now just mark unavailable
                    self._available = False
                    return False

                self._available = True
                logger.debug("Ollama is available with required model")
                return True

        except httpx.ConnectError:
            logger.debug("Cannot connect to Ollama - service may not be running")
            self._available = False
            return False
        except Exception as e:
            logger.warning(f"Error checking Ollama availability: {e}")
            self._available = False
            return False

    async def generate_explanation(
        self,
        request: ExplanationRequest,
    ) -> Optional[ExplanationResponse]:
        """
        Generate an explanation using Ollama.

        Args:
            request: The explanation request

        Returns:
            ExplanationResponse if successful, None otherwise
        """
        logger.info(
            f"Generating explanation via Ollama",
            extra={
                "topic": request.topic,
                "type": request.explanation_type.value,
                "model": self.model,
            }
        )

        prompt = self._build_prompt(request)

        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 500,  # Limit response length
                        },
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"Ollama API error: {response.status_code}",
                        extra={"response": response.text[:500]}
                    )
                    return None

                data = response.json()
                explanation = data.get("response", "").strip()

                if not explanation:
                    logger.warning("Ollama returned empty response")
                    return None

                logger.info(
                    "Ollama explanation generated successfully",
                    extra={"topic": request.topic, "length": len(explanation)}
                )

                return ExplanationResponse(
                    explanation=explanation,
                    provider=self.provider_type,
                    topic=request.topic,
                    cached=False,
                    difficulty_level=request.difficulty_level,
                    related_topics=self._extract_related_topics(request.topic),
                )

        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating Ollama explanation: {e}")
            return None
