"""CRUD operations for ApiKey model."""
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import async_session_factory
from ..models.api_key import ApiKey

# Password hashing context for API keys
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_key(plain_key: str, hashed: str) -> bool:
    """Verify a plain API key against its hash.

    Args:
        plain_key: Plaintext API key
        hashed: Hashed API key from database

    Returns:
        True if key matches, False otherwise
    """
    return pwd_context.verify(plain_key, hashed)


async def get_api_key_by_id(db: AsyncSession, api_key_id: int) -> Optional[ApiKey]:
    """Get an API key by ID.

    Args:
        db: AsyncSession instance
        api_key_id: API key ID

    Returns:
        ApiKey instance or None if not found
    """
    result = await db.execute(select(ApiKey).where(ApiKey.id == api_key_id))
    return result.scalar_one_or_none()


async def get_api_key_by_hash(db: AsyncSession, key_hash: str) -> Optional[ApiKey]:
    """Get an API key by its hash.

    Args:
        db: AsyncSession instance
        key_hash: Hashed API key

    Returns:
        ApiKey instance or None if not found
    """
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    return result.scalar_one_or_none()


async def create_api_key(
    db: AsyncSession, key_name: str, plain_key: str, is_active: bool = True
) -> ApiKey:
    """Create a new API key with hashed storage.

    Args:
        db: AsyncSession instance
        key_name: Human-readable name for the key
        plain_key: Plaintext API key (will be hashed)
        is_active: Whether the key is active

    Returns:
        Created ApiKey instance with hashed key
    """
    key_hash = pwd_context.hash(plain_key)

    api_key = ApiKey(
        key_name=key_name,
        key_hash=key_hash,
        is_active=is_active,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def deactivate_api_key(db: AsyncSession, api_key_id: int) -> Optional[ApiKey]:
    """Deactivate an API key.

    Args:
        db: AsyncSession instance
        api_key_id: API key ID

    Returns:
        Updated ApiKey instance or None if not found
    """
    api_key = await get_api_key_by_id(db, api_key_id)
    if not api_key:
        return None

    api_key.is_active = False
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def reactivate_api_key(db: AsyncSession, api_key_id: int) -> Optional[ApiKey]:
    """Reactivate an API key.

    Args:
        db: AsyncSession instance
        api_key_id: API key ID

    Returns:
        Updated ApiKey instance or None if not found
    """
    api_key = await get_api_key_by_id(db, api_key_id)
    if not api_key:
        return None

    api_key.is_active = True
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def get_api_keys(
    db: AsyncSession,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ApiKey]:
    """Get all API keys with optional filters.

    Args:
        db: AsyncSession instance
        is_active: Optional filter by active status
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of ApiKey instances
    """
    from sqlalchemy import select

    stmt = select(ApiKey)

    if is_active is not None:
        stmt = stmt.where(ApiKey.is_active == is_active)

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())
