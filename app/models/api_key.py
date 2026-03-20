"""ApiKey model for storing API key hashes and metadata."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Index
from sqlalchemy.orm import relationship

from .base import Base


class ApiKey(Base):
    """ApiKey model for authentication and tracking API usage."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    wake_history = relationship(
        "WakeHistory", back_populates="api_key", cascade="all, delete-orphan"
    )
    webhook_deliveries = relationship(
        "WebhookDelivery", back_populates="api_key", cascade="all, delete-orphan"
    )
