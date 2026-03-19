"""WebhookConfig model for storing webhook configurations."""
import json
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator

from .base import Base


class JSONEncodedDict(TypeDecorator):
    """JSON-encoded dictionary type that stores as TEXT in SQLite and JSON in PostgreSQL."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convert Python object to JSON string for database storage."""
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """Convert JSON string from database to Python object."""
        if value is None:
            return None
        return json.loads(value)


class WebhookConfig(Base):
    """WebhookConfig model for configuring outgoing webhooks."""

    __tablename__ = "webhook_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    event_types = Column(JSONEncodedDict, nullable=False, default=list)
    headers = Column(JSONEncodedDict, nullable=False, default=dict)
    secret = Column(String, nullable=True)  # HMAC secret for signing webhook payloads
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    max_retries = Column(Integer, default=5, nullable=False)
    retry_base_delay = Column(Float, default=1.0, nullable=False)
    retry_max_delay = Column(Float, default=60.0, nullable=False)
    timeout = Column(Float, default=10.0, nullable=False)

    # Relationships
    deliveries = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return string representation of the webhook config."""
        return f"<WebhookConfig(id={self.id}, name={self.name}, url={self.url})>"
