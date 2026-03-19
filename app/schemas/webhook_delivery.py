"""Pydantic schemas for WebhookDelivery model."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import BaseConfig

DeliveryStatus = Literal["pending", "success", "failure", "circuit_open"]


class WebhookDeliveryCreate(BaseModel):
    """Schema for creating a new webhook delivery entry."""

    webhook_id: int
    event_type: str = Field(..., min_length=1, max_length=50)
    payload: Optional[dict] = None
    status: DeliveryStatus = "pending"
    api_key_id: Optional[int] = None
    device_id: Optional[int] = None

    model_config = BaseConfig


class WebhookDeliveryUpdate(BaseModel):
    """Schema for updating a webhook delivery entry."""

    status: Optional[DeliveryStatus] = None
    attempt_count: Optional[int] = Field(None, ge=0)
    last_attempt_at: Optional[datetime] = None
    last_error: Optional[str] = None
    payload: Optional[dict] = None

    model_config = BaseConfig


class WebhookDelivery(BaseModel):
    """Schema for webhook delivery response (read)."""

    id: int
    webhook_id: int
    event_type: str
    payload: Optional[dict] = None
    status: DeliveryStatus
    attempt_count: int
    last_attempt_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    api_key_id: Optional[int] = None
    device_id: Optional[int] = None

    # Read-only relationship IDs (if needed for expanded responses)
    webhook: Optional[dict] = None  # Could be nested webhook config read schema
    api_key: Optional[dict] = None
    device: Optional[dict] = None

    model_config = BaseConfig


__all__ = ["WebhookDeliveryCreate", "WebhookDeliveryUpdate", "WebhookDelivery", "DeliveryStatus"]
