"""
Main LLM service.

Orchestrates LLM providers with fallback chain and caching.
"""

from typing import Optional

from app.core.logging import get_llm_logger
from app.services.llm.models import (
    ExplanationRequest,
    ExplanationResponse,
    LLMHealthStatus,
    LLMProvider,
)
from app.services.llm.cache import LLMCache
from app.services.llm.providers import (
    BaseLLMProvider,
    OllamaProvider,
    HostedAPIProvider,
    StaticKnowledgeProvider,
)

logger = get_llm_logger()


class LLMService:
    """
    Main LLM service with provider fallback chain and caching.

    The service tries providers in order:
    1. Ollama (local, privacy-preserving)
    2. Hosted API (cloud fallback)
    3. Static knowledge base (always available)

    Responses are cached to improve performance and reduce API calls.
    """

    def __init__(
        self,
        cache_ttl_hours: int = 24,
        cache_max_size: int = 1000,
    ):
        """
        Initialize the LLM service.

        Args:
            cache_ttl_hours: Cache entry TTL in hours
            cache_max_size: Maximum cache entries
        """
        # Initialize providers
        self._ollama = OllamaProvider()
        self._hosted = HostedAPIProvider()
        self._static = StaticKnowledgeProvider()

        # Initialize cache
        self._cache = LLMCache(
            ttl_hours=cache_ttl_hours,
            max_size=cache_max_size,
        )

        # Provider fallback order
        self._providers: list[BaseLLMProvider] = [
            self._ollama,
            self._hosted,
            self._static,
        ]

        logger.info("LLMService initialized with fallback chain")

    async def get_explanation(
        self,
        request: ExplanationRequest,
        skip_cache: bool = False,
        prefer_local: bool = True,
    ) -> ExplanationResponse:
        """
        Get an explanation for the given request.

        Tries cache first, then each provider in the fallback chain.

        Args:
            request: The explanation request
            skip_cache: If True, bypass cache lookup (but still cache result)
            prefer_local: If True, skip hosted API for privacy (Ollama -> Static only)

        Returns:
            ExplanationResponse with the generated explanation
        """
        logger.info(
            "Getting explanation",
            extra={
                "topic": request.topic,
                "type": request.explanation_type.value,
                "skip_cache": skip_cache,
                "prefer_local": prefer_local,
            }
        )

        # Check cache first (unless explicitly skipped)
        if not skip_cache:
            cached = self._cache.get(request)
            if cached:
                logger.info(
                    "Returning cached explanation",
                    extra={"topic": request.topic}
                )
                return cached

        # Filter providers based on preference
        # If prefer_local is True, skip hosted API for privacy
        providers = [p for p in self._providers if not (prefer_local and p.provider_type == LLMProvider.HOSTED)]

        # Try each provider in order
        for provider in providers:
            logger.debug(
                f"Trying provider: {provider.provider_type.value}",
                extra={"topic": request.topic}
            )

            # Check if provider is available
            if not await provider.is_available():
                logger.debug(
                    f"Provider {provider.provider_type.value} not available"
                )
                continue

            # Try to generate explanation
            response = await provider.generate_explanation(request)

            if response:
                # Cache successful response (except static fallback)
                if provider.provider_type != LLMProvider.STATIC:
                    self._cache.set(request, response)

                logger.info(
                    "Explanation generated successfully",
                    extra={
                        "topic": request.topic,
                        "provider": response.provider.value,
                    }
                )
                return response

            logger.warning(
                f"Provider {provider.provider_type.value} failed to generate"
            )

        # This should never happen since static is always available
        # but handle it gracefully
        logger.error("All providers failed - this should not happen")
        return ExplanationResponse(
            explanation="Unable to generate explanation at this time. Please try again later.",
            provider=LLMProvider.STATIC,
            topic=request.topic,
            cached=False,
            difficulty_level=request.difficulty_level,
            related_topics=[],
        )

    async def check_health(self) -> LLMHealthStatus:
        """
        Check the health status of all LLM providers.

        Returns:
            LLMHealthStatus with availability information
        """
        ollama_available = await self._ollama.is_available()
        hosted_available = await self._hosted.is_available()

        # Determine active provider
        if ollama_available:
            active = LLMProvider.OLLAMA
        elif hosted_available:
            active = LLMProvider.HOSTED
        else:
            active = LLMProvider.STATIC

        return LLMHealthStatus(
            ollama_available=ollama_available,
            hosted_available=hosted_available,
            active_provider=active,
            cache_size=self._cache.size,
        )

    def clear_cache(self) -> int:
        """
        Clear the explanation cache.

        Returns:
            Number of entries cleared
        """
        count = self._cache.clear()
        logger.info(f"Cache cleared: {count} entries removed")
        return count

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        return self._cache.stats


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """
    Get the singleton LLM service instance.

    Returns:
        The global LLMService instance
    """
    global _llm_service

    if _llm_service is None:
        _llm_service = LLMService()

    return _llm_service
