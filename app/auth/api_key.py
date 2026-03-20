"""API Key authentication for FastAPI."""
from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import verify_key
from app.db.session import get_db

# Define the API key header name (X-API-Key)
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    api_key: str = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dependency that validates API key and returns API key info.

    Args:
        api_key: API key from X-API-Key header
        db: Database session

    Returns:
        Dictionary with api_key_id, key_name, is_active

    Raises:
        HTTPException: 401 if API key is missing, invalid, or inactive
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Hash the provided key to look up in database
    # We use a simple SHA256 hash for lookup (not bcrypt) because we need to query by hash
    # Actually, bcrypt is not suitable for direct hash lookup because it includes salt and is expensive.
    # Better approach: store a separate lookup hash (SHA256) or use constant-time compare on all keys.
    # For simplicity and security, we'll fetch all active keys and compare using verify_key.
    # This is less efficient but with proper indexing and small number of keys it's fine.
    # Alternatively, we could store a SHA256 hash column for lookup.
    # Let's use the approach: fetch by key_hash? But we only have plain key.
    # We can't query by bcrypt hash because it's salted and different each time.
    # So we need to either:
    # 1. Fetch all active API keys and verify each with verify_key (inefficient for many keys)
    # 2. Add a separate column key_sha256 for lookup.
    #
    # Given this is a small personal project, option 1 is acceptable.
    # But we can optimize by caching active keys in memory? Not ideal.
    #
    # Better: modify the ApiKey model to include key_sha256 (unique) and use that for lookup.
    # However, the model already has key_hash (bcrypt). We can add a new column.
    # But to avoid schema changes now, we'll do the fetch-all approach with a limit.
    #
    # Actually, the crud has get_api_key_by_hash which expects the hash. That's for looking up by hash.
    # That function is used for internal lookups where we already have the hash.
    # For authentication from plain key, we need a different approach.
    #
    # Let's implement: fetch all active API keys (maybe limit to 100) and verify.
    # This is O(n) but n is small (few keys). Acceptable.
    #
    # Alternatively, we could compute bcrypt hash and try to query by hash? No, bcrypt hash includes salt, so same password gives different hash each time. So we can't query directly.
    # So we must fetch and compare.
    #
    # We'll fetch all active API keys. In production with many keys, we'd add a SHA256 column.
    from app.models import ApiKey

    result = await db.execute(
        select(ApiKey).where(ApiKey.is_active == True).limit(1000)
    )
    api_keys = result.scalars().all()

    for key_record in api_keys:
        if verify_key(plain_key=api_key, hashed=key_record.key_hash):
            # Update last_used_at
            from app.crud import get_api_key_by_id
            # We'll update last_used_at asynchronously but not wait for it
            # We can do a fire-and-forget update
            try:
                key_record.last_used_at = datetime.utcnow()  # type: ignore
                await db.commit()
            except Exception:
                # Don't fail auth if update fails
                pass
            return {
                "api_key_id": key_record.id,
                "key_name": key_record.key_name,
                "is_active": key_record.is_active,
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


# Optional: Simple API key dependency that just returns the key string (for rate limiting)
async def get_api_key_str(
    api_key: str = Security(API_KEY_HEADER),
) -> str:
    """Extract API key string without validation (for rate limiting key function)."""
    if not api_key:
        return ""
    return api_key
