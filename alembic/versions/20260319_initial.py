"""Initial migration - create all tables.

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-03-19 15:00:00

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables and indexes."""
    # Create devices table
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("mac_address", sa.String(17), unique=True, nullable=False, index=True),
        sa.Column("ip_address", sa.String, nullable=True, index=True),
        sa.Column("port", sa.Integer, default=9, nullable=False),
        sa.Column("enabled", sa.Boolean, default=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, default=datetime.utcnow, nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        ),
    )

    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("key_hash", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("key_name", sa.String, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, default=datetime.utcnow, nullable=False
        ),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
    )

    # Create wake_history table
    op.create_table(
        "wake_history",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "device_id",
            sa.Integer,
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("mac_address", sa.String(17), nullable=False, index=True),
        sa.Column(
            "api_key_id",
            sa.Integer,
            sa.ForeignKey("api_keys.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "timestamp", sa.DateTime, default=datetime.utcnow, nullable=False, index=True
        ),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("response_time_ms", sa.Float, nullable=True),
    )
    # Index for wake_history: (device_id, timestamp) maybe? Already have timestamp index.
    op.create_index(
        "ix_wake_history_device_timestamp",
        "wake_history",
        ["device_id", "timestamp"],
    )

    # Create webhook_configs table
    op.create_table(
        "webhook_configs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("url", sa.String, nullable=False),
        sa.Column(
            "event_types",
            sqlite.TEXT,  # JSON encoded for SQLite; Alembic will handle dialect differences
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "headers",
            sqlite.TEXT,
            nullable=False,
            server_default="{}",
        ),
        sa.Column("secret", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column(
            "created_at", sa.DateTime, default=datetime.utcnow, nullable=False
        ),
        sa.Column("max_retries", sa.Integer, default=5, nullable=False),
        sa.Column("retry_base_delay", sa.Float, default=1.0, nullable=False),
        sa.Column("retry_max_delay", sa.Float, default=60.0, nullable=False),
        sa.Column("timeout", sa.Float, default=10.0, nullable=False),
    )

    # Create webhook_deliveries table
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "webhook_id",
            sa.Integer,
            sa.ForeignKey("webhook_configs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("event_type", sa.String(50), nullable=False, index=True),
        sa.Column("payload", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "success",
                "failure",
                "circuit_open",
                name="webhook_delivery_status",
            ),
            default="pending",
            nullable=False,
        ),
        sa.Column("attempt_count", sa.Integer, default=0, nullable=False),
        sa.Column("last_attempt_at", sa.DateTime, nullable=True),
        sa.Column("last_error", sa.Text, nullable=True),
        sa.Column(
            "created_at", sa.DateTime, default=datetime.utcnow, nullable=False, index=True
        ),
        sa.Column(
            "api_key_id",
            sa.Integer,
            sa.ForeignKey("api_keys.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "device_id",
            sa.Integer,
            sa.ForeignKey("devices.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    # Composite index for dead-letter queue queries
    op.create_index(
        "ix_webhook_delivery_status_created",
        "webhook_deliveries",
        ["status", "created_at"],
    )

    # Create foreign keys explicitly if not auto-created by column definitions
    # (SQLAlchemy's ForeignKey in column definitions should create them automatically)
    # But we can add additional constraints if needed.
    pass


def downgrade() -> None:
    """Drop all tables in reverse order."""
    op.drop_index("ix_webhook_delivery_status_created", table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_configs")
    op.drop_index("ix_wake_history_device_timestamp", table_name="wake_history")
    op.drop_table("wake_history")
    op.drop_table("api_keys")
    op.drop_table("devices")
    # Drop enum type if created (PostgreSQL)
    # For SQLite, enum is stored as VARCHAR, no need to drop type
    try:
        op.execute("DROP TYPE webhook_delivery_status")
    except Exception:
        pass
