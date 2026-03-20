"""Tests for webhook system."""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.crud import create_webhook_config, get_webhook_configs
from app.models import WebhookConfig


@pytest.fixture
async def webhook_config(db_session) -> WebhookConfig:
    """Create a test webhook configuration."""
    wh = await create_webhook_config(
        db_session,
        name="Test Webhook",
        url="https://example.com/webhook",
        event_types=["wol_sent"],
        headers={"X-Custom": "value"},
        secret="testsecret",
        is_active=True,
    )
    return wh


def test_create_webhook(client: TestClient, test_api_key):
    """Test creating a webhook configuration."""
    plain_key = test_api_key._plain_key
    response = client.post(
        "/webhooks",
        json={
            "name": "My Webhook",
            "url": "https://example.com/hook",
            "event_types": ["wol_sent", "wol_success"],
            "headers": {"Authorization": "Bearer token"},
            "secret": "mysecret",
            "is_active": True,
        },
        headers={"X-API-Key": plain_key},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My Webhook"
    assert data["url"] == "https://example.com/hook"
    # Secret should not be returned
    assert "secret" not in data or data.get("secret") is None


def test_list_webhooks(client: TestClient, test_api_key, webhook_config: WebhookConfig):
    """Test listing webhook configurations."""
    plain_key = test_api_key._plain_key
    response = client.get("/webhooks", headers={"X-API-Key": plain_key})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(w["id"] == webhook_config.id for w in data)


def test_webhook_delivery_creation_flow(client: TestClient, test_api_key, db_session):
    """Test that waking a device creates a webhook delivery entry."""
    # This is an integration test: create device, wake, check delivery
    plain_key = test_api_key._plain_key
    # Create a device
    resp = client.post(
        "/devices",
        json={
            "name": "Webhook Test Device",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "ip_address": None,
            "port": 9,
            "enabled": True,
        },
        headers={"X-API-Key": plain_key},
    )
    assert resp.status_code == 200
    device = resp.json()

    # Create a webhook config
    resp = client.post(
        "/webhooks",
        json={
            "name": "Test Hook",
            "url": "https://example.com/hook",
            "event_types": ["wol_sent"],
            "secret": "secret",
        },
        headers={"X-API-Key": plain_key},
    )
    assert resp.status_code == 200
    webhook = resp.json()

    # Trigger wake (mock send_magic_packet to avoid actual network)
    with patch("app.main.send_magic_packet") as mock_send:
        mock_send.return_value = None
        resp = client.get(
            f"/wake/{device['mac_address']}",
            headers={"X-API-Key": plain_key},
        )
        assert resp.status_code == 200

    # Check that a webhook delivery was created (query DB directly)
    from app.crud import get_deliveries
    import asyncio
    deliveries = asyncio.run(get_deliveries(db_session, webhook_id=webhook["id"]))
    assert len(deliveries) >= 1
    assert deliveries[0].event_type == "wol_sent"
    assert deliveries[0].status == "pending"  # pending, will be processed by worker
