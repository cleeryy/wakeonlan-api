"""Device model for storing network device information."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Index
from sqlalchemy.orm import relationship

from .base import Base


class Device(Base):
    """Device model representing a network device that can be woken via WoL."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    ip_address = Column(String, nullable=True, index=True)
    port = Column(Integer, default=9, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    wake_history = relationship(
        "WakeHistory", back_populates="device", cascade="all, delete-orphan"
    )

    def __str__(self) -> str:
        """Return string representation of the device."""
        return self.name
