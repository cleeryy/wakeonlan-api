"""CRUD operations package."""
from .crud_api_key import (
    create_api_key,
    deactivate_api_key,
    get_api_key_by_hash,
    get_api_key_by_id,
    get_api_keys,
    reactivate_api_key,
    verify_key,
)
from .crud_device import (
    create_device,
    delete_device,
    get_device,
    get_devices,
    update_device,
)
from .crud_wake_history import (
    create_wake_history,
    get_history,
    get_history_by_api_key,
    get_history_by_device,
    get_recent_failures,
)
from .crud_webhook_config import (
    create_webhook_config,
    delete_webhook_config,
    get_webhook_config,
    get_webhook_configs,
    update_webhook_config,
)
from .crud_webhook_delivery import (
    create_webhook_delivery,
    delete_delivery,
    get_deliveries,
    get_delivery,
    get_pending_deliveries,
    get_statistics,
    increment_attempt,
    mark_circuit_open,
    mark_failure,
    mark_success,
    update_delivery,
)

__all__ = [
    # ApiKey
    "create_api_key",
    "get_api_key_by_id",
    "get_api_key_by_hash",
    "get_api_keys",
    "deactivate_api_key",
    "reactivate_api_key",
    "verify_key",
    # Device
    "get_device",
    "get_devices",
    "create_device",
    "update_device",
    "delete_device",
    # WakeHistory
    "create_wake_history",
    "get_history",
    "get_history_by_device",
    "get_history_by_api_key",
    "get_recent_failures",
    # WebhookConfig
    "get_webhook_config",
    "create_webhook_config",
    "update_webhook_config",
    "delete_webhook_config",
    "get_webhook_configs",
    # WebhookDelivery
    "create_webhook_delivery",
    "get_delivery",
    "update_delivery",
    "increment_attempt",
    "mark_success",
    "mark_failure",
    "mark_circuit_open",
    "delete_delivery",
    "get_deliveries",
    "get_pending_deliveries",
    "get_statistics",
]
