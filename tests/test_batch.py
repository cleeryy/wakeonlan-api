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

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    app.state.limiter.reset()


class TestBatchWake:
    """Tests for batch wake endpoint."""

    def test_batch_wake_success(self):
        """Should send WoL to all MACs and return success for each."""
        with patch('app.main.send_magic_packet') as mock_send:
            response = client.post(
                "/wake/batch",
                json={"mac_addresses": ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]},
                headers={"X-API-Key": "test-key"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Batch wake completed for 2 devices"
            assert len(data["results"]) == 2
            for result in data["results"]:
                assert result["status"] == "success"
            assert mock_send.call_count == 2

    def test_batch_wake_with_invalid_mac(self):
        """Should reject batch if any MAC is invalid."""
        response = client.post(
            "/wake/batch",
            json={"mac_addresses": ["AA:BB:CC:DD:EE:FF", "invalid"]},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 400
        assert "Invalid MAC address format" in response.json()["detail"]["error"]

    def test_batch_wake_with_partial_failure(self):
        """Should return error for MACs that fail."""
        call_count = 0
        def mock_send_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None  # success
            raise Exception("Network error")
        
        with patch('app.main.send_magic_packet', side_effect=mock_send_side_effect):
            response = client.post(
                "/wake/batch",
                json={"mac_addresses": ["AA:BB:CC:DD:EE:FF", "11:22:33:44:55:66"]},
                headers={"X-API-Key": "test-key"}
            )
            assert response.status_code == 200  # Overall success (partial ok)
            data = response.json()
            assert len(data["results"]) == 2
            assert data["results"][0]["status"] == "success"
            assert data["results"][1]["status"] == "error"
            assert "Network error" in data["results"][1]["error"]

    def test_batch_wake_empty_list(self):
        """Should handle empty MAC list gracefully."""
        response = client.post(
            "/wake/batch",
            json={"mac_addresses": []},
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Batch wake completed for 0 devices"
        assert data["results"] == []

    def test_batch_wake_requires_auth(self):
        """Should require API key."""
        response = client.post("/wake/batch", json={"mac_addresses": ["AA:BB:CC:DD:EE:FF"]})
        assert response.status_code == 403

    def test_batch_uses_broadcast_ip(self):
        """Should use BROADCAST_IP if configured."""
        import app.main as main_mod
        original = main_mod.BROADCAST_IP
        main_mod.BROADCAST_IP = "192.168.1.255"
        try:
            with patch('app.main.send_magic_packet') as mock_send:
                response = client.post(
                    "/wake/batch",
                    json={"mac_addresses": ["AA:BB:CC:DD:EE:FF"]},
                    headers={"X-API-Key": "test-key"}
                )
                assert response.status_code == 200
                mock_send.assert_called_once_with("AA:BB:CC:DD:EE:FF", ip_address="192.168.1.255")
        finally:
            main_mod.BROADCAST_IP = original

    def test_batch_wake_large_list(self):
        """Should handle large batch (10 MACs) efficiently."""
        with patch('app.main.send_magic_packet') as mock_send:
            macs = [f"{i:02X}:{i+1:02X}:{i+2:02X}:{i+3:02X}:{i+4:02X}:{i+5:02X}" for i in range(0, 60, 6)]
            response = client.post(
                "/wake/batch",
                json={"mac_addresses": macs},
                headers={"X-API-Key": "test-key"}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == len(macs)
            assert all(r["status"] == "success" for r in data["results"])
