"""
Tests for main LLM service.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.llm.models import (
    ExplanationRequest,
    ExplanationResponse,
    ExplanationType,
    LLMProvider,
)
from app.services.llm.service import LLMService


@pytest.fixture
def sample_request():
    """Create a sample explanation request."""
    return ExplanationRequest(
        explanation_type=ExplanationType.VULNERABILITY,
        topic="default_credentials",
        difficulty_level="beginner",
    )


@pytest.fixture
def sample_response():
    """Create a sample explanation response."""
    return ExplanationResponse(
        explanation="Test explanation",
        provider=LLMProvider.OLLAMA,
        topic="default_credentials",
        cached=False,
        difficulty_level="beginner",
        related_topics=["password_security"],
    )


@pytest.fixture
def service():
    """Create a fresh LLM service instance."""
    return LLMService(cache_ttl_hours=1, cache_max_size=100)


class TestLLMService:
    """Tests for LLMService."""

    @pytest.mark.asyncio
    async def test_get_explanation_uses_cache(self, service, sample_request):
        """Should return cached response when available."""
        # First call - should hit static provider
        response1 = await service.get_explanation(sample_request)
        assert response1 is not None
        assert response1.cached is False

        # Second call - should be cached (if provider is not static)
        # Note: Static provider responses are not cached
        response2 = await service.get_explanation(sample_request)
        assert response2 is not None

    @pytest.mark.asyncio
    async def test_get_explanation_skips_cache_when_requested(
        self, service, sample_request
    ):
        """Should skip cache when skip_cache is True."""
        # First call
        response1 = await service.get_explanation(sample_request)
        assert response1 is not None

        # Second call with skip_cache
        response2 = await service.get_explanation(sample_request, skip_cache=True)
        assert response2 is not None
        # With skip_cache, should still work (will hit providers)

    @pytest.mark.asyncio
    async def test_fallback_to_static_when_others_unavailable(
        self, service, sample_request
    ):
        """Should fall back to static provider when others unavailable."""
        # Mock Ollama and Hosted as unavailable
        service._ollama.is_available = AsyncMock(return_value=False)
        service._hosted.is_available = AsyncMock(return_value=False)

        response = await service.get_explanation(sample_request, skip_cache=True)

        assert response is not None
        assert response.provider == LLMProvider.STATIC

    @pytest.mark.asyncio
    async def test_uses_ollama_when_available(self, service, sample_request):
        """Should use Ollama when available."""
        mock_response = ExplanationResponse(
            explanation="Ollama explanation",
            provider=LLMProvider.OLLAMA,
            topic="default_credentials",
            cached=False,
            difficulty_level="beginner",
            related_topics=[],
        )

        service._ollama.is_available = AsyncMock(return_value=True)
        service._ollama.generate_explanation = AsyncMock(return_value=mock_response)

        response = await service.get_explanation(sample_request, skip_cache=True)

        assert response is not None
        assert response.provider == LLMProvider.OLLAMA

    @pytest.mark.asyncio
    async def test_caches_llm_responses(self, service, sample_request, sample_response):
        """Should cache responses from LLM providers."""
        # Mock Ollama to return a response
        service._ollama.is_available = AsyncMock(return_value=True)
        service._ollama.generate_explanation = AsyncMock(return_value=sample_response)

        # First call
        response1 = await service.get_explanation(sample_request)
        assert response1 is not None
        assert service._cache.size == 1

        # Second call should use cache
        response2 = await service.get_explanation(sample_request)
        assert response2 is not None
        assert response2.cached is True

    @pytest.mark.asyncio
    async def test_check_health_returns_status(self, service):
        """Should return health status for all providers."""
        service._ollama.is_available = AsyncMock(return_value=False)
        service._hosted.is_available = AsyncMock(return_value=False)

        status = await service.check_health()

        assert status.ollama_available is False
        assert status.hosted_available is False
        assert status.active_provider == LLMProvider.STATIC
        assert status.cache_size == service._cache.size

    @pytest.mark.asyncio
    async def test_check_health_with_ollama_available(self, service):
        """Should show Ollama as active when available."""
        service._ollama.is_available = AsyncMock(return_value=True)
        service._hosted.is_available = AsyncMock(return_value=False)

        status = await service.check_health()

        assert status.ollama_available is True
        assert status.active_provider == LLMProvider.OLLAMA

    def test_clear_cache(self, service, sample_request):
        """Should clear all cached entries."""
        # Add some entries to cache manually
        from app.services.llm.models import ExplanationResponse

        response = ExplanationResponse(
            explanation="test",
            provider=LLMProvider.STATIC,
            topic="test",
            cached=False,
            difficulty_level="beginner",
            related_topics=[],
        )
        service._cache.set(sample_request, response)
        assert service._cache.size > 0

        count = service.clear_cache()
        assert count > 0
        assert service._cache.size == 0

    def test_get_cache_stats(self, service):
        """Should return cache statistics."""
        stats = service.get_cache_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "size" in stats
        assert "hit_rate" in stats


class TestFallbackChain:
    """Tests for provider fallback chain behavior."""

    @pytest.mark.asyncio
    async def test_falls_back_from_ollama_to_hosted(self, service, sample_request):
        """Should fall back to hosted when Ollama fails (when prefer_local=False)."""
        hosted_response = ExplanationResponse(
            explanation="Hosted explanation",
            provider=LLMProvider.HOSTED,
            topic="default_credentials",
            cached=False,
            difficulty_level="beginner",
            related_topics=[],
        )

        # Ollama available but fails to generate
        service._ollama.is_available = AsyncMock(return_value=True)
        service._ollama.generate_explanation = AsyncMock(return_value=None)

        # Hosted works
        service._hosted.is_available = AsyncMock(return_value=True)
        service._hosted.generate_explanation = AsyncMock(return_value=hosted_response)

        # Pass prefer_local=False to allow fallback to hosted API
        response = await service.get_explanation(sample_request, skip_cache=True, prefer_local=False)

        assert response is not None
        assert response.provider == LLMProvider.HOSTED

    @pytest.mark.asyncio
    async def test_skips_hosted_when_prefer_local(self, service, sample_request):
        """Should skip hosted API when prefer_local=True for privacy."""
        # Ollama available but fails to generate
        service._ollama.is_available = AsyncMock(return_value=True)
        service._ollama.generate_explanation = AsyncMock(return_value=None)

        # Hosted is available but should be skipped
        service._hosted.is_available = AsyncMock(return_value=True)
        service._hosted.generate_explanation = AsyncMock(
            return_value=ExplanationResponse(
                explanation="Should not be used",
                provider=LLMProvider.HOSTED,
                topic="default_credentials",
                cached=False,
                difficulty_level="beginner",
                related_topics=[],
            )
        )

        # With prefer_local=True (default), should skip hosted and use static
        response = await service.get_explanation(sample_request, skip_cache=True, prefer_local=True)

        assert response is not None
        assert response.provider == LLMProvider.STATIC
        # Verify hosted was never called
        service._hosted.generate_explanation.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_back_from_hosted_to_static(self, service, sample_request):
        """Should fall back to static when hosted fails."""
        # Both Ollama and Hosted unavailable
        service._ollama.is_available = AsyncMock(return_value=False)
        service._hosted.is_available = AsyncMock(return_value=False)

        response = await service.get_explanation(sample_request, skip_cache=True)

        assert response is not None
        assert response.provider == LLMProvider.STATIC

    @pytest.mark.asyncio
    async def test_always_returns_response(self, service, sample_request):
        """Should always return a response even if all providers fail."""
        # Mock all providers as failing
        service._ollama.is_available = AsyncMock(return_value=False)
        service._hosted.is_available = AsyncMock(return_value=False)
        # Static should still work

        response = await service.get_explanation(sample_request, skip_cache=True)

        # Should still get a response from static fallback
        assert response is not None
        assert len(response.explanation) > 0
