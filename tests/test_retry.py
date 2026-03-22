import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set required env vars
os.environ.setdefault("DEFAULT_MAC", "AA:BB:CC:DD:EE:FF")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("WOL_RETRIES", "3")
os.environ.setdefault("WOL_RETRY_DELAY", "0.1")

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    app.state.limiter.reset()


class TestRetryLogic:
    """Tests for WoL retry logic."""

    def test_retry_on_failure_eventually_succeeds(self):
        """Should retry when send_magic_packet fails and eventually succeed."""
        with patch('app.main.send_magic_packet') as mock_send:
            # Fail first 2 times, succeed on 3rd
            mock_send.side_effect = [Exception("Network error"), Exception("Network error"), None]
            
            response = client.get("/wake", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            assert mock_send.call_count == 3

    def test_retry_exhausted_raises_500(self):
        """Should return 500 when all retries fail."""
        with patch('app.main.send_magic_packet') as mock_send:
            mock_send.side_effect = Exception("Network error")
            
            response = client.get("/wake", headers={"X-API-Key": "test-key"})
            assert response.status_code == 500
            assert "Failed to send Wake-on-LAN packet" in response.json()["detail"]["error"]
            assert mock_send.call_count == 3  # WOL_RETRIES default

    def test_retry_on_wake_mac_endpoint(self):
        """Retry logic should apply to /wake/{mac} endpoint."""
        with patch('app.main.send_magic_packet') as mock_send:
            mock_send.side_effect = [Exception("fail"), None]
            
            response = client.get("/wake/AA:BB:CC:DD:EE:FF", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            assert mock_send.call_count == 2

    def test_retry_on_device_wake_endpoint(self):
        """Retry logic should apply to /wake/device/{name} endpoint."""
        with patch('app.main.send_magic_packet') as mock_send:
            mock_send.side_effect = [Exception("fail"), None]
            
            # Add device first
            client.post("/devices", json={"name": "pc1", "mac": "AA:BB:CC:DD:EE:FF"}, headers={"X-API-Key": "test-key"})
            response = client.get("/wake/device/pc1", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            assert mock_send.call_count == 2

    def test_immediate_success_no_retry(self):
        """If first attempt succeeds, no retry should occur."""
        with patch('app.main.send_magic_packet') as mock_send:
            mock_send.return_value = None
            
            response = client.get("/wake", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            assert mock_send.call_count == 1

    def test_custom_retry_count_via_env(self):
        """Should respect WOL_RETRIES environment variable."""
        import app.main as main_mod
        original_retries = main_mod.WOL_RETRIES
        main_mod.WOL_RETRIES = 5
        try:
            with patch('app.main.send_magic_packet') as mock_send:
                mock_send.side_effect = Exception("fail")
                
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 500
                assert mock_send.call_count == 5
        finally:
            main_mod.WOL_RETRIES = original_retries

    def test_retry_delay_respected(self):
        """Should sleep between retries (verify by mocking sleep)."""
        with patch('app.main.send_magic_packet') as mock_send, \
             patch('app.main.asyncio.sleep') as mock_sleep:
            mock_send.side_effect = [Exception("fail"), None]
            
            response = client.get("/wake", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            assert mock_sleep.called
            # sleep should be called once (between first failure and second attempt)
            assert mock_sleep.call_count == 1
