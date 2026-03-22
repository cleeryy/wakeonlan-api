import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set required env vars
os.environ.setdefault("DEFAULT_MAC", "AA:BB:CC:DD:EE:FF")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("WEBHOOK_URL", "https://example.com/webhook")
os.environ.setdefault("WEBHOOK_TIMEOUT", "5.0")

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    app.state.limiter.reset()


class TestWebhookNotifications:
    """Tests for webhook notifications on WoL events."""

    def test_webhook_sent_on_success(self):
        """Should call send_webhook_notification with success=True on successful WoL."""
        import app.main as main_mod
        main_mod.WEBHOOK_URL = "https://example.com/webhook"
        try:
            with patch('app.main.send_webhook_notification') as mock_webhook:
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200
                mock_webhook.assert_called_once_with(
                    mac="AA:BB:CC:DD:EE:FF",
                    endpoint="/wake",
                    success=True
                )
        finally:
            main_mod.WEBHOOK_URL = ""  # reset if needed

    def test_webhook_sent_on_failure(self):
        """Should call send_webhook_notification with success=False on failed WoL."""
        import app.main as main_mod
        main_mod.WEBHOOK_URL = "https://example.com/webhook"
        try:
            with patch('app.main.send_magic_packet') as mock_send, \
                 patch('app.main.send_webhook_notification') as mock_webhook:
                mock_send.side_effect = Exception("Network error")
                response = client.get("/wake/AA:BB:CC:DD:EE:FF", headers={"X-API-Key": "test-key"})
                assert response.status_code == 500
                mock_webhook.assert_called_once_with(
                    mac="AA:BB:CC:DD:EE:FF",
                    endpoint="/wake/AA:BB:CC:DD:EE:FF",
                    success=False,
                    error="Network error"
                )
        finally:
            main_mod.WEBHOOK_URL = ""

    def test_webhook_not_sent_when_disabled(self):
        """Should not call send_webhook_notification if WEBHOOK_URL is not set."""
        import app.main as main_mod
        original_url = main_mod.WEBHOOK_URL
        main_mod.WEBHOOK_URL = ""
        try:
            with patch('app.main.send_webhook_notification') as mock_webhook:
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200
                mock_webhook.assert_not_called()
        finally:
            main_mod.WEBHOOK_URL = original_url

    def test_webhook_sent_on_device_wake_success(self):
        """Should call send_webhook_notification on wake device by name success."""
        import app.main as main_mod
        main_mod.WEBHOOK_URL = "https://example.com/webhook"
        try:
            # Add device first
            client.post("/devices", json={"name": "my-pc", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})
            
            with patch('app.main.send_webhook_notification') as mock_webhook:
                response = client.get("/wake/device/my-pc", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200
                mock_webhook.assert_called_once_with(
                    mac="AA:BB:CC:DD:EE:FF",
                    endpoint="/wake/device/my-pc",
                    success=True
                )
        finally:
            main_mod.WEBHOOK_URL = ""

    def test_webhook_sent_on_batch_success(self):
        """Should call send_webhook_notification for each MAC in batch on success."""
        import app.main as main_mod
        main_mod.WEBHOOK_URL = "https://example.com/webhook"
        try:
            with patch('app.main.send_webhook_notification') as mock_webhook:
                response = client.post(
                    "/wake/batch",
                    json={"mac_addresses": ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]},
                    headers={"X-API-Key": "test-key"}
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data["results"]) == 2
                # Should have called webhook twice (once per MAC)
                assert mock_webhook.call_count == 2
                # Check first call args
                first_call = mock_webhook.call_args_list[0]
                assert first_call.kwargs['mac'] == "AA:BB:CC:DD:EE:FF"
                assert first_call.kwargs['endpoint'] == "/wake/batch"
                assert first_call.kwargs['success'] is True
                # Second call
                second_call = mock_webhook.call_args_list[1]
                assert second_call.kwargs['mac'] == "11:22:33:44:55:66"
                assert second_call.kwargs['endpoint'] == "/wake/batch"
                assert second_call.kwargs['success'] is True
        finally:
            main_mod.WEBHOOK_URL = ""

    def test_webhook_sent_on_batch_partial_failure(self):
        """Should call send_webhook_notification with success=False for failed MACs."""
        import app.main as main_mod
        main_mod.WEBHOOK_URL = "https://example.com/webhook"
        try:
            with patch('app.main.send_magic_packet') as mock_send, \
                 patch('app.main.send_webhook_notification') as mock_webhook:
                # First MAC succeeds on first try. Second MAC fails all attempts.
                # We need enough side_effect entries: 1 success + WOL_RETRIES failures (default 3)
                mock_send.side_effect = [None] + [Exception("fail")] * 3
                response = client.post(
                    "/wake/batch",
                    json={"mac_addresses": ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]},
                    headers={"X-API-Key": "test-key"}
                )
                assert response.status_code == 200
                data = response.json()
                assert data["results"][0]["status"] == "success"
                assert data["results"][1]["status"] == "error"
                # Two webhook calls (one per MAC)
                assert mock_webhook.call_count == 2
                # Check second call has success=False and error containing "fail"
                second_call = mock_webhook.call_args_list[1]
                assert second_call.kwargs['mac'] == "11:22:33:44:55:66"
                assert second_call.kwargs['success'] is False
                assert 'fail' in second_call.kwargs['error']
        finally:
            main_mod.WEBHOOK_URL = ""
