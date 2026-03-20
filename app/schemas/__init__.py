"""Pydantic schemas for the application."""
from .base import BaseConfig
from .device import DeviceCreate, DeviceUpdate, Device, DeviceStatus
from .api_key import ApiKeyCreate, ApiKeyUpdate, ApiKey
from .wake_history import WakeHistoryCreate, WakeHistoryUpdate, WakeHistory
from .webhook_config import (
    WebhookConfigCreate,
    WebhookConfigUpdate,
    WebhookConfig,
    EventType,
)
from .webhook_delivery import (
    WebhookDeliveryCreate,
    WebhookDeliveryUpdate,
    WebhookDelivery,
    DeliveryStatus,
)

__all__ = [
    "BaseConfig",
    "DeviceCreate",
    "DeviceUpdate",
    "Device",
    "DeviceStatus",
    "ApiKeyCreate",
    "ApiKeyUpdate",
    "ApiKey",
    "WakeHistoryCreate",
    "WakeHistoryUpdate",
    "WakeHistory",
    "WebhookConfigCreate",
    "WebhookConfigUpdate",
    "WebhookConfig",
    "EventType",
    "WebhookDeliveryCreate",
    "WebhookDeliveryUpdate",
    "WebhookDelivery",
    "DeliveryStatus",
]
