"""
Rate limiter for API endpoints.

This module provides rate limiting functionality to prevent abuse
and ensure fair usage of API resources.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Dict
from collections import defaultdict
import asyncio

from fastapi import Request, HTTPException, status
from app.core.logging import get_logger

logger = get_logger("ratelimit")


class RateLimiter:
    """
    Simple in-memory rate limiter using token bucket algorithm.
    
    This is a basic implementation. For production with multiple instances,
    consider using Redis-based rate limiting.
    """
    
    def __init__(
        self,
        default_rate: int = 10,  # requests per minute
        default_burst: int = 20,  # max burst size
    ):
        """
        Initialize the rate limiter.
        
        Args:
            default_rate: Default requests per minute per user
            default_burst: Maximum burst size allowed
        """
        self.default_rate = default_rate
        self.default_burst = default_burst
        
        # Storage for user tokens: {user_id: {tokens, last_update}}
        self._tokens: Dict[str, Dict[str, float]] = {}
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(
        self,
        user_id: str = "default",
        endpoint: str = "default",
        rate: Optional[int] = None,
        burst: Optional[int] = None,
    ) -> bool:
        """
        Check if a request should be allowed based on rate limit.
        
        Args:
            user_id: Identifier for the user (e.g., IP, user ID)
            endpoint: Endpoint identifier
            rate: Custom rate limit (requests per minute)
            burst: Custom burst size
            
        Returns:
            True if request is allowed, False otherwise
        """
        effective_rate = rate or self.default_rate
        effective_burst = burst or self.default_burst
        
        key = f"{user_id}:{endpoint}"
        
        async with self._lock:
            now = datetime.now(UTC)
            
            if key not in self._tokens:
                # First request for this user/endpoint
                self._tokens[key] = {
                    "tokens": effective_burst - 1,
                    "last_update": now,
                }
                return True
            
            user_data = self._tokens[key]
            time_passed = (now - user_data["last_update"]).total_seconds()
            
            # Replenish tokens based on time passed
            # Rate is per minute, so tokens_per_second = rate / 60
            tokens_to_add = time_passed * (effective_rate / 60)
            
            # Don't exceed burst capacity
            user_data["tokens"] = min(
                effective_burst,
                user_data["tokens"] + tokens_to_add
            )
            user_data["last_update"] = now
            
            # Check if we have enough tokens
            if user_data["tokens"] >= 1:
                user_data["tokens"] -= 1
                return True
            else:
                logger.warning(
                    f"Rate limit exceeded for user {user_id} on endpoint {endpoint}"
                )
                return False
    
    def get_rate_limit_headers(
        self,
        user_id: str = "default",
        endpoint: str = "default",
        rate: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        Get rate limit headers for response.
        
        Args:
            user_id: User identifier
            endpoint: Endpoint identifier
            rate: Rate limit being enforced
            
        Returns:
            Dictionary with rate limit headers
        """
        effective_rate = rate or self.default_rate
        key = f"{user_id}:{endpoint}"
        
        headers = {
            "X-RateLimit-Limit": str(effective_rate),
        }
        
        if key in self._tokens:
            user_data = self._tokens[key]
            headers["X-RateLimit-Remaining"] = str(int(user_data["tokens"]))
            # Calculate reset time (when tokens will be fully replenished)
            now = datetime.now(UTC)
            time_passed = (now - user_data["last_update"]).total_seconds()
            tokens_needed = effective_rate - user_data["tokens"]
            seconds_to_reset = (tokens_needed / effective_rate) * 60
            reset_time = now + timedelta(seconds=seconds_to_reset)
            headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
        
        return headers
    
    async def cleanup_old_entries(self, max_age_hours: int = 24) -> int:
        """
        Remove old entries from the rate limiter storage.
        
        Args:
            max_age_hours: Maximum age of entries to keep
            
        Returns:
            Number of entries removed
        """
        async with self._lock:
            cutoff = datetime.now(UTC) - timedelta(hours=max_age_hours)
            keys_to_remove = []
            
            for key, data in self._tokens.items():
                if data["last_update"] < cutoff:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._tokens[key]
            
            if keys_to_remove:
                logger.info(f"Cleaned up {len(keys_to_remove)} old rate limit entries")
            
            return len(keys_to_remove)


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get the global rate limiter instance.
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


# FastAPI dependency for rate limiting (Fix Issue #16)
async def rate_limit_decorator(
    request: Request,
    user_id: str = "default",
    rate: Optional[int] = None,
    burst: Optional[int] = None,
):
    """
    FastAPI dependency for rate limiting.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            _=Depends(check_rate_limit(rate=20))
        ):
            ...
    
    Args:
        request: FastAPI request object
        user_id: User identifier
        rate: Custom rate limit
        burst: Custom burst size
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    limiter = get_rate_limiter()
    
    # Get client IP for user_id if not provided
    if user_id == "default":
        user_id = request.client.host if request.client else "unknown"
    
    endpoint = request.url.path
    
    allowed = await limiter.check_rate_limit(
        user_id=user_id,
        endpoint=endpoint,
        rate=rate,
        burst=burst,
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers=limiter.get_rate_limit_headers(user_id, endpoint, rate),
        )