import os
import re
import logging
from typing import Union, List, Optional
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header, status, Request, Body, Response, BackgroundTasks
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse
from wakeonlan import send_magic_packet
import httpx
from datetime import datetime
from .devices import DeviceRegistry
from .utils import validate_mac_address
from .logging_config import setup_logging
from .middleware import LoggingMiddleware
from .models import BatchWakeRequest
from . import metrics

# Configure structured logging
setup_logging()
logger = logging.getLogger("wol")

load_dotenv()

# Metrics enabled flag (can be disabled via environment)
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"

# Conditionally import metrics module
if METRICS_ENABLED:
    from . import metrics

app = FastAPI()

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Initialize device registry
DEVICES_FILE = os.getenv("DEVICES_FILE", "devices.json")
device_registry = DeviceRegistry(DEVICES_FILE)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_STRING = f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW_SECONDS}s"

# API version
API_VERSION = os.getenv("API_VERSION", "1.0")

# Broadcast IP configuration (optional, defaults to wakeonlan library default)
BROADCAST_IP = os.getenv("BROADCAST_IP", "")

# WoL Retry configuration
WOL_RETRIES = int(os.getenv("WOL_RETRIES", "3"))
WOL_RETRY_DELAY = float(os.getenv("WOL_RETRY_DELAY", "0.5"))  # seconds

# Webhook configuration
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_TIMEOUT = float(os.getenv("WEBHOOK_TIMEOUT", "5.0"))

import asyncio

async def send_wol_with_retry(mac: str, broadcast_ip: Union[str, None] = None, endpoint: Union[str, None] = None):
    """Send WoL packet with retry logic."""
    last_exception = None
    for attempt in range(WOL_RETRIES):
        try:
            if METRICS_ENABLED:
                if endpoint:
                    # Increment retry counter (excluding first attempt)
                    if attempt > 0:
                        metrics.wol_retries_total.labels(endpoint=endpoint).inc()
                    # Track duration with histogram
                    timer_context = metrics.wol_duration_seconds.labels(endpoint=endpoint).time()
                else:
                    timer_context = metrics.wol_duration_seconds.labels(endpoint="unknown").time()
                
                with timer_context:
                    if broadcast_ip:
                        send_magic_packet(mac, ip_address=broadcast_ip)
                    else:
                        send_magic_packet(mac)
            else:
                if broadcast_ip:
                    send_magic_packet(mac, ip_address=broadcast_ip)
                else:
                    send_magic_packet(mac)
            return
        except Exception as e:
            last_exception = e
            if attempt < WOL_RETRIES - 1:
                await asyncio.sleep(WOL_RETRY_DELAY)
            else:
                raise last_exception


async def send_webhook_notification(
    mac: str,
    endpoint: str,
    success: bool,
    error: Optional[str] = None
):
    """Send webhook notification if WEBHOOK_URL is configured."""
    if not WEBHOOK_URL:
        return
    
    payload = {
        "event": "wol",
        "mac": mac,
        "endpoint": endpoint,
        "success": success,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if error:
        payload["error"] = error
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(WEBHOOK_URL, json=payload, timeout=WEBHOOK_TIMEOUT)
    except Exception as e:
        logger.error("Failed to send webhook", extra={
            "webhook_url": WEBHOOK_URL,
            "error": str(e)
        })

# Initialize limiter with remote address as key
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Add SlowAPI middleware
app.add_middleware(SlowAPIMiddleware)

# Custom rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS} seconds."}
    )

DEFAULT_MAC = os.getenv("DEFAULT_MAC") or ""
API_KEY = os.getenv("API_KEY", "").strip()

if not DEFAULT_MAC:
    raise RuntimeError("DEFAULT_MAC environment variable is required")

