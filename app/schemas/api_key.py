"""Pydantic schemas for ApiKey model."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseConfig


class ApiKeyCreate(BaseModel):
    """Schema for creating a new API key."""

    key_name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True

    model_config = BaseConfig


class ApiKeyUpdate(BaseModel):
    """Schema for updating an existing API key."""

    key_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None

    model_config = BaseConfig


class ApiKey(BaseModel):
    """Schema for API key response (read)."""

    id: int
    key_hash: str
    key_name: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = BaseConfig


__all__ = ["ApiKeyCreate", "ApiKeyUpdate", "ApiKey"]
