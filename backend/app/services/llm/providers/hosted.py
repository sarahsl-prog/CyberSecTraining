"""
Hosted LLM API provider.

Provides integration with hosted LLM APIs (like Anthropic, OpenAI)
as a fallback when local Ollama is not available.
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


class HostedAPIProvider(BaseLLMProvider):
    """
    Hosted API provider for cloud-based LLM inference.

    Uses a hosted LLM API as a fallback when local Ollama is not available.
    Supports OpenAI-compatible APIs.
    """

    # Timeout for API requests (seconds)
    REQUEST_TIMEOUT = 30.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the Hosted API provider.

        Args:
            api_key: API key for authentication
            base_url: API base URL
        """
        self.api_key = api_key or settings.hosted_llm_api_key
        self.base_url = base_url or settings.hosted_llm_base_url
        self._available: Optional[bool] = None

        logger.info(
            "HostedAPIProvider initialized",
            extra={
                "base_url": self.base_url,
                "has_key": bool(self.api_key),
            }
        )

    @property
    def provider_type(self) -> LLMProvider:
        """Return the provider type."""
        return LLMProvider.HOSTED

    async def is_available(self) -> bool:
        """
        Check if the hosted API is configured and accessible.

        Returns:
            True if API key is set and API is reachable
        """
        # Must have API key configured
        if not self.api_key or not self.base_url:
            logger.debug("Hosted API not configured (missing key or URL)")
            self._available = False
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Make a lightweight request to check connectivity
                # Most OpenAI-compatible APIs have a /models endpoint
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )

                if response.status_code == 200:
                    self._available = True
                    logger.debug("Hosted API is available")
                    return True

                # 401/403 means key issue, still consider service "reachable"
                # but not available due to auth
                if response.status_code in (401, 403):
                    logger.warning("Hosted API authentication failed")
                    self._available = False
                    return False

                logger.warning(f"Hosted API returned status {response.status_code}")
                self._available = False
                return False

        except httpx.ConnectError:
            logger.debug("Cannot connect to hosted API")
            self._available = False
            return False
        except Exception as e:
            logger.warning(f"Error checking hosted API availability: {e}")
            self._available = False
            return False

    async def generate_explanation(
        self,
        request: ExplanationRequest,
    ) -> Optional[ExplanationResponse]:
        """
        Generate an explanation using the hosted API.

        Args:
            request: The explanation request

        Returns:
            ExplanationResponse if successful, None otherwise
        """
        if not self.api_key or not self.base_url:
            logger.warning("Hosted API not configured")
            return None

        logger.info(
            f"Generating explanation via hosted API",
            extra={
                "topic": request.topic,
                "type": request.explanation_type.value,
            }
        )

        prompt = self._build_prompt(request)

        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                # Use OpenAI-compatible chat completions API
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-3.5-turbo",  # Default model
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a helpful cybersecurity educator."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7,
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"Hosted API error: {response.status_code}",
                        extra={"response": response.text[:500]}
                    )
                    return None

                data = response.json()
                choices = data.get("choices", [])

                if not choices:
                    logger.warning("Hosted API returned no choices")
                    return None

                explanation = choices[0].get("message", {}).get("content", "").strip()

                if not explanation:
                    logger.warning("Hosted API returned empty content")
                    return None

                logger.info(
                    "Hosted API explanation generated successfully",
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
            logger.error("Hosted API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error generating hosted API explanation: {e}")
            return None