def validate_mac_address(mac: str) -> bool:
    mac = mac.strip()
    # Check colon-separated format (XX:XX:XX:XX:XX:XX)
    if re.fullmatch(r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}', mac):
        return True
    # Check hyphen-separated format (XX-XX-XX-XX-XX-XX)
    if re.fullmatch(r'([0-9A-Fa-f]{2}-){5}[0-9A-Fa-f]{2}', mac):
        return True
    return False


if not validate_mac_address(DEFAULT_MAC):
    raise RuntimeError(
        f"Invalid DEFAULT_MAC format: '{DEFAULT_MAC}'. "
        "Must be in format XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX"
    )


def get_api_keys() -> List[str]:
    """Parse API_KEY environment variable into a list of allowed keys."""
    if not API_KEY:
        return []
    # Support comma-separated list of keys
    return [key.strip() for key in API_KEY.split(",") if key.strip()]


async def verify_api_key(
    x_api_key: Union[str, None] = Header(None, alias="X-API-Key")
) -> str:
    """
    Dependency that verifies the provided API key.
    
    Raises HTTPException if key is missing or invalid.
    """
    allowed_keys = get_api_keys()
    
    # If API_KEY is not configured, allow all (backward compatibility)
    if not allowed_keys:
        return x_api_key or ""
    
    if x_api_key is None or x_api_key not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Invalid or missing API key"}
        )
    return x_api_key


