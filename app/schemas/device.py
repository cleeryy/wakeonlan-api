"""Pydantic schemas for Device model."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, HttpUrl

from .base import BaseConfig


class DeviceCreate(BaseModel):
    """Schema for creating a new device."""

    name: str = Field(..., min_length=1, max_length=100)
    mac_address: str = Field(..., min_length=17, max_length=17)
    ip_address: Optional[str] = Field(None, max_length=45)
    port: int = Field(9, ge=0, le=65535)
    enabled: bool = True

    model_config = BaseConfig

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        """Validate MAC address format (AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)."""
        import re

        pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        if not re.match(pattern, v):
            raise ValueError("Invalid MAC address format. Use AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF")
        # Normalize to uppercase with colons
        v = v.upper().replace("-", ":")
        return v

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        """Basic IP address validation (IPv4 or IPv6)."""
        if v is None:
            return None
        # Simple validation - could be enhanced with ipaddress module
        import ipaddress

        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError("Invalid IP address format")


class DeviceUpdate(BaseModel):
    """Schema for updating an existing device."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    mac_address: Optional[str] = Field(None, min_length=17, max_length=17)
    ip_address: Optional[str] = Field(None, max_length=45)
    port: Optional[int] = Field(None, ge=0, le=65535)
    enabled: Optional[bool] = None

    model_config = BaseConfig

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate MAC address format (AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)."""
        if v is None:
            return None
        import re

        pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        if not re.match(pattern, v):
            raise ValueError("Invalid MAC address format. Use AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF")
        v = v.upper().replace("-", ":")
        return v

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        """Basic IP address validation (IPv4 or IPv6)."""
        if v is None:
            return None
        import ipaddress

        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError("Invalid IP address format")


class Device(BaseModel):
    """Schema for device response (read)."""

    id: int
    name: str
    mac_address: str
    ip_address: Optional[str] = None
    port: int
    enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = BaseConfig


class DeviceStatus(BaseModel):
    """Schema for device status check response."""

    online: bool
    latency_ms: Optional[float] = None
    method: str
    open_ports: Optional[list[int]] = None

    model_config = BaseConfig


__all__ = ["DeviceCreate", "DeviceUpdate", "Device", "DeviceStatus"]
