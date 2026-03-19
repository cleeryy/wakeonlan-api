"""Rate limiting configuration using slowapi."""
import hashlib
from typing import Callable

from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings


def get_rate_limit_key(request: Request) -> str:
    """Generate a rate limit key based on API key (if present and enabled) or IP address.

    If RATE_LIMIT_PER_KEY is True and an X-API-Key header is present, the key is
    a SHA256 hash truncated to 16 characters to avoid exposing the full key.

    Otherwise, falls back to the remote IP address.

    Args:
        request: FastAPI request object

    Returns:
        String key for rate limiting
    """
    if settings.RATE_LIMIT_PER_KEY:
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            # Use truncated SHA256 hash as key to avoid storing full key in memory
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"api_key:{key_hash}"

    # Fallback to IP-based limiting
    return get_remote_address(request)


# Create the limiter instance with custom key function
limiter = Limiter(key_func=get_rate_limit_key)

__all__ = [
    "limiter",
    "RateLimitExceeded",
    "_rate_limit_exceeded_handler",
    "get_rate_limit_key",
]
