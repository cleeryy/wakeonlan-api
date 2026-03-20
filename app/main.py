import os
import re
from typing import Union, List

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header, status
from wakeonlan import send_magic_packet

load_dotenv()

app = FastAPI()

DEFAULT_MAC = os.getenv("DEFAULT_MAC") or ""
API_KEY = os.getenv("API_KEY", "").strip()

if not DEFAULT_MAC:
    raise RuntimeError("DEFAULT_MAC environment variable is required")

MAC_ADDRESS_REGEX = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')


def validate_mac_address(mac: str) -> bool:
    return bool(MAC_ADDRESS_REGEX.fullmatch(mac.strip()))


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
    x_api_key: str = Header(..., alias="X-API-Key")
) -> str:
    """
    Dependency that verifies the provided API key.
    
    Raises HTTPException if key is missing or invalid.
    """
    allowed_keys = get_api_keys()
    
    # If API_KEY is not configured, allow all (backward compatibility)
    if not allowed_keys:
        return x_api_key
    
    if x_api_key not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Invalid or missing API key"}
        )
    return x_api_key


@app.get("/")
async def root():
    return {"status": 200, "message": "Welcome to the Wake-on-LAN API!"}


@app.get("/wake")
async def wake_pc(api_key: str = Depends(verify_api_key)):
    try:
        send_magic_packet(DEFAULT_MAC)
        return {"message": "Wake-on-LAN packet sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to send Wake-on-LAN packet: {str(e)}"}
        )


@app.get("/wake/{wake_addr}")
async def read_wake(
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
