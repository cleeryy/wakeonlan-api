"""Pydantic schemas for WakeHistory model."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import BaseConfig


class WakeHistoryCreate(BaseModel):
    """Schema for creating a new wake history entry."""

    device_id: Optional[int] = None
    mac_address: str = Field(..., min_length=17, max_length=17)
    api_key_id: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None

    model_config = BaseConfig

    @field_validator("mac_address")
    @classmethod
    def validate_mac_address(cls, v: str) -> str:
        """Validate MAC address format (AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)."""
        import re

        pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        if not re.match(pattern, v):
            raise ValueError("Invalid MAC address format. Use AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF")
        v = v.upper().replace("-", ":")
        return v


class WakeHistoryUpdate(BaseModel):
    """Schema for updating a wake history entry (rarely used, mostly read-only)."""

    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None

    model_config = BaseConfig


class WakeHistory(BaseModel):
    """Schema for wake history response (read)."""

    id: int
    device_id: Optional[int] = None
    mac_address: str
    api_key_id: Optional[int] = None
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None

    # Read-only relationship IDs (if needed for expanded responses)
    # These would be populated via joins in the query
    device: Optional[dict] = None  # Could be nested device read schema
    api_key: Optional[dict] = None  # Could be nested api_key read schema

    model_config = BaseConfig


__all__ = ["WakeHistoryCreate", "WakeHistoryUpdate", "WakeHistory"]
