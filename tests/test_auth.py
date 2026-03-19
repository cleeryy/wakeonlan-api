"""Tests for API key authentication."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.crud import create_api_key, deactivate_api_key
from app.models import ApiKey


@pytest.fixture
async def test_api_key(db_session) -> ApiKey:
    """Create a test API key."""
    import secrets
    plain_key = secrets.token_hex(16)
    api_key = await create_api_key(
        db_session,
        key_name="Test Key",
        plain_key=plain_key,
        is_active=True,
    )
    # Attach plain key for test usage
    api_key._plain_key = plain_key  # type: ignore
    return api_key


@pytest.mark.asyncio
async def test_root_requires_no_auth(client: TestClient):
    """Root endpoint should be accessible without authentication."""
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_requires_no_auth(client: TestClient):
    """Health endpoint should be accessible without authentication."""
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_endpoint_requires_api_key(client: TestClient):
    """Protected endpoints should require X-API-Key header."""
    response = client.get("/devices")
    assert response.status_code == 401
    assert "API key required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_valid_api_key_works(client: TestClient, test_api_key: ApiKey):
    """Valid API key should grant access."""
    response = client.get("/devices", headers={"X-API-Key": test_api_key._plain_key})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_api_key_rejected(client: TestClient):
    """Invalid API key should be rejected."""
    response = client.get("/devices", headers={"X-API-Key": "invalidkey"})
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_deactivated_api_key_rejected(
    client: TestClient, db_session
):
    """Deactivated API key should be rejected."""
    import secrets
    plain_key = secrets.token_hex(16)
    api_key = await create_api_key(
        db_session, key_name="Deactivated", plain_key=plain_key, is_active=True
    )
    await deactivate_api_key(db_session, api_key.id)
    await db_session.commit()

    response = client.get("/devices", headers={"X-API-Key": plain_key})
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

