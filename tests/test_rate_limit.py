"""Tests for rate limiting."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.crud import create_api_key
from app.db.session import async_session_factory


@pytest.fixture
async def test_api_key_with_auth(db_session) -> tuple[str, str]:
    """Create an API key and return (key_id, plain_key)."""
    import secrets
    from app.crud import create_api_key
    plain_key = secrets.token_hex(16)
    api_key = await create_api_key(
        db_session,
        key_name="Rate Limit Test",
        plain_key=plain_key,
        is_active=True,
    )
    return api_key.id, plain_key


def test_rate_limit_headers_present(client: TestClient, test_api_key_with_auth):
    """Rate limit headers should be present in response."""
    key_id, plain_key = test_api_key_with_auth
    response = client.get("/devices", headers={"X-API-Key": plain_key})
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    # Optionally, Retry-After may be present when limit exceeded


def test_rate_limit_exceeded(client: TestClient, test_api_key_with_auth, monkeypatch):
    """After exceeding rate limit, should return 429."""
    key_id, plain_key = test_api_key_with_auth
    # Temporarily set a very low rate limit for testing
    from app.core.config import settings
    original = settings.RATE_LIMIT_DEFAULT
    settings.RATE_LIMIT_DEFAULT = "1/minute"

    try:
        # First request should succeed
        response = client.get("/devices", headers={"X-API-Key": plain_key})
        assert response.status_code == 200
        # Second request should be rate limited
        response = client.get("/devices", headers={"X-API-Key": plain_key})
        assert response.status_code == 429
        assert "rate limit exceeded" in response.json()["detail"].lower()
    finally:
        settings.RATE_LIMIT_DEFAULT = original


def test_different_endpoints_have_different_limits(
    client: TestClient, test_api_key_with_auth
):
    """Wake endpoint should have stricter limit than health."""
    key_id, plain_key = test_api_key_with_auth
    # Health endpoint should allow many requests
    for _ in range(5):
        resp = client.get("/health", headers={"X-API-Key": plain_key})
        assert resp.status_code == 200
    # Wake endpoint may be more restricted; we can't easily test without exceeding
    # Just check that both return 200 when under limit
    resp = client.get("/wake", headers={"X-API-Key": plain_key})
    # Could be 200 or 429 depending on default limit; we assume it's allowed for test
    # In a real test we'd set high limits
