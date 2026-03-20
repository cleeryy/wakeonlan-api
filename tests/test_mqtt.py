"""Tests for MQTT client."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.mqtt.client import mqtt_client, MQTTClient


@pytest.mark.asyncio
async def test_mqtt_connect_disabled(monkeypatch):
    """When MQTT_BROKER is not set, connect should be skipped."""
    from app.core.config import settings
    original = settings.MQTT_BROKER
    settings.MQTT_BROKER = None
    try:
        await mqtt_client.connect()
        assert mqtt_client.connected is False
    finally:
        settings.MQTT_BROKER = original


@pytest.mark.asyncio
async def test_mqtt_publish_when_not_connected(monkeypatch):
    """Publish should log warning when not connected."""
    mqtt_client.connected = False
    # Should not raise
    await mqtt_client.publish("test/topic", {"msg": "hello"})


@pytest.mark.asyncio
async def test_mqtt_publish_success(monkeypatch):
    """Test successful publish."""
    # Mock the aiomqtt client
    mock_client = AsyncMock()
    mock_client.publish.return_value = None
    mqtt_client.client = mock_client
    mqtt_client.connected = True

    result = await mqtt_client.publish("test/topic", {"key": "value"})
    assert result is True
    mock_client.publish.assert_awaited_once()
    # Check topic includes prefix
    call_args = mock_client.publish.call_args
    topic = call_args.kwargs.get("topic") or call_args.args[0]
    assert topic.startswith("wol/")  # default prefix
