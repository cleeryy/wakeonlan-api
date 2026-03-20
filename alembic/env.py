"""Alembic migration environment configuration for async SQLAlchemy."""
import asyncio
import sys
from logging.config import fileConfig

from alembic import context

# Add the project root to the Python path
sys.path.insert(0, '.')

# Alembic configuration
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import Base to get metadata
from app.db.database import Base

# Import all models to ensure they are registered with Base.metadata
# These imports are not used directly but are required for metadata population
from app.models import (  # noqa: F401
    device,
    api_key,
    wake_history,
    webhook_config,
    webhook_delivery,
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # Required for SQLite autogenerate
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using async engine."""
    from sqlalchemy.ext.asyncio import create_async_engine

    # Get database URL from config
    url = config.get_main_option("sqlalchemy.url")

    # Create async engine
    connectable = create_async_engine(
        url,
        echo=config.get_main_option("sqlalchemy.echo") == "true",
        pool_pre_ping=True,
        future=True,
    )

    async with connectable.connect() as connection:
        # Configure the context with the connection
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Required for SQLite autogenerate
        )

        # Run migrations
        async with context.begin_transaction():
            await connection.run_sync(context.run_migrations)


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run async migrations
    asyncio.run(run_migrations_online())
