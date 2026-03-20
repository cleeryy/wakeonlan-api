"""WebhookDelivery model for tracking webhook delivery attempts."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Index, Enum as SQLAEnum
from sqlalchemy.orm import relationship

from .base import Base


class WebhookDelivery(Base):
    """WebhookDelivery model for tracking outgoing webhook deliveries."""

    __tablename__ = "webhook_deliveries"

    # Define status enum values
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILURE = "failure"
    STATUS_CIRCUIT_OPEN = "circuit_open"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhook_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    payload = Column(Text, nullable=True)
    status = Column(
        SQLAEnum(
            STATUS_PENDING,
            STATUS_SUCCESS,
            STATUS_FAILURE,
            STATUS_CIRCUIT_OPEN,
            name="webhook_delivery_status",
        ),
        default=STATUS_PENDING,
        nullable=False,
    )
    attempt_count = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Foreign keys (optional, for tracking which device/api_key triggered)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    webhook = relationship("WebhookConfig", back_populates="deliveries")
    api_key = relationship("ApiKey", back_populates="webhook_deliveries")
    device = relationship("Device", backref="webhook_deliveries")

    # Composite index for dead-letter queue queries
    __table_args__ = (
        Index("ix_webhook_delivery_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        """Return string representation of the webhook delivery."""
        return f"<WebhookDelivery(id={self.id}, status={self.status}, event_type={self.event_type})>"
