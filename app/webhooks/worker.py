"""Webhook delivery retry worker."""
import asyncio
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_pending_deliveries,
    get_webhook_config,
    increment_attempt,
    mark_failure,
    mark_success,
)
from app.db.session import async_session_factory
from app.models.webhook_delivery import WebhookDelivery
from app.webhooks.sender import attempt_delivery
from app.core.config import settings


# How often the worker polls for pending deliveries
POLL_INTERVAL = 5.0  # seconds


async def process_delivery(db: AsyncSession, delivery: WebhookDelivery) -> None:
    """Process a single pending delivery.

    Args:
        db: AsyncSession instance
        delivery: WebhookDelivery ORM instance
    """
    # Fetch associated webhook config
    webhook = await get_webhook_config(db, delivery.webhook_id)
    if not webhook or not webhook.is_active:
        # Webhook config missing or inactive, mark as failure
        await mark_failure(
            db, delivery.id, "Webhook config not found or inactive"
        )
        return

    # Check if we've exceeded max retries
    if delivery.attempt_count >= webhook.max_retries:
        await mark_failure(
            db, delivery.id, f"Max retries ({webhook.max_retries}) exceeded"
        )
        return

    # Compute exponential backoff delay
    if delivery.attempt_count > 0 and delivery.last_attempt_at:
        delay = min(
            webhook.retry_base_delay * (2 ** (delivery.attempt_count - 1)),
            webhook.retry_max_delay,
        )
        now = datetime.utcnow()
        if delivery.last_attempt_at + timedelta(seconds=delay) > now:
            # Not ready to retry yet; skip until next cycle
            return

    # Increment attempt counter before sending
    delivery = await increment_attempt(db, delivery.id)
    if not delivery:
        # Delivery disappeared?
        return

    # Attempt to send
    success = await attempt_delivery(
        db=db,
        delivery_id=delivery.id,
        webhook_url=webhook.url,
        event_type=delivery.event_type,
        payload=delivery.payload or {},
        secret=webhook.secret,
        custom_headers=webhook.headers,
        timeout=webhook.timeout,
    )

    if success:
        # Already marked success by attempt_delivery
        pass
    else:
        # If failure and we've now exceeded max retries, mark as failure
        if delivery.attempt_count >= webhook.max_retries:
            await mark_failure(
                db, delivery.id, f"Max retries ({webhook.max_retries}) exceeded after attempt {delivery.attempt_count}"
            )
        # else: keep pending for next retry (already incremented, status remains pending)


async def worker_loop() -> None:
    """Main worker loop that continuously processes pending deliveries."""
    while True:
        try:
            async with async_session_factory() as db:
                # Get a batch of pending deliveries
                stmt = select(WebhookDelivery).where(
                    WebhookDelivery.status == "pending"
                ).order_by(WebhookDelivery.created_at).limit(100)
                result = await db.execute(stmt)
                deliveries: List[WebhookDelivery] = list(result.scalars().all())

                for delivery in deliveries:
                    try:
                        await process_delivery(db, delivery)
                        # Commit after each delivery to persist status changes
                        await db.commit()
                    except Exception as e:
                        await db.rollback()
                        # Log error but continue
                        from app.logging_config import get_application_logger
                        logger = get_application_logger()
                        logger.error(
                            "webhook_delivery_error",
                            delivery_id=delivery.id,
                            error=str(e),
                        )
                        # Mark as failure after max attempts?
                        try:
                            await mark_failure(
                                db, delivery.id, f"Worker error: {str(e)[:200]}"
                            )
                            await db.commit()
                        except Exception:
                            pass

                await db.close()

        except Exception as e:
            from app.logging_config import get_application_logger
            logger = get_application_logger()
            logger.error("webhook_worker_loop_error", error=str(e))

        # Wait before next poll
        await asyncio.sleep(POLL_INTERVAL)


async def start_webhook_worker() -> None:
    """Start the webhook retry worker background task.

    This should be called during application startup (e.g., in a lifespan context).
    """
    from app.logging_config import get_application_logger
    logger = get_application_logger()
    logger.info("Starting webhook retry worker")
    # Run the worker loop as a background task
    asyncio.create_task(worker_loop())
