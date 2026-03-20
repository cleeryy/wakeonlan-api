"""CRUD operations for WebhookDelivery model."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import async_session_factory
from ..models.webhook_delivery import WebhookDelivery, DeliveryStatus


async def create_webhook_delivery(
    db: AsyncSession,
    *,
    webhook_id: int,
    event_type: str,
    payload: Optional[dict] = None,
    status: DeliveryStatus = DeliveryStatus.STATUS_PENDING,
    api_key_id: Optional[int] = None,
    device_id: Optional[int] = None,
) -> WebhookDelivery:
    """Create a new webhook delivery entry.

    Args:
        db: AsyncSession instance
        webhook_id: WebhookConfig ID
        event_type: Type of event (e.g., 'wake_sent', 'device_online')
        payload: Event payload (will be JSON-encoded)
        status: Delivery status (pending, success, failure, circuit_open)
        api_key_id: Optional API key that triggered the event
        device_id: Optional device ID related to the event

    Returns:
        Created WebhookDelivery instance
    """
    delivery = WebhookDelivery(
        webhook_id=webhook_id,
        event_type=event_type,
        payload=payload,
        status=status,
        api_key_id=api_key_id,
        device_id=device_id,
    )
    db.add(delivery)
    await db.commit()
    await db.refresh(delivery)
    return delivery


async def get_delivery(db: AsyncSession, delivery_id: int) -> Optional[WebhookDelivery]:
    """Get a webhook delivery by ID.

    Args:
        db: AsyncSession instance
        delivery_id: Delivery ID

    Returns:
        WebhookDelivery instance or None if not found
    """
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    return result.scalar_one_or_none()


async def update_delivery(
    db: AsyncSession,
    delivery_id: int,
    **kwargs,
) -> Optional[WebhookDelivery]:
    """Update a webhook delivery entry.

    Args:
        db: AsyncSession instance
        delivery_id: Delivery ID
        **kwargs: Fields to update (status, attempt_count, last_attempt_at, last_error, payload)

    Returns:
        Updated WebhookDelivery instance or None if not found
    """
    delivery = await get_delivery(db, delivery_id)
    if not delivery:
        return None

    for key, value in kwargs.items():
        if hasattr(delivery, key):
            setattr(delivery, key, value)

    await db.commit()
    await db.refresh(delivery)
    return delivery


async def increment_attempt(
    db: AsyncSession,
    delivery_id: int,
    error: Optional[str] = None,
) -> Optional[WebhookDelivery]:
    """Increment attempt count and set last_attempt_at and optional error.

    Args:
        db: AsyncSession instance
        delivery_id: Delivery ID
        error: Optional error message if attempt failed

    Returns:
        Updated WebhookDelivery instance or None if not found
    """
    delivery = await get_delivery(db, delivery_id)
    if not delivery:
        return None

    delivery.attempt_count += 1
    delivery.last_attempt_at = datetime.utcnow()
    if error:
        delivery.last_error = error[:1000]  # Truncate long errors

    await db.commit()
    await db.refresh(delivery)
    return delivery


async def mark_success(db: AsyncSession, delivery_id: int) -> Optional[WebhookDelivery]:
    """Mark a delivery as successful.

    Args:
        db: AsyncSession instance
        delivery_id: Delivery ID

    Returns:
        Updated WebhookDelivery instance or None if not found
    """
    return await update_delivery(
        db,
        delivery_id,
        status=DeliveryStatus.STATUS_SUCCESS,
        last_error=None,
    )


async def mark_failure(
    db: AsyncSession, delivery_id: int, error: str
) -> Optional[WebhookDelivery]:
    """Mark a delivery as failed.

    Args:
        db: AsyncSession instance
        delivery_id: Delivery ID
        error: Error message

    Returns:
        Updated WebhookDelivery instance or None if not found
    """
    return await update_delivery(
        db,
        delivery_id,
        status=DeliveryStatus.STATUS_FAILURE,
        last_error=error[:1000],
    )


async def mark_circuit_open(db: AsyncSession, delivery_id: int) -> Optional[WebhookDelivery]:
    """Mark a delivery as circuit open (temporary disable due to failures).

    Args:
        db: AsyncSession instance
        delivery_id: Delivery ID

    Returns:
        Updated WebhookDelivery instance or None if not found
    """
    return await update_delivery(
        db,
        delivery_id,
        status=DeliveryStatus.STATUS_CIRCUIT_OPEN,
    )


async def delete_delivery(db: AsyncSession, delivery_id: int) -> bool:
    """Delete a delivery entry by ID.

    Args:
        db: AsyncSession instance
        delivery_id: Delivery ID

    Returns:
        True if deleted, False if not found
    """
    delivery = await get_delivery(db, delivery_id)
    if not delivery:
        return False

    await db.delete(delivery)
    await db.commit()
    return True


async def get_deliveries(
    db: AsyncSession,
    webhook_id: Optional[int] = None,
    status: Optional[DeliveryStatus] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[WebhookDelivery]:
    """Get deliveries with optional filters.

    Args:
        db: AsyncSession instance
        webhook_id: Filter by webhook config ID
        status: Filter by delivery status
        event_type: Filter by event type
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of WebhookDelivery instances ordered by created_at descending
    """
    from sqlalchemy import select, and_, desc

    stmt = select(WebhookDelivery).order_by(desc(WebhookDelivery.created_at))

    conditions = []
    if webhook_id is not None:
        conditions.append(WebhookDelivery.webhook_id == webhook_id)
    if status is not None:
        conditions.append(WebhookDelivery.status == status)
    if event_type is not None:
        conditions.append(WebhookDelivery.event_type == event_type)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_pending_deliveries(
    db: AsyncSession, limit: int = 100, older_than: Optional[datetime] = None
) -> List[WebhookDelivery]:
    """Get pending deliveries that need to be sent/retried.

    Args:
        db: AsyncSession instance
        limit: Maximum number of results
        older_than: Only return deliveries created before this time (for locking)

    Returns:
        List of pending WebhookDelivery instances ordered by created_at ascending
    """
    from sqlalchemy import select, asc

    stmt = (
        select(WebhookDelivery)
        .where(WebhookDelivery.status == DeliveryStatus.STATUS_PENDING)
        .order_by(asc(WebhookDelivery.created_at))
        .limit(limit)
    )

    if older_than is not None:
        stmt = stmt.where(WebhookDelivery.created_at <= older_than)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_statistics(
    db: AsyncSession,
    webhook_id: Optional[int] = None,
    hours: int = 24,
) -> dict:
    """Get delivery statistics for monitoring.

    Args:
        db: AsyncSession instance
        webhook_id: Optional webhook ID to filter
        hours: Lookback period in hours

    Returns:
        Dictionary with counts per status and total
    """
    from datetime import timedelta
    from sqlalchemy import select, func, and_

    start_date = datetime.utcnow() - timedelta(hours=hours)

    stmt = select(
        WebhookDelivery.status,
        func.count(WebhookDelivery.id).label("count"),
    ).where(WebhookDelivery.created_at >= start_date)

    if webhook_id is not None:
        stmt = stmt.where(WebhookDelivery.webhook_id == webhook_id)

    stmt = stmt.group_by(WebhookDelivery.status)

    result = await db.execute(stmt)
    rows = result.all()

    stats = {status: 0 for status in DeliveryStatus.__args__}  # type: ignore
    total = 0
    for status, count in rows:
        stats[status] = count
        total += count

    stats["total"] = total
    return stats


# Export all CRUD functions for convenience
__all__ = [
    "create_webhook_delivery",
    "get_delivery",
    "update_delivery",
    "increment_attempt",
    "mark_success",
    "mark_failure",
    "mark_circuit_open",
    "delete_delivery",
    "get_deliveries",
    "get_pending_deliveries",
    "get_statistics",
]
