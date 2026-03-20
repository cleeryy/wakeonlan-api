"""CRUD operations for Device model."""
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import async_session_factory
from ..models.device import Device


async def get_device(db: AsyncSession, device_id: int) -> Optional[Device]:
    """Get a device by ID.

    Args:
        db: AsyncSession instance
        device_id: Device ID

    Returns:
        Device instance or None if not found
    """
    result = await db.execute(select(Device).where(Device.id == device_id))
    return result.scalar_one_or_none()


async def create_device(db: AsyncSession, **kwargs) -> Device:
    """Create a new device.

    Args:
        db: AsyncSession instance
        **kwargs: Device fields (name, mac_address, ip_address, port, enabled)

    Returns:
        Created Device instance
    """
    device = Device(**kwargs)
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


async def update_device(db: AsyncSession, device_id: int, **kwargs) -> Optional[Device]:
    """Update a device by ID.

    Args:
        db: AsyncSession instance
        device_id: Device ID
        **kwargs: Fields to update

    Returns:
        Updated Device instance or None if not found
    """
    device = await get_device(db, device_id)
    if not device:
        return None

    for key, value in kwargs.items():
        if hasattr(device, key):
            setattr(device, key, value)

    await db.commit()
    await db.refresh(device)
    return device


async def delete_device(db: AsyncSession, device_id: int) -> bool:
    """Delete a device by ID.

    Args:
        db: AsyncSession instance
        device_id: Device ID

    Returns:
        True if deleted, False if not found
    """
    device = await get_device(db, device_id)
    if not device:
        return False

    await db.delete(device)
    await db.commit()
    return True


async def get_devices(
    db: AsyncSession,
    enabled: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Device]:
    """Get all devices with optional filters.

    Args:
        db: AsyncSession instance
        enabled: Optional filter by enabled status
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of Device instances
    """
    stmt = select(Device)

    if enabled is not None:
        stmt = stmt.where(Device.enabled == enabled)

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().all())
