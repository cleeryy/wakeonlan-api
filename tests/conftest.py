"""Pytest configuration and fixtures for the Wake-on-LAN API project."""
import asyncio
import os
from typing import AsyncGenerator, Callable

import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app
from app.models import ApiKey, Device, WakeHistory, WebhookConfig, WebhookDelivery

# Test database URL (can be overridden with TEST_DB_URL env var)
TEST_DB_URL = os.getenv("TEST_DB_URL", "sqlite+aiosqlite:///./test.db")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh temporary SQLite database for each test, with tables.

    The database is created in the project root as `test.db`. All tables are
    created before the test and dropped after the test.
    """
    engine = create_async_engine(TEST_DB_URL, echo=False, future=True)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create a session factory bound to this engine
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session

    # Drop all tables after the test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """Create a TestClient for the FastAPI app with DB session override.

    The `get_db` dependency is overridden to return the test session.
    After the test, the dependency overrides are cleared.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def create_test_device(db_session: AsyncSession) -> Callable[..., Device]:
    """Factory fixture to create a Device in the test database.

    Returns a callable that accepts keyword arguments to override default values.
    Default device: name="Test Device", mac_address="AA:BB:CC:DD:EE:FF",
    ip_address=None, port=9, enabled=True.
    """
    async def _create_device(**kwargs) -> Device:
        defaults = {
            "name": "Test Device",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "ip_address": None,
            "port": 9,
            "enabled": True,
        }
        defaults.update(kwargs)
        device = Device(**defaults)
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)
        return device
    return _create_device


@pytest.fixture
async def create_test_api_key(db_session: AsyncSession) -> Callable[..., ApiKey]:
    """Factory fixture to create an ApiKey in the test database.

    Returns a callable that accepts either `key` (plain text, will be hashed)
    or `key_hash` (already hashed). Default: key_name="Test API Key", is_active=True.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def _create_api_key(**kwargs) -> ApiKey:
        defaults = {
            "key_name": "Test API Key",
            "is_active": True,
        }
        # Handle plain key or existing hash
        if "key" in kwargs:
            plain_key = kwargs.pop("key")
            key_hash = pwd_context.hash(plain_key)
        elif "key_hash" in kwargs:
            key_hash = kwargs.pop("key_hash")
        else:
            # Generate a default random key if none provided
            plain_key = "testapikey123"
            key_hash = pwd_context.hash(plain_key)
        defaults["key_hash"] = key_hash
        defaults.update(kwargs)
        api_key = ApiKey(**defaults)
        db_session.add(api_key)
        await db_session.commit()
        await db_session.refresh(api_key)
        return api_key
    return _create_api_key
