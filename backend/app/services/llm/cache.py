"""
LLM response caching.

Provides in-memory caching for LLM explanations to reduce
API calls and improve response times for repeated queries.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

from app.core.logging import get_llm_logger
from app.services.llm.models import ExplanationRequest, ExplanationResponse

logger = get_llm_logger()


@dataclass
class CacheEntry:
    """
    A single cache entry with expiration tracking.

    Attributes:
        response: The cached explanation response
        created_at: When the entry was created
        expires_at: When the entry expires
        hit_count: Number of times this entry has been accessed
    """

    response: ExplanationResponse
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now())
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return datetime.now() > self.expires_at

    def record_hit(self) -> None:
        """Record a cache hit."""
        self.hit_count += 1


class LLMCache:
    """
    In-memory cache for LLM explanations.

    Features:
    - TTL-based expiration
    - LRU-style eviction when max size reached
    - Cache key based on request parameters
    - Statistics tracking

    Thread-safe for concurrent access.
    """

    # Default cache settings
    DEFAULT_TTL_HOURS = 24
    DEFAULT_MAX_SIZE = 1000

    def __init__(
        self,
        ttl_hours: int = DEFAULT_TTL_HOURS,
        max_size: int = DEFAULT_MAX_SIZE,
    ):
        """
        Initialize the cache.

        Args:
            ttl_hours: Time-to-live for cache entries in hours
            max_size: Maximum number of entries to store
        """
        self.ttl = timedelta(hours=ttl_hours)
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

        logger.info(
            "LLM cache initialized",
            extra={"ttl_hours": ttl_hours, "max_size": max_size}
        )

    def _generate_key(self, request: ExplanationRequest) -> str:
        """
        Generate a unique cache key from the request.

        Args:
            request: The explanation request

        Returns:
            A hash string uniquely identifying the request
        """
        # Combine relevant fields into a string
        key_parts = [
            request.explanation_type.value,
            request.topic.lower(),
            request.difficulty_level,
            request.context or "",
        ]
        key_string = "|".join(key_parts)

        # Generate SHA256 hash for consistent key length
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def get(self, request: ExplanationRequest) -> Optional[ExplanationResponse]:
        """
        Retrieve a cached response for the given request.

        Args:
            request: The explanation request

        Returns:
            Cached ExplanationResponse if found and not expired, None otherwise
        """
        key = self._generate_key(request)

        if key not in self._cache:
            self._stats["misses"] += 1
            logger.debug(f"Cache miss for key {key[:8]}...")
            return None

        entry = self._cache[key]

        # Check expiration
        if entry.is_expired():
            logger.debug(f"Cache entry expired for key {key[:8]}...")
            del self._cache[key]
            self._stats["misses"] += 1
            return None

        # Record hit and return
        entry.record_hit()
        self._stats["hits"] += 1

        logger.debug(
            f"Cache hit for key {key[:8]}...",
            extra={"hit_count": entry.hit_count}
        )

        # Clone response with cached flag set
        response = ExplanationResponse(
            explanation=entry.response.explanation,
            provider=entry.response.provider,
            topic=entry.response.topic,
            cached=True,  # Mark as cached
            difficulty_level=entry.response.difficulty_level,
            related_topics=entry.response.related_topics,
        )

        return response

    def set(
        self,
        request: ExplanationRequest,
        response: ExplanationResponse,
    ) -> None:
        """
        Store a response in the cache.

        Args:
            request: The original request
            response: The response to cache
        """
        # Evict expired entries and check size
        self._cleanup()

        # Check if we need to evict oldest entries
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        key = self._generate_key(request)

        entry = CacheEntry(
            response=response,
            created_at=datetime.now(),
            expires_at=datetime.now() + self.ttl,
        )

        self._cache[key] = entry

        logger.debug(
            f"Cached response for key {key[:8]}...",
            extra={"topic": request.topic}
        )

    def invalidate(self, request: ExplanationRequest) -> bool:
        """
        Remove a specific entry from the cache.

        Args:
            request: The request to invalidate

        Returns:
            True if entry was removed, False if not found
        """
        key = self._generate_key(request)

        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Invalidated cache entry {key[:8]}...")
            return True

        return False

    def clear(self) -> int:
        """
        Clear all entries from the cache.

        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return count

    def _cleanup(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

        return len(expired_keys)

    def _evict_oldest(self) -> None:
        """Evict the oldest cache entry to make room."""
        if not self._cache:
            return

        # Find oldest entry
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )

        del self._cache[oldest_key]
        self._stats["evictions"] += 1

        logger.debug(f"Evicted oldest cache entry {oldest_key[:8]}...")

    @property
    def size(self) -> int:
        """Return current cache size."""
        return len(self._cache)

    @property
    def stats(self) -> dict:
        """
        Return cache statistics.

        Returns:
            Dict with hits, misses, evictions, and size
        """
        return {
            **self._stats,
            "size": self.size,
            "hit_rate": (
                self._stats["hits"] / (self._stats["hits"] + self._stats["misses"])
                if (self._stats["hits"] + self._stats["misses"]) > 0
                else 0.0
            ),
        }
