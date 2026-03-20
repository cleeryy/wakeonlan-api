"""Webhook sender with HMAC signature support."""
import hashlib
import hmac
import json
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    mark_failure,
    mark_success,
    increment_attempt,
)
from app.models.webhook_delivery import DeliveryStatus
from app.core.config import settings


async def attempt_delivery(
    db: AsyncSession,
    delivery_id: int,
    webhook_url: str,
    event_type: str,
    payload: Dict[str, Any],
    secret: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    timeout: float = 10.0,
) -> bool:
    """Attempt to deliver a webhook, updating delivery status in the database.

    This function sends an HTTP POST with optional HMAC signature and updates
    the WebhookDelivery record based on the outcome.

    Args:
        db: AsyncSession instance
        delivery_id: WebhookDelivery ID
        webhook_url: Target webhook URL
        event_type: Event type string
        payload: Event payload (will be JSON-encoded)
        secret: Optional HMAC secret for signing
        custom_headers: Optional additional headers from webhook config
        timeout: Request timeout in seconds

    Returns:
        True if delivery succeeded (2xx), False otherwise
    """
    headers = {"Content-Type": "application/json"}
    if custom_headers:
        headers.update(custom_headers)

    # Build the body with event metadata
    body = {
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    body_json = json.dumps(body, separators=(",", ":"))

    # Sign payload if secret provided
    if secret:
        signature = hmac.new(
            secret.encode("utf-8"),
            body_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                webhook_url,
                content=body_json,
                headers=headers,
                timeout=timeout,
            )
            success = 200 <= response.status_code < 300

            if success:
                await mark_success(db, delivery_id)
                return True
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                await mark_failure(db, delivery_id, error_msg)
                return False

        except Exception as e:
            error_msg = str(e)[:200]
            await mark_failure(db, delivery_id, error_msg)
            return False
