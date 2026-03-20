"""Main FastAPI application with all features integrated."""
import os
import re
import secrets
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Security,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import configuration and core modules
from app.core.config import settings
from app.db.database import Base, get_db
from app.logging_config import configure_logging
from app.middleware import LoggingMiddleware

# Import auth and rate limiting
from app.auth.api_key import get_api_key
from app.rate_limit import limiter, RateLimitExceeded, _rate_limit_exceeded_handler

# Import models and schemas
from app.models import Device, ApiKey, WebhookConfig
from app.schemas import (
    DeviceCreate,
    DeviceUpdate,
    Device as DeviceSchema,
    ApiKeyCreate,
    ApiKey as ApiKeySchema,
    WebhookConfigCreate,
    WebhookConfigUpdate,
    WebhookConfig as WebhookConfigSchema,
    DeviceStatus,
)

# Import CRUD operations
from app.crud import (
    get_device,
    get_devices,
    create_device,
    update_device,
    delete_device,
    create_api_key,
    get_api_keys,
    deactivate_api_key,
    reactivate_api_key,
    create_wake_history,
    get_webhook_configs,
    create_webhook_config,
    update_webhook_config,
    delete_webhook_config,
    get_webhook_config,
    create_webhook_delivery,
)

# Import feature modules
from app.status.checker import check_device_status
from app.events.broadcast import broadcast_manager
from app.mqtt.client import mqtt_client
from app.webhooks.worker import start_webhook_worker

# Import WoL library
from wakeonlan import send_magic_packet

# Configure logging as early as possible
configure_logging()


# Lifespan for startup/shutdown operations
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events."""
    # Startup
    # Start MQTT client if enabled
    if settings.FEATURE_MQTT_ENABLED:
        await mqtt_client.connect()
    # Start webhook retry worker
    await start_webhook_worker()
    yield
    # Shutdown
    await mqtt_client.disconnect()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Wake-on-LAN API with device management, webhooks, MQTT, and SSE",
    version="2.0.0",
    lifespan=lifespan,
)

# Add request/response logging middleware
app.add_middleware(LoggingMiddleware)

# Configure rate limiting
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.state.limiter = limiter


# === Public endpoints ===

@app.get("/")
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def root():
    """Welcome and health check endpoint."""
    return {"status": 200, "message": f"Welcome to {settings.APP_NAME}!"}


@app.get("/health")
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}


# === Device management endpoints (require auth) ===

@app.post("/devices", response_model=DeviceSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def create_device_endpoint(
    device_in: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Create a new device."""
    # Check for duplicate MAC
    result = await db.execute(
        select(Device).where(Device.mac_address == device_in.mac_address)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device with this MAC address already exists",
        )
    device = await create_device(db, **device_in.model_dump())
    return device


