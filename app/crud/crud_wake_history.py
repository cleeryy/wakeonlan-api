"""CRUD operations for WakeHistory model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import async_session_factory
from ..models.wake_history import WakeHistory


async def create_wake_history(
    db: AsyncSession,
    *,
    mac_address: str,
    success: bool,
    device_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    error_message: Optional[str] = None,
    response_time_ms: Optional[float] = None,
) -> WakeHistory:
    """Create a wake history entry.

    Args:
        db: AsyncSession instance
        mac_address: MAC address that was targeted
        success: Whether the wake attempt succeeded
        device_id: Optional device ID
        api_key_id: Optional API key ID
        error_message: Optional error message if failed
        response_time_ms: Optional response time in milliseconds

    Returns:
        Created WakeHistory instance
    """
    history = WakeHistory(
        device_id=device_id,
        mac_address=mac_address,
        api_key_id=api_key_id,
        success=success,
        error_message=error_message,
        response_time_ms=response_time_ms,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


async def get_history(
    db: AsyncSession,
    device_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    success: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[WakeHistory]:
    """Get wake history with optional filters.

    Args:
        db: AsyncSession instance
        device_id: Filter by device ID
        api_key_id: Filter by API key ID
        start_date: Filter entries on or after this date
        end_date: Filter entries on or before this date
        success: Filter by success status
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of WakeHistory instances ordered by timestamp descending
    """
    from sqlalchemy import select, and_, desc

    stmt = select(WakeHistory).order_by(desc(WakeHistory.timestamp))

    conditions = []

    if device_id is not None:
        conditions.append(WakeHistory.device_id == device_id)

    if api_key_id is not None:
        conditions.append(WakeHistory.api_key_id == api_key_id)

    if start_date is not None:
        conditions.append(WakeHistory.timestamp >= start_date)

    if end_date is not None:
        conditions.append(WakeHistory.timestamp <= end_date)

    if success is not None:
        conditions.append(WakeHistory.success == success)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_history_by_device(
    db: AsyncSession, device_id: int, limit: int = 100, offset: int = 0
) -> list[WakeHistory]:
    """Get wake history for a specific device.

    Args:
        db: AsyncSession instance
        device_id: Device ID
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of WakeHistory instances for the device
    """
    return await get_history(db=db, device_id=device_id, limit=limit, offset=offset)


async def get_history_by_api_key(
    db: AsyncSession, api_key_id: int, limit: int = 100, offset: int = 0
) -> list[WakeHistory]:
    """Get wake history for a specific API key.

    Args:
        db: AsyncSession instance
        api_key_id: API key ID
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of WakeHistory instances for the API key
    """
    return await get_history(db=db, api_key_id=api_key_id, limit=limit, offset=offset)


async def get_recent_failures(
    db: AsyncSession, hours: int = 24, limit: int = 50
) -> list[WakeHistory]:
    """Get recent failed wake attempts.

    Args:
        db: AsyncSession instance
        hours: Number of hours to look back
        limit: Maximum number of results

    Returns:
        List of failed WakeHistory instances
    """
    from datetime import timedelta

    start_date = datetime.utcnow() - timedelta(hours=hours)

    return await get_history(
        db=db,
        start_date=start_date,
        success=False,
        limit=limit,
    )
