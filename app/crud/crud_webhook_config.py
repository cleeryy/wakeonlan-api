"""CRUD operations for WebhookConfig model."""
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import async_session_factory
from ..models.webhook_config import WebhookConfig


async def get_webhook_config(db: AsyncSession, config_id: int) -> Optional[WebhookConfig]:
    """Get a webhook configuration by ID.

    Args:
        db: AsyncSession instance
        config_id: Webhook config ID

    Returns:
        WebhookConfig instance or None if not found
    """
    result = await db.execute(select(WebhookConfig).where(WebhookConfig.id == config_id))
    return result.scalar_one_or_none()


async def create_webhook_config(
    db: AsyncSession,
    *,
    name: str,
    url: str,
    event_types: list[str],
    headers: Optional[dict] = None,
    is_active: bool = True,
    max_retries: int = 5,
    retry_base_delay: float = 1.0,
    retry_max_delay: float = 60.0,
    timeout: float = 10.0,
) -> WebhookConfig:
    """Create a new webhook configuration.

    Args:
        db: AsyncSession instance
        name: Configuration name
        url: Webhook URL
        event_types: List of event types to trigger this webhook
        headers: Optional custom headers
        is_active: Whether the config is active
        max_retries: Maximum retry attempts
        retry_base_delay: Base delay for exponential backoff (seconds)
        retry_max_delay: Maximum delay between retries (seconds)
        timeout: Request timeout (seconds)

    Returns:
        Created WebhookConfig instance
    """
    config = WebhookConfig(
        name=name,
        url=url,
        event_types=event_types,
        headers=headers or {},
        is_active=is_active,
        max_retries=max_retries,
        retry_base_delay=retry_base_delay,
        retry_max_delay=retry_max_delay,
        timeout=timeout,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def update_webhook_config(
    db: AsyncSession, config_id: int, **kwargs
) -> Optional[WebhookConfig]:
    """Update a webhook configuration (PATCH style - only provided fields).

    Args:
        db: AsyncSession instance
        config_id: Webhook config ID
        **kwargs: Fields to update

    Returns:
        Updated WebhookConfig instance or None if not found
    """
    config = await get_webhook_config(db, config_id)
    if not config:
        return None

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return config


async def delete_webhook_config(db: AsyncSession, config_id: int) -> bool:
    """Delete a webhook configuration by ID.

    Args:
        db: AsyncSession instance
        config_id: Webhook config ID

    Returns:
        True if deleted, False if not found
    """
    config = await get_webhook_config(db, config_id)
    if not config:
        return False

    await db.delete(config)
    await db.commit()
    return True


async def get_webhook_configs(
    db: AsyncSession,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[WebhookConfig]:
    """Get all webhook configurations with optional filters.

    Args:
        db: AsyncSession instance
        is_active: Optional filter by active status
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of WebhookConfig instances
    """
    stmt = select(WebhookConfig)

    if is_active is not None:
        stmt = stmt.where(WebhookConfig.is_active == is_active)

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())
