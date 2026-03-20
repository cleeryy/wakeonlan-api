import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set required env vars BEFORE importing app to satisfy startup validation
os.environ.setdefault("DEFAULT_MAC", "AA:BB:CC:DD:EE:FF")
os.environ.setdefault("API_KEY", "test-key")  # Default API key for tests

from app.main import app

client = TestClient(app)


class TestRootEndpoint:
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {
            "status": 200,
            "message": "Welcome to the Wake-on-LAN API!"
        }

    def test_health_check(self):
        """Health check endpoint should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "wakeonlan-api"
        assert "timestamp" in data


class TestWakeEndpointAuth:
    def test_wake_without_api_key(self):
        response = client.get("/wake")
        assert response.status_code == 403
        assert response.json() == {"detail": {"error": "Invalid or missing API key"}}

    def test_wake_with_invalid_api_key(self):
        response = client.get("/wake", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 403
        assert response.json() == {"detail": {"error": "Invalid or missing API key"}}

    def test_wake_with_valid_api_key(self):
        with patch('app.main.send_magic_packet') as mock_send:
            response = client.get("/wake", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            assert response.json() == {"message": "Wake-on-LAN packet sent successfully"}
            mock_send.assert_called_once_with("AA:BB:CC:DD:EE:FF")

    def test_wake_mac_without_api_key(self):
        response = client.get("/wake/AA:BB:CC:DD:EE:FF")
        assert response.status_code == 403
        assert response.json() == {"detail": {"error": "Invalid or missing API key"}}

    def test_wake_mac_with_valid_api_key(self):
        test_mac = "AA:BB:CC:DD:EE:FF"
        with patch('app.main.send_magic_packet') as mock_send:
            response = client.get(f"/wake/{test_mac}", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            expected_msg = f"Wake-on-LAN packet sent successfully to {test_mac} device!"
            assert response.json() == {"message": expected_msg}
            mock_send.assert_called_once_with(test_mac)

    def test_wake_mac_with_invalid_api_key(self):
        test_mac = "AA:BB:CC:DD:EE:FF"
        response = client.get(f"/wake/{test_mac}", headers={"X-API-Key": "invalid"})
        assert response.status_code == 403
        assert response.json() == {"detail": {"error": "Invalid or missing API key"}}

    def test_multiple_api_keys(self):
        with patch('app.main.send_magic_packet') as mock_send:
            import app.main as main_module
            original_api_key = main_module.API_KEY
            try:
                main_module.API_KEY = "test-key,another-key"
                response = client.get("/wake", headers={"X-API-Key": "test-key"})
                assert response.status_code == 200
                response = client.get("/wake", headers={"X-API-Key": "invalid"})
                assert response.status_code == 403
            finally:
                main_module.API_KEY = original_api_key


class TestMacAddressValidation:
    def test_valid_mac_with_colons(self):
        with patch('app.main.send_magic_packet') as mock_send:
            response = client.get("/wake/AA:BB:CC:DD:EE:FF", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            mock_send.assert_called_once_with("AA:BB:CC:DD:EE:FF")

    def test_valid_mac_with_hyphens(self):
        with patch('app.main.send_magic_packet') as mock_send:
            response = client.get("/wake/AA-BB-CC-DD-EE-FF", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            mock_send.assert_called_once_with("AA-BB-CC-DD-EE-FF")

    def test_invalid_mac_too_short(self):
        response = client.get("/wake/AA:BB:CC:DD:EE", headers={"X-API-Key": "test-key"})
        assert response.status_code == 400
        assert response.json() == {"detail": {"error": "Invalid MAC address format: 'AA:BB:CC:DD:EE'. Must be XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX"}}

    def test_invalid_mac_too_long(self):
        response = client.get("/wake/AA:BB:CC:DD:EE:FF:11", headers={"X-API-Key": "test-key"})
        assert response.status_code == 400
        assert "Invalid MAC address format" in response.json()["detail"]["error"]

    def test_invalid_mac_invalid_characters(self):
        response = client.get("/wake/GG:HH:II:JJ:KK:LL", headers={"X-API-Key": "test-key"})
        assert response.status_code == 400
        assert "Invalid MAC address format" in response.json()["detail"]["error"]

    def test_invalid_mac_missing_separators(self):
        response = client.get("/wake/AABBCCDDEEFF", headers={"X-API-Key": "test-key"})
        assert response.status_code == 400
        assert "Invalid MAC address format" in response.json()["detail"]["error"]

    def test_invalid_mac_wrong_separator_mixed(self):
        response = client.get("/wake/AA:BB-CC:DD-EE:FF", headers={"X-API-Key": "test-key"})
        assert response.status_code == 400
        assert "Invalid MAC address format" in response.json()["detail"]["error"]

    def test_invalid_mac_lowercase_valid(self):
        with patch('app.main.send_magic_packet') as mock_send:
            response = client.get("/wake/aa:bb:cc:dd:ee:ff", headers={"X-API-Key": "test-key"})
            assert response.status_code == 200
            mock_send.assert_called_once_with("aa:bb:cc:dd:ee:ff")
