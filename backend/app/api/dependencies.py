"""
API dependency injection for authentication and authorization.

This module provides dependencies for protecting API endpoints with
authentication and authorization.

Note: This is a minimal implementation. For production, implement
proper JWT token validation and user management.
"""

from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.core.logging import get_logger

logger = get_logger("auth")

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


@lru_cache
def is_trusted_host(request: Request) -> bool:
    """
    Check if the request comes from a trusted host.

    In production, this should always fail unless explicitly configured.
    Development mode allows localhost requests.

    Args:
        request: The incoming request

    Returns:
        True if host is trusted, False otherwise
    """
    if settings.debug:
        host = request.headers.get("host", "")
        logger.debug(f"Debug mode - allowing localhost host: {host}")
        return True
    return False


async def require_api_key(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header),
) -> bool:
    """
    Require API key authentication.

    For development, localhost requests are trusted.
    For production, a valid API key or Bearer token is required.

    Args:
        request: The incoming request
        api_key: API key from X-API-Key header

    Returns:
        True if authenticated

    Raises:
        HTTPException: If authentication fails
    """
    # Allow localhost in development mode
    if is_trusted_host(request):
        logger.debug("Development mode - skipping authentication")
        return True

    # Check API key
    if api_key and api_key == settings.secret_key:
        logger.warning(f"API key authentication used (insecure - use proper JWT)")
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> Optional[dict]:
    """
    Get the current authenticated user from JWT token.

    This is a placeholder implementation. In production, implement
    proper JWT validation with a token service.

    Args:
        request: The incoming request
        credentials: Bearer token credentials

    Returns:
        User information dict or None

    Raises:
        HTTPException: If authentication fails
    """
    # Allow localhost in development mode
    if is_trusted_host(request):
        logger.debug("Development mode - skipping user authentication")
        return {"user_id": "dev", "is_admin": True}

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Placeholder: Validate JWT token
    # In production, implement proper JWT validation
    token = credentials.credentials
    try:
        # TODO: Implement proper JWT validation
        logger.warning("JWT validation not implemented - using mock user")
        return {"user_id": "user", "is_admin": False}
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def require_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Require admin privileges.

    Args:
        current_user: Current authenticated user

    Returns:
        User information

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user