"""
Tests for LLM cache.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.services.llm.cache import LLMCache, CacheEntry
from app.services.llm.models import (
    ExplanationRequest,
    ExplanationResponse,
    ExplanationType,
    LLMProvider,
)


@pytest.fixture
def cache():
    """Create a fresh cache instance."""
    return LLMCache(ttl_hours=1, max_size=10)


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
        provider=LLMProvider.STATIC,
        topic="default_credentials",
        cached=False,
        difficulty_level="beginner",
        related_topics=["password_security"],
    )


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_is_expired_false_for_new_entry(self, sample_response):
        """New entries should not be expired."""
        entry = CacheEntry(
            response=sample_response,
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert not entry.is_expired()

    def test_is_expired_true_for_old_entry(self, sample_response):
        """Old entries should be expired."""
        entry = CacheEntry(
            response=sample_response,
            expires_at=datetime.now() - timedelta(hours=1),
        )
        assert entry.is_expired()

    def test_record_hit_increments_count(self, sample_response):
        """Recording hits should increment the counter."""
        entry = CacheEntry(
            response=sample_response,
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert entry.hit_count == 0

        entry.record_hit()
        assert entry.hit_count == 1

        entry.record_hit()
        assert entry.hit_count == 2


class TestLLMCache:
    """Tests for LLMCache."""

    def test_get_returns_none_for_miss(self, cache, sample_request):
        """Get should return None for cache miss."""
        result = cache.get(sample_request)
        assert result is None

    def test_set_and_get_returns_cached_response(
        self, cache, sample_request, sample_response
    ):
        """Set followed by get should return the cached response."""
        cache.set(sample_request, sample_response)
        result = cache.get(sample_request)

        assert result is not None
        assert result.explanation == sample_response.explanation
        assert result.cached is True  # Should be marked as cached

    def test_get_returns_none_for_expired(self, sample_request, sample_response):
        """Get should return None for expired entries."""
        # Create cache with very short TTL
        cache = LLMCache(ttl_hours=0, max_size=10)

        # Manually patch the timedelta to make entries expire immediately
        with patch.object(cache, 'ttl', timedelta(seconds=-1)):
            cache.set(sample_request, sample_response)

        # Entry should be expired
        result = cache.get(sample_request)
        assert result is None

    def test_different_requests_have_different_keys(self, cache, sample_response):
        """Different requests should have different cache keys."""
        request1 = ExplanationRequest(
            explanation_type=ExplanationType.VULNERABILITY,
            topic="topic1",
            difficulty_level="beginner",
        )
        request2 = ExplanationRequest(
            explanation_type=ExplanationType.VULNERABILITY,
            topic="topic2",
            difficulty_level="beginner",
        )

        cache.set(request1, sample_response)

        assert cache.get(request1) is not None
        assert cache.get(request2) is None

    def test_difficulty_affects_cache_key(self, cache, sample_response):
        """Different difficulty levels should have different cache keys."""
        request_beginner = ExplanationRequest(
            explanation_type=ExplanationType.VULNERABILITY,
            topic="test",
            difficulty_level="beginner",
        )
        request_advanced = ExplanationRequest(
            explanation_type=ExplanationType.VULNERABILITY,
            topic="test",
            difficulty_level="advanced",
        )

        cache.set(request_beginner, sample_response)

        assert cache.get(request_beginner) is not None
        assert cache.get(request_advanced) is None

    def test_invalidate_removes_entry(self, cache, sample_request, sample_response):
        """Invalidate should remove the entry."""
        cache.set(sample_request, sample_response)
        assert cache.get(sample_request) is not None

        result = cache.invalidate(sample_request)
        assert result is True
        assert cache.get(sample_request) is None

    def test_invalidate_returns_false_for_missing(self, cache, sample_request):
        """Invalidate should return False if entry doesn't exist."""
        result = cache.invalidate(sample_request)
        assert result is False

    def test_clear_removes_all_entries(self, cache, sample_response):
        """Clear should remove all entries."""
        for i in range(5):
            request = ExplanationRequest(
                explanation_type=ExplanationType.VULNERABILITY,
                topic=f"topic{i}",
                difficulty_level="beginner",
            )
            cache.set(request, sample_response)

        assert cache.size == 5

        count = cache.clear()
        assert count == 5
        assert cache.size == 0

    def test_eviction_when_max_size_reached(self, sample_response):
        """Cache should evict oldest entry when max size reached."""
        cache = LLMCache(ttl_hours=1, max_size=3)

        # Add 3 entries
        for i in range(3):
            request = ExplanationRequest(
                explanation_type=ExplanationType.VULNERABILITY,
                topic=f"topic{i}",
                difficulty_level="beginner",
            )
            cache.set(request, sample_response)

        assert cache.size == 3

        # Add one more - should evict oldest
        new_request = ExplanationRequest(
            explanation_type=ExplanationType.VULNERABILITY,
            topic="topic_new",
            difficulty_level="beginner",
        )
        cache.set(new_request, sample_response)

        assert cache.size == 3  # Still at max
        assert cache.get(new_request) is not None  # New entry exists

    def test_stats_tracking(self, cache, sample_request, sample_response):
        """Cache should track statistics."""
        # Initial stats
        stats = cache.stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0

        # Cache miss
        cache.get(sample_request)
        stats = cache.stats
        assert stats["misses"] == 1

        # Set and hit
        cache.set(sample_request, sample_response)
        cache.get(sample_request)
        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_size_property(self, cache, sample_request, sample_response):
        """Size property should reflect cache size."""
        assert cache.size == 0

        cache.set(sample_request, sample_response)
        assert cache.size == 1
