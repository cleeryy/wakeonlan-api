"""Application configuration using Pydantic Settings."""
import os
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Wake-on-LAN API"
    DEBUG: bool = False

    # Database
    DB_URL: str = Field(
        default="sqlite+aiosqlite:///./wakeonlan.db",
        description="Database connection URL (async SQLAlchemy format)",
    )

    # Default MAC (for backward compatibility)
    DEFAULT_MAC: Optional[str] = Field(
        default=None, description="Default MAC address for /wake endpoint"
    )

    # API Key (initial admin key auto-creation)
    API_KEY_INITIAL: Optional[str] = Field(
        default=None, description="Initial API key to create on first startup"
    )
    API_KEY_NAME: str = Field(
        default="Initial Admin Key", description="Name for initial API key"
    )

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = Field(
        default="60/minute", description="Default rate limit (e.g., '60/minute')"
    )
    RATE_LIMIT_PER_KEY: bool = Field(
        default=True, description="Apply rate limiting per API key if available"
    )
    RATE_LIMIT_WAKE: str = Field(
        default="10/minute", description="Rate limit for /wake endpoints"
    )
    RATE_LIMIT_HEALTH: str = Field(
        default="60/minute", description="Rate limit for /health endpoint"
    )

    # Webhook
    WEBHOOK_MAX_RETRIES: int = Field(default=5, ge=0, le=10)
    WEBHOOK_RETRY_BASE_DELAY: float = Field(default=1.0, ge=0.1, le=60.0)
    WEBHOOK_RETRY_MAX_DELAY: float = Field(default=60.0, ge=1.0, le=3600.0)
    WEBHOOK_TIMEOUT: float = Field(default=10.0, ge=1.0, le=60.0)
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, ge=1, le=20)
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: float = Field(
        default=60.0, ge=10.0, le=3600.0
    )  # seconds

    # MQTT
    MQTT_BROKER: Optional[str] = Field(
        default=None, description="MQTT broker host (e.g., 'localhost')"
    )
    MQTT_PORT: int = Field(default=1883, ge=1, le=65535)
    MQTT_USER: Optional[str] = Field(default=None, description="MQTT username")
    MQTT_PASSWORD: Optional[str] = Field(default=None, description="MQTT password")
    MQTT_TOPIC_PREFIX: str = Field(
        default="wol", description="MQTT topic prefix (e.g., 'wol')"
    )
    MQTT_KEEPALIVE: int = Field(default=60, ge=10, le=300)
    MQTT_RECONNECT_DELAY: int = Field(default=5, ge=1, le=60)

    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FORMAT: str = Field(default="json", pattern=r"^(json|console)$")
    LOG_DEST: str = Field(default="stdout", pattern=r"^(stdout|file)$")
    LOG_FILE: Optional[str] = Field(
        default=None, description="Log file path if LOG_DEST=file"
    )

    # Status Check
    STATUS_PING_TIMEOUT: float = Field(
        default=1.0, ge=0.1, le=5.0, description="Ping timeout in seconds"
    )
    STATUS_PING_COUNT: int = Field(
        default=1, ge=1, le=10, description="Number of ping attempts"
    )
    STATUS_ARP_ENABLED: bool = Field(
        default=True, description="Enable ARP scan fallback (Linux only)"
    )
    STATUS_CACHE_TTL: int = Field(
        default=5, ge=0, le=60, description="Cache TTL for status checks in seconds"
    )

    # SSE
    SSE_HEARTBEAT_INTERVAL: int = Field(
        default=15, ge=5, le=60, description="Heartbeat interval in seconds"
    )
    SSE_MAX_QUEUE_SIZE: int = Field(
        default=1000, ge=100, le=10000, description="Max events queued per client"
    )

    # Feature flags
    FEATURE_WEBHOOKS_ENABLED: bool = Field(default=True)
    FEATURE_MQTT_ENABLED: bool = Field(default=False)  # Disabled by default
    FEATURE_SSE_ENABLED: bool = Field(default=True)

    @field_validator("DEFAULT_MAC")
    @classmethod
    def normalize_mac(cls, v: Optional[str]) -> Optional[str]:
        """Normalize MAC address to uppercase with colons."""
        if v is None:
            return None
        v = v.strip().upper().replace("-", ":")
        # Validate format
        import re

        pattern = r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid MAC address format: {v}")
        return v


# Global settings instance
settings = Settings()
