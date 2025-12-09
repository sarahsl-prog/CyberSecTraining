"""
Tests for LLM providers.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.llm.models import (
    ExplanationRequest,
    ExplanationType,
    LLMProvider,
)
from app.services.llm.providers.static import StaticKnowledgeProvider
from app.services.llm.providers.ollama import OllamaProvider
from app.services.llm.providers.hosted import HostedAPIProvider


@pytest.fixture
def sample_vulnerability_request():
    """Create a sample vulnerability explanation request."""
    return ExplanationRequest(
        explanation_type=ExplanationType.VULNERABILITY,
        topic="default_credentials",
        difficulty_level="beginner",
    )


@pytest.fixture
def sample_remediation_request():
    """Create a sample remediation request."""
    return ExplanationRequest(
        explanation_type=ExplanationType.REMEDIATION,
        topic="default_credentials",
        difficulty_level="beginner",
    )


@pytest.fixture
def sample_concept_request():
    """Create a sample concept request."""
    return ExplanationRequest(
        explanation_type=ExplanationType.CONCEPT,
        topic="encryption",
        difficulty_level="beginner",
    )


class TestStaticKnowledgeProvider:
    """Tests for StaticKnowledgeProvider."""

    @pytest.fixture
    def provider(self):
        """Create a static provider instance."""
        return StaticKnowledgeProvider()

    def test_provider_type(self, provider):
        """Provider type should be STATIC."""
        assert provider.provider_type == LLMProvider.STATIC

    @pytest.mark.asyncio
    async def test_is_always_available(self, provider):
        """Static provider should always be available."""
        assert await provider.is_available() is True

    @pytest.mark.asyncio
    async def test_generates_explanation_for_known_vulnerability(
        self, provider, sample_vulnerability_request
    ):
        """Should generate explanation for known vulnerabilities."""
        response = await provider.generate_explanation(sample_vulnerability_request)

        assert response is not None
        assert response.provider == LLMProvider.STATIC
        assert response.topic == "default_credentials"
        assert "default" in response.explanation.lower()
        assert len(response.explanation) > 100

    @pytest.mark.asyncio
    async def test_generates_explanation_for_unknown_topic(self, provider):
        """Should generate generic explanation for unknown topics."""
        request = ExplanationRequest(
            explanation_type=ExplanationType.VULNERABILITY,
            topic="unknown_vuln_type_xyz",
            difficulty_level="beginner",
        )

        response = await provider.generate_explanation(request)

        assert response is not None
        assert response.provider == LLMProvider.STATIC
        # Should contain generic guidance
        assert "security" in response.explanation.lower() or "knowledge base" in response.explanation.lower()

    @pytest.mark.asyncio
    async def test_returns_appropriate_difficulty(self, provider):
        """Should return explanation at requested difficulty level."""
        beginner = ExplanationRequest(
            explanation_type=ExplanationType.VULNERABILITY,
            topic="default_credentials",
            difficulty_level="beginner",
        )
        advanced = ExplanationRequest(
            explanation_type=ExplanationType.VULNERABILITY,
            topic="default_credentials",
            difficulty_level="advanced",
        )

        beginner_response = await provider.generate_explanation(beginner)
        advanced_response = await provider.generate_explanation(advanced)

        assert beginner_response is not None
        assert advanced_response is not None

        # Both should have explanations but potentially different content
        assert beginner_response.difficulty_level == "beginner"
        assert advanced_response.difficulty_level == "advanced"

    @pytest.mark.asyncio
    async def test_includes_related_topics(self, provider, sample_vulnerability_request):
        """Should include related topics for further learning."""
        response = await provider.generate_explanation(sample_vulnerability_request)

        assert response is not None
        assert len(response.related_topics) > 0
        # For default_credentials, should suggest related security topics
        assert any("password" in t or "auth" in t for t in response.related_topics)


class TestOllamaProvider:
    """Tests for OllamaProvider."""

    @pytest.fixture
    def provider(self):
        """Create an Ollama provider instance."""
        return OllamaProvider(base_url="http://localhost:11434")

    def test_provider_type(self, provider):
        """Provider type should be OLLAMA."""
        assert provider.provider_type == LLMProvider.OLLAMA

    @pytest.mark.asyncio
    async def test_is_available_when_ollama_running(self, provider):
        """Should return True when Ollama is running with the model."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama3.2:latest"}]
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await provider.is_available()
            assert result is True

    @pytest.mark.asyncio
    async def test_is_not_available_when_no_connection(self, provider):
        """Should return False when cannot connect to Ollama."""
        import httpx

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            result = await provider.is_available()
            assert result is False

    @pytest.mark.asyncio
    async def test_generates_explanation_successfully(
        self, provider, sample_vulnerability_request
    ):
        """Should generate explanation when Ollama responds."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is an explanation about default credentials."
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            response = await provider.generate_explanation(sample_vulnerability_request)

            assert response is not None
            assert response.provider == LLMProvider.OLLAMA
            assert "default credentials" in response.explanation.lower()

    @pytest.mark.asyncio
    async def test_returns_none_on_error(self, provider, sample_vulnerability_request):
        """Should return None when Ollama returns an error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            response = await provider.generate_explanation(sample_vulnerability_request)
            assert response is None


class TestHostedAPIProvider:
    """Tests for HostedAPIProvider."""

    @pytest.fixture
    def provider(self):
        """Create a hosted API provider instance."""
        return HostedAPIProvider(
            api_key="test-key",
            base_url="https://api.example.com/v1"
        )

    def test_provider_type(self, provider):
        """Provider type should be HOSTED."""
        assert provider.provider_type == LLMProvider.HOSTED

    @pytest.mark.asyncio
    async def test_not_available_without_api_key(self):
        """Should not be available without API key."""
        provider = HostedAPIProvider(api_key=None, base_url=None)
        result = await provider.is_available()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_available_when_api_accessible(self, provider):
        """Should be available when API is accessible."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await provider.is_available()
            assert result is True

    @pytest.mark.asyncio
    async def test_not_available_on_auth_failure(self, provider):
        """Should not be available on authentication failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await provider.is_available()
            assert result is False

    @pytest.mark.asyncio
    async def test_generates_explanation_successfully(
        self, provider, sample_vulnerability_request
    ):
        """Should generate explanation when API responds."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "This is an explanation about default credentials."
                }
            }]
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            response = await provider.generate_explanation(sample_vulnerability_request)

            assert response is not None
            assert response.provider == LLMProvider.HOSTED
            assert "default credentials" in response.explanation.lower()