@app.get("/devices", response_model=List[DeviceSchema])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_devices(
    enabled: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """List all devices with optional filters."""
    devices = await get_devices(db, enabled=enabled, limit=limit, offset=offset)
    return devices


@app.get("/devices/{device_id}", response_model=DeviceSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_device_endpoint(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Get a specific device by ID."""
    device = await get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.put("/devices/{device_id}", response_model=DeviceSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def update_device_endpoint(
    device_id: int,
    device_in: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Update a device."""
    device = await update_device(
        db, device_id, **device_in.model_dump(exclude_unset=True)
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.delete("/devices/{device_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def delete_device_endpoint(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Delete a device."""
    success = await delete_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deleted"}


@app.get("/devices/{device_id}/status", response_model=DeviceStatus)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_device_status(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Check if a device is online using ping/ARP."""
    device = await get_device(db, device_id)
    if not device or not device.ip_address:
        raise HTTPException(
            status_code=404,
            detail="Device not found or no IP address configured",
        )
    result = await check_device_status(device.ip_address)
    return result


# === API Key management endpoints ===

@app.post("/auth/keys", response_model=ApiKeySchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def create_api_key_endpoint(
    key_in: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Create a new API key.

    Returns the plaintext key once in the response. Store it securely.
    """
    # Generate a random API key
    plain_key = secrets.token_hex(16)
    api_key_obj = await create_api_key(
        db,
        key_name=key_in.key_name,
        plain_key=plain_key,
        is_active=key_in.is_active,
    )
    # Return the plain key along with the schema (excluding it from schema fields)
    response = ApiKeySchema.model_validate(api_key_obj)
    return {"api_key": plain_key, **response.model_dump()}


@app.get("/auth/keys", response_model=List[ApiKeySchema])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """List all API keys (metadata only, no plaintext keys)."""
    keys = await get_api_keys(db)
    return keys


@app.post("/auth/keys/{key_id}/deactivate")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def deactivate_api_key_endpoint(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Deactivate an API key."""
    api_key_obj = await deactivate_api_key(db, key_id)
    if not api_key_obj:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key deactivated"}


@app.post("/auth/keys/{key_id}/reactivate")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def reactivate_api_key_endpoint(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Reactivate an API key."""
    api_key_obj = await reactivate_api_key(db, key_id)
    if not api_key_obj:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key reactivated"}


# === Webhook configuration endpoints ===

@app.post("/webhooks", response_model=WebhookConfigSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def create_webhook_endpoint(
    webhook_in: WebhookConfigCreate,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Create a new webhook configuration."""
    webhook = await create_webhook_config(db, **webhook_in.model_dump())
    return webhook


@app.get("/webhooks", response_model=List[WebhookConfigSchema])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_webhooks(
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """List all webhook configurations."""
    webhooks = await get_webhook_configs(db, is_active=is_active)
    return webhooks


@app.get("/webhooks/{webhook_id}", response_model=WebhookConfigSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_webhook_endpoint(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Get a specific webhook configuration."""
    webhook = await get_webhook_config(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@app.put("/webhooks/{webhook_id}", response_model=WebhookConfigSchema)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def update_webhook_endpoint(
    webhook_id: int,
    webhook_in: WebhookConfigUpdate,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Update a webhook configuration."""
    webhook = await update_webhook_config(
        db, webhook_id, **webhook_in.model_dump(exclude_unset=True)
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@app.delete("/webhooks/{webhook_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def delete_webhook_endpoint(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Delete a webhook configuration."""
    success = await delete_webhook_config(db, webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted"}


# === Server-Sent Events (SSE) endpoint ===

@app.get("/events")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def events(
    request: Request,
    event_types: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Stream server-sent events for real-time updates.

    Query parameter `event_types` can be a comma-separated list to filter events.
    """
    # Parse event type filters
    filters: set[str] = set()
    if event_types:
        filters = {et.strip() for et in event_types.split(",") if et.strip()}

    # Register client with broadcast manager
    client_id = await broadcast_manager.connect()

    # Return streaming response
    return StreamingResponse(
        broadcast_manager.generate(client_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# === Wake-on-LAN endpoints (require auth) ===

@app.get("/wake")
@limiter.limit(settings.RATE_LIMIT_WAKE)
async def wake_default(
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Wake the default device configured via DEFAULT_MAC."""
    if not settings.DEFAULT_MAC:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No default MAC address configured",
        )
    mac = settings.DEFAULT_MAC
    device = None
    result = await db.execute(select(Device).where(Device.mac_address == mac))
    device = result.scalar_one_or_none()

    # Send magic packet
    try:
        send_magic_packet(mac)
        success = True
        error_msg = None
    except Exception as e:
        success = False
        error_msg = str(e)

    # Log history
    await create_wake_history(
        db,
        mac_address=mac,
        success=success,
        device_id=device.id if device else None,
        api_key_id=api_key["api_key_id"],
        error_message=error_msg,
    )

    # Handle success/failure events
    if success:
        payload = {
            "mac_address": mac,
            "device_name": device.name if device else None,
            "triggered_by": api_key["key_name"],
        }
        # Trigger webhooks
        webhooks = await get_webhook_configs(db, is_active=True)
        for wh in webhooks:
            if any(et in wh.event_types for et in ["wol_sent", "wol_success"]):
                await create_webhook_delivery(
                    db,
                    webhook_id=wh.id,
                    event_type="wol_sent",
                    payload=payload,
                    api_key_id=api_key["api_key_id"],
                    device_id=device.id if device else None,
                )
        # Publish MQTT
        if settings.FEATURE_MQTT_ENABLED:
            device_name = device.name if device else mac
            await mqtt_client.publish_wake_event(
                device_name=device_name,
                mac_address=mac,
                success=True,
                triggered_by=api_key["key_name"],
            )
        # Broadcast SSE
        await broadcast_manager.broadcast(
            "wake",
            {
                "mac_address": mac,
                "device_name": device.name if device else None,
                "success": True,
                "triggered_by": api_key["key_name"],
            },
        )
        return {"message": f"Wake packet sent to {mac}"}
    else:
        await broadcast_manager.broadcast(
            "wake",
            {
                "mac_address": mac,
                "device_name": device.name if device else None,
                "success": False,
                "error": error_msg,
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to send WoL packet: {error_msg}"
        )


@app.get("/wake/{mac_address}")
@limiter.limit(settings.RATE_LIMIT_WAKE)
async def wake_specific(
    mac_address: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: dict = Depends(get_api_key),
):
    """Wake a specific device by MAC address."""
    # Normalize MAC address
    mac = mac_address.strip().upper().replace("-", ":")
    pattern = r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$"
    if not re.match(pattern, mac):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MAC address format. Use AA:BB:CC:DD:EE:FF",
        )

    device = None
    result = await db.execute(select(Device).where(Device.mac_address == mac))
    device = result.scalar_one_or_none()

    try:
        send_magic_packet(mac)
        success = True
        error_msg = None
    except Exception as e:
        success = False
        error_msg = str(e)

    await create_wake_history(
        db,
        mac_address=mac,
        success=success,
        device_id=device.id if device else None,
        api_key_id=api_key["api_key_id"],
        error_message=error_msg,
    )

    if success:
        payload = {
            "mac_address": mac,
            "device_name": device.name if device else None,
            "triggered_by": api_key["key_name"],
        }
        webhooks = await get_webhook_configs(db, is_active=True)
        for wh in webhooks:
            if any(et in wh.event_types for et in ["wol_sent", "wol_success"]):
                await create_webhook_delivery(
                    db,
                    webhook_id=wh.id,
                    event_type="wol_sent",
                    payload=payload,
                    api_key_id=api_key["api_key_id"],
                    device_id=device.id if device else None,
                )
        if settings.FEATURE_MQTT_ENABLED:
            device_name = device.name if device else mac
            await mqtt_client.publish_wake_event(
                device_name=device_name,
                mac_address=mac,
                success=True,
                triggered_by=api_key["key_name"],
            )
        await broadcast_manager.broadcast(
            "wake",
            {
                "mac_address": mac,
                "device_name": device.name if device else None,
                "success": True,
                "triggered_by": api_key["key_name"],
            },
        )
        return {"message": f"Wake packet sent to {mac}"}
    else:
        await broadcast_manager.broadcast(
            "wake",
            {
                "mac_address": mac,
                "device_name": device.name if device else None,
                "success": False,
                "error": error_msg,
            },
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to send WoL packet: {error_msg}"
        )
