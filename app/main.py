import os
import re
from typing import Union, List

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header, status, Request, Body, Body
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse
from wakeonlan import send_magic_packet
from .devices import DeviceRegistry
from .utils import validate_mac_address

load_dotenv()

app = FastAPI()

# Initialize device registry
DEVICES_FILE = os.getenv("DEVICES_FILE", "devices.json")
device_registry = DeviceRegistry(DEVICES_FILE)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_STRING = f"{RATE_LIMIT_REQUESTS}/{RATE_LIMIT_WINDOW_SECONDS}s"

# Broadcast IP configuration (optional, defaults to wakeonlan library default)
BROADCAST_IP = os.getenv("BROADCAST_IP", "")

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
async def wake_device_by_name(request: Request, name: str):
    """Wake a device by its registered name."""
    mac = device_registry.get(name)
    if not mac:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Device '{name}' not found in registry"}
        )
    
    try:
        if BROADCAST_IP:
            send_magic_packet(mac, ip_address=BROADCAST_IP)
        else:
            send_magic_packet(mac)
        return {
            "message": f"Wake-on-LAN packet sent successfully to {name} ({mac})!"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to send Wake-on-LAN packet to {name}: {str(e)}"}
        )


@app.get("/wake")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def wake_pc(request: Request, api_key: str = Depends(verify_api_key)):
    try:
        if BROADCAST_IP:
            send_magic_packet(DEFAULT_MAC, ip_address=BROADCAST_IP)
        else:
            send_magic_packet(DEFAULT_MAC)
        return {"message": "Wake-on-LAN packet sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to send Wake-on-LAN packet: {str(e)}"}
        )


@app.get("/wake/{wake_addr}")
@limiter.limit(f"{RATE_LIMIT_REQUESTS}/minute")
async def read_wake(
    request: Request,
    wake_addr: str,
    api_key: str = Depends(verify_api_key),
    q: Union[str, None] = None
):
    # Validate MAC address format
    if not validate_mac_address(wake_addr):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid MAC address format: '{wake_addr}'. Must be XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX"}
        )
    try:
        if BROADCAST_IP:
            send_magic_packet(wake_addr, ip_address=BROADCAST_IP)
        else:
            send_magic_packet(wake_addr)
        return {
            "message": f"Wake-on-LAN packet sent successfully to {wake_addr} device!"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": f"Failed to send Wake-on-LAN packet to {wake_addr} device: {str(e)}"
            }
        )