@app.get("/")
async def root():
    return {"status": 200, "message": "Welcome to the Wake-on-LAN API!"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and Docker HEALTHCHECK."""
    return {
        "status": "healthy",
        "service": "wakeonlan-api",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
    }


@app.get("/version")
async def version():
    """API version endpoint."""
    return {"name": "wakeonlan-api", "version": API_VERSION}


@app.get("/devices", dependencies=[Depends(verify_api_key)])
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def list_devices(request: Request):
    """List all registered devices."""
    return device_registry.list_devices()


@app.post("/devices", dependencies=[Depends(verify_api_key)])
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def add_device(
    request: Request,
    name: str = Body(..., embed=True),
    mac: str = Body(..., embed=True)
):
    """
    Add a new device.
    
    - **name**: Device name (alphanumeric, dashes, underscores)
    - **mac**: MAC address (XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)
    """
    if not validate_mac_address(mac):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid MAC address format: '{mac}'"}
        )
    
    if device_registry.exists(name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": f"Device '{name}' already exists"}
        )
    
    success = device_registry.add(name, mac)
    if success:
        return {"message": f"Device '{name}' added successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to add device"}
        )


@app.delete("/devices/{name}", dependencies=[Depends(verify_api_key)])
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def delete_device(request: Request, name: str):
    """Delete a device by name."""
    if not device_registry.exists(name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Device '{name}' not found"}
        )
    
    success = device_registry.remove(name)
    if success:
        return {"message": f"Device '{name}' deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to delete device"}
        )


@app.get("/wake/device/{name}", dependencies=[Depends(verify_api_key)])
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def wake_device_by_name(
    request: Request,
    name: str,
    background_tasks: BackgroundTasks
):
    """Wake a device by its registered name."""
    endpoint = f"/wake/device/{name}"
    if METRICS_ENABLED:
        metrics.wol_requests_total.labels(endpoint=endpoint, status="started").inc()
    
    mac = device_registry.get(name)
    if not mac:
        if METRICS_ENABLED:
            metrics.wol_failure_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="failure").inc()
        # No WoL attempt; skip webhook
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Device '{name}' not found in registry"}
        )
    
    try:
        logger.info("WoL attempt", extra={
            "device_name": name,
            "mac": mac,
            "broadcast_ip": BROADCAST_IP or None,
            "endpoint": endpoint
        })
        await send_wol_with_retry(mac, broadcast_ip=BROADCAST_IP if BROADCAST_IP else None, endpoint=endpoint)
        logger.info("WoL success", extra={
            "device_name": name,
            "mac": mac,
            "broadcast_ip": BROADCAST_IP or None
        })
        if METRICS_ENABLED:
            metrics.wol_success_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="success").inc()
        # Schedule webhook notification (if enabled)
        if WEBHOOK_URL:
            background_tasks.add_task(
                send_webhook_notification,
                mac=mac,
                endpoint=endpoint,
                success=True
            )
        return {
            "message": f"Wake-on-LAN packet sent successfully to {name} ({mac})!"
        }
    except Exception as e:
        logger.error("WoL failure", extra={
            "device_name": name,
            "mac": mac,
            "broadcast_ip": BROADCAST_IP or None,
            "error": str(e)
        })
        if METRICS_ENABLED:
            metrics.wol_failure_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="failure").inc()
        # Schedule webhook notification (if enabled)
        if WEBHOOK_URL:
            background_tasks.add_task(
                send_webhook_notification,
                mac=mac,
                endpoint=endpoint,
                success=False,
                error=str(e)
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": {"error": f"Failed to send Wake-on-LAN packet to {name}: {str(e)}"}}
        )


@app.get("/status/{name}", dependencies=[Depends(verify_api_key)])
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def device_status(request: Request, name: str):
    """Get device registration status."""
    mac = device_registry.get(name)
    if not mac:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Device '{name}' not found in registry"}
        )
    return {"name": name, "mac": mac, "status": "registered"}


@app.get("/wake")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def wake_pc(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    endpoint = "/wake"
    if METRICS_ENABLED:
        metrics.wol_requests_total.labels(endpoint=endpoint, status="started").inc()
    try:
        logger.info("WoL attempt", extra={
            "mac": DEFAULT_MAC,
            "broadcast_ip": BROADCAST_IP or None,
            "endpoint": endpoint
        })
        await send_wol_with_retry(DEFAULT_MAC, broadcast_ip=BROADCAST_IP if BROADCAST_IP else None, endpoint=endpoint)
        logger.info("WoL success", extra={
            "mac": DEFAULT_MAC,
            "broadcast_ip": BROADCAST_IP or None
        })
        if METRICS_ENABLED:
            metrics.wol_success_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="success").inc()
        # Schedule webhook notification (if enabled)
        if WEBHOOK_URL:
            background_tasks.add_task(
                send_webhook_notification,
                mac=DEFAULT_MAC,
                endpoint=endpoint,
                success=True
            )
        return {"message": "Wake-on-LAN packet sent successfully"}
    except Exception as e:
        logger.error("WoL failure", extra={
            "mac": DEFAULT_MAC,
            "broadcast_ip": BROADCAST_IP or None,
            "error": str(e)
        })
        if METRICS_ENABLED:
            metrics.wol_failure_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="failure").inc()
        # Schedule webhook notification (if enabled)
        if WEBHOOK_URL:
            background_tasks.add_task(
                send_webhook_notification,
                mac=DEFAULT_MAC,
                endpoint=endpoint,
                success=False,
                error=str(e)
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": {"error": f"Failed to send Wake-on-LAN packet: {str(e)}"}}
        )


@app.post("/wake/batch")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def wake_batch(
    request: Request,
    data: BatchWakeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """
    Wake multiple devices at once.
    
    Body: { "mac_addresses": ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"] }
    """
    endpoint = "/wake/batch"
    if METRICS_ENABLED:
        metrics.wol_requests_total.labels(endpoint=endpoint, status="started").inc()
    
    mac_addresses = data.mac_addresses
    # Validate all MAC addresses
    invalid_macs = [mac for mac in mac_addresses if not validate_mac_address(mac)]
    if invalid_macs:
        if METRICS_ENABLED:
            metrics.wol_failure_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="failure").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid MAC address format(s): {invalid_macs}"}
        )
    
    results = []
    tasks = []
    for mac in mac_addresses:
        task = send_wol_with_retry(mac, broadcast_ip=BROADCAST_IP if BROADCAST_IP else None, endpoint=endpoint)
        tasks.append(task)
    
    # Run all WoL attempts in parallel
    for idx, mac in enumerate(mac_addresses):
        try:
            await tasks[idx]
            logger.info("WoL success (batch)", extra={
                "mac": mac,
                "broadcast_ip": BROADCAST_IP or None,
                "batch_size": len(mac_addresses)
            })
            if METRICS_ENABLED:
                metrics.wol_success_total.labels(endpoint=endpoint).inc()
            results.append({"mac": mac, "status": "success"})
            # Schedule webhook for success (if enabled)
            if WEBHOOK_URL:
                background_tasks.add_task(
                    send_webhook_notification,
                    mac=mac,
                    endpoint=endpoint,
                    success=True
                )
        except Exception as e:
            logger.error("WoL failure (batch)", extra={
                "mac": mac,
                "broadcast_ip": BROADCAST_IP or None,
                "error": str(e)
            })
            if METRICS_ENABLED:
                metrics.wol_failure_total.labels(endpoint=endpoint).inc()
            results.append({"mac": mac, "status": "error", "error": str(e)})
            # Schedule webhook for failure (if enabled)
            if WEBHOOK_URL:
                background_tasks.add_task(
                    send_webhook_notification,
                    mac=mac,
                    endpoint=endpoint,
                    success=False,
                    error=str(e)
                )
    
    if METRICS_ENABLED:
        metrics.wol_requests_total.labels(endpoint=endpoint, status="success").inc()
    return {"message": f"Batch wake completed for {len(mac_addresses)} devices", "results": results}


@app.get("/wake/{wake_addr}")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def read_wake(
    request: Request,
    wake_addr: str,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key),
    q: Union[str, None] = None
):
    endpoint = f"/wake/{wake_addr}"
    if METRICS_ENABLED:
        metrics.wol_requests_total.labels(endpoint=endpoint, status="started").inc()
    
    # Validate MAC address format
    if not validate_mac_address(wake_addr):
        if METRICS_ENABLED:
            metrics.wol_failure_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="failure").inc()
        # Schedule webhook? Probably not for validation failure; no WoL attempt. Skip.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid MAC address format: '{wake_addr}'. Must be XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX"}
        )
    try:
        logger.info("WoL attempt", extra={
            "mac": wake_addr,
            "broadcast_ip": BROADCAST_IP or None,
            "endpoint": endpoint
        })
        await send_wol_with_retry(wake_addr, broadcast_ip=BROADCAST_IP if BROADCAST_IP else None, endpoint=endpoint)
        logger.info("WoL success", extra={
            "mac": wake_addr,
            "broadcast_ip": BROADCAST_IP or None
        })
        if METRICS_ENABLED:
            metrics.wol_success_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="success").inc()
        # Schedule webhook notification (if enabled)
        if WEBHOOK_URL:
            background_tasks.add_task(
                send_webhook_notification,
                mac=wake_addr,
                endpoint=endpoint,
                success=True
            )
        return {
            "message": f"Wake-on-LAN packet sent successfully to {wake_addr} device!"
        }
    except Exception as e:
        logger.error("WoL failure", extra={
            "mac": wake_addr,
            "broadcast_ip": BROADCAST_IP or None,
            "error": str(e)
        })
        if METRICS_ENABLED:
            metrics.wol_failure_total.labels(endpoint=endpoint).inc()
            metrics.wol_requests_total.labels(endpoint=endpoint, status="failure").inc()
        # Schedule webhook notification (if enabled)
        if WEBHOOK_URL:
            background_tasks.add_task(
                send_webhook_notification,
                mac=wake_addr,
                endpoint=endpoint,
                success=False,
                error=str(e)
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": {"error": f"Failed to send Wake-on-LAN packet to {wake_addr} device: {str(e)}"}}
        )


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    if not METRICS_ENABLED:
        return Response(content="", status_code=status.HTTP_404_NOT_FOUND)
    return Response(content=metrics.get_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8")
