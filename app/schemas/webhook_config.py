"""Pydantic schemas for WebhookConfig model."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from .base import BaseConfig

EventType = Literal["wol_sent", "wol_success", "wol_failure"]


class WebhookConfigCreate(BaseModel):
    """Schema for creating a new webhook configuration."""

    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    event_types: list[EventType] = Field(..., min_length=1)
    headers: dict = Field(default_factory=dict)
    secret: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: bool = True
    max_retries: int = Field(5, ge=0, le=10)
    retry_base_delay: float = Field(1.0, ge=0.1, le=300.0)
    retry_max_delay: float = Field(60.0, ge=1.0, le=600.0)
    timeout: float = Field(10.0, ge=1.0, le=60.0)

    model_config = BaseConfig

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v: list[EventType]) -> list[EventType]:
        """Validate that event_types are unique and valid."""
        if not v:
            raise ValueError("At least one event type must be specified")
        if len(set(v)) != len(v):
            raise ValueError("Event types must be unique")
        return v


class WebhookConfigUpdate(BaseModel):
    """Schema for updating an existing webhook configuration."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[HttpUrl] = None
    event_types: Optional[list[EventType]] = None
    headers: Optional[dict] = None
    secret: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_base_delay: Optional[float] = Field(None, ge=0.1, le=300.0)
    retry_max_delay: Optional[float] = Field(None, ge=1.0, le=600.0)
    timeout: Optional[float] = Field(None, ge=1.0, le=60.0)

    model_config = BaseConfig

    @field_validator("event_types")
    @classmethod
    def validate_event_types(cls, v: Optional[list[EventType]]) -> Optional[list[EventType]]:
        """Validate that event_types are unique and valid."""
        if v is None:
            return None
        if not v:
            raise ValueError("At least one event type must be specified")
        if len(set(v)) != len(v):
            raise ValueError("Event types must be unique")
        return v


class WebhookConfig(BaseModel):
    """Schema for webhook configuration response (read)."""

    id: int
    name: str
    url: str
    event_types: list[EventType]
    headers: dict
    is_active: bool
    created_at: datetime
    max_retries: int
    retry_base_delay: float
    retry_max_delay: float
    timeout: float
    secret: Optional[str] = Field(None, exclude=True)  # Excluded from response

    model_config = BaseConfig


__all__ = ["WebhookConfigCreate", "WebhookConfigUpdate", "WebhookConfig", "EventType"]
