"""WakeHistory model for tracking WoL wake attempts."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from .base import Base


class WakeHistory(Base):
    """WakeHistory model for logging wake attempts and their outcomes."""

    __tablename__ = "wake_history"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    mac_address = Column(String(17), nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    response_time_ms = Column(Float, nullable=True)

    # Relationships
    device = relationship("Device", back_populates="wake_history")
    api_key = relationship("ApiKey", back_populates="wake_history")

    def __repr__(self) -> str:
        """Return string representation of the wake history entry."""
        return f"<WakeHistory(id={self.id}, mac={self.mac_address}, success={self.success})>"
